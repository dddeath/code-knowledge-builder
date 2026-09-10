"""Incrementally migrate an audited CKB output onto a newer Git snapshot."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import shutil
import sqlite3
from typing import Any
from urllib.parse import quote, unquote

from . import SCHEMA_VERSION, VERSION
from .automation import initialize_automation_database
from .common import CkbError, json_load, json_write, safe_rmtree, sha256_file, utc_now, write_marker
from .gitrepo import blob_bytes_many
from .navigation import build_review_packs
from .pipeline import _replace_output_prefix, _write_review_pack_templates, build_chunk, initialize, review_pack


MIGRATION_SCHEMA_VERSION = 1
MUTABLE_BASELINE_DIRECTORY = "migration/preserved-baseline"
REFERENCE_STATUS_MARKERS = frozenset({
    "references/.failed", "references/.pending-agent-review", "references/.complete",
})


def _entity_key(entity: dict[str, Any]) -> tuple[Any, ...]:
    source_range = entity.get("range", {})
    return (
        entity.get("path"),
        entity.get("blob"),
        entity.get("kind"),
        entity.get("name"),
        entity.get("qualified_name"),
        source_range.get("start_byte"),
        source_range.get("end_byte"),
    )


def _review_shape(classification: str | None) -> str:
    return "appendix" if classification == "appendix" else "narrative"


def _review_for_new_entity(entity: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "entity_id": entity["id"],
        "classification": entity["classification"],
        "owner_page_id": entity["owner_page_id"],
        "source_path": entity["path"],
        "start_line": entity["range"]["start_line"],
        "end_line": entity["range"]["end_line"],
        "status": "agent-reviewed",
        "evidence_note": previous.get("evidence_note"),
    }
    if entity["classification"] == "appendix":
        item["description_zh"] = previous.get("description_zh")
    else:
        item.update(
            {
                "meaning_zh": previous.get("meaning_zh"),
                "role_zh": previous.get("role_zh"),
                "change_when_zh": previous.get("change_when_zh"),
            }
        )
    return item


def _copy_file(source: Path, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {
        "source": str(source.resolve()),
        "target": str(target.resolve()),
        "relative_target": target.as_posix(),
        "sha256": sha256_file(target),
        "size": target.stat().st_size,
    }


def _mutable_target(output: Path, relative_target: str) -> Path:
    """Resolve a migration-owned relative path without trusting stale absolutes."""
    target = (output / Path(relative_target.replace("\\", "/"))).resolve()
    try:
        target.relative_to(output.resolve())
    except ValueError as exc:
        raise CkbError(f"migration mutable path escapes output: {relative_target}") from exc
    return target


def _add_mutable_baseline(output: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Keep immutable proof of the bytes initially preserved by migration.

    The live note/database is intentionally mutable after migration because Hook
    ingestion, deterministic relinking, and Agent notes append to it.  Audits
    therefore validate this baseline plus the readability/integrity of the live
    file instead of freezing the live file at its migration-time hash.
    """
    relative_target = str(record["relative_target"])
    live_target = _mutable_target(output, relative_target)
    if record.get("kind") == "authoring-package-file":
        baseline_relative = f"{MUTABLE_BASELINE_DIRECTORY}/authoring/{sha256_file(live_target)}"
    elif record.get("kind") == "transaction-archive-file":
        baseline_relative = f"{MUTABLE_BASELINE_DIRECTORY}/transactions/{sha256_file(live_target)}"
    else:
        baseline_relative = f"{MUTABLE_BASELINE_DIRECTORY}/{relative_target}"
    baseline = _mutable_target(output, baseline_relative)
    baseline.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(live_target, baseline)
    record["baseline_relative_target"] = baseline_relative
    record["baseline_sha256"] = sha256_file(baseline)
    record["initial_target_sha256"] = sha256_file(live_target)
    return record


def _generated_paths(vault: Path) -> set[str]:
    manifest = vault / ".ckb-generated-files.json"
    files = set(json_load(manifest).get("files", [])) if manifest.is_file() else set()
    references = vault.parent / "references/projection.json"
    if references.is_file():
        files.update(json_load(references).get("files", []))
    return {str(value).replace("\\", "/") for value in files}


