#!/usr/bin/env python3
"""Optional RapidOCR adapter used only by the real PDF OCR benchmark.

The adapter renders exactly one PDF page with Poppler and sends that image to
RapidOCR.  It is deliberately outside the CKB runtime dependency graph.  The
parent process must make ``rapidocr_onnxruntime`` importable and either put
``pdftoppm`` on PATH or set ``CKB_PDFTOPPM``.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
from typing import Any


ADAPTER_ID = "ckb-real-rapidocr-poppler-v1"


def _tool(name: str, environment_name: str) -> Path:
    configured = os.environ.get(environment_name, "").strip()
    if configured:
        candidate = Path(configured).resolve()
        if candidate.is_file():
            return candidate
        raise RuntimeError(f"ocr-tool-missing: {environment_name}={candidate}")
    candidate = shutil.which(name)
    if candidate:
        return Path(candidate).resolve()
    raise RuntimeError(f"ocr-tool-missing: {name}")


def _bounds(item: list[Any]) -> tuple[float, float, float, float, str, float]:
    box, text, score = item
    xs = [float(point[0]) for point in box]
    ys = [float(point[1]) for point in box]
    return min(xs), min(ys), max(xs), max(ys), str(text).strip(), float(score)


def _group_rows(detections: list[list[Any]]) -> list[list[tuple[float, float, float, float, str, float]]]:
    values = [value for value in (_bounds(item) for item in detections) if value[4]]
    values.sort(key=lambda value: ((value[1] + value[3]) / 2.0, value[0]))
    rows: list[list[tuple[float, float, float, float, str, float]]] = []
    for value in values:
        center = (value[1] + value[3]) / 2.0
        height = max(1.0, value[3] - value[1])
        if rows:
            row = rows[-1]
            row_center = statistics.mean((item[1] + item[3]) / 2.0 for item in row)
            row_height = statistics.mean(max(1.0, item[3] - item[1]) for item in row)
            if abs(center - row_center) <= max(8.0, min(height, row_height) * 0.55):
                row.append(value)
                row.sort(key=lambda item: item[0])
                continue
        rows.append([value])
    return rows


def _character_width(rows: list[list[tuple[float, float, float, float, str, float]]]) -> float:
    widths: list[float] = []
    for row in rows:
        for left, _top, right, _bottom, text, _score in row:
            ascii_count = sum(1 for character in text if ord(character) < 128 and not character.isspace())
            if ascii_count >= 4:
                widths.append((right - left) / max(len(text), 1))
    return max(4.0, statistics.median(widths)) if widths else 12.0


def layout_text(detections: list[list[Any]]) -> str:
    """Reconstruct rows, visible column gaps, and relative code indentation."""

    rows = _group_rows(detections)
    if not rows:
        return ""
    character_width = _character_width(rows)
    centers = [statistics.mean((item[1] + item[3]) / 2.0 for item in row) for row in rows]
    gaps = [right - left for left, right in zip(centers, centers[1:]) if right > left]
    ordinary = [gap for gap in gaps if gap <= (statistics.median(gaps) * 3 if gaps else gap)]
    typical_gap = statistics.median(ordinary or gaps or [40.0])
    blank_threshold = max(typical_gap * 1.65, 100.0)

    block_starts = [0]
    for index, gap in enumerate(gaps, start=1):
        if gap > blank_threshold:
            block_starts.append(index)
    block_starts.append(len(rows))

    rendered: list[str] = []
    for block_number, (start, end) in enumerate(zip(block_starts, block_starts[1:])):
        if block_number:
            rendered.append("")
        block = rows[start:end]
        block_left = min(item[0] for row in block for item in row)
        for row in block:
            line = ""
            cursor = block_left
            for left, _top, right, _bottom, text, _score in row:
                space_count = max(0, round((left - cursor) / character_width))
                if line and space_count < 2:
                    space_count = 2
                line += " " * space_count + text
                cursor = right
            rendered.append(line.rstrip())
    return "\n".join(rendered).strip()


def run(source: Path, page_number: int, output: Path, schema_version: int, cancel_file: Path | None) -> None:
    if cancel_file is not None and cancel_file.exists():
        raise RuntimeError("ocr-cancelled-before-render")
    renderer = _tool("pdftoppm", "CKB_PDFTOPPM")
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError("ocr-tool-missing: rapidocr_onnxruntime") from exc

    with tempfile.TemporaryDirectory(prefix="ckb-real-ocr-") as directory:
        prefix = Path(directory) / "page"
        command = [
            str(renderer),
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-r",
            "250",
            "-png",
            "-singlefile",
            str(source),
            str(prefix),
        ]
        completed = subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True)
        image = prefix.with_suffix(".png")
        if completed.returncode or not image.is_file():
            detail = completed.stderr.strip()[:500]
            raise RuntimeError(f"ocr-render-failed: exit={completed.returncode}; {detail}")
        if cancel_file is not None and cancel_file.exists():
            raise RuntimeError("ocr-cancelled-after-render")
        result, _elapsed = RapidOCR()(str(image))

    detections = result or []
    text = layout_text(detections)
    scores = [float(item[2]) for item in detections if len(item) >= 3]
    confidence = sum(scores) / len(scores) if scores else 0.0
    payload = {
        "schema_version": schema_version,
        "status": "extracted",
        "page_number": page_number,
        "text": text,
        "confidence": round(confidence, 6),
        "engine": {
            "adapter_id": ADAPTER_ID,
            "name": "rapidocr_onnxruntime",
            "version": importlib.metadata.version("rapidocr-onnxruntime"),
            "onnxruntime_version": importlib.metadata.version("onnxruntime"),
        },
        "renderer": {"name": "pdftoppm", "path": str(renderer), "dpi": 250},
        "detection_count": len(detections),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--page", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--schema-version", required=True, type=int)
    parser.add_argument("--cancel-file", type=Path)
    arguments = parser.parse_args(argv)
    try:
        run(
            arguments.source.resolve(),
            arguments.page,
            arguments.output.resolve(),
            arguments.schema_version,
            arguments.cancel_file.resolve() if arguments.cancel_file else None,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
