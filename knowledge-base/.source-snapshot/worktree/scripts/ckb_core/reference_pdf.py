"""Page-level native PDF extraction with an optional bounded OCR adapter."""

from __future__ import annotations

import importlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

from .common import CkbError, DependencyError, background_process_options, json_load, json_write, path_inside, sha256_file, stable_id, utc_now


PDF_EXTRACTION_SCHEMA_VERSION = 1
PDF_PARSER_NAME = "pypdf"
PDF_PARSER_VERSION = "6.16.2"
DEFAULT_MAX_PDF_BYTES = 32 * 1024 * 1024
DEFAULT_MAX_PDF_PAGES = 400
ABSOLUTE_MAX_PDF_BYTES = 256 * 1024 * 1024
ABSOLUTE_MAX_PDF_PAGES = 2000
DEFAULT_NATIVE_MIN_CHARACTERS = 12
DEFAULT_NATIVE_MIN_PRINTABLE_RATIO = 0.90
DEFAULT_OCR_MAX_PAGES = 12
DEFAULT_OCR_TIMEOUT_SECONDS = 30
DEFAULT_OCR_MAX_INPUT_BYTES = 16 * 1024 * 1024
ABSOLUTE_OCR_MAX_PAGES = 100
ABSOLUTE_OCR_TIMEOUT_SECONDS = 300
ABSOLUTE_OCR_MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_PAGE_TEXT_CHARACTERS = 2 * 1024 * 1024
MAX_DOCUMENT_TEXT_CHARACTERS = 16 * 1024 * 1024
MAX_OCR_OUTPUT_BYTES = 8 * 1024 * 1024
OCR_ADAPTER_SCHEMA_VERSION = 1


class PdfExtractionError(CkbError):
    """A deterministic PDF validation or extraction failure."""


def _load_pypdf():
    """Load the locked parser, permitting an isolated test/runtime staging path."""

    extra = os.environ.get("CKB_PDF_LIBRARY_PATH", "").strip()
    if extra:
        resolved = Path(extra).resolve()
        if not resolved.is_dir():
            raise DependencyError(f"CKB_PDF_LIBRARY_PATH is not a directory: {resolved}")
        value = str(resolved)
        if value not in sys.path:
            sys.path.insert(0, value)
    try:
        module = importlib.import_module(PDF_PARSER_NAME)
    except ModuleNotFoundError as exc:
        raise DependencyError(
            f"native PDF extraction requires locked {PDF_PARSER_NAME} {PDF_PARSER_VERSION}"
        ) from exc
    version = str(getattr(module, "__version__", ""))
    if version != PDF_PARSER_VERSION:
        raise DependencyError(
            f"native PDF extraction requires {PDF_PARSER_NAME} {PDF_PARSER_VERSION}; found {version or 'unknown'}"
        )
    return module


def _validate_positive_limit(name: str, value: int, absolute: int) -> int:
    if not isinstance(value, int) or value < 1 or value > absolute:
        raise CkbError(f"{name} must be within 1..{absolute}")
    return value


def validate_pdf_limits(max_bytes: int, max_pages: int) -> tuple[int, int]:
    return (
        _validate_positive_limit("PDF max bytes", max_bytes, ABSOLUTE_MAX_PDF_BYTES),
        _validate_positive_limit("PDF max pages", max_pages, ABSOLUTE_MAX_PDF_PAGES),
    )


def validate_ocr_limits(max_pages: int, timeout_seconds: int, max_input_bytes: int) -> tuple[int, int, int]:
    return (
        _validate_positive_limit("OCR max pages", max_pages, ABSOLUTE_OCR_MAX_PAGES),
        _validate_positive_limit("OCR timeout seconds", timeout_seconds, ABSOLUTE_OCR_TIMEOUT_SECONDS),
        _validate_positive_limit("OCR max input bytes", max_input_bytes, ABSOLUTE_OCR_MAX_INPUT_BYTES),
    )


