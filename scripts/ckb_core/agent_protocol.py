"""Persistent cross-Harness instructions and deterministic maintenance checks."""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .common import AuditError, CkbError, json_load, json_write, path_inside, safe_title
from .feedback import audit_feedback, prepare_feedback_store
from .obsidian import NOTE_DIRECTORIES
from .workspace_notes import DIRECTORY_BY_KIND, audit_notes
from .work_record_index import audit_work_record_index


AGENT_PROTOCOL_SCHEMA_VERSION = 1
AGENT_PROTOCOL_VERSION = "1.3.0"
POLICY_BEGIN = "<!-- CKB-AGENT-PROTOCOL:BEGIN -->"
POLICY_END = "<!-- CKB-AGENT-PROTOCOL:END -->"
INTERNAL_ROOT_NAMES = ("output", "markdown", "human")
ADAPTER_PATHS = {
    "agents": Path("AGENTS.md"),
    "claude": Path("CLAUDE.md"),
    "gemini": Path("GEMINI.md"),
    "copilot": Path(".github/copilot-instructions.md"),
    "cursor": Path(".cursor/rules/code-knowledge-builder.mdc"),
}
OBSIDIAN_IGNORES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/", ".cursor/")
OBSIDIAN_HIDE_CSS = """.nav-file-title[data-path=\"AGENTS.md\"],
.nav-file-title[data-path=\"CLAUDE.md\"],
.nav-file-title[data-path=\"GEMINI.md\"] { display: none; }"""


def _default_python() -> Path:
    return Path(sys.executable).resolve()


def _default_ckb() -> Path:
    return (Path(__file__).resolve().parents[1] / "ckb.py").resolve()


def _single_quote(value: str) -> str:
    return value.replace("'", "''")


def _command_examples(output: Path, python: Path, ckb: Path) -> dict[str, str]:
    py = _single_quote(str(python))
    cli = _single_quote(str(ckb))
    out = _single_quote(str(output.resolve()))
    prefix = f"& '{py}' '{cli}'"
    return {
        "brief": f'{prefix} brief --out \'{out}\' "QUESTION" --budget 1800 --max-pages 8 --profile fast',
        "retrieve": f'{prefix} retrieve --out \'{out}\' "QUESTION" --budget 1800 --max-pages 8 --profile fast',
        "precise": f'{prefix} retrieve --out \'{out}\' "QUESTION" --budget 3000 --max-pages 12 --profile precise',
        "entity": f'{prefix} entity --out \'{out}\' "SYMBOL"',
        "neighbors": f'{prefix} neighbors --out \'{out}\' "SYMBOL" --depth 2',
        "source": f'{prefix} source --out \'{out}\' "SYMBOL" --context-lines 3',
        "record": f"{prefix} record --out '{out}' --kind analysis --title 'TITLE' --body 'BODY.md' --from-pack 'PACK.json'",
        "append": f"{prefix} record --out '{out}' --kind analysis --title 'EXISTING_TITLE' --body 'BODY.md' --from-pack 'PACK.json' --append",
        "feedback_list": f"{prefix} feedback list --out '{out}' --status open",
        "feedback_locate": f"{prefix} feedback locate --out '{out}' --feedback 'FEEDBACK_ID'",
        "feedback_audit": f"{prefix} feedback audit --out '{out}'",
        "check": f"{prefix} agent-policy check --out '{out}'",
        "maintain": f"{prefix} maintain --out '{out}'",
        "capabilities": f"{prefix} capabilities --format json",
        "reference_list": f"{prefix} reference list --out '{out}' --status all",
        "reference_audit": f"{prefix} reference audit --out '{out}'",
    }