def _referenced_machine_evidence(previous_output: Path) -> list[Path]:
    """Collect the file closure referenced by retained records, not a history tree."""
    previous_output = previous_output.resolve()
    required: set[Path] = set()
    visited: set[Path] = set()
    pending: list[Path] = []
    # Canonical record stores are dependency roots; transaction snapshots and
    # generated reports under workspace-meta are retained, not reactivated.
    for directory in (
        "workspace-meta/notes", "workspace-meta/gaps/records",
        "workspace-meta/feedback/open", "workspace-meta/feedback/resolved",
        "references/manifests", "references/reviews",
    ):
        pending.extend(sorted((previous_output / directory).glob("*.json")))
    for path in sorted((previous_output / "workspace-meta/pending-notes").glob("*.json")):
        document = json_load(path)
        if isinstance(document, dict) and document.get("status") == "materialized":
            continue
        pending.append(path)
        if path.with_suffix(".md").is_file():
            pending.append(path.with_suffix(".md"))
    for vault in ("human", "markdown"):
        generated = _generated_paths(previous_output / vault)
        pending.extend(path for path in sorted((previous_output / vault).rglob("*.md"))
                       if path.relative_to(previous_output / vault).as_posix() not in generated)

    def consider(value: str, *, explicit: bool = False) -> None:
        value = unquote(value).replace("\\", "/")
        old = previous_output.as_posix()
        if value.startswith(old + "/"):
            value = value[len(old) + 1:]
        # External record queries remain external. Gap evidence is OUTPUT-relative.
        if not value.startswith("machine/"):
            if explicit and not Path(value).is_absolute() and not re.match(r"^[A-Za-z]:/", value):
                path = _mutable_target(previous_output, value)
                if not path.is_file():
                    raise CkbError(f"required migration evidence is missing: {value}")
            return
        path = _mutable_target(previous_output, value)
        if not path.is_file():
            raise CkbError(f"required migration evidence is missing: {value}")
        if path not in required:
            required.add(path)
            pending.append(path)

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for name, item in value.items():
                visit(item, name)
        elif isinstance(value, list):
            for item in value:
                visit(item, key)
        elif isinstance(value, str) and key in {
            "evidence_paths", "resolution_evidence_paths", "query_record",
            "from_pack", "from_query", "pack_path", "record_path", "evidence_file",
        }:
            consider(value, explicit=key in {"evidence_paths", "resolution_evidence_paths"})

    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        if path.suffix.casefold() == ".json":
            visit(json_load(path))
        elif path.suffix.casefold() == ".md":
            text = path.read_text(encoding="utf-8")
            # Backtick-delimited code is exposition, not a file dependency.
            text = re.sub(r"(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)", "", text)
            for value in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                link = unquote(value).split("#", 1)[0]
                if link.startswith("vscode://file/"):
                    link = re.sub(r":\d+:\d+$", "", link[len("vscode://file/"):])
                elif link.startswith("file://"):
                    link = link[len("file://"):]
                    if re.match(r"^/[A-Za-z]:/", link):
                        link = link[1:]
                elif link.startswith(("../", "./")):
                    link = str((path.parent / link).resolve())
                consider(link)
    return sorted(required)


def authoring_package_inventory(previous_output: Path) -> list[dict[str, Any]]:
    """Validate retained V3 records and enumerate only their package dependencies."""
    from .workspace_notes import note_contract_metadata, read_note_body

    packages: list[dict[str, Any]] = []
    for note_path in sorted((previous_output / "workspace-meta/notes").glob("*.json")):
        metadata = json_load(note_path)
        contract = metadata.get("human_output_contract") or {}
        if not (metadata.get("authoring_package") or metadata.get("section_evidence")
                or contract.get("v3_validated")):
            continue
        try:
            manifest_path = Path(metadata["authoring_package"]).resolve()
            if manifest_path.name != "manifest.json" or not manifest_path.is_file():
                raise CkbError("V3 authoring manifest is missing or not manifest.json")
            body_path = manifest_path.parent / "body.md"
            body = read_note_body(body_path)
            if hashlib.sha256((body.rstrip() + "\n").encode("utf-8")).hexdigest() != metadata.get("body_sha256"):
                raise CkbError("V3 record body digest differs from its authoring package")
            verified = note_contract_metadata(body_path, metadata["kind"], body)
            if not verified["human_output_contract"]["v3_validated"]:
                raise CkbError("retained V3 record has no validated authoring package")
            for field in ("validation_context", "section_evidence", "section_evidence_sha256"):
                if metadata.get(field) != verified[field]:
                    raise CkbError(f"V3 record and authoring package metadata drift: {field}")
            files: dict[str, dict[str, Any]] = {}

            def add(path: Path, role: str) -> None:
                if not path.resolve().is_relative_to(manifest_path.parent):
                    raise CkbError(f"V3 authoring file escapes its package: {path}")
                relative = path.relative_to(manifest_path.parent).as_posix()
                if relative not in files:
                    files[relative] = {"source": str(path), "relative_path": relative,
                                       "sha256": sha256_file(path), "roles": []}
                if role not in files[relative]["roles"]:
                    files[relative]["roles"].append(role)

            add(manifest_path, "manifest")
            add(body_path, "body")
            for section in verified["section_evidence"].get("sections", []):
                for field in ("source_refs", "machine_evidence_refs"):
                    for ref in section.get(field, []):
                        if ref.get("target_basis") == "uri":
                            continue
                        # The shared validator already checked containment and the declared digest.
                        add((manifest_path.parent / ref["target"]).resolve(), field)
            digest = files["manifest.json"]["sha256"]
            if (manifest_path.parent.parent == (previous_output / "machine/authoring").resolve()
                    and manifest_path.parent.name != digest[:20]):
                raise CkbError("V3 archived authoring manifest digest drift")
            packages.append({
                "note_relative": note_path.relative_to(previous_output).as_posix(),
                "source_manifest": str(manifest_path),
                "archive_relative": f"machine/authoring/{digest[:20]}",
                "files": [files[key] for key in sorted(files)],
            })
        except (CkbError, OSError, KeyError, TypeError, ValueError) as exc:
            raise CkbError(f"V3 authoring package preflight failed for {note_path.name}: {exc}") from exc
    return packages


