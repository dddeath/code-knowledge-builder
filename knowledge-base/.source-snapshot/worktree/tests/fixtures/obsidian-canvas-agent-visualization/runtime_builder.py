"""在 Windows runtime 中实例化无绝对根的 CKB Canvas fixture。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
from typing import Any


FIXTURE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = FIXTURE_ROOT.parents[2]
SKILL_ROOT = REPO_ROOT / "prototypes" / "ckb-canvas-skill"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remove_tree(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)


def _link_directory(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError:
        pass
    if os.name != "nt":
        raise OSError("directory symlink is unavailable")
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise OSError(completed.stderr or completed.stdout or "mklink /J failed")


@dataclass
class FixtureCase:
    root: Path
    output: Path
    human: Path
    snapshot: Path
    staging: Path
    target: Path
    request: Path
    record: Path
    pack: Path
    source: Path
    original_roles: dict[str, bytes | None]

    @property
    def validation(self) -> Path:
        return Path(str(self.target.resolve()) + ".validation.json")

    @property
    def rollback_manifest(self) -> Path:
        return Path(str(self.target.resolve()) + ".rollback.json")

    def request_value(self) -> dict[str, Any]:
        return json.loads(self.request.read_text(encoding="utf-8"))

    def write_request(self, value: dict[str, Any]) -> None:
        write_json(self.request, value)

    def cleanup(self) -> None:
        remove_tree(self.root)


def _case_root(case_id: str, explicit_root: Path | None) -> Path:
    if explicit_root is not None:
        return explicit_root.resolve()
    return Path(tempfile.gettempdir()) / "ckb-canvas-fixtures" / case_id


def build_case(
    case_id: str,
    *,
    explicit_root: Path | None = None,
    page_count: int = 1,
    record_count: int = 1,
    source_count: int = 1,
    replace: bool = False,
    long_target: bool = False,
    link_mode: str | None = None,
) -> FixtureCase:
    """创建一个完整 runtime request；不扫描仓库或活动知识库。"""

    root = _case_root(case_id, explicit_root)
    remove_tree(root)
    output = root / "output"
    human = output / "human"
    packs = output / "machine" / "agent-packs"
    snapshot = output / ".source-snapshot" / "worktree"
    staging = root / "交付暂存"
    outside = root / "outside"
    for path in (human / "pages", human / "sessions", packs, snapshot / "scripts", staging, outside):
        path.mkdir(parents=True, exist_ok=True)

    commit = "1" * 40
    tree = "2" * 40
    index = human / "INDEX.md"
    index.write_text("# CKB Canvas Fixture\n", encoding="utf-8", newline="\n")

    human_paths = ["INDEX.md"]
    entities: list[dict[str, Any]] = []
    source_evidence: list[dict[str, str]] = []
    first_source = snapshot / "scripts" / "source-00.py"
    for ordinal in range(page_count):
        page_rel = f"pages/page-{ordinal:02d}.md"
        page_path = human.joinpath(*page_rel.split("/"))
        page_path.write_text(f"# Page {ordinal}\n\n冻结人类页 {ordinal}。\n", encoding="utf-8", newline="\n")
        human_paths.append(page_rel)
        source_rel = f"scripts/source-{ordinal:02d}.py"
        source_path = snapshot.joinpath(*source_rel.split("/"))
        source_path.write_text(
            f"def function_{ordinal}():\n    value = {ordinal}\n    return value\n\n",
            encoding="utf-8",
            newline="\n",
        )
        if ordinal == 0:
            first_source = source_path
        if ordinal < source_count:
            source_evidence.append({"relative_path": source_rel, "sha256": sha256(source_path)})
        entities.append(
            {
                "entity_id": f"entity-{ordinal}",
                "name": f"function_{ordinal}",
                "qualified_name": f"function_{ordinal}",
                "kind": "function",
                "source_path": source_rel,
                "start_line": 1,
                "end_line": 3,
                "human_page_title": f"Page {ordinal}",
                "human_page_file": page_rel,
                "display_mode": "page",
                "score": 1.0 - ordinal / 100,
                "score_breakdown": {},
                "reasons": ["fixture"],
                "sections": [],
            }
        )

    documents: list[dict[str, Any]] = []
    for ordinal in range(record_count):
        record_rel = f"sessions/record-{ordinal:02d}.md"
        record_file = human.joinpath(*record_rel.split("/"))
        record_file.write_text(f"# Record {ordinal}\n\n已审阅记录 {ordinal}。\n", encoding="utf-8", newline="\n")
        human_paths.append(record_rel)
        documents.append(
            {
                "document_id": f"document-{ordinal}",
                "title": f"Record {ordinal}",
                "kind": "session",
                "status": "agent-reviewed",
                "human_file": record_rel,
                "source_path": None,
                "start_line": None,
                "end_line": None,
                "severity": None,
                "target": None,
                "content_excerpt": "已审阅记录",
            }
        )

    projection = {
        "pages": [{"file": f"pages/page-{ordinal:02d}.md"} for ordinal in range(page_count)],
        "work_record_index": {"file": "sessions/record-00.md"} if record_count else {},
        "generated_ownership": {"schema_version": 1, "status": "ready", "files": human_paths},
    }
    write_json(human / "projection.json", projection)
    write_json(human / "manifest.json", {"schema_version": 1, "status": "ready", "generated_files": human_paths})
    write_json(
        output / "state.json",
        {
            "schema_version": 4,
            "status": "complete",
            "repository": {"root": str(root / "repo"), "commit": commit, "tree": tree},
            "source_snapshot": {"status": "ready", "root": str(snapshot), "commit": commit, "tree": tree},
        },
    )
    write_json(
        output / "local-openers.json",
        {
            "schema_version": 1,
            "source_editor": "vscode",
            "working_repo_root": str(snapshot),
            "baseline_snapshot_root": str(snapshot),
            "source_view": "baseline",
            "show_source_range": True,
            "custom_template": None,
        },
    )

    machine_index = output / "machine" / "knowledge.sqlite"
    connection = sqlite3.connect(machine_index)
    try:
        connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO meta(key,value) VALUES(?,?)",
            [("status", "ready"), ("schema_version", "3"), ("repository_commit", commit)],
        )
        connection.commit()
    finally:
        connection.close()

    pack = packs / "pack-fixture.md"
    pack.write_text("# Agent Pack\n\n冻结检索证据。\n", encoding="utf-8", newline="\n")
    record_path = packs / "pack-fixture.json"
    record_value = {
        "schema_version": 3,
        "status": "passed",
        "question": "fixture question",
        "profile": "fast",
        "budget": 1800,
        "estimated_tokens": 200,
        "terms": ["fixture"],
        "anchors": [],
        "seed_entity_ids": [],
        "selected_entities": entities,
        "related_documents": documents,
        "open_feedback": 0,
        "pack": str(pack),
        "record": str(record_path),
        "retrieval": {"status": "passed"},
        "deterministic": True,
        "source_grounded": True,
        "grep_fallback_required": False,
    }
    write_json(record_path, record_value)

    target_parent = staging
    if long_target:
        current = len(str(staging / "ckb-navigation.canvas"))
        index = 0
        while current < 250:
            component = (f"segment-{index:02d}-" + "x" * 35)[:48]
            candidate = target_parent / component
            if len(str(candidate / "ckb-navigation.canvas")) > 259:
                remaining = 255 - len(str(target_parent / "" / "ckb-navigation.canvas"))
                component = "z" * max(1, min(remaining, 48))
                candidate = target_parent / component
            target_parent = candidate
            current = len(str(target_parent / "ckb-navigation.canvas"))
            index += 1
        target_parent.mkdir(parents=True, exist_ok=True)
    if link_mode:
        link = staging / "linked"
        target_dir = (staging / "inside") if link_mode == "inside" else outside
        target_dir.mkdir(parents=True, exist_ok=True)
        _link_directory(link, target_dir)
        target_parent = link
    target = target_parent / "ckb-navigation.canvas"

    role_paths = {
        "canvas": target,
        "validation_manifest": Path(str(target) + ".validation.json"),
        "rollback_manifest": Path(str(target) + ".rollback.json"),
    }
    originals: dict[str, bytes | None] = {role: None for role in role_paths}
    if replace:
        originals = {
            "canvas": canonical(
                {
                    "nodes": [
                        {"id": "0123456789abcdef", "type": "text", "x": 0, "y": 0, "width": 10, "height": 10, "text": "baseline"}
                    ],
                    "edges": [],
                }
            ),
            "validation_manifest": b"baseline-validation\n",
            "rollback_manifest": b"baseline-rollback\n",
        }
        for role, data in originals.items():
            role_paths[role].parent.mkdir(parents=True, exist_ok=True)
            role_paths[role].write_bytes(data or b"")

    baselines: dict[str, dict[str, str]] = {}
    for role, role_path in role_paths.items():
        if replace:
            baselines[role] = {"state": "present", "sha256": sha256(role_path)}
        else:
            baselines[role] = {"state": "absent"}
    human_evidence = [
        {"relative_path": relative, "sha256": sha256(human.joinpath(*relative.split("/")))} for relative in human_paths
    ]
    ckb = {
        "output_root": str(output),
        "state_path": str(output / "state.json"),
        "state_sha256": sha256(output / "state.json"),
        "machine_index_path": str(machine_index),
        "machine_index_sha256": sha256(machine_index),
        "snapshot_commit": commit,
        "snapshot_tree": tree,
        "agent_pack_path": str(pack),
        "agent_pack_sha256": sha256(pack),
        "record_path": str(record_path),
        "record_sha256": sha256(record_path),
        "record_schema_version": 3,
        "human_root": str(human),
        "human_projection_path": str(human / "projection.json"),
        "human_projection_sha256": sha256(human / "projection.json"),
        "human_manifest_path": str(human / "manifest.json"),
        "human_manifest_sha256": sha256(human / "manifest.json"),
        "local_openers_path": str(output / "local-openers.json"),
        "local_openers_sha256": sha256(output / "local-openers.json"),
        "frozen_evidence": {"human_files": human_evidence, "source_files": source_evidence},
    }
    required_entries: list[dict[str, Any]] = []
    if page_count:
        requirement = "page-and-source" if source_count else "page"
        required_entries.append({"kind": "selected_entity", "ordinal": 0, "require": requirement})
    if record_count:
        required_entries.append({"kind": "related_document", "ordinal": 0, "require": "record"})
    request_value = {
        "schema_version": 1,
        "mode": "agent-pack-navigation",
        "ckb": ckb,
        "request": {
            "title": "CKB Canvas 导航",
            "source_link_mode": "verified-editor-uri",
            "authorized_staging_root": str(staging),
            "target_canvas_path": str(target),
            "backup_root": str(staging / ".ckb-canvas-backups" / case_id),
            "replace": replace,
            "baseline": baselines,
            "required_entries": required_entries,
        },
        "budget": {
            "max_nodes": 12,
            "max_edges": 16,
            "max_page_nodes": 6,
            "max_record_nodes": 2,
            "max_source_nodes": 3,
            "max_text_nodes": 1,
            "max_groups": 0,
        },
    }
    request_path = root / "request.json"
    write_json(request_path, request_value)
    return FixtureCase(root, output, human, snapshot, staging, target, request_path, record_path, pack, first_source, originals)


def build_acceptance_runtime() -> FixtureCase:
    return build_case("success", explicit_root=FIXTURE_ROOT / "runtime" / "success")
