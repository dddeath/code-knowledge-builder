"""Reviewed local Markdown/TXT references kept separate from fixed code facts."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
from typing import Any
from urllib.parse import quote

from .common import CkbError, json_load, json_write, safe_title, sha256_file, stable_id, utc_now
from .machine_knowledge import contains_chinese_narrative


REFERENCE_SCHEMA_VERSION = 1
MAX_REFERENCE_BYTES = 2 * 1024 * 1024
SUPPORTED_SUFFIXES = {".md": "markdown", ".txt": "text"}
INVALID_LICENSE_VALUES = {"", "unknown", "unspecified", "none", "n/a", "na", "待定", "未知"}
REFERENCE_TAG = "#类型/资料"
REFERENCE_INDEX = "REFERENCES.md"
LONG_HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{40,}(?![0-9A-Fa-f])")


def _root(output: Path) -> Path:
    return output.resolve() / "references"


def _manifests(output: Path) -> list[dict[str, Any]]:
    directory = _root(output) / "manifests"
    return [json_load(path) for path in sorted(directory.glob("*.json"))] if directory.is_dir() else []


def _manifest(output: Path, reference_id: str) -> tuple[Path, dict[str, Any]]:
    path = _root(output) / "manifests" / f"{reference_id}.json"
    if not path.is_file():
        raise CkbError(f"reference does not exist: {reference_id}")
    return path, json_load(path)


def _validate_output(output: Path) -> Path:
    output = output.resolve()
    if not (output / "state.json").is_file() or not (output / "human").is_dir() or not (output / "markdown").is_dir():
        raise CkbError(f"completed CKB Markdown output is required: {output}")
    return output


def _validate_license(value: str) -> str:
    normalized = value.strip()
    if normalized.casefold() in INVALID_LICENSE_VALUES:
        raise CkbError("reference license must be an explicit SPDX identifier or a concrete user-provided license statement")
    return normalized


def _decode_source(source: Path) -> tuple[bytes, str, str]:
    suffix = source.suffix.casefold()
    if suffix not in SUPPORTED_SUFFIXES:
        raise CkbError("reference source must be a local UTF-8 .md or .txt file")
    raw = source.read_bytes()
    if not raw or len(raw) > MAX_REFERENCE_BYTES:
        raise CkbError(f"reference source must contain 1..{MAX_REFERENCE_BYTES} bytes")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CkbError(f"reference source must be valid UTF-8: {exc}") from exc
    if "\x00" in text:
        raise CkbError("reference source contains a NUL byte and is not treated as text")
    return raw, text.replace("\r\n", "\n").replace("\r", "\n"), SUPPORTED_SUFFIXES[suffix]


def _set_marker(output: Path, status: str, payload: dict[str, Any]) -> None:
    root = _root(output)
    for name in (".pending-agent-review", ".failed", ".complete"):
        (root / name).unlink(missing_ok=True)
    name = ".complete" if status == "passed" else ".pending-agent-review" if status == "pending-agent-review" else ".failed"
    json_write(root / name, payload)


def ingest_reference(
    output: Path,
    source: Path,
    title: str,
    origin: str,
    license_name: str,
    author: str | None = None,
    revision_of: str | None = None,
) -> dict[str, Any]:
    output = _validate_output(output)
    source = source.resolve()
    if not source.is_file():
        raise CkbError(f"reference source does not exist: {source}")
    title = title.strip()
    origin = origin.strip()
    if not title or not origin:
        raise CkbError("reference title and origin are required")
    license_name = _validate_license(license_name)
    raw, _text, source_type = _decode_source(source)
    digest = __import__("hashlib").sha256(raw).hexdigest()
    existing = _manifests(output)
    same_key = [
        item for item in existing
        if str(item.get("title", "")).casefold() == title.casefold()
        and str(item.get("origin", "")).casefold() == origin.casefold()
    ]
    title_conflicts = [
        item for item in existing
        if str(item.get("title", "")).casefold() == title.casefold()
        and str(item.get("origin", "")).casefold() != origin.casefold()
        and item.get("status") != "superseded"
    ]
    if title_conflicts:
        raise CkbError(f"active reference title must be unique: {title}; existing={title_conflicts[0]['reference_id']}")
    for item in same_key:
        if item.get("source_sha256") == digest and item.get("license") == license_name:
            return {
                "schema_version": REFERENCE_SCHEMA_VERSION,
                "status": item["status"],
                "reference_id": item["reference_id"],
                "idempotent": True,
                "manifest": str((_root(output) / "manifests" / f"{item['reference_id']}.json").resolve()),
                "review_template": item.get("review_template"),
            }
    latest = max(same_key, key=lambda item: int(item.get("revision", 1)), default=None)
    if latest:
        if not revision_of:
            raise CkbError(f"reference source changed; pass --revision-of {latest['reference_id']} to create a reviewed revision")
        if revision_of != latest["reference_id"]:
            raise CkbError(f"--revision-of must name the latest reference revision: {latest['reference_id']}")
        if latest.get("status") != "agent-reviewed":
            raise CkbError("a new revision requires the previous revision to be agent-reviewed")
    elif revision_of:
        raise CkbError("--revision-of was provided but no previous reference exists for this title and origin")
    reference_id = stable_id("reference", title.casefold(), origin.casefold(), digest)
    root = _root(output)
    for name in ("raw", "manifests", "review-templates", "reviews", "transactions"):
        (root / name).mkdir(parents=True, exist_ok=True)
    revision = int(latest.get("revision", 1)) + 1 if latest else 1
    raw_path = root / "raw" / f"{safe_title(title)}--r{revision}{source.suffix.casefold()}"
    raw_path.write_bytes(raw)
    review_template_path = root / "review-templates" / f"{reference_id}.json"
    manifest_path = root / "manifests" / f"{reference_id}.json"
    manifest = {
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "reference_id": reference_id,
        "status": "pending-agent-review",
        "title": title,
        "origin": origin,
        "author": (author or "").strip() or None,
        "license": license_name,
        "copy_permission": "full-text",
        "source_type": source_type,
        "source_suffix": source.suffix.casefold(),
        "source_file": str(raw_path.resolve()),
        "source_relative": raw_path.relative_to(output).as_posix(),
        "source_sha256": digest,
        "source_size": len(raw),
        "revision": revision,
        "supersedes": latest["reference_id"] if latest else None,
        "review_template": str(review_template_path.resolve()),
        "review_file": None,
        "human_file": None,
        "ingested_at_utc": utc_now(),
    }
    template = {
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "reference_id": reference_id,
        "status": "pending-agent-review",
        "title": title,
        "source_file": str(raw_path.resolve()),
        "source_sha256": digest,
        "summary_zh": "",
        "claims": [],
    }
    json_write(manifest_path, manifest)
    json_write(review_template_path, template)
    transaction = {
        "schema_version": 1,
        "reference_id": reference_id,
        "status": "pending-agent-review",
        "created_files": [str(raw_path.resolve()), str(manifest_path.resolve()), str(review_template_path.resolve())],
        "baseline_reference_ids": [item["reference_id"] for item in existing],
    }
    json_write(root / "transactions" / f"{reference_id}.json", transaction)
    from .machine_knowledge import build_machine_knowledge

    build_machine_knowledge(output)
    _set_marker(output, "pending-agent-review", {"reference_id": reference_id, "review_template": str(review_template_path.resolve())})
    return {
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "status": "pending-agent-review",
        "reference_id": reference_id,
        "revision": revision,
        "idempotent": False,
        "source": str(raw_path.resolve()),
        "manifest": str(manifest_path.resolve()),
        "review_template": str(review_template_path.resolve()),
        "next": "reference review",
    }


def write_reference_review_template(output: Path, reference_id: str, target: Path) -> dict[str, Any]:
    output = _validate_output(output)
    _path, manifest = _manifest(output, reference_id)
    source = Path(str(manifest["review_template"]))
    target = target.resolve()
    if target.exists():
        raise CkbError(f"reference review target already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {"schema_version": 1, "status": "written", "reference_id": reference_id, "review": str(target)}


def _source_lines(manifest: dict[str, Any]) -> list[str]:
    raw = Path(str(manifest["source_file"])).read_bytes()
    if __import__("hashlib").sha256(raw).hexdigest() != manifest.get("source_sha256"):
        raise CkbError(f"reference source drifted: {manifest['reference_id']}")
    return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _validate_review(manifest: dict[str, Any], review: dict[str, Any]) -> None:
    if review.get("schema_version") != REFERENCE_SCHEMA_VERSION:
        raise CkbError("reference review schema_version mismatch")
    if review.get("reference_id") != manifest["reference_id"] or review.get("status") != "agent-reviewed":
        raise CkbError("reference review must target one manifest and use status agent-reviewed")
    if review.get("source_sha256") != manifest["source_sha256"]:
        raise CkbError("reference review source_sha256 does not match the preserved source")
    if not contains_chinese_narrative(review.get("summary_zh")):
        raise CkbError("reference summary_zh must contain useful Simplified-Chinese narrative")
    claims = review.get("claims")
    if not isinstance(claims, list) or not claims:
        raise CkbError("reference review requires at least one source-grounded claim")
    lines = _source_lines(manifest)
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise CkbError(f"reference claim {index} must be an object")
        if not contains_chinese_narrative(claim.get("claim_zh")) or not contains_chinese_narrative(claim.get("evidence_note")):
            raise CkbError(f"reference claim {index} requires Chinese claim_zh and evidence_note")
        start = claim.get("start_line")
        end = claim.get("end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(lines):
            raise CkbError(f"reference claim {index} has an invalid inclusive line range")
        expected = "\n".join(lines[start - 1 : end]).strip()
        if not expected or str(claim.get("source_text") or "").strip() != expected:
            raise CkbError(f"reference claim {index} source_text does not exactly match the preserved line range")


def _source_uri(path: Path, line: int = 1) -> str:
    value = path.resolve().as_posix()
    return f"vscode://file/{quote(value, safe='/:')}:{line}:1"


def _render_reference_page(manifest: dict[str, Any], review: dict[str, Any]) -> str:
    raw = Path(str(manifest["source_file"]))
    lines = [
        f"# {manifest['title']}",
        "",
        f"标签：{REFERENCE_TAG}",
        "",
        "## 这份资料讲什么",
        "",
        str(review["summary_zh"]).strip(),
        "",
        "## 关键结论",
        "",
    ]
    for claim in review["claims"]:
        start = int(claim["start_line"])
        end = int(claim["end_line"])
        label = f"原文第 {start} 行" if start == end else f"原文第 {start}–{end} 行"
        lines.append(f"- {str(claim['claim_zh']).strip()}（[{label}]({_source_uri(raw, start)}））")
    lines.extend(
        [
            "",
            "## 来源",
            "",
            f"- 资料来源：{manifest['origin']}",
            f"- 作者或组织：{manifest.get('author') or '来源中未单列'}",
            f"- 许可：{manifest['license']}",
            f"- [打开归档原文]({_source_uri(raw)})",
            "",
        ]
    )
    text = "\n".join(lines)
    if LONG_HEX.search(text):
        raise CkbError("human reference page exposed a machine hash-like identifier")
    return text


def _active_reviewed(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [item for item in manifests if item.get("status") == "agent-reviewed"],
        key=lambda item: (str(item["title"]).casefold(), str(item["reference_id"])),
    )


def project_references(output: Path) -> dict[str, Any]:
    output = _validate_output(output)
    root = _root(output)
    manifests = _manifests(output)
    active = _active_reviewed(manifests)
    previous_path = root / "projection.json"
    previous = json_load(previous_path) if previous_path.is_file() else {"files": []}
    for vault_name in ("human", "markdown"):
        vault = output / vault_name
        for relative in previous.get("files", []):
            path = vault / str(relative)
            if path.is_file():
                path.unlink()
        (vault / "references").mkdir(parents=True, exist_ok=True)
    pages: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for manifest in active:
        title = str(manifest["title"])
        if title.casefold() in seen_titles:
            raise CkbError(f"active reference titles must be unique: {title}")
        seen_titles.add(title.casefold())
        review = json_load(Path(str(manifest["review_file"])))
        _validate_review(manifest, review)
        filename = safe_title(title) + ".md"
        relative = Path("references") / filename
        text = _render_reference_page(manifest, review)
        for vault_name in ("human", "markdown"):
            target = output / vault_name / relative
            target.write_text(text, encoding="utf-8", newline="\n")
        manifest["human_file"] = relative.as_posix()
        json_write(root / "manifests" / f"{manifest['reference_id']}.json", manifest)
        pages.append(
            {
                "reference_id": manifest["reference_id"],
                "title": title,
                "file": relative.as_posix(),
                "summary_zh": str(review["summary_zh"]).strip(),
                "revision": manifest["revision"],
            }
        )
    index_lines = [
        "# 参考资料导览",
        "",
        "标签：#类型/导览",
        "",
        "> 这里汇总经过来源、许可和逐项引用审阅的外部文本资料；参考资料不会被当作代码来源实体。",
        "",
    ]
    if pages:
        index_lines.extend(["## 已审阅资料", ""])
        for page in pages:
            summary = re.split(r"(?<=[。！？])", page["summary_zh"], maxsplit=1)[0].strip()
            index_lines.append(f"- [[{page['title']}]] — {summary}")
    index_text = "\n".join(index_lines).rstrip() + "\n"
    for vault_name in ("human", "markdown"):
        target = output / vault_name / REFERENCE_INDEX
        if pages:
            target.write_text(index_text, encoding="utf-8", newline="\n")
        else:
            target.unlink(missing_ok=True)
    files = [REFERENCE_INDEX, *[page["file"] for page in pages]] if pages else []
    projection = {
        "schema_version": 1,
        "status": "ready",
        "page_count": len(pages),
        "page_limit_per_source": 1,
        "pages": pages,
        "files": files,
        "projected_at_utc": utc_now(),
    }
    json_write(previous_path, projection)
    from .pipeline import refresh_human_navigation

    refresh_human_navigation(output)
    from .agent_index import build_agent_index
    from .machine_knowledge import build_machine_knowledge

    build_machine_knowledge(output)
    build_agent_index(output)
    return projection


def submit_reference_review(output: Path, review_path: Path) -> dict[str, Any]:
    output = _validate_output(output)
    review = json_load(review_path.resolve())
    reference_id = str(review.get("reference_id") or "")
    manifest_path, manifest = _manifest(output, reference_id)
    _validate_review(manifest, review)
    target = _root(output) / "reviews" / f"{reference_id}.json"
    json_write(target, review)
    manifest["status"] = "agent-reviewed"
    manifest["review_file"] = str(target.resolve())
    manifest["reviewed_at_utc"] = utc_now()
    json_write(manifest_path, manifest)
    if manifest.get("supersedes"):
        previous_path, previous = _manifest(output, str(manifest["supersedes"]))
        previous["status"] = "superseded"
        previous["superseded_by"] = reference_id
        json_write(previous_path, previous)
    projection = project_references(output)
    _projected_path, projected_manifest = _manifest(output, reference_id)
    audit = audit_references(output)
    if audit["status"] != "passed":
        raise CkbError(f"reference audit failed after review: {audit['errors'][:10]}")
    _set_marker(output, "passed", {"reference_ids": [item["reference_id"] for item in _active_reviewed(_manifests(output))], "audit": str((_root(output) / "audit.json").resolve())})
    return {
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "status": "agent-reviewed",
        "reference_id": reference_id,
        "human_file": str((output / "human" / str(projected_manifest["human_file"])).resolve()),
        "compatibility_file": str((output / "markdown" / str(projected_manifest["human_file"])).resolve()),
        "projection": projection,
        "audit": audit,
    }


def reference_machine_records(output: Path) -> dict[str, Any]:
    manifests = _manifests(output)
    sources = [dict(item) for item in manifests]
    documents: list[dict[str, Any]] = []
    for manifest in _active_reviewed(manifests):
        review_path = Path(str(manifest.get("review_file") or ""))
        human_relative = str(manifest.get("human_file") or "")
        human_path = output / "human" / human_relative
        if not review_path.is_file() or not human_path.is_file():
            continue
        review = json_load(review_path)
        lines = _source_lines(manifest)
        sections = _reference_sections(lines, manifest["source_type"])
        documents.append(
            {
                "document_id": f"reference:{manifest['reference_id']}",
                "reference_id": manifest["reference_id"],
                "kind": "reference",
                "title": manifest["title"],
                "tag": REFERENCE_TAG,
                "human_file": human_relative,
                "content": human_path.read_text(encoding="utf-8"),
                "links": re.findall(r"\[\[([^\]|#]+)", human_path.read_text(encoding="utf-8")),
                "sections": sections,
                "raw_file": manifest["source_file"],
                "summary_zh": review["summary_zh"],
            }
        )
    return {"sources": sources, "documents": documents}


def _reference_sections(lines: list[str], source_type: str) -> list[dict[str, Any]]:
    if source_type == "text":
        result = []
        for start in range(0, len(lines), 80):
            content = "\n".join(lines[start : start + 80]).strip()
            if content:
                result.append({"heading": f"原文 {start + 1}–{min(len(lines), start + 80)} 行", "content": content, "start_line": start + 1, "end_line": min(len(lines), start + 80)})
        return result
    headings: list[tuple[int, str]] = []
    in_fence = False
    for index, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append((index, match.group(1).strip()))
    if not headings:
        return _reference_sections(lines, "text")
    result = []
    for position, (start, heading) in enumerate(headings):
        end = headings[position + 1][0] - 1 if position + 1 < len(headings) else len(lines)
        content = "\n".join(lines[start - 1 : end]).strip()
        if content:
            result.append({"heading": heading, "content": content, "start_line": start, "end_line": end})
    return result


def audit_references(output: Path) -> dict[str, Any]:
    output = _validate_output(output)
    root = _root(output)
    manifests = _manifests(output)
    errors: list[dict[str, Any]] = []
    pending = 0
    superseded = 0
    for manifest in manifests:
        reference_id = str(manifest.get("reference_id") or "")
        source = Path(str(manifest.get("source_file") or ""))
        if not source.is_file():
            errors.append({"reason": "reference-source-missing", "reference_id": reference_id})
            continue
        if sha256_file(source) != manifest.get("source_sha256"):
            errors.append({"reason": "reference-source-drift", "reference_id": reference_id})
        try:
            _validate_license(str(manifest.get("license") or ""))
            _decode_source(source)
        except CkbError as exc:
            errors.append({"reason": "reference-source-invalid", "reference_id": reference_id, "detail": str(exc)})
        status = manifest.get("status")
        if status == "pending-agent-review":
            pending += 1
        elif status == "superseded":
            superseded += 1
        elif status == "agent-reviewed":
            review = Path(str(manifest.get("review_file") or ""))
            try:
                if not review.is_file():
                    raise CkbError("review file is missing")
                _validate_review(manifest, json_load(review))
            except CkbError as exc:
                errors.append({"reason": "reference-review-invalid", "reference_id": reference_id, "detail": str(exc)})
        else:
            errors.append({"reason": "reference-status-invalid", "reference_id": reference_id, "status": status})
    active = _active_reviewed(manifests)
    projection_path = root / "projection.json"
    projection = json_load(projection_path) if projection_path.is_file() else {"pages": [], "files": []}
    expected_ids = {item["reference_id"] for item in active}
    actual_ids = {item["reference_id"] for item in projection.get("pages", [])}
    if actual_ids != expected_ids:
        errors.append({"reason": "reference-projection-set", "missing": sorted(expected_ids - actual_ids), "extra": sorted(actual_ids - expected_ids)})
    if int(projection.get("page_count", 0)) != len(active) or int(projection.get("page_limit_per_source", 1)) != 1:
        errors.append({"reason": "reference-page-quota", "active": len(active), "projection": projection.get("page_count")})
    for item in projection.get("pages", []):
        relative = str(item["file"])
        left = output / "markdown" / relative
        right = output / "human" / relative
        if not left.is_file() or not right.is_file() or left.read_bytes() != right.read_bytes():
            errors.append({"reason": "reference-page-mirror", "path": relative})
        elif not contains_chinese_narrative(left.read_text(encoding="utf-8")) or LONG_HEX.search(left.read_text(encoding="utf-8")):
            errors.append({"reason": "reference-page-human-contract", "path": relative})
    left_index = output / "markdown" / REFERENCE_INDEX
    right_index = output / "human" / REFERENCE_INDEX
    if active and (not left_index.is_file() or not right_index.is_file() or left_index.read_bytes() != right_index.read_bytes()):
        errors.append({"reason": "reference-index-mirror"})
    machine = output / "machine/knowledge.sqlite"
    machine_counts = {"sources": 0, "documents": 0}
    if machine.is_file():
        import sqlite3

        connection = sqlite3.connect(f"file:{machine.as_posix()}?mode=ro", uri=True)
        try:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "reference_sources" in tables:
                machine_counts["sources"] = connection.execute("SELECT count(*) FROM reference_sources").fetchone()[0]
                machine_counts["documents"] = connection.execute("SELECT count(*) FROM documents WHERE kind='reference'").fetchone()[0]
            elif manifests and pending == 0:
                errors.append({"reason": "reference-machine-table-missing"})
        finally:
            connection.close()
        if pending == 0 and (machine_counts["sources"] != len(manifests) or machine_counts["documents"] != len(active)):
            errors.append({"reason": "reference-machine-count", "actual": machine_counts, "expected": {"sources": len(manifests), "documents": len(active)}})
    elif manifests:
        errors.append({"reason": "reference-machine-missing"})
    status = "failed" if errors else "pending-agent-review" if pending else "passed"
    result = {
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "status": status,
        "counts": {"total": len(manifests), "active": len(active), "pending": pending, "superseded": superseded},
        "page_count": len(projection.get("pages", [])),
        "page_limit_per_source": 1,
        "machine_counts": machine_counts,
        "errors": errors,
    }
    root.mkdir(parents=True, exist_ok=True)
    json_write(root / "audit.json", result)
    _set_marker(output, status, {"audit": str((root / "audit.json").resolve()), "counts": result["counts"], "errors": errors})
    return result


def list_references(output: Path, status: str = "all") -> dict[str, Any]:
    output = _validate_output(output)
    records = _manifests(output)
    if status != "all":
        records = [item for item in records if item.get("status") == status]
    return {
        "schema_version": 1,
        "status": "ready",
        "count": len(records),
        "records": [
            {key: item.get(key) for key in ("reference_id", "status", "title", "origin", "license", "revision", "supersedes", "human_file")}
            for item in records
        ],
    }


def rollback_reference(output: Path, reference_id: str) -> dict[str, Any]:
    output = _validate_output(output)
    manifest_path, manifest = _manifest(output, reference_id)
    if manifest.get("superseded_by"):
        raise CkbError(f"rollback the active superseding revision first: {manifest['superseded_by']}")
    restored = None
    if manifest.get("supersedes"):
        previous_path, previous = _manifest(output, str(manifest["supersedes"]))
        previous["status"] = "agent-reviewed"
        previous.pop("superseded_by", None)
        json_write(previous_path, previous)
        restored = previous["reference_id"]
    for value in (
        manifest.get("source_file"),
        manifest.get("review_template"),
        manifest.get("review_file"),
        str(_root(output) / "transactions" / f"{reference_id}.json"),
        str(manifest_path),
    ):
        path = Path(str(value or ""))
        if path.is_file():
            path.unlink()
    project_references(output)
    audit = audit_references(output)
    if audit["status"] not in {"passed", "pending-agent-review"}:
        raise CkbError(f"reference rollback audit failed: {audit['errors'][:10]}")
    return {"schema_version": 1, "status": "rolled-back", "reference_id": reference_id, "restored_reference_id": restored, "audit": audit}
