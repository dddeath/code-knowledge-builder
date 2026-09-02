"""Small deterministic PDF fixtures built without a PDF authoring dependency."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _pdf_string(value: str) -> str:
    encoded = value.encode("cp1252")
    escaped = encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return "(" + escaped.decode("latin-1") + ")"


def _write_objects(path: Path, objects: list[bytes]) -> None:
    value = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(value))
        value.extend(f"{number} 0 obj\n".encode("ascii"))
        value.extend(body)
        value.extend(b"\nendobj\n")
    xref = len(value)
    value.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    value.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        value.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    value.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode("ascii")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(value))


def ascii_pdf(path: Path, pages: list[list[tuple[float, float, str]]]) -> Path:
    """Write pages containing Type1 WinAnsi text at explicit coordinates."""

    page_refs = [4 + index * 2 for index in range(len(pages))]
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(f'{number} 0 R' for number in page_refs)}] >>".encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>",
    ]
    for index, commands in enumerate(pages):
        page_number = page_refs[index]
        content_number = page_number + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>"
            ).encode("ascii")
        )
        content = ["BT", "/F1 12 Tf"]
        for x, y, text in commands:
            content.append(f"1 0 0 1 {x:g} {y:g} Tm {_pdf_string(text)} Tj")
        content.append("ET")
        stream = ("\n".join(content) + "\n").encode("latin-1")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"endstream")
    _write_objects(path, objects)
    return path


def blank_pdf(path: Path, page_count: int = 1) -> Path:
    return ascii_pdf(path, [[] for _ in range(page_count)])


def chinese_pdf(path: Path, lines: Iterable[str]) -> Path:
    """Write one Type0 page with a deterministic ToUnicode map."""

    lines = list(lines)
    characters = sorted(set("".join(lines)))
    codes = {character: index + 1 for index, character in enumerate(characters)}
    bfchar = "\n".join(f"<{code:04X}> <{ord(character):04X}>" for character, code in codes.items())
    cmap = (
        "/CIDInit /ProcSet findresource begin\n"
        "12 dict begin\n"
        "begincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /CKBFixture def\n"
        "/CMapType 2 def\n"
        "1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n"
        f"{len(characters)} beginbfchar\n{bfchar}\nendbfchar\n"
        "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n"
    ).encode("ascii")
    content = ["BT", "/F1 12 Tf"]
    y = 740
    for line in lines:
        encoded = "".join(f"{codes[character]:04X}" for character in line)
        content.append(f"1 0 0 1 72 {y} Tm <{encoded}> Tj")
        y -= 24
    content.append("ET")
    stream = ("\n".join(content) + "\n").encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [6 0 R] >>",
        b"<< /Type /Font /Subtype /Type0 /BaseFont /CKBFixture /Encoding /Identity-H /DescendantFonts [4 0 R] /ToUnicode 5 0 R >>",
        b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /CKBFixture /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /CIDToGIDMap /Identity >>",
        f"<< /Length {len(cmap)} >>\nstream\n".encode("ascii") + cmap + b"endstream",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents 7 0 R >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"endstream",
    ]
    _write_objects(path, objects)
    return path


def encrypt_pdf(source: Path, target: Path, parser_module, password: str = "fixture-secret") -> Path:
    reader = parser_module.PdfReader(str(source), strict=True)
    writer = parser_module.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with target.open("wb") as stream:
        writer.write(stream)
    return target
