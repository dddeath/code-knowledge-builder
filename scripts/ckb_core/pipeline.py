from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from xml.sax.saxutils import escape as xml_escape
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from . import SCHEMA_VERSION, VERSION
from .agent_index import audit_agent_index, build_agent_index
from .agent_protocol import audit_agent_protocol, project_agent_protocol
from .common import (
    AuditError,
    CkbError,
    DependencyError,
    ReviewRequired,
    StaleSourceError,
    clear_markers,
    json_load,
    json_write,
    run,
    path_inside,
    safe_rmtree,
    sha256_file,
    safe_title,
    stable_id,
    utc_now,
    write_marker,
)
from .gitrepo import (
    DEFAULT_INITIAL_COMMIT_MESSAGE,
    assert_source_snapshot,
    assert_unchanged,
    blob_bytes_many,
    create_source_snapshot,
    preflight,
    resolve_scope_paths,
    tracked_sources,
    tracked_csharp_project_files,
)
from .graphify_core import audit_graphify, project_graphify
from .knowledge_layers import (
    audit_facts_layer,
    audit_human_layer,
    build_facts_layer,
    sync_human_layer,
)
from .machine_knowledge import (
    audit_machine_knowledge,
    build_machine_knowledge,
    contains_chinese_narrative,
)
from .parsers import lexical_links, merge_csharp_partials, parse_file
from .navigation import (
    HUMAN_CODE_UNIT_KINDS,
    apply_navigation_plan,
    build_navigation_plan,
    build_review_packs,
    context_budget_record,
    estimated_tokens,
    module_name,
    page_limit,
)
from .obsidian import audit_obsidian, install_obsidian, prepare_vault, write_generated_ownership
from .page_config import (
    DEFAULT_PAGE_CONFIG,
    load_page_config,
    normalize_page_config,
    page_config_bytes,
    page_config_sha256,
)
from .providers import collect_semantics, resolve_executable
from .source_links import ensure_local_openers, source_markdown_link
from .workspace_notes import audit_notes, materialize_pending_notes, page_tag


MAX_FILES = 40
MAX_ENTITIES = 2000
MAX_BYTES = 1024 * 1024
ALLOWED_CLASSIFICATIONS = {"page", "appendix", "boundary"}
_CATALOG_CACHE: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
LOGSEQ_FILE_GRAPH_CONFIG_COMMIT = "fab27740975dcda1e93dbca718d1f620eda543c7"
LOGSEQ_FILE_GRAPH_CONFIG_SHA256 = "133005ee8ebbf15ff483d444d14fcb326c36424193223a9d09a6fedbdc0988e2"
LOGSEQ_FILE_GRAPH_CONFIG_URL = (
    "https://github.com/logseq/logseq/blob/"
    f"{LOGSEQ_FILE_GRAPH_CONFIG_COMMIT}/deps/common/resources/templates/config.edn"
)


def _replace_output_prefix(value: Any, old_output: str, new_output: str) -> Any:
    """Rewrite only serialized paths that point inside a relocated output."""

    if isinstance(value, dict):
        return {key: _replace_output_prefix(item, old_output, new_output) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_output_prefix(item, old_output, new_output) for item in value]
    if not isinstance(value, str):
        return value
    updated = value.replace(old_output, new_output)
    old_posix = old_output.replace("\\", "/")
    new_posix = new_output.replace("\\", "/")
    updated = updated.replace(old_posix, new_posix)
    return updated.replace(quote(old_output, safe=""), quote(new_output, safe=""))