def _protocol_text(output: Path, repository: str, python: Path, ckb: Path) -> str:
    commands = _command_examples(output, python, ckb)
    return f"""# Code Knowledge Builder Agent 工作协议

本文件是自动加载的项目级工作指令，不是知识页面。凡是读取、解释或修改本知识库及其对应源码的智能体，都必须遵循以下流程；无需用户再次点名 Skill。

## 绑定范围

- 知识库：`{output.resolve()}`
- 源码仓库：`{repository}`
- 命令入口：`{ckb}`

## 先检索，后读源码

1. 回答架构、实现、定位或修改问题前，先执行紧凑阅读入口。它在一个小 JSON 中返回开放反馈数、Agent pack、完整检索 record 和固定阅读入口，不把候选实体、词项和得分展开到首轮上下文：

```powershell
{commands['brief']}
```

2. 若 `open_feedback` 大于零，再列出开放反馈；任务涉及其目标页时按 `error`、`warn`、`suggest`、`info` 的固定优先级处理：

```powershell
{commands['feedback_list']}
```

3. 先阅读 `brief` 返回的预算化 Agent pack；完整候选与得分仍保存在 `record`。再按 pack 使用 `entity`、`neighbors`、`source` 或 `changes`；复杂跨模块问题才切换 `precise`。
4. 只有检索明确返回 `needs-source-read`，或返回了需要核实的精确路径和范围时，才使用窄范围源码读取。`grep`、全仓文件遍历和整库页面加载只作为这一分支的补充手段，不得替代首轮 SQLite 检索。
5. 人类需要查找已有分析、变更或实验时，从 `RECORDS.md` 按任务目的浏览；查找已审阅外部资料时从 `REFERENCES.md` 浏览。两个导览都由完整集合生成，不允许为单个查询手工挑选页面。

## 受控维护

1. `human/pages`、`markdown/pages`、`human/references`、`markdown/references`、`INDEX.md`、`WIKI.md`、`REFERENCES.md`、投影清单和 SQLite 文件属于生成器管理内容，不直接编辑。
2. 可复用分析、修改原因、踩坑和实验只通过 `record` 写入；正文使用简体中文，并通过 `--from-pack`、`--from-query` 或唯一 `--link` 回链至少一个知识页。
3. 创建分析页的标准命令：

```powershell
{commands['record']}
```

4. 更新已有人工笔记时使用同标题和 `--append`。Hook 仅采集会话与修改事件，并在 Agent 审核后新建会话页或修改页；其他已有页面只在任务明确要求时执行显式追加，不随每轮对话扩散更新。
5. 外部文本资料只通过 `reference ingest/review/audit/rollback` 进入独立参考层。Agent 必须重新打开归档原文，逐项提交精确行范围、原文文本、中文主张和中文来源核对；参考资料不成为代码实体。
6. 人工反馈通过 `feedback create` 进入带行范围和文本窗口的收件箱。处理前先执行：

```powershell
{commands['feedback_locate']}
```

生成器管理页面仍不直接编辑；采纳或部分采纳时先修改来源、生成规则或通过 `record` 写入落实记录，再用 `feedback resolve` 归档。拒绝必须写明中文理由；暂缓记录继续留在开放列表。反馈记录不删除。
7. 结束实质任务前执行聚合维护门；它统一检查反馈、Agent Policy、工作记录、参考资料、人类可读性、机器知识库和兼容索引，并且不创建知识页面：

```powershell
{commands['maintain']}
```

只有协议文件、中文与链接规则、human/markdown 镜像、笔记元数据以及两个 SQLite 索引全部一致时，才报告知识库维护完成。失败时根据 `failed_checks` 运行窄范围审计，修复对应笔记或重新执行 `record`/`reindex`，再复查。

## 最小上下文原则

- 优先顺序固定为：`brief fast` → Agent pack → `entity/neighbors/source/changes` → 返回路径的窄范围读取。
- 不预先加载整个模块、整个 vault 或完整关系图。
- 页面正文保持面向人类的简体中文叙述；英文仅保留专有名词、API、类型、函数、变量、命令和路径。
"""


def _adapter_texts(protocol: str) -> dict[str, str]:
    return {
        "agents": protocol,
        "claude": "# Claude Code 项目指令\n\n@./AGENTS.md\n",
        "gemini": "# Gemini CLI 项目指令\n\n@./AGENTS.md\n",
        "copilot": protocol,
        "cursor": (
            "---\n"
            "description: Code Knowledge Builder 检索与维护协议\n"
            "globs:\n"
            "alwaysApply: true\n"
            "---\n\n"
            + protocol
        ),
    }


