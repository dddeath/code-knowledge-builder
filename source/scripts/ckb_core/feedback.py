"""Deterministic, location-anchored human feedback for knowledge pages.

The fixed source graph remains generator-owned.  Feedback is stored as machine
JSON under ``workspace-meta`` and projected as small, frontmatter-free Chinese
Markdown records into both human vaults.  Resolved feedback is archived rather
than deleted.
"""

from __future__ import annotations

from collections import defaultdict
import datetime as dt
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .common import CkbError, json_load, json_write, path_inside, safe_title, utc_now


FEEDBACK_SCHEMA_VERSION = 1
FEEDBACK_DIRECTORIES = ("feedback/open", "feedback/resolved")
SEVERITIES = ("error", "warn", "suggest", "info")
SOURCES = ("manual", "obsidian-plugin", "web-viewer")
DECISIONS = ("accepted", "partial", "rejected", "deferred")
SEVERITY_ORDER = {value: index for index, value in enumerate(SEVERITIES)}
STATUS_DIRECTORY = {"open": "open", "resolved": "resolved"}
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
LONG_HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{40,}(?![0-9A-Fa-f])")


def _contains_chinese(value: Any, minimum_han: int = 2) -> bool:
    return isinstance(value, str) and len(CHINESE_RE.findall(value)) >= minimum_han


def prepare_feedback_store(output: Path) -> dict[str, Any]:
    """Create only the feedback-owned directories for a finalized Markdown KB."""
    output = output.resolve()
    metadata = output / "workspace-meta/feedback"
    for status in STATUS_DIRECTORY.values():
        (metadata / status).mkdir(parents=True, exist_ok=True)
    vaults = []
    for name in ("markdown", "human"):
        root = output / name
        if root.is_dir():
            for relative in FEEDBACK_DIRECTORIES:
                (root / relative).mkdir(parents=True, exist_ok=True)
            vaults.append(str(root.resolve()))
    return {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "ready",
        "metadata_root": str(metadata.resolve()),
        "vaults": vaults,
    }


def _canonical_relative_target(output: Path, target: Path) -> tuple[str, Path, Path]:
    output = output.resolve()
    human = output / "human"
    markdown = output / "markdown"
    if not human.is_dir() or not markdown.is_dir():
        raise CkbError("feedback requires finalized human and markdown knowledge roots")
    raw = str(target).replace("\\", "/")
    candidate = Path(target)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if path_inside(resolved, human):
            relative = resolved.relative_to(human).as_posix()
        elif path_inside(resolved, markdown):
            relative = resolved.relative_to(markdown).as_posix()
        else:
            raise CkbError("feedback target must be inside OUTPUT/human or OUTPUT/markdown")
    else:
        for prefix in ("human/", "markdown/"):
            if raw.startswith(prefix):
                raw = raw[len(prefix) :]
                break
        pure = PurePosixPath(raw)
        if pure.is_absolute() or ".." in pure.parts:
            raise CkbError("feedback target must be a knowledge-root relative path")
        relative = pure.as_posix().lstrip("./")
    if not relative or relative.startswith("feedback/") or not relative.endswith(".md"):
        raise CkbError("feedback target must be a non-feedback Markdown knowledge page")
    human_target = human / relative
    markdown_target = markdown / relative
    if not human_target.is_file() or not markdown_target.is_file():
        raise CkbError(f"feedback target is missing from the mirrored human knowledge roots: {relative}")
    if human_target.read_bytes() != markdown_target.read_bytes():
        raise CkbError(f"feedback target differs between human and markdown roots: {relative}")
    return relative, human_target, markdown_target


def _read_chinese_body(path: Path, label: str) -> str:
    if not path.is_file():
        raise CkbError(f"{label} body does not exist: {path}")
    value = path.read_text(encoding="utf-8-sig").strip()
    if not value:
        raise CkbError(f"{label} body must not be empty")
    if not _contains_chinese(value):
        raise CkbError(f"{label} narrative must use Simplified Chinese")
    if value.startswith("---\n") or LONG_HEX.search(value):
        raise CkbError(f"{label} body must omit frontmatter and hash-like identifiers")
    return value