def _relocate_completed_output(output: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Rebase output-owned absolute paths after an audited directory rename.

    Incremental migration deliberately finalizes in a staging directory and is
    promoted with a same-volume rename.  The detached Git worktree moves with
    that directory, so an absent old snapshot plus a valid local snapshot is an
    unambiguous relocation signal.  Immutable migration baselines are excluded
    because their original bytes are themselves audit evidence.
    """

    snapshot = state.get("source_snapshot")
    if not isinstance(snapshot, dict) or not snapshot.get("root"):
        return state
    stored_root = Path(str(snapshot["root"]))
    actual_root = (output / ".source-snapshot" / "worktree").resolve()
    if stored_root.resolve() == actual_root or stored_root.is_dir() or not actual_root.is_dir():
        return state
    if tuple(stored_root.parts[-2:]) != (".source-snapshot", "worktree"):
        raise StaleSourceError(f"fixed source snapshot path is not output-owned: {stored_root}")
    old_output = str(stored_root.parent.parent)
    new_output = str(output.resolve())
    relocated_state = _replace_output_prefix(state, old_output, new_output)
    assert_source_snapshot(relocated_state["repository"], relocated_state["source_snapshot"])
    rewritten: list[str] = []
    candidates = list(output.rglob("*.json"))
    candidates.extend(output / name for name in (".complete", ".machine.complete", ".human.complete") if (output / name).is_file())
    for path in sorted(set(candidates)):
        relative = path.relative_to(output)
        if relative.parts[:1] == (".source-snapshot",) or relative.parts[:2] == ("migration", "preserved-baseline"):
            continue
        try:
            document = json_load(path)
        except (CkbError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        updated = _replace_output_prefix(document, old_output, new_output)
        if updated != document:
            json_write(path, updated)
            rewritten.append(relative.as_posix())
    json_write(output / "state.json", relocated_state)
    json_write(
        output / "audit" / "output-relocation.json",
        {
            "schema_version": SCHEMA_VERSION,
            "status": "passed",
            "old_output": old_output,
            "new_output": new_output,
            "snapshot_root": str(actual_root),
            "rewritten_json_files": rewritten,
            "relocated_at_utc": utc_now(),
        },
    )
    return relocated_state


def _load_state(output: Path) -> dict[str, Any]:
    path = output / "state.json"
    if not path.is_file():
        raise CkbError(f"state.json does not exist: {path}")
    state = json_load(path)
    if "parse_batches" not in state and "chunks" in state:
        state["parse_batches"] = state["chunks"]
    # Keep the former chunk key as a CLI/state compatibility alias.  Both keys
    # reference the same in-memory list and are serialized together.
    state["chunks"] = state["parse_batches"]
    state = _relocate_completed_output(output, state)
    if isinstance(state.get("source_snapshot"), dict):
        assert_source_snapshot(state["repository"], state["source_snapshot"])
    else:
        # Compatibility for completed 3.2.0 outputs created before fixed
        # source snapshots existed.
        assert_unchanged(state["repository"])
    record = state.get("page_config")
    if not isinstance(record, dict):
        raise StaleSourceError("output has no pinned page configuration; initialize it with the current Skill version")
    config_path = output / str(record.get("relative_path", "page-config.json"))
    if not config_path.is_file():
        raise StaleSourceError(f"pinned page configuration is missing: {config_path}")
    actual_hash = sha256_file(config_path)
    if actual_hash != record.get("sha256"):
        raise StaleSourceError(
            f"pinned page configuration drifted: expected {record.get('sha256')}, got {actual_hash}"
        )
    try:
        config = normalize_page_config(json_load(config_path))
    except CkbError as exc:
        raise StaleSourceError(f"pinned page configuration is invalid: {exc}") from exc
    if page_config_bytes(config) != config_path.read_bytes():
        raise StaleSourceError("pinned page configuration is not in canonical normalized form")
    return state


def _module(path: str) -> str:
    return module_name(path)


def _parse_entry(value: str) -> tuple[str | None, str | None, str]:
    if "#" not in value:
        return None, None, value
    left, qualified = value.split("#", 1)
    if ":" not in left:
        raise CkbError(f"entry must use LANGUAGE:PATH#QUALIFIED_NAME: {value}")
    language, path = left.split(":", 1)
    return language, path.replace("\\", "/"), qualified


def _resolve_entries(entities: list[dict[str, Any]], entries: list[str]) -> list[str]:
    result: list[str] = []
    for value in entries:
        language, path, qualified = _parse_entry(value)
        matches = [
            entity
            for entity in entities
            if entity["kind"] != "file"
            and (language is None or entity["language"] == language)
            and (
                path is None
                or entity["path"] == path
                or any(fragment.get("path") == path for fragment in entity.get("fragments", []))
            )
            and (entity["qualified_name"] == qualified or (language is None and entity["name"] == qualified))
        ]
        if len(matches) != 1:
            candidates = [f"{e['language']}:{e['path']}#{e['qualified_name']}" for e in matches[:30]]
            raise CkbError(f"entry resolves to {len(matches)} entities: {value}; candidates={candidates}")
        result.append(matches[0]["id"])
    return result


def _expand_entries(
    all_entities: list[dict[str, Any]],
    links: list[dict[str, Any]],
    entry_ids: list[str],
    depth: int,
    direction: str,
) -> set[str]:
    if not entry_ids:
        return set()
    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)
    for link in links:
        if link["type"] != "references":
            continue
        outgoing[link["source"]].add(link["target"])
        incoming[link["target"]].add(link["source"])
    reached = set(entry_ids)
    frontier = deque((value, 0) for value in entry_ids)
    while frontier:
        current, level = frontier.popleft()
        if level >= depth:
            continue
        neighbors: set[str] = set()
        if direction in {"both", "callees"}:
            neighbors.update(outgoing.get(current, set()))
        if direction in {"both", "callers"}:
            neighbors.update(incoming.get(current, set()))
        for neighbor in neighbors:
            if neighbor not in reached:
                reached.add(neighbor)
                frontier.append((neighbor, level + 1))
    return reached


def _chunks(files: list[dict[str, Any]], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entities_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entity in entities:
        if entity["kind"] != "boundary":
            entities_by_path[entity["path"]].append(entity)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for file_entry in sorted(files, key=lambda item: item["path"]):
        grouped[_module(file_entry["path"])].append(file_entry)
    result: list[dict[str, Any]] = []
    current_units: list[dict[str, Any]] = []
    current_entities = 0
    current_bytes = 0

    def flush(module_name: str) -> None:
        nonlocal current_units, current_entities, current_bytes
        if not current_units:
            return
        chunk_id = f"batch-{len(result) + 1:04d}"
        paths = sorted({item["file"]["path"] for item in current_units})
        entity_ids = [entity_id for item in current_units for entity_id in item["entity_ids"]]
        result.append(
            {
                "id": chunk_id,
                "module": module_name,
                "file_paths": paths,
                "entity_ids": entity_ids,
                "file_count": len(paths),
                "entity_count": current_entities,
                "source_bytes": current_bytes,
                "oversized_unit": any(item.get("oversized") for item in current_units),
                "status": "planned",
            }
        )
        current_units = []
        current_entities = 0
        current_bytes = 0

    def units_for_file(file_entry: dict[str, Any]) -> list[dict[str, Any]]:
        file_entities = sorted(entities_by_path[file_entry["path"]], key=lambda value: (value["range"]["start_byte"], value["id"]))
        if len(file_entities) <= MAX_ENTITIES and int(file_entry["size"]) <= MAX_BYTES:
            return [{"file": file_entry, "entity_ids": [value["id"] for value in file_entities], "bytes": int(file_entry["size"])}]
        file_entity = next((value for value in file_entities if value["kind"] == "file"), None)
        by_id = {value["id"]: value for value in file_entities}
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for entity in file_entities:
            if entity["kind"] == "file":
                continue
            cursor = entity
            while cursor.get("parent_id") and cursor["parent_id"] in by_id and by_id[cursor["parent_id"]]["kind"] != "file":
                cursor = by_id[cursor["parent_id"]]
            groups[cursor["id"]].append(entity)
        ordered_groups = sorted(groups.values(), key=lambda values: min(value["range"]["start_byte"] for value in values))
        units: list[dict[str, Any]] = []
        pending_ids = [file_entity["id"]] if file_entity else []
        pending_start = 0
        pending_end = 0
        for values in ordered_groups:
            values.sort(key=lambda value: (value["range"]["start_byte"], value["id"]))
            group_ids = [value["id"] for value in values]
            group_start = min(value["range"]["start_byte"] for value in values)
            group_end = max(value["range"]["end_byte"] for value in values)
            group_bytes = max(1, group_end - group_start)
            pending_bytes = max(0, pending_end - pending_start)
            if pending_ids and len(pending_ids) > (1 if file_entity and pending_ids == [file_entity["id"]] else 0) and (
                len(pending_ids) + len(group_ids) > MAX_ENTITIES or pending_bytes + group_bytes > MAX_BYTES
            ):
                units.append({"file": file_entry, "entity_ids": pending_ids, "bytes": max(1, pending_bytes)})
                pending_ids = []
                pending_start = group_start
                pending_end = group_start
            if not pending_ids:
                pending_start = group_start
            pending_ids.extend(group_ids)
            pending_end = max(pending_end, group_end)
            if len(group_ids) > MAX_ENTITIES or group_bytes > MAX_BYTES:
                units.append({"file": file_entry, "entity_ids": pending_ids, "bytes": group_bytes, "oversized": True})
                pending_ids = []
                pending_start = pending_end
        if pending_ids:
            units.append({"file": file_entry, "entity_ids": pending_ids, "bytes": max(1, pending_end - pending_start)})
        return units or [{"file": file_entry, "entity_ids": [value["id"] for value in file_entities], "bytes": int(file_entry["size"]), "oversized": True}]

    for module_name in sorted(grouped):
        flush(module_name)
        for file_entry in grouped[module_name]:
            for unit in units_for_file(file_entry):
                count = len(unit["entity_ids"])
                size = int(unit["bytes"])
                file_count = len({value["file"]["path"] for value in current_units} | {file_entry["path"]})
                if current_units and (
                    file_count > MAX_FILES
                    or current_entities + count > MAX_ENTITIES
                    or current_bytes + size > MAX_BYTES
                ):
                    flush(module_name)
                current_units.append(unit)
                current_entities += count
                current_bytes += size
                if unit.get("oversized"):
                    flush(module_name)
        flush(module_name)
    return result


def _write_review_pack_templates(
    output: Path,
    review_packs: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    sources: dict[str, bytes],
) -> None:
    by_id = {entity["id"]: entity for entity in entities}
    for pack in review_packs:
        pack_dir = output / "review-packs" / pack["id"]
        pack_dir.mkdir(parents=True, exist_ok=True)
        reviews = []
        for entity_id in pack["entity_ids"]:
            entity = by_id[entity_id]
            start = int(entity["range"]["start_byte"])
            end = int(entity["range"]["end_byte"])
            source = sources.get(entity["path"], b"")
            item = {
                "entity_id": entity_id,
                "classification": entity["classification"],
                "owner_page_id": entity["owner_page_id"],
                "source_path": entity["path"],
                "start_line": entity["range"]["start_line"],
                "end_line": entity["range"]["end_line"],
                "source_blob": entity["blob"],
                "source_excerpt": source[start:end].decode("utf-8", errors="replace"),
                "status": "draft",
                "evidence_note": "",
            }
            if pack["kind"] == "appendix-review":
                item["description_zh"] = ""
            else:
                item.update({"meaning_zh": "", "role_zh": "", "change_when_zh": ""})
            reviews.append(item)
        template = {
            "schema_version": SCHEMA_VERSION,
            "pack_id": pack["id"],
            "kind": pack["kind"],
            "reviewer": "Agent",
            "reviewed_at_utc": None,
            "reviews": reviews,
        }
        template_path = pack_dir / "review-template.json"
        json_write(template_path, template)
        pack["review_template_path"] = str(template_path.resolve())


def _normalize_repo_selector(repo: Path, value: str) -> str:
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (repo / candidate).resolve()
    if not path_inside(resolved, repo):
        raise CkbError(f"C# project selector is outside the repository: {value}")
    return resolved.relative_to(repo).as_posix()


def _resolve_csharp_workspace(
    repository: dict[str, Any],
    project_files: list[dict[str, Any]],
    csharp_solution: str | None,
    csharp_project: str | None,
) -> dict[str, Any]:
    if csharp_solution and csharp_project:
        raise CkbError("use only one of --csharp-solution or --csharp-project")
    repo = Path(repository["root"]).resolve()
    tracked = {item["path"]: item for item in project_files}
    solutions = sorted(path for path in tracked if PurePosixPath(path).suffix.lower() in {".sln", ".slnx"})
    projects = sorted(path for path in tracked if PurePosixPath(path).suffix.lower() == ".csproj")
    selected: str | None = None
    kind = "folder"
    selection = "fallback-no-project-file"
    if csharp_solution:
        selected = _normalize_repo_selector(repo, csharp_solution)
        if selected not in solutions:
            raise CkbError(f"--csharp-solution is not a tracked .sln/.slnx file: {selected}; candidates={solutions}")
        kind, selection = "solution", "explicit"
    elif csharp_project:
        selected = _normalize_repo_selector(repo, csharp_project)
        if selected not in projects:
            raise CkbError(f"--csharp-project is not a tracked .csproj file: {selected}; candidates={projects}")
        kind, selection = "project", "explicit"
    elif len(solutions) == 1:
        selected, kind, selection = solutions[0], "solution", "unique-auto"
    elif len(solutions) > 1:
        raise CkbError(f"multiple tracked C# solutions require --csharp-solution: candidates={solutions}")
    elif len(projects) == 1:
        selected, kind, selection = projects[0], "project", "unique-auto"
    elif len(projects) > 1:
        raise CkbError(f"multiple tracked C# projects require --csharp-project: candidates={projects}")
    return {
        "kind": kind,
        "path": selected,
        "selection": selection,
        "solution_candidates": solutions,
        "project_candidates": projects,
        "workspace_root": str(repo),
        "precision": "exact" if selected else "bounded-approximate",
        "restore": {"requested": False, "performed": False, "network_restore": False},
    }


def _prepare_csharp_restore(output: Path, repository: dict[str, Any], workspace: dict[str, Any]) -> dict[str, Any]:
    dotnet = resolve_executable("dotnet")
    if not dotnet:
        raise DependencyError("dotnet 10 SDK is required for --allow-dotnet-restore")
    runtime_root = output / ".csharp-runtime"
    existing_fallback = workspace.get("kind") == "fallback-project" and workspace.get("workspace_root")
    worktree = Path(workspace["workspace_root"]).resolve() if existing_fallback else runtime_root / "worktree"
    packages = runtime_root / "nuget-packages"
    cli_home = runtime_root / "dotnet-home"
    runtime_root.mkdir(parents=True, exist_ok=True)
    packages.mkdir()
    cli_home.mkdir()
    if not existing_fallback:
        add = run(["git", "-C", repository["root"], "worktree", "add", "--detach", "--force", str(worktree), repository["commit"]], timeout=180)
        if add.returncode:
            raise CkbError(f"isolated C# restore worktree creation failed: {(add.stderr or add.stdout).strip()}")
    target = workspace.get("path") or "."
    env = os.environ.copy()
    env.update(
        {
            "NUGET_PACKAGES": str(packages.resolve()),
            "DOTNET_CLI_HOME": str(cli_home.resolve()),
            "DOTNET_NOLOGO": "1",
            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        }
    )
    command = [dotnet, "restore", target, "--packages", str(packages.resolve()), "--nologo"]
    restored = run(command, cwd=worktree, env=env, timeout=1800)
    record_dir = output / "audit" / "csharp-restore"
    record_dir.mkdir(parents=True, exist_ok=True)
    command_record = {
        "command": command,
        "cwd": str(worktree.resolve()),
        "environment": {key: env[key] for key in ("NUGET_PACKAGES", "DOTNET_CLI_HOME", "DOTNET_NOLOGO", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE", "DOTNET_CLI_TELEMETRY_OPTOUT")},
        "exit_status": restored.returncode,
        "stdout": restored.stdout,
        "stderr": restored.stderr,
    }
    json_write(record_dir / "command.json", command_record)
    if restored.returncode:
        raise CkbError(f"explicit isolated dotnet restore failed; see {record_dir / 'command.json'}")
    manifests = []
    restored_files = [value for value in packages.rglob("*") if value.is_file()]
    restored_files.extend(
        value
        for value in worktree.rglob("*")
        if value.is_file() and (value.name == "project.assets.json" or value.name.endswith((".nuget.g.props", ".nuget.g.targets", ".nuget.cache")))
    )
    for path in sorted(set(restored_files)):
        manifests.append({"path": path.relative_to(runtime_root).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)})
    json_write(record_dir / "files.json", {"files": manifests})
    rollback = record_dir / "rollback.ps1"
    quoted_repo = str(repository["root"]).replace("'", "''")
    quoted_worktree = str(worktree.resolve()).replace("'", "''")
    quoted_runtime = str(runtime_root.resolve()).replace("'", "''")
    rollback.write_text(
        "$ErrorActionPreference = 'Stop'\n"
        f"& git -C '{quoted_repo}' worktree remove --force '{quoted_worktree}'\n"
        f"if (Test-Path -LiteralPath '{quoted_runtime}') {{ Remove-Item -LiteralPath '{quoted_runtime}' -Recurse -Force }}\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        **workspace,
        "workspace_root": str(worktree.resolve()),
        "restore": {
            "requested": True,
            "performed": True,
            "network_restore": True,
            "command_record": str((record_dir / "command.json").resolve()),
            "file_manifest": str((record_dir / "files.json").resolve()),
            "rollback": str(rollback.resolve()),
            "worktree_commit": repository["commit"],
        },
    }


def _prepare_csharp_fallback_workspace(
    output: Path,
    repository: dict[str, Any],
    workspace: dict[str, Any],
    selected_paths: list[str],
) -> dict[str, Any]:
    """Create a no-restore SDK fallback project in an isolated fixed-commit worktree."""
    runtime_root = output / ".csharp-runtime"
    worktree = runtime_root / "fallback-worktree"
    runtime_root.mkdir(parents=True, exist_ok=True)
    add = run(["git", "-C", repository["root"], "worktree", "add", "--detach", "--force", str(worktree), repository["commit"]], timeout=180)
    if add.returncode:
        raise CkbError(f"isolated C# fallback worktree creation failed: {(add.stderr or add.stdout).strip()}")
    project_name = ".ckb-bounded-fallback.csproj"
    project = worktree / project_name
    compile_items = "\n".join(f'    <Compile Include="{xml_escape(path)}" />' for path in sorted(selected_paths))
    project_text = (
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <PropertyGroup>\n"
        "    <TargetFramework>net10.0</TargetFramework>\n"
        "    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>\n"
        "    <ImplicitUsings>disable</ImplicitUsings>\n"
        "    <Nullable>disable</Nullable>\n"
        "    <RestoreIgnoreFailedSources>true</RestoreIgnoreFailedSources>\n"
        "  </PropertyGroup>\n"
        "  <ItemGroup>\n"
        f"{compile_items}\n"
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    project.write_text(project_text, encoding="utf-8", newline="\n")
    record_dir = output / "audit" / "csharp-fallback"
    record_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "status": "ready",
        "precision": "bounded-approximate",
        "network_restore": False,
        "worktree": str(worktree.resolve()),
        "worktree_commit": repository["commit"],
        "project": project_name,
        "project_sha256": sha256_file(project),
        "selected_source_paths": sorted(selected_paths),
        "flags": ["TargetFramework=net10.0", "EnableDefaultCompileItems=false", "ImplicitUsings=disable", "Nullable=disable"],
    }
    json_write(record_dir / "record.json", record)
    quoted_repo = str(repository["root"]).replace("'", "''")
    quoted_worktree = str(worktree.resolve()).replace("'", "''")
    quoted_runtime = str(runtime_root.resolve()).replace("'", "''")
    rollback = record_dir / "rollback.ps1"
    rollback.write_text(
        "$ErrorActionPreference = 'Stop'\n"
        f"& git -C '{quoted_repo}' worktree remove --force '{quoted_worktree}'\n"
        f"if (Test-Path -LiteralPath '{quoted_runtime}') {{ Remove-Item -LiteralPath '{quoted_runtime}' -Recurse -Force }}\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        **workspace,
        "kind": "fallback-project",
        "path": project_name,
        "workspace_root": str(worktree.resolve()),
        "precision": "bounded-approximate",
        "fallback": {**record, "record": str((record_dir / "record.json").resolve()), "rollback": str(rollback.resolve())},
    }


def _rekey_reused_file_parse(
    repository: dict[str, Any],
    file_entry: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    """Reuse an exact-blob parse while rebuilding every commit-sensitive ID."""
    old_file = previous.get("file", {})
    if old_file.get("path") != file_entry.get("path") or old_file.get("blob") != file_entry.get("blob"):
        raise CkbError(f"migration parse reuse mismatch: {file_entry.get('path')}")
    if previous.get("parse", {}).get("status") != "passed":
        raise CkbError(f"migration source parse did not pass: {file_entry.get('path')}")
    id_map: dict[str, str] = {}
    for entity in previous.get("entities", []):
        if entity.get("kind") == "file":
            new_id = file_entry["id"]
        else:
            source_range = entity.get("range", {})
            new_id = stable_id(
                "ent",
                repository["commit"],
                file_entry["blob"],
                file_entry["path"],
                source_range.get("start_byte"),
                source_range.get("end_byte"),
                entity.get("kind"),
                entity.get("name"),
            )
        id_map[str(entity["id"])] = new_id
    entities: list[dict[str, Any]] = []
    for entity in previous.get("entities", []):
        item = json.loads(json.dumps(entity))
        item["id"] = id_map[str(entity["id"])]
        item["commit"] = repository["commit"]
        item["blob"] = file_entry["blob"]
        item["path"] = file_entry["path"]
        if entity.get("parent_id"):
            item["parent_id"] = id_map[str(entity["parent_id"])]
        entities.append(item)
    return {
        "file": dict(file_entry),
        "parse": json.loads(json.dumps(previous["parse"])),
        "entities": entities,
        "migration_reuse": {
            "basis": "exact-path-language-blob-and-passed-parse",
            "previous_file_id": old_file.get("id"),
            "rekeyed_entity_count": len(entities),
        },
    }


def initialize(
    repo: Path,
    output: Path,
    format_name: str,
    scope_paths: list[str],
    entries: list[str],
    expand_depth: int,
    expand_direction: str,
    includes: list[str],
    init_git: bool = False,
    initial_commit_message: str = DEFAULT_INITIAL_COMMIT_MESSAGE,
    git_author_name: str | None = None,
    git_author_email: str | None = None,
    csharp_solution: str | None = None,
    csharp_project: str | None = None,
    allow_dotnet_restore: bool = False,
    page_config_path: Path | None = None,
    reuse_from_output: Path | None = None,
) -> dict[str, Any]:
    if output.exists():
        raise CkbError(f"output already exists: {output}")
    page_config, page_config_source = load_page_config(page_config_path)
    resolved_repo = repo.resolve()
    resolved_output = output.resolve()
    if path_inside(resolved_output, resolved_repo) or path_inside(resolved_repo, resolved_output):
        raise CkbError("output and repository must be separate, non-overlapping directories")
    repository = preflight(
        resolved_repo,
        initialize_git=init_git,
        initial_commit_message=initial_commit_message,
        git_author_name=git_author_name,
        git_author_email=git_author_email,
    )
    actual_repo_root = Path(repository["root"]).resolve()
    if path_inside(resolved_output, actual_repo_root) or path_inside(actual_repo_root, resolved_output):
        raise CkbError("output and repository must be separate, non-overlapping directories")
    output.mkdir(parents=True)
    (output / "chunks").mkdir()
    (output / "parse-batches").mkdir()
    (output / "review-packs").mkdir()
    (output / "audit").mkdir()
    source_snapshot = create_source_snapshot(repository, output)
    pinned_page_config = output / "page-config.json"
    pinned_page_config.write_bytes(page_config_bytes(page_config))
    page_config_record = {
        "schema_version": page_config["schema_version"],
        "relative_path": "page-config.json",
        "sha256": page_config_sha256(page_config),
        "source": page_config_source,
    }
    entry_include_paths = [path for value in entries if (path := _parse_entry(value)[1]) is not None]
    all_files, exclusions = tracked_sources(repository, [*includes, *entry_include_paths])
    if not all_files:
        raise CkbError("repository has no supported tracked project source")
    file_results: list[dict[str, Any]] = []
    all_entities: list[dict[str, Any]] = []
    sources = blob_bytes_many(repository, all_files)
    reusable_by_path: dict[str, dict[str, Any]] = {}
    reuse_origin: dict[str, Any] | None = None
    if reuse_from_output is not None:
        reuse_root = reuse_from_output.resolve()
        old_catalog_path = reuse_root / "catalog.json"
        old_state_path = reuse_root / "state.json"
        old_complete_path = reuse_root / ".complete"
        old_audit_path = reuse_root / "audit" / "global.json"
        if not all(path.is_file() for path in (old_catalog_path, old_state_path, old_complete_path, old_audit_path)):
            raise CkbError(f"migration reuse source is not a completed CKB output: {reuse_root}")
        old_state = json_load(old_state_path)
        old_audit = json_load(old_audit_path)
        if old_state.get("status") != "complete" or old_audit.get("status") != "passed":
            raise CkbError(f"migration reuse source did not pass its global audit: {reuse_root}")
        old_catalog = json_load(old_catalog_path)
        reusable_by_path = {
            item["file"]["path"]: item
            for item in old_catalog.get("files", [])
            if item.get("file", {}).get("path") and item.get("parse", {}).get("status") == "passed"
        }
        reuse_origin = {
            "output": str(reuse_root),
            "version": old_state.get("version"),
            "commit": old_state.get("repository", {}).get("commit"),
        }
    reused_paths: list[str] = []
    reused_entity_count = 0
    for file_entry in all_files:
        source = sources[file_entry["path"]]
        previous = reusable_by_path.get(file_entry["path"])
        if (
            previous
            and previous.get("file", {}).get("blob") == file_entry.get("blob")
            and previous.get("file", {}).get("language") == file_entry.get("language")
        ):
            parsed = _rekey_reused_file_parse(repository, file_entry, previous)
            reused_paths.append(file_entry["path"])
            reused_entity_count += len(parsed["entities"])
        else:
            parsed = parse_file(repository, file_entry, source)
        file_results.append(parsed)
        all_entities.extend(parsed["entities"])
    all_entities = merge_csharp_partials(repository, all_entities)
    all_links = lexical_links(all_entities, sources)
    selected_paths = resolve_scope_paths(all_files, scope_paths)
    entry_ids = _resolve_entries(all_entities, entries)
    reached = _expand_entries(all_entities, all_links, entry_ids, expand_depth, expand_direction)
    entity_by_id = {entity["id"]: entity for entity in all_entities}
    selected_paths.update(entity_by_id[value]["path"] for value in reached)
    for entity in all_entities:
        fragment_paths = {fragment["path"] for fragment in entity.get("fragments", [])}
        if fragment_paths and (entity["path"] in selected_paths or fragment_paths.intersection(selected_paths)):
            selected_paths.update(fragment_paths)
    csharp_project_files = tracked_csharp_project_files(repository)
    selected_has_csharp = any(item["language"] == "csharp" and item["path"] in selected_paths for item in all_files)
    if not selected_has_csharp and (csharp_solution or csharp_project or allow_dotnet_restore):
        raise CkbError("C# workspace/restore options were supplied, but the selected scan scope has no C# source")
    csharp_workspace = None
    if selected_has_csharp:
        csharp_workspace = _resolve_csharp_workspace(repository, csharp_project_files, csharp_solution, csharp_project)
        if csharp_workspace["precision"] == "exact":
            csharp_workspace["workspace_root"] = source_snapshot["root"]
        if csharp_workspace["precision"] == "bounded-approximate":
            csharp_workspace = _prepare_csharp_fallback_workspace(
                output,
                repository,
                csharp_workspace,
                [item["path"] for item in all_files if item["language"] == "csharp" and item["path"] in selected_paths],
            )
        if allow_dotnet_restore:
            csharp_workspace = _prepare_csharp_restore(output, repository, csharp_workspace)
    selected_entities = [entity for entity in all_entities if entity["path"] in selected_paths]
    selected_ids = {entity["id"] for entity in selected_entities}
    boundary_ids: set[str] = set()
    boundary_links: list[dict[str, Any]] = []
    for link in all_links:
        if link["type"] != "references":
            continue
        if link["source"] in selected_ids and link["target"] not in selected_ids:
            boundary_ids.add(link["target"])
            boundary_links.append(link)
        elif link["target"] in selected_ids and link["source"] not in selected_ids and expand_direction in {"both", "callers"}:
            boundary_ids.add(link["source"])
            boundary_links.append(link)
    boundary_entities = []
    for entity_id in sorted(boundary_ids):
        entity = dict(entity_by_id[entity_id])
        entity["kind_original"] = entity["kind"]
        entity["kind"] = "boundary"
        entity["candidate_classification"] = "boundary"
        entity["classification_evidence"] = ["one-hop-outside-selected-scope"]
        boundary_entities.append(entity)
    selected_entities.extend(boundary_entities)
    navigation_links = [
        link
        for link in [*all_links, *boundary_links]
        if link.get("source") in {entity["id"] for entity in selected_entities}
        and link.get("target") in {entity["id"] for entity in selected_entities}
    ]
    navigation_plan = build_navigation_plan(selected_entities, navigation_links, entry_ids, page_config)
    if navigation_plan["status"] != "passed":
        raise AuditError(f"deterministic navigation quotas failed: {navigation_plan['quota_errors']}")
    selected_entities = apply_navigation_plan(selected_entities, navigation_plan)
    selected_entity_by_id = {entity["id"]: entity for entity in selected_entities}
    all_entities = [selected_entity_by_id.get(entity["id"], entity) for entity in all_entities]
    boundary_entities = [selected_entity_by_id[entity["id"]] for entity in boundary_entities]
    selected_files = [item for item in all_files if item["path"] in selected_paths]
    chunks = _chunks(selected_files, selected_entities)
    if not chunks:
        raise CkbError("selected scope has no supported source")
    for boundary in boundary_entities:
        owner_link = next((link for link in boundary_links if link["target"] == boundary["id"] or link["source"] == boundary["id"]), None)
        peer_id = owner_link["source"] if owner_link and owner_link["target"] == boundary["id"] else (owner_link["target"] if owner_link else None)
        owner_chunk = next((chunk for chunk in chunks if peer_id in chunk["entity_ids"]), chunks[0])
        owner_chunk["entity_ids"].append(boundary["id"])
        owner_chunk.setdefault("boundary_entity_ids", []).append(boundary["id"])
    entity_chunk = {entity_id: chunk["id"] for chunk in chunks for entity_id in chunk["entity_ids"]}
    for entity in selected_entities:
        entity["chunk_id"] = entity_chunk[entity["id"]]
        entity["parse_batch_id"] = entity_chunk[entity["id"]]
    for link in all_links:
        if link["source"] in entity_chunk and link["target"] in entity_chunk:
            link["cross_chunk"] = entity_chunk[link["source"]] != entity_chunk[link["target"]]
    catalog = {
        "schema_version": SCHEMA_VERSION,
        "repository": repository,
        "source_snapshot": source_snapshot,
        "files": file_results,
        "entities": all_entities,
        "links": all_links,
        "csharp_project_files": csharp_project_files,
        "csharp_workspace": csharp_workspace,
        "page_config": page_config_record,
        "migration_reuse": {
            "origin": reuse_origin,
            "reused_file_paths": sorted(reused_paths),
            "reused_file_count": len(reused_paths),
            "rekeyed_entity_count": reused_entity_count,
            "parsed_file_count": len(all_files) - len(reused_paths),
        }
        if reuse_origin
        else None,
    }
    scope = {
        "repository": repository,
        "source_snapshot": source_snapshot,
        "format": format_name,
        "selectors": {
            "scope_paths": scope_paths,
            "entries": entries,
            "entry_ids": entry_ids,
            "expand_depth": expand_depth,
            "expand_direction": expand_direction,
            "include": includes,
            "csharp_solution": csharp_solution,
            "csharp_project": csharp_project,
            "allow_dotnet_restore": allow_dotnet_restore,
        },
        "csharp_workspace": csharp_workspace,
        "page_config": page_config_record,
        "selected_file_paths": sorted(selected_paths),
        "selected_entity_ids": sorted(entity["id"] for entity in selected_entities),
        "boundary_entity_ids": sorted(boundary_ids),
        "excluded": exclusions,
    }
    review_packs = build_review_packs(chunks, selected_entities, page_config)
    _write_review_pack_templates(output, review_packs, selected_entities, sources)
    state = {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "created_at_utc": utc_now(),
        "repository": repository,
        "source_snapshot": source_snapshot,
        "format": format_name,
        "semantic_precision": "bounded-approximate" if csharp_workspace and csharp_workspace.get("precision") == "bounded-approximate" else "exact",
        "status": "initialized",
        "parse_batches": chunks,
        "chunks": chunks,
        "review_packs": review_packs,
        "navigation_algorithm": navigation_plan["algorithm"],
        "csharp_workspace": csharp_workspace,
        "page_config": page_config_record,
    }
    json_write(output / "catalog.json", catalog)
    json_write(output / "scope.json", scope)
    json_write(output / "boundary.json", {"entities": boundary_entities, "links": boundary_links})
    json_write(output / "navigation-plan.json", navigation_plan)
    json_write(output / "state.json", state)
    write_marker(output, ".pending-agent-review", {"status": "initialized", "next_chunk": chunks[0]["id"]})
    return state


def _selected_catalog(output: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    key = str(output.resolve())
    if key not in _CATALOG_CACHE:
        _CATALOG_CACHE[key] = (
            json_load(output / "catalog.json"),
            json_load(output / "scope.json"),
            json_load(output / "boundary.json"),
        )
    return _CATALOG_CACHE[key]


def _chunk(state: dict[str, Any], chunk_id: str) -> dict[str, Any]:
    found = next((item for item in state["chunks"] if item["id"] == chunk_id), None)
    if not found:
        raise CkbError(f"unknown chunk: {chunk_id}")
    return found


def _review_pack(state: dict[str, Any], pack_id: str) -> dict[str, Any]:
    found = next((item for item in state.get("review_packs", []) if item["id"] == pack_id), None)
    if not found:
        raise CkbError(f"unknown review pack: {pack_id}")
    return found


def _invalidate_after_build(output: Path, chunk: dict[str, Any], state: dict[str, Any]) -> None:
    clear_markers(output)
    for path in (output / "graph.json", output / "audit" / "global.json"):
        path.unlink(missing_ok=True)
    for pack in state.get("review_packs", []):
        if chunk["id"] not in pack.get("parse_batch_ids", []):
            continue
        pack["status"] = "planned"
        pack.pop("review_path", None)
        pack.pop("audit_path", None)
        for path in (output / "review-packs" / pack["id"] / "agent-review.json", output / "review-packs" / pack["id"] / "audit.json"):
            path.unlink(missing_ok=True)
    chunk["status"] = "building"


def build_chunk(output: Path, chunk_id: str, stage: str = "all") -> dict[str, Any]:
    state = _load_state(output)
    chunk = _chunk(state, chunk_id)
    _invalidate_after_build(output, chunk, state)
    catalog, scope, boundary_doc = _selected_catalog(output)
    selected_ids = set(scope["selected_entity_ids"])
    entity_by_id = {entity["id"]: dict(entity) for entity in catalog["entities"] if entity["id"] in selected_ids}
    for boundary in boundary_doc["entities"]:
        entity_by_id[boundary["id"]] = dict(boundary)
    entities = [entity_by_id[value] for value in chunk["entity_ids"]]
    file_by_path = {item["file"]["path"]: item["file"] for item in catalog["files"]}
    files = [file_by_path[path] for path in chunk["file_paths"]]
    if stage == "syntax":
        parse_by_path = {item["file"]["path"]: item["parse"] for item in catalog["files"]}
        syntax_result = {
            "schema_version": SCHEMA_VERSION,
            "chunk_id": chunk_id,
            "stage": "syntax",
            "status": "passed" if all(parse_by_path[path]["status"] == "passed" for path in chunk["file_paths"]) else "failed",
            "file_paths": chunk["file_paths"],
            "entity_ids": chunk["entity_ids"],
            "parse_results": {path: parse_by_path[path] for path in chunk["file_paths"]},
            "built_at_utc": utc_now(),
        }
        chunk_dir = output / "chunks" / chunk_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        json_write(chunk_dir / "syntax.json", syntax_result)
        chunk["status"] = "syntax-built" if syntax_result["status"] == "passed" else "failed"
        state["status"] = "in-progress" if syntax_result["status"] == "passed" else "failed"
        json_write(output / "state.json", state)
        write_marker(
            output,
            ".pending-agent-review" if syntax_result["status"] == "passed" else ".failed",
            {"status": chunk["status"], "chunk_id": chunk_id, "next_stage": "semantics"},
        )
        if syntax_result["status"] != "passed":
            raise AuditError(f"syntax stage failed: {chunk_dir / 'syntax.json'}")
        return syntax_result
    links = [
        dict(link)
        for link in catalog["links"]
        if link["source"] in selected_ids and link["target"] in selected_ids
        and (link["source"] in chunk["entity_ids"] or link["target"] in chunk["entity_ids"])
    ]
    boundary_ids = set(scope["boundary_entity_ids"])
    links.extend(
        {**link, "cross_chunk": True, "boundary": True}
        for link in boundary_doc["links"]
        if (link["source"] in chunk["entity_ids"] or link["target"] in chunk["entity_ids"])
        and (link["source"] in boundary_ids or link["target"] in boundary_ids)
    )
    all_entity_by_id = {**entity_by_id}
    for entity in catalog["entities"]:
        all_entity_by_id.setdefault(entity["id"], entity)
    provider_results: list[dict[str, Any]] = []
    semantic_links: list[dict[str, Any]] = []
    if stage in {"semantics", "all"}:
        for language in sorted({file_entry["language"] for file_entry in files}):
            language_files = [item for item in files if item["language"] == language]
            language_entities = [item for item in entities if item["language"] == language and item["kind"] != "boundary"]
            result = collect_semantics(
                Path(state.get("source_snapshot", {}).get("root") or state["repository"]["root"]),
                language,
                language_files,
                language_entities,
                {"csharp_workspace": state.get("csharp_workspace")},
            )
            provider_results.append(result["provider"])
            semantic_links.extend(result["links"])
            semantic_path = output / "chunks" / chunk_id / f"semantic-{language}.json"
            json_write(semantic_path, result)
            if result["provider"].get("precision") == "bounded-approximate":
                state["semantic_precision"] = "bounded-approximate"
    else:
        existing = sorted((output / "chunks" / chunk_id).glob("semantic-*.json"))
        if not existing:
            raise CkbError("semantic stage has not been built")
        for path in existing:
            result = json_load(path)
            provider_results.append(result["provider"])
            semantic_links.extend(result["links"])
    seen_links = {link["id"] for link in links}
    for link in semantic_links:
        if link["id"] not in seen_links:
            links.append({**link, "cross_chunk": False})
            seen_links.add(link["id"])
    chunk_dir = output / "chunks" / chunk_id
    chunk_dir.mkdir(parents=True, exist_ok=True)
    candidate = {
        "schema_version": SCHEMA_VERSION,
        "chunk_id": chunk_id,
        "repository": state["repository"],
        "files": files,
        "entities": entities,
        "links": links,
        "providers": provider_results,
        "built_at_utc": utc_now(),
    }
    json_write(chunk_dir / "candidate.json", candidate)
    template = {
        "schema_version": SCHEMA_VERSION,
        "chunk_id": chunk_id,
        "reviewed_at_utc": None,
        "reviewer": "Agent",
        "reviews": [
            {
                "entity_id": entity["id"],
                "classification": entity["classification"],
                "owner_page_id": entity["owner_page_id"],
                "source_path": entity["path"],
                "start_line": entity["range"]["start_line"],
                "end_line": entity["range"]["end_line"],
                "meaning_zh": "" if entity["classification"] != "appendix" else None,
                "role_zh": "" if entity["classification"] != "appendix" else None,
                "change_when_zh": "" if entity["classification"] != "appendix" else None,
                "description_zh": "" if entity["classification"] == "appendix" else None,
                "evidence_note": "",
                "status": "draft",
            }
            for entity in entities
        ],
    }
    json_write(chunk_dir / "review-template.json", template)
    chunk["status"] = "awaiting-agent-review"
    chunk["candidate_path"] = str((chunk_dir / "candidate.json").resolve())
    chunk["review_template_path"] = str((chunk_dir / "review-template.json").resolve())
    state["status"] = "awaiting-agent-review"
    json_write(output / "state.json", state)
    write_marker(output, ".pending-agent-review", {"status": "awaiting-agent-review", "chunk_id": chunk_id, "review_template": chunk["review_template_path"]})
    return candidate


def _substantive_chinese(value: Any) -> bool:
    if not isinstance(value, str) or len(value.strip()) < 8:
        return False
    if not re.search(r"[\u3400-\u9fff]", value):
        return False
    lowered = value.lower()
    return not any(token in lowered for token in ("todo", "placeholder", "待填写", "草稿"))


def _single_chinese_sentence(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if len(text) < 4 or len(text) > 80 or not re.search(r"[\u3400-\u9fff]", text):
        return False
    if any(token in text.lower() for token in ("todo", "placeholder", "待填写", "草稿", "相关逻辑", "相关操作")):
        return False
    # Exactly one terminal sentence; internal punctuation is allowed.
    return len(re.findall(r"[。！？!?]", text)) == 1 and bool(re.search(r"[。！？!?]$", text))


def _source_check(entity: dict[str, Any], source: bytes | None, expected_blob: str | None) -> str | None:
    if source is None:
        return "blob-object-missing"
    if expected_blob != entity["blob"]:
        return "entity-blob-does-not-match-source-manifest"
    start = int(entity["range"]["start_byte"])
    end = int(entity["range"]["end_byte"])
    if start < 0 or end > len(source) or start > end:
        return "source-range-out-of-bounds"
    if entity["kind"] != "file" and entity["name"].encode("utf-8") not in source[start:end]:
        return "entity-name-not-in-source-range"
    return None


def _partial_fragment_source_errors(entity: dict[str, Any], sources: dict[str, bytes], file_by_path: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for fragment in entity.get("fragments", []):
        source = sources.get(fragment["path"])
        manifest = file_by_path.get(fragment["path"])
        start = int(fragment["range"]["start_byte"])
        end = int(fragment["range"]["end_byte"])
        reason = None
        if source is None or manifest is None:
            reason = "partial-fragment-blob-missing"
        elif manifest.get("blob") != fragment.get("blob"):
            reason = "partial-fragment-blob-mismatch"
        elif start < 0 or end > len(source) or start > end:
            reason = "partial-fragment-range-out-of-bounds"
        elif entity["name"].encode("utf-8") not in source[start:end]:
            reason = "partial-fragment-name-not-in-range"
        if reason:
            errors.append({"id": entity["id"], "fragment": fragment, "reason": reason})
    return errors


def audit_chunk(output: Path, chunk_id: str) -> dict[str, Any]:
    state = _load_state(output)
    (output / ".complete").unlink(missing_ok=True)
    if state.get("status") == "complete":
        state["status"] = "in-progress"
        json_write(output / "state.json", state)
    chunk = _chunk(state, chunk_id)
    chunk_dir = output / "chunks" / chunk_id
    candidate_path = chunk_dir / "candidate.json"
    review_path = chunk_dir / "agent-review.json"
    if not candidate_path.is_file():
        raise AuditError("candidate.json is missing")
    candidate = json_load(candidate_path)
    review = json_load(review_path) if review_path.is_file() else {"reviews": []}
    entities = candidate["entities"]
    entity_by_id = {entity["id"]: entity for entity in entities}
    review_by_id = {item.get("entity_id"): item for item in review.get("reviews", []) if isinstance(item, dict)}
    gates: dict[str, dict[str, Any]] = {}

    def gate(name: str, checks: list[dict[str, Any]]) -> None:
        gates[name] = {"status": "passed" if all(item["passed"] for item in checks) else "failed", "checks": checks}

    scope_ids = set(chunk["entity_ids"])
    gate("scope", [{"name": "chunk-entity-set-exact", "passed": set(entity_by_id) == scope_ids, "detail": {"missing": sorted(scope_ids - set(entity_by_id)), "extra": sorted(set(entity_by_id) - scope_ids)}}])
    catalog, _scope_doc, _boundary_doc = _selected_catalog(output)
    parse_by_path = {item["file"]["path"]: item["parse"] for item in catalog["files"]}
    gate("syntax", [{"name": "all-files-parse", "passed": all(parse_by_path[path]["status"] == "passed" for path in chunk["file_paths"]), "detail": {path: parse_by_path[path] for path in chunk["file_paths"] if parse_by_path[path]["status"] != "passed"}}, {"name": "entity-ids-unique", "passed": len(entity_by_id) == len(entities), "detail": len(entities)}])
    classification_errors = []
    navigation_plan = json_load(output / "navigation-plan.json")
    planned_by_id = {item["entity_id"]: item for item in navigation_plan["decisions"]}
    global_page_ids = set(navigation_plan["page_entity_ids"]) | set(navigation_plan["boundary_entity_ids"])
    for entity in entities:
        item = review_by_id.get(entity["id"], {})
        classification = item.get("classification")
        owner = item.get("owner_page_id")
        planned = planned_by_id.get(entity["id"])
        if classification not in ALLOWED_CLASSIFICATIONS:
            classification_errors.append({"id": entity["id"], "reason": "invalid-classification"})
        elif not planned or classification != planned["classification"]:
            classification_errors.append({"id": entity["id"], "reason": "classification-differs-from-deterministic-plan", "planned": planned})
        elif owner != planned["owner_page_id"]:
            classification_errors.append({"id": entity["id"], "reason": "owner-differs-from-deterministic-plan", "planned_owner": planned["owner_page_id"], "actual_owner": owner})
        elif entity["kind"] == "file" and classification != "page":
            classification_errors.append({"id": entity["id"], "reason": "file-not-page"})
        elif entity["kind"] == "boundary" and classification != "boundary":
            classification_errors.append({"id": entity["id"], "reason": "boundary-mismatch"})
        elif classification == "appendix" and owner not in global_page_ids:
            classification_errors.append({"id": entity["id"], "reason": "appendix-owner-not-page", "owner": owner})
    gate("classification", [{"name": "classification-and-owner-valid", "passed": not classification_errors, "detail": classification_errors}])
    provider_errors = []
    covered: set[str] = set()
    for provider in candidate.get("providers", []):
        if provider.get("status") != "passed":
            provider_errors.append(provider)
        covered.update(provider.get("covered_entity_ids", []))
    key_ids = {entity["id"] for entity in entities if entity["kind"] != "boundary" and review_by_id.get(entity["id"], {}).get("classification") == "page" and entity["kind"] != "file"}
    if os.environ.get("CKB_TEST_PROVIDER") != "deterministic-fixture":
        missing_key = sorted(key_ids - covered)
    else:
        missing_key = []
    gate("semantics", [{"name": "providers-passed", "passed": not provider_errors, "detail": provider_errors}, {"name": "key-entity-coverage", "passed": not missing_key, "detail": missing_key}])
    file_by_path = {item["file"]["path"]: item["file"] for item in catalog["files"]}
    audit_paths = {entity["path"] for entity in entities}
    audit_paths.update(fragment["path"] for entity in entities for fragment in entity.get("fragments", []))
    audit_files = [file_by_path[path] for path in sorted(audit_paths)]
    audit_sources = blob_bytes_many(state["repository"], audit_files)
    source_errors = [
        {"id": entity["id"], "reason": reason}
        for entity in entities
        if (reason := _source_check(entity, audit_sources.get(entity["path"]), file_by_path.get(entity["path"], {}).get("blob")))
    ]
    source_errors.extend(error for entity in entities for error in _partial_fragment_source_errors(entity, audit_sources, file_by_path))
    gate("source", [{"name": "git-source-authentic", "passed": not source_errors, "detail": source_errors}])
    description_errors = []
    if set(review_by_id) != set(entity_by_id):
        description_errors.append({"reason": "review-entity-set-mismatch", "missing": sorted(set(entity_by_id) - set(review_by_id)), "extra": sorted(set(review_by_id) - set(entity_by_id))})
    for entity_id, item in review_by_id.items():
        entity = entity_by_id.get(entity_id)
        if not entity:
            continue
        if item.get("status") != "agent-reviewed":
            description_errors.append({"id": entity_id, "reason": "status-not-agent-reviewed"})
        if item.get("classification") == "appendix":
            if not _single_chinese_sentence(item.get("description_zh")):
                description_errors.append({"id": entity_id, "reason": "description_zh-not-one-useful-sentence"})
            if not _substantive_chinese(item.get("evidence_note")):
                description_errors.append({"id": entity_id, "reason": "evidence_note-not-substantive"})
        else:
            for field in ("meaning_zh", "role_zh", "change_when_zh", "evidence_note"):
                if not _substantive_chinese(item.get(field)):
                    description_errors.append({"id": entity_id, "reason": f"{field}-not-substantive"})
        if item.get("source_path") != entity["path"] or item.get("start_line") != entity["range"]["start_line"] or item.get("end_line") != entity["range"]["end_line"]:
            description_errors.append({"id": entity_id, "reason": "source-basis-mismatch"})
    gate("descriptions", [{"name": "pages-and-appendix-sentences-agent-reviewed", "passed": not description_errors, "detail": description_errors}])
    scope = _scope_doc
    global_ids = set(scope["selected_entity_ids"])
    link_errors = []
    for link in candidate.get("links", []):
        if link["source"] not in global_ids or link["target"] not in global_ids:
            link_errors.append({"id": link["id"], "reason": "endpoint-outside-selected-or-boundary"})
    gate("links", [{"name": "link-endpoints-valid", "passed": not link_errors, "detail": link_errors}])
    status = "passed" if all(item["status"] == "passed" for item in gates.values()) else "failed"
    result = {"schema_version": SCHEMA_VERSION, "chunk_id": chunk_id, "status": status, "gates": gates, "audited_at_utc": utc_now()}
    json_write(chunk_dir / "audit.json", result)
    write_marker(
        output,
        ".pending-agent-review" if status == "passed" else ".failed",
        {"status": "audit-passed-finalize-required" if status == "passed" else "failed", "chunk_id": chunk_id, "audit": str((chunk_dir / "audit.json").resolve())},
    )
    return result


def review_chunk(output: Path, chunk_id: str, review_file: Path) -> dict[str, Any]:
    state = _load_state(output)
    chunk = _chunk(state, chunk_id)
    candidate_path = output / "chunks" / chunk_id / "candidate.json"
    if not candidate_path.is_file():
        raise CkbError("build the chunk before submitting a review")
    review = json_load(review_file)
    review["reviewed_at_utc"] = review.get("reviewed_at_utc") or utc_now()
    review["chunk_id"] = chunk_id
    destination = output / "chunks" / chunk_id / "agent-review.json"
    json_write(destination, review)
    audit = audit_chunk(output, chunk_id)
    if audit["status"] != "passed":
        chunk["status"] = "failed"
        state["status"] = "failed"
        json_write(output / "state.json", state)
        write_marker(output, ".failed", {"status": "failed", "chunk_id": chunk_id, "audit": str((output / "chunks" / chunk_id / "audit.json").resolve())})
        raise AuditError(f"chunk review failed: {output / 'chunks' / chunk_id / 'audit.json'}")
    candidate = json_load(candidate_path)
    review_by_id = {item["entity_id"]: item for item in review["reviews"]}
    for entity in candidate["entities"]:
        item = review_by_id[entity["id"]]
        entity["classification"] = item["classification"]
        entity["owner_page_id"] = item["owner_page_id"]
        if item["classification"] == "appendix":
            entity["description_zh"] = item["description_zh"]
        else:
            entity["meaning_zh"] = item["meaning_zh"]
            entity["role_zh"] = item["role_zh"]
            entity["change_when_zh"] = item["change_when_zh"]
        entity["evidence_note"] = item["evidence_note"]
        entity["review_status"] = "agent-reviewed"
    json_write(candidate_path, candidate)
    chunk["status"] = "passed"
    chunk["review_path"] = str(destination.resolve())
    chunk["audit_path"] = str((output / "chunks" / chunk_id / "audit.json").resolve())
    state["status"] = "in-progress"
    review_items = {item["entity_id"]: item for item in review["reviews"]}
    for pack in state.get("review_packs", []):
        if chunk_id not in pack.get("parse_batch_ids", []):
            continue
        subset = [review_items[value] for value in pack["entity_ids"] if value in review_items]
        if len(subset) != len(pack["entity_ids"]):
            continue
        pack_dir = output / "review-packs" / pack["id"]
        pack_dir.mkdir(parents=True, exist_ok=True)
        json_write(pack_dir / "agent-review.json", {"schema_version": SCHEMA_VERSION, "pack_id": pack["id"], "kind": pack["kind"], "reviewer": review.get("reviewer", "Agent"), "reviewed_at_utc": review["reviewed_at_utc"], "reviews": subset})
        json_write(pack_dir / "audit.json", {"schema_version": SCHEMA_VERSION, "pack_id": pack["id"], "status": "passed", "basis": "legacy-combined-batch-review", "audited_at_utc": utc_now()})
        pack["status"] = "passed"
        pack["review_path"] = str((pack_dir / "agent-review.json").resolve())
        pack["audit_path"] = str((pack_dir / "audit.json").resolve())
    json_write(output / "state.json", state)
    next_chunk = next((item for item in state["chunks"] if item["status"] != "passed"), None)
    if next_chunk:
        write_marker(output, ".pending-agent-review", {"status": "next-chunk", "next_chunk": next_chunk["id"]})
    else:
        write_marker(output, ".pending-agent-review", {"status": "ready-to-merge"})
    return audit


def review_pack(output: Path, pack_id: str, review_file: Path) -> dict[str, Any]:
    """Validate one page/appendix Agent review unit independently of parsing."""
    state = _load_state(output)
    pack = _review_pack(state, pack_id)
    required_batches = [_chunk(state, value) for value in pack["parse_batch_ids"]]
    if any(not (output / "chunks" / batch["id"] / "candidate.json").is_file() for batch in required_batches):
        raise CkbError("build every parse batch referenced by the review pack before submitting it")
    review = json_load(review_file)
    items = [item for item in review.get("reviews", []) if isinstance(item, dict)]
    by_id = {item.get("entity_id"): item for item in items}
    catalog, scope_doc, boundary_doc = _selected_catalog(output)
    entity_by_id = {entity["id"]: entity for entity in catalog["entities"]}
    entity_by_id.update({entity["id"]: entity for entity in boundary_doc.get("entities", [])})
    planned = {item["entity_id"]: item for item in json_load(output / "navigation-plan.json")["decisions"]}
    errors: list[dict[str, Any]] = []
    expected_ids = set(pack["entity_ids"])
    if set(by_id) != expected_ids:
        errors.append({"reason": "review-pack-entity-set-mismatch", "missing": sorted(expected_ids - set(by_id)), "extra": sorted(set(by_id) - expected_ids)})
    file_by_path = {item["file"]["path"]: item["file"] for item in catalog["files"]}
    files = [file_by_path[path] for path in sorted({entity_by_id[value]["path"] for value in expected_ids if value in entity_by_id})]
    sources = blob_bytes_many(state["repository"], files)
    for entity_id in sorted(expected_ids & set(by_id)):
        item = by_id[entity_id]
        entity = entity_by_id[entity_id]
        decision = planned[entity_id]
        if item.get("status") != "agent-reviewed":
            errors.append({"id": entity_id, "reason": "status-not-agent-reviewed"})
        if item.get("classification") != decision["classification"] or item.get("owner_page_id") != decision["owner_page_id"]:
            errors.append({"id": entity_id, "reason": "deterministic-classification-or-owner-changed"})
        if item.get("source_path") != entity["path"] or item.get("start_line") != entity["range"]["start_line"] or item.get("end_line") != entity["range"]["end_line"]:
            errors.append({"id": entity_id, "reason": "source-basis-mismatch"})
        reason = _source_check(entity, sources.get(entity["path"]), file_by_path.get(entity["path"], {}).get("blob"))
        if reason:
            errors.append({"id": entity_id, "reason": reason})
        if pack["kind"] == "appendix-review":
            if not _single_chinese_sentence(item.get("description_zh")):
                errors.append({"id": entity_id, "reason": "description_zh-not-one-useful-sentence"})
        else:
            for field in ("meaning_zh", "role_zh", "change_when_zh"):
                if not _substantive_chinese(item.get(field)):
                    errors.append({"id": entity_id, "reason": f"{field}-not-substantive"})
        if not _substantive_chinese(item.get("evidence_note")):
            errors.append({"id": entity_id, "reason": "evidence_note-not-substantive"})
    status_value = "passed" if not errors else "failed"
    pack_dir = output / "review-packs" / pack_id
    destination = pack_dir / "agent-review.json"
    review["pack_id"] = pack_id
    review["kind"] = pack["kind"]
    review["reviewed_at_utc"] = review.get("reviewed_at_utc") or utc_now()
    json_write(destination, review)
    audit = {"schema_version": SCHEMA_VERSION, "pack_id": pack_id, "kind": pack["kind"], "status": status_value, "errors": errors, "audited_at_utc": utc_now()}
    json_write(pack_dir / "audit.json", audit)
    pack["status"] = status_value
    pack["review_path"] = str(destination.resolve())
    pack["audit_path"] = str((pack_dir / "audit.json").resolve())
    state["status"] = "in-progress" if status_value == "passed" else "failed"
    json_write(output / "state.json", state)
    if errors:
        write_marker(output, ".failed", {"status": "failed", "review_pack": pack_id, "audit": pack["audit_path"]})
        raise AuditError(f"review pack failed: {pack_dir / 'audit.json'}")

    # When all review packs for a parse batch pass, materialize the combined
    # review expected by the existing deterministic batch audit and close it.
    state = _load_state(output)
    for batch in required_batches:
        batch_packs = [value for value in state["review_packs"] if batch["id"] in value.get("parse_batch_ids", [])]
        if not batch_packs or any(value["status"] != "passed" for value in batch_packs):
            continue
        combined_items: list[dict[str, Any]] = []
        for value in batch_packs:
            combined_items.extend(json_load(output / "review-packs" / value["id"] / "agent-review.json")["reviews"])
        combined = {"schema_version": SCHEMA_VERSION, "chunk_id": batch["id"], "reviewer": "Agent", "reviewed_at_utc": utc_now(), "reviews": combined_items}
        json_write(output / "chunks" / batch["id"] / "agent-review.json", combined)
        batch_audit = audit_chunk(output, batch["id"])
        if batch_audit["status"] != "passed":
            raise AuditError(f"parse batch audit failed after review packs: {batch['id']}")
        candidate_path = output / "chunks" / batch["id"] / "candidate.json"
        candidate = json_load(candidate_path)
        combined_by_id = {item["entity_id"]: item for item in combined_items}
        for entity in candidate["entities"]:
            item = combined_by_id[entity["id"]]
            entity["classification"] = item["classification"]
            entity["owner_page_id"] = item["owner_page_id"]
            if item["classification"] == "appendix":
                entity["description_zh"] = item["description_zh"]
            else:
                entity["meaning_zh"] = item["meaning_zh"]
                entity["role_zh"] = item["role_zh"]
                entity["change_when_zh"] = item["change_when_zh"]
            entity["evidence_note"] = item["evidence_note"]
            entity["review_status"] = "agent-reviewed"
        json_write(candidate_path, candidate)
        refreshed = _load_state(output)
        refreshed_batch = _chunk(refreshed, batch["id"])
        refreshed_batch["status"] = "passed"
        refreshed["status"] = "in-progress"
        json_write(output / "state.json", refreshed)
    state = _load_state(output)
    remaining = next((value for value in state["review_packs"] if value["status"] != "passed"), None)
    if remaining:
        write_marker(output, ".pending-agent-review", {"status": "next-review-pack", "next_review_pack": remaining["id"], "review_template": remaining.get("review_template_path")})
    else:
        write_marker(output, ".pending-agent-review", {"status": "ready-to-merge"})
    return audit


def merge(output: Path) -> dict[str, Any]:
    state = _load_state(output)
    page_config = normalize_page_config(json_load(output / state["page_config"]["relative_path"]))
    incomplete = [chunk["id"] for chunk in state["chunks"] if chunk["status"] != "passed"]
    if incomplete:
        raise ReviewRequired(f"chunks still require build/review: {incomplete}")
    incomplete_packs = [pack["id"] for pack in state.get("review_packs", []) if pack["status"] != "passed"]
    if incomplete_packs:
        raise ReviewRequired(f"review packs still require Agent review: {incomplete_packs}")
    entities: list[dict[str, Any]] = []
    links_by_id: dict[str, dict[str, Any]] = {}
    providers: list[dict[str, Any]] = []
    for chunk in state["chunks"]:
        candidate = json_load(output / "chunks" / chunk["id"] / "candidate.json")
        entities.extend(candidate["entities"])
        for link in candidate["links"]:
            links_by_id[link["id"]] = link
        providers.extend(candidate["providers"])
    if len({entity["id"] for entity in entities}) != len(entities):
        raise AuditError("duplicate entity IDs across chunks")
    entity_ids = {entity["id"] for entity in entities}
    dangling = [link for link in links_by_id.values() if link["source"] not in entity_ids or link["target"] not in entity_ids]
    if dangling:
        raise AuditError(f"dangling links after merge: {[item['id'] for item in dangling[:20]]}")
    graph = {
        "schema_version": SCHEMA_VERSION,
        "repository": state["repository"],
        "scope": json_load(output / "scope.json"),
        "format": state["format"],
        "semantic_precision": state["semantic_precision"],
        "entities": sorted(entities, key=lambda item: item["id"]),
        "links": sorted(links_by_id.values(), key=lambda item: item["id"]),
        "providers": providers,
        "navigation_plan": json_load(output / "navigation-plan.json"),
        "page_config": page_config,
        "page_config_sha256": page_config_sha256(page_config),
        "review_packs": state.get("review_packs", []),
        "merged_at_utc": utc_now(),
    }
    json_write(output / "graph.json", graph)
    state["status"] = "merged"
    json_write(output / "state.json", state)
    return graph


HUMAN_TITLE_PREFIXES = ("实体 ·", "文件 ·", "模块 ·", "仓库 ·", "边界 ·")
HUMAN_VISIBLE_FORBIDDEN = (
    "Git commit",
    "仓库 commit",
    "Graphify commit",
    "Git：",
    "CKB 页面 ID",
    "CKB 实体 ID",
    "CKB 关系 ID",
    "CKB 附属实体",
    "CKB 边界实体",
    "条机器关系",
    "EXTRACTED",
    "INFERRED",
    "AMBIGUOUS",
)


def _repository_name(root: str) -> str:
    return PurePosixPath(str(root).replace("\\", "/")).name or "代码项目"


def _short_code_unit_name(entity: dict[str, Any], entity_by_id: dict[str, dict[str, Any]]) -> str:
    """Return a source-recognizable class/function title without namespace noise."""
    name = str(entity.get("name") or entity.get("qualified_name") or "未命名代码单元")
    parent = entity_by_id.get(entity.get("parent_id"))
    if parent and parent.get("kind") in {"class", "struct", "interface", "record"}:
        return f"{parent.get('name', parent.get('qualified_name'))}.{name}"
    return name


def _source_role(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    if any(part.lower() in {"test", "tests"} for part in PurePosixPath(path).parts) or re.search(
        r"(?:^|[_-])test$|\.test$", PurePosixPath(path).stem, flags=re.IGNORECASE
    ):
        return "测试"
    if suffix in {".h", ".hh", ".hpp", ".hxx"}:
        return "接口"
    return "实现"


def _human_page_base_title(
    page: dict[str, Any],
    entities: list[dict[str, Any]],
    entity_by_id: dict[str, dict[str, Any]],
    repository_name: str,
) -> str:
    if page["page_type"] == "entity":
        return _short_code_unit_name(page["entity"], entity_by_id)
    if page["page_type"] == "file":
        source = page["entity"]
        units = [
            value
            for value in entities
            if value["path"] == source["path"] and value.get("kind") in HUMAN_CODE_UNIT_KINDS
        ]
        units.sort(
            key=lambda value: (
                0 if value.get("classification") == "page" else 1,
                int(value["range"]["start_line"]),
                value["id"],
            )
        )
        unit_names: list[str] = []
        for value in units:
            display = _short_code_unit_name(value, entity_by_id)
            if display not in unit_names:
                unit_names.append(display)
            if len(unit_names) == 2:
                break
        if _source_role(source["path"]) == "测试":
            lead = unit_names[0] if unit_names else PurePosixPath(source["path"]).stem
            return f"{lead} 等测试场景"
        if len(unit_names) == 1:
            return f"{unit_names[0]} 相关实现"
        if unit_names:
            return f"{unit_names[0]} 与 {unit_names[1]} 的协作实现"
        return f"{PurePosixPath(source['path']).stem} 实现概览"
    if page["page_type"] == "repository":
        return f"{repository_name} 代码导览"
    if page["page_type"] == "module":
        return "项目入口与根目录" if page.get("module") == "root" else f"{page['module']} 职责导览"
    boundary_path = page["boundary_entities"][0]["path"] if page.get("boundary_entities") else page.get("module", "范围外代码")
    return f"{PurePosixPath(boundary_path).stem} 的协作边界"


def _assign_human_titles(pages: dict[str, dict[str, Any]], entities: list[dict[str, Any]], repository_name: str) -> None:
    """Assign short prefix-free titles and deterministic natural disambiguators."""
    entity_by_id = {entity["id"]: entity for entity in entities}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages.values():
        base = _human_page_base_title(page, entities, entity_by_id, repository_name).strip()
        if len(base) > 84:
            base = base[:83].rstrip() + "…"
        page["title_base"] = base
        groups[base].append(page)
    used: set[str] = set()
    for base, values in sorted(groups.items()):
        for page in sorted(values, key=lambda value: value["id"]):
            title = base
            if len(values) > 1:
                entity = page.get("entity")
                if entity:
                    stem = PurePosixPath(entity["path"]).stem
                    qualifier = f"{stem} {_source_role(entity['path'])}"
                else:
                    qualifier = str(page.get("module") or "相关代码")
                title = f"{base}（{qualifier}）"
            if title in used:
                entity = page.get("entity")
                location = f"{entity['path']}:{entity['range']['start_line']}" if entity else page["id"][-8:]
                title = f"{base}（{location}）"
            if title in used:
                title = f"{title}·{len(used) + 1}"
            page["title"] = title
            used.add(title)


def _logical_projection(graph: dict[str, Any]) -> dict[str, Any]:
    """Project the complete fact graph into a deterministic bounded navigation graph."""
    page_config = normalize_page_config(graph.get("page_config", DEFAULT_PAGE_CONFIG))
    entities = graph["entities"]
    entity_by_id = {entity["id"]: entity for entity in entities}
    pages: dict[str, dict[str, Any]] = {}
    owner_by_entity: dict[str, str] = {}

    def new_page(page_id: str, title: str, page_type: str, entity: dict[str, Any] | None = None, module: str | None = None) -> dict[str, Any]:
        value = {
            "id": page_id,
            "title": title,
            "page_type": page_type,
            "human_page_kind": "code-unit" if page_type == "entity" else "code-unit-aggregate",
            "entity": entity,
            "appendix_entities": [],
            "boundary_entities": [],
            "outgoing": [],
            "backlinks": [],
            "module": module,
            "relation_summary": {},
        }
        pages[page_id] = value
        return value

    # Source pages are selected by the deterministic navigation plan.  Boundary
    # facts are grouped by source path so a large local scan does not create one
    # human page per one-hop endpoint.
    for entity in entities:
        classification = entity["classification"]
        if classification == "page":
            owner_by_entity[entity["id"]] = entity["id"]
            page_type = "file" if entity["kind"] == "file" else "entity"
            new_page(entity["id"], "", page_type, entity)
    boundary_groups: dict[str, str] = {}
    for entity in sorted((value for value in entities if value["classification"] == "boundary"), key=lambda value: (value["path"], value["range"]["start_line"], value["id"])):
        group_id = boundary_groups.setdefault(entity["path"], stable_id("nav", graph["repository"]["commit"], "boundary", entity["path"]))
        if group_id not in pages:
            new_page(group_id, "", "boundary", module=module_name(entity["path"]))
        pages[group_id]["boundary_entities"].append(entity)
        owner_by_entity[entity["id"]] = group_id
    for entity in entities:
        if entity["classification"] == "appendix":
            owner = entity["owner_page_id"]
            if owner not in pages:
                raise AuditError(f"appendix owner has no page: {entity['id']} -> {owner}")
            owner_by_entity[entity["id"]] = owner
            pages[owner]["appendix_entities"].append(entity)

    # Collapse all entity relations between the same page pair and type.  The
    # original link IDs remain in graph.json; only the human navigation view is
    # bounded here.
    relation_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for link in graph["links"]:
        source_page = owner_by_entity[link["source"]]
        target_page = owner_by_entity[link["target"]]
        if source_page == target_page:
            continue
        relation_groups[(source_page, target_page, link["type"])].append(link)
    candidate_links: list[dict[str, Any]] = []
    for (source_page, target_page, relation_type), evidence_links in sorted(relation_groups.items()):
        link_id = stable_id("plink", source_page, target_page, relation_type)
        candidate_links.append(
            {
                "id": link_id,
                "type": relation_type,
                "source": source_page,
                "target": target_page,
                "entity_link_ids": sorted(value["id"] for value in evidence_links),
                "count": len(evidence_links),
            }
        )
    reference_outgoing: dict[str, set[str]] = defaultdict(set)
    for link in graph["links"]:
        if link["type"] == "references":
            reference_outgoing[link["source"]].add(link["target"])
    test_entities = [
        entity
        for entity in entities
        if entity["kind"] != "file"
        and any(part.lower() in {"test", "tests"} for part in PurePosixPath(entity["path"]).parts)
        or (entity["kind"] != "file" and re.search(r"(^test[_-]|[_-]test$)", PurePosixPath(entity["path"]).stem, flags=re.IGNORECASE))
    ]
    for test_entity in test_entities:
        test_page = owner_by_entity[test_entity["id"]]
        frontier = deque([(test_entity["id"], 0)])
        visited = {test_entity["id"]}
        while frontier:
            current, depth = frontier.popleft()
            if depth >= 4:
                continue
            for target in reference_outgoing.get(current, set()):
                if target in visited:
                    continue
                visited.add(target)
                frontier.append((target, depth + 1))
                target_page = owner_by_entity[target]
                if target_page == test_page:
                    continue
                key = stable_id("plink", target_page, test_page, "tested-by")
                candidate_links.append({"id": key, "type": "tested-by", "source": target_page, "target": test_page, "entity_link_ids": [], "count": 1, "evidence": {"test_entity_id": test_entity["id"], "reference_depth": depth + 1}})
    repository_page_id = stable_id("nav", graph["repository"]["commit"], "repository")
    new_page(repository_page_id, "", "repository")
    module_pages: dict[str, str] = {}
    for entity in entities:
        if entity["kind"] != "file" or entity["classification"] != "page":
            continue
        module = module_name(entity["path"])
        module_id = module_pages.setdefault(module, stable_id("nav", graph["repository"]["commit"], "module", module))
        if module_id not in pages:
            new_page(module_id, "", "module", module=module)
            key = stable_id("plink", repository_page_id, module_id, "contains-module")
            candidate_links.append({"id": key, "type": "contains-module", "source": repository_page_id, "target": module_id, "entity_link_ids": [], "count": 1, "category": "navigation"})
        key = stable_id("plink", module_id, entity["id"], "contains-file")
        candidate_links.append({"id": key, "type": "contains-file", "source": module_id, "target": entity["id"], "entity_link_ids": [], "count": 1, "category": "navigation"})

    # A partial C# type is counted against its deterministic primary fragment;
    # the other fragment files receive links to the unified logical page without
    # consuming their one-key-entity quota.
    file_page_by_path = {entity["path"]: entity["id"] for entity in entities if entity["kind"] == "file" and entity["classification"] == "page"}
    for entity in entities:
        if entity.get("classification") != "page" or not entity.get("partial"):
            continue
        for fragment in entity.get("fragments", []):
            source_page = file_page_by_path.get(fragment["path"])
            if not source_page or source_page == entity["id"]:
                continue
            key = stable_id("plink", source_page, entity["id"], "partial-fragment")
            candidate_links.append({"id": key, "type": "partial-fragment", "source": source_page, "target": entity["id"], "entity_link_ids": [], "count": 1, "category": "navigation"})

    _assign_human_titles(pages, entities, _repository_name(graph["repository"]["root"]))

    # Deduplicate inferred test and navigation links, then apply the four hard
    # per-source budgets.  Hidden relations remain represented by counts and by
    # the complete machine graph.
    deduplicated: dict[str, dict[str, Any]] = {}
    for link in candidate_links:
        existing = deduplicated.get(link["id"])
        if existing:
            existing["count"] = max(existing.get("count", 1), link.get("count", 1))
            existing["entity_link_ids"] = sorted(set(existing.get("entity_link_ids", [])) | set(link.get("entity_link_ids", [])))
            if link.get("evidence") and not existing.get("evidence"):
                existing["evidence"] = link["evidence"]
        else:
            deduplicated[link["id"]] = link

    def relation_category(link: dict[str, Any]) -> str:
        if link.get("category") == "navigation" or link["type"] in {"contains-module", "contains-file", "partial-fragment"}:
            return "navigation"
        if link["type"] == "tested-by":
            return "test"
        if pages[link["source"]]["page_type"] == "boundary" or pages[link["target"]]["page_type"] == "boundary":
            return "boundary"
        return "aggregate" if int(link.get("count", 1)) > 1 else "direct"

    limits = dict(page_config["relation_limits"])
    by_source_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    visible_links: list[dict[str, Any]] = []
    for link in deduplicated.values():
        link["category"] = relation_category(link)
        if link["category"] == "navigation":
            visible_links.append(link)
        else:
            by_source_category[(link["source"], link["category"])].append(link)
    for (source, category), values in sorted(by_source_category.items()):
        values.sort(key=lambda value: (-int(value.get("count", 1)), value["type"], pages[value["target"]]["title"], value["id"]))
        limit = limits[category]
        visible_links.extend(values[:limit])
        pages[source]["relation_summary"][category] = {
            "total_groups": len(values),
            "visible_groups": min(len(values), limit),
            "hidden_groups": max(0, len(values) - limit),
            "machine_relation_count": sum(int(value.get("count", 1)) for value in values),
            "limit": limit,
        }
    for page in pages.values():
        for category, limit in limits.items():
            page["relation_summary"].setdefault(category, {"total_groups": 0, "visible_groups": 0, "hidden_groups": 0, "machine_relation_count": 0, "limit": limit})
    page_links = {link["id"]: link for link in visible_links}
    for link in page_links.values():
        pages[link["source"]]["outgoing"].append(link)
        pages[link["target"]]["backlinks"].append(link)
    for page in pages.values():
        page["appendix_entities"].sort(key=lambda item: (item["path"], item["range"]["start_line"], item["qualified_name"]))
        page["boundary_entities"].sort(key=lambda item: (item["range"]["start_line"], item["qualified_name"]))
        page["tag"] = page_tag(page["page_type"])
    hidden_relation_groups = sum(summary["hidden_groups"] for page in pages.values() for summary in page["relation_summary"].values())
    return {
        "pages": sorted(pages.values(), key=lambda item: item["title"]),
        "links": sorted(page_links.values(), key=lambda item: item["id"]),
        "entity_owner_pages": owner_by_entity,
        "repository_page_id": repository_page_id,
        "module_page_ids": module_pages,
        "boundary_group_count": len(boundary_groups),
        "candidate_relation_group_count": len(deduplicated),
        "hidden_relation_group_count": hidden_relation_groups,
        "relation_limits": limits,
        "page_config": page_config,
        "page_config_sha256": page_config_sha256(page_config),
    }


def _source_manifest(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the source/provenance contract shared by every projection."""
    return sorted(
        [
            {
                "entity_id": entity["id"],
                "commit": entity["commit"],
                "blob": entity["blob"],
                "path": entity["path"],
                "start_byte": entity["range"]["start_byte"],
                "end_byte": entity["range"]["end_byte"],
                "start_line": entity["range"]["start_line"],
                "end_line": entity["range"]["end_line"],
            }
            for entity in graph["entities"]
        ],
        key=lambda item: item["entity_id"],
    )


def _page_sections(page: dict[str, Any], page_config: dict[str, Any]) -> list[str]:
    content = page_config["content"]
    if page["page_type"] in {"file", "entity"}:
        return list(content["code_page_sections"])
    if page["page_type"] == "boundary":
        return list(content["boundary_page_sections"])
    return list(content["aggregate_page_sections"])


def _overview_text(entity: dict[str, Any], page_config: dict[str, Any]) -> str:
    fields = page_config["content"]["overview_fields"]
    values = {
        "meaning": str(entity.get("meaning_zh", "")).strip(),
        "role": str(entity.get("role_zh", "")).strip(),
    }
    return " ".join(values[field] for field in fields if values[field]).strip()


def _aggregate_overview(page: dict[str, Any]) -> str:
    if page["page_type"] == "repository":
        return "从这里按职责进入项目中的类、函数和相关实现。"
    return f"这里汇集 {page['module']} 范围内彼此协作的类、函数和辅助实现。"


def _canonical_page_context(page: dict[str, Any], title_by_id: dict[str, str]) -> str:
    """Render the stable human facts used by deterministic context accounting."""
    page_config = page.get("page_config") or DEFAULT_PAGE_CONFIG
    sections = set(_page_sections(page, page_config))
    lines = [f"# {page['title']}", f"标签：{page.get('tag') or page_tag(page['page_type'])}"]
    entity = page.get("entity")
    if entity:
        if "overview" in sections:
            lines.append(f"说明：{_overview_text(entity, page_config)}")
        if "change_when" in sections:
            lines.append(f"修改提示：{entity.get('change_when_zh', '')}")
        if "source_location" in sections:
            lines.append(f"来源：{entity['path']}:{entity['range']['start_line']}-{entity['range']['end_line']}")
        if "partial_fragments" in sections:
            for fragment in entity.get("fragments", []):
                lines.append(f"组成位置：{fragment['path']}:{fragment['range']['start_line']}-{fragment['range']['end_line']}")
    elif page["page_type"] == "boundary":
        if "overview" in sections:
            lines.append("说明：这里汇集当前扫描范围之外、但与所选功能直接协作的代码。")
        if "boundary_details" in sections:
            for boundary in page.get("boundary_entities", []):
                lines.append(f"边界：{boundary['qualified_name']}｜{boundary['path']}:{boundary['range']['start_line']}-{boundary['range']['end_line']}")
    elif "overview" in sections:
        lines.append(f"说明：{_aggregate_overview(page)}")
    if "appendix" in sections:
        for appendix in page.get("appendix_entities", []):
            lines.append(f"附属：{appendix['qualified_name']}｜{appendix.get('description_zh', '')}")
    outgoing = sorted(page.get("outgoing", []), key=lambda value: (value["type"], title_by_id[value["target"]], value["id"]))
    for link in outgoing:
        section = "tests" if link["type"] == "tested-by" else "related_code"
        if section in sections:
            lines.append(f"协作：{title_by_id[link['target']]}")
    if "backlinks" in sections:
        for link in sorted(page.get("backlinks", []), key=lambda value: (title_by_id[value["source"]], value["id"])):
            lines.append(f"来源协作：{title_by_id[link['source']]}")
    return "\n".join(lines) + "\n"


def _logical_context_budgets(logical: dict[str, Any]) -> dict[str, Any]:
    page_config = logical.get("page_config", DEFAULT_PAGE_CONFIG)
    context_config = page_config["context"]
    title_by_id = {page["id"]: page["title"] for page in logical["pages"]}
    for page in logical["pages"]:
        page["page_config"] = page_config
    text_by_id = {page["id"]: _canonical_page_context(page, title_by_id) for page in logical["pages"]}
    modules: dict[str, Any] = {}
    for module, module_page_id in sorted(logical["module_page_ids"].items()):
        page_ids = {module_page_id}
        for page in logical["pages"]:
            source = page.get("entity")
            if source and module_name(source["path"]) == module:
                page_ids.add(page["id"])
            elif page["page_type"] == "boundary" and page.get("module") == module:
                page_ids.add(page["id"])
        text = "\n".join(text_by_id[value] for value in sorted(page_ids))
        record = context_budget_record(text, "full-module", module, page_config)
        record["page_ids"] = sorted(page_ids)
        record["full_module_allowed"] = record["status"] == "passed"
        if record["status"] != "passed":
            record["required_mode"] = "task-subgraph"
            record["task_subgraph_limit"] = int(context_config["task_max_tokens"])
        modules[module] = record
    return {
        "formula": f"ceil(utf8_bytes / {int(context_config['bytes_per_token'])})",
        "module_limit": int(context_config["module_max_tokens"]),
        "task_subgraph_limit": int(context_config["task_max_tokens"]),
        "total_context_budget": int(context_config["total_max_tokens"]),
        "reserved_agent_tokens": int(context_config["reserved_agent_tokens"]),
        "modules": modules,
    }


def _relation_phrase(link: dict[str, Any], other_title: str, incoming: bool = False) -> str:
    """Translate a machine relation into one short human navigation sentence."""
    relation = link["type"]
    if relation in {"contains-module", "contains-file"}:
        return f"可从 [[{other_title}]] 进入本页。" if incoming else f"继续浏览 [[{other_title}]]。"
    if relation == "contains":
        return f"[[{other_title}]] 汇总了本页。" if incoming else f"主要代码单元是 [[{other_title}]]。"
    if relation == "tested-by":
        return f"[[{other_title}]] 关联到这里的验证场景。" if incoming else f"由 [[{other_title}]] 覆盖相关行为。"
    if relation == "partial-fragment":
        return f"[[{other_title}]] 也参与组成这段实现。" if incoming else f"与 [[{other_title}]] 共同组成完整实现。"
    if relation in {"calls", "invokes"}:
        return f"[[{other_title}]] 会调用这里。" if incoming else f"执行时会调用 [[{other_title}]]。"
    if relation in {"imports", "depends-on", "uses"}:
        return f"[[{other_title}]] 依赖这里。" if incoming else f"实现依赖 [[{other_title}]]。"
    return f"[[{other_title}]] 会使用这里提供的行为。" if incoming else f"实现时会用到 [[{other_title}]]。"


def _human_relation_sentences(
    links: list[dict[str, Any]], title_by_id: dict[str, str], incoming: bool = False
) -> list[str]:
    """Keep one best sentence per neighboring page, hiding machine-type duplicates."""
    priorities = {
        "contains": 0,
        "contains-module": 0,
        "contains-file": 0,
        "partial-fragment": 1,
        "tested-by": 1,
        "calls": 2,
        "invokes": 2,
        "imports": 3,
        "depends-on": 3,
        "uses": 3,
        "references": 4,
    }
    selected: dict[str, dict[str, Any]] = {}
    endpoint = "source" if incoming else "target"
    for link in sorted(links, key=lambda value: (priorities.get(value["type"], 5), title_by_id[value[endpoint]], value["id"])):
        selected.setdefault(link[endpoint], link)
    return [
        _relation_phrase(link, title_by_id[link[endpoint]], incoming=incoming)
        for _neighbor, link in sorted(selected.items(), key=lambda item: title_by_id[item[0]])
    ]


def _normalized_edn_document(
    graph: dict[str, Any],
    logical: dict[str, Any],
    local_openers: dict[str, Any] | None = None,
) -> tuple[str, dict[str, int]]:
    """Render the same minimal narrative used by Markdown into Logseq EDN."""
    page_config = logical.get("page_config", DEFAULT_PAGE_CONFIG)
    title_by_id = {page["id"]: page["title"] for page in logical["pages"]}
    edn_pages: list[str] = []
    expected_relation_blocks = 0
    expected_page_entity_blocks = 0
    expected_appendix_blocks = 0
    expected_boundary_blocks = 0
    for page in logical["pages"]:
        entity = page["entity"]
        blocks: list[str] = [f"标签：{page.get('tag') or page_tag(page['page_type'])}"]
        sections = _page_sections(page, page_config)
        if page["page_type"] in {"file", "entity"}:
            for section in sections:
                if section == "overview":
                    blocks.append(f"页面说明：{_overview_text(entity, page_config)}")
                elif section == "change_when":
                    blocks.append(f"需要修改时：{entity['change_when_zh']}")
                elif section == "source_location":
                    if local_openers:
                        blocks.append(
                            "源码入口："
                            + source_markdown_link(
                                local_openers,
                                entity["path"],
                                int(entity["range"]["start_line"]),
                                int(entity["range"]["end_line"]),
                            )
                        )
                    else:
                        blocks.append(f"代码位置：{entity['path']}:{entity['range']['start_line']}-{entity['range']['end_line']}")
                    expected_page_entity_blocks += 1
                elif section == "partial_fragments" and entity.get("partial"):
                    for fragment in entity.get("fragments", []):
                        blocks.append(f"组成位置：{fragment['path']}:{fragment['range']['start_line']}-{fragment['range']['end_line']}")
                elif section == "appendix":
                    for appendix in page["appendix_entities"]:
                        blocks.append(f"内部实现：{appendix['qualified_name']} — {appendix['description_zh']}")
                        expected_appendix_blocks += 1
        elif page["page_type"] == "boundary":
            for section in sections:
                if section == "overview":
                    blocks.append("页面说明：这里汇集当前扫描范围之外、但与所选功能直接协作的代码。")
                elif section == "boundary_details":
                    for boundary in page["boundary_entities"]:
                        blocks.append(f"边界协作：{boundary['qualified_name']} — 位于 {boundary['path']}:{boundary['range']['start_line']}-{boundary['range']['end_line']}，本次未继续展开。")
                        expected_boundary_blocks += 1
        else:
            if "overview" in sections:
                blocks.append(f"页面说明：{_aggregate_overview(page)}")
        relation_blocks: list[str] = []
        outgoing = sorted(page["outgoing"], key=lambda link: (title_by_id[link["target"]], link["type"], link["id"]))
        tested_by = [link for link in outgoing if link["type"] == "tested-by"]
        collaboration = [link for link in outgoing if link["type"] != "tested-by"]
        if "related_code" in sections:
            relation_blocks.extend(f"协作：{sentence}" for sentence in _human_relation_sentences(collaboration, title_by_id))
        if "tests" in sections:
            relation_blocks.extend(f"协作：{sentence}" for sentence in _human_relation_sentences(tested_by, title_by_id))
        if "backlinks" in sections:
            relation_blocks.extend(f"协作：{sentence}" for sentence in _human_relation_sentences(page["backlinks"], title_by_id, incoming=True))
        expected_relation_blocks += len(relation_blocks)
        blocks.extend(relation_blocks)
        block_edn = " ".join(f"{{:block/title {json.dumps(content, ensure_ascii=False)}}}" for content in blocks)
        edn_pages.append(f"{{:page {{:block/title {json.dumps(page['title'], ensure_ascii=False)}}} :blocks [{block_edn}]}}")
    document = "{:pages-and-blocks [\n" + "\n".join(edn_pages) + "\n]}\n"
    counts = {
        "pages": len(logical["pages"]),
        "page_entities": expected_page_entity_blocks,
        "appendix_entities": expected_appendix_blocks,
        "boundary_entities": expected_boundary_blocks,
        "entities": expected_page_entity_blocks + expected_appendix_blocks + expected_boundary_blocks,
        "relations": expected_relation_blocks,
    }
    return document, counts


def _render_markdown_page(
    page: dict[str, Any],
    title_by_id: dict[str, str],
    page_config: dict[str, Any],
    local_openers: dict[str, Any],
) -> str:
    content = page_config["content"]
    headings = content["headings"]
    sections = _page_sections(page, page_config)
    entity = page.get("entity")
    lines = [f"# {page['title']}", "", f"标签：{page.get('tag') or page_tag(page['page_type'])}", ""]
    outgoing = sorted(page["outgoing"], key=lambda link: (title_by_id[link["target"]], link["type"], link["id"]))
    tested_by = [link for link in outgoing if link["type"] == "tested-by"]
    collaboration = [link for link in outgoing if link["type"] != "tested-by"]
    backlinks = sorted(page["backlinks"], key=lambda link: (title_by_id[link["source"]], link["type"], link["id"]))

    for section in sections:
        if section == "overview":
            if entity:
                lines.append(f"> {_overview_text(entity, page_config)}")
            elif page["page_type"] == "boundary":
                lines.append("> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。")
            else:
                lines.append(f"> {_aggregate_overview(page)}")
        elif section == "change_when" and entity:
            lines.extend(["", f"## {headings['change_when']}", "", str(entity["change_when_zh"])])
        elif section == "source_location" and entity:
            lines.extend(
                [
                    "",
                    f"## {headings['source_location']}",
                    "",
                    source_markdown_link(
                        local_openers,
                        entity["path"],
                        int(entity["range"]["start_line"]),
                        int(entity["range"]["end_line"]),
                    ),
                ]
            )
        elif section == "partial_fragments" and entity and entity.get("partial"):
            lines.extend(["", "这个类型由下面几段代码共同组成："])
            lines.extend(f"- `{item['path']}:{item['range']['start_line']}-{item['range']['end_line']}`" for item in entity.get("fragments", []))
        elif section == "boundary_details" and page.get("boundary_entities"):
            lines.extend(["", f"## {headings['boundary_details']}", ""])
            lines.extend(
                f"- **{boundary['qualified_name']}**：位于 `{boundary['path']}:{boundary['range']['start_line']}-{boundary['range']['end_line']}`。"
                for boundary in page["boundary_entities"]
            )
        elif section == "related_code" and collaboration:
            lines.extend(["", f"## {headings['related_code']}", ""])
            lines.extend(f"- {sentence}" for sentence in _human_relation_sentences(collaboration, title_by_id))
        elif section == "backlinks" and backlinks:
            lines.extend(["", f"## {headings['backlinks']}", ""])
            lines.extend(f"- {sentence}" for sentence in _human_relation_sentences(backlinks, title_by_id, incoming=True))
        elif section == "tests" and tested_by:
            lines.extend(["", f"## {headings['tests']}", ""])
            lines.extend(f"- [[{title_by_id[link['target']]}]]" for link in tested_by)
        elif section == "hidden_relation_hint":
            hidden = sum(int(value["hidden_groups"]) for value in page["relation_summary"].values())
            if hidden:
                lines.extend(["", "> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。"])
        elif section == "appendix" and page.get("appendix_entities"):
            lines.extend(["", f"## {headings['appendix']}", ""])
            if content["appendix_mode"] == "collapsed":
                lines.extend([f"<details><summary>查看本页收纳的 {len(page['appendix_entities'])} 个辅助实现</summary>", ""])
            lines.extend(["| 代码单元 | 一句话作用 |", "|---|---|"])
            for appendix in page["appendix_entities"]:
                symbol = str(appendix["qualified_name"]).replace("|", "\\|").replace("\n", " ")
                description = str(appendix["description_zh"]).replace("|", "\\|").replace("\n", " ")
                lines.append(f"| `{symbol}` | {description} |")
            if content["appendix_mode"] == "collapsed":
                lines.extend(["", "</details>"])
    return "\n".join(lines).rstrip() + "\n"


def _logseq_file_graph_config_bytes() -> bytes:
    """Load the pinned Logseq file-graph config and enforce its source hash."""
    template = Path(__file__).resolve().parents[2] / "references" / "logseq-config.edn"
    if not template.is_file():
        raise AuditError(f"pinned Logseq file-graph config is absent: {template}")
    if sha256_file(template) != LOGSEQ_FILE_GRAPH_CONFIG_SHA256:
        raise AuditError(
            "pinned Logseq file-graph config differs from the locked upstream template: "
            f"{template}"
        )
    return template.read_bytes()


def _install_logseq_file_graph_config(root: Path) -> dict[str, str]:
    """Make a Markdown projection directly openable as a Logseq file graph."""
    content = _logseq_file_graph_config_bytes()
    config = root / "logseq" / "config.edn"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(content)
    return {
        "graph_root": str(root.resolve()),
        "config": str(config.resolve()),
        "config_relative_path": "logseq/config.edn",
        "config_sha256": sha256_file(config),
        "source_commit": LOGSEQ_FILE_GRAPH_CONFIG_COMMIT,
        "source_url": LOGSEQ_FILE_GRAPH_CONFIG_URL,
    }


def _audit_logseq_file_graph_config(
    graph_root: Path,
    config_record: dict[str, Any],
    reason_prefix: str,
) -> list[dict[str, Any]]:
    """Audit one selectable Logseq file-graph root against the pinned template."""
    config = graph_root / "logseq" / "config.edn"
    expected_config = _logseq_file_graph_config_bytes()
    errors: list[dict[str, Any]] = []
    if not config.is_file():
        errors.append({"reason": f"{reason_prefix}-config-missing", "path": "logseq/config.edn"})
    else:
        if config.read_bytes() != expected_config:
            errors.append({"reason": f"{reason_prefix}-config-content-mismatch", "path": "logseq/config.edn"})
        actual_config_hash = sha256_file(config)
        if config_record.get("config_sha256") != actual_config_hash:
            errors.append({"reason": f"{reason_prefix}-config-hash-mismatch", "path": "logseq/config.edn"})
        if Path(config_record.get("config", "")).resolve() != config.resolve():
            errors.append({"reason": f"{reason_prefix}-config-path-mismatch", "path": "logseq/config.edn"})
    if Path(config_record.get("graph_root", "")).resolve() != graph_root.resolve():
        errors.append({"reason": f"{reason_prefix}-graph-root-mismatch"})
    if config_record.get("config_relative_path") != "logseq/config.edn":
        errors.append({"reason": f"{reason_prefix}-config-relative-path-mismatch"})
    if config_record.get("source_commit") != LOGSEQ_FILE_GRAPH_CONFIG_COMMIT:
        errors.append({"reason": f"{reason_prefix}-config-source-commit-mismatch"})
    if config_record.get("source_url") != LOGSEQ_FILE_GRAPH_CONFIG_URL:
        errors.append({"reason": f"{reason_prefix}-config-source-url-mismatch"})
    return errors


def _human_page_filenames(logical: dict[str, Any]) -> dict[str, str]:
    """Create readable filenames; use a numeric suffix only after sanitization collisions."""
    result: dict[str, str] = {}
    counts: dict[str, int] = defaultdict(int)
    for page in logical["pages"]:
        base = safe_title(page["title"], 105)
        counts[base] += 1
        suffix = f"（{counts[base]}）" if counts[base] > 1 else ""
        result[page["id"]] = f"{base}{suffix}.md"
    return result


def _wiki_document(graph: dict[str, Any], logical: dict[str, Any], output: Path) -> str:
    project = _repository_name(graph["repository"]["root"])
    repository_title = next(page["title"] for page in logical["pages"] if page["id"] == logical["repository_page_id"])
    module_ids = set(logical["module_page_ids"].values())
    module_titles = [page["title"] for page in logical["pages"] if page["id"] in module_ids]
    page_config = logical["page_config"]
    page_limits = page_config["page_limits"]
    code_sections = "、".join(page_config["content"]["code_page_sections"])
    lines = [
        f"# 如何阅读 {project} 代码知识库",
        "",
        "> 这是一套面向理解和修改代码的中文导航，而不是机器实体清单。",
        "",
        "## 从哪里开始",
        "",
        f"先打开 [[{repository_title}]]，再按当前任务进入下面的职责导览：",
        "",
        *[f"- [[{title}]]" for title in module_titles],
        "",
        "## 页面只保留什么",
        "",
        "- **类与函数页**：说明它做什么、何时修改、位于哪里，以及会和哪些代码协作。",
        "- **职责聚合页**：把同一实现文件或相邻目录中的类、函数和辅助逻辑放在一起讲清楚。",
        "- **内部细节**：访问器、简单判断、局部辅助函数和薄包装只以一句话收纳，不膨胀成独立页面。",
        "- **自然双链**：关系写成“会使用”“由测试覆盖”“继续浏览”等阅读提示，不展示机器关系类型或计数。",
        "- **页面类型**：每页只有一个 `#类型/...` 标签，用于区分代码、职责和边界。",
        "- **源码入口**：带源码位置的页面可以直接打开本地编辑器中的对应行。",
        "",
        "页面正文不展示内部 ID、版本标识、机器分类和解析器字段；这些真实性证据仍保存在机器审计层，并继续决定知识库能否完成。",
        "",
        "## 中文描述约定",
        "",
        "所有职责、修改时机、内部细节、关系说明以及 Agent 分析和修改记录都使用简体中文。英文只保留在专有名词、API、代码符号、命令、路径和必要技术术语中。类名和函数名无需翻译，但不得用纯英文段落代替中文解释。",
        "",
        "## 本次页面配置",
        "",
        f"普通文件、核心文件和邻近文件最多分别生成 {page_limits['ordinary_file']}、{page_limits['core_file']}、{page_limits['adjacent_file']} 个关键实体页；每个入口最多选择 {page_limits['core_per_entry']} 个核心页和 {page_limits['adjacent_per_entry']} 个邻近页。",
        "",
        f"代码页按以下顺序组织内容：{code_sections}。附录采用 `{page_config['content']['appendix_mode']}` 展示方式。完整规范化配置保存在 `{(output / 'page-config.json').resolve()}`。",
        "",
        "## 如何寻找修改入口",
        "",
        "1. 从职责导览找到最接近需求的业务区域。",
        "2. 打开相关类或函数页，先读“它做什么”和“什么时候需要修改”。",
        "3. 沿“相关代码”和“谁会来到这里”继续浏览。",
        "4. 在“相关测试”中确认修改后应验证的场景。",
        "5. 只有需要实现细节时才展开“内部细节”。",
        "",
        "## Graphify 关系导览",
        "",
        "Graphify 会把彼此连接紧密的代码归为职责群；机器知识库先按确定性词项和章节检索选择实体，再按固定图权重扩展关系。人类版关系报告见 [项目关系导览](../graphify-out/GRAPH_REPORT.md)。",
        "",
        "## Agent 确定性检索",
        "",
        "Agent 默认查询 `machine/knowledge.sqlite`，不把整套人类页面或完整实体图装入上下文。`fast` 使用有界图传播，`precise` 使用固定轮次加权排序；两者都不调用向量模型。",
        "",
        "```powershell",
        '& PYTHON scripts\\ckb.py retrieve --out OUTPUT "职责关键词" --budget 1800 --profile fast',
        '& PYTHON scripts\\ckb.py entity --out OUTPUT "类名或函数名"',
        '& PYTHON scripts\\ckb.py neighbors --out OUTPUT "类名或函数名" --depth 2',
        '& PYTHON scripts\\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"',
        "```",
        "",
        "## Agent 分析与修改记录",
        "",
        "Agent 解释代码时先读取 retrieve 产生的阅读包，再把结论保存到 `analysis`；修改内容和原因保存到 `changes`，独立失败经验和实验分别进入 `pitfalls` 与 `experiments`。这些笔记使用双链回到代码页，并在重新投影后继续保留。",
        "",
        "## 在 Obsidian 中打开",
        "",
        f"把 `{(output / 'human').resolve()}` 作为 vault 打开。核心搜索、图谱、反向链接、出链、标签和页面预览配置已经准备好；从 `INDEX` 或本页开始。`{(output / 'markdown').resolve()}` 是兼容镜像。",
        "",
        "## 在 Logseq 中打开",
        "",
        f"选择知识库输出目录 `{output.resolve()}`。该目录已经包含 Logseq 文件图谱所需的配置；进入图谱后从 `INDEX` 或本页开始阅读。",
        "",
    ]
    return "\n".join(lines)


def _readability_report(root: Path, graph: dict[str, Any], logical: dict[str, Any], files: dict[str, str]) -> dict[str, Any]:
    titles = {page["title"] for page in logical["pages"]}
    errors: list[dict[str, Any]] = []
    metrics = {
        "page_count": len(logical["pages"]),
        "frontmatter_pages": 0,
        "prefixed_titles": 0,
        "visible_commit_identifiers": 0,
        "machine_markers": 0,
        "raw_relation_labels": 0,
        "page_property_lines": 0,
        "invalid_page_tags": 0,
        "missing_source_links": 0,
        "visible_hash_identifiers": 0,
        "wiki_chinese_characters": 0,
        "non_chinese_narrative_fields": 0,
    }
    documents: list[tuple[str, str]] = []
    for page in logical["pages"]:
        path = root / "pages" / files[page["id"]]
        text = path.read_text(encoding="utf-8")
        documents.append((str(path), text))
        if text.startswith("---\n"):
            metrics["frontmatter_pages"] += 1
            errors.append({"page": page["title"], "reason": "frontmatter-exposed"})
        if page["title"].startswith(HUMAN_TITLE_PREFIXES):
            metrics["prefixed_titles"] += 1
            errors.append({"page": page["title"], "reason": "technical-title-prefix"})
        if not text.startswith(f"# {page['title']}\n"):
            errors.append({"page": page["title"], "reason": "title-heading-mismatch"})
        if page["page_type"] == "entity" and page["entity"].get("kind") not in HUMAN_CODE_UNIT_KINDS:
            errors.append({"page": page["title"], "reason": "standalone-page-is-not-class-or-function"})
        if page.get("human_page_kind") not in {"code-unit", "code-unit-aggregate"}:
            errors.append({"page": page["title"], "reason": "invalid-human-page-kind"})
        tags = re.findall(r"#类型/[\w\u3400-\u9fff-]+", text)
        expected_tag = page.get("tag") or page_tag(page["page_type"])
        if tags != [expected_tag]:
            metrics["invalid_page_tags"] += 1
            errors.append({"page": page["title"], "reason": "page-type-tag-invalid", "tags": tags, "expected": expected_tag})
        if page.get("entity") and "source_location" in _page_sections(page, logical["page_config"]):
            if not re.search(r"\[打开源码：[^\]]+\]\([a-z][a-z0-9+.-]*://", text, flags=re.IGNORECASE):
                metrics["missing_source_links"] += 1
                errors.append({"page": page["title"], "reason": "clickable-source-link-missing"})
        for target in re.findall(r"\[\[([^\]]+)\]\]", text):
            if target not in titles:
                errors.append({"page": page["title"], "target": target, "reason": "dangling-human-wikilink"})
    for name in ("INDEX.md", "WIKI.md"):
        path = root / name
        if not path.is_file():
            errors.append({"path": name, "reason": "human-document-missing"})
            continue
        documents.append((str(path), path.read_text(encoding="utf-8")))
    graph_report = root.parent / "graphify-out" / "GRAPH_REPORT.md"
    if graph_report.is_file():
        documents.append((str(graph_report), graph_report.read_text(encoding="utf-8")))
    combined = "\n".join(text for _path, text in documents)
    metrics["visible_commit_identifiers"] = len(re.findall(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", combined, flags=re.IGNORECASE))
    metrics["visible_hash_identifiers"] = len(re.findall(r"(?<![0-9a-f])[0-9a-f]{40,}(?![0-9a-f])", combined, flags=re.IGNORECASE))
    metrics["machine_markers"] = sum(combined.count(value) for value in HUMAN_VISIBLE_FORBIDDEN)
    metrics["raw_relation_labels"] = len(
        re.findall(
            r"(?m)^- `(?:references|contains|contains-file|contains-module|tested-by|partial-fragment|calls|imports)`\s*(?:→|←)",
            combined,
        )
    )
    metrics["page_property_lines"] = len(re.findall(r"(?m)^(?:id|page_type|commit|classification|language):", combined))
    wiki = (root / "WIKI.md").read_text(encoding="utf-8") if (root / "WIKI.md").is_file() else ""
    metrics["wiki_chinese_characters"] = len(re.findall(r"[\u3400-\u9fff]", wiki))
    narrative_errors: list[dict[str, Any]] = []
    for entity in graph.get("entities", []):
        fields = ("description_zh",) if entity.get("classification") == "appendix" else ("meaning_zh", "role_zh", "change_when_zh")
        for field in fields:
            if not contains_chinese_narrative(entity.get(field)):
                narrative_errors.append({"entity_id": entity["id"], "field": field})
        if not contains_chinese_narrative(entity.get("evidence_note")):
            narrative_errors.append({"entity_id": entity["id"], "field": "evidence_note"})
    metrics["non_chinese_narrative_fields"] = len(narrative_errors)
    if narrative_errors:
        errors.append({"reason": "simplified-chinese-description-contract", "count": len(narrative_errors), "detail": narrative_errors})
    for key in (
        "frontmatter_pages",
        "prefixed_titles",
        "visible_commit_identifiers",
        "machine_markers",
        "raw_relation_labels",
        "page_property_lines",
        "invalid_page_tags",
        "missing_source_links",
        "visible_hash_identifiers",
    ):
        if metrics[key]:
            errors.append({"reason": key, "count": metrics[key]})
    required_wiki = {"从哪里开始", "页面只保留什么", "中文描述约定", "本次页面配置", "如何寻找修改入口", "Graphify 关系导览", "Agent 确定性检索", "Agent 分析与修改记录", "在 Obsidian 中打开", "在 Logseq 中打开"}
    missing_sections = sorted(section for section in required_wiki if f"## {section}" not in wiki)
    if missing_sections or metrics["wiki_chinese_characters"] < 180:
        errors.append({"reason": "chinese-wiki-incomplete", "missing_sections": missing_sections, "chinese_characters": metrics["wiki_chinese_characters"]})
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "principle": "human-pages-describe-classes-functions-or-their-aggregations",
        "metrics": metrics,
        "errors": errors,
    }


def project_markdown(output: Path, graph: dict[str, Any], logical: dict[str, Any]) -> dict[str, Any]:
    root = output / "markdown"
    prepare_vault(root, output)
    pages_dir = root / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    state = json_load(output / "state.json")
    snapshot = state.get("source_snapshot") or {}
    local_openers = ensure_local_openers(
        output,
        Path(state["repository"]["root"]),
        Path(snapshot["root"]) if snapshot.get("root") else None,
    )
    obsidian = install_obsidian(root)
    logseq_file_graph = _install_logseq_file_graph_config(root)
    logseq_import_root = _install_logseq_file_graph_config(output)
    edn_text, expected_counts = _normalized_edn_document(graph, logical, local_openers)
    normalized_edn = root / "normalized.edn"
    normalized_edn.write_text(edn_text, encoding="utf-8", newline="\n")
    title_by_id = {page["id"]: page["title"] for page in logical["pages"]}
    files = _human_page_filenames(logical)
    for page in logical["pages"]:
        rendered = _render_markdown_page(page, title_by_id, logical["page_config"], local_openers)
        (pages_dir / files[page["id"]]).write_text(rendered, encoding="utf-8", newline="\n")

    repository_title = next(page["title"] for page in logical["pages"] if page["id"] == logical["repository_page_id"])
    project = _repository_name(graph["repository"]["root"])
    module_ids = set(logical["module_page_ids"].values())
    module_titles = [page["title"] for page in logical["pages"] if page["id"] in module_ids]
    index_lines = [
        f"# {project} 知识库",
        "",
        "> 用类、函数和职责聚合页理解代码；机器审计信息不占用阅读页面。",
        "",
        "## 从这里开始",
        "",
        f"- [[{repository_title}]]",
        "- [阅读这套知识库的方法](WIKI.md)",
        "",
        "## 按职责浏览",
        "",
        *[f"- [[{title}]]" for title in module_titles],
        "",
        "## 精确定位",
        "",
        "遇到具体修改任务时，优先使用 `retrieve --profile fast` 获取预算内机器阅读包；复杂问题再使用 `precise`。只在索引返回 `needs-source-read` 时读取最窄源码范围。两种档位都不调用向量模型。",
        "",
        "## 工作记录",
        "",
        "Agent 的分析、修改、踩坑、实验和会话笔记分别保存在同名目录，并通过双链回到代码页。",
        "",
        "## 在 Obsidian 中打开",
        "",
        f"把 `{(output / 'human').resolve()}` 作为 Obsidian vault 打开；从本页、标签或反向链接进入。`{root.resolve()}` 是兼容镜像。",
        "",
        "## 在 Logseq 中打开",
        "",
        f"选择输出目录 `{output.resolve()}`；配置文件位于 [logseq/config.edn](logseq/config.edn)。",
        "",
    ]
    (root / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8", newline="\n")
    (root / "WIKI.md").write_text(_wiki_document(graph, logical, output), encoding="utf-8", newline="\n")
    json_write(root / "context-budget.json", _logical_context_budgets(logical))
    readability = _readability_report(root, graph, logical, files)
    json_write(root / "readability-audit.json", readability)
    projection = {
        "format": "markdown",
        "pages": [{"id": page["id"], "title": page["title"], "page_type": page["page_type"], "human_page_kind": page["human_page_kind"], "tag": page.get("tag"), "file": f"pages/{files[page['id']]}"} for page in logical["pages"]],
        "links": logical["links"],
        "entity_owner_pages": logical["entity_owner_pages"],
        "source_manifest": _source_manifest(graph),
        "normalized_edn": str(normalized_edn.resolve()),
        "normalized_edn_sha256": sha256_file(normalized_edn),
        "logseq_file_graph": logseq_file_graph,
        "logseq_import_root": logseq_import_root,
        "expected_counts": expected_counts,
        "context_budget": str((root / "context-budget.json").resolve()),
        "readability_audit": str((root / "readability-audit.json").resolve()),
        "readability_status": readability["status"],
        "wiki": str((root / "WIKI.md").resolve()),
        "relation_limits": logical["relation_limits"],
        "hidden_relation_group_count": logical["hidden_relation_group_count"],
        "page_config": logical["page_config"],
        "page_config_sha256": logical.get("page_config_sha256"),
        "obsidian": obsidian,
        "source_links": {
            "editor": local_openers["source_editor"],
            "source_view": local_openers["source_view"],
            "config": str((output / "local-openers.json").resolve()),
        },
    }
    json_write(root / "projection.json", projection)
    generated = [
        *[path for path in pages_dir.rglob("*") if path.is_file()],
        root / "INDEX.md",
        root / "WIKI.md",
        root / "normalized.edn",
        root / "projection.json",
        root / "context-budget.json",
        root / "readability-audit.json",
        root / "logseq/config.edn",
        root / ".obsidian/app.json",
        root / ".obsidian/core-plugins.json",
        root / ".obsidian/appearance.json",
        root / ".obsidian/snippets/ckb.css",
    ]
    projection["generated_ownership"] = write_generated_ownership(root, generated)
    json_write(root / "projection.json", projection)
    return projection


def _logseq(command: str, root: Path, *args: str) -> tuple[int, str]:
    completed = run([command, "--root-dir", str(root), *args], timeout=180)
    graph_name = args[args.index("--graph") + 1] if "--graph" in args and args.index("--graph") + 1 < len(args) else None
    if graph_name and tuple(args[:2]) != ("server", "stop"):
        stopped = run(
            [command, "--root-dir", str(root), "server", "stop", "--graph", graph_name],
            timeout=60,
        )
        cleanup = {
            "command": "server stop",
            "graph": graph_name,
            "exit_status": stopped.returncode,
            "output": stopped.stdout + stopped.stderr,
        }
        cleanup_path = root / "worker-cleanup.jsonl"
        with cleanup_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(cleanup, ensure_ascii=False) + "\n")
        if completed.returncode == 0 and stopped.returncode:
            return stopped.returncode, f"Logseq command passed but its scoped DB worker did not stop: {stopped.stdout}{stopped.stderr}"
    return completed.returncode, (completed.stdout + completed.stderr)


def _logseq_count(output: str, label: str) -> int:
    """Extract a single numeric result from Logseq's JSON query output."""
    try:
        value = json.loads(output.strip())
    except json.JSONDecodeError as exc:
        raise AuditError(f"Logseq {label} count query did not return JSON: {output}") from exc

    numbers: list[int] = []

    def visit(item: Any) -> None:
        if isinstance(item, bool):
            return
        if isinstance(item, int):
            numbers.append(item)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)

    visit(value)
    def contains_null_result(item: Any) -> bool:
        if isinstance(item, dict):
            return any((key == "result" and child is None) or contains_null_result(child) for key, child in item.items())
        if isinstance(item, list):
            return any(contains_null_result(child) for child in item)
        return False

    if not numbers and contains_null_result(value):
        return 0
    if len(numbers) != 1:
        raise AuditError(f"Logseq {label} count query returned {len(numbers)} numeric values: {output}")
    return numbers[0]


def project_logseq(output: Path, graph: dict[str, Any], logical: dict[str, Any]) -> dict[str, Any]:
    command = resolve_executable("logseq")
    if not command:
        raise DependencyError("Logseq CLI is required for logseq-db or both output")
    graph_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", _repository_name(graph["repository"]["root"])).strip("-.") or "project"
    graph_name = "code-knowledge-" + graph_slug
    root = output / ".logseq-runtime"
    if root.exists():
        # An interrupted CLI call can leave its owned db-worker alive. Stop only
        # the worker scoped to this output root and graph before deleting the
        # disposable runtime. The normal command path also stops after every
        # operation so repeated finalize remains deterministic.
        run([command, "--root-dir", str(root), "server", "stop", "--graph", graph_name], timeout=60)
        for attempt in range(5):
            try:
                safe_rmtree(root, output)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.5 * (attempt + 1))
    root.mkdir()
    logs: list[dict[str, Any]] = []
    db_dir = output / "logseq-db"
    if db_dir.exists():
        safe_rmtree(db_dir, output)
    db_dir.mkdir()
    state = json_load(output / "state.json")
    snapshot = state.get("source_snapshot") or {}
    local_openers = ensure_local_openers(
        output,
        Path(state["repository"]["root"]),
        Path(snapshot["root"]) if snapshot.get("root") else None,
    )
    edn_text, expected_counts = _normalized_edn_document(graph, logical, local_openers)
    normalized_edn = db_dir / "normalized.edn"
    normalized_edn.write_text(edn_text, encoding="utf-8", newline="\n")
    logseq_readability_errors: list[dict[str, Any]] = []
    if any(page["title"].startswith(HUMAN_TITLE_PREFIXES) for page in logical["pages"]):
        logseq_readability_errors.append({"reason": "technical-title-prefix"})
    if any(
        page["page_type"] == "entity" and page["entity"].get("kind") not in HUMAN_CODE_UNIT_KINDS
        for page in logical["pages"]
    ):
        logseq_readability_errors.append({"reason": "standalone-page-is-not-class-or-function"})
    if re.search(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", edn_text, flags=re.IGNORECASE):
        logseq_readability_errors.append({"reason": "visible-commit-identifier"})
    if any(marker in edn_text for marker in HUMAN_VISIBLE_FORBIDDEN):
        logseq_readability_errors.append({"reason": "machine-marker-visible"})
    json_write(db_dir / "context-budget.json", _logical_context_budgets(logical))
    code, text = _logseq(command, root, "graph", "import", "--type", "edn", "--input", str(normalized_edn), "--graph", graph_name)
    logs.append({"command": "graph import --type edn", "input": str(normalized_edn.resolve()), "exit_status": code, "output": text})
    if code:
        raise AuditError(f"Logseq normalized EDN import failed: {text}")
    code, text = _logseq(command, root, "graph", "validate", "--graph", graph_name)
    logs.append({"command": "graph validate", "exit_status": code, "output": text})
    if code:
        raise AuditError(f"Logseq graph validation failed: {text}")
    validate_text = text
    query_outputs: dict[str, dict[str, Any]] = {}
    queries = {
        "pages": '[:find (count ?b) . :where [?b :block/title ?title] [(clojure.string/starts-with? ?title "页面说明：")]]',
        "page_entities": '[:find (count ?b) . :where [?b :block/title ?title] [(clojure.string/starts-with? ?title "源码入口：")]]',
        "appendix_entities": '[:find (count ?b) . :where [?b :block/title ?title] [(clojure.string/starts-with? ?title "内部实现：")]]',
        "boundary_entities": '[:find (count ?b) . :where [?b :block/title ?title] [(clojure.string/starts-with? ?title "边界协作：")]]',
        "relations": '[:find (count ?b) . :where [?b :block/title ?title] [(clojure.string/starts-with? ?title "协作：")]]',
    }
    for name, query in queries.items():
        code, query_text = _logseq(command, root, "--output", "json", "query", "--query", query, "--graph", graph_name)
        logs.append({"command": f"query {name}", "query": query, "exit_status": code, "output": query_text})
        query_outputs[name] = {"exit_status": code, "output": query_text}
        if code:
            raise AuditError(f"Logseq {name} count query failed: {query_text}")
        actual_count = _logseq_count(query_text, name)
        query_outputs[name]["actual_count"] = actual_count
        query_outputs[name]["expected_count"] = expected_counts[name]
        if actual_count != expected_counts[name]:
            raise AuditError(f"Logseq {name} count mismatch: expected {expected_counts[name]}, got {actual_count}")
    query_outputs["entities"] = {
        "actual_count": sum(int(query_outputs[name]["actual_count"]) for name in ("page_entities", "appendix_entities", "boundary_entities")),
        "expected_count": expected_counts["entities"],
        "basis": ["page_entities", "appendix_entities", "boundary_entities"],
    }
    if query_outputs["entities"]["actual_count"] != expected_counts["entities"]:
        raise AuditError(f"Logseq total entity count mismatch: expected {expected_counts['entities']}, got {query_outputs['entities']['actual_count']}")
    db_path = db_dir / "db.sqlite"
    code, text = _logseq(command, root, "graph", "export", "--type", "sqlite", "--file", str(db_path), "--graph", graph_name)
    logs.append({"command": "graph export sqlite", "exit_status": code, "output": text})
    if code or not db_path.is_file() or db_path.read_bytes()[:16] != b"SQLite format 3\x00":
        raise AuditError(f"Logseq SQLite export failed: {text}")
    with sqlite3.connect(db_path) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise AuditError(f"exported Logseq SQLite integrity check failed: {integrity}")
    cleanup_path = root / "worker-cleanup.jsonl"
    cleanup_records = [
        json.loads(line)
        for line in cleanup_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    projection = {
        "format": "logseq-db",
        "graph_name": graph_name,
        "db_path": str(db_path.resolve()),
        "normalized_edn": str(normalized_edn.resolve()),
        "normalized_edn_sha256": sha256_file(normalized_edn),
        "pages": [{"id": page["id"], "title": page["title"], "page_type": page["page_type"], "human_page_kind": page["human_page_kind"], "tag": page.get("tag")} for page in logical["pages"]],
        "links": logical["links"],
        "entity_owner_pages": logical["entity_owner_pages"],
        "source_manifest": _source_manifest(graph),
        "expected_counts": expected_counts,
        "context_budget": str((db_dir / "context-budget.json").resolve()),
        "relation_limits": logical["relation_limits"],
        "hidden_relation_group_count": logical["hidden_relation_group_count"],
        "page_config": logical["page_config"],
        "page_config_sha256": logical.get("page_config_sha256"),
        "source_links": {
            "editor": local_openers["source_editor"],
            "source_view": local_openers["source_view"],
            "config": str((output / "local-openers.json").resolve()),
        },
        "human_readability": {"status": "passed" if not logseq_readability_errors else "failed", "errors": logseq_readability_errors},
        "cli_queries": query_outputs,
        "validation": {"exit_status": 0, "graph_validate_output": validate_text, "sqlite_integrity": integrity, "sqlite_header": "SQLite format 3\\0"},
        "worker_cleanup": {
            "path": str(cleanup_path.resolve()),
            "operation_count": len(logs),
            "stop_count": len(cleanup_records),
            "all_stopped": len(cleanup_records) == len(logs) and all(item.get("exit_status") == 0 for item in cleanup_records),
        },
    }
    json_write(db_dir / "projection.json", projection)
    json_write(db_dir / "commands.json", logs)
    return projection


def _audit_markdown(output: Path, graph: dict[str, Any], logical: dict[str, Any]) -> list[dict[str, Any]]:
    root = output / "markdown"
    projection = json_load(root / "projection.json")
    state = json_load(output / "state.json")
    snapshot = state.get("source_snapshot") or {}
    local_openers = ensure_local_openers(
        output,
        Path(state["repository"]["root"]),
        Path(snapshot["root"]) if snapshot.get("root") else None,
    )
    titles = {item["title"] for item in projection["pages"]}
    errors = []
    if projection.get("page_config") != logical.get("page_config"):
        errors.append({"reason": "page-config-projection-mismatch"})
    if projection.get("page_config_sha256") != logical.get("page_config_sha256"):
        errors.append({"reason": "page-config-hash-mismatch"})
    logical_by_id = {page["id"]: page for page in logical["pages"]}
    for page in projection["pages"]:
        text = (root / page["file"]).read_text(encoding="utf-8")
        for target in re.findall(r"\[\[([^\]]+)\]\]", text):
            if target not in titles:
                errors.append({"page": page["id"], "target": target, "reason": "dangling-wikilink"})
        for appendix in logical_by_id[page["id"]].get("appendix_entities", []):
            if appendix["id"] in text:
                errors.append({"page": page["id"], "entity": appendix["id"], "reason": "appendix-stable-id-exposed"})
            if appendix.get("description_zh") not in text:
                errors.append({"page": page["id"], "entity": appendix["id"], "reason": "appendix-description-missing"})
    for document_name in ("INDEX.md", "WIKI.md"):
        document = root / document_name
        if not document.is_file():
            errors.append({"reason": "human-document-missing", "path": document_name})
            continue
        for target in re.findall(r"\[\[([^\]]+)\]\]", document.read_text(encoding="utf-8")):
            if target not in titles:
                errors.append({"path": document_name, "target": target, "reason": "dangling-wikilink"})
    readability_path = root / "readability-audit.json"
    if not readability_path.is_file():
        errors.append({"reason": "readability-audit-missing"})
    else:
        readability = json_load(readability_path)
        if readability.get("status") != "passed" or readability.get("errors"):
            errors.append({"reason": "human-readability-failed", "detail": readability})
        if Path(projection.get("readability_audit", "")).resolve() != readability_path.resolve():
            errors.append({"reason": "readability-audit-path-mismatch"})
        if projection.get("readability_status") != "passed":
            errors.append({"reason": "readability-status-mismatch"})
    logical_pairs = {(link["source"], link["target"], link["type"]) for link in logical["links"]}
    projected_pairs = {(link["source"], link["target"], link["type"]) for link in projection["links"]}
    if logical_pairs != projected_pairs:
        errors.append({"reason": "projection-link-set-mismatch"})
    normalized_edn = root / "normalized.edn"
    expected_edn, expected_counts = _normalized_edn_document(graph, logical, local_openers)
    if not normalized_edn.is_file():
        errors.append({"reason": "normalized-edn-missing"})
    else:
        actual_edn = normalized_edn.read_text(encoding="utf-8")
        if actual_edn != expected_edn:
            errors.append({"reason": "normalized-edn-content-mismatch"})
        actual_hash = sha256_file(normalized_edn)
        if projection.get("normalized_edn_sha256") != actual_hash:
            errors.append({"reason": "normalized-edn-hash-mismatch"})
        if Path(projection.get("normalized_edn", "")).resolve() != normalized_edn.resolve():
            errors.append({"reason": "normalized-edn-path-mismatch"})
    if projection.get("expected_counts") != expected_counts:
        errors.append({"reason": "normalized-edn-count-contract-mismatch"})
    errors.extend(_audit_logseq_file_graph_config(root, projection.get("logseq_file_graph", {}), "logseq-markdown-root"))
    errors.extend(_audit_logseq_file_graph_config(output, projection.get("logseq_import_root", {}), "logseq-import-root"))
    errors.extend(audit_obsidian(root))
    errors.extend(audit_notes(output))
    return errors


def audit_global(output: Path) -> dict[str, Any]:
    state = _load_state(output)
    clear_markers(output)
    if state.get("status") == "complete":
        state["status"] = "in-progress"
        json_write(output / "state.json", state)
    graph_path = output / "graph.json"
    if not graph_path.is_file():
        raise AuditError("merge must produce graph.json before global audit")
    graph = json_load(graph_path)
    page_config = normalize_page_config(graph.get("page_config", DEFAULT_PAGE_CONFIG))
    logical = _logical_projection(graph)
    checks: list[dict[str, Any]] = []
    pinned_config_path = output / state["page_config"]["relative_path"]
    config_hash = page_config_sha256(page_config)
    checks.append(
        {
            "name": "page-configuration-pinned",
            "passed": (
                pinned_config_path.is_file()
                and sha256_file(pinned_config_path) == state["page_config"]["sha256"]
                and config_hash == state["page_config"]["sha256"]
                and graph.get("page_config_sha256") == config_hash
                and page_config_bytes(page_config) == pinned_config_path.read_bytes()
            ),
            "detail": {
                "path": str(pinned_config_path.resolve()),
                "state_sha256": state["page_config"]["sha256"],
                "graph_sha256": graph.get("page_config_sha256"),
                "actual_sha256": sha256_file(pinned_config_path) if pinned_config_path.is_file() else None,
                "page_limits": page_config["page_limits"],
                "content": page_config["content"],
            },
        }
    )
    snapshot_errors: list[dict[str, Any]] = []
    try:
        if not isinstance(state.get("source_snapshot"), dict):
            snapshot_errors.append({"reason": "fixed-source-snapshot-missing"})
        else:
            assert_source_snapshot(state["repository"], state["source_snapshot"])
    except CkbError as exc:
        snapshot_errors.append({"reason": "fixed-source-snapshot-invalid", "detail": str(exc)})
    checks.append(
        {
            "name": "fixed-source-snapshot",
            "passed": not snapshot_errors,
            "detail": {
                "errors": snapshot_errors,
                "snapshot": state.get("source_snapshot"),
                "live-worktree-may-change": True,
            },
        }
    )
    if state.get("migration"):
        from .migration import audit_migration

        migration_audit = audit_migration(output, require_complete_reviews=True)
        checks.append(
            {
                "name": "incremental-migration",
                "passed": migration_audit.get("status") == "passed",
                "detail": migration_audit,
            }
        )
    chunk_audits = []
    for chunk in state["chunks"]:
        audit = audit_chunk(output, chunk["id"])
        chunk_audits.append(audit)
    checks.append({"name": "all-chunk-audits-passed", "passed": all(item["status"] == "passed" for item in chunk_audits), "detail": {item["chunk_id"]: item["status"] for item in chunk_audits}})
    review_pack_status = {item["id"]: item["status"] for item in state.get("review_packs", [])}
    checks.append({"name": "all-review-packs-passed", "passed": bool(review_pack_status) and all(value == "passed" for value in review_pack_status.values()), "detail": review_pack_status})
    catalog, scope_doc, _boundary_doc = _selected_catalog(output)
    scope_ids = set(scope_doc["selected_entity_ids"])
    graph_ids = {entity["id"] for entity in graph["entities"]}
    checks.append({"name": "global-entity-set-exact", "passed": graph_ids == scope_ids, "detail": {"missing": sorted(scope_ids - graph_ids), "extra": sorted(graph_ids - scope_ids)}})
    dangling = [link["id"] for link in graph["links"] if link["source"] not in graph_ids or link["target"] not in graph_ids]
    checks.append({"name": "global-link-endpoints", "passed": not dangling, "detail": dangling})
    chinese_description_errors: list[dict[str, Any]] = []
    for entity in graph["entities"]:
        if entity.get("classification") == "appendix":
            if not contains_chinese_narrative(entity.get("description_zh")):
                chinese_description_errors.append({"entity_id": entity["id"], "field": "description_zh"})
        else:
            for field in ("meaning_zh", "role_zh", "change_when_zh"):
                if not contains_chinese_narrative(entity.get(field)):
                    chinese_description_errors.append({"entity_id": entity["id"], "field": field})
        if not contains_chinese_narrative(entity.get("evidence_note")):
            chinese_description_errors.append({"entity_id": entity["id"], "field": "evidence_note"})
    checks.append(
        {
            "name": "simplified-chinese-description-contract",
            "passed": not chinese_description_errors,
            "detail": {
                "rule": "所有叙述字段使用简体中文；英文专有名词、路径和代码标识符可以保留。",
                "errors": chinese_description_errors,
            },
        }
    )
    navigation_plan = graph.get("navigation_plan", {})
    planned = {item["entity_id"]: item for item in navigation_plan.get("decisions", [])}
    navigation_errors = []
    for entity in graph["entities"]:
        decision = planned.get(entity["id"])
        if not decision:
            navigation_errors.append({"id": entity["id"], "reason": "missing-navigation-decision"})
        elif entity.get("classification") != decision.get("classification") or entity.get("owner_page_id") != decision.get("owner_page_id"):
            navigation_errors.append({"id": entity["id"], "reason": "navigation-decision-drift"})
    navigation_config_equal = navigation_plan.get("page_limits") == page_config["page_limits"]
    checks.append({"name": "deterministic-navigation-plan", "passed": navigation_plan.get("status") == "passed" and not navigation_plan.get("quota_errors") and not navigation_errors and navigation_config_equal, "detail": {"algorithm": navigation_plan.get("algorithm"), "quota_errors": navigation_plan.get("quota_errors"), "decision_errors": navigation_errors, "page_limits_equal": navigation_config_equal}})
    page_entities = [entity for entity in graph["entities"] if entity.get("classification") == "page"]
    actual_page_ids = {entity["id"] for entity in page_entities}
    planned_page_ids = set(navigation_plan.get("page_entity_ids", []))
    module_count = len(logical["module_page_ids"])
    entry_cluster_count = len(navigation_plan.get("entry_clusters", []))
    maximum_pages = page_limit(len(scope_doc["selected_file_paths"]), module_count, entry_cluster_count, logical["boundary_group_count"], page_config)
    checks.append({"name": "human-page-count-bounded", "passed": actual_page_ids == planned_page_ids and len(logical["pages"]) <= maximum_pages, "detail": {"actual_navigation_pages": len(logical["pages"]), "maximum_navigation_pages": maximum_pages, "planned_page_entity_delta": sorted(actual_page_ids ^ planned_page_ids)}})
    appendix_errors = []
    page_ids = {entity["id"] for entity in page_entities}
    for entity in graph["entities"]:
        if entity.get("classification") != "appendix":
            continue
        if entity.get("owner_page_id") not in page_ids:
            appendix_errors.append({"id": entity["id"], "reason": "owner-not-source-page", "owner": entity.get("owner_page_id")})
        if not _single_chinese_sentence(entity.get("description_zh")):
            appendix_errors.append({"id": entity["id"], "reason": "description-not-one-reviewed-sentence"})
    checks.append({"name": "appendix-ownership-and-description", "passed": not appendix_errors, "detail": appendix_errors})
    title_counts: dict[str, int] = defaultdict(int)
    for page in logical["pages"]:
        title_counts[page["title"]] += 1
    title_errors = [title for title, count in title_counts.items() if count != 1]
    tag_errors = [
        {"page": page["id"], "tag": page.get("tag"), "expected": page_tag(page["page_type"])}
        for page in logical["pages"]
        if page.get("tag") != page_tag(page["page_type"])
    ]
    relation_budget_errors = []
    for page in logical["pages"]:
        counts: dict[str, int] = defaultdict(int)
        for link in page["outgoing"]:
            if link.get("category") != "navigation":
                counts[link["category"]] += 1
        for category, limit in logical["relation_limits"].items():
            if counts.get(category, 0) > limit:
                relation_budget_errors.append({"page": page["id"], "category": category, "count": counts[category], "limit": limit})
        if any(link not in logical["links"] for link in page["outgoing"]):
            relation_budget_errors.append({"page": page["id"], "reason": "outgoing-not-in-visible-link-set"})
    backlinks = {(link["id"], link["source"], link["target"]) for page in logical["pages"] for link in page["backlinks"]}
    visible = {(link["id"], link["source"], link["target"]) for link in logical["links"]}
    checks.append({"name": "titles-tags-links-and-backlinks-complete", "passed": not title_errors and not tag_errors and not relation_budget_errors and backlinks == visible, "detail": {"duplicate_titles": title_errors, "tag_errors": tag_errors, "relation_budget_errors": relation_budget_errors, "backlink_delta": sorted(backlinks ^ visible)}})
    contexts = _logical_context_budgets(logical)
    task_context_limit = int(page_config["context"]["task_max_tokens"])
    context_errors = []
    for module, record in contexts["modules"].items():
        if record["status"] != "passed" and (record.get("required_mode") != "task-subgraph" or record.get("task_subgraph_limit") != task_context_limit):
            context_errors.append({"module": module, "record": record})
    checks.append({"name": "context-budget-contract", "passed": not context_errors, "detail": {"errors": context_errors, "modules": contexts["modules"]}})
    file_by_path = {item["file"]["path"]: item["file"] for item in catalog["files"]}
    audit_paths = {entity["path"] for entity in graph["entities"]}
    audit_paths.update(fragment["path"] for entity in graph["entities"] for fragment in entity.get("fragments", []))
    audit_files = [file_by_path[path] for path in sorted(audit_paths)]
    audit_sources = blob_bytes_many(state["repository"], audit_files)
    source_errors = [
        {"id": entity["id"], "reason": reason}
        for entity in graph["entities"]
        if (reason := _source_check(entity, audit_sources.get(entity["path"]), file_by_path.get(entity["path"], {}).get("blob")))
    ]
    source_errors.extend(error for entity in graph["entities"] for error in _partial_fragment_source_errors(entity, audit_sources, file_by_path))
    checks.append({"name": "global-git-source-authentic", "passed": not source_errors, "detail": source_errors})
    csharp_workspace = state.get("csharp_workspace")
    csharp_workspace_errors: list[dict[str, Any]] = []
    if csharp_workspace:
        restore = csharp_workspace.get("restore") or {}
        fallback = csharp_workspace.get("fallback") or {}
        if not restore.get("requested") and restore.get("network_restore"):
            csharp_workspace_errors.append({"reason": "network-restore-without-explicit-request"})
        if restore.get("performed"):
            workspace_root = Path(csharp_workspace["workspace_root"])
            head = run(["git", "-C", str(workspace_root), "rev-parse", "HEAD"], timeout=30)
            if head.returncode or head.stdout.strip() != state["repository"]["commit"]:
                csharp_workspace_errors.append({"reason": "restore-worktree-commit-drift", "output": head.stdout + head.stderr})
            manifest_path = Path(restore.get("file_manifest", ""))
            if not manifest_path.is_file():
                csharp_workspace_errors.append({"reason": "restore-file-manifest-missing"})
            else:
                runtime_root = workspace_root.parent
                for item in json_load(manifest_path).get("files", []):
                    path = runtime_root / item["path"]
                    if not path.is_file() or path.stat().st_size != int(item["size"]) or sha256_file(path) != item["sha256"]:
                        csharp_workspace_errors.append({"reason": "restore-file-hash-mismatch", "path": item["path"]})
                        break
        if csharp_workspace.get("precision") == "exact" and not csharp_workspace.get("path"):
            csharp_workspace_errors.append({"reason": "exact-csharp-workspace-without-project"})
        if csharp_workspace.get("precision") == "bounded-approximate":
            workspace_root = Path(csharp_workspace.get("workspace_root", ""))
            project = workspace_root / str(csharp_workspace.get("path", ""))
            head = run(["git", "-C", str(workspace_root), "rev-parse", "HEAD"], timeout=30) if workspace_root.is_dir() else None
            if head is None or head.returncode or head.stdout.strip() != state["repository"]["commit"]:
                csharp_workspace_errors.append({"reason": "fallback-worktree-commit-drift"})
            if not project.is_file() or sha256_file(project) != fallback.get("project_sha256"):
                csharp_workspace_errors.append({"reason": "fallback-project-hash-mismatch", "path": str(project)})
            if fallback.get("network_restore"):
                csharp_workspace_errors.append({"reason": "fallback-project-network-restore"})
    checks.append({"name": "csharp-workspace-and-restore", "passed": not csharp_workspace_errors, "detail": {"workspace": csharp_workspace, "errors": csharp_workspace_errors}})
    projections: dict[str, Any] = {}
    projections["facts"] = build_facts_layer(output, graph)
    facts_errors = audit_facts_layer(output, graph).get("errors", [])
    checks.append({"name": "facts-layer-valid", "passed": not facts_errors, "detail": projections["facts"]})
    projections["graphify"] = project_graphify(output, graph)
    graphify_errors = audit_graphify(output, graph, projections["graphify"])
    checks.append(
        {
            "name": "graphify-projection-valid",
            "passed": not graphify_errors,
            "detail": {
                "errors": graphify_errors,
                "node_count": projections["graphify"].get("node_count"),
                "link_count": projections["graphify"].get("link_count"),
                "community_count": projections["graphify"].get("community_count"),
                "graphify_commit": projections["graphify"].get("graphify_commit"),
            },
        }
    )
    # Version 5 always emits a conservative Markdown human layer.  The format
    # flag still controls whether a Logseq DB projection is additionally built.
    projections["markdown"] = project_markdown(output, graph, logical)
    projections["agent-protocol"] = project_agent_protocol(output)
    if state.get("migration"):
        from .migration import relink_preserved_notes

        projections["markdown"]["migration_note_relink"] = relink_preserved_notes(output, graph, projections["markdown"])
    pending_notes = materialize_pending_notes(output)
    projections["markdown"]["materialized_pending_notes"] = pending_notes
    json_write(output / "markdown/projection.json", projections["markdown"])
    errors = _audit_markdown(output, graph, logical)
    checks.append({"name": "markdown-valid", "passed": not errors, "detail": errors})
    readability = json_load(output / "markdown" / "readability-audit.json")
    checks.append(
        {
            "name": "human-readable-pages",
            "passed": readability.get("status") == "passed" and not readability.get("errors"),
            "detail": readability,
        }
    )
    projections["human"] = sync_human_layer(output, graph)
    human_audit = audit_human_layer(output, graph)
    checks.append({"name": "human-layer-valid", "passed": human_audit.get("status") == "passed", "detail": human_audit})
    if state["format"] in {"logseq-db", "both"}:
        projections["logseq-db"] = project_logseq(output, graph, logical)
        checks.append({"name": "logseq-db-valid", "passed": Path(projections["logseq-db"]["db_path"]).read_bytes()[:16] == b"SQLite format 3\x00", "detail": projections["logseq-db"].get("validation")})
        checks.append({"name": "logseq-human-readable", "passed": projections["logseq-db"]["human_readability"]["status"] == "passed", "detail": projections["logseq-db"]["human_readability"]})
        checks.append({"name": "logseq-worker-cleanup", "passed": projections["logseq-db"]["worker_cleanup"]["all_stopped"], "detail": projections["logseq-db"]["worker_cleanup"]})
    projections["machine"] = build_machine_knowledge(output, graph, logical)
    machine_audit = audit_machine_knowledge(output, graph)
    checks.append({"name": "machine-layer-valid", "passed": machine_audit.get("status") == "passed", "detail": machine_audit})
    projections["agent-index"] = build_agent_index(output)
    index_audit = audit_agent_index(output)
    checks.append(
        {
            "name": "agent-index-valid",
            "passed": index_audit.get("status") == "passed",
            "detail": index_audit,
        }
    )
    agent_protocol_audit = audit_agent_protocol(output)
    checks.append(
        {
            "name": "agent-protocol-valid",
            "passed": agent_protocol_audit.get("status") == "passed",
            "detail": agent_protocol_audit,
        }
    )
    if state["format"] == "both":
        markdown_projection = projections["markdown"]
        logseq_projection = projections["logseq-db"]
        md_pages = {(item["id"], item["title"], item["page_type"], item["human_page_kind"], item.get("tag")) for item in markdown_projection["pages"]}
        db_pages = {(item["id"], item["title"], item["page_type"], item["human_page_kind"], item.get("tag")) for item in logseq_projection["pages"]}
        md_links = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in markdown_projection["links"]}
        db_links = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in logseq_projection["links"]}
        owner_equal = markdown_projection["entity_owner_pages"] == logseq_projection["entity_owner_pages"]
        source_equal = markdown_projection["source_manifest"] == logseq_projection["source_manifest"]
        edn_equal = markdown_projection["normalized_edn_sha256"] == logseq_projection["normalized_edn_sha256"]
        config_equal = (
            markdown_projection.get("page_config") == logseq_projection.get("page_config") == page_config
            and markdown_projection.get("page_config_sha256") == logseq_projection.get("page_config_sha256") == config_hash
        )
        checks.append({
            "name": "dual-projection-parity",
            "passed": md_pages == db_pages and md_links == db_links and owner_equal and source_equal and edn_equal and config_equal,
            "detail": {
                "page_delta": sorted(md_pages ^ db_pages),
                "link_delta": sorted(md_links ^ db_links),
                "entity_ownership_equal": owner_equal,
                "source_manifest_equal": source_equal,
                "normalized_edn_equal": edn_equal,
                "page_config_equal": config_equal,
            },
        })
    status = "passed" if all(item["passed"] for item in checks) else "failed"
    result = {"schema_version": SCHEMA_VERSION, "status": status, "checks": checks, "projections": projections, "audited_at_utc": utc_now()}
    json_write(output / "audit" / "global.json", result)
    write_marker(
        output,
        ".pending-agent-review" if status == "passed" else ".failed",
        {"status": "global-audit-passed-finalize-required" if status == "passed" else "failed", "audit": str((output / "audit" / "global.json").resolve())},
    )
    return result