def _managed_block(text: str) -> str:
    return f"{POLICY_BEGIN}\n{text.rstrip()}\n{POLICY_END}\n"


def _replace_managed_block(existing: str, block: str) -> str:
    pattern = re.compile(re.escape(POLICY_BEGIN) + r".*?" + re.escape(POLICY_END) + r"\n?", re.DOTALL)
    matches = pattern.findall(existing)
    if len(matches) > 1:
        raise CkbError("workspace instruction file contains duplicate CKB Agent protocol blocks")
    if matches:
        return pattern.sub(lambda _match: block, existing, count=1)
    if not existing.strip():
        return block
    return existing.rstrip() + "\n\n" + block


def _instruction_roots(output: Path) -> dict[str, Path]:
    roots = {"output": output.resolve()}
    for name in ("markdown", "human"):
        path = (output / name).resolve()
        if path.is_dir():
            roots[name] = path
    return roots


def _write_exact_root(root: Path, texts: dict[str, str]) -> list[str]:
    written: list[str] = []
    for key, relative in ADAPTER_PATHS.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(texts[key], encoding="utf-8", newline="\n")
        written.append(relative.as_posix())
    return written


def _update_markdown_ownership(output: Path) -> None:
    ownership_path = output / "markdown/.ckb-generated-files.json"
    if not ownership_path.is_file():
        return
    ownership = json_load(ownership_path)
    ownership["files"] = sorted(set(ownership.get("files", [])) | {path.as_posix() for path in ADAPTER_PATHS.values()})
    json_write(ownership_path, ownership)


def _hide_protocol_files(output: Path) -> None:
    """Keep Harness adapters out of the human Obsidian navigation surface."""
    for name in ("markdown", "human"):
        root = output / name
        app_path = root / ".obsidian/app.json"
        if app_path.is_file():
            app = json_load(app_path)
            app["userIgnoreFilters"] = list(dict.fromkeys([*app.get("userIgnoreFilters", []), *OBSIDIAN_IGNORES]))
            json_write(app_path, app)
        css_path = root / ".obsidian/snippets/ckb.css"
        if css_path.is_file():
            css = css_path.read_text(encoding="utf-8")
            if OBSIDIAN_HIDE_CSS not in css:
                css_path.write_text(css.rstrip() + "\n" + OBSIDIAN_HIDE_CSS + "\n", encoding="utf-8", newline="\n")


def _load_record(output: Path) -> dict[str, Any] | None:
    path = output / "workspace-meta/agent-protocol.json"
    return json_load(path) if path.is_file() else None


def _resolve_runtime(record: dict[str, Any] | None, python: Path | None, ckb: Path | None) -> tuple[Path, Path]:
    python_path = python or (Path(str(record["python"])) if record and record.get("python") else _default_python())
    ckb_path = ckb or (Path(str(record["ckb"])) if record and record.get("ckb") else _default_ckb())
    if not python_path.is_file():
        raise CkbError(f"Agent protocol Python executable is missing: {python_path}")
    if not ckb_path.is_file():
        raise CkbError(f"Agent protocol CKB entrypoint is missing: {ckb_path}")
    return python_path.resolve(), ckb_path.resolve()


def _workspace_root_allowed(root: Path, output: Path, repository: str) -> bool:
    if path_inside(output.resolve(), root.resolve()):
        return True
    repo = Path(repository)
    return repo.is_absolute() and path_inside(repo.resolve(), root.resolve())


