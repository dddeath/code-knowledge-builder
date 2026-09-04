#!/usr/bin/env python3
"""运行冻结的原生 PDF 效果对照，不调用 Web 或真实 OCR。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from ckb_core.reference_inputs import web_input_adapter_contract
from ckb_core.reference_pdf import PdfExtractionError, _load_pypdf, extract_pdf, inspect_pdf
from pdf_fixture_factory import ascii_pdf, blank_pdf, chinese_pdf, encrypt_pdf


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)
    if path.read_bytes() != data:
        raise RuntimeError(f"reopened JSON differs: {path}")


def _git(git: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [git, *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def _commands(*rows: tuple[float, float, str]) -> list[tuple[float, float, str]]:
    return list(rows)


def _ratio(passed: int, total: int) -> float:
    return round(passed / total, 10) if total else 0.0


def _runtime_parser_identity() -> dict[str, str | None]:
    module = _load_pypdf()
    module_name = str(getattr(module, "__name__", ""))
    distribution_name = module_name.split(".", 1)[0]
    try:
        distribution_version = importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        distribution_version = None
    return {
        "module_name": module_name,
        "module_version": str(getattr(module, "__version__", "")) or None,
        "distribution_name": distribution_name,
        "distribution_version": distribution_version,
    }


def _parser_identity_matches(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    name = expected.get("name")
    version = expected.get("version")
    return (
        actual.get("module_name") == name
        and actual.get("distribution_name") == name
        and actual.get("module_version") == version
        and actual.get("distribution_version") == version
    )


def _capture_diagnostic(
    diagnostic_id: str,
    operation: Callable[[], object],
    expected_fragment: str,
) -> dict[str, Any]:
    try:
        operation()
    except PdfExtractionError as exc:
        observed = str(exc)
        return {
            "diagnostic_id": diagnostic_id,
            "expected_fragment": expected_fragment,
            "observed": observed,
            "passed": expected_fragment in observed,
        }
    return {
        "diagnostic_id": diagnostic_id,
        "expected_fragment": expected_fragment,
        "observed": "no-error",
        "passed": False,
    }


def summarize(raw: dict[str, Any]) -> dict[str, Any]:
    metrics = raw["metrics"]
    checks = raw["checks"]
    gates = raw["protocol_gates"]
    exact = {
        "baseline_feature_absent": checks["baseline_feature_absent"] is gates["baseline_feature_absent"],
        "current_implementation_matches_snapshot": checks["current_implementation_matches_snapshot"]
        is gates["current_implementation_matches_snapshot"],
        "parser_identity_matches_protocol": checks["parser_identity_matches_protocol"]
        is gates["parser_identity_matches_protocol"],
        "page_locator_accuracy": metrics["page_locator_accuracy"] == gates["page_locator_accuracy"],
        "unicode_line_recall": metrics["unicode_line_recall"] == gates["unicode_line_recall"],
        "code_line_accuracy": metrics["code_line_accuracy"] == gates["code_line_accuracy"],
        "code_indent_accuracy": metrics["code_indent_accuracy"] == gates["code_indent_accuracy"],
        "table_line_accuracy": metrics["table_line_accuracy"] == gates["table_line_accuracy"],
        "diagnostic_accuracy": metrics["diagnostic_accuracy"] == gates["diagnostic_accuracy"],
        "web_implementation_status": raw["web"]["implementation_status"] == gates["web_implementation_status"],
        "real_ocr_calls": raw["coverage"]["real_ocr_calls"] == gates["real_ocr_calls"],
    }
    status = "passed" if all(exact.values()) else "failed"
    return {
        "schema_version": 1,
        "status": status,
        "benchmark": raw["benchmark"],
        "baseline_commit": raw["baseline"]["commit"],
        "feature_merge_commit": raw["feature_merge_commit"],
        "current_source_commit": raw["current"]["source_commit"],
        "parser_identity": raw["current"]["parser"],
        "checks": exact,
        "metrics": metrics,
        "effect": {
            "native_pdf": "已证实增强" if status == "passed" else "证据不足",
            "pdf_web_ocr_combined_gap": "证据不足",
            "reason_zh": "旧基线没有页级 PDF 提取模块；当前固定样例的页码、中文、代码缩进、表格和诊断全部命中。Web 仍未实现，真实 OCR 调用为零。",
        },
        "coverage": raw["coverage"],
    }


def run_benchmark(protocol_path: Path, git: str) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema_version") != 1 or protocol.get("status") != "frozen":
        raise ValueError("PDF benchmark protocol must be frozen schema version 1")

    implementation = str(protocol["implementation_path"])
    baseline_commit = str(protocol["baseline_commit"])
    current_commit = str(protocol["current_source_commit"])
    expected_parser = dict(protocol["parser"])
    actual_parser = _runtime_parser_identity()
    parser_identity_matches = _parser_identity_matches(expected_parser, actual_parser)
    baseline_probe = _git(git, "cat-file", "-e", f"{baseline_commit}:{implementation}")
    snapshot_blob = _git(git, "rev-parse", f"{current_commit}:{implementation}")
    working_blob = _git(git, "hash-object", str(ROOT / implementation))
    if snapshot_blob.returncode != 0 or working_blob.returncode != 0:
        raise RuntimeError("could not bind current PDF implementation blob")

    with tempfile.TemporaryDirectory(prefix="ckb-pdf-effect-") as directory:
        temporary = Path(directory)
        layout_pdf = ascii_pdf(
            temporary / "layout.pdf",
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
        layout = extract_pdf(layout_pdf, "benchmark-layout", temporary / "layout-extraction")
        page_texts = [Path(page["text_file"]).read_text(encoding="utf-8") for page in layout["pages"]]

        page_checks = [
            {"page_number": page, "marker": marker, "passed": marker in page_texts[page - 1]}
            for page, marker in protocol["layout_case"]["page_markers"]
        ]
        code_lines = list(protocol["layout_case"]["code_lines"])
        table_lines = list(protocol["layout_case"]["table_lines"])
        code_checks = [{"line": line, "passed": line in page_texts[0]} for line in code_lines]
        table_checks = [{"line": line, "passed": line in page_texts[0]} for line in table_lines]
        indented = next(line for line in code_lines if line.startswith("    "))
        code_indent_check = {
            "line": indented,
            "leading_spaces_expected": 4,
            "passed": any(line == indented for line in page_texts[0].splitlines()),
        }

        unicode_pdf = chinese_pdf(temporary / "unicode.pdf", protocol["unicode_case"]["expected_lines"])
        unicode_result = extract_pdf(unicode_pdf, "benchmark-unicode", temporary / "unicode-extraction")
        unicode_text = Path(unicode_result["pages"][0]["text_file"]).read_text(encoding="utf-8")
        unicode_checks = [
            {"line": line, "passed": line in unicode_text}
            for line in protocol["unicode_case"]["expected_lines"]
        ]

        blank = blank_pdf(temporary / "blank.pdf")
        blank_result = extract_pdf(blank, "benchmark-blank", temporary / "blank-extraction")
        no_adapter = extract_pdf(
            blank,
            "benchmark-no-adapter",
            temporary / "no-adapter-extraction",
            ocr_enabled=True,
        )
        invalid_header = temporary / "invalid-header.pdf"
        invalid_header.write_bytes(b"NOT-PDF")
        corrupt = temporary / "corrupt.pdf"
        corrupt.write_bytes(b"%PDF-1.7\ntruncated")
        plain = ascii_pdf(
            temporary / "plain.pdf",
            [[(72, 740, "This native PDF has enough text to be encrypted for a failure fixture.")]],
        )
        encrypted = encrypt_pdf(plain, temporary / "encrypted.pdf", _load_pypdf())
        multi = blank_pdf(temporary / "multi.pdf", page_count=2)
        diagnostics = [
            {
                "diagnostic_id": "blank-native-page",
                "expected_fragment": "native-text-below-usable-threshold",
                "observed": blank_result["pages"][0]["reason"],
                "passed": blank_result["pages"][0]["reason"] == "native-text-below-usable-threshold",
            },
            {
                "diagnostic_id": "missing-ocr-adapter",
                "expected_fragment": "ocr-adapter-not-configured",
                "observed": no_adapter["pages"][0]["reason"],
                "passed": no_adapter["pages"][0]["reason"] == "ocr-adapter-not-configured",
            },
            _capture_diagnostic(
                "invalid-pdf-header", lambda: inspect_pdf(invalid_header, 1024, 10), "does not start with a PDF header"
            ),
            _capture_diagnostic(
                "corrupt-pdf", lambda: inspect_pdf(corrupt, 1024, 10), "corrupt or unsupported PDF source"
            ),
            _capture_diagnostic(
                "encrypted-pdf", lambda: inspect_pdf(encrypted, 1024 * 1024, 10), "encrypted PDF sources"
            ),
            _capture_diagnostic("pdf-byte-limit", lambda: inspect_pdf(plain, 10, 10), "must contain"),
            _capture_diagnostic("pdf-page-limit", lambda: inspect_pdf(multi, 1024 * 1024, 1), "exceeds limit"),
        ]

        raw = {
            "schema_version": 1,
            "status": "measured",
            "benchmark": protocol["benchmark"],
            "measured_at_utc": protocol["measured_at_utc"],
            "feature_merge_commit": protocol["feature_merge_commit"],
            "baseline": {
                "commit": baseline_commit,
                "implementation_path": implementation,
                "cat_file_exit": baseline_probe.returncode,
                "feature_present": baseline_probe.returncode == 0,
            },
            "current": {
                "source_commit": current_commit,
                "implementation_path": implementation,
                "snapshot_blob": snapshot_blob.stdout.strip(),
                "working_blob": working_blob.stdout.strip(),
                "parser": {
                    "expected": expected_parser,
                    "actual": actual_parser,
                    "extraction_manifest": layout["parser"],
                    "matches_protocol": parser_identity_matches,
                },
            },
            "checks": {
                "baseline_feature_absent": baseline_probe.returncode != 0,
                "current_implementation_matches_snapshot": snapshot_blob.stdout.strip() == working_blob.stdout.strip(),
                "parser_identity_matches_protocol": parser_identity_matches,
            },
            "observations": {
                "layout": {
                    "status": layout["status"],
                    "page_count": layout["page_count"],
                    "page_text_sha256": [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in page_texts],
                    "page_locator_checks": page_checks,
                    "code_checks": code_checks,
                    "code_indent_check": code_indent_check,
                    "table_checks": table_checks,
                },
                "unicode": {
                    "status": unicode_result["status"],
                    "text_sha256": hashlib.sha256(unicode_text.encode("utf-8")).hexdigest(),
                    "checks": unicode_checks,
                },
                "diagnostics": diagnostics,
            },
            "metrics": {
                "direct_pdf_capability": {"baseline": 0.0, "current": 1.0, "delta": 1.0},
                "page_locator_accuracy": _ratio(sum(item["passed"] for item in page_checks), len(page_checks)),
                "unicode_line_recall": _ratio(sum(item["passed"] for item in unicode_checks), len(unicode_checks)),
                "code_line_accuracy": _ratio(sum(item["passed"] for item in code_checks), len(code_checks)),
                "code_indent_accuracy": 1.0 if code_indent_check["passed"] else 0.0,
                "table_line_accuracy": _ratio(sum(item["passed"] for item in table_checks), len(table_checks)),
                "diagnostic_accuracy": _ratio(sum(item["passed"] for item in diagnostics), len(diagnostics)),
            },
            "web": web_input_adapter_contract(),
            "coverage": {
                "native_pdf_cases": 4,
                "diagnostic_cases": len(diagnostics),
                "real_ocr_calls": 0,
                "web_fetch_calls": 0,
                "boundary_zh": "本次只测原生 PDF 与已有失败分类；测试适配器不计作真实 OCR，Web 合同不计作抓取实现。",
            },
            "protocol_gates": protocol["gates"],
        }
        report = summarize(raw)
        raw["status"] = report["status"]
        return raw, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--git", default=os.environ.get("CKB_GIT", "git"))
    arguments = parser.parse_args(argv)
    raw, report = run_benchmark(arguments.protocol.resolve(), arguments.git)
    raw_path = arguments.raw.resolve()
    report_path = arguments.report.resolve()
    if report["status"] == "passed":
        _write_json(raw_path, raw)
        _write_json(report_path, report)
    failed_checks = [name for name, passed in report["checks"].items() if not passed]
    print(
        json.dumps(
            {
                "status": report["status"],
                "raw": str(raw_path),
                "report": str(report_path),
                "written": report["status"] == "passed",
                "failed_checks": failed_checks,
                "parser_identity": report["parser_identity"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
