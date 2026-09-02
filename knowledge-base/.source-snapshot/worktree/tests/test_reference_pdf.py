from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest

from pdf_fixture_factory import ascii_pdf, blank_pdf, chinese_pdf, encrypt_pdf
from test_ckb import invoke, make_repo, review_all

from ckb_core.common import CkbError
from ckb_core.reference_documents import ingest_reference
from ckb_core.reference_inputs import WEB_INPUT_ADAPTER_ID, web_input_adapter_contract
from ckb_core.reference_pdf import PdfExtractionError, _load_pypdf, extract_pdf, inspect_pdf, validate_pdf_extraction


def _commands(*lines: tuple[float, float, str]) -> list[tuple[float, float, str]]:
    return list(lines)


class PdfReferenceExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-pdf-test-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_native_layout_preserves_page_code_and_table_boundaries(self) -> None:
        source = ascii_pdf(
            self.root / "native-structure.pdf",
            [
                _commands(
                    (72, 740, "PDF STRUCTURE TEST"),
                    (72, 710, "A paragraph with enough deterministic native text for extraction."),
                    (72, 650, "def calculate(value):"),
                    (108, 630, "return value + 1"),
                    (72, 570, "Name          Value"),
                    (72, 550, "alpha         10"),
                    (72, 530, "beta          20"),
                ),
                _commands(
                    (72, 740, "SECOND PAGE"),
                    (72, 710, "A second page proves deterministic ordering and one-based provenance."),
                ),
            ],
        )
        result = extract_pdf(source, "reference-native", self.root / "extraction")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["page_count"], 2)
        self.assertEqual([page["page_number"] for page in result["pages"]], [1, 2])
        structures = {fragment["structure"]: fragment for fragment in result["pages"][0]["fragments"]}
        self.assertIn("code", structures)
        self.assertIn("table", structures)
        self.assertIn("    return value + 1", structures["code"]["text"])
        self.assertIn("Name          Value", structures["table"]["text"])
        for page in result["pages"]:
            page_text = Path(page["text_file"]).read_text(encoding="utf-8")
            for fragment in page["fragments"]:
                self.assertEqual(fragment["source_id"], "reference-native")
                self.assertEqual(Path(fragment["source_file"]), source.resolve())
                self.assertEqual(fragment["page_number"], page["page_number"])
                self.assertEqual(fragment["method"], "native")
                self.assertIn(fragment["confidence"], {"high", "medium"})
                start, end = fragment["text_range"]["start"], fragment["text_range"]["end"]
                self.assertEqual(page_text[start:end], fragment["text"])
        manifest = {
            "reference_id": "reference-native",
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "extraction_file": result["manifest"],
            "extraction_sha256": result["manifest_sha256"],
            "extraction_status": "ready",
        }
        extraction, errors = validate_pdf_extraction(self.root.parent, manifest)
        # The managed-path audit requires the production references/extractions
        # root, which is covered by the end-to-end test below.
        self.assertIsNone(extraction)
        self.assertEqual(errors[0]["reason"], "reference-pdf-extraction-path")

    def test_page_audit_detects_manifest_page_empty_and_path_drift(self) -> None:
        output = self.root / "managed-output"
        reference_id = "reference-audit"
        source = ascii_pdf(
            output / "references" / "raw" / "audit.pdf",
            [
                [(72, 740, "First page has enough native text for a complete audit record.")],
                [(72, 740, "Second page has enough native text for a complete audit record.")],
            ],
        )
        result = extract_pdf(
            source,
            reference_id,
            output / "references" / "extractions" / reference_id,
        )
        manifest = {
            "reference_id": reference_id,
            "source_file": str(source.resolve()),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "extraction_file": result["manifest"],
            "extraction_sha256": result["manifest_sha256"],
            "extraction_status": "ready",
            "page_count": 2,
            "pending_pages": [],
        }
        extraction, errors = validate_pdf_extraction(output, manifest, require_ready=True)
        self.assertIsNotNone(extraction)
        self.assertEqual(errors, [])

        extraction_path = Path(result["manifest"])
        baseline = extraction_path.read_bytes()
        extraction_path.write_bytes(baseline + b" ")
        _extraction, errors = validate_pdf_extraction(output, manifest)
        self.assertIn("reference-pdf-extraction-drift", {item["reason"] for item in errors})

        extraction_path.write_bytes(baseline)
        changed = json.loads(baseline)
        changed["pages"][1]["page_number"] = 1
        extraction_path.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["extraction_sha256"] = hashlib.sha256(extraction_path.read_bytes()).hexdigest()
        _extraction, errors = validate_pdf_extraction(output, manifest)
        self.assertIn("reference-pdf-page-sequence", {item["reason"] for item in errors})

        extraction_path.write_bytes(baseline)
        changed = json.loads(baseline)
        escaped = self.root / "escaped-page.txt"
        escaped.write_text(changed["pages"][0]["fragments"][0]["text"], encoding="utf-8")
        changed["pages"][0]["text_file"] = str(escaped.resolve())
        extraction_path.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["extraction_sha256"] = hashlib.sha256(extraction_path.read_bytes()).hexdigest()
        _extraction, errors = validate_pdf_extraction(output, manifest)
        self.assertIn("reference-pdf-page-path", {item["reason"] for item in errors})

    def test_native_chinese_page_round_trips_unicode(self) -> None:
        source = chinese_pdf(
            self.root / "native-chinese.pdf",
            ["中文资料页标题", "这段中文原生文本用于验证页级提取与原文定位。"],
        )
        result = extract_pdf(source, "reference-chinese", self.root / "chinese-extraction")
        self.assertEqual(result["status"], "ready")
        page_text = Path(result["pages"][0]["text_file"]).read_text(encoding="utf-8")
        self.assertIn("中文资料页标题", page_text)
        self.assertIn("页级提取与原文定位", page_text)

    def test_scanned_mixed_and_bounded_ocr_states_are_explicit(self) -> None:
        scanned = blank_pdf(self.root / "scanned.pdf")
        pending = extract_pdf(scanned, "reference-scan", self.root / "scan-extraction")
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["pending_pages"], [1])
        self.assertEqual(pending["pages"][0]["reason"], "native-text-below-usable-threshold")

        unavailable = extract_pdf(
            scanned,
            "reference-scan-no-runtime",
            self.root / "scan-no-runtime-extraction",
            ocr_enabled=True,
        )
        self.assertEqual(unavailable["status"], "pending")
        self.assertEqual(unavailable["pages"][0]["reason"], "ocr-adapter-not-configured")

        mixed = ascii_pdf(
            self.root / "mixed.pdf",
            [
                _commands((72, 740, "Native page contains sufficient text and must bypass OCR completely.")),
                [],
            ],
        )
        mixed_result = extract_pdf(
            mixed,
            "reference-mixed",
            self.root / "mixed-extraction",
            ocr_enabled=True,
        )
        self.assertEqual([page["status"] for page in mixed_result["pages"]], ["extracted", "pending"])
        self.assertEqual(mixed_result["pages"][0]["ocr"]["status"], "not-needed")

        adapter = self.root / "ocr_adapter.py"
        adapter.write_text(
            "import argparse, json\n"
            "parser=argparse.ArgumentParser()\n"
            "parser.add_argument('--source'); parser.add_argument('--page',type=int); "
            "parser.add_argument('--output'); parser.add_argument('--schema-version',type=int); "
            "parser.add_argument('--cancel-file')\n"
            "args=parser.parse_args()\n"
            "value={'schema_version':args.schema_version,'status':'extracted','page_number':args.page,"
            "'text':'OCR recovered page text with sufficient deterministic characters.','confidence':0.96}\n"
            "open(args.output,'w',encoding='utf-8').write(json.dumps(value,ensure_ascii=False))\n",
            encoding="utf-8",
        )
        recovered = extract_pdf(
            scanned,
            "reference-scan-ocr",
            self.root / "scan-ocr-extraction",
            ocr_enabled=True,
            ocr_adapter=adapter,
            ocr_max_pages=1,
            ocr_timeout_seconds=5,
        )
        self.assertEqual(recovered["status"], "ready")
        self.assertEqual(recovered["pages"][0]["method"], "ocr")
        self.assertEqual(recovered["ocr"]["attempted_pages"], 1)

        size_bounded = extract_pdf(
            scanned,
            "reference-size-bounded",
            self.root / "size-bounded-extraction",
            ocr_enabled=True,
            ocr_adapter=adapter,
            ocr_max_input_bytes=10,
        )
        self.assertEqual(size_bounded["pages"][0]["reason"], "ocr-input-size-limit")

        two_scans = blank_pdf(self.root / "two-scans.pdf", page_count=2)
        bounded = extract_pdf(
            two_scans,
            "reference-bounded",
            self.root / "bounded-extraction",
            ocr_enabled=True,
            ocr_adapter=adapter,
            ocr_max_pages=1,
            ocr_timeout_seconds=5,
        )
        self.assertEqual(bounded["pages"][1]["reason"], "ocr-page-limit")
        cancel = self.root / "cancel.flag"
        cancel.write_text("cancel\n", encoding="utf-8")
        cancelled = extract_pdf(
            scanned,
            "reference-cancelled",
            self.root / "cancelled-extraction",
            ocr_enabled=True,
            ocr_adapter=adapter,
            ocr_cancel_file=cancel,
        )
        self.assertEqual(cancelled["pages"][0]["reason"], "ocr-cancelled")

        slow_adapter = self.root / "slow_ocr_adapter.py"
        slow_adapter.write_text(
            "import argparse, time\n"
            "parser=argparse.ArgumentParser(); parser.add_argument('--source'); parser.add_argument('--page'); "
            "parser.add_argument('--output'); parser.add_argument('--schema-version'); parser.add_argument('--cancel-file')\n"
            "parser.parse_args(); time.sleep(5)\n",
            encoding="utf-8",
        )
        timed_out = extract_pdf(
            scanned,
            "reference-timeout",
            self.root / "timeout-extraction",
            ocr_enabled=True,
            ocr_adapter=slow_adapter,
            ocr_timeout_seconds=1,
        )
        self.assertEqual(timed_out["pages"][0]["reason"], "ocr-timeout")

        live_cancel = self.root / "live-cancel.flag"
        creator = threading.Thread(target=lambda: (time.sleep(0.2), live_cancel.write_text("cancel\n", encoding="utf-8")))
        creator.start()
        cancelled_live = extract_pdf(
            scanned,
            "reference-live-cancel",
            self.root / "live-cancel-extraction",
            ocr_enabled=True,
            ocr_adapter=slow_adapter,
            ocr_timeout_seconds=5,
            ocr_cancel_file=live_cancel,
        )
        creator.join()
        self.assertEqual(cancelled_live["pages"][0]["reason"], "ocr-cancelled")

    def test_corrupt_encrypted_size_page_and_source_root_limits(self) -> None:
        corrupt = self.root / "corrupt.pdf"
        corrupt.write_bytes(b"%PDF-1.7\ntruncated")
        with self.assertRaisesRegex(PdfExtractionError, "corrupt or unsupported"):
            inspect_pdf(corrupt, 1024, 10)

        plain = ascii_pdf(
            self.root / "plain.pdf",
            [[(72, 740, "This native PDF has enough text to be encrypted for a failure fixture.")]],
        )
        encrypted = encrypt_pdf(plain, self.root / "encrypted.pdf", _load_pypdf())
        with self.assertRaisesRegex(PdfExtractionError, "encrypted PDF"):
            inspect_pdf(encrypted, 1024 * 1024, 10)
        with self.assertRaisesRegex(PdfExtractionError, "must contain"):
            inspect_pdf(plain, 10, 10)
        multi = blank_pdf(self.root / "limit-pages.pdf", page_count=2)
        with self.assertRaisesRegex(PdfExtractionError, "exceeds limit"):
            inspect_pdf(multi, 1024 * 1024, 1)

        output = self.root / "minimal-output"
        (output / "human").mkdir(parents=True)
        (output / "markdown").mkdir()
        (output / "state.json").write_text("{}\n", encoding="utf-8")
        allowed = self.root / "allowed"
        allowed.mkdir()
        with self.assertRaisesRegex(CkbError, "outside --source-root"):
            ingest_reference(
                output,
                plain,
                "越界 PDF",
                "本地测试",
                "CC0-1.0",
                source_root=allowed,
            )

    def test_web_adapter_boundary_is_frozen_without_fetch_implementation(self) -> None:
        contract = web_input_adapter_contract()
        self.assertEqual(contract["adapter_id"], WEB_INPUT_ADAPTER_ID)
        self.assertEqual(contract["implementation_status"], "not-implemented")
        self.assertIn("output-still-requires-reference-ingest-and-agent-review", contract["boundary"])


class PdfReferenceEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-pdf-e2e-")
        self.root = Path(self.temp.name)
        self.repo = make_repo(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _completed_output(self) -> Path:
        output = self.root / "output"
        initialized = invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown")
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        review_all(output)
        merged = invoke("merge", "--out", str(output))
        self.assertEqual(merged.returncode, 0, merged.stderr)
        finalized = invoke("finalize", "--out", str(output))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        return output

    def test_pdf_ingest_review_audit_indexes_and_rollback(self) -> None:
        output = self._completed_output()
        baseline_connection = sqlite3.connect(output / "machine/knowledge.sqlite")
        try:
            baseline_entity_count = baseline_connection.execute("SELECT count(*) FROM entities").fetchone()[0]
        finally:
            baseline_connection.close()
        scanned = blank_pdf(self.root / "pending-scan.pdf")
        pending_ingest = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(scanned),
            "--title", "待 OCR 扫描资料", "--origin", "本地扫描 fixture", "--license", "CC0-1.0",
            "--pdf-ocr",
        )
        self.assertEqual(pending_ingest.returncode, 4, pending_ingest.stderr)
        pending_result = json.loads(pending_ingest.stdout)
        self.assertEqual(pending_result["extraction"]["status"], "pending")
        self.assertEqual(pending_result["next"], "reference rollback -> reference ingest --pdf-ocr")
        self.assertEqual(pending_result["next_steps"][0]["command"], "reference rollback")
        self.assertEqual(
            pending_result["next_steps"][0]["arguments"]["reference"],
            pending_result["reference_id"],
        )
        e2e_adapter = self.root / "e2e_ocr_adapter.py"
        e2e_adapter.write_text(
            "import argparse, json\n"
            "parser=argparse.ArgumentParser(); parser.add_argument('--source'); parser.add_argument('--page',type=int); "
            "parser.add_argument('--output'); parser.add_argument('--schema-version',type=int); parser.add_argument('--cancel-file')\n"
            "args=parser.parse_args(); value={'schema_version':args.schema_version,'status':'extracted','page_number':args.page,"
            "'text':'OCR page text is now long enough for deterministic review.','confidence':0.97}\n"
            "open(args.output,'w',encoding='utf-8').write(json.dumps(value))\n",
            encoding="utf-8",
        )
        repeated_with_ocr = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(scanned),
            "--title", "待 OCR 扫描资料", "--origin", "本地扫描 fixture", "--license", "CC0-1.0",
            "--pdf-ocr", "--pdf-ocr-adapter", str(e2e_adapter),
        )
        self.assertEqual(repeated_with_ocr.returncode, 4, repeated_with_ocr.stderr)
        repeated_result = json.loads(repeated_with_ocr.stdout)
        self.assertTrue(repeated_result["idempotent"])
        self.assertEqual(repeated_result["reference_id"], pending_result["reference_id"])
        self.assertEqual(repeated_result["next_steps"][0]["command"], "reference rollback")
        self.assertEqual(repeated_result["next_steps"][1]["command"], "reference ingest")
        self.assertTrue(repeated_result["next_steps"][1]["arguments"]["pdf_ocr"])
        self.assertEqual(repeated_result["next_steps"][1]["arguments"]["pdf_ocr_adapter"], str(e2e_adapter.resolve()))
        pending_review = json.loads(Path(pending_result["review_template"]).read_text(encoding="utf-8"))
        pending_review.update(
            {
                "status": "agent-reviewed",
                "summary_zh": "该扫描资料仍缺少可复核的页级文本，因此当前保持待处理状态。",
                "claims": [
                    {
                        "claim_zh": "该项主张没有可核对的页级片段。",
                        "page_number": 1,
                        "fragment_id": "missing-fragment",
                        "start_offset": 0,
                        "end_offset": 1,
                        "source_text": "x",
                        "evidence_note": "扫描页仍待 OCR，当前没有可用于事实确认的原文片段。",
                    }
                ],
            }
        )
        pending_review_path = self.root / "pending-review.json"
        pending_review_path.write_text(json.dumps(pending_review, ensure_ascii=False, indent=2), encoding="utf-8")
        rejected = invoke("reference", "review", "--out", str(output), "--review", str(pending_review_path))
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("not reviewable", rejected.stderr)
        self.assertFalse((output / "human/references/待 OCR 扫描资料.md").exists())
        pending_rollback = invoke(
            "reference", "rollback", "--out", str(output), "--reference", pending_result["reference_id"]
        )
        self.assertEqual(pending_rollback.returncode, 0, pending_rollback.stderr)
        reingested_with_ocr = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(scanned),
            "--title", "待 OCR 扫描资料", "--origin", "本地扫描 fixture", "--license", "CC0-1.0",
            "--pdf-ocr", "--pdf-ocr-adapter", str(e2e_adapter),
        )
        self.assertEqual(reingested_with_ocr.returncode, 4, reingested_with_ocr.stderr)
        reingested_result = json.loads(reingested_with_ocr.stdout)
        self.assertFalse(reingested_result["idempotent"])
        self.assertEqual(reingested_result["extraction"]["status"], "ready")
        reingested_manifest = json.loads(Path(reingested_result["extraction"]["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(reingested_manifest["pages"][0]["method"], "ocr")
        reingested_rollback = invoke(
            "reference", "rollback", "--out", str(output), "--reference", reingested_result["reference_id"]
        )
        self.assertEqual(reingested_rollback.returncode, 0, reingested_rollback.stderr)

        source = ascii_pdf(
            self.root / "reviewable.pdf",
            [
                _commands(
                    (72, 740, "PAGE LEVEL PROVENANCE"),
                    (72, 710, "The archived page keeps an exact fragment for later human review."),
                ),
                _commands(
                    (72, 740, "SECOND PAGE EVIDENCE"),
                    (72, 710, "The second page proves that page numbering remains one based."),
                ),
            ],
        )
        ingested = invoke(
            "reference",
            "ingest",
            "--out",
            str(output),
            "--source",
            str(source),
            "--source-root",
            str(self.root),
            "--title",
            "PDF 页级证据资料",
            "--origin",
            "本地 PDF fixture",
            "--license",
            "CC0-1.0",
        )
        self.assertEqual(ingested.returncode, 4, ingested.stderr)
        result = json.loads(ingested.stdout)
        self.assertEqual(result["extraction"]["status"], "ready")
        reference_id = result["reference_id"]
        archived = Path(result["source"])
        self.assertEqual(archived.read_bytes(), source.read_bytes())
        manifest_path = Path(result["manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        extraction_path = Path(manifest["extraction_file"])
        extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
        self.assertEqual(extraction["page_count"], 2)
        self.assertEqual(extraction["pending_pages"], [])

        review = json.loads(Path(result["review_template"]).read_text(encoding="utf-8"))
        page = extraction["pages"][1]
        fragment = next(item for item in page["fragments"] if "second page proves" in item["text"].casefold())
        start, end = fragment["text_range"]["start"], fragment["text_range"]["end"]
        review.update(
            {
                "status": "agent-reviewed",
                "summary_zh": "这份 PDF 用两个原生文本页面验证可回到页码的片段证据，并保留逐页审阅边界。",
                "claims": [
                    {
                        "claim_zh": "资料第二页明确说明页码保持从一开始编号。",
                        "page_number": 2,
                        "fragment_id": fragment["fragment_id"],
                        "start_offset": start,
                        "end_offset": end,
                        "source_text": fragment["text"],
                        "evidence_note": "已重新打开归档 PDF 第二页，并逐字核对提取片段和页码。",
                    }
                ],
            }
        )
        review_path = self.root / "pdf-review.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
        invalid_review = json.loads(review_path.read_text(encoding="utf-8"))
        invalid_review["claims"][0]["page_number"] = 1
        review_path.write_text(json.dumps(invalid_review, ensure_ascii=False, indent=2), encoding="utf-8")
        rejected_locator = invoke("reference", "review", "--out", str(output), "--review", str(review_path))
        self.assertEqual(rejected_locator.returncode, 2)
        self.assertIn("page does not match", rejected_locator.stderr)
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
        reviewed = invoke("reference", "review", "--out", str(output), "--review", str(review_path))
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        reviewed_result = json.loads(reviewed.stdout)
        self.assertEqual(reviewed_result["audit"]["status"], "passed")
        human = Path(reviewed_result["human_file"])
        markdown = Path(reviewed_result["compatibility_file"])
        self.assertEqual(human.read_bytes(), markdown.read_bytes())
        human_text = human.read_text(encoding="utf-8")
        self.assertIn("原文第 2 页", human_text)
        self.assertIn("#page=2", human_text)
        self.assertIn("资料第二页明确说明页码保持从一开始编号。（[原文第 2 页]", human_text)
        self.assertNotIn("））", human_text)

        connection = sqlite3.connect(output / "machine/knowledge.sqlite")
        try:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("SELECT count(*) FROM entities").fetchone()[0], baseline_entity_count)
            rows = connection.execute(
                "SELECT start_line,end_line,source_path,content FROM sections WHERE document_id=? ORDER BY ordinal",
                (f"reference:{reference_id}",),
            ).fetchall()
            self.assertTrue(any(row[0] == 2 and row[1] == 2 and "one based" in row[3] for row in rows))
            self.assertTrue(all(row[2] == str(archived) for row in rows))
        finally:
            connection.close()
        agent = sqlite3.connect(output / "agent-index.sqlite")
        try:
            self.assertEqual(agent.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            agent.close()
        maintained = invoke("maintain", "--out", str(output))
        self.assertEqual(maintained.returncode, 0, maintained.stdout + maintained.stderr)

        unrelated_source = self.root / "unrelated.txt"
        unrelated_source.write_text(
            "Unrelated reference remains after targeted PDF rollback.\n",
            encoding="utf-8",
        )
        unrelated_ingest = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(unrelated_source),
            "--title", "不相关文本资料", "--origin", "本地文本 fixture", "--license", "CC0-1.0",
        )
        self.assertEqual(unrelated_ingest.returncode, 4, unrelated_ingest.stderr)
        unrelated_result = json.loads(unrelated_ingest.stdout)
        unrelated_review = json.loads(Path(unrelated_result["review_template"]).read_text(encoding="utf-8"))
        unrelated_review.update(
            {
                "status": "agent-reviewed",
                "summary_zh": "这份独立文本资料用于证明 PDF 定向回滚不会删除其他参考来源。",
                "claims": [
                    {
                        "claim_zh": "资料明确说明定向 PDF 回滚后该来源仍然保留。",
                        "start_line": 1,
                        "end_line": 1,
                        "source_text": "Unrelated reference remains after targeted PDF rollback.",
                        "evidence_note": "已重新打开归档文本第一行并逐字核对该回滚边界。",
                    }
                ],
            }
        )
        unrelated_review_path = self.root / "unrelated-review.json"
        unrelated_review_path.write_text(json.dumps(unrelated_review, ensure_ascii=False, indent=2), encoding="utf-8")
        unrelated_reviewed = invoke(
            "reference", "review", "--out", str(output), "--review", str(unrelated_review_path)
        )
        self.assertEqual(unrelated_reviewed.returncode, 0, unrelated_reviewed.stderr)
        unrelated_human = output / "human/references/不相关文本资料.md"
        self.assertTrue(unrelated_human.is_file())

        extraction_root = extraction_path.parent
        rolled = invoke("reference", "rollback", "--out", str(output), "--reference", reference_id)
        self.assertEqual(rolled.returncode, 0, rolled.stderr)
        self.assertFalse(archived.exists())
        self.assertFalse(manifest_path.exists())
        self.assertFalse(extraction_root.exists())
        self.assertFalse(human.exists())
        self.assertFalse(markdown.exists())
        self.assertTrue(unrelated_human.is_file())
        final_audit = json.loads(invoke("reference", "audit", "--out", str(output)).stdout)
        self.assertEqual(final_audit["status"], "passed")
        self.assertEqual(final_audit["counts"]["total"], 1)
        self.assertEqual(final_audit["counts"]["active"], 1)
        final_connection = sqlite3.connect(output / "machine/knowledge.sqlite")
        try:
            self.assertEqual(final_connection.execute("SELECT count(*) FROM entities").fetchone()[0], baseline_entity_count)
            self.assertEqual(final_connection.execute("SELECT count(*) FROM reference_sources").fetchone()[0], 1)
        finally:
            final_connection.close()


if __name__ == "__main__":
    unittest.main()
