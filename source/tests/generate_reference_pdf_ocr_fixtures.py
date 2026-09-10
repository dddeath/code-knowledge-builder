#!/usr/bin/env python3
"""Generate the frozen native, scanned, and hybrid PDF OCR fixtures.

This developer-only script uses ReportLab, Pillow, Poppler, and pypdf.  The
generated PDFs are committed fixtures; none of these authoring dependencies are
added to the CKB runtime or imported by the default test suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


PAGE_WIDTH = 595.2756
PAGE_HEIGHT = 841.8898

PAGES: list[dict[str, Any]] = [
    {
        "page_number": 1,
        "header": "CKB OCR REFERENCE | CODE PAGE",
        "title": "扫描 OCR 基准 / Scan OCR Benchmark",
        "body": "中英文混排 Mixed Chinese and English 2026.",
        "code_lines": [
            "def normalize(items):",
            "    total = sum(x[\"value\"] for x in items)",
            "    return {\"count\": len(items), \"total\": total}",
        ],
        "footer": "FIXTURE ONLY | Page 1 / 2",
    },
    {
        "page_number": 2,
        "header": "CKB OCR REFERENCE | TABLE PAGE",
        "title": "跨行表格 / Multi-line Table",
        "table_rows": [
            ["模块 Module", "状态 Status", "说明 Note"],
            ["parser", "READY", "保留页码 / page 2"],
            ["ocr", "CHECK", "code + table"],
            ["trace", "PASS", "source-page=2"],
        ],
        "wrapped_cell": ["保留页码", "page 2"],
        "footer": "FIXTURE ONLY | Page 2 / 2",
    },
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _font(path: str | None, fallbacks: list[Path]) -> Path:
    candidates = [Path(path).expanduser()] if path else []
    candidates.extend(fallbacks)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"fixture font not found: {[str(item) for item in candidates]}")


def _renderer(path: str | None) -> Path:
    if path:
        candidate = Path(path).resolve()
        if candidate.is_file():
            return candidate
    command = shutil.which("pdftoppm")
    if command:
        return Path(command).resolve()
    raise FileNotFoundError("pdftoppm is required to rasterize the scanned fixture")


def _draw_native(path: Path, cjk_font: Path, mono_font: Path) -> None:
    from reportlab import rl_config
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    rl_config.useA85 = 0
    pdfmetrics.registerFont(TTFont("FixtureCJK", str(cjk_font)))
    pdfmetrics.registerFont(TTFont("FixtureMono", str(mono_font)))
    drawing = canvas.Canvas(str(path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT), invariant=1, pageCompression=1)
    drawing.setAuthor("Code Knowledge Builder")
    drawing.setCreator("CKB deterministic OCR fixture generator")
    drawing.setTitle("CKB OCR code and table fidelity fixture")

    first = PAGES[0]
    drawing.setFillColorRGB(0.25, 0.25, 0.25)
    drawing.setFont("FixtureCJK", 9)
    drawing.drawString(48, 804, first["header"])
    drawing.setStrokeColorRGB(0.75, 0.75, 0.75)
    drawing.line(48, 792, 547, 792)
    drawing.setFillColorRGB(0.05, 0.05, 0.05)
    drawing.setFont("FixtureCJK", 22)
    drawing.drawString(48, 748, first["title"])
    drawing.setFont("FixtureCJK", 13)
    drawing.drawString(48, 712, first["body"])
    drawing.setFillColorRGB(0.96, 0.97, 0.98)
    drawing.roundRect(48, 514, 499, 156, 5, fill=1, stroke=0)
    drawing.setFillColorRGB(0.05, 0.05, 0.05)
    drawing.setFont("FixtureMono", 13)
    code_y = 630
    for line in first["code_lines"]:
        drawing.drawString(70, code_y, line)
        code_y -= 37
    drawing.setFillColorRGB(0.35, 0.35, 0.35)
    drawing.setFont("FixtureCJK", 9)
    drawing.drawCentredString(PAGE_WIDTH / 2, 34, first["footer"])
    drawing.showPage()

    second = PAGES[1]
    drawing.setFillColorRGB(0.25, 0.25, 0.25)
    drawing.setFont("FixtureCJK", 9)
    drawing.drawString(48, 804, second["header"])
    drawing.setStrokeColorRGB(0.75, 0.75, 0.75)
    drawing.line(48, 792, 547, 792)
    drawing.setFillColorRGB(0.05, 0.05, 0.05)
    drawing.setFont("FixtureCJK", 22)
    drawing.drawString(48, 748, second["title"])

    x_positions = [48, 198, 328, 547]
    top = 690
    row_heights = [48, 70, 48, 48]
    bottom = top - sum(row_heights)
    drawing.setStrokeColorRGB(0.20, 0.20, 0.20)
    drawing.setLineWidth(0.8)
    for x in x_positions:
        drawing.line(x, top, x, bottom)
    y = top
    for height in row_heights:
        drawing.line(x_positions[0], y, x_positions[-1], y)
        y -= height
    drawing.line(x_positions[0], bottom, x_positions[-1], bottom)
    drawing.setFont("FixtureCJK", 12)
    y = top
    for row_index, (row, height) in enumerate(zip(second["table_rows"], row_heights)):
        center_y = y - 29
        if row_index == 1:
            values = [row[0], row[1], second["wrapped_cell"][0]]
        else:
            values = row
        for column, value in enumerate(values):
            drawing.drawString(x_positions[column] + 8, center_y, value)
        if row_index == 1:
            drawing.drawString(x_positions[2] + 8, center_y - 24, second["wrapped_cell"][1])
        y -= height
    drawing.setFillColorRGB(0.35, 0.35, 0.35)
    drawing.setFont("FixtureCJK", 9)
    drawing.drawCentredString(PAGE_WIDTH / 2, 34, second["footer"])
    drawing.showPage()
    drawing.save()


def _render_pages(native: Path, renderer: Path, directory: Path) -> list[Path]:
    prefix = directory / "page"
    command = [str(renderer), "-r", "250", "-png", str(native), str(prefix)]
    completed = subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"pdftoppm failed ({completed.returncode}): {completed.stderr.strip()}")
    pages = sorted(directory.glob("page-*.png"))
    if len(pages) != len(PAGES):
        raise RuntimeError(f"expected {len(PAGES)} rendered pages, found {len(pages)}")
    return pages


def _draw_scanned(path: Path, rendered_pages: list[Path]) -> None:
    from reportlab import rl_config
    from reportlab.pdfgen import canvas

    rl_config.useA85 = 0
    drawing = canvas.Canvas(str(path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT), invariant=1, pageCompression=1)
    drawing.setAuthor("Code Knowledge Builder")
    drawing.setCreator("CKB deterministic OCR fixture generator")
    drawing.setTitle("CKB image-only scanned OCR fixture")
    for page in rendered_pages:
        drawing.drawImage(str(page), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT, preserveAspectRatio=False, mask="auto")
        drawing.showPage()
    drawing.save()


def _draw_hybrid(path: Path, native: Path, scanned: Path) -> None:
    from pypdf import PdfReader, PdfWriter

    native_reader = PdfReader(str(native), strict=True)
    scanned_reader = PdfReader(str(scanned), strict=True)
    writer = PdfWriter()
    writer.add_page(native_reader.pages[0])
    writer.add_page(scanned_reader.pages[1])
    writer.add_metadata(
        {
            "/Author": "Code Knowledge Builder",
            "/Creator": "CKB deterministic OCR fixture generator",
            "/Title": "CKB native and scanned hybrid fixture",
        }
    )
    with path.open("wb") as stream:
        writer.write(stream)


def _verify_kinds(native: Path, scanned: Path, hybrid: Path) -> dict[str, Any]:
    from pypdf import PdfReader

    native_text = [(page.extract_text() or "").strip() for page in PdfReader(str(native), strict=True).pages]
    scanned_text = [(page.extract_text() or "").strip() for page in PdfReader(str(scanned), strict=True).pages]
    hybrid_text = [(page.extract_text() or "").strip() for page in PdfReader(str(hybrid), strict=True).pages]
    if not all(native_text) or any(scanned_text) or not hybrid_text[0] or hybrid_text[1]:
        raise RuntimeError(
            "fixture kind verification failed: "
            f"native={[bool(value) for value in native_text]}, "
            f"scanned={[bool(value) for value in scanned_text]}, "
            f"hybrid={[bool(value) for value in hybrid_text]}"
        )
    return {
        "native_text_pages": [bool(value) for value in native_text],
        "scanned_text_pages": [bool(value) for value in scanned_text],
        "hybrid_text_pages": [bool(value) for value in hybrid_text],
    }


def generate(output: Path, cjk_font: Path, mono_font: Path, renderer: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    native = output / "native-code-table-mixed.pdf"
    scanned = output / "scanned-code-table-mixed.pdf"
    hybrid = output / "hybrid-native-scanned.pdf"
    render_root = output / ".fixture-build"
    render_root.mkdir(exist_ok=True)
    for existing in render_root.glob("page-*.png"):
        existing.unlink()
    _draw_native(native, cjk_font, mono_font)
    rendered_pages = _render_pages(native, renderer, render_root)
    _draw_scanned(scanned, rendered_pages)
    _draw_hybrid(hybrid, native, scanned)
    for rendered in rendered_pages:
        rendered.unlink()
    render_root.rmdir()
    kind_evidence = _verify_kinds(native, scanned, hybrid)
    fixture = {
        "schema_version": 1,
        "fixture_id": "ckb-reference-pdf-ocr-code-table-v1",
        "description_zh": "冻结的原生文本、纯图像扫描和原生加扫描混合 PDF，用于分别测量文本覆盖、代码保真、表格结构与来源页定位。",
        "documents": {
            "native": {"path": native.name, "sha256": _sha256(native), "page_text_modes": ["native", "native"]},
            "scanned": {"path": scanned.name, "sha256": _sha256(scanned), "page_text_modes": ["image-only", "image-only"]},
            "hybrid": {"path": hybrid.name, "sha256": _sha256(hybrid), "page_text_modes": ["native", "image-only"]},
        },
        "kind_evidence": kind_evidence,
        "pages": PAGES,
        "quality_dimensions": ["text_coverage", "code_fidelity", "table_structure", "source_page_locator"],
        "noise": {"repeated_header": True, "footer_page_number": True},
    }
    manifest = output / "fixture-ground-truth.json"
    data = (json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest.write_bytes(data)
    if manifest.read_bytes() != data:
        raise RuntimeError("reopened ground-truth manifest differs")
    return fixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cjk-font")
    parser.add_argument("--mono-font")
    parser.add_argument("--pdftoppm")
    arguments = parser.parse_args(argv)
    cjk = _font(
        arguments.cjk_font or os.environ.get("CKB_OCR_FIXTURE_CJK_FONT"),
        [Path(r"C:\Windows\Fonts\simhei.ttf"), Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")],
    )
    mono = _font(
        arguments.mono_font or os.environ.get("CKB_OCR_FIXTURE_MONO_FONT"),
        [Path(r"C:\Windows\Fonts\DejaVuSansMono.ttf")],
    )
    result = generate(arguments.output.resolve(), cjk, mono, _renderer(arguments.pdftoppm))
    print(json.dumps({"status": "generated", "fixture_id": result["fixture_id"], "documents": result["documents"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
