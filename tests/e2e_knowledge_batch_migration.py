from __future__ import annotations

import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from ckb_core import SCHEMA_VERSION, VERSION
from ckb_core.agent_protocol import AGENT_PROTOCOL_VERSION
from ckb_core.common import json_load, json_write, sha256_file
from ckb_core.gitrepo import preflight
from ckb_core.knowledge_batch_migration import (
    apply_knowledge_batch_plan,
    audit_knowledge_batch_state,
    create_knowledge_batch_plan,
    cutover_knowledge_batch_state,
    rollback_knowledge_batch_state,
)
from ckb_core.scope_extension import _tree_manifest


GIT_COMMON_DIR = ROOT.parents[1] / "source" / ".git"
FIXTURES = ROOT / "tests/fixtures/knowledge-batch-migration/versions.json"


def command(args: list[str], *, cwd: Path | None = None, expected: set[int] = {0}) -> dict[str, Any]:
    env = dict(os.environ)
    env["CKB_TEST_PROVIDER"] = "deterministic-fixture"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result = {
        "command": args,
        "cwd": str(cwd.resolve()) if cwd else None,
        "exit_status": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode not in expected:
        raise RuntimeError(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def historical_source(commit: str, target: Path) -> None:
    archived = subprocess.run(
        ["git", "-c", "core.autocrlf=false", f"--git-dir={GIT_COMMON_DIR}", "archive", "--format=tar", commit],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    target.mkdir(parents=True)
    with tarfile.open(fileobj=BytesIO(archived), mode="r:") as archive:
        archive.extractall(target, filter="data")


def fixture_repository(root: Path, fixture_id: str) -> Path:
    repo = root / f"{fixture_id}-repo"
    repo.mkdir()
    (repo / "app.py").write_text(
        "def calculate(value):\n"
        "    doubled = value * 2\n"
        "    return doubled + 1\n",
        encoding="utf-8",
    )
    command(["git", "init"], cwd=repo)
    command(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo)
    command(["git", "config", "user.name", "Fixture"], cwd=repo)
    command(["git", "add", "."], cwd=repo)
    command(["git", "commit", "-m", fixture_id], cwd=repo)
    return repo


def historical_output(root: Path, fixture: dict[str, Any]) -> tuple[Path, Path, list[dict[str, Any]]]:
    source = root / f"{fixture['fixture_id']}-source"
    historical_source(fixture["source_commit"], source)
    repo = fixture_repository(root, fixture["fixture_id"])
    output = root / f"{fixture['fixture_id']}-output"
    ckb = source / "scripts/ckb.py"
    config_hash = sha256_file(source / "references/logseq-config.edn")
    if config_hash != "133005ee8ebbf15ff483d444d14fcb326c36424193223a9d09a6fedbdc0988e2":
        raise RuntimeError(f"historical Logseq fixture hash drifted: {config_hash}")
    evidence = [
        command(
            [
                sys.executable,
                str(ckb),
                "init",
                "--repo",
                str(repo),
                "--out",
                str(output),
                "--format",
                "markdown",
                "--scope-path",
                "app.py",
                "--entry",
                "python:app.py#calculate",
                "--expand-depth",
                "0",
            ]
        )
    ]
    state = json_load(output / "state.json")
    for batch in state["parse_batches"]:
        evidence.append(command([sys.executable, str(ckb), "build-chunk", "--out", str(output), "--chunk", batch["id"], "--stage", "all"]))
    state = json_load(output / "state.json")
    for pack in state["review_packs"]:
        template = json_load(Path(pack["review_template_path"]))
        for item in template["reviews"]:
            item["status"] = "agent-reviewed"
            item["evidence_note"] = "Agent 已重新打开历史 fixture 的固定 Git 源码范围，并逐项核对名称、范围和调用关系。"
            if pack["kind"] == "appendix-review":
                item["description_zh"] = "该局部代码完成所属流程中的辅助计算，并把确定结果交给主流程。"
            else:
                item["meaning_zh"] = "该代码页说明历史固定源码范围内的输入、计算步骤和返回结果。"
                item["role_zh"] = "它负责执行当前代码单元的主要计算，并向调用方返回确定结果。"
                item["change_when_zh"] = "当输入约定、计算步骤或返回结果变化时，需要修改并重新核对该代码单元。"
        review = root / f"{fixture['fixture_id']}-{pack['id']}.json"
        json_write(review, template)
        evidence.append(command([sys.executable, str(ckb), "review-pack", "--out", str(output), "--pack", pack["id"], "--review", str(review)]))
    evidence.append(command([sys.executable, str(ckb), "finalize", "--out", str(output)]))
    complete = json_load(output / ".complete")
    state = json_load(output / "state.json")
    protocol = json_load(output / "workspace-meta/agent-protocol.json")
    if complete.get("status") != "complete" or state.get("version") != fixture["ckb_version"]:
        raise RuntimeError(f"historical output did not finalize at {fixture['fixture_id']}")
    if state.get("schema_version") != fixture["schema_version"] or protocol.get("protocol_version") != fixture["protocol_version"]:
        raise RuntimeError(f"historical version tuple mismatch at {fixture['fixture_id']}")
    return repo, output, evidence


def project_manifest(root: Path, fixture: dict[str, Any], repo: Path, output: Path) -> dict[str, Any]:
    state = json_load(output / "state.json")
    scope = json_load(output / "scope.json")
    snapshot = preflight(repo)
    tree = _tree_manifest(output)
    records = {
        relative: sha256_file(output / relative)
        for relative in (
            "state.json",
            "scope.json",
            "catalog.json",
            "graph.json",
            "audit/global.json",
            ".complete",
            ".machine.complete",
            ".human.complete",
        )
    }
    project_id = fixture["fixture_id"]
    staging = root / f"{project_id}-staging"
    return {
        "project_id": project_id,
        "output": str(output.resolve()),
        "repository": str(repo.resolve()),
        "staging": str(staging.resolve()),
        "source": {
            "ckb_version": fixture["ckb_version"],
            "schema_version": fixture["schema_version"],
            "protocol_version": fixture["protocol_version"],
            "release_commit": fixture["source_commit"],
        },
        "target": {
            "ckb_version": VERSION,
            "schema_version": SCHEMA_VERSION,
            "protocol_version": AGENT_PROTOCOL_VERSION,
            "release_commit": "2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
        },
        "origin_snapshot": {"commit": state["repository"]["commit"], "tree": state["repository"]["tree"]},
        "target_snapshot": {"commit": snapshot["commit"], "tree": snapshot["tree"]},
        "format": state["format"],
        "scope_selectors": scope["selectors"],
        "runtime": {"python": str(Path(sys.executable).resolve()), "ckb": str((ROOT / "scripts/ckb.py").resolve())},
        "workspace_roots": [],
        "harnesses": ["codex", "generic"],
        "origin": {
            "tree": {key: tree[key] for key in ("algorithm", "file_count", "byte_count", "sha256")},
            "records": records,
        },
        "strategies": ["compatible-migration", "delta-review", "cold-build"],
        "cutover": {"output": str(output.resolve()), "backup_root": str((root / f"b-{fixture['source_commit'][:8]}").resolve())},
        "rollback": {"quarantine_root": str((root / f"q-{fixture['source_commit'][:8]}").resolve())},
    }


def run_e2e(write_report: Path | None = None) -> dict[str, Any]:
    fixture_doc = json_load(FIXTURES)
    temporary = tempfile.TemporaryDirectory(prefix="ckb-historical-batch-e2e-")
    root = Path(temporary.name)
    commands: list[dict[str, Any]] = []
    try:
        projects = []
        origins = {}
        for fixture in fixture_doc["fixtures"]:
            repo, output, fixture_commands = historical_output(root, fixture)
            commands.extend(fixture_commands)
            projects.append(project_manifest(root, fixture, repo, output))
            origins[fixture["fixture_id"]] = _tree_manifest(output)
        manifest = root / "manifest.json"
        json_write(
            manifest,
            {
                "schema_version": 1,
                "batch_id": "historical-e2e",
                "allowed_roots": [str(root.resolve()), str(ROOT.resolve())],
                "projects": projects,
            },
        )
        plan_path = root / "plan.json"
        plan = create_knowledge_batch_plan(manifest, plan_path)
        if plan["status"] != "ready" or any(item["strategy"] != "compatible-migration" for item in plan["projects"]):
            raise RuntimeError(json.dumps(plan, ensure_ascii=False, indent=2))
        state_path = root / "state.json"
        applied = apply_knowledge_batch_plan(plan_path, state_path)
        if applied["status"] != "ready":
            raise RuntimeError(json.dumps(applied, ensure_ascii=False, indent=2))
        audited = audit_knowledge_batch_state(state_path)
        if audited["status"] != "passed":
            raise RuntimeError(json.dumps(audited, ensure_ascii=False, indent=2))
        cutover = cutover_knowledge_batch_state(state_path)
        if cutover["status"] != "passed":
            raise RuntimeError(json.dumps(cutover, ensure_ascii=False, indent=2))
        rollback = rollback_knowledge_batch_state(state_path)
        if rollback["status"] != "passed":
            raise RuntimeError(json.dumps(rollback, ensure_ascii=False, indent=2))
        restored = {
            project["project_id"]: _tree_manifest(Path(project["output"])) == origins[project["project_id"]]
            for project in projects
        }
        if not all(restored.values()):
            raise RuntimeError(f"historical rollback byte mismatch: {restored}")
        result = {
            "schema_version": 1,
            "status": "passed",
            "fixtures": [item["fixture_id"] for item in fixture_doc["fixtures"]],
            "historical_build_commands": commands,
            "plan": {"status": plan["status"], "strategies": {item["project_id"]: item["strategy"] for item in plan["projects"]}},
            "apply_status": applied["status"],
            "audit_status": audited["status"],
            "cutover_status": cutover["status"],
            "rollback_status": rollback["status"],
            "byte_exact_restored": restored,
        }
        if write_report:
            json_write(write_report.resolve(), result)
        return result
    finally:
        try:
            temporary.cleanup()
        except OSError:
            shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args()
    result = run_e2e(args.write_report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