def finalize(output: Path) -> dict[str, Any]:
    state = _load_state(output)
    if not (output / "graph.json").is_file():
        merge(output)
    result = audit_global(output)
    if result["status"] != "passed":
        state["status"] = "failed"
        json_write(output / "state.json", state)
        write_marker(output, ".failed", {"status": "failed", "audit": str((output / "audit" / "global.json").resolve())})
        raise AuditError(f"global audit failed: {output / 'audit' / 'global.json'}")
    # audit_migration may promote the nested migration state to ``passed``.
    # Reopen state so finalize does not overwrite that promotion with the
    # pre-audit ``pending-agent-review`` value held by this stack frame.
    state = _load_state(output)
    state["status"] = "complete"
    state["completed_at_utc"] = utc_now()
    json_write(output / "state.json", state)
    complete = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "commit": state["repository"]["commit"],
        "scope": str((output / "scope.json").resolve()),
        "format": state["format"],
        "semantic_precision": state["semantic_precision"],
        "semantic_providers": [
            {
                "language": provider.get("language"),
                "name": provider.get("name"),
                "status": provider.get("status"),
                "precision": provider.get("precision"),
                "fallback_flags": provider.get("initialization_options", {}).get("fallbackFlags", []),
                "fallback_evidence": provider.get("initialization_options", {}).get("fallbackEvidence"),
                "diagnostic_count": provider.get("diagnostic_count", 0),
                "fatal_diagnostic_count": len(provider.get("fatal_diagnostics", [])) + len(provider.get("fatal_stderr", [])),
            }
            for provider in json_load(output / "graph.json").get("providers", [])
        ],
        "chunks": [chunk["id"] for chunk in state["chunks"]],
        "parse_batches": [chunk["id"] for chunk in state["parse_batches"]],
        "review_packs": [pack["id"] for pack in state.get("review_packs", [])],
        "navigation_plan": str((output / "navigation-plan.json").resolve()),
        "page_config": {
            **state["page_config"],
            "path": str((output / state["page_config"]["relative_path"]).resolve()),
        },
        "csharp_workspace": state.get("csharp_workspace"),
        "source_snapshot": state.get("source_snapshot"),
        "global_audit": str((output / "audit" / "global.json").resolve()),
        "graph": str((output / "graph.json").resolve()),
        "artifacts": result["projections"],
        "completed_at_utc": utc_now(),
    }
    write_marker(output, ".complete", complete)
    json_write(
        output / ".machine.complete",
        {
            "schema_version": SCHEMA_VERSION,
            "status": "complete",
            "machine": result["projections"].get("machine"),
            "facts": result["projections"].get("facts"),
            "global_audit": complete["global_audit"],
            "completed_at_utc": complete["completed_at_utc"],
        },
    )
    json_write(
        output / ".human.complete",
        {
            "schema_version": SCHEMA_VERSION,
            "status": "complete",
            "human": result["projections"].get("human"),
            "readability": result["projections"].get("markdown", {}).get("readability_audit"),
            "global_audit": complete["global_audit"],
            "completed_at_utc": complete["completed_at_utc"],
        },
    )
    return complete