def _preserve_mutable_layers(
    previous_output: Path, output: Path, *, authoring_packages: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    packages = authoring_package_inventory(previous_output) if authoring_packages is None else authoring_packages
    package_sources = {item["source"] for package in packages for item in package["files"]}
    evidence = _referenced_machine_evidence(previous_output)
    records: list[dict[str, Any]] = []
    for root_name in ("human", "markdown"):
        source_root = previous_output / root_name
        if not source_root.is_dir():
            continue
        generated = _generated_paths(source_root)
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(source_root).as_posix()
            if relative == ".ckb-generated-files.json" or relative in generated:
                continue
            target = output / root_name / relative
            record = _copy_file(source, target)
            record["kind"] = "vault-user-file"
            record["relative_target"] = f"{root_name}/{relative}"
            records.append(_add_mutable_baseline(output, record))
    # The mutable machine layer is intentionally copied as one bounded tree.
    # It includes work records, pending/session notes, feedback, research gaps,
    # operation journal shards, Agent protocol bindings and automation state.
    # Fixed source facts and the two searchable indexes are rebuilt elsewhere.
    source_root = previous_output / "workspace-meta"
    if source_root.is_dir():
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(source_root)
            target = output / "workspace-meta" / relative
            record = _copy_file(source, target)
            record["kind"] = (
                "transaction-archive-file" if relative.parts[:1] == ("record-replace",)
                else "authoring-package-file" if record["source"] in package_sources else "workspace-mutable-file"
            )
            record["relative_target"] = target.relative_to(output).as_posix()
            records.append(_add_mutable_baseline(output, record))
    # Reviewed external references own archived raw bytes, manifests and Agent
    # reviews under OUTPUT/references.  Human reference pages are projections
    # and will be regenerated from this preserved source layer.
    source_root = previous_output / "references"
    if source_root.is_dir():
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(source_root)
            target = output / "references" / relative
            record = _copy_file(source, target)
            record["kind"] = (
                "reference-status-marker" if target.relative_to(output).as_posix() in REFERENCE_STATUS_MARKERS
                else "reviewed-reference-source"
            )
            record["relative_target"] = target.relative_to(output).as_posix()
            records.append(_add_mutable_baseline(output, record))
    old_database = previous_output / "machine" / "automation.sqlite"
    if old_database.is_file():
        new_database = output / "machine" / "automation.sqlite"
        new_database.parent.mkdir(parents=True, exist_ok=True)
        source_connection = sqlite3.connect(f"file:{old_database.as_posix()}?mode=ro", uri=True)
        target_connection = sqlite3.connect(new_database)
        try:
            source_connection.backup(target_connection)
            target_connection.commit()
        finally:
            target_connection.close()
            source_connection.close()
        initialize_automation_database(output)
        records.append(
            _add_mutable_baseline(
                output,
                {
                    "kind": "automation-database-backup",
                    "source": str(old_database.resolve()),
                    "target": str(new_database.resolve()),
                    "relative_target": new_database.relative_to(output).as_posix(),
                    "sha256": sha256_file(new_database),
                    "size": new_database.stat().st_size,
                },
            )
        )
    copied = {record["relative_target"] for record in records}
    for source in evidence:
        relative = source.relative_to(previous_output).as_posix()
        if relative in copied:
            continue
        target = output / relative
        if relative == "machine/knowledge.sqlite":
            raise CkbError("required migration evidence is a rebuilt live index; archive a fixed evidence file first")
        if target.is_file() and sha256_file(target) != sha256_file(source):
            raise CkbError(f"required migration evidence conflicts with target artifact: {relative}")
        record = _copy_file(source, target)
        record.update(kind="referenced-machine-evidence", relative_target=relative)
        records.append(_add_mutable_baseline(output, record))
    # Archive selected package files byte-for-byte; neither the signed manifest
    # nor its context/evidence is a mutable output-path document.
    archived: set[str] = set()
    for package in packages:
        for item in package["files"]:
            source = Path(item["source"])
            if not source.is_file() or sha256_file(source) != item["sha256"]:
                raise CkbError(f"V3 authoring package changed during migration: {source}")
            relative = package["archive_relative"] + "/" + item["relative_path"]
            target = _mutable_target(output, relative)
            if target.exists() and sha256_file(target) != item["sha256"]:
                raise CkbError(f"V3 authoring archive conflicts with target: {relative}")
            if relative in archived:
                continue
            record = _copy_file(source, target)
            record.update(kind="authoring-package-file", relative_target=relative,
                          roles=item["roles"], package_manifest=package["archive_relative"] + "/manifest.json")
            records.append(_add_mutable_baseline(output, record))
            archived.add(relative)
    # Existing OUTPUT-owned copies remain frozen too, even if the note now
    # points to the selected archive instead of its old workspace directory.
    for record in records:
        if record["source"] in package_sources:
            record["kind"] = "authoring-package-file"
    # Rebase live metadata only. Baselines, archived originals and evidence keep
    # their original bytes; historical prose is not a serialized path.
    for record in records:
        relative = str(record["relative_target"])
        if (record["kind"] in {"authoring-package-file", "transaction-archive-file"} or not relative.endswith(".json")
                or not relative.startswith("workspace-meta/")):
            continue
        target = output / relative
        document = json_load(target)
        updated = _replace_output_prefix(document, str(previous_output), str(output))
        if updated != document:
            json_write(target, updated)
    for package in packages:
        note_path = output / package["note_relative"]
        metadata = json_load(note_path)
        metadata["authoring_package"] = str((output / package["archive_relative"] / "manifest.json").resolve())
        json_write(note_path, metadata)
    if (output / "references/manifests").is_dir():
        from .reference_documents import relocate_reference_paths

        relocate_reference_paths(output, str(previous_output), str(output))
    if (output / "references/manifests").is_dir() and (output / "state.json").is_file():
        from .reference_documents import _project_reference_pages

        _project_reference_pages(output)
    return records


def _selected_entities(output: Path) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    catalog = json_load(output / "catalog.json")
    scope = json_load(output / "scope.json")
    boundary = json_load(output / "boundary.json")
    selected_ids = set(scope["selected_entity_ids"])
    by_id = {entity["id"]: entity for entity in catalog["entities"] if entity["id"] in selected_ids}
    by_id.update({entity["id"]: entity for entity in boundary.get("entities", [])})
    entities = [by_id[value] for value in sorted(selected_ids)]
    file_by_path = {item["file"]["path"]: item["file"] for item in catalog["files"]}
    files = [file_by_path[path] for path in sorted({entity["path"] for entity in entities})]
    state = json_load(output / "state.json")
    sources = blob_bytes_many(state["repository"], files)
    return entities, sources


def _replace_review_packs(
    output: Path,
    reusable_reviews: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    state = json_load(output / "state.json")
    entities, sources = _selected_entities(output)
    by_id = {entity["id"]: entity for entity in entities}
    reusable_entities = [entity for entity in entities if entity["id"] in reusable_reviews]
    delta_entities = [entity for entity in entities if entity["id"] not in reusable_reviews]
    page_config = json_load(output / state["page_config"]["relative_path"])
    migrated = build_review_packs(state["parse_batches"], reusable_entities, page_config)
    delta = build_review_packs(state["parse_batches"], delta_entities, page_config)
    for pack in migrated:
        pack["id"] = f"migrated-{pack['id']}"
        pack["status"] = "planned"
    for pack in delta:
        pack["id"] = f"delta-{pack['id']}"
        pack["status"] = "planned"
    safe_rmtree(output / "review-packs", output)
    (output / "review-packs").mkdir(parents=True)
    state["review_packs"] = [*migrated, *delta]
    state["status"] = "awaiting-agent-review"
    json_write(output / "state.json", state)
    _write_review_pack_templates(output, state["review_packs"], entities, sources)
    json_write(output / "state.json", state)
    for pack in migrated:
        review_document = {
            "schema_version": SCHEMA_VERSION,
            "pack_id": pack["id"],
            "kind": pack["kind"],
            "reviewer": "Agent（经精确源码证据迁移）",
            "reviewed_at_utc": utc_now(),
            "reviews": [reusable_reviews[entity_id] for entity_id in pack["entity_ids"]],
        }
        review_path = output / "migration" / "reused-reviews" / f"{pack['id']}.json"
        json_write(review_path, review_document)
        review_pack(output, pack["id"], review_path)
    # Reopen the templates after review_pack state rewrites and leave a single
    # explicit checkpoint pointing at the first delta unit.
    refreshed = json_load(output / "state.json")
    pending = [pack for pack in refreshed["review_packs"] if pack["status"] != "passed"]
    if pending:
        write_marker(
            output,
            ".pending-agent-review",
            {
                "status": "migration-delta-review-required",
                "next_review_pack": pending[0]["id"],
                "review_template": pending[0]["review_template_path"],
            },
        )
    return [entity["id"] for entity in reusable_entities], [entity["id"] for entity in delta_entities]


def migrate_output(previous_output: Path, repository: Path, output: Path, format_name: str | None = None) -> dict[str, Any]:
    previous_output = previous_output.resolve()
    repository = repository.resolve()
    output = output.resolve()
    old_state = json_load(previous_output / "state.json")
    old_scope = json_load(previous_output / "scope.json")
    old_graph = json_load(previous_output / "graph.json")
    if old_state.get("status") != "complete" or json_load(previous_output / "audit" / "global.json").get("status") != "passed":
        raise CkbError(f"migration origin is not globally audited: {previous_output}")
    packages = authoring_package_inventory(previous_output)
    _referenced_machine_evidence(previous_output)
    selectors = old_scope.get("selectors", {})
    initialize(
        repository,
        output,
        format_name or old_state["format"],
        list(selectors.get("scope_paths") or []),
        list(selectors.get("entries") or []),
        int(selectors.get("expand_depth", 1)),
        str(selectors.get("expand_direction", "both")),
        list(selectors.get("include") or []),
        csharp_solution=selectors.get("csharp_solution"),
        csharp_project=selectors.get("csharp_project"),
        allow_dotnet_restore=bool(selectors.get("allow_dotnet_restore", False)),
        page_config_path=previous_output / "page-config.json",
        reuse_from_output=previous_output,
    )
    preserved = _preserve_mutable_layers(previous_output, output, authoring_packages=packages)
    state = json_load(output / "state.json")
    catalog = json_load(output / "catalog.json")
    reuse_paths = set((catalog.get("migration_reuse") or {}).get("reused_file_paths", []))
    migration = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "mode": "incremental-exact-blob",
        "origin_output": str(previous_output),
        "origin_version": old_state.get("version"),
        "origin_commit": old_state.get("repository", {}).get("commit"),
        "target_version": VERSION,
        "target_commit": state["repository"]["commit"],
        "started_at_utc": utc_now(),
    }
    state["migration"] = migration
    json_write(output / "state.json", state)
    for batch in state["parse_batches"]:
        build_chunk(output, batch["id"], "all")
    new_entities, _sources = _selected_entities(output)
    old_by_key = {_entity_key(entity): entity for entity in old_graph.get("entities", [])}
    reusable_reviews: dict[str, dict[str, Any]] = {}
    id_map: dict[str, str] = {}
    for entity in new_entities:
        if entity["path"] not in reuse_paths:
            continue
        previous = old_by_key.get(_entity_key(entity))
        if not previous or previous.get("review_status") != "agent-reviewed":
            continue
        if _review_shape(previous.get("classification")) != _review_shape(entity.get("classification")):
            continue
        reusable_reviews[entity["id"]] = _review_for_new_entity(entity, previous)
        id_map[str(previous["id"])] = entity["id"]
    reused_ids, delta_ids = _replace_review_packs(output, reusable_reviews)
    final_state = json_load(output / "state.json")
    final_state["migration"] = {
        **migration,
        "reused_file_paths": sorted(reuse_paths),
        "reused_file_count": len(reuse_paths),
        "reused_review_entity_count": len(reused_ids),
        "delta_review_entity_count": len(delta_ids),
        "preserved_mutable_file_count": len(preserved),
        "status": "pending-agent-review" if delta_ids else "ready-to-finalize",
    }
    json_write(output / "state.json", final_state)
    plan = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": final_state["migration"]["status"],
        "origin": {
            "output": str(previous_output),
            "version": old_state.get("version"),
            "commit": old_state.get("repository", {}).get("commit"),
        },
        "target": {
            "output": str(output),
            "version": VERSION,
            "repository": str(repository),
            "commit": final_state["repository"]["commit"],
        },
        "files": {
            "reused": sorted(reuse_paths),
            "reused_count": len(reuse_paths),
            "parsed_count": int((catalog.get("migration_reuse") or {}).get("parsed_file_count", 0)),
        },
        "entities": {
            "reused_review_count": len(reused_ids),
            "delta_review_count": len(delta_ids),
            "old_to_new_id_map": id_map,
        },
        "mutable_files": preserved,
        "created_at_utc": utc_now(),
    }
    json_write(output / "migration" / "plan.json", plan)
    audit = audit_migration(output, require_complete_reviews=False)
    return {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": plan["status"],
        "output": str(output),
        "plan": str((output / "migration" / "plan.json").resolve()),
        "audit": audit,
        "reused_file_count": len(reuse_paths),
        "reused_review_entity_count": len(reused_ids),
        "delta_review_entity_count": len(delta_ids),
        "next_review_pack": next(
            (pack["id"] for pack in final_state["review_packs"] if pack["status"] != "passed"),
            None,
        ),
    }


