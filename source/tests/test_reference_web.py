from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from test_ckb import invoke, make_repo, review_all

from ckb_core.common import CkbError
from ckb_core.reference_documents import ingest_reference, ingest_web_reference
from ckb_core.reference_inputs import (
    WebSnapshotError,
    fetch_web_snapshot,
    prepare_static_web_snapshot,
    web_input_adapter_contract,
)


HTML = """<!doctype html>
<html>
<head><style>.hidden { display:none }</style><script>window.secret='noise'</script></head>
<body>
<header>站点标题</header>
<nav>导航噪声</nav>
<main>
<h1>许可可追溯快照</h1>
<p>正文结论可由归档 HTML 的精确行范围复核。</p>
<div role="navigation">角色导航噪声</div>
</main>
<footer>页脚噪声</footer>
</body>
</html>
"""


class _FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/article")
            self.end_headers()
            return
        if self.path == "/json":
            payload = b'{"not":"html"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path == "/large":
            payload = ("<html><body><p>" + ("x" * 4096) + "</p></body></html>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path == "/slow":
            time.sleep(1.5)
            payload = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            payload = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("ETag", '"fixture-v1"')
            self.send_header("Set-Cookie", "fixture-secret=omitted")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass

    def log_message(self, _format: str, *_args: object) -> None:
        pass


class WebSnapshotInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-web-input-")
        self.root = Path(self.temp.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def _snapshot(self, content: bytes = HTML.encode("utf-8")) -> Path:
        path = self.root / "snapshot.html"
        path.write_bytes(content)
        return path

    def test_static_snapshot_has_no_network_and_preserves_boundaries(self) -> None:
        source = self._snapshot()
        prepared = prepare_static_web_snapshot(
            source,
            requested_url="https://example.test/start",
            final_url="https://example.test/article",
            retrieved_at_utc="2026-09-05T01:02:03+00:00",
            status_code=200,
            content_type="text/html; charset=utf-8",
            response_headers={"ETag": '"fixture-v1"', "Set-Cookie": "secret=omitted"},
        )
        provenance = prepared.provenance
        self.assertEqual(provenance["acquisition_mode"], "provided-static-snapshot")
        self.assertEqual(provenance["network_access"], "not-used")
        self.assertEqual(provenance["final_url"], "https://example.test/article")
        self.assertEqual(provenance["retrieved_at_utc"], "2026-09-05T01:02:03Z")
        self.assertEqual(provenance["raw_snapshot_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertIn("set-cookie", provenance["omitted_response_headers"])
        self.assertNotIn("set-cookie", provenance["response_headers"])

        extraction = prepared.extraction
        body = extraction["body_snapshot_text"]
        self.assertIn("许可可追溯快照", body)
        self.assertIn("正文结论可由归档 HTML", body)
        self.assertNotIn("window.secret", body)
        self.assertNotIn("导航噪声", body)
        self.assertNotIn("页脚噪声", body)
        self.assertEqual(extraction["body_boundary"], {"start_line": 4, "end_line": 13})
        self.assertEqual(
            extraction["body_snapshot_sha256"],
            hashlib.sha256(body.encode("utf-8")).hexdigest(),
        )
        reasons = {item["reason"] for item in extraction["excluded_regions"]}
        self.assertEqual(reasons, {"navigation-container", "navigation-role", "non-content-tag"})
        paragraph = next(item for item in extraction["fragments"] if item["structure"] == "p")
        self.assertEqual(paragraph["source_range"], {"start_line": 9, "end_line": 9})

    def test_static_snapshot_rejects_non_html_oversize_and_bad_encoding(self) -> None:
        source = self._snapshot()
        common = {
            "requested_url": "https://example.test/article",
            "final_url": "https://example.test/article",
            "retrieved_at_utc": "2026-09-05T01:02:03Z",
            "status_code": 200,
        }
        with self.assertRaisesRegex(WebSnapshotError, "must be HTML"):
            prepare_static_web_snapshot(source, content_type="application/json", **common)
        with self.assertRaisesRegex(WebSnapshotError, "exceeds max_response_bytes"):
            prepare_static_web_snapshot(source, content_type="text/html", max_response_bytes=32, **common)
        bad = self._snapshot(b"<html><body><p>\xff</p></body></html>")
        with self.assertRaisesRegex(WebSnapshotError, "does not match declared charset"):
            prepare_static_web_snapshot(bad, content_type="text/html; charset=utf-8", **common)
        with self.assertRaisesRegex(WebSnapshotError, "single-line"):
            prepare_static_web_snapshot(
                source,
                content_type="text/html; charset=utf-8",
                response_headers={"ETag": "fixture\r\ninjected: value"},
                **common,
            )

    def test_live_fetch_records_redirect_final_url_and_response_metadata(self) -> None:
        prepared = fetch_web_snapshot(f"{self.base_url}/redirect", timeout_seconds=3)
        provenance = prepared.provenance
        self.assertEqual(provenance["acquisition_mode"], "live-url-fetch")
        self.assertEqual(provenance["network_access"], "explicit")
        self.assertEqual(provenance["requested_url"], f"{self.base_url}/redirect")
        self.assertEqual(provenance["final_url"], f"{self.base_url}/article")
        self.assertEqual(provenance["status_code"], 200)
        self.assertEqual(len(provenance["redirect_chain"]), 1)
        self.assertEqual(provenance["redirect_chain"][0]["status_code"], 302)
        self.assertEqual(provenance["response_headers"]["etag"], ['"fixture-v1"'])
        self.assertIn("set-cookie", provenance["omitted_response_headers"])

    def test_live_fetch_rejects_non_html_timeout_oversize_and_network_unavailable(self) -> None:
        with self.assertRaisesRegex(WebSnapshotError, "must be HTML"):
            fetch_web_snapshot(f"{self.base_url}/json", timeout_seconds=3)
        with self.assertRaisesRegex(WebSnapshotError, "exceeds max_response_bytes"):
            fetch_web_snapshot(f"{self.base_url}/large", timeout_seconds=3, max_response_bytes=256)
        with self.assertRaisesRegex(WebSnapshotError, "timed out"):
            fetch_web_snapshot(f"{self.base_url}/slow", timeout_seconds=1)

        class _UnavailableOpener:
            def open(self, *_args: object, **_kwargs: object) -> object:
                raise URLError(OSError("fixture network unavailable"))

        with patch("ckb_core.reference_inputs.build_opener", return_value=_UnavailableOpener()):
            with self.assertRaisesRegex(WebSnapshotError, "network request failed"):
                fetch_web_snapshot("http://127.0.0.1:9/unavailable", timeout_seconds=1)

    def test_contract_keeps_local_and_live_modes_separate(self) -> None:
        contract = web_input_adapter_contract()
        self.assertEqual(contract["implementation_status"], "implemented")
        self.assertEqual(contract["input_modes"]["provided-static-snapshot"]["network_access"], "not-used")
        self.assertEqual(contract["input_modes"]["live-url-fetch"]["network_access"], "explicit-only")
        self.assertIn("output-still-requires-reference-ingest-and-agent-review", contract["boundary"])

    def test_default_local_ingest_does_not_switch_to_network_or_html(self) -> None:
        output = self.root / "minimal-output"
        (output / "human").mkdir(parents=True)
        (output / "markdown").mkdir()
        (output / "state.json").write_text("{}\n", encoding="utf-8")
        source = self._snapshot()
        with patch("ckb_core.reference_documents.fetch_web_snapshot") as fetch:
            with self.assertRaisesRegex(CkbError, "local UTF-8 .md/.txt file or a local .pdf"):
                ingest_reference(output, source, "默认本地导入", "本地 fixture", "CC0-1.0")
            fetch.assert_not_called()


class WebReferenceEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-web-e2e-")
        self.root = Path(self.temp.name)
        self.repo = make_repo(self.root)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
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

    def _static_ingest(self, output: Path, snapshot: Path, *extra: str, title: str = "网页快照资料", final_url: str = "https://example.test/article"):
        return invoke(
            "reference", "web-snapshot",
            "--out", str(output),
            "--snapshot", str(snapshot),
            "--source-root", str(self.root),
            "--requested-url", "https://example.test/start",
            "--final-url", final_url,
            "--retrieved-at", "2026-09-05T01:02:03Z",
            "--status-code", "200",
            "--content-type", "text/html; charset=utf-8",
            "--response-header", 'ETag:"fixture-v1"',
            "--title", title,
            "--origin", "显式提供的静态 HTTP 快照",
            "--license", "CC0-1.0",
            *extra,
        )

    def test_static_ingest_review_drift_duplicate_audit_and_rollback(self) -> None:
        output = self._completed_output()
        snapshot = self.root / "snapshot.html"
        snapshot.write_text(HTML, encoding="utf-8", newline="\n")

        ingested = self._static_ingest(output, snapshot)
        self.assertEqual(ingested.returncode, 4, ingested.stderr)
        result = json.loads(ingested.stdout)
        self.assertEqual(result["status"], "pending-agent-review")
        self.assertEqual(result["acquisition_mode"], "provided-static-snapshot")
        self.assertEqual(result["final_url"], "https://example.test/article")
        self.assertFalse((output / "human/references/网页快照资料.md").exists())

        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        extraction = json.loads(Path(manifest["extraction_file"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["input_adapter"], "web-snapshot-v1")
        self.assertEqual(manifest["source_sha256"], result["raw_snapshot_sha256"])
        self.assertEqual(manifest["body_snapshot_sha256"], result["body_snapshot_sha256"])
        self.assertEqual(manifest["web_capture"]["response_headers"]["etag"], ['"fixture-v1"'])
        self.assertGreaterEqual(len(extraction["excluded_regions"]), 4)

        repeated = self._static_ingest(output, snapshot)
        self.assertEqual(repeated.returncode, 4, repeated.stderr)
        repeated_result = json.loads(repeated.stdout)
        self.assertTrue(repeated_result["idempotent"])
        self.assertEqual(repeated_result["reference_id"], result["reference_id"])

        review = json.loads(Path(result["review_template"]).read_text(encoding="utf-8"))
        paragraph = next(item for item in extraction["fragments"] if item["structure"] == "p")
        start = paragraph["source_range"]["start_line"]
        end = paragraph["source_range"]["end_line"]
        archived_lines = Path(result["source"]).read_text(encoding="utf-8").splitlines()
        review.update(
            {
                "status": "agent-reviewed",
                "summary_zh": "该网页快照记录许可可追溯的静态正文，并保留精确来源行范围。",
                "claims": [
                    {
                        "claim_zh": "归档正文明确说明结论可以通过 HTML 行范围复核。",
                        "fragment_id": paragraph["fragment_id"],
                        "start_line": start,
                        "end_line": end,
                        "source_text": "\n".join(archived_lines[start - 1 : end]),
                        "evidence_note": "已重新打开归档 HTML，并核对正文片段及其精确行范围。",
                    }
                ],
            }
        )
        review_path = self.root / "web-review.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
        reviewed = invoke("reference", "review", "--out", str(output), "--review", str(review_path))
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        human = output / "human/references/网页快照资料.md"
        human_text = human.read_text(encoding="utf-8")
        self.assertIn("[最终 URL](https://example.test/article)", human_text)
        self.assertIn(f"原文第 {start} 行", human_text)
        self.assertIn("获取时间：2026-09-05T01:02:03Z", human_text)

        connection = sqlite3.connect(output / "machine/knowledge.sqlite")
        try:
            indexed = "\n".join(row[0] for row in connection.execute(
                "SELECT content FROM sections WHERE document_id=? ORDER BY start_line",
                (f"reference:{result['reference_id']}",),
            ))
        finally:
            connection.close()
        self.assertIn("正文结论可由归档 HTML", indexed)
        self.assertNotIn("导航噪声", indexed)
        self.assertNotIn("window.secret", indexed)

        drifted = self.root / "snapshot-drifted.html"
        drifted.write_text(HTML.replace("正文结论", "漂移后的正文结论"), encoding="utf-8", newline="\n")
        rejected_drift = self._static_ingest(output, drifted)
        self.assertEqual(rejected_drift.returncode, 2)
        self.assertIn("snapshot drift detected", rejected_drift.stderr)
        revision = self._static_ingest(output, drifted, "--revision-of", result["reference_id"])
        self.assertEqual(revision.returncode, 4, revision.stderr)
        revision_result = json.loads(revision.stdout)
        self.assertEqual(revision_result["revision"], 2)
        self.assertNotEqual(revision_result["body_snapshot_sha256"], result["body_snapshot_sha256"])
        rolled_revision = invoke("reference", "rollback", "--out", str(output), "--reference", revision_result["reference_id"])
        self.assertEqual(rolled_revision.returncode, 0, rolled_revision.stderr)

        duplicate = self._static_ingest(
            output,
            snapshot,
            title="同内容不同地址资料",
            final_url="https://mirror.example.test/article",
        )
        self.assertEqual(duplicate.returncode, 4, duplicate.stderr)
        duplicate_result = json.loads(duplicate.stdout)
        self.assertEqual(duplicate_result["duplicate_content_of"], result["reference_id"])
        rolled_duplicate = invoke("reference", "rollback", "--out", str(output), "--reference", duplicate_result["reference_id"])
        self.assertEqual(rolled_duplicate.returncode, 0, rolled_duplicate.stderr)

        body_snapshot = Path(result["extraction"]["body_snapshot"])
        baseline_body = body_snapshot.read_bytes()
        body_snapshot.write_bytes(baseline_body + b"drift")
        drift_audit = invoke("reference", "audit", "--out", str(output))
        self.assertEqual(drift_audit.returncode, 5)
        self.assertIn("reference-web-body-drift", drift_audit.stdout)
        body_snapshot.write_bytes(baseline_body)
        repaired_audit = invoke("reference", "audit", "--out", str(output))
        self.assertEqual(repaired_audit.returncode, 0, repaired_audit.stderr)

        rolled = invoke("reference", "rollback", "--out", str(output), "--reference", result["reference_id"])
        self.assertEqual(rolled.returncode, 0, rolled.stderr)
        self.assertFalse(human.exists())

    def test_explicit_live_fetch_and_network_failure_leave_existing_references_unchanged(self) -> None:
        output = self._completed_output()
        fetched = invoke(
            "reference", "web-fetch",
            "--out", str(output),
            "--url", f"{self.base_url}/redirect",
            "--timeout-seconds", "3",
            "--title", "实时抓取网页资料",
            "--origin", "显式实时 URL 抓取",
            "--license", "CC0-1.0",
        )
        self.assertEqual(fetched.returncode, 4, fetched.stderr)
        result = json.loads(fetched.stdout)
        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(result["acquisition_mode"], "live-url-fetch")
        self.assertEqual(result["final_url"], f"{self.base_url}/article")
        self.assertEqual(manifest["web_capture"]["redirect_chain"][0]["status_code"], 302)
        self.assertEqual(manifest["status"], "pending-agent-review")
        self.assertFalse((output / "human/references/实时抓取网页资料.md").exists())

        reference_root = output / "references"
        before = {
            path.relative_to(reference_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in reference_root.rglob("*")
            if path.is_file()
        }
        with patch(
            "ckb_core.reference_documents.fetch_web_snapshot",
            side_effect=WebSnapshotError("fixture network unavailable"),
        ):
            with self.assertRaisesRegex(WebSnapshotError, "network unavailable"):
                ingest_web_reference(
                    output,
                    "断网失败资料",
                    "显式实时 URL 抓取",
                    "CC0-1.0",
                    url="https://unavailable.example.test/article",
                )
        after = {
            path.relative_to(reference_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in reference_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)

        rolled = invoke("reference", "rollback", "--out", str(output), "--reference", result["reference_id"])
        self.assertEqual(rolled.returncode, 0, rolled.stderr)


if __name__ == "__main__":
    unittest.main()