def relink_sources(
    output: Path,
    repository_root: Path,
    editor: str,
    source_view: str = "working",
    custom_template: str | None = None,
) -> dict[str, Any]:
    """Regenerate local clickable source links and re-run completion gates."""
    from .source_links import update_local_openers

    config = update_local_openers(
        output,
        repository_root,
        editor=editor,
        source_view=source_view,
        custom_template=custom_template,
    )
    complete = finalize(output)
    return {"schema_version": SCHEMA_VERSION, "status": "passed", "local_openers": config, "complete": complete}


def build_context(output: Path, module: str, entry: str | None = None) -> dict[str, Any]:
    """Build a deterministic full-module or bounded task-subgraph context file."""
    _load_state(output)
    graph_path = output / "graph.json"
    if not graph_path.is_file():
        raise CkbError("merge must produce graph.json before building navigation context")
    graph = json_load(graph_path)
    logical = _logical_projection(graph)
    page_config = logical["page_config"]
    context_config = page_config["context"]
    module_context_limit = int(context_config["module_max_tokens"])
    task_context_limit = int(context_config["task_max_tokens"])
    token_divisor = int(context_config["bytes_per_token"])
    budgets = _logical_context_budgets(logical)
    if module not in budgets["modules"]:
        raise CkbError(f"unknown module: {module}; candidates={sorted(budgets['modules'])}")
    title_by_id = {page["id"]: page["title"] for page in logical["pages"]}
    page_by_id = {page["id"]: page for page in logical["pages"]}
    text_by_id = {page["id"]: _canonical_page_context(page, title_by_id) for page in logical["pages"]}
    module_ids = set(budgets["modules"][module]["page_ids"])
    record = budgets["modules"][module]
    if record["status"] == "passed":
        mode = "full-module"
        selected = sorted(module_ids)
        text = "\n".join(text_by_id[value] for value in selected)
    else:
        if not entry:
            candidates = sorted(
                page["entity"]["qualified_name"]
                for page in logical["pages"]
                if page["id"] in module_ids and page.get("entity") and page["entity"]["kind"] != "file"
            )[:50]
            raise CkbError(f"module exceeds {module_context_limit} estimated tokens; --entry is required for a <= {task_context_limit} task subgraph; candidates={candidates}")
        matches = [
            page
            for page in logical["pages"]
            if page["id"] in module_ids
            and (
                page["id"] == entry
                or page["title"] == entry
                or (page.get("entity") and entry in {page["entity"]["name"], page["entity"]["qualified_name"], page["entity"]["path"]})
            )
        ]
        if len(matches) != 1:
            candidates = [f"{page['title']} [{page['id']}]" for page in matches[:30]]
            raise CkbError(f"context entry resolves to {len(matches)} pages: {entry}; candidates={candidates}")
        seed = matches[0]["id"]
        neighbors: dict[str, set[str]] = defaultdict(set)
        for link in logical["links"]:
            if link["source"] in module_ids and link["target"] in module_ids:
                neighbors[link["source"]].add(link["target"])
                neighbors[link["target"]].add(link["source"])
        selected = []
        chunks: list[str] = []
        queue_ids = deque([seed])
        visited = {seed}
        while queue_ids:
            page_id = queue_ids.popleft()
            candidate = text_by_id[page_id]
            combined = "\n".join([*chunks, candidate])
            if estimated_tokens(combined, token_divisor) <= task_context_limit:
                selected.append(page_id)
                chunks.append(candidate)
            elif page_id == seed:
                # Preserve complete lines from the seed page up to the hard
                # context limit; the omission record is explicit and stable.
                bounded_lines: list[str] = []
                omitted = 0
                for line in candidate.splitlines():
                    trial = "\n".join([*bounded_lines, line, "附属实体省略：待按源码位置继续加载。"])
                    if estimated_tokens(trial, token_divisor) <= task_context_limit:
                        bounded_lines.append(line)
                    else:
                        omitted += 1
                bounded_lines.append(f"上下文预算省略行数：{omitted}")
                chunks.append("\n".join(bounded_lines) + "\n")
                selected.append(page_id)
            for neighbor in sorted(neighbors.get(page_id, set()), key=lambda value: (title_by_id[value], value)):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue_ids.append(neighbor)
        text = "\n".join(chunks)
        mode = "task-subgraph"
    budget = context_budget_record(text, mode, module, page_config)
    if budget["status"] != "passed":
        raise AuditError(f"generated context exceeds deterministic {mode} limit: {budget}")
    context_dir = output / "context"
    context_dir.mkdir(exist_ok=True)
    context_id = stable_id("context", graph["repository"]["commit"], module, mode, entry or "")
    context_path = context_dir / f"{context_id}.md"
    context_path.write_text(text, encoding="utf-8", newline="\n")
    result = {
        "schema_version": SCHEMA_VERSION,
        "context_id": context_id,
        "mode": mode,
        "module": module,
        "entry": entry,
        "page_ids": selected,
        "page_titles": [title_by_id[value] for value in selected],
        "budget": budget,
        "path": str(context_path.resolve()),
        "sha256": sha256_file(context_path),
        "created_at_utc": utc_now(),
    }
    json_write(context_dir / f"{context_id}.json", result)
    return result


