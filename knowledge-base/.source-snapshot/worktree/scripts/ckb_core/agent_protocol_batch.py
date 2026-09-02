"""Deterministic version matrix and batch upgrade contracts for Agent Protocol."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time
from typing import Any
import uuid

from .agent_protocol import (
    ADAPTER_PATHS,
    AGENT_PROTOCOL_VERSION,
    INTERNAL_ROOT_NAMES,
    OBSIDIAN_HIDE_CSS,
    OBSIDIAN_IGNORES,
    POLICY_BEGIN,
    POLICY_END,
    _adapter_texts,
    _protocol_text,
)
from .automation import SUPPORTED_HARNESSES as AUTOMATION_HARNESSES
from .common import CkbError, json_load, json_write, path_inside, stable_id, utc_now


BATCH_MANIFEST_SCHEMA_VERSION = 1
BATCH_PLAN_SCHEMA_VERSION = 1
BATCH_STATE_SCHEMA_VERSION = 1
BATCH_EVIDENCE_SCHEMA_VERSION = 1

MANIFEST_KEYS = frozenset({"schema_version", "allowed_roots", "projects"})
PROJECT_KEYS = frozenset(
    {
        "project_id",
        "output",
        "workspace_roots",
        "source_version",
        "target_version",
        "harnesses",
        "python",
        "ckb",
        "expected_digest",
    }
)

SUPPORTED_HARNESSES = frozenset(AUTOMATION_HARNESSES)
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_BATCH_PROJECTS = 128
MAX_WORKSPACE_ROOTS = 32
MAX_STATE_EVENTS = 256
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_STALE_SECONDS = 60.0
OUTPUT_LOCK_SCHEMA_VERSION = 1
OUTPUT_LOCK_FIELDS = frozenset(
    {"schema_version", "owner_pid", "owner_token", "owner_process_start", "owner_host", "created_at_utc"}
)
OWNER_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")


@dataclass(frozen=True)
class ProtocolRelease:
    version: str
    source_commit: str
    next_version: str | None
    capabilities: tuple[str, ...]
    output_contract: bool


PROTOCOL_RELEASES: dict[str, ProtocolRelease] = {
    "1.0.0": ProtocolRelease(
        version="1.0.0",
        source_commit="c0e6cb650d707512d0edbcc481db373359a8f46f",
        next_version="1.3.0",
        capabilities=("retrieve-fast", "record", "agent-policy-check"),
        output_contract=False,
    ),
    "1.3.0": ProtocolRelease(
        version="1.3.0",
        source_commit="3f117b8a3565b24633b88799a3ee180d6b3451ab",
        next_version="1.4.0",
        capabilities=("brief-fast", "feedback", "maintain", "output-contract"),
        output_contract=True,
    ),
    "1.4.0": ProtocolRelease(
        version="1.4.0",
        source_commit="02b3f9bae10663f8d8d41626bb52454a226d4228",
        next_version="1.5.0",
        capabilities=("brief-fast", "feedback", "references", "maintain", "output-contract"),
        output_contract=True,
    ),
    "1.5.0": ProtocolRelease(
        version="1.5.0",
        source_commit="2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
        next_version=None,
        capabilities=("brief-fast", "feedback", "references", "research-gaps", "operations", "maintain", "output-contract"),
        output_contract=True,
    ),
}


if AGENT_PROTOCOL_VERSION not in PROTOCOL_RELEASES:
    raise RuntimeError(f"current Agent Protocol is absent from the batch version matrix: {AGENT_PROTOCOL_VERSION}")


def supported_upgrade_path(source_version: str, target_version: str) -> list[str]:
    """Return the frozen inclusive path, rejecting unknown or backward/jump-only routes."""
    if source_version not in PROTOCOL_RELEASES:
        raise CkbError(f"unsupported Agent Protocol source version: {source_version}")
    if target_version not in PROTOCOL_RELEASES:
        raise CkbError(f"unsupported Agent Protocol target version: {target_version}")
    path = [source_version]
    while path[-1] != target_version:
        next_version = PROTOCOL_RELEASES[path[-1]].next_version
        if next_version is None:
            raise CkbError(f"no Agent Protocol upgrade path: {source_version} -> {target_version}")
        path.append(next_version)
        if len(path) > len(PROTOCOL_RELEASES):
            raise RuntimeError("Agent Protocol version matrix contains a cycle")
    return path


def version_matrix() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "current_version": AGENT_PROTOCOL_VERSION,
        "releases": [
            {
                "version": release.version,
                "source_commit": release.source_commit,
                "next_version": release.next_version,
                "capabilities": list(release.capabilities),
                "output_contract": release.output_contract,
            }
            for release in PROTOCOL_RELEASES.values()
        ],
    }


def reject_unknown_fields(value: dict[str, Any], allowed: frozenset[str], location: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CkbError(f"unknown batch manifest field at {location}: {', '.join(unknown)}")


def require_absolute_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CkbError(f"batch manifest {field} must be a non-empty absolute path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise CkbError(f"batch manifest {field} must be absolute: {value}")
    return path.resolve()


class BatchProjectError(CkbError):
    def __init__(self, category: str, detail: str):
        super().__init__(detail)
        self.category = category


def _canonical_bytes(value: Any, *, pretty: bool = False) -> bytes:
    if pretty:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _single_quote(value: str) -> str:
    return value.replace("'", "''")


def command_examples_for_version(version: str, output: Path, python: Path, ckb: Path) -> dict[str, str]:
    if version not in PROTOCOL_RELEASES:
        raise CkbError(f"unsupported Agent Protocol version: {version}")
    py = _single_quote(str(python))
    cli = _single_quote(str(ckb))
    out = _single_quote(str(output.resolve()))
    prefix = f"& '{py}' '{cli}'"
    commands: dict[str, str] = {}
    if version != "1.0.0":
        commands["brief"] = f'{prefix} brief --out \'{out}\' "QUESTION" --budget 1800 --max-pages 8 --profile fast'
    commands.update(
        {
            "retrieve": f'{prefix} retrieve --out \'{out}\' "QUESTION" --budget 1800 --max-pages 8 --profile fast',
            "precise": f'{prefix} retrieve --out \'{out}\' "QUESTION" --budget 3000 --max-pages 12 --profile precise',
            "entity": f'{prefix} entity --out \'{out}\' "SYMBOL"',
            "neighbors": f'{prefix} neighbors --out \'{out}\' "SYMBOL" --depth 2',
            "source": f'{prefix} source --out \'{out}\' "SYMBOL" --context-lines 3',
            "record": f"{prefix} record --out '{out}' --kind analysis --title 'TITLE' --body 'BODY.md' --from-pack 'PACK.json'",
            "append": f"{prefix} record --out '{out}' --kind analysis --title 'EXISTING_TITLE' --body 'BODY.md' --from-pack 'PACK.json' --append",
        }
    )
    if version != "1.0.0":
        commands.update(
            {
                "feedback_list": f"{prefix} feedback list --out '{out}' --status open",
                "feedback_locate": f"{prefix} feedback locate --out '{out}' --feedback 'FEEDBACK_ID'",
                "feedback_audit": f"{prefix} feedback audit --out '{out}'",
            }
        )
    commands["check"] = f"{prefix} agent-policy check --out '{out}'"
    if version != "1.0.0":
        commands["maintain"] = f"{prefix} maintain --out '{out}'"
        commands["capabilities"] = f"{prefix} capabilities --format json"
    if version in {"1.4.0", "1.5.0"}:
        commands["reference_list"] = f"{prefix} reference list --out '{out}' --status all"
        commands["reference_audit"] = f"{prefix} reference audit --out '{out}'"
    if version == "1.5.0":
        commands["gaps_list"] = f"{prefix} gaps list --out '{out}' --status open"
        commands["gaps_audit"] = f"{prefix} gaps audit --out '{out}'"
    return commands


def protocol_text_for_version(version: str, output: Path, repository: str, python: Path, ckb: Path) -> str:
    """Render the source-tagged historical protocol without reading an old executable."""
    commands = command_examples_for_version(version, output, python, ckb)
    if version == "1.0.0":
        return f"""# Code Knowledge Builder Agent 工作协议

本文件是自动加载的项目级工作指令，不是知识页面。凡是读取、解释或修改本知识库及其对应源码的智能体，都必须遵循以下流程；无需用户再次点名 Skill。