def _line_selection(text: str, start_line: int, end_line: int) -> tuple[str, str, str]:
    if start_line < 1 or end_line < start_line:
        raise CkbError("feedback line range must be a positive inclusive range")
    lines = text.splitlines(keepends=True)
    if end_line > len(lines):
        raise CkbError(f"feedback line range exceeds target length: {end_line}>{len(lines)}")
    start_offset = sum(len(value) for value in lines[: start_line - 1])
    end_offset = sum(len(value) for value in lines[:end_line])
    anchor_text = text[start_offset:end_offset]
    if not anchor_text:
        raise CkbError("feedback selection must not be empty")
    return text[max(0, start_offset - 80) : start_offset], anchor_text, text[end_offset : end_offset + 80]


def _next_feedback_id(output: Path) -> str:
    prefix = dt.datetime.now(dt.timezone.utc).strftime("feedback-%Y%m%d-%H%M%S")
    existing = {
        path.stem
        for status in STATUS_DIRECTORY.values()
        for path in (output / "workspace-meta/feedback" / status).glob(f"{prefix}-*.json")
    }
    index = 1
    while f"{prefix}-{index:02d}" in existing:
        index += 1
    return f"{prefix}-{index:02d}"


def _title_of(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text else ""
    return first.removeprefix("# ").strip() or path.stem


def _blockquote(value: str) -> str:
    lines = value.rstrip("\n").splitlines() or [""]
    return "\n".join("> " + line for line in lines)


def _visible_feedback(record: dict[str, Any]) -> str:
    severity_names = {"error": "错误", "warn": "警告", "suggest": "建议", "info": "说明"}
    status_names = {"open": "待处理", "resolved": "已归档"}
    source_names = {"manual": "手动", "obsidian-plugin": "Obsidian", "web-viewer": "本地查看器"}
    decision_names = {"accepted": "采纳", "partial": "部分采纳", "rejected": "不采纳", "deferred": "暂缓"}
    sections = [
        f"# {record['title']}",
        "",
        "标签：#类型/反馈",
        "",
        f"状态：{status_names[record['status']]}",
        f"严重程度：{severity_names[record['severity']]}",
        f"目标：[[{record['target_title']}]]（`{record['target']}` 第 {record['target_lines'][0]}–{record['target_lines'][1]} 行）",
        f"来源：{source_names[record['source']]}，提交者 `{record['author']}`",
        "",
        "## 反馈内容",
        "",
        record["comment"].strip(),
        "",
        "## 锚点摘录",
        "",
        _blockquote(record["anchor_text"]),
    ]
    if record.get("decision"):
        sections.extend(
            [
                "",
                "## 处理结果",
                "",
                f"决议：{decision_names[record['decision']]}。",
                "",
                str(record.get("resolution") or "").strip(),
            ]
        )
        if record.get("applied_record"):
            sections.extend(["", f"落实记录：`{record['applied_record']}`"])
    return "\n".join(sections).rstrip() + "\n"


def _record_path(output: Path, status: str, feedback_id: str) -> Path:
    return output / "workspace-meta/feedback" / STATUS_DIRECTORY[status] / f"{feedback_id}.json"


def _visible_relative(status: str, feedback_id: str) -> Path:
    return Path("feedback") / STATUS_DIRECTORY[status] / f"{feedback_id}.md"


def _write_visible_mirrors(output: Path, record: dict[str, Any]) -> list[str]:
    text = _visible_feedback(record)
    relative = _visible_relative(record["status"], record["id"])
    paths = []
    for root_name in ("markdown", "human"):
        path = output / root_name / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        paths.append(str(path.resolve()))
    return paths


def create_feedback(
    output: Path,
    target: Path,
    start_line: int,
    end_line: int,
    comment_path: Path,
    severity: str,
    author: str,
    source: str,
) -> dict[str, Any]:
    output = output.resolve()
    if severity not in SEVERITIES:
        raise CkbError(f"feedback severity must be one of: {list(SEVERITIES)}")
    if source not in SOURCES:
        raise CkbError(f"feedback source must be one of: {list(SOURCES)}")
    if not author.strip():
        raise CkbError("feedback author must not be empty")
    prepare_feedback_store(output)
    relative, human_target, _ = _canonical_relative_target(output, target)
    target_text = human_target.read_text(encoding="utf-8-sig")
    before, anchor, after = _line_selection(target_text, start_line, end_line)
    comment = _read_chinese_body(comment_path.resolve(), "feedback")
    feedback_id = _next_feedback_id(output)
    target_title = _title_of(human_target)
    created_at = utc_now()
    record = {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "id": feedback_id,
        "status": "open",
        "target": relative,
        "target_title": target_title,
        "title": f"关于 {target_title} 的反馈（{created_at.replace('T', ' ').removesuffix('Z')} UTC，第 {feedback_id.rsplit('-', 1)[1]} 条）",
        "target_lines": [start_line, end_line],
        "anchor_before": before,
        "anchor_text": anchor,
        "anchor_after": after,
        "severity": severity,
        "author": author.strip(),
        "source": source,
        "created_at_utc": created_at,
        "comment": comment,
        "decision": None,
        "resolution": None,
        "applied_record": None,
        "resolved_at_utc": None,
    }
    json_write(_record_path(output, "open", feedback_id), record)
    record["visible_files"] = _write_visible_mirrors(output, record)
    result = {**record, "anchor": locate_feedback(output, feedback_id)["anchor"]}
    audit = audit_feedback(output)
    if audit["status"] != "passed":
        raise CkbError(f"feedback audit failed after create: {audit['errors'][:10]}")
    return result


def _load_feedback(output: Path, feedback_id: str) -> tuple[dict[str, Any], Path]:
    if not re.fullmatch(r"feedback-\d{8}-\d{6}-\d{2,}", feedback_id):
        raise CkbError("feedback identifier has an invalid shape")
    matches = [path for status in STATUS_DIRECTORY for path in [_record_path(output, status, feedback_id)] if path.is_file()]
    if len(matches) != 1:
        raise CkbError(f"feedback identifier must resolve to exactly one record: {feedback_id}")
    return json_load(matches[0]), matches[0]


def _all_offsets(text: str, needle: str) -> list[int]:
    offsets = []
    start = 0
    while needle:
        value = text.find(needle, start)
        if value < 0:
            break
        offsets.append(value)
        start = value + 1
    return offsets


def _offset_lines(text: str, start: int, end: int) -> list[int]:
    return [text.count("\n", 0, start) + 1, text.count("\n", 0, max(start, end - 1)) + 1]


def _locate_anchor(text: str, record: dict[str, Any]) -> dict[str, Any]:
    start_line, end_line = [int(value) for value in record["target_lines"]]
    lines = text.splitlines(keepends=True)
    if 1 <= start_line <= end_line <= len(lines):
        start = sum(len(value) for value in lines[: start_line - 1])
        end = sum(len(value) for value in lines[:end_line])
        if record["anchor_text"] in text[start:end]:
            return {"status": "line-range", "current_lines": [start_line, end_line], "match_count": 1}
    offsets = _all_offsets(text, str(record["anchor_text"]))
    if len(offsets) == 1:
        start = offsets[0]
        return {
            "status": "unique-text",
            "current_lines": _offset_lines(text, start, start + len(record["anchor_text"])),
            "match_count": 1,
        }
    if len(offsets) > 1:
        window = str(record["anchor_before"]) + str(record["anchor_text"]) + str(record["anchor_after"])
        windows = _all_offsets(text, window)
        if len(windows) == 1:
            start = windows[0] + len(record["anchor_before"])
            return {
                "status": "anchor-window",
                "current_lines": _offset_lines(text, start, start + len(record["anchor_text"])),
                "match_count": len(offsets),
            }
    return {"status": "stale", "current_lines": None, "match_count": len(offsets)}


def locate_feedback(output: Path, feedback_id: str) -> dict[str, Any]:
    output = output.resolve()
    record, path = _load_feedback(output, feedback_id)
    relative, human_target, _ = _canonical_relative_target(output, Path(str(record["target"])))
    anchor = _locate_anchor(human_target.read_text(encoding="utf-8-sig"), record)
    return {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "passed" if anchor["status"] != "stale" else "stale",
        "feedback_id": feedback_id,
        "feedback_status": record["status"],
        "target": relative,
        "record": str(path.resolve()),
        "anchor": anchor,
    }


def _canonical_applied_record(output: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    if not resolved.is_file() or not path_inside(resolved, output.resolve()):
        raise CkbError("applied record must be an existing file inside the knowledge output")
    relative = resolved.relative_to(output.resolve())
    if len(relative.parts) < 3 or relative.parts[0] not in {"human", "markdown"}:
        raise CkbError("applied record must point to a reviewed human knowledge note")
    note_directories = {"analysis", "changes", "pitfalls", "experiments", "sessions"}
    if relative.parts[1] not in note_directories or resolved.suffix.casefold() != ".md":
        raise CkbError("applied record must point to an analysis, change, pitfall, experiment, or session note")
    note_relative = Path(*relative.parts[1:])
    human = output / "human" / note_relative
    markdown = output / "markdown" / note_relative
    if not human.is_file() or not markdown.is_file() or human.read_bytes() != markdown.read_bytes():
        raise CkbError("applied record must have byte-identical human and markdown note mirrors")
    title = _title_of(human)
    metadata = output / "workspace-meta/notes" / f"{safe_title(title)}.json"
    if not metadata.is_file():
        raise CkbError("applied record metadata is missing; create the note through record")
    value = json_load(metadata)
    if value.get("status") != "agent-reviewed" or value.get("title") != title:
        raise CkbError("applied record must have agent-reviewed metadata")
    return relative.as_posix()


def resolve_feedback(
    output: Path,
    feedback_id: str,
    decision: str,
    resolution_path: Path,
    applied_record: Path | None = None,
) -> dict[str, Any]:
    output = output.resolve()
    if decision not in DECISIONS:
        raise CkbError(f"feedback decision must be one of: {list(DECISIONS)}")
    resolution = _read_chinese_body(resolution_path.resolve(), "feedback resolution")
    record, source_path = _load_feedback(output, feedback_id)
    if record.get("status") != "open":
        raise CkbError("only open feedback can receive a new decision")
    applied = _canonical_applied_record(output, applied_record)
    if decision in {"accepted", "partial"} and not applied:
        raise CkbError("accepted or partial feedback requires --applied-record with verified implementation evidence")
    anchor = locate_feedback(output, feedback_id)["anchor"]
    record["decision"] = decision
    record["resolution"] = resolution
    record["applied_record"] = applied
    record["resolution_anchor"] = anchor
    record["resolved_at_utc"] = utc_now() if decision != "deferred" else None
    if decision == "deferred":
        json_write(source_path, record)
        record["visible_files"] = _write_visible_mirrors(output, record)
        audit = audit_feedback(output)
        if audit["status"] != "passed":
            raise CkbError(f"feedback audit failed after defer: {audit['errors'][:10]}")
        return {**record, "anchor": anchor}
    record["status"] = "resolved"
    destination = _record_path(output, "resolved", feedback_id)
    json_write(destination, record)
    source_path.unlink()
    old_relative = _visible_relative("open", feedback_id)
    for root_name in ("markdown", "human"):
        (output / root_name / old_relative).unlink(missing_ok=True)
    record["visible_files"] = _write_visible_mirrors(output, record)
    audit = audit_feedback(output)
    if audit["status"] != "passed":
        raise CkbError(f"feedback audit failed after resolve: {audit['errors'][:10]}")
    return {**record, "anchor": anchor, "record": str(destination.resolve())}


def list_feedback(output: Path, status: str = "open") -> dict[str, Any]:
    output = output.resolve()
    if status not in {"open", "resolved", "all"}:
        raise CkbError("feedback list status must be open, resolved, or all")
    prepare_feedback_store(output)
    statuses = ("open", "resolved") if status == "all" else (status,)
    rows = []
    for value in statuses:
        for path in sorted((output / "workspace-meta/feedback" / value).glob("*.json")):
            record = json_load(path)
            anchor = locate_feedback(output, str(record["id"]))["anchor"]
            rows.append(
                {
                    "id": record["id"],
                    "status": record["status"],
                    "severity": record["severity"],
                    "target": record["target"],
                    "target_title": record["target_title"],
                    "target_lines": record["target_lines"],
                    "comment": record["comment"],
                    "decision": record.get("decision"),
                    "anchor": anchor,
                    "record": str(path.resolve()),
                }
            )
    rows.sort(key=lambda item: (SEVERITY_ORDER.get(item["severity"], 99), item["target"], item["id"]))
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[row["target"]].append(row["id"])
    return {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "ready",
        "selection": status,
        "count": len(rows),
        "grouped_by_target": [{"target": key, "feedback_ids": grouped[key]} for key in sorted(grouped)],
        "feedback": rows,
    }


def audit_feedback(output: Path) -> dict[str, Any]:
    output = output.resolve()
    prepare_feedback_store(output)
    errors: list[dict[str, Any]] = []
    records = []
    seen: set[str] = set()
    seen_titles: set[str] = set()
    for directory_status in ("open", "resolved"):
        root = output / "workspace-meta/feedback" / directory_status
        for path in sorted(root.glob("*.json")):
            try:
                record = json_load(path)
            except Exception as exc:
                errors.append({"reason": "feedback-record-invalid-json", "path": str(path), "detail": str(exc)})
                continue
            feedback_id = str(record.get("id", ""))
            if feedback_id in seen:
                errors.append({"reason": "feedback-id-duplicate", "feedback_id": feedback_id})
            seen.add(feedback_id)
            if path.stem != feedback_id or not re.fullmatch(r"feedback-\d{8}-\d{6}-\d{2,}", feedback_id):
                errors.append({"reason": "feedback-id-invalid", "path": str(path), "feedback_id": feedback_id})
            if record.get("schema_version") != FEEDBACK_SCHEMA_VERSION:
                errors.append({"reason": "feedback-schema-version", "feedback_id": feedback_id})
            required = {
                "id",
                "status",
                "target",
                "target_title",
                "title",
                "target_lines",
                "anchor_before",
                "anchor_text",
                "anchor_after",
                "severity",
                "author",
                "source",
                "created_at_utc",
                "comment",
            }
            missing = sorted(required - set(record))
            line_range = record.get("target_lines")
            if missing or not isinstance(line_range, list) or len(line_range) != 2 or not all(isinstance(value, int) for value in line_range):
                errors.append({"reason": "feedback-record-shape-invalid", "feedback_id": feedback_id, "missing": missing})
                continue
            title = str(record.get("title", ""))
            if title in seen_titles:
                errors.append({"reason": "feedback-visible-title-duplicate", "feedback_id": feedback_id, "title": title})
            seen_titles.add(title)
            if record.get("status") != directory_status:
                errors.append({"reason": "feedback-status-directory-mismatch", "feedback_id": feedback_id})
            if record.get("severity") not in SEVERITIES:
                errors.append({"reason": "feedback-severity-invalid", "feedback_id": feedback_id})
            if record.get("source") not in SOURCES:
                errors.append({"reason": "feedback-source-invalid", "feedback_id": feedback_id})
            if not _contains_chinese(record.get("comment")):
                errors.append({"reason": "feedback-comment-not-chinese", "feedback_id": feedback_id})
            target_valid = True
            try:
                _canonical_relative_target(output, Path(str(record.get("target", ""))))
                location = locate_feedback(output, feedback_id)["anchor"]
            except Exception as exc:
                errors.append({"reason": "feedback-target-invalid", "feedback_id": feedback_id, "detail": str(exc)})
                target_valid = False
                location = {"status": "unavailable"}
            if directory_status == "open" and target_valid and location.get("status") == "stale":
                errors.append({"reason": "feedback-anchor-stale", "feedback_id": feedback_id})
            decision = record.get("decision")
            if directory_status == "open" and decision not in {None, "deferred"}:
                errors.append({"reason": "feedback-open-decision-invalid", "feedback_id": feedback_id})
            if directory_status == "open" and decision == "deferred" and not _contains_chinese(record.get("resolution")):
                errors.append({"reason": "feedback-deferred-resolution-not-chinese", "feedback_id": feedback_id})
            if directory_status == "resolved":
                if decision not in {"accepted", "partial", "rejected"}:
                    errors.append({"reason": "feedback-resolved-decision-invalid", "feedback_id": feedback_id})
                if not _contains_chinese(record.get("resolution")):
                    errors.append({"reason": "feedback-resolution-not-chinese", "feedback_id": feedback_id})
                if decision in {"accepted", "partial"}:
                    applied_value = record.get("applied_record")
                    try:
                        _canonical_applied_record(output, output / str(applied_value)) if applied_value else None
                        applied_valid = bool(applied_value)
                    except CkbError:
                        applied_valid = False
                    if not applied_valid:
                        errors.append({"reason": "feedback-applied-record-missing", "feedback_id": feedback_id})
            relative = _visible_relative(directory_status, feedback_id)
            mirrors = [output / root / relative for root in ("markdown", "human")]
            if not all(path_value.is_file() for path_value in mirrors):
                errors.append({"reason": "feedback-visible-mirror-missing", "feedback_id": feedback_id})
            elif mirrors[0].read_bytes() != mirrors[1].read_bytes():
                errors.append({"reason": "feedback-visible-mirror-differs", "feedback_id": feedback_id})
            else:
                text = mirrors[0].read_text(encoding="utf-8-sig")
                if text.startswith("---\n") or text.count("#类型/反馈") != 1 or LONG_HEX.search(text):
                    errors.append({"reason": "feedback-visible-shape-invalid", "feedback_id": feedback_id})
            records.append({"feedback_id": feedback_id, "status": directory_status, "anchor_status": location.get("status")})
    result = {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "counts": {
            "open": sum(1 for item in records if item["status"] == "open"),
            "resolved": sum(1 for item in records if item["status"] == "resolved"),
            "stale_open": sum(1 for item in records if item["status"] == "open" and item["anchor_status"] == "stale"),
        },
        "records": records,
        "errors": errors,
    }
    json_write(output / "workspace-meta/feedback-audit.json", result)
    return result


def _query_terms(question: str) -> list[str]:
    terms = {value.casefold() for value in re.findall(r"[A-Za-z0-9_.:#/-]{2,}", question)}
    for run in re.findall(r"[\u3400-\u9fff]+", question):
        terms.add(run)
        terms.update(run[index : index + 2] for index in range(max(0, len(run) - 1)))
    return sorted(terms, key=lambda value: (-len(value), value))


def search_feedback(output: Path, question: str, limit: int = 8) -> list[dict[str, Any]]:
    """Return deterministic feedback matches without mutating the knowledge base."""
    output = output.resolve()
    root = output / "workspace-meta/feedback"
    if not root.is_dir():
        return []
    terms = _query_terms(question)
    rows = []
    for status in ("open", "resolved"):
        for path in sorted((root / status).glob("*.json")):
            record = json_load(path)
            haystack = "\n".join(
                str(record.get(field) or "")
                for field in ("target", "target_title", "comment", "resolution", "severity", "decision", "status")
            ).casefold()
            matches = [term for term in terms if term in haystack]
            score = sum(8 + min(len(term), 12) for term in matches)
            if status == "open":
                score += 25
            score += max(0, 8 - 2 * SEVERITY_ORDER.get(str(record.get("severity")), 4))
            if terms and not matches and not re.search(r"反馈|纠错|audit|feedback", question, re.IGNORECASE):
                continue
            rows.append(
                {
                    "feedback_id": record["id"],
                    "title": record["title"],
                    "status": record["status"],
                    "severity": record["severity"],
                    "target": record["target"],
                    "target_title": record["target_title"],
                    "comment": record["comment"],
                    "decision": record.get("decision"),
                    "resolution": record.get("resolution"),
                    "human_file": _visible_relative(status, record["id"]).as_posix(),
                    "score": score,
                }
            )
    rows.sort(key=lambda item: (-item["score"], SEVERITY_ORDER.get(item["severity"], 99), item["target"], item["feedback_id"]))
    return rows[: max(0, limit)]