def audit_migration(output: Path, *, require_complete_reviews: bool = True) -> dict[str, Any]:
    output = output.resolve()
    state = json_load(output / "state.json")
    plan_path = output / "migration" / "plan.json"
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("migration-plan-present", plan_path.is_file(), str(plan_path))
    if not plan_path.is_file():
        result = {"schema_version": MIGRATION_SCHEMA_VERSION, "status": "failed", "checks": checks, "audited_at_utc": utc_now()}
        json_write(output / "migration" / "audit.json", result)
        return result
    plan = json_load(plan_path)
    migration = state.get("migration") or {}
    check("target-version-current", state.get("version") == VERSION and migration.get("target_version") == VERSION, {"state": state.get("version"), "target": migration.get("target_version")})
    check("target-commit-pinned", state.get("repository", {}).get("commit") == plan.get("target", {}).get("commit"), state.get("repository", {}).get("commit"))
    catalog = json_load(output / "catalog.json")
    reused_paths = set(plan.get("files", {}).get("reused", []))
    catalog_reused = set((catalog.get("migration_reuse") or {}).get("reused_file_paths", []))
    check("exact-blob-reuse-set", reused_paths == catalog_reused, {"missing": sorted(reused_paths - catalog_reused), "extra": sorted(catalog_reused - reused_paths)})
    reused_records = {
        item["file"]["path"]: item
        for item in catalog.get("files", [])
        if item["file"]["path"] in reused_paths
    }
    reuse_errors = [
        path
        for path in sorted(reused_paths)
        if path not in reused_records or not reused_records[path].get("migration_reuse")
    ]
    check("reused-files-carry-rekey-proof", not reuse_errors, reuse_errors)
    mutable_errors: list[dict[str, Any]] = []
    retired_reference_status_markers: list[str] = []
    for item in plan.get("mutable_files", []):
        relative_target = str(item.get("relative_target") or "")
        baseline_relative = str(item.get("baseline_relative_target") or "")
        try:
            target = _mutable_target(output, relative_target)
            baseline = _mutable_target(output, baseline_relative)
        except CkbError as exc:
            mutable_errors.append({"path": relative_target, "reason": str(exc)})
            continue
        expected_baseline = item.get("baseline_sha256")
        if not baseline.is_file() or not expected_baseline or sha256_file(baseline) != expected_baseline:
            mutable_errors.append({"path": relative_target, "reason": "preserved-baseline-missing-or-changed"})
            continue
        # Reference audits replace these three mutually exclusive generated
        # markers. Keep their original bytes, not their obsolete live presence.
        # Legacy staging plans classified the same paths as reference sources.
        reference_marker = (
            target.relative_to(output).as_posix() in REFERENCE_STATUS_MARKERS
            and item.get("kind") in {"reference-status-marker", "reviewed-reference-source"}
        )
        if reference_marker and not target.exists():
            retired_reference_status_markers.append(target.relative_to(output).as_posix())
            continue
        if not target.is_file():
            mutable_errors.append({"path": relative_target, "reason": "live-mutable-file-missing"})
            continue
        if item.get("kind") in {"referenced-machine-evidence", "authoring-package-file", "transaction-archive-file"} and sha256_file(target) != expected_baseline:
            mutable_errors.append({"path": relative_target, "reason": "referenced-machine-evidence-changed"})
            continue
        try:
            suffix = target.suffix.casefold()
            if suffix == ".json" or reference_marker:
                json_load(target)
            elif suffix == ".md":
                target.read_text(encoding="utf-8")
            elif suffix in {".sqlite", ".db"}:
                connection = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
                try:
                    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                finally:
                    connection.close()
                if integrity != "ok":
                    raise CkbError(f"SQLite integrity_check returned {integrity}")
            else:
                target.read_bytes()
        except (CkbError, OSError, UnicodeError, json.JSONDecodeError, sqlite3.Error) as exc:
            mutable_errors.append({"path": relative_target, "reason": "live-mutable-file-invalid", "detail": str(exc)})
    check("mutable-layers-preserved", not mutable_errors, mutable_errors)
    review_status = {pack["id"]: pack.get("status") for pack in state.get("review_packs", [])}
    reviews_complete = bool(review_status) and all(value == "passed" for value in review_status.values())
    check("migration-review-state", reviews_complete if require_complete_reviews else True, review_status)
    graph_path = output / "graph.json"
    graph_errors: list[Any] = []
    if graph_path.is_file():
        graph = json_load(graph_path)
        target_commit = state["repository"]["commit"]
        id_map = plan.get("entities", {}).get("old_to_new_id_map", {})
        # A CKB-version-only migration may retain the same fixed Git commit.
        # In that case commit-sensitive IDs are intentionally identical and
        # are not obsolete IDs.  Only mappings whose target actually changed
        # may be treated as forbidden old-ID residue.
        old_ids = {old for old, new in id_map.items() if old != new}
        new_ids = {entity["id"] for entity in graph.get("entities", [])}
        if old_ids & new_ids:
            graph_errors.append({"reason": "old-entity-id-remains", "ids": sorted(old_ids & new_ids)[:20]})
        wrong_commit = [entity["id"] for entity in graph.get("entities", []) if entity.get("commit") != target_commit]
        if wrong_commit:
            graph_errors.append({"reason": "entity-commit-mismatch", "ids": wrong_commit[:20]})
    elif require_complete_reviews:
        graph_errors.append({"reason": "graph-not-merged"})
    check("target-graph-has-only-new-provenance", not graph_errors, graph_errors)
    all_checks_passed = all(item["passed"] for item in checks)
    if all_checks_passed and reviews_complete:
        status = "passed"
    elif all_checks_passed and not require_complete_reviews:
        status = "pending-agent-review"
    else:
        status = "failed"
    result = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": status,
        "checks": checks,
        "counts": {"passed": sum(item["passed"] for item in checks), "total": len(checks)},
        "retired_reference_status_markers": sorted(retired_reference_status_markers),
        "audited_at_utc": utc_now(),
    }
    if status == "passed":
        plan["status"] = "passed"
        json_write(plan_path, plan)
        state["migration"] = {**migration, "status": "passed", "audited_at_utc": result["audited_at_utc"]}
        json_write(output / "state.json", state)
    json_write(output / "migration" / "audit.json", result)
    return result