## 绑定范围

- 知识库：`{output.resolve()}`
- 源码仓库：`{repository}`
- 命令入口：`{ckb}`

## 先检索，后读源码

1. 回答架构、实现、定位或修改问题前，先执行确定性 SQLite 检索：

```powershell
{commands['retrieve']}
```

2. 先阅读返回的预算化 Agent pack，再按结果使用 `entity`、`neighbors`、`source` 或 `changes`；复杂跨模块问题才切换 `precise`。
3. 只有检索明确返回 `needs-source-read`，或返回了需要核实的精确路径和范围时，才使用窄范围源码读取。`grep`、全仓文件遍历和整库页面加载只作为这一分支的补充手段，不得替代首轮 SQLite 检索。

## 受控维护

1. `human/pages`、`markdown/pages`、`INDEX.md`、`WIKI.md`、投影清单和 SQLite 文件属于生成器管理内容，不直接编辑。
2. 可复用分析、修改原因、踩坑和实验只通过 `record` 写入；正文使用简体中文，并通过 `--from-pack`、`--from-query` 或唯一 `--link` 回链至少一个知识页。
3. 创建分析页的标准命令：

```powershell
{commands['record']}
```

4. 更新已有人工笔记时使用同标题和 `--append`。Hook 仅采集会话与修改事件，并在 Agent 审核后新建会话页或修改页；其他已有页面只在任务明确要求时执行显式追加，不随每轮对话扩散更新。
5. 结束实质任务前执行：

```powershell
{commands['check']}
```

只有协议文件、中文与链接规则、human/markdown 镜像、笔记元数据以及两个 SQLite 索引全部一致时，才报告知识库维护完成。失败时先修复对应笔记或重新执行 `record`/`reindex`，再复查。

## 最小上下文原则

- 优先顺序固定为：`retrieve fast` → Agent pack → `entity/neighbors/source/changes` → 返回路径的窄范围读取。
- 不预先加载整个模块、整个 vault 或完整关系图。
- 页面正文保持面向人类的简体中文叙述；英文仅保留专有名词、API、类型、函数、变量、命令和路径。
"""

    reference_aware = version in {"1.4.0", "1.5.0"}
    gap_aware = version == "1.5.0"
    navigation = (
        "人类需要查找已有分析、变更或实验时，从 `RECORDS.md` 按任务目的浏览；查找已审阅外部资料时从 `REFERENCES.md` 浏览。两个导览都由完整集合生成，不允许为单个查询手工挑选页面。"
        if reference_aware
        else "人类需要查找已有分析、变更或实验时，从 `RECORDS.md` 按任务目的浏览；该导览必须覆盖全部工作记录，不允许为单个查询手工挑选页面。"
    )
    generated = (
        "`human/pages`、`markdown/pages`、`human/references`、`markdown/references`、`INDEX.md`、`WIKI.md`、`REFERENCES.md`、投影清单和 SQLite 文件"
        if reference_aware
        else "`human/pages`、`markdown/pages`、`INDEX.md`、`WIKI.md`、投影清单和 SQLite 文件"
    )
    steps = [
        f"1. {generated}属于生成器管理内容，不直接编辑。",
        "2. 可复用分析、修改原因、踩坑和实验只通过 `record` 写入；正文使用简体中文，并通过 `--from-pack`、`--from-query` 或唯一 `--link` 回链至少一个知识页。",
        f"""3. 创建分析页的标准命令：

```powershell
{commands['record']}
```
""",
        "4. 更新已有人工笔记时使用同标题和 `--append`。Hook 仅采集会话与修改事件，并在 Agent 审核后新建会话页或修改页；其他已有页面只在任务明确要求时执行显式追加，不随每轮对话扩散更新。",
    ]
    number = 5
    if reference_aware:
        steps.append(f"{number}. 外部文本资料只通过 `reference ingest/review/audit/rollback` 进入独立参考层。Agent 必须重新打开归档原文，逐项提交精确行范围、原文文本、中文主张和中文来源核对；参考资料不成为代码实体。")
        number += 1
    if gap_aware:
        steps.append(
            f"""{number}. 检索证据不足、来源冲突或反馈需要暂缓时，使用 `gaps create` 把中文待验证说明和现有证据路径写入机器缺口层。缺口不属于已确认事实，也不为每项缺口创建页面；开始新任务时可执行：

```powershell
{commands['gaps_list']}
```
"""
        )
        number += 1
    steps.append(
        f"""{number}. 人工反馈通过 `feedback create` 进入带行范围和文本窗口的收件箱。处理前先执行：

```powershell
{commands['feedback_locate']}
```

生成器管理页面仍不直接编辑；采纳或部分采纳时先修改来源、生成规则或通过 `record` 写入落实记录，再用 `feedback resolve` 归档。拒绝必须写明中文理由；暂缓记录继续留在开放列表。反馈记录不删除。"""
    )
    number += 1
    maintained = "反馈、Agent Policy、工作记录"
    if reference_aware:
        maintained += "、参考资料"
    if gap_aware:
        maintained += "、研究缺口、机器操作日志"
    maintained += "、人类可读性、机器知识库和兼容索引"
    steps.append(
        f"""{number}. 结束实质任务前执行聚合维护门；它统一检查{maintained}，并且不创建知识页面：

```powershell
{commands['maintain']}
```

只有协议文件、中文与链接规则、human/markdown 镜像、笔记元数据以及两个 SQLite 索引全部一致时，才报告知识库维护完成。失败时根据 `failed_checks` 运行窄范围审计，修复对应笔记或重新执行 `record`/`reindex`，再复查。"""
    )
    maintenance = "\n".join(steps)
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
5. {navigation}

## 受控维护

{maintenance}

## 最小上下文原则

- 优先顺序固定为：`brief fast` → Agent pack → `entity/neighbors/source/changes` → 返回路径的窄范围读取。
- 不预先加载整个模块、整个 vault 或完整关系图。
- 页面正文保持面向人类的简体中文叙述；英文仅保留专有名词、API、类型、函数、变量、命令和路径。
"""


def adapter_texts_for_version(version: str, output: Path, repository: str, python: Path, ckb: Path) -> dict[str, str]:
    return _adapter_texts(protocol_text_for_version(version, output, repository, python, ckb))


