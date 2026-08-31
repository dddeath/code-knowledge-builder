"""Deterministic version matrix and batch upgrade contracts for Agent Protocol."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from .agent_protocol import (
    ADAPTER_PATHS,
    AGENT_PROTOCOL_VERSION,
    INTERNAL_ROOT_NAMES,
    POLICY_BEGIN,
    POLICY_END,
    _adapter_texts,
    _protocol_text,
)
from .automation import SUPPORTED_HARNESSES as AUTOMATION_HARNESSES
from .common import CkbError, json_load, json_write, path_inside


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
    path = supported_upgrade_path(source_version, target_version)
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
        "action": "noop" if source_version == target_version else "upgrade",
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
