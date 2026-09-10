#!/usr/bin/env python3
"""Measure real OCR fidelity through the reference-ingest PDF path."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from ckb_core.reference_pdf import PdfExtractionError, extract_pdf, inspect_pdf, validate_pdf_extraction
from test_ckb import invoke, make_repo, review_all


FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "reference-pdf-ocr"
ADAPTER = ROOT / "tests" / "real_ocr_adapter.py"
EMPTY_ADAPTER = FIXTURE_ROOT / "adapters" / "empty_ocr_adapter.py"
SLOW_ADAPTER = FIXTURE_ROOT / "adapters" / "slow_ocr_adapter.py"


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


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        [os.environ.get("CKB_GIT", "git"), "-C", str(ROOT), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"git {' '.join(arguments)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _pdftoppm_version() -> str:
    configured = os.environ.get("CKB_PDFTOPPM", "").strip()
    command = configured or shutil.which("pdftoppm")
    if not command:
        return "missing"
    completed = subprocess.run(
        [command, "-v"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    observed = completed.stdout + completed.stderr
    match = re.search(r"pdftoppm version ([^\s]+)", observed)
    return match.group(1) if completed.returncode == 0 and match else "unrecognized"


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("丨", "|")
    return re.sub(r"\s+", "", value)


def _ratio(passed: int, total: int) -> float:
    return round(passed / total, 6) if total else 0.0


def _page_text(extraction: dict[str, Any], page_number: int) -> str:
    page = extraction["pages"][page_number - 1]
    return Path(page["text_file"]).read_text(encoding="utf-8")


def _portable_page(page: dict[str, Any]) -> dict[str, Any]:
    ocr = page["ocr"]
    return {
        "page_number": page["page_number"],
        "status": page["status"],
        "method": page["method"],
        "confidence": page["confidence"],
        "reason": page["reason"],
        "text": Path(page["text_file"]).read_text(encoding="utf-8"),
        "text_sha256": page["text_sha256"],
        "ocr": {
            "status": ocr.get("status"),
            "confidence_score": ocr.get("confidence_score"),
            "output_sha256": ocr.get("output_sha256"),
            "metadata": ocr.get("metadata", {}),
        },
        "fragments": [
            {
                "structure": fragment["structure"],
                "structure_confidence": fragment["structure_confidence"],
                "warnings": fragment["warnings"],
                "text": fragment["text"],
                "page_number": fragment["page_number"],
            }
            for fragment in page["fragments"]
        ],
    }


def _completed_output(root: Path) -> Path:
    repository = make_repo(root)
    output = root / "output"
    initialized = invoke("init", "--repo", str(repository), "--out", str(output), "--format", "markdown")
    if initialized.returncode:
        raise RuntimeError(f"CKB init failed ({initialized.returncode}): {initialized.stderr.strip()}")
    review_all(output)
    merged = invoke("merge", "--out", str(output))
    if merged.returncode:
        raise RuntimeError(f"CKB merge failed ({merged.returncode}): {merged.stderr.strip()}")
    finalized = invoke("finalize", "--out", str(output))
    if finalized.returncode:
        raise RuntimeError(f"CKB finalize failed ({finalized.returncode}): {finalized.stderr.strip()}")
    return output


def _ingest(output: Path, source: Path, title: str, *, use_ocr: bool) -> dict[str, Any]:
    arguments = [
        "reference",
        "ingest",
        "--out",
        str(output),
        "--source",
        str(source),
        "--source-root",
        str(FIXTURE_ROOT),
        "--title",
        title,
        "--origin",
        "CKB 冻结 OCR fixture",
        "--license",
        "CC0-1.0",
    ]
    if use_ocr:
        arguments.extend(
            [
                "--pdf-ocr",
                "--pdf-ocr-adapter",
                str(ADAPTER),
                "--pdf-ocr-max-pages",
                "2",
                "--pdf-ocr-timeout-seconds",
                "60",
            ]
        )
    completed = invoke(*arguments)
    if completed.returncode != 4:
        raise RuntimeError(
            f"reference ingest returned {completed.returncode}; stdout={completed.stdout.strip()}; "
            f"stderr={completed.stderr.strip()}"
        )
    result = json.loads(completed.stdout)
    manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    extraction = json.loads(Path(manifest["extraction_file"]).read_text(encoding="utf-8"))
    reopened, errors = validate_pdf_extraction(output, manifest, require_ready=True)
    if reopened is None:
        raise RuntimeError("reference PDF extraction did not reopen")
    archived = Path(result["source"])
    return {
        "command": "reference ingest",
        "input": source.relative_to(ROOT).as_posix(),
        "ocr_enabled": use_ocr,
        "exit_status": completed.returncode,
        "reference_id": result["reference_id"],
        "source_sha256": _sha256(source),
        "archived_source_sha256": _sha256(archived),
        "audit_errors": errors,
        "status": extraction["status"],
        "page_count": extraction["page_count"],
        "pages": [_portable_page(page) for page in extraction["pages"]],
    }


@contextlib.contextmanager
def _environment(name: str, value: str) -> Iterator[None]:
    original = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if original is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = original


def _diagnostics(root: Path, scanned: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    child_path = os.pathsep.join([str(ROOT / "scripts"), str(ROOT / "tests")])
    with _environment("PYTHONPATH", child_path):
        missing = extract_pdf(
            scanned,
            "diagnostic-missing-tool",
            root / "missing-tool",
            ocr_enabled=True,
            ocr_adapter=ADAPTER,
            ocr_max_pages=1,
            ocr_timeout_seconds=10,
        )
    missing_ocr = missing["pages"][0]["ocr"]
    cases.append(
        {
            "case": "ocr-tool-missing",
            "expected_reason": "ocr-adapter-failed",
            "observed_reason": missing["pages"][0]["reason"],
            "stderr_contains": "ocr-tool-missing: rapidocr_onnxruntime",
            "stderr": missing_ocr.get("stderr", ""),
            "matched": missing["pages"][0]["reason"] == "ocr-adapter-failed"
            and "ocr-tool-missing: rapidocr_onnxruntime" in missing_ocr.get("stderr", ""),
        }
    )

    timed_out = extract_pdf(
        scanned,
        "diagnostic-timeout",
        root / "timeout",
        ocr_enabled=True,
        ocr_adapter=SLOW_ADAPTER,
        ocr_max_pages=1,
        ocr_timeout_seconds=1,
    )
    cases.append(
        {
            "case": "ocr-timeout",
            "expected_reason": "ocr-timeout",
            "observed_reason": timed_out["pages"][0]["reason"],
            "matched": timed_out["pages"][0]["reason"] == "ocr-timeout",
        }
    )

    empty = extract_pdf(
        scanned,
        "diagnostic-empty-output",
        root / "empty-output",
        ocr_enabled=True,
        ocr_adapter=EMPTY_ADAPTER,
        ocr_max_pages=1,
        ocr_timeout_seconds=5,
    )
    cases.append(
        {
            "case": "ocr-empty-output",
            "expected_reason": "ocr-text-below-usable-threshold",
            "observed_reason": empty["pages"][0]["reason"],
            "output_sha256": empty["pages"][0]["ocr"].get("output_sha256"),
            "matched": empty["pages"][0]["reason"] == "ocr-text-below-usable-threshold",
        }
    )

    bounded = extract_pdf(
        scanned,
        "diagnostic-page-limit",
        root / "page-limit",
        ocr_enabled=True,
        ocr_adapter=EMPTY_ADAPTER,
        ocr_max_pages=1,
        ocr_timeout_seconds=5,
    )
    cases.append(
        {
            "case": "ocr-page-limit",
            "expected_reason": "ocr-page-limit",
            "observed_reason": bounded["pages"][1]["reason"],
            "attempted_pages": bounded["ocr"]["attempted_pages"],
            "matched": bounded["pages"][1]["reason"] == "ocr-page-limit"
            and bounded["ocr"]["attempted_pages"] == 1,
        }
    )

    corrupt = root / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF-1.7\ntruncated")
    try:
        inspect_pdf(corrupt, 1024, 10)
    except PdfExtractionError as exc:
        observed = str(exc)
    else:
        observed = "no-error"
    cases.append(
        {
            "case": "corrupt-pdf",
            "expected_reason": "corrupt or unsupported PDF source",
            "observed_reason": observed,
            "matched": "corrupt or unsupported PDF source" in observed,
        }
    )
    return cases


def _content_targets(ground_truth: dict[str, Any]) -> dict[int, list[str]]:
    first, second = ground_truth["pages"]
    page_one = [first["header"], first["title"], first["body"], *first["code_lines"], first["footer"]]
    table_cells = [
        "模块 Module",
        "状态 Status",
        "说明 Note",
        "parser",
        "READY",
        *second["wrapped_cell"],
        "ocr",
        "CHECK",
        "code + table",
        "trace",
        "PASS",
        "source-page=2",
    ]
    return {1: page_one, 2: [second["header"], second["title"], *table_cells, second["footer"]]}


def _code_metrics(scanned: dict[str, Any], expected: list[str]) -> dict[str, Any]:
    page = scanned["pages"][0]
    fragment = next(item for item in page["fragments"] if item["structure"] == "code")
    observed = fragment["text"].splitlines()
    common = min((len(line) - len(line.lstrip(" ")) for line in observed if line.strip()), default=0)
    observed = [line[common:] for line in observed]
    exact = [actual == wanted for actual, wanted in zip(observed, expected)]
    alphabet = set("()[]{}:=,\"'_+-*/")
    symbol_checks = [
        "".join(character for character in actual if character in alphabet)
        == "".join(character for character in wanted if character in alphabet)
        for actual, wanted in zip(observed, expected)
    ]
    indentation = [len(line) - len(line.lstrip(" ")) for line in observed]
    expected_indentation = [len(line) - len(line.lstrip(" ")) for line in expected]
    return {
        "expected_lines": expected,
        "observed_lines": observed,
        "exact_line_recall": _ratio(sum(exact), len(expected)),
        "symbol_sequence_accuracy": _ratio(sum(symbol_checks), len(expected)),
        "indentation_accuracy": _ratio(
            sum(actual == wanted for actual, wanted in zip(indentation, expected_indentation)),
            len(expected_indentation),
        ),
        "observed_indentation": indentation,
        "expected_indentation": expected_indentation,
    }


def _table_metrics(scanned: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    page = scanned["pages"][1]
    text = page["text"]
    lines = text.splitlines()
    expected_cells = _content_targets(ground_truth)[2][2:-1]
    normalized_page = _normalize(text)
    cell_checks = {cell: _normalize(cell) in normalized_page for cell in expected_cells}
    row_markers = [("parser", ["parser", "READY", "保留页码"]), ("ocr", ["ocr", "CHECK", "code + table"]), ("trace", ["trace", "PASS", "source-page=2"])]
    row_checks: list[dict[str, Any]] = []
    row_indexes: list[int] = []
    for marker, cells in row_markers:
        index = next(
            (
                offset
                for offset, line in enumerate(lines)
                if _normalize(marker) in _normalize(line) and _normalize(cells[1]) in _normalize(line)
            ),
            -1,
        )
        row_indexes.append(index)
        normalized_line = _normalize(lines[index]) if index >= 0 else ""
        positions = [normalized_line.find(_normalize(cell)) for cell in cells]
        row_checks.append(
            {
                "marker": marker,
                "line_index": index,
                "cells": cells,
                "same_line": all(position >= 0 for position in positions),
                "column_order": all(left < right for left, right in zip(positions, positions[1:])),
            }
        )
    parser_index = row_indexes[0]
    continuation_index = next((index for index, line in enumerate(lines) if _normalize("page 2") in _normalize(line)), -1)
    wrapped_continuation = (
        parser_index >= 0
        and continuation_index == parser_index + 1
        and len(lines[continuation_index]) - len(lines[continuation_index].lstrip(" "))
        > lines[parser_index].casefold().find("ready")
    )
    structures = [fragment["structure"] for fragment in page["fragments"]]
    return {
        "cell_recall": _ratio(sum(cell_checks.values()), len(cell_checks)),
        "cell_checks": cell_checks,
        "row_alignment_accuracy": _ratio(sum(item["same_line"] for item in row_checks), len(row_checks)),
        "column_order_accuracy": _ratio(sum(item["column_order"] for item in row_checks), len(row_checks)),
        "wrapped_cell_continuation": wrapped_continuation,
        "table_fragment_detected": "table" in structures,
        "row_checks": row_checks,
        "fragment_structures": structures,
    }


def score(ingests: dict[str, dict[str, Any]], ground_truth: dict[str, Any]) -> dict[str, Any]:
    scanned = ingests["scanned"]
    targets = _content_targets(ground_truth)
    text_checks: list[dict[str, Any]] = []
    for page_number, expected in targets.items():
        observed = scanned["pages"][page_number - 1]["text"]
        normalized = _normalize(observed)
        for item in expected:
            text_checks.append(
                {"page_number": page_number, "expected": item, "matched": _normalize(item) in normalized}
            )
    code = _code_metrics(scanned, ground_truth["pages"][0]["code_lines"])
    table = _table_metrics(scanned, ground_truth)
    locator_markers = {1: "normalize(items)", 2: "source-page=2"}
    locator_checks = []
    for expected_page, marker in locator_markers.items():
        matches = [
            page["page_number"]
            for page in scanned["pages"]
            if _normalize(marker) in _normalize(page["text"])
        ]
        locator_checks.append(
            {"marker": marker, "expected_page": expected_page, "observed_pages": matches, "matched": matches == [expected_page]}
        )
    hybrid_methods = [page["method"] for page in ingests["hybrid"]["pages"]]
    return {
        "text_coverage": {
            "matched_items": sum(item["matched"] for item in text_checks),
            "expected_items": len(text_checks),
            "recall": _ratio(sum(item["matched"] for item in text_checks), len(text_checks)),
            "checks": text_checks,
        },
        "code_fidelity": code,
        "table_structure": table,
        "source_page_locator": {
            "accuracy": _ratio(sum(item["matched"] for item in locator_checks), len(locator_checks)),
            "checks": locator_checks,
            "hybrid_expected_methods": ["native", "ocr"],
            "hybrid_observed_methods": hybrid_methods,
            "hybrid_methods_match": hybrid_methods == ["native", "ocr"],
        },
    }


def _quality_evaluations(metrics: dict[str, Any], gates: dict[str, Any]) -> dict[str, bool]:
    return {
        "text_coverage": metrics["text_coverage"]["recall"] >= gates["text_coverage_min"],
        "code_exact_lines": metrics["code_fidelity"]["exact_line_recall"] >= gates["code_exact_line_recall_min"],
        "code_symbols": metrics["code_fidelity"]["symbol_sequence_accuracy"] >= gates["code_symbol_accuracy_min"],
        "code_indentation": metrics["code_fidelity"]["indentation_accuracy"] >= gates["code_indentation_accuracy_min"],
        "table_cells": metrics["table_structure"]["cell_recall"] >= gates["table_cell_recall_min"],
        "table_rows": metrics["table_structure"]["row_alignment_accuracy"] >= gates["table_row_alignment_min"],
        "table_columns": metrics["table_structure"]["column_order_accuracy"] >= gates["table_column_order_min"],
        "table_wrapped_cell": metrics["table_structure"]["wrapped_cell_continuation"] is gates["table_wrapped_cell"],
        "table_fragment": metrics["table_structure"]["table_fragment_detected"] is gates["table_fragment_detected"],
        "source_page_locator": metrics["source_page_locator"]["accuracy"] >= gates["source_page_locator_min"],
        "hybrid_methods": metrics["source_page_locator"]["hybrid_methods_match"] is gates["hybrid_methods_match"],
    }


def run_benchmark(protocol_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema_version") != 1 or protocol.get("status") != "frozen":
        raise ValueError("OCR benchmark protocol must be frozen schema version 1")
    ground_truth_path = ROOT / protocol["fixture_manifest"]
    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    fixture_checks = {
        "ground_truth_sha256": _sha256(ground_truth_path) == protocol["fixture_manifest_sha256"],
        "documents": all(
            _sha256(FIXTURE_ROOT / value["path"]) == value["sha256"]
            for value in ground_truth["documents"].values()
        ),
        "declared_documents": all(
            ground_truth["documents"][name]["sha256"] == value
            for name, value in protocol["fixture_sha256"].items()
        ),
    }
    implementation_checks = {
        "baseline_commit": _git("merge-base", "--is-ancestor", protocol["baseline_commit"], "HEAD") == "",
        "implementation_sha256": _sha256(ROOT / protocol["implementation_path"])
        == protocol["implementation_sha256"],
        "adapter_sha256": _sha256(ROOT / protocol["adapter_path"]) == protocol["adapter_sha256"],
    }
    runtime = {
        "python": sys.version.split()[0],
        "pypdf": importlib.metadata.version("pypdf"),
        "rapidocr_onnxruntime": importlib.metadata.version("rapidocr-onnxruntime"),
        "onnxruntime": importlib.metadata.version("onnxruntime"),
        "pdftoppm": _pdftoppm_version(),
    }
    runtime_checks = {name: runtime[name] == value for name, value in protocol["runtime"].items()}

    with tempfile.TemporaryDirectory(prefix="ckb-real-ocr-benchmark-") as directory:
        temporary = Path(directory)
        output = _completed_output(temporary)
        ingests = {
            "native": _ingest(
                output,
                FIXTURE_ROOT / ground_truth["documents"]["native"]["path"],
                "原生 PDF OCR 对照",
                use_ocr=False,
            ),
            "scanned": _ingest(
                output,
                FIXTURE_ROOT / ground_truth["documents"]["scanned"]["path"],
                "纯扫描 PDF OCR 基准",
                use_ocr=True,
            ),
            "hybrid": _ingest(
                output,
                FIXTURE_ROOT / ground_truth["documents"]["hybrid"]["path"],
                "原生与扫描混合 PDF OCR 基准",
                use_ocr=True,
            ),
        }
        diagnostics = _diagnostics(temporary / "diagnostics", FIXTURE_ROOT / ground_truth["documents"]["scanned"]["path"])
        metrics = score(ingests, ground_truth)

    expected_modes = {
        "native": ["native", "native"],
        "scanned": ["ocr", "ocr"],
        "hybrid": ["native", "ocr"],
    }
    ingest_checks = {
        name: {
            "exit_status_4": ingest["exit_status"] == 4,
            "source_copy_exact": ingest["source_sha256"] == ingest["archived_source_sha256"],
            "audit_passed": ingest["audit_errors"] == [],
            "status_ready": ingest["status"] == "ready",
            "methods_match": [page["method"] for page in ingest["pages"]] == expected_modes[name],
        }
        for name, ingest in ingests.items()
    }
    quality = _quality_evaluations(metrics, protocol["quality_gates"])
    diagnostic_checks = {item["case"]: item["matched"] for item in diagnostics}
    contract_failures = [
        f"fixture.{name}" for name, passed in fixture_checks.items() if not passed
    ] + [
        f"implementation.{name}" for name, passed in implementation_checks.items() if not passed
    ] + [
        f"runtime.{name}" for name, passed in runtime_checks.items() if not passed
    ] + [
        f"ingest.{name}.{check}"
        for name, values in ingest_checks.items()
        for check, passed in values.items()
        if not passed
    ] + [
        f"diagnostic.{name}" for name, passed in diagnostic_checks.items() if not passed
    ]
    quality_failures = [name for name, passed in quality.items() if not passed]
    raw = {
        "schema_version": 1,
        "status": "measured",
        "benchmark": protocol["benchmark"],
        "measured_at_utc": protocol["measured_at_utc"],
        "source_commit": _git("rev-parse", "HEAD"),
        "runtime": runtime,
        "bindings": {
            "fixture": fixture_checks,
            "implementation": implementation_checks,
            "runtime": runtime_checks,
        },
        "ingests": ingests,
        "ingest_checks": ingest_checks,
        "metrics": metrics,
        "quality_gate_evaluations": quality,
        "diagnostics": diagnostics,
        "diagnostic_checks": diagnostic_checks,
        "contract_failures": contract_failures,
        "quality_gate_failures": quality_failures,
    }
    report = {
        "schema_version": 1,
        "status": "measured",
        "benchmark": protocol["benchmark"],
        "measured_at_utc": protocol["measured_at_utc"],
        "source_commit": raw["source_commit"],
        "runtime": runtime,
        "fixture_kinds": ground_truth["kind_evidence"],
        "reference_ingest": ingest_checks,
        "metrics": metrics,
        "quality_gate_evaluations": quality,
        "diagnostics": diagnostics,
        "contract_failures": contract_failures,
        "quality_gate_failures": quality_failures,
        "boundary_zh": "RapidOCR 与 Poppler 仅用于本次可选基准环境，未写入 CKB 默认依赖；结果按文本覆盖、代码保真、表格结构和来源页定位分别报告。",
    }
    return raw, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    arguments = parser.parse_args(argv)
    raw, report = run_benchmark(arguments.protocol.resolve())
    _write_json(arguments.raw.resolve(), raw)
    _write_json(arguments.report.resolve(), report)
    failures = report["contract_failures"] + report["quality_gate_failures"]
    print(
        json.dumps(
            {
                "status": report["status"],
                "raw": str(arguments.raw.resolve()),
                "report": str(arguments.report.resolve()),
                "contract_failures": report["contract_failures"],
                "quality_gate_failures": report["quality_gate_failures"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