def _record_roots(record: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for value in record.get("workspace_roots", []):
        if not isinstance(value, dict) or not isinstance(value.get("root"), str):
            raise BatchProjectError("protocol-record-invalid", "Agent Protocol workspace root record is invalid")
        roots.append(Path(value["root"]).resolve())
    return roots


def _tracked_paths(output: Path, workspace_roots: list[Path]) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = [
        ("protocol-record", output / "workspace-meta/agent-protocol.json"),
        ("protocol-audit", output / "workspace-meta/agent-protocol-audit.json"),
    ]
    for root_name in INTERNAL_ROOT_NAMES:
        root = output if root_name == "output" else output / root_name
        for relative in ADAPTER_PATHS.values():
            paths.append((f"internal-adapter:{root_name}", root / relative))
    for root in workspace_roots:
        for relative in ADAPTER_PATHS.values():
            paths.append(("workspace-managed-adapter", root / relative))
    for root_name in ("human", "markdown"):
        root = output / root_name
        paths.extend(
            [
                (f"output-contract:{root_name}", root / ".ckb/output-contract.json"),
                (f"generated-ownership:{root_name}", root / ".ckb-generated-files.json"),
                (f"obsidian-ignore:{root_name}", root / ".obsidian/app.json"),
                (f"obsidian-hide:{root_name}", root / ".obsidian/snippets/ckb.css"),
            ]
        )
    unique: dict[str, tuple[str, Path]] = {}
    for role, path in paths:
        unique[str(path.resolve())] = (role, path.resolve())
    return [unique[key] for key in sorted(unique)]


def snapshot_files(output: Path, workspace_roots: list[Path]) -> list[dict[str, Any]]:
    files = []
    for role, path in _tracked_paths(output.resolve(), workspace_roots):
        exists = path.is_file()
        files.append(
            {
                "role": role,
                "path": str(path),
                "exists": exists,
                "sha256": _sha256_bytes(path.read_bytes()) if exists else None,
                "mode": stat.S_IMODE(path.stat().st_mode) if exists else None,
            }
        )
    return files


def snapshot_digest(files: list[dict[str, Any]]) -> str:
    return _digest_value(files)


def _normalized_managed_block(value: bytes) -> str:
    try:
        text = value.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BatchProjectError("managed-file-encoding", f"managed instruction file is not UTF-8: {exc}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _validate_workspace_managed(path: Path, expected_text: str) -> None:
    if not path.is_file():
        raise BatchProjectError("managed-file-missing", f"workspace managed adapter is missing: {path}")
    text = _normalized_managed_block(path.read_bytes())
    begin_count = text.count(POLICY_BEGIN)
    end_count = text.count(POLICY_END)
    if begin_count > 1 or end_count > 1:
        raise BatchProjectError("managed-block-duplicate", f"workspace instruction file has duplicate managed markers: {path}")
    if begin_count != 1 or end_count != 1 or text.index(POLICY_BEGIN) > text.index(POLICY_END):
        raise BatchProjectError("managed-block-broken", f"workspace instruction file has broken managed markers: {path}")
    start = text.index(POLICY_BEGIN)
    end = text.index(POLICY_END, start) + len(POLICY_END)
    actual = text[start:end].rstrip("\n") + "\n"
    expected = f"{POLICY_BEGIN}\n{expected_text.rstrip()}\n{POLICY_END}\n"
    if actual != expected:
        raise BatchProjectError("managed-block-source-drift", f"workspace managed block differs from declared source version: {path}")


def _validate_internal_adapters(output: Path, expected: dict[str, str]) -> None:
    for root_name in INTERNAL_ROOT_NAMES:
        root = output if root_name == "output" else output / root_name
        if not root.is_dir():
            raise BatchProjectError("internal-root-missing", f"Agent Protocol internal root is missing: {root}")
        for key, relative in ADAPTER_PATHS.items():
            path = root / relative
            if not path.is_file():
                raise BatchProjectError("internal-adapter-missing", f"Agent Protocol internal adapter is missing: {path}")
            try:
                actual = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError as exc:
                raise BatchProjectError("internal-adapter-encoding", f"Agent Protocol internal adapter is not UTF-8: {path}") from exc
            if actual != expected[key]:
                raise BatchProjectError("internal-adapter-source-drift", f"Agent Protocol internal adapter differs from declared source version: {path}")


def _within_any(path: Path, roots: list[Path]) -> bool:
    return any(path_inside(path, root) for root in roots)


def _validate_structural_manifest(manifest: dict[str, Any]) -> tuple[list[Path], list[dict[str, Any]]]:
    reject_unknown_fields(manifest, MANIFEST_KEYS, "manifest")
    if manifest.get("schema_version") != BATCH_MANIFEST_SCHEMA_VERSION:
        raise CkbError(f"unsupported batch manifest schema_version: {manifest.get('schema_version')}")
    allowed_values = manifest.get("allowed_roots")
    if not isinstance(allowed_values, list) or not allowed_values:
        raise CkbError("batch manifest allowed_roots must be a non-empty list")
    allowed_roots = [require_absolute_path(value, f"allowed_roots[{index}]") for index, value in enumerate(allowed_values)]
    if len({str(path) for path in allowed_roots}) != len(allowed_roots):
        raise CkbError("batch manifest allowed_roots contains duplicates")
    for root in allowed_roots:
        if not root.is_dir():
            raise CkbError(f"batch manifest allowed root is missing: {root}")
    projects = manifest.get("projects")
    if not isinstance(projects, list) or not projects or len(projects) > MAX_BATCH_PROJECTS:
        raise CkbError(f"batch manifest projects must contain 1..{MAX_BATCH_PROJECTS} entries")
    identifiers: set[str] = set()
    outputs: list[Path] = []
    for index, project in enumerate(projects):
        if not isinstance(project, dict):
            raise CkbError(f"batch manifest projects[{index}] must be an object")
        reject_unknown_fields(project, PROJECT_KEYS, f"projects[{index}]")
        project_id = project.get("project_id")
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", project_id):
            raise CkbError(f"batch manifest projects[{index}].project_id is invalid")
        if project_id in identifiers:
            raise CkbError(f"batch manifest project_id is duplicated: {project_id}")
        identifiers.add(project_id)
        output = require_absolute_path(project.get("output"), f"projects[{index}].output")
        if not _within_any(output, allowed_roots):
            raise CkbError(f"batch manifest OUTPUT escapes allowed_roots: {output}")
        outputs.append(output)
    for index, output in enumerate(outputs):
        for other in outputs[index + 1 :]:
            if output == other:
                raise CkbError(f"batch manifest OUTPUT is duplicated: {output}")
            if path_inside(output, other) or path_inside(other, output):
                raise CkbError(f"batch manifest OUTPUT values must not be nested: {output} ; {other}")
    return allowed_roots, projects


def load_batch_manifest(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise CkbError(f"batch manifest is missing: {path}")
    value = json_load(path)
    if not isinstance(value, dict):
        raise CkbError("batch manifest root must be an object")
    _validate_structural_manifest(value)
    return value


def _inspect_project(project: dict[str, Any], allowed_roots: list[Path]) -> dict[str, Any]:
    project_id = str(project["project_id"])
    output = require_absolute_path(project.get("output"), f"{project_id}.output")
    source_version = str(project.get("source_version") or "")
    target_version = str(project.get("target_version") or "")
    if source_version not in PROTOCOL_RELEASES:
        raise BatchProjectError("source-version-unsupported", f"unsupported Agent Protocol source version: {source_version}")
    if target_version not in PROTOCOL_RELEASES:
        raise BatchProjectError("target-version-unsupported", f"unsupported Agent Protocol target version: {target_version}")
    try:
        path = supported_upgrade_path(source_version, target_version)
    except CkbError as exc:
        raise BatchProjectError("upgrade-path-missing", str(exc)) from exc
    if target_version != AGENT_PROTOCOL_VERSION:
        raise BatchProjectError(
            "target-version-not-current",
            f"batch upgrades must target the current Agent Protocol {AGENT_PROTOCOL_VERSION}: {target_version}",
        )
    if not output.is_dir():
        raise BatchProjectError("output-missing", f"knowledge OUTPUT is missing: {output}")
    state_path = output / "state.json"
    if not state_path.is_file():
        raise BatchProjectError("knowledge-state-missing", f"knowledge build state is missing: {state_path}")
    state = json_load(state_path)
    if not isinstance(state, dict) or not isinstance(state.get("repository"), dict) or not state["repository"].get("root"):
        raise BatchProjectError("knowledge-state-invalid", f"knowledge build state has no repository root: {state_path}")
    repository = str(state["repository"]["root"])
    protocol_path = output / "workspace-meta/agent-protocol.json"
    if not protocol_path.is_file():
        raise BatchProjectError("protocol-record-missing", f"Agent Protocol record is missing: {protocol_path}")
    record_bytes = protocol_path.read_bytes()
    record = json.loads(record_bytes.decode("utf-8-sig"))
    if not isinstance(record, dict):
        raise BatchProjectError("protocol-record-invalid", f"Agent Protocol record must be an object: {protocol_path}")
    if record.get("protocol_version") != source_version:
        raise BatchProjectError(
            "source-version-mismatch",
            f"Agent Protocol source version differs from manifest: {record.get('protocol_version')} != {source_version}",
        )
    expected_digest = project.get("expected_digest")
    if not isinstance(expected_digest, str) or not HEX_SHA256.fullmatch(expected_digest):
        raise BatchProjectError("expected-digest-invalid", f"expected_digest must be a lowercase SHA-256 for {project_id}")
    record_digest = _sha256_bytes(record_bytes)
    if record_digest != expected_digest:
        raise BatchProjectError("expected-digest-mismatch", f"Agent Protocol record digest differs from manifest for {project_id}")
    python = require_absolute_path(project.get("python"), f"{project_id}.python")
    ckb = require_absolute_path(project.get("ckb"), f"{project_id}.ckb")
    if not python.is_file():
        raise BatchProjectError("python-missing", f"Agent Protocol Python executable is missing: {python}")
    if not ckb.is_file():
        raise BatchProjectError("ckb-missing", f"Agent Protocol CKB entrypoint is missing: {ckb}")
    workspace_values = project.get("workspace_roots")
    if not isinstance(workspace_values, list) or len(workspace_values) > MAX_WORKSPACE_ROOTS:
        raise BatchProjectError("workspace-roots-invalid", f"workspace_roots must contain 0..{MAX_WORKSPACE_ROOTS} entries")
    workspace_roots = [require_absolute_path(value, f"{project_id}.workspace_roots[{index}]") for index, value in enumerate(workspace_values)]
    if len({str(root) for root in workspace_roots}) != len(workspace_roots):
        raise BatchProjectError("workspace-root-duplicate", f"workspace_roots contains duplicates for {project_id}")
    for root in workspace_roots:
        if not root.is_dir():
            raise BatchProjectError("workspace-root-missing", f"Agent Protocol workspace root is missing: {root}")
        if not _within_any(root, allowed_roots):
            raise BatchProjectError("workspace-root-out-of-bounds", f"workspace root escapes allowed_roots: {root}")
        repo_path = Path(repository)
        if not (path_inside(output, root) or (repo_path.is_absolute() and path_inside(repo_path, root))):
            raise BatchProjectError("workspace-root-unbound", f"workspace root contains neither repository nor OUTPUT: {root}")
    if {str(root) for root in workspace_roots} != {str(root) for root in _record_roots(record)}:
        raise BatchProjectError("workspace-root-record-mismatch", f"manifest workspace_roots differ from Agent Protocol record for {project_id}")
    harnesses = project.get("harnesses")
    if not isinstance(harnesses, list) or not harnesses or any(not isinstance(value, str) for value in harnesses):
        raise BatchProjectError("harnesses-invalid", f"harnesses must be a non-empty string list for {project_id}")
    if len(set(harnesses)) != len(harnesses):
        raise BatchProjectError("harness-duplicate", f"harnesses contains duplicates for {project_id}")
    unsupported = sorted(set(harnesses) - SUPPORTED_HARNESSES)
    if unsupported:
        raise BatchProjectError("harness-unsupported", f"unsupported Harness values for {project_id}: {', '.join(unsupported)}")
    source_python = Path(str(record.get("python") or "")).resolve()
    source_ckb = Path(str(record.get("ckb") or "")).resolve()
    expected_source = adapter_texts_for_version(source_version, output, repository, source_python, source_ckb)
    _validate_internal_adapters(output, expected_source)
    for root in workspace_roots:
        for key, relative in ADAPTER_PATHS.items():
            _validate_workspace_managed(root / relative, expected_source[key])
    files = snapshot_files(output, workspace_roots)
    observed_digest = snapshot_digest(files)
    risks = []
    if source_version != target_version:
        risks.append("managed-protocol-replacement")
    if workspace_roots:
        risks.append("workspace-user-content-boundary")
    if PROTOCOL_RELEASES[target_version].output_contract:
        risks.append("plugin-output-contract-parity")
    return {
        "project_id": project_id,
        "status": "ready",
        "action": (
            "noop"
            if source_version == target_version and source_python == python and source_ckb == ckb
            else "upgrade"
        ),
        "output": str(output),
        "repository": repository,
        "workspace_roots": [str(value) for value in workspace_roots],
        "source_version": source_version,
        "target_version": target_version,
        "upgrade_path": path,
        "harnesses": sorted(harnesses),
        "python": str(python),
        "ckb": str(ckb),
        "record_digest": record_digest,
        "observed_digest": observed_digest,
        "managed_files": files,
        "risks": sorted(risks),
        "rollback": {"command": f"agent-policy batch rollback --state STATE_PATH --project {project_id}"},
    }


def create_batch_plan(manifest_path: Path, write: Path | None = None) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest = load_batch_manifest(manifest_path)
    allowed_roots, projects = _validate_structural_manifest(manifest)
    normalized_manifest = {
        "schema_version": BATCH_MANIFEST_SCHEMA_VERSION,
        "allowed_roots": sorted(str(path) for path in allowed_roots),
        "projects": sorted(projects, key=lambda item: str(item["project_id"])),
    }
    manifest_digest = _digest_value(normalized_manifest)
    project_plans: list[dict[str, Any]] = []
    for project in normalized_manifest["projects"]:
        try:
            project_plans.append(_inspect_project(project, allowed_roots))
        except BatchProjectError as exc:
            project_plans.append(
                {
                    "project_id": str(project["project_id"]),
                    "status": "failed",
                    "action": "none",
                    "output": str(project["output"]),
                    "source_version": str(project.get("source_version") or ""),
                    "target_version": str(project.get("target_version") or ""),
                    "failure": {"category": exc.category, "detail": str(exc)},
                }
            )
        except (CkbError, OSError, ValueError, json.JSONDecodeError) as exc:
            project_plans.append(
                {
                    "project_id": str(project["project_id"]),
                    "status": "failed",
                    "action": "none",
                    "output": str(project["output"]),
                    "source_version": str(project.get("source_version") or ""),
                    "target_version": str(project.get("target_version") or ""),
                    "failure": {"category": "project-validation-failed", "detail": str(exc)},
                }
            )
    ready = sum(item["status"] == "ready" for item in project_plans)
    failed = len(project_plans) - ready
    status = "ready" if failed == 0 else "failed" if ready == 0 else "partial"
    body = {
        "schema_version": BATCH_PLAN_SCHEMA_VERSION,
        "batch_id": f"agent-policy-batch-{manifest_digest[:24]}",
        "status": status,
        "dry_run": True,
        "manifest": str(manifest_path),
        "manifest_digest": manifest_digest,
        "version_matrix": version_matrix(),
        "summary": {"projects": len(project_plans), "ready": ready, "failed": failed},
        "projects": project_plans,
    }
    plan = {**body, "plan_digest": _digest_value(body)}
    if write is not None:
        write = write.expanduser().resolve()
        json_write(write, plan)
        return {**plan, "plan_path": str(write)}
    return plan


def _load_batch_plan(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise CkbError(f"Agent Protocol batch plan is missing: {path}")
    plan = json_load(path)
    if not isinstance(plan, dict):
        raise CkbError("Agent Protocol batch plan root must be an object")
    if plan.get("schema_version") != BATCH_PLAN_SCHEMA_VERSION:
        raise CkbError(f"unsupported Agent Protocol batch plan schema: {plan.get('schema_version')}")
    digest = plan.get("plan_digest")
    body = {key: value for key, value in plan.items() if key != "plan_digest"}
    if not isinstance(digest, str) or _digest_value(body) != digest:
        raise CkbError("Agent Protocol batch plan digest mismatch")
    if not isinstance(plan.get("projects"), list) or not isinstance(plan.get("batch_id"), str):
        raise CkbError("Agent Protocol batch plan is structurally invalid")
    return plan


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _replace_workspace_block_bytes(existing: bytes, target_text: str, path: Path) -> bytes:
    bom = existing.startswith(b"\xef\xbb\xbf")
    try:
        text = existing.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BatchProjectError("managed-file-encoding", f"workspace managed adapter is not UTF-8: {path}") from exc
    begin_count = text.count(POLICY_BEGIN)
    end_count = text.count(POLICY_END)
    if begin_count > 1 or end_count > 1:
        raise BatchProjectError("managed-block-duplicate", f"workspace instruction file has duplicate managed markers: {path}")
    if begin_count != 1 or end_count != 1:
        raise BatchProjectError("managed-block-broken", f"workspace instruction file has broken managed markers: {path}")
    start = text.index(POLICY_BEGIN)
    end_marker = text.index(POLICY_END, start)
    end = end_marker + len(POLICY_END)
    segment = text[start:end]
    crlf = segment.count("\r\n")
    newline = "\r\n" if crlf and crlf == segment.count("\n") else "\n"
    block = f"{POLICY_BEGIN}\n{target_text.rstrip()}\n{POLICY_END}".replace("\n", newline)
    updated = (text[:start] + block + text[end:]).encode("utf-8")
    return (b"\xef\xbb\xbf" + updated) if bom else updated


def _target_record(project: dict[str, Any], previous: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    output = Path(project["output"]).resolve()
    repository = str(project["repository"])
    python = Path(project["python"]).resolve()
    ckb = Path(project["ckb"]).resolve()
    target_version = str(project["target_version"])
    texts = adapter_texts_for_version(target_version, output, repository, python, ckb)
    internal = {
        root_name: {
            "root": str((output if root_name == "output" else output / root_name).resolve()),
            "files": [relative.as_posix() for relative in ADAPTER_PATHS.values()],
        }
        for root_name in INTERNAL_ROOT_NAMES
    }
    workspace_records = []
    for root_value in project["workspace_roots"]:
        root = Path(root_value).resolve()
        files = []
        for relative in ADAPTER_PATHS.values():
            path = root / relative
            files.append(
                {
                    "path": str(path.resolve()),
                    "relative_path": relative.as_posix(),
                    "created": not path.is_file(),
                }
            )
        workspace_records.append({"root": str(root), "files": files})
    record = {
        "schema_version": 1,
        "protocol_version": target_version,
        "status": "installed",
        "output": str(output),
        "repository": repository,
        "python": str(python),
        "ckb": str(ckb),
        "internal_roots": internal,
        "workspace_roots": workspace_records,
        "commands": command_examples_for_version(target_version, output, python, ckb),
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
    return record, texts


def _desired_project_files(project: dict[str, Any]) -> dict[str, bytes | None]:
    from .obsidian_plugin import obsidian_plugin_installation
    from .output_contract import OUTPUT_CONTRACT_RELATIVE, output_contract_for_runtime

    output = Path(project["output"]).resolve()
    previous = json_load(output / "workspace-meta/agent-protocol.json")
    record, texts = _target_record(project, previous)
    desired: dict[str, bytes | None] = {}
    desired[str((output / "workspace-meta/agent-protocol.json").resolve())] = _json_bytes(record)
    for root_name in INTERNAL_ROOT_NAMES:
        root = output if root_name == "output" else output / root_name
        for key, relative in ADAPTER_PATHS.items():
            desired[str((root / relative).resolve())] = texts[key].encode("utf-8")
    for root_value in project["workspace_roots"]:
        root = Path(root_value).resolve()
        for key, relative in ADAPTER_PATHS.items():
            path = (root / relative).resolve()
            if not path.is_file():
                raise BatchProjectError("managed-file-missing", f"workspace managed adapter is missing: {path}")
            desired[str(path)] = _replace_workspace_block_bytes(path.read_bytes(), texts[key], path)
    python = Path(project["python"]).resolve()
    ckb = Path(project["ckb"]).resolve()
    for root_name in ("human", "markdown"):
        vault = (output / root_name).resolve()
        contract_path = (vault / OUTPUT_CONTRACT_RELATIVE).resolve()
        installation = obsidian_plugin_installation(vault)
        required = PROTOCOL_RELEASES[str(project["target_version"])].output_contract and installation["installed"]
        desired[str(contract_path)] = (
            _json_bytes(output_contract_for_runtime(output, vault, python, ckb)) if required else None
        )
        ownership_path = (vault / ".ckb-generated-files.json").resolve()
        if ownership_path.is_file():
            ownership = json_load(ownership_path)
            files = {str(value) for value in ownership.get("files", [])}
            if required:
                files.add(OUTPUT_CONTRACT_RELATIVE.as_posix())
            else:
                files.discard(OUTPUT_CONTRACT_RELATIVE.as_posix())
            ownership["files"] = sorted(files)
            desired[str(ownership_path)] = _json_bytes(ownership)
        app_path = (vault / ".obsidian/app.json").resolve()
        app = json_load(app_path) if app_path.is_file() else {}
        app["userIgnoreFilters"] = list(dict.fromkeys([*app.get("userIgnoreFilters", []), *OBSIDIAN_IGNORES]))
        desired[str(app_path)] = _json_bytes(app)
        css_path = (vault / ".obsidian/snippets/ckb.css").resolve()
        css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
        if OBSIDIAN_HIDE_CSS not in css:
            css = css.rstrip() + ("\n" if css.strip() else "") + OBSIDIAN_HIDE_CSS + "\n"
        desired[str(css_path)] = css.encode("utf-8")
    return desired


def _state_file(path: Path) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path.resolve()),
        "exists": exists,
        "sha256": _sha256_bytes(path.read_bytes()) if exists else None,
        "mode": stat.S_IMODE(path.stat().st_mode) if exists else None,
    }


def _write_bytes_atomic(path: Path, value: bytes, mode: int | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.ckb-batch-{os.getpid()}.tmp")
    temporary.write_bytes(value)
    os.chmod(temporary, mode if mode is not None else 0o644)
    os.replace(temporary, path)


def _desired_inventory(desired: dict[str, bytes | None]) -> list[dict[str, Any]]:
    result = []
    for path_value in sorted(desired):
        value = desired[path_value]
        path = Path(path_value)
        result.append(
            {
                "path": path_value,
                "exists": value is not None,
                "sha256": _sha256_bytes(value) if value is not None else None,
                "mode": stat.S_IMODE(path.stat().st_mode) if path.is_file() else 0o644,
            }
        )
    return result


def _create_backup(project: dict[str, Any], backup_root: Path) -> dict[str, Any]:
    output = Path(project["output"]).resolve()
    workspace_roots = [Path(value).resolve() for value in project["workspace_roots"]]
    files = snapshot_files(output, workspace_roots)
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_files = backup_root / "files"
    backup_files.mkdir(parents=True, exist_ok=True)
    manifest_files = []
    for index, item in enumerate(files):
        copied = dict(item)
        if item["exists"]:
            source = Path(item["path"])
            blob_name = f"{index:03d}-{item['sha256']}.bin"
            blob = backup_files / blob_name
            blob.write_bytes(source.read_bytes())
            if _sha256_bytes(blob.read_bytes()) != item["sha256"]:
                raise BatchProjectError("backup-verification-failed", f"backup digest mismatch: {source}")
            copied["backup_blob"] = f"files/{blob_name}"
        else:
            copied["backup_blob"] = None
        manifest_files.append(copied)
    manifest = {
        "schema_version": 1,
        "project_id": project["project_id"],
        "baseline_digest": snapshot_digest(files),
        "files": manifest_files,
    }
    manifest_path = backup_root / "backup.json"
    json_write(manifest_path, manifest)
    reopened = json_load(manifest_path)
    if reopened != manifest:
        raise BatchProjectError("backup-verification-failed", f"backup manifest did not reopen exactly: {manifest_path}")
    return {**manifest, "manifest_path": str(manifest_path.resolve())}


def _restore_backup(manifest_path: Path) -> None:
    manifest_path = manifest_path.resolve()
    manifest = json_load(manifest_path)
    for item in manifest["files"]:
        path = Path(item["path"])
        if item["exists"]:
            blob = manifest_path.parent / item["backup_blob"]
            value = blob.read_bytes()
            if _sha256_bytes(value) != item["sha256"]:
                raise BatchProjectError("backup-verification-failed", f"backup blob drifted: {blob}")
            _write_bytes_atomic(path, value, int(item["mode"]))
        elif path.exists():
            if path.is_file():
                path.unlink()
            else:
                raise BatchProjectError("rollback-path-type-drift", f"rollback target became a directory: {path}")


def _commit_desired(desired: dict[str, bytes | None]) -> None:
    for path_value in sorted(desired):
        path = Path(path_value)
        value = desired[path_value]
        if value is None:
            if path.is_file():
                path.unlink()
            continue
        mode = stat.S_IMODE(path.stat().st_mode) if path.is_file() else 0o644
        _write_bytes_atomic(path, value, mode)
        if path.read_bytes() != value:
            raise BatchProjectError("atomic-write-verification-failed", f"managed file did not reopen exactly: {path}")


def _descriptor_lock(descriptor: int) -> bool:
    """Acquire one OS-released byte-range/advisory lock without waiting."""
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl

    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (BlockingIOError, OSError):
        return False


def _descriptor_unlock(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)


def _descriptor_bytes(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        block = os.read(descriptor, 4096)
        if not block:
            return b"".join(chunks)
        chunks.append(block)


def _write_lock_descriptor(descriptor: int, record: dict[str, Any]) -> None:
    value = _json_bytes(record)
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.ftruncate(descriptor, 0)
    offset = 0
    while offset < len(value):
        offset += os.write(descriptor, value[offset:])
    os.fsync(descriptor)


def _process_start_identity(pid: int) -> tuple[str, str | None]:
    """Return alive/dead/unverifiable plus a PID-reuse-resistant start identity."""
    if pid < 1:
        return "dead", None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            return ("dead", None) if error in {87, 1168} else ("unverifiable", None)
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return "unverifiable", None
            if int(exit_code.value) != 259:  # STILL_ACTIVE
                return "dead", None
            created = wintypes.FILETIME()
            exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not kernel32.GetProcessTimes(handle, created, exited, kernel, user):
                return "unverifiable", None
            identity = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
            return "alive", str(identity)
        finally:
            kernel32.CloseHandle(handle)
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.is_file():
        try:
            fields = proc_stat.read_text(encoding="ascii").split()
            return "alive", fields[21] if len(fields) > 21 else None
        except (OSError, UnicodeError):
            return "unverifiable", None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "dead", None
    except (PermissionError, OSError):
        return "unverifiable", None
    return "unverifiable", None


def _new_output_lock_record(owner_token: str) -> dict[str, Any]:
    state, identity = _process_start_identity(os.getpid())
    if state != "alive" or not identity:
        raise BatchProjectError(
            "output-lock-owner-identity-unavailable",
            f"current process identity is unavailable for OUTPUT lock: {os.getpid()}",
        )
    return {
        "schema_version": OUTPUT_LOCK_SCHEMA_VERSION,
        "owner_pid": os.getpid(),
        "owner_token": owner_token,
        "owner_process_start": identity,
        "owner_host": socket.gethostname(),
        "created_at_utc": utc_now(),
    }


def _parse_output_lock(value: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        record = json.loads(value.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "output-lock-record-invalid"
    if not isinstance(record, dict) or set(record) != OUTPUT_LOCK_FIELDS:
        return None, "output-lock-record-invalid"
    if record.get("schema_version") != OUTPUT_LOCK_SCHEMA_VERSION:
        return None, "output-lock-record-invalid"
    if not isinstance(record.get("owner_pid"), int) or record["owner_pid"] < 1:
        return None, "output-lock-record-invalid"
    if not isinstance(record.get("owner_token"), str) or not OWNER_TOKEN_PATTERN.fullmatch(record["owner_token"]):
        return None, "output-lock-record-invalid"
    for field in ("owner_process_start", "owner_host", "created_at_utc"):
        if not isinstance(record.get(field), str) or not record[field] or len(record[field]) > 128:
            return None, "output-lock-record-invalid"
    return record, None


def _lock_owner_state(record: dict[str, Any]) -> str:
    if record["owner_host"] != socket.gethostname():
        return "output-lock-owner-unverifiable"
    state, identity = _process_start_identity(int(record["owner_pid"]))
    if state == "dead":
        return "output-lock-owner-dead"
    if state != "alive" or not identity:
        return "output-lock-owner-unverifiable"
    if identity != record["owner_process_start"]:
        return "output-lock-owner-pid-reused"
    return "concurrent-output-lock"


def _legacy_lock_owner_state(value: bytes) -> str | None:
    """Treat the former PID-only record conservatively during one-way recovery."""
    try:
        text = value.decode("ascii").strip()
        pid = int(text)
    except (UnicodeDecodeError, ValueError):
        return None
    state, _identity = _process_start_identity(pid)
    if state == "alive":
        return "output-lock-legacy-owner-live"
    if state == "dead":
        return "output-lock-legacy-owner-dead"
    return "output-lock-owner-unverifiable"


def _same_lock_file(lock: Path, descriptor: int) -> bool:
    try:
        left = os.fstat(descriptor)
        right = lock.stat()
    except FileNotFoundError:
        return False
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _release_output_lock(lock: Path, descriptor: int, owner_token: str) -> None:
    category: str | None = None
    try:
        if not _same_lock_file(lock, descriptor):
            category = "output-lock-release-file-replaced"
        else:
            record, invalid = _parse_output_lock(_descriptor_bytes(descriptor))
            if invalid or record is None or record.get("owner_token") != owner_token:
                category = "output-lock-release-owner-token-drift"
    finally:
        _descriptor_unlock(descriptor)
        os.close(descriptor)
    if category is None:
        try:
            record, invalid = _parse_output_lock(lock.read_bytes())
        except FileNotFoundError:
            category = "output-lock-release-missing"
        else:
            if invalid or record is None or record.get("owner_token") != owner_token:
                category = "output-lock-release-owner-token-drift"
            else:
                lock.unlink()
    if category:
        raise BatchProjectError(category, f"OUTPUT lock ownership changed before release: {lock}")


@contextmanager
def _output_lock(output: Path):
    lock = output.resolve() / "workspace-meta/agent-policy-batch.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    owner_token = uuid.uuid4().hex
    descriptor: int | None = None
    recovered_category: str | None = None
    last_category = "concurrent-output-lock"
    while descriptor is None:
        created = False
        try:
            candidate = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            created = True
            os.write(candidate, b" ")
        except FileExistsError:
            try:
                candidate = os.open(lock, os.O_RDWR)
            except FileNotFoundError:
                continue
        if not _descriptor_lock(candidate):
            os.close(candidate)
            last_category = "concurrent-output-lock"
        elif not _same_lock_file(lock, candidate):
            _descriptor_unlock(candidate)
            os.close(candidate)
            continue
        elif created:
            _write_lock_descriptor(candidate, _new_output_lock_record(owner_token))
            descriptor = candidate
        else:
            age = max(0.0, time.time() - os.fstat(candidate).st_mtime)
            record, invalid = _parse_output_lock(_descriptor_bytes(candidate))
            if invalid or record is None:
                legacy_state = _legacy_lock_owner_state(_descriptor_bytes(candidate))
                last_category = legacy_state or "output-lock-record-invalid"
                recover = age > LOCK_STALE_SECONDS and last_category in {
                    "output-lock-legacy-owner-dead",
                    "output-lock-record-invalid",
                }
                recovered_category = (
                    "output-lock-record-invalid-stale"
                    if recover and last_category == "output-lock-record-invalid"
                    else last_category if recover else None
                )
            else:
                last_category = _lock_owner_state(record)
                recover = age > LOCK_STALE_SECONDS and last_category in {
                    "output-lock-owner-dead",
                    "output-lock-owner-pid-reused",
                }
                recovered_category = last_category if recover else None
            if recover:
                _write_lock_descriptor(candidate, _new_output_lock_record(owner_token))
                descriptor = candidate
            else:
                _descriptor_unlock(candidate)
                os.close(candidate)
        if descriptor is None:
            if time.monotonic() >= deadline:
                raise BatchProjectError(last_category, f"Agent Protocol batch OUTPUT is busy: {output}")
            time.sleep(0.05)
    body_error = False
    try:
        yield {
            "schema_version": OUTPUT_LOCK_SCHEMA_VERSION,
            "owner_pid": os.getpid(),
            "owner_token": owner_token,
            "recovered_category": recovered_category,
            "_descriptor": descriptor,
        }
    except BaseException:
        body_error = True
        raise
    finally:
        try:
            _release_output_lock(lock, descriptor, owner_token)
        except BatchProjectError:
            if not body_error:
                raise


def _append_state_event(state: dict[str, Any], project_id: str, action: str, status: str, category: str | None = None) -> None:
    stamp = utc_now()
    event = {
        "event_id": stable_id("agent-policy-batch-event", state["batch_id"], project_id, action, status, stamp),
        "recorded_at_utc": stamp,
        "project_id": project_id,
        "action": action,
        "status": status,
        "category": category,
    }
    state.setdefault("events", []).append(event)
    state["events"] = state["events"][-MAX_STATE_EVENTS:]
    state["updated_at_utc"] = stamp


def _save_state(path: Path, state: dict[str, Any]) -> None:
    state["state_digest"] = _digest_value({key: value for key, value in state.items() if key != "state_digest"})
    json_write(path, state)


def _load_state(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise CkbError(f"Agent Protocol batch state is missing: {path}")
    state = json_load(path)
    if not isinstance(state, dict) or state.get("schema_version") != BATCH_STATE_SCHEMA_VERSION:
        raise CkbError("Agent Protocol batch state schema is invalid")
    digest = state.get("state_digest")
    body = {key: value for key, value in state.items() if key != "state_digest"}
    if not isinstance(digest, str) or digest != _digest_value(body):
        raise CkbError("Agent Protocol batch state digest mismatch")
    return state


def _new_state(plan: dict[str, Any], plan_path: Path, state_path: Path) -> dict[str, Any]:
    projects = {}
    for project in plan["projects"]:
        project_id = project["project_id"]
        if project["status"] == "ready":
            projects[project_id] = {
                "project_id": project_id,
                "status": "pending",
                "output": project["output"],
                "source_version": project["source_version"],
                "target_version": project["target_version"],
                "idempotency_key": stable_id(
                    "agent-policy-batch-project",
                    plan["batch_id"],
                    project_id,
                    project["observed_digest"],
                    project["target_version"],
                ),
                "baseline_digest": project["observed_digest"],
                "applied_digest": None,
                "backup": None,
                "desired_files": [],
                "failure": None,
                "evidence": None,
            }
        else:
            projects[project_id] = {
                "project_id": project_id,
                "status": "failed",
                "output": project["output"],
                "source_version": project["source_version"],
                "target_version": project["target_version"],
                "idempotency_key": None,
                "baseline_digest": None,
                "applied_digest": None,
                "backup": None,
                "desired_files": [],
                "failure": project["failure"],
                "evidence": None,
            }
    stamp = utc_now()
    return {
        "schema_version": BATCH_STATE_SCHEMA_VERSION,
        "batch_id": plan["batch_id"],
        "status": "running",
        "plan": str(plan_path.resolve()),
        "plan_digest": plan["plan_digest"],
        "state": str(state_path.resolve()),
        "created_at_utc": stamp,
        "updated_at_utc": stamp,
        "projects": projects,
        "events": [],
    }


def _current_digest(project: dict[str, Any]) -> str:
    return snapshot_digest(
        snapshot_files(Path(project["output"]), [Path(value) for value in project.get("workspace_roots", [])])
    )


def _recovery_matches(project_state: dict[str, Any], backup: dict[str, Any]) -> bool:
    desired = {item["path"]: item for item in project_state.get("desired_files", [])}
    for original in backup["files"]:
        path = Path(original["path"])
        current = _state_file(path)
        allowed = {(bool(original["exists"]), original["sha256"])}
        target = desired.get(original["path"])
        if target:
            allowed.add((bool(target["exists"]), target["sha256"]))
        if original["role"] == "protocol-audit":
            continue
        if (bool(current["exists"]), current["sha256"]) not in allowed:
            return False
    return True


def _write_project_evidence(
    output: Path,
    batch_id: str,
    project_state: dict[str, Any],
    action: str,
) -> Path:
    relative = Path("workspace-meta/agent-policy-batches") / batch_id / f"{project_state['project_id']}.json"
    path = output / relative
    value = {
        "schema_version": BATCH_EVIDENCE_SCHEMA_VERSION,
        "batch_id": batch_id,
        "project_id": project_state["project_id"],
        "status": project_state["status"],
        "action": action,
        "source_version": project_state["source_version"],
        "target_version": project_state["target_version"],
        "baseline_digest": project_state["baseline_digest"],
        "applied_digest": project_state["applied_digest"],
        "failure_category": (project_state.get("failure") or {}).get("category"),
        "recovery": f"agent-policy batch rollback --state STATE_PATH --project {project_state['project_id']}",
    }
    json_write(path, value)
    return path.resolve()


def _journal_batch_result(output: Path, action: str, status: str, evidence: Path) -> None:
    from .operation_journal import record_operation

    relative = evidence.relative_to(output.resolve()).as_posix()
    result_status = re.sub(r"[^a-z0-9._-]+", "-", status.casefold()).strip("-") or "completed"
    record_operation(output, "audit" if action == "audit" else "compile", f"agent-policy:batch-{action}", result_status, [relative])


def _summarize_state(state: dict[str, Any]) -> str:
    statuses = [item["status"] for item in state["projects"].values()]
    if statuses and all(value in {"completed", "skipped", "rolled-back"} for value in statuses):
        return "completed"
    if any(value in {"completed", "skipped", "rolled-back"} for value in statuses):
        return "partial"
    if statuses and all(value == "failed" for value in statuses):
        return "failed"
    return "running"


def apply_batch_plan(plan_path: Path, state_path: Path) -> dict[str, Any]:
    plan_path = plan_path.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    plan = _load_batch_plan(plan_path)
    for project in plan["projects"]:
        output = Path(project["output"]).resolve()
        if path_inside(state_path, output):
            raise CkbError(f"batch state must be outside every target OUTPUT: {state_path}")
    if state_path.is_file():
        state = _load_state(state_path)
        if state.get("batch_id") != plan["batch_id"] or state.get("plan_digest") != plan["plan_digest"]:
            raise CkbError("batch state is bound to a different immutable plan")
    else:
        state = _new_state(plan, plan_path, state_path)
        _save_state(state_path, state)
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    backup_base = state_path.parent / ".ckb-agent-policy-batch-backups" / plan["batch_id"]
    for project_id in sorted(plan_by_id):
        project = plan_by_id[project_id]
        project_state = state["projects"][project_id]
        if project["status"] != "ready":
            continue
        output = Path(project["output"]).resolve()
        workspace_roots = [Path(value).resolve() for value in project["workspace_roots"]]
        try:
            with _output_lock(output):
                if project_state["status"] in {"completed", "skipped"}:
                    current = snapshot_digest(snapshot_files(output, workspace_roots))
                    if current != project_state["applied_digest"]:
                        raise BatchProjectError("post-apply-drift", f"completed project drifted after batch apply: {project_id}")
                    project_state["status"] = "skipped"
                    _append_state_event(state, project_id, "apply", "skipped", "idempotent-success")
                    _save_state(state_path, state)
                    continue
                if project_state["status"] == "applying":
                    if not project_state.get("backup"):
                        raise BatchProjectError("resume-backup-missing", f"interrupted project has no backup: {project_id}")
                    backup = json_load(Path(project_state["backup"]))
                    if not _recovery_matches(project_state, backup):
                        raise BatchProjectError("resume-external-drift", f"interrupted project contains non-batch drift: {project_id}")
                    _restore_backup(Path(project_state["backup"]))
                    project_state["status"] = "pending"
                    _append_state_event(state, project_id, "resume", "restored-baseline")
                    _save_state(state_path, state)
                current_files = snapshot_files(output, workspace_roots)
                current_digest = snapshot_digest(current_files)
                if current_digest != project["observed_digest"]:
                    raise BatchProjectError("plan-target-drift", f"target bytes changed after plan: {project_id}")
                desired = {} if project["action"] == "noop" else _desired_project_files(project)
                backup = _create_backup(project, backup_base / project_id)
                if backup["baseline_digest"] != project["observed_digest"]:
                    raise BatchProjectError("backup-baseline-mismatch", f"backup differs from plan baseline: {project_id}")
                project_state["backup"] = backup["manifest_path"]
                project_state["desired_files"] = _desired_inventory(desired)
                project_state["status"] = "applying"
                _append_state_event(state, project_id, "apply", "applying")
                _save_state(state_path, state)
                _commit_desired(desired)
                from .agent_protocol import audit_agent_protocol

                audit = audit_agent_protocol(output)
                if audit.get("status") != "passed":
                    raise BatchProjectError(
                        "post-upgrade-audit-failed",
                        f"Agent Protocol audit failed after upgrade: {output / 'workspace-meta/agent-protocol-audit.json'}",
                    )
                applied_files = snapshot_files(output, workspace_roots)
                project_state["applied_digest"] = snapshot_digest(applied_files)
                project_state["status"] = "completed" if project["action"] == "upgrade" else "skipped"
                project_state["failure"] = None
                evidence = _write_project_evidence(output, plan["batch_id"], project_state, "apply")
                project_state["evidence"] = str(evidence)
                _append_state_event(state, project_id, "apply", project_state["status"])
                _save_state(state_path, state)
                _journal_batch_result(output, "apply", project_state["status"], evidence)
        except BatchProjectError as exc:
            if project_state.get("backup") and project_state.get("status") == "applying":
                try:
                    _restore_backup(Path(project_state["backup"]))
                except (BatchProjectError, OSError) as restore_exc:
                    exc = BatchProjectError("automatic-restore-failed", f"{exc}; restore failed: {restore_exc}")
            project_state["status"] = "failed"
            project_state["failure"] = {"category": exc.category, "detail": str(exc)}
            project_state["applied_digest"] = None
            evidence = _write_project_evidence(output, plan["batch_id"], project_state, "apply")
            project_state["evidence"] = str(evidence)
            _append_state_event(state, project_id, "apply", "failed", exc.category)
            _save_state(state_path, state)
            _journal_batch_result(output, "apply", "failed", evidence)
        except (CkbError, OSError, ValueError, json.JSONDecodeError) as exc:
            if project_state.get("backup") and project_state.get("status") == "applying":
                _restore_backup(Path(project_state["backup"]))
            project_state["status"] = "failed"
            project_state["failure"] = {"category": "apply-failed", "detail": str(exc)}
            project_state["applied_digest"] = None
            evidence = _write_project_evidence(output, plan["batch_id"], project_state, "apply")
            project_state["evidence"] = str(evidence)
            _append_state_event(state, project_id, "apply", "failed", "apply-failed")
            _save_state(state_path, state)
            _journal_batch_result(output, "apply", "failed", evidence)
    state["status"] = _summarize_state(state)
    _save_state(state_path, state)
    return batch_status(state_path)


def batch_status(state_path: Path) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_state(state_path)
    plan = _load_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    projects = []
    drifted = 0
    for project_id in sorted(state["projects"]):
        item = dict(state["projects"][project_id])
        plan_project = plan_by_id[project_id]
        current_digest = None
        expected_digest = None
        if plan_project["status"] == "ready":
            current_digest = snapshot_digest(
                snapshot_files(
                    Path(plan_project["output"]),
                    [Path(value) for value in plan_project["workspace_roots"]],
                )
            )
            expected_digest = item["baseline_digest"] if item["status"] == "rolled-back" else item["applied_digest"]
            if expected_digest and current_digest != expected_digest:
                item["drift"] = {"category": "managed-bytes-drift", "expected": expected_digest, "actual": current_digest}
                drifted += 1
            else:
                item["drift"] = None
        item["current_digest"] = current_digest
        item["recovery"] = f"agent-policy batch rollback --state '{state_path}' --project {project_id}"
        projects.append(item)
    counts: dict[str, int] = {}
    for item in projects:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    status = "drifted" if drifted else state["status"]
    return {
        "schema_version": BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "status": status,
        "state": str(state_path),
        "plan": state["plan"],
        "summary": {"projects": len(projects), "drifted": drifted, "counts": dict(sorted(counts.items()))},
        "projects": projects,
        "event_count": len(state.get("events", [])),
    }


def audit_batch_state(state_path: Path) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_state(state_path)
    plan = _load_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    results = []
    for project_id in sorted(state["projects"]):
        project_state = state["projects"][project_id]
        project = plan_by_id[project_id]
        errors = []
        audit = None
        if project["status"] != "ready":
            errors.append({"category": "plan-project-failed"})
        elif project_state["status"] in {"completed", "skipped"}:
            from .agent_protocol import audit_agent_protocol

            audit = audit_agent_protocol(Path(project["output"]))
            if audit.get("status") != "passed":
                errors.append({"category": "agent-policy-audit-failed", "evidence": str(Path(project["output"]) / "workspace-meta/agent-protocol-audit.json")})
            current = snapshot_digest(
                snapshot_files(Path(project["output"]), [Path(value) for value in project["workspace_roots"]])
            )
            if current != project_state["applied_digest"]:
                errors.append({"category": "applied-bytes-drift", "expected": project_state["applied_digest"], "actual": current})
            evidence = project_state.get("evidence")
            if not evidence or not Path(evidence).is_file():
                errors.append({"category": "batch-evidence-missing"})
        elif project_state["status"] == "rolled-back":
            current = snapshot_digest(
                snapshot_files(Path(project["output"]), [Path(value) for value in project["workspace_roots"]])
            )
            if current != project_state["baseline_digest"]:
                errors.append({"category": "rollback-bytes-drift", "expected": project_state["baseline_digest"], "actual": current})
        else:
            errors.append({"category": "project-not-complete", "status": project_state["status"]})
        result = {
            "project_id": project_id,
            "status": "passed" if not errors else "failed",
            "source_version": project_state["source_version"],
            "target_version": project_state["target_version"],
            "evidence": project_state.get("evidence"),
            "recovery": f"agent-policy batch rollback --state '{state_path}' --project {project_id}",
            "agent_policy": audit,
            "errors": errors,
        }
        results.append(result)
        if project["status"] == "ready" and Path(project["output"]).is_dir():
            evidence = _write_project_evidence(Path(project["output"]), state["batch_id"], project_state, "audit")
            project_state["evidence"] = str(evidence)
            _journal_batch_result(Path(project["output"]), "audit", result["status"], evidence)
    failed = sum(item["status"] == "failed" for item in results)
    _append_state_event(state, "batch", "audit", "passed" if failed == 0 else "failed", None if failed == 0 else "project-audit-failed")
    _save_state(state_path, state)
    return {
        "schema_version": BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "status": "passed" if failed == 0 else "failed",
        "state": str(state_path),
        "summary": {"projects": len(results), "passed": len(results) - failed, "failed": failed},
        "projects": results,
    }


def rollback_batch_state(state_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_state(state_path)
    plan = _load_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    requested = sorted(set(project_ids or []))
    unknown = sorted(set(requested) - set(state["projects"]))
    if unknown:
        raise CkbError(f"unknown Agent Protocol batch rollback project: {', '.join(unknown)}")
    selected = requested or sorted(
        project_id
        for project_id, item in state["projects"].items()
        if item["status"] in {"completed", "skipped"}
    )
    if not selected:
        raise CkbError("Agent Protocol batch rollback has no completed project to restore")
    results = []
    for project_id in selected:
        project_state = state["projects"][project_id]
        project = plan_by_id[project_id]
        output = Path(project["output"]).resolve()
        result = {
            "project_id": project_id,
            "status": "failed",
            "source_version": project_state["source_version"],
            "target_version": project_state["target_version"],
            "failure": None,
            "evidence": project_state.get("evidence"),
        }
        try:
            if project_state["status"] == "rolled-back":
                current = snapshot_digest(
                    snapshot_files(output, [Path(value) for value in project["workspace_roots"]])
                )
                if current != project_state["baseline_digest"]:
                    raise BatchProjectError("rollback-post-drift", f"rolled-back project drifted: {project_id}")
                result["status"] = "skipped"
                results.append(result)
                continue
            if project_state["status"] not in {"completed", "skipped"}:
                raise BatchProjectError("rollback-project-not-complete", f"project is not rollback eligible: {project_id}")
            if not project_state.get("backup") or not Path(project_state["backup"]).is_file():
                raise BatchProjectError("rollback-backup-missing", f"rollback backup is missing: {project_id}")
            with _output_lock(output):
                current = snapshot_digest(
                    snapshot_files(output, [Path(value) for value in project["workspace_roots"]])
                )
                if current != project_state["applied_digest"]:
                    raise BatchProjectError(
                        "rollback-external-drift",
                        f"rollback refuses to overwrite managed bytes changed after batch apply: {project_id}",
                    )
                _restore_backup(Path(project_state["backup"]))
                restored = snapshot_digest(
                    snapshot_files(output, [Path(value) for value in project["workspace_roots"]])
                )
                if restored != project_state["baseline_digest"]:
                    raise BatchProjectError("rollback-verification-failed", f"rollback baseline digest mismatch: {project_id}")
                project_state["status"] = "rolled-back"
                project_state["failure"] = None
                evidence = _write_project_evidence(output, state["batch_id"], project_state, "rollback")
                project_state["evidence"] = str(evidence)
                _append_state_event(state, project_id, "rollback", "rolled-back")
                _save_state(state_path, state)
                _journal_batch_result(output, "rollback", "rolled-back", evidence)
                result["status"] = "passed"
                result["evidence"] = str(evidence)
        except BatchProjectError as exc:
            result["failure"] = {"category": exc.category, "detail": str(exc)}
            _append_state_event(state, project_id, "rollback", "failed", exc.category)
            _save_state(state_path, state)
        except (CkbError, OSError, ValueError, json.JSONDecodeError) as exc:
            result["failure"] = {"category": "rollback-failed", "detail": str(exc)}
            _append_state_event(state, project_id, "rollback", "failed", "rollback-failed")
            _save_state(state_path, state)
        results.append(result)
    state["status"] = _summarize_state(state)
    _save_state(state_path, state)
    failed = sum(item["status"] == "failed" for item in results)
    passed = sum(item["status"] == "passed" for item in results)
    return {
        "schema_version": BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "status": "passed" if failed == 0 else "failed" if passed == 0 else "partial",
        "state": str(state_path),
        "summary": {"selected": len(results), "passed": passed, "skipped": len(results) - passed - failed, "failed": failed},
        "projects": results,
    }