def status(output: Path) -> dict[str, Any]:
    state = _load_state(output)
    next_chunk = next((item for item in state["chunks"] if item["status"] != "passed"), None)
    next_pack = next((item for item in state.get("review_packs", []) if item["status"] != "passed" and (not next_chunk or next_chunk["id"] in item.get("parse_batch_ids", []))), None)
    if state["status"] == "complete":
        next_action = "complete"
    elif next_chunk:
        next_action = "review-pack" if next_chunk["status"] == "awaiting-agent-review" and next_pack else "build-chunk"
    else:
        next_action = "finalize"
    return {**state, "next_action": next_action, "next_chunk": next_chunk["id"] if next_chunk else None, "next_review_pack": next_pack["id"] if next_pack else None}


def run_fast(
    *,
    repo: Path | None,
    output: Path,
    format_name: str | None,
    resume: bool,
    scope_paths: list[str],
    entries: list[str],
    expand_depth: int,
    expand_direction: str,
    includes: list[str],
    init_git: bool = False,
    initial_commit_message: str = DEFAULT_INITIAL_COMMIT_MESSAGE,
    git_author_name: str | None = None,
    git_author_email: str | None = None,
    csharp_solution: str | None = None,
    csharp_project: str | None = None,
    allow_dotnet_restore: bool = False,
    page_config_path: Path | None = None,
) -> dict[str, Any]:
    if resume and (init_git or git_author_name is not None or git_author_email is not None or csharp_solution is not None or csharp_project is not None or allow_dotnet_restore or page_config_path is not None):
        raise CkbError("repository initialization, C# project options, and --page-config apply only to the initial run, not --resume")
    if not resume:
        if repo is None or format_name is None:
            raise CkbError("--repo and --format are required for the initial run")
        initialize(
            repo,
            output,
            format_name,
            scope_paths,
            entries,
            expand_depth,
            expand_direction,
            includes,
            init_git=init_git,
            initial_commit_message=initial_commit_message,
            git_author_name=git_author_name,
            git_author_email=git_author_email,
            csharp_solution=csharp_solution,
            csharp_project=csharp_project,
            allow_dotnet_restore=allow_dotnet_restore,
            page_config_path=page_config_path,
        )
    current = status(output)
    if current["next_action"] == "build-chunk":
        build_chunk(output, current["next_chunk"], "all")
        refreshed = status(output)
        if refreshed.get("next_review_pack"):
            pack = _review_pack(refreshed, refreshed["next_review_pack"])
            raise ReviewRequired(pack["review_template_path"])
        raise ReviewRequired(str((output / "chunks" / current["next_chunk"] / "review-template.json").resolve()))
    if current["next_action"] == "review-pack":
        pack = _review_pack(current, current["next_review_pack"])
        raise ReviewRequired(pack["review_template_path"])
    return current