def _semantic_page_key(entity: dict[str, Any]) -> tuple[str, str, str]:
    kind = "file" if entity.get("kind") == "file" else str(entity.get("kind_original") or entity.get("kind"))
    return (str(entity.get("path")), kind, str(entity.get("qualified_name") or entity.get("name")))


def relink_preserved_notes(output: Path, graph: dict[str, Any], projection: dict[str, Any]) -> dict[str, Any]:
    """Retarget preserved Wiki links after deterministic human titles change."""
    output = output.resolve()
    plan_path = output / "migration" / "plan.json"
    if not plan_path.is_file():
        return {"schema_version": MIGRATION_SCHEMA_VERSION, "status": "not-applicable", "changed_files": []}
    plan = json_load(plan_path)
    origin = Path(plan["origin"]["output"])
    old_graph_path = origin / "graph.json"
    old_projection_path = origin / "markdown" / "projection.json"
    if not old_graph_path.is_file() or not old_projection_path.is_file():
        raise CkbError(f"migration note relink requires the origin graph and Markdown projection: {origin}")
    old_graph = json_load(old_graph_path)
    old_projection = json_load(old_projection_path)
    old_entities = {entity["id"]: entity for entity in old_graph.get("entities", [])}
    new_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for entity in graph.get("entities", []):
        new_by_key.setdefault(_semantic_page_key(entity), []).append(entity)
    new_pages = {page["id"]: page for page in projection.get("pages", [])}
    old_owners = old_projection.get("entity_owner_pages", {})
    new_owners = projection.get("entity_owner_pages", {})
    title_map: dict[str, str] = {}
    unresolved: list[dict[str, Any]] = []

    def owner_for(old_entity: dict[str, Any]) -> str | None:
        matches = new_by_key.get(_semantic_page_key(old_entity), [])
        if len(matches) != 1:
            return None
        entity = matches[0]
        owner = new_owners.get(entity["id"]) or entity.get("owner_page_id") or entity["id"]
        return owner if owner in new_pages else None

    new_modules: dict[str, set[str]] = {}
    for link in projection.get("links", []):
        if link.get("type") == "contains-file":
            new_modules.setdefault(link["target"], set()).add(link["source"])
    for page in old_projection.get("pages", []):
        old_title = page.get("title")
        if not old_title:
            continue
        old_entity = old_entities.get(page.get("id"))
        candidates: list[str | None] = []
        if old_entity:
            candidates = [owner_for(old_entity)]
        elif page.get("page_type") == "boundary":
            members = [entity for entity in old_entities.values() if old_owners.get(entity["id"]) == page["id"]]
            candidates = [owner_for(entity) for entity in members]
        elif page.get("page_type") == "module":
            members = [old_entities.get(link["target"]) for link in old_projection.get("links", [])
                       if link.get("type") == "contains-file" and link.get("source") == page["id"]]
            for entity in members:
                modules = new_modules.get(owner_for(entity), set()) if entity else set()
                candidates.append(next(iter(modules)) if len(modules) == 1 else None)
        elif page.get("page_type") == "repository":
            old_root = old_graph.get("repository", {}).get("root")
            new_root = graph.get("repository", {}).get("root")
            if old_root and new_root and Path(old_root).resolve() == Path(new_root).resolve():
                candidates = [key for key, value in new_pages.items() if value.get("page_type") == "repository"]
        if not candidates or None in candidates or len(set(candidates)) != 1:
            unresolved.append({"old_title": old_title, "reason": "no-unique-semantic-owner"})
            continue
        new_title = new_pages[candidates[0]]["title"]
        if old_title != new_title:
            title_map[str(old_title)] = str(new_title)

    def replace_links(text: str) -> str:
        # One substitution pass avoids A->B->C cascades. Only actual Wiki-link
        # targets change; prose, aliases, inline code and fenced examples stay.
        lines = []
        fence = None
        for line in text.splitlines(keepends=True):
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if marker:
                token = marker.group(1)
                if fence is None:
                    fence = token
                elif token[0] == fence[0] and len(token) >= len(fence):
                    fence = None
                lines.append(line)
                continue
            if fence is not None:
                lines.append(line)
                continue
            parts = re.split(r"(`+[^`]*`+)", line)
            for index in range(0, len(parts), 2):
                parts[index] = re.sub(r"\[\[([^\]|#]+)([^\]]*)\]\]",
                    lambda match: "[[" + title_map.get(match.group(1), match.group(1)) + match.group(2) + "]]", parts[index])
            lines.append("".join(parts))
        return "".join(lines)

    changed: list[str] = []
    for item in plan.get("mutable_files", []):
        if item.get("kind") in {"referenced-machine-evidence", "authoring-package-file", "transaction-archive-file"}:
            continue
        target = _mutable_target(output, str(item["relative_target"]))
        if not target.is_file():
            continue
        if (plan.get("note_relink", {}).get("title_map") == title_map
                and item.get("post_migration_sha256") == sha256_file(target)):
            continue
        if target.suffix.casefold() == ".md":
            text = target.read_bytes().decode("utf-8")
            updated = replace_links(text)
            if updated != text:
                target.write_bytes(updated.encode("utf-8"))
                changed.append(item["relative_target"])
        elif target.suffix.casefold() == ".json" and "workspace-meta" in target.parts:
            try:
                value = json_load(target)
            except (json.JSONDecodeError, OSError):
                continue
            updated = False
            linked = value.get("linked_pages")
            if isinstance(linked, list):
                replacement = [title_map.get(str(page), str(page)) for page in linked]
                if replacement != linked:
                    value["linked_pages"] = replacement
                    updated = True
            for field, root_name in (("file", "human"), ("compatibility_file", "markdown")):
                current = value.get(field)
                if isinstance(current, str):
                    candidate = output / root_name / Path(current.replace("\\", "/")).name
                    kind = str(value.get("kind") or "session")
                    directory = {"change": "changes", "analysis": "analysis", "pitfall": "pitfalls", "experiment": "experiments", "session": "sessions"}.get(kind, "user")
                    candidate = output / root_name / directory / candidate.name
                    rendered = str(candidate.resolve())
                    if rendered != current:
                        value[field] = rendered
                        updated = True
            if isinstance(value.get("compatibility_file"), str):
                uri = "obsidian://open?path=" + quote(value["compatibility_file"], safe="")
                if value.get("obsidian_uri") != uri:
                    value["obsidian_uri"] = uri
                    updated = True
            if updated:
                json_write(target, value)
                changed.append(item["relative_target"])
        item["post_migration_sha256"] = sha256_file(target)
        item["post_migration_size"] = target.stat().st_size
    plan["note_relink"] = {
        "status": "passed",
        "title_map": title_map,
        "unresolved_titles": unresolved,
        "changed_files": sorted(set(changed)),
        "updated_at_utc": utc_now(),
    }
    json_write(plan_path, plan)
    result = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": "passed",
        "title_map_count": len(title_map),
        "changed_files": sorted(set(changed)),
        "title_map": title_map,
        "unresolved_titles": unresolved,
    }
    json_write(output / "migration" / "note-relink.json", result)
    return result


def migration_status(output: Path) -> dict[str, Any]:
    output = output.resolve()
    state = json_load(output / "state.json")
    migration = state.get("migration")
    if not migration:
        raise CkbError(f"output is not an incremental migration: {output}")
    pending = [pack for pack in state.get("review_packs", []) if pack.get("status") != "passed"]
    audit = audit_migration(output, require_complete_reviews=False)
    if state.get("status") == "complete" and audit.get("status") == "passed":
        status = "complete"
    else:
        status = "pending-agent-review" if pending else "ready-to-finalize"
    return {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": status,
        "migration": migration,
        "pending_review_packs": [pack["id"] for pack in pending],
        "next_review_template": pending[0].get("review_template_path") if pending else None,
        "audit": audit,
    }
