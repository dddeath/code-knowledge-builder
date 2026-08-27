"""Deterministic Agent task sessions layered over a fixed baseline knowledge build."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import CkbError, json_load, json_write, safe_title, utc_now
from .machine_knowledge import (
    contains_chinese_narrative,
    retrieve_machine,
    sync_workspace_changes,
)
from .workspace_notes import queue_pending_note, record_note, selectors_for_changed_paths, sync_workspace


SESSION_SCHEMA_VERSION = 1
_REQUIRED_CHANGE_HEADINGS = ("修改内容", "修改原因", "验证结果")


def _session_directory(output: Path) -> Path:
    directory = output / "workspace-meta/sessions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _new_session_id(output: Path) -> str:
    stamp = utc_now().replace("-", "").replace(":", "").replace("T", "-").removesuffix("Z")
    directory = _session_directory(output)
    counter = 1
    while (directory / f"session-{stamp}-{counter:02d}.json").exists():
        counter += 1
    return f"session-{stamp}-{counter:02d}"


def _record_or_queue(
    output: Path,
    kind: str,
    title: str,
    body_path: Path,
    *,
    query_record: Path | None = None,
    changed_paths: list[str] | None = None,
) -> dict[str, Any]:
    if (output / "markdown/projection.json").is_file():
        selectors = selectors_for_changed_paths(output, changed_paths or [])
        return {
            "mode": "materialized",
            **record_note(
                output,
                kind,
                title,
                body_path,
                selectors=selectors,
                query_record=query_record,
            ),
        }
    pending = queue_pending_note(
        output,
        kind,
        title,
        body_path.read_text(encoding="utf-8-sig"),
        query_record=query_record,
        changed_paths=changed_paths or [],
    )
    return {"mode": "queued-until-human-projection", **pending}


def start_session(
    output: Path,
    repo: Path,
    question: str,
    budget: int = 1800,
    profile: str = "fast",
) -> dict[str, Any]:
    """Start one task session and retrieve a bounded source-grounded reading pack.

    A session may start immediately after ``init``.  If projections are not yet
    available, its Chinese narrative is queued and materialized by ``finalize``.
    """
    output = output.resolve()
    repo = repo.resolve()
    if not question.strip():
        raise CkbError("Agent session question must not be empty")
    if profile not in {"fast", "precise"}:
        raise CkbError("Agent session retrieval profile must be fast or precise")
    if not (output / "state.json").is_file():
        raise CkbError(f"knowledge build state is missing: {output / 'state.json'}")

    overlay = sync_workspace(output, repo)
    machine_sync = sync_workspace_changes(output) if (output / "machine/knowledge.sqlite").is_file() else {"status": "waiting-for-machine-layer"}
    retrieval: dict[str, Any]
    query_record: Path | None = None
    if (output / "machine/knowledge.sqlite").is_file():
        retrieval = retrieve_machine(output, question, budget, 8, profile)
        if retrieval.get("record"):
            query_record = Path(str(retrieval["record"]))
    else:
        retrieval = {
            "status": "waiting-for-machine-layer",
            "reason": "固定快照知识库仍在分段构建；会话记录先进入待投影队列，完成后再执行确定性检索。",
        }

    session_id = _new_session_id(output)
    directory = _session_directory(output)
    body_path = directory / f"{session_id}-start.md"
    body_lines = [
        "## 本次任务",
        "",
        question.strip(),
        "",
        "## 工作方式",
        "",
        "Agent 以固定源码快照为知识基线，同时把当前工作树修改保存在独立覆盖层；分析结论、修改原因、踩坑与实验都将回链到人类知识页。",
        "",
        "## 初始工作树",
        "",
        f"当前状态为“{overlay['status']}”，已记录 {len(overlay.get('changed_paths', []))} 个已跟踪修改和 {len(overlay.get('untracked_paths', []))} 个未跟踪路径。",
    ]
    body_path.write_text("\n".join(body_lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    title = f"Agent 会话 {session_id.removeprefix('session-')}"
    note = _record_or_queue(output, "session", title, body_path, query_record=query_record)
    record = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "session_id": session_id,
        "status": "active",
        "question": question.strip(),
        "profile": profile,
        "budget": budget,
        "repository": str(repo),
        "knowledge_output": str(output),
        "started_at_utc": utc_now(),
        "initial_overlay": overlay,
        "machine_overlay": machine_sync,
        "retrieval": retrieval,
        "session_note": note,
        "finish_note": None,
    }
    record_path = directory / f"{session_id}.json"
    json_write(record_path, record)
    return {**record, "record": str(record_path.resolve())}


def _summary_heading_errors(text: str, changed: bool) -> list[str]:
    if not changed:
        return []
    headings = {
        re.sub(r"\s+", "", line.lstrip().lstrip("#").strip())
        for line in text.splitlines()
        if line.lstrip().startswith("#")
    }
    return [heading for heading in _REQUIRED_CHANGE_HEADINGS if heading not in headings]


def finish_session(
    output: Path,
    repo: Path,
    session_id: str,
    summary_path: Path,
    title: str | None = None,
) -> dict[str, Any]:
    """Finish an Agent task and persist a Chinese, source-linked change record."""
    output = output.resolve()
    repo = repo.resolve()
    record_path = _session_directory(output) / f"{safe_title(session_id)}.json"
    if not record_path.is_file():
        raise CkbError(f"Agent session does not exist: {session_id}")
    record = json_load(record_path)
    if record.get("status") != "active":
        raise CkbError(f"Agent session is not active: {session_id}; status={record.get('status')}")
    if not summary_path.is_file():
        raise CkbError(f"Agent session summary does not exist: {summary_path}")
    summary = summary_path.read_text(encoding="utf-8-sig").strip()
    if not contains_chinese_narrative(summary):
        raise CkbError("Agent session summary must use Simplified Chinese; English proper nouns and code identifiers are allowed")

    overlay = sync_workspace(output, repo)
    changed_paths = sorted(set(overlay.get("changed_paths", [])) | set(overlay.get("untracked_paths", [])))
    missing_headings = _summary_heading_errors(summary, bool(changed_paths))
    if missing_headings:
        raise CkbError(f"a changed Agent session summary requires headings: {missing_headings}")
    machine_sync = sync_workspace_changes(output) if (output / "machine/knowledge.sqlite").is_file() else {"status": "waiting-for-machine-layer"}

    kind = "change" if changed_paths else "session"
    finish_title = title.strip() if title and title.strip() else (
        f"{session_id} 修改记录" if changed_paths else f"{session_id} 分析总结"
    )
    body_path = _session_directory(output) / f"{session_id}-finish.md"
    scope_lines = [f"- `{path}`" for path in changed_paths] or ["- 本次会话没有工作树文件变化。"]
    body = "\n".join(
        [
            summary,
            "",
            "## 工作树范围",
            "",
            *scope_lines,
            "",
            "## 记录边界",
            "",
            "本页只叙述本次任务的结论与修改依据；固定快照事实、当前工作树差异和机器索引继续分层保存。",
        ]
    ).rstrip() + "\n"
    body_path.write_text(body, encoding="utf-8", newline="\n")
    query_record = None
    retrieval = record.get("retrieval") or {}
    if retrieval.get("record") and Path(str(retrieval["record"])).is_file():
        query_record = Path(str(retrieval["record"]))
    note = _record_or_queue(
        output,
        kind,
        finish_title,
        body_path,
        query_record=query_record,
        changed_paths=changed_paths,
    )
    record.update(
        {
            "status": "complete",
            "completed_at_utc": utc_now(),
            "final_overlay": overlay,
            "machine_overlay": machine_sync,
            "changed_paths": changed_paths,
            "finish_note": note,
        }
    )
    json_write(record_path, record)
    return {**record, "record": str(record_path.resolve())}


def sessions_status(output: Path) -> dict[str, Any]:
    directory = output.resolve() / "workspace-meta/sessions"
    sessions = []
    if directory.is_dir():
        for path in sorted(directory.glob("session-*.json")):
            value = json_load(path)
            if value.get("session_id"):
                sessions.append(
                    {
                        "session_id": value["session_id"],
                        "status": value.get("status"),
                        "question": value.get("question"),
                        "started_at_utc": value.get("started_at_utc"),
                        "completed_at_utc": value.get("completed_at_utc"),
                        "record": str(path.resolve()),
                    }
                )
    return {
        "schema_version": SESSION_SCHEMA_VERSION,
        "status": "ready",
        "active": sum(item["status"] == "active" for item in sessions),
        "complete": sum(item["status"] == "complete" for item in sessions),
        "sessions": sessions,
    }