def _write_workspace_root(root: Path, texts: dict[str, str]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for key, relative in ADAPTER_PATHS.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_text(encoding="utf-8-sig") if target.is_file() else ""
        block = _managed_block(texts[key])
        updated = _replace_managed_block(existing, block)
        target.write_text(updated, encoding="utf-8", newline="\n")
        files.append({"path": str(target.resolve()), "relative_path": relative.as_posix(), "created": not bool(existing)})
    return {"root": str(root.resolve()), "files": files}


def project_agent_protocol(
    output: Path,
    *,
    python: Path | None = None,
    ckb: Path | None = None,
) -> dict[str, Any]:
    """Project exact protocol adapters into the knowledge output roots."""
    output = output.resolve()
    state_path = output / "state.json"
    if not state_path.is_file():
        raise CkbError(f"knowledge build state is missing: {state_path}")
    state = json_load(state_path)
    repository = str(state["repository"]["root"])
    prepare_feedback_store(output)
    previous = _load_record(output)
    python_path, ckb_path = _resolve_runtime(previous, python, ckb)
    protocol = _protocol_text(output, repository, python_path, ckb_path)
    texts = _adapter_texts(protocol)
    roots = _instruction_roots(output)
    internal: dict[str, Any] = {}
    for name, root in roots.items():
        internal[name] = {"root": str(root), "files": _write_exact_root(root, texts)}
    _update_markdown_ownership(output)
    _hide_protocol_files(output)
    workspace_roots = list(previous.get("workspace_roots", [])) if previous else []
    record = {
        "schema_version": AGENT_PROTOCOL_SCHEMA_VERSION,
        "protocol_version": AGENT_PROTOCOL_VERSION,
        "status": "installed",
        "output": str(output),
        "repository": repository,
        "python": str(python_path),
        "ckb": str(ckb_path),
        "internal_roots": internal,
        "workspace_roots": workspace_roots,
        "commands": _command_examples(output, python_path, ckb_path),
        "harness_contract": {
            "codex": "AGENTS.md",
            "opencode": "AGENTS.md",
            "claude-code": "CLAUDE.md imports AGENTS.md",
            "gemini-cli": "GEMINI.md imports AGENTS.md",
            "github-copilot": ".github/copilot-instructions.md",
            "cursor": ".cursor/rules/code-knowledge-builder.mdc",
            "generic": "read AGENTS.md before knowledge-base access",
        },
    }
    json_write(output / "workspace-meta/agent-protocol.json", record)
    return record


def install_agent_protocol(
    output: Path,
    workspace_roots: list[Path],
    *,
    python: Path | None = None,
    ckb: Path | None = None,
) -> dict[str, Any]:
    """Install internal adapters and managed blocks at Harness task roots."""
    output = output.resolve()
    record = project_agent_protocol(output, python=python, ckb=ckb)
    protocol = _protocol_text(output, record["repository"], Path(record["python"]), Path(record["ckb"]))
    texts = _adapter_texts(protocol)
    requested = {Path(str(value["root"])).resolve() for value in record.get("workspace_roots", [])}
    requested.update(root.resolve() for root in workspace_roots)
    merged: dict[str, dict[str, Any]] = {}
    for root in sorted(requested, key=str):
        if not root.is_dir():
            raise CkbError(f"Agent protocol workspace root is missing: {root}")
        if not _workspace_root_allowed(root, output, record["repository"]):
            raise CkbError(f"Agent protocol workspace root must contain the repository or knowledge output: {root}")
        merged[str(root)] = _write_workspace_root(root, texts)
    record["workspace_roots"] = [merged[key] for key in sorted(merged)]
    json_write(output / "workspace-meta/agent-protocol.json", record)
    audit = audit_agent_protocol(output)
    if audit["status"] != "passed":
        raise AuditError(f"Agent protocol audit failed: {output / 'workspace-meta/agent-protocol-audit.json'}")
    return {**record, "audit": audit}


def _expected_internal(output: Path, record: dict[str, Any]) -> tuple[dict[str, str], dict[str, Path]]:
    protocol = _protocol_text(output, str(record["repository"]), Path(record["python"]), Path(record["ckb"]))
    return _adapter_texts(protocol), _instruction_roots(output)


def _audit_note_storage(output: Path) -> list[dict[str, Any]]:
    errors = list(audit_notes(output))
    human = output / "human"
    markdown = output / "markdown"
    meta_root = output / "workspace-meta/notes"
    notes: dict[str, dict[str, Any]] = {}
    for directory in NOTE_DIRECTORIES:
        left = {path.name: path for path in (human / directory).glob("*.md")}
        right = {path.name: path for path in (markdown / directory).glob("*.md")}
        if set(left) != set(right):
            errors.append({"reason": "agent-note-mirror-set-mismatch", "directory": directory, "human_only": sorted(set(left) - set(right)), "markdown_only": sorted(set(right) - set(left))})
        for name in sorted(set(left) & set(right)):
            if left[name].read_bytes() != right[name].read_bytes():
                errors.append({"reason": "agent-note-mirror-byte-mismatch", "path": f"{directory}/{name}"})
                continue
            text = right[name].read_text(encoding="utf-8")
            title = text.splitlines()[0].removeprefix("# ").strip() if text else ""
            relative = f"{directory}/{name}"
            notes[title] = {"relative": relative, "content": text, "kind": next((kind for kind, value in DIRECTORY_BY_KIND.items() if value == directory), "")}
            meta = meta_root / f"{safe_title(title)}.json"
            if not meta.is_file():
                errors.append({"reason": "agent-note-metadata-missing", "path": relative, "title": title})
                continue
            value = json_load(meta)
            if value.get("status") != "agent-reviewed" or value.get("title") != title or value.get("kind") != notes[title]["kind"]:
                errors.append({"reason": "agent-note-metadata-invalid", "path": relative, "metadata": str(meta)})

    index = output / "agent-index.sqlite"
    if index.is_file():
        connection = sqlite3.connect(f"file:{index.as_posix()}?mode=ro", uri=True)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            indexed = {row[0]: {"file": row[1], "content": row[2]} for row in connection.execute("SELECT note_title,note_file,content FROM notes")}
        except sqlite3.DatabaseError as exc:
            errors.append({"reason": "agent-index-read-failed", "detail": str(exc)})
            indexed = {}
            integrity = "error"
        finally:
            connection.close()
        if integrity != "ok":
            errors.append({"reason": "agent-index-integrity", "detail": integrity})
        for title, note in notes.items():
            row = indexed.get(title)
            if row != {"file": note["relative"], "content": note["content"]}:
                errors.append({"reason": "agent-index-note-stale", "title": title, "path": note["relative"]})
        if set(indexed) != set(notes):
            errors.append({"reason": "agent-index-note-set-mismatch", "index_only": sorted(set(indexed) - set(notes)), "file_only": sorted(set(notes) - set(indexed))})
    else:
        errors.append({"reason": "agent-index-missing"})

    machine = output / "machine/knowledge.sqlite"
    if machine.is_file():
        connection = sqlite3.connect(f"file:{machine.as_posix()}?mode=ro", uri=True)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            indexed = {
                row[0]: {"file": row[1], "content": row[2], "kind": row[3]}
                for row in connection.execute("SELECT title,human_file,content,kind FROM documents WHERE kind NOT IN ('entity','reference')")
            }
        except sqlite3.DatabaseError as exc:
            errors.append({"reason": "machine-index-read-failed", "detail": str(exc)})
            indexed = {}
            integrity = "error"
        finally:
            connection.close()
        if integrity != "ok":
            errors.append({"reason": "machine-index-integrity", "detail": integrity})
        for title, note in notes.items():
            row = indexed.get(title)
            if row != {"file": note["relative"], "content": note["content"], "kind": note["kind"]}:
                errors.append({"reason": "machine-index-note-stale", "title": title, "path": note["relative"]})
        if set(indexed) != set(notes):
            errors.append({"reason": "machine-index-note-set-mismatch", "index_only": sorted(set(indexed) - set(notes)), "file_only": sorted(set(notes) - set(indexed))})
    else:
        errors.append({"reason": "machine-index-missing"})
    return errors


def audit_agent_protocol(output: Path) -> dict[str, Any]:
    """Verify discovery adapters and every durable Agent-note representation."""
    output = output.resolve()
    record = _load_record(output)
    errors: list[dict[str, Any]] = []
    if not record:
        errors.append({"reason": "agent-protocol-record-missing"})
    elif record.get("protocol_version") != AGENT_PROTOCOL_VERSION:
        errors.append({"reason": "agent-protocol-version-mismatch", "actual": record.get("protocol_version"), "expected": AGENT_PROTOCOL_VERSION})
    if record:
        python = Path(str(record.get("python", "")))
        ckb = Path(str(record.get("ckb", "")))
        if not python.is_file():
            errors.append({"reason": "agent-protocol-python-missing", "path": str(python)})
        if not ckb.is_file():
            errors.append({"reason": "agent-protocol-ckb-missing", "path": str(ckb)})
        texts, roots = _expected_internal(output, record)
        for root_name in INTERNAL_ROOT_NAMES:
            root = roots.get(root_name)
            if root is None:
                errors.append({"reason": "agent-protocol-internal-root-missing", "root": root_name})
                continue
            for key, relative in ADAPTER_PATHS.items():
                path = root / relative
                if not path.is_file():
                    errors.append({"reason": "agent-protocol-adapter-missing", "root": root_name, "path": relative.as_posix()})
                elif path.read_text(encoding="utf-8-sig") != texts[key]:
                    errors.append({"reason": "agent-protocol-adapter-drift", "root": root_name, "path": relative.as_posix()})
        for workspace in record.get("workspace_roots", []):
            root = Path(str(workspace["root"]))
            for key, relative in ADAPTER_PATHS.items():
                path = root / relative
                if not path.is_file():
                    errors.append({"reason": "agent-protocol-workspace-adapter-missing", "root": str(root), "path": relative.as_posix()})
                    continue
                text = path.read_text(encoding="utf-8-sig")
                expected = _managed_block(texts[key])
                if text.count(POLICY_BEGIN) != 1 or text.count(POLICY_END) != 1 or expected not in text:
                    errors.append({"reason": "agent-protocol-workspace-adapter-drift", "root": str(root), "path": relative.as_posix()})
        for root_name in ("markdown", "human"):
            root = roots.get(root_name)
            if root is None:
                continue
            app_path = root / ".obsidian/app.json"
            app = json_load(app_path) if app_path.is_file() else {}
            if any(value not in app.get("userIgnoreFilters", []) for value in OBSIDIAN_IGNORES):
                errors.append({"reason": "agent-protocol-obsidian-ignore-missing", "root": root_name})
            css_path = root / ".obsidian/snippets/ckb.css"
            if not css_path.is_file() or OBSIDIAN_HIDE_CSS not in css_path.read_text(encoding="utf-8"):
                errors.append({"reason": "agent-protocol-obsidian-hide-rule-missing", "root": root_name})
    errors.extend(_audit_note_storage(output))
    work_record_audit = audit_work_record_index(output)
    errors.extend(work_record_audit["errors"])
    feedback_audit = audit_feedback(output)
    errors.extend(feedback_audit["errors"])
    from .output_contract import audit_output_contract

    output_contracts: dict[str, Any] = {}
    for name in ("markdown", "human"):
        vault = output / name
        if vault.is_dir():
            output_contracts[name] = audit_output_contract(output, vault)
            errors.extend(output_contracts[name]["errors"])
    result = {
        "schema_version": AGENT_PROTOCOL_SCHEMA_VERSION,
        "protocol_version": AGENT_PROTOCOL_VERSION,
        "status": "passed" if not errors else "failed",
        "output": str(output),
        "internal_roots": list(INTERNAL_ROOT_NAMES),
        "workspace_root_count": len(record.get("workspace_roots", [])) if record else 0,
        "feedback": feedback_audit,
        "output_contracts": output_contracts,
        "work_record_index": work_record_audit,
        "errors": errors,
    }
    json_write(output / "workspace-meta/agent-protocol-audit.json", result)
    return result


def agent_protocol_status(output: Path) -> dict[str, Any]:
    record = _load_record(output.resolve())
    return {
        "schema_version": AGENT_PROTOCOL_SCHEMA_VERSION,
        "status": "installed" if record else "missing",
        "record": record,
        "audit": audit_agent_protocol(output.resolve()) if record else None,
    }