def _normalized_layout_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [line.rstrip() for line in value.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _text_metrics(text: str) -> dict[str, Any]:
    nonspace = [character for character in text if not character.isspace()]
    printable = [character for character in nonspace if character.isprintable()]
    replacement = text.count("\ufffd")
    ratio = len(printable) / len(nonspace) if nonspace else 0.0
    return {
        "character_count": len(text),
        "nonspace_character_count": len(nonspace),
        "printable_ratio": round(ratio, 6),
        "replacement_character_count": replacement,
    }


def _usable_text(metrics: dict[str, Any], min_characters: int, min_printable_ratio: float) -> bool:
    return (
        int(metrics["nonspace_character_count"]) >= min_characters
        and float(metrics["printable_ratio"]) >= min_printable_ratio
        and int(metrics["replacement_character_count"]) <= max(1, int(metrics["nonspace_character_count"]) // 100)
    )


def _native_confidence(metrics: dict[str, Any]) -> str:
    if int(metrics["nonspace_character_count"]) >= 80 and float(metrics["printable_ratio"]) >= 0.99:
        return "high"
    return "medium"


_HEADING = re.compile(r"^(?:#{1,6}\s+|(?:\d+(?:\.\d+){0,4}|[A-Z])(?:[.)]|\s+-)\s*)?[^\n]{1,100}$")
_NUMBERED_HEADING = re.compile(r"^(?:\d+(?:\.\d+){1,4}|(?:chapter|section)\s+\d+)\s+\S", re.IGNORECASE)
_LIST_LINE = re.compile(r"^\s*(?:[-*+\u2022\u25cf\u25aa]|\d+[.)]|[A-Za-z][.)])\s+\S")
_CODE_SIGNAL = re.compile(r"(?:[{};]|\b(?:def|class|return|if|for|while|public|private|const|let|var|import|from)\b)")


def _classify_block(lines: list[str]) -> tuple[str, str, list[str]]:
    nonblank = [line for line in lines if line.strip()]
    warnings: list[str] = []
    if not nonblank:
        return "raw", "low", ["empty-block"]
    if all(_LIST_LINE.match(line) for line in nonblank):
        return "list", "high", warnings
    pipe_columns = [line.count("|") for line in nonblank]
    gap_columns = [len(re.findall(r"\S\s{2,}\S", line)) for line in nonblank]
    if len(nonblank) >= 2 and (min(pipe_columns) >= 2 or min(gap_columns) >= 1):
        return "table", "medium", ["layout-derived-table-boundary"]
    indented = sum(1 for line in nonblank if len(line) - len(line.lstrip(" ")) >= 4)
    signals = sum(1 for line in nonblank if _CODE_SIGNAL.search(line))
    if len(nonblank) >= 2 and (indented >= max(1, len(nonblank) // 2) or signals >= 2):
        return "code", "medium", ["layout-derived-code-boundary"]
    if len(nonblank) == 1:
        line = nonblank[0].strip()
        if line.startswith("#") or _NUMBERED_HEADING.match(line):
            return "heading", "high", warnings
        if _HEADING.match(line) and (line.isupper() or not re.search(r"[.!?。！？]$", line)):
            return "heading", "low", ["heading-inferred-from-short-line"]
    if all(len(line.strip()) >= 2 for line in nonblank):
        return "paragraph", "medium", warnings
    return "raw", "low", ["structure-not-reliably-classified"]


def segment_page_text(
    reference_id: str,
    page_number: int,
    method: str,
    confidence: str,
    text: str,
    source_file: str | None = None,
) -> list[dict[str, Any]]:
    """Split page text without rewriting its non-blank lines."""

    # Blank lines are the only hard boundaries.  The classifier never rewrites
    # non-blank lines, so indentation and column spacing remain evidence.
    blocks: list[tuple[int, int, str]] = []
    start: int | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        content_end = offset + len(line.rstrip("\r\n"))
        if line.strip():
            if start is None:
                start = offset
        elif start is not None:
            blocks.append((start, content_end - len(line.rstrip("\r\n")), text[start:offset].rstrip("\n")))
            start = None
        offset += len(line)
    if start is not None:
        blocks.append((start, len(text), text[start:].rstrip("\n")))
    if not blocks and text:
        blocks = [(0, len(text), text)]
    fragments: list[dict[str, Any]] = []
    for ordinal, (begin, _end, block) in enumerate(blocks, start=1):
        end = begin + len(block)
        if not block.strip():
            continue
        structure, structure_confidence, warnings = _classify_block(block.split("\n"))
        fragments.append(
            {
                "fragment_id": stable_id("reference-fragment", reference_id, page_number, ordinal, begin, end, block),
                "source_id": reference_id,
                "source_file": source_file,
                "page_number": page_number,
                "method": method,
                "confidence": confidence,
                "structure": structure,
                "structure_confidence": structure_confidence,
                "text_range": {"start": begin, "end": end, "unit": "unicode-codepoint", "end_exclusive": True},
                "text": block,
                "warnings": warnings,
            }
        )
    return fragments


def _resolve_ocr_adapter(adapter: Path | None) -> tuple[Path | None, dict[str, Any]]:
    if adapter is None:
        return None, {"status": "missing", "reason": "ocr-adapter-not-configured"}
    resolved = adapter.resolve()
    if not resolved.is_file() or resolved.suffix.casefold() != ".py":
        return None, {"status": "missing", "reason": "ocr-adapter-not-usable", "path": str(resolved)}
    return resolved, {"status": "ready", "path": str(resolved), "sha256": sha256_file(resolved)}


def _run_ocr_page(
    adapter: Path,
    source: Path,
    page_number: int,
    output_path: Path,
    timeout_seconds: int,
    cancel_file: Path | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    command = [
        sys.executable,
        str(adapter),
        "--source",
        str(source),
        "--page",
        str(page_number),
        "--output",
        str(output_path),
        "--schema-version",
        str(OCR_ADAPTER_SCHEMA_VERSION),
    ]
    if cancel_file is not None:
        command.extend(["--cancel-file", str(cancel_file)])
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **background_process_options(),
    )
    deadline = started + timeout_seconds
    while process.poll() is None:
        if cancel_file is not None and cancel_file.exists():
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            return None, {
                "status": "pending",
                "reason": "ocr-cancelled",
                "exit_status": process.returncode,
                "stderr": stderr.strip()[:1000],
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        if time.monotonic() >= deadline:
            process.kill()
            _stdout, stderr = process.communicate()
            return None, {
                "status": "pending",
                "reason": "ocr-timeout",
                "exit_status": process.returncode,
                "stderr": stderr.strip()[:1000],
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        time.sleep(0.05)
    stdout, stderr = process.communicate()
    completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    elapsed = round(time.monotonic() - started, 3)
    if completed.returncode != 0:
        return None, {
            "status": "pending",
            "reason": "ocr-adapter-failed",
            "exit_status": completed.returncode,
            "stderr": completed.stderr.strip()[:1000],
            "elapsed_seconds": elapsed,
        }
    if not output_path.is_file():
        return None, {"status": "pending", "reason": "ocr-output-missing", "elapsed_seconds": elapsed}
    if output_path.stat().st_size > MAX_OCR_OUTPUT_BYTES:
        return None, {"status": "pending", "reason": "ocr-output-size-limit", "elapsed_seconds": elapsed}
    try:
        result = json_load(output_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, {"status": "pending", "reason": "ocr-output-invalid-json", "detail": str(exc), "elapsed_seconds": elapsed}
    if (
        result.get("schema_version") != OCR_ADAPTER_SCHEMA_VERSION
        or result.get("status") != "extracted"
        or result.get("page_number") != page_number
        or not isinstance(result.get("text"), str)
    ):
        return None, {"status": "pending", "reason": "ocr-output-contract", "elapsed_seconds": elapsed}
    score = result.get("confidence")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= float(score) <= 1.0:
        return None, {"status": "pending", "reason": "ocr-confidence-invalid", "elapsed_seconds": elapsed}
    return result, {"status": "completed", "elapsed_seconds": elapsed, "confidence_score": round(float(score), 6)}


def inspect_pdf(source: Path, max_bytes: int, max_pages: int):
    """Open a PDF before any managed files are created."""

    max_bytes, max_pages = validate_pdf_limits(max_bytes, max_pages)
    size = source.stat().st_size
    if size < 5 or size > max_bytes:
        raise PdfExtractionError(f"PDF source must contain 5..{max_bytes} bytes")
    with source.open("rb") as stream:
        header = stream.read(5)
    if header != b"%PDF-":
        raise PdfExtractionError("PDF source does not start with a PDF header")
    pypdf = _load_pypdf()
    parser_logger = logging.getLogger("pypdf")
    previous_level = parser_logger.level
    try:
        parser_logger.setLevel(logging.CRITICAL + 1)
        reader = pypdf.PdfReader(str(source), strict=False)
        if reader.is_encrypted:
            raise PdfExtractionError("encrypted PDF sources require decryption before reference ingest")
        page_count = len(reader.pages)
    except PdfExtractionError:
        raise
    except Exception as exc:
        name = type(exc).__name__
        raise PdfExtractionError(f"corrupt or unsupported PDF source ({name}): {exc}") from exc
    finally:
        parser_logger.setLevel(previous_level)
    if page_count < 1:
        raise PdfExtractionError("PDF source contains no pages")
    if page_count > max_pages:
        raise PdfExtractionError(f"PDF page count {page_count} exceeds limit {max_pages}")
    return pypdf, reader, page_count


def extract_pdf(
    source: Path,
    reference_id: str,
    extraction_root: Path,
    *,
    max_bytes: int = DEFAULT_MAX_PDF_BYTES,
    max_pages: int = DEFAULT_MAX_PDF_PAGES,
    native_min_characters: int = DEFAULT_NATIVE_MIN_CHARACTERS,
    native_min_printable_ratio: float = DEFAULT_NATIVE_MIN_PRINTABLE_RATIO,
    ocr_enabled: bool = False,
    ocr_adapter: Path | None = None,
    ocr_max_pages: int = DEFAULT_OCR_MAX_PAGES,
    ocr_timeout_seconds: int = DEFAULT_OCR_TIMEOUT_SECONDS,
    ocr_max_input_bytes: int = DEFAULT_OCR_MAX_INPUT_BYTES,
    ocr_cancel_file: Path | None = None,
) -> dict[str, Any]:
    """Extract page text and write relocatable evidence beneath one managed root."""

    if native_min_characters < 1 or native_min_characters > 10000:
        raise CkbError("native minimum characters must be within 1..10000")
    if not 0.5 <= native_min_printable_ratio <= 1.0:
        raise CkbError("native minimum printable ratio must be within 0.5..1.0")
    ocr_max_pages, ocr_timeout_seconds, ocr_max_input_bytes = validate_ocr_limits(
        ocr_max_pages,
        ocr_timeout_seconds,
        ocr_max_input_bytes,
    )
    _pypdf, reader, page_count = inspect_pdf(source, max_bytes, max_pages)
    extraction_root = extraction_root.resolve()
    extraction_root.mkdir(parents=True, exist_ok=False)
    pages_root = extraction_root / "pages"
    ocr_root = extraction_root / "ocr"
    pages_root.mkdir()
    if ocr_enabled:
        ocr_root.mkdir()
    adapter, adapter_status = _resolve_ocr_adapter(ocr_adapter) if ocr_enabled else (
        None,
        {"status": "disabled", "reason": "ocr-not-enabled"},
    )
    cancel_file = ocr_cancel_file.resolve() if ocr_cancel_file is not None else None
    pages: list[dict[str, Any]] = []
    missing_pages: list[int] = []
    ocr_attempts = 0
    total_characters = 0
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            native_text = page.extract_text(
                extraction_mode="layout",
                layout_mode_space_vertically=True,
                layout_mode_scale_weight=1.0,
                layout_mode_strip_rotated=False,
            ) or ""
        except Exception as exc:
            native_text = ""
            native_error = {"type": type(exc).__name__, "detail": str(exc)[:1000]}
        else:
            native_error = None
        native_text = _normalized_layout_text(native_text)
        native_metrics = _text_metrics(native_text)
        native_usable = _usable_text(native_metrics, native_min_characters, native_min_printable_ratio)
        selected_text = native_text
        method = "native"
        confidence = _native_confidence(native_metrics) if native_usable else "low"
        status = "extracted" if native_usable else "pending"
        reason = None if native_usable else "native-text-below-usable-threshold"
        ocr_record: dict[str, Any] = {"status": "not-needed" if native_usable else adapter_status["status"]}
        if not native_usable and ocr_enabled:
            if cancel_file is not None and cancel_file.exists():
                ocr_record = {"status": "pending", "reason": "ocr-cancelled"}
                reason = "ocr-cancelled"
            elif source.stat().st_size > ocr_max_input_bytes:
                ocr_record = {"status": "pending", "reason": "ocr-input-size-limit"}
                reason = "ocr-input-size-limit"
            elif adapter is None:
                ocr_record = dict(adapter_status)
                reason = str(adapter_status["reason"])
            elif ocr_attempts >= ocr_max_pages:
                ocr_record = {"status": "pending", "reason": "ocr-page-limit"}
                reason = "ocr-page-limit"
            else:
                ocr_attempts += 1
                adapter_output = ocr_root / f"page-{page_number:04d}.json"
                result, execution = _run_ocr_page(
                    adapter,
                    source,
                    page_number,
                    adapter_output,
                    ocr_timeout_seconds,
                    cancel_file,
                )
                ocr_record = execution
                if result is not None:
                    candidate = _normalized_layout_text(result["text"])
                    metrics = _text_metrics(candidate)
                    score = float(result["confidence"])
                    usable = _usable_text(metrics, native_min_characters, native_min_printable_ratio) and score >= 0.75
                    selected_text = candidate
                    method = "ocr"
                    confidence = "high" if score >= 0.90 else "medium" if usable else "low"
                    status = "extracted" if usable else "pending"
                    reason = None if usable else "ocr-text-below-usable-threshold"
                    ocr_record.update({"text_metrics": metrics, "accepted": usable})
                else:
                    reason = str(execution["reason"])
        if len(selected_text) > MAX_PAGE_TEXT_CHARACTERS:
            raise PdfExtractionError(
                f"PDF page {page_number} extracted text exceeds {MAX_PAGE_TEXT_CHARACTERS} characters"
            )
        total_characters += len(selected_text)
        if total_characters > MAX_DOCUMENT_TEXT_CHARACTERS:
            raise PdfExtractionError(
                f"PDF extracted text exceeds {MAX_DOCUMENT_TEXT_CHARACTERS} characters"
            )
        page_text_path = pages_root / f"page-{page_number:04d}.txt"
        page_text_path.write_text(selected_text, encoding="utf-8", newline="\n")
        page_record = {
            "page_number": page_number,
            "status": status,
            "method": method,
            "confidence": confidence,
            "reason": reason,
            "source_id": reference_id,
            "source_file": str(source.resolve()),
            "text_file": str(page_text_path.resolve()),
            "text_relative": page_text_path.relative_to(extraction_root.parent.parent).as_posix(),
            "text_sha256": sha256_file(page_text_path),
            "text_length": len(selected_text),
            "native_metrics": native_metrics,
            "native_error": native_error,
            "ocr": ocr_record,
            "fragments": segment_page_text(
                reference_id,
                page_number,
                method,
                confidence,
                selected_text,
                str(source.resolve()),
            ),
        }
        if status != "extracted":
            missing_pages.append(page_number)
        pages.append(page_record)
    result = {
        "schema_version": PDF_EXTRACTION_SCHEMA_VERSION,
        "reference_id": reference_id,
        "status": "ready" if not missing_pages else "pending",
        "source_file": str(source.resolve()),
        "source_sha256": sha256_file(source),
        "parser": {"name": PDF_PARSER_NAME, "version": PDF_PARSER_VERSION, "mode": "layout"},
        "page_count": page_count,
        "extracted_page_count": page_count - len(missing_pages),
        "pending_pages": missing_pages,
        "limits": {
            "max_pdf_bytes": max_bytes,
            "max_pdf_pages": max_pages,
            "max_page_text_characters": MAX_PAGE_TEXT_CHARACTERS,
            "max_document_text_characters": MAX_DOCUMENT_TEXT_CHARACTERS,
            "native_min_characters": native_min_characters,
            "native_min_printable_ratio": native_min_printable_ratio,
        },
        "ocr": {
            "enabled": ocr_enabled,
            "adapter": adapter_status,
            "max_pages": ocr_max_pages,
            "attempted_pages": ocr_attempts,
            "timeout_seconds_per_page": ocr_timeout_seconds,
            "max_input_bytes": ocr_max_input_bytes,
            "max_output_bytes_per_page": MAX_OCR_OUTPUT_BYTES,
            "cancel_file": str(cancel_file) if cancel_file is not None else None,
        },
        "pages": pages,
        "created_at_utc": utc_now(),
    }
    extraction_manifest = extraction_root / "manifest.json"
    json_write(extraction_manifest, result)
    result["manifest"] = str(extraction_manifest.resolve())
    result["manifest_sha256"] = sha256_file(extraction_manifest)
    return result


def validate_pdf_extraction(
    output: Path,
    manifest: dict[str, Any],
    *,
    require_ready: bool = False,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Reopen page evidence and report all extraction/provenance drift."""

    errors: list[dict[str, Any]] = []
    reference_id = str(manifest.get("reference_id") or "")
    extraction_value = manifest.get("extraction_file")
    if not isinstance(extraction_value, str) or not extraction_value:
        return None, [{"reason": "reference-pdf-extraction-missing", "reference_id": reference_id}]
    extraction_path = Path(extraction_value)
    expected_root = (output / "references" / "extractions" / reference_id).resolve()
    if not path_inside(extraction_path, expected_root) or extraction_path.resolve() != expected_root / "manifest.json":
        return None, [{"reason": "reference-pdf-extraction-path", "reference_id": reference_id, "path": str(extraction_path)}]
    if not extraction_path.is_file():
        return None, [{"reason": "reference-pdf-extraction-missing", "reference_id": reference_id}]
    if sha256_file(extraction_path) != manifest.get("extraction_sha256"):
        errors.append({"reason": "reference-pdf-extraction-drift", "reference_id": reference_id})
    try:
        extraction = json_load(extraction_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [{"reason": "reference-pdf-extraction-invalid", "reference_id": reference_id, "detail": str(exc)}]
    if extraction.get("schema_version") != PDF_EXTRACTION_SCHEMA_VERSION or extraction.get("reference_id") != reference_id:
        errors.append({"reason": "reference-pdf-extraction-contract", "reference_id": reference_id})
    if extraction.get("source_sha256") != manifest.get("source_sha256"):
        errors.append({"reason": "reference-pdf-source-binding", "reference_id": reference_id})
    if Path(str(extraction.get("source_file") or "")).resolve() != Path(str(manifest.get("source_file") or "")).resolve():
        errors.append({"reason": "reference-pdf-source-path-binding", "reference_id": reference_id})
    parser = extraction.get("parser") if isinstance(extraction.get("parser"), dict) else {}
    if parser.get("name") != PDF_PARSER_NAME or parser.get("version") != PDF_PARSER_VERSION or parser.get("mode") != "layout":
        errors.append({"reason": "reference-pdf-parser-contract", "reference_id": reference_id})
    pages = extraction.get("pages")
    declared_page_count = extraction.get("page_count")
    if (
        not isinstance(pages, list)
        or not isinstance(declared_page_count, int)
        or isinstance(declared_page_count, bool)
        or len(pages) != declared_page_count
    ):
        errors.append({"reason": "reference-pdf-page-count", "reference_id": reference_id})
        pages = pages if isinstance(pages, list) else []
    expected_numbers = list(range(1, len(pages) + 1))
    actual_numbers = [page.get("page_number") for page in pages if isinstance(page, dict)]
    if actual_numbers != expected_numbers:
        errors.append({"reason": "reference-pdf-page-sequence", "reference_id": reference_id, "pages": actual_numbers})
    if manifest.get("page_count") != extraction.get("page_count"):
        errors.append({"reason": "reference-pdf-manifest-page-count", "reference_id": reference_id})
    fragment_ids: set[str] = set()
    expected_page_files: set[Path] = set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_number = page.get("page_number")
        page_contract = (
            page.get("source_id") == reference_id
            and page.get("status") in {"extracted", "pending"}
            and page.get("method") in {"native", "ocr"}
            and page.get("confidence") in {"high", "medium", "low"}
            and isinstance(page.get("native_metrics"), dict)
            and isinstance(page.get("ocr"), dict)
            and (
                (page.get("status") == "extracted" and page.get("confidence") in {"high", "medium"} and page.get("reason") is None)
                or (page.get("status") == "pending" and page.get("confidence") == "low" and isinstance(page.get("reason"), str))
            )
        )
        if not page_contract:
            errors.append({"reason": "reference-pdf-page-contract", "reference_id": reference_id, "page_number": page_number})
        path = Path(str(page.get("text_file") or ""))
        expected_page_files.add(path.resolve())
        if not path_inside(path, expected_root / "pages"):
            errors.append({"reason": "reference-pdf-page-path", "reference_id": reference_id, "page_number": page_number})
            continue
        expected_relative = path.resolve().relative_to((output / "references").resolve()).as_posix()
        if page.get("text_relative") != expected_relative:
            errors.append({"reason": "reference-pdf-page-relative-path", "reference_id": reference_id, "page_number": page_number})
        if Path(str(page.get("source_file") or "")).resolve() != Path(str(manifest.get("source_file") or "")).resolve():
            errors.append({"reason": "reference-pdf-page-source-binding", "reference_id": reference_id, "page_number": page_number})
        if not path.is_file() or sha256_file(path) != page.get("text_sha256"):
            errors.append({"reason": "reference-pdf-page-drift", "reference_id": reference_id, "page_number": page_number})
            continue
        text = path.read_text(encoding="utf-8")
        if len(text) != page.get("text_length"):
            errors.append({"reason": "reference-pdf-page-length", "reference_id": reference_id, "page_number": page_number})
        fragments = page.get("fragments")
        if not isinstance(fragments, list):
            errors.append({"reason": "reference-pdf-fragments", "reference_id": reference_id, "page_number": page_number})
            continue
        ranges: list[tuple[int, int]] = []
        for fragment in fragments:
            if not isinstance(fragment, dict):
                errors.append({"reason": "reference-pdf-fragment-contract", "reference_id": reference_id, "page_number": page_number})
                continue
            fragment_id = str(fragment.get("fragment_id") or "")
            text_range = fragment.get("text_range") if isinstance(fragment.get("text_range"), dict) else {}
            start, end = text_range.get("start"), text_range.get("end")
            method_matches = fragment.get("method") == page.get("method") and fragment.get("method") in {"native", "ocr"}
            confidence_matches = (
                fragment.get("confidence") == page.get("confidence")
                and fragment.get("confidence") in {"high", "medium", "low"}
            )
            valid = (
                fragment.get("source_id") == reference_id
                and Path(str(fragment.get("source_file") or "")).resolve() == Path(str(manifest.get("source_file") or "")).resolve()
                and fragment.get("page_number") == page_number
                and method_matches
                and confidence_matches
                and fragment.get("structure") in {"heading", "paragraph", "list", "code", "table", "raw"}
                and fragment.get("structure_confidence") in {"high", "medium", "low"}
                and isinstance(fragment.get("warnings"), list)
                and isinstance(start, int)
                and isinstance(end, int)
                and 0 <= start < end <= len(text)
                and text[start:end] == fragment.get("text")
                and fragment_id
                and fragment_id not in fragment_ids
            )
            if not valid:
                errors.append({"reason": "reference-pdf-fragment-contract", "reference_id": reference_id, "page_number": page_number, "fragment_id": fragment_id})
            else:
                fragment_ids.add(fragment_id)
                ranges.append((start, end))
        if ranges != sorted(ranges) or any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
            errors.append({"reason": "reference-pdf-fragment-overlap", "reference_id": reference_id, "page_number": page_number})
        if page.get("status") == "extracted" and (not text.strip() or not fragments):
            errors.append({"reason": "reference-pdf-empty-extracted-page", "reference_id": reference_id, "page_number": page_number})
    pages_directory = expected_root / "pages"
    actual_page_files = {path.resolve() for path in pages_directory.glob("page-*.txt")} if pages_directory.is_dir() else set()
    if actual_page_files != expected_page_files:
        errors.append(
            {
                "reason": "reference-pdf-page-file-set",
                "reference_id": reference_id,
                "missing": sorted(str(path) for path in expected_page_files - actual_page_files),
                "extra": sorted(str(path) for path in actual_page_files - expected_page_files),
            }
        )
    pending_pages = [page.get("page_number") for page in pages if isinstance(page, dict) and page.get("status") != "extracted"]
    if pending_pages != extraction.get("pending_pages"):
        errors.append({"reason": "reference-pdf-pending-page-set", "reference_id": reference_id})
    expected_status = "pending" if pending_pages else "ready"
    if extraction.get("status") != expected_status or manifest.get("extraction_status") != expected_status:
        errors.append({"reason": "reference-pdf-extraction-status", "reference_id": reference_id})
    if extraction.get("extracted_page_count") != len(pages) - len(pending_pages):
        errors.append({"reason": "reference-pdf-extracted-page-count", "reference_id": reference_id})
    if manifest.get("pending_pages") != pending_pages:
        errors.append({"reason": "reference-pdf-manifest-pending-pages", "reference_id": reference_id})
    if require_ready and pending_pages:
        errors.append({"reason": "reference-pdf-pages-pending", "reference_id": reference_id, "pages": pending_pages})
    return extraction, errors


def pdf_fragment(extraction: dict[str, Any], fragment_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for page in extraction.get("pages", []):
        for fragment in page.get("fragments", []):
            if fragment.get("fragment_id") == fragment_id:
                return page, fragment
    raise CkbError(f"PDF review fragment does not exist: {fragment_id}")
