#!/usr/bin/env python3
"""Run real finalized-output Agent Protocol batch upgrade, resume, audit, and rollback probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.agent_protocol import ADAPTER_PATHS, AGENT_PROTOCOL_VERSION, INTERNAL_ROOT_NAMES, install_agent_protocol
from ckb_core.agent_protocol_batch import (
    _replace_workspace_block_bytes,
    adapter_texts_for_version,
    command_examples_for_version,
    snapshot_digest,
    snapshot_files,
)
from ckb_core.common import json_load, json_write
from ckb_core.pipeline import build_chunk, finalize, initialize, review_pack


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    return completed.stdout.strip()


def review_all(output: Path) -> None:
    state = json_load(output / "state.json")
    for batch in state["parse_batches"]:
        if not (output / "chunks" / batch["id"] / "candidate.json").is_file():
            build_chunk(output, batch["id"], "all")
    state = json_load(output / "state.json")
    for pack in state["review_packs"]:
        if pack["status"] == "passed":
            continue
        template = json_load(Path(pack["review_template_path"]))
        for item in template["reviews"]:
            item["status"] = "agent-reviewed"
            item["evidence_note"] = "Agent 已重新打开固定 Git 源码范围，核对名称、签名、分支和调用关系后确认本条说明。"
            if pack["kind"] == "appendix-review":
                item["description_zh"] = "该局部代码负责完成所属流程中的辅助处理，并把结果交给主流程继续使用。"
            else:
                item["meaning_zh"] = "该代码页说明固定源码范围内的主要实现及其输入输出约定。"
                item["role_zh"] = "它负责组织当前代码单元的处理步骤，并与相邻函数形成可追踪的调用关系。"
                item["change_when_zh"] = "当输入约定、处理步骤、返回结果或调用关系变化时，需要修改该代码单元并同步验证。"
        review_path = output / "e2e-reviews" / f"{pack['id']}.json"
        json_write(review_path, template)
        review_pack(output, pack["id"], review_path)


def build_output(root: Path, name: str) -> tuple[Path, Path, Path]:
    project = root / name
    repo = project / "repo"
    output = project / "knowledge-base"
    repo.mkdir(parents=True)
    (repo / "app.py").write_text(
        "from helper import double\n\ndef calculate(value):\n    return double(value) + 1\n",
        encoding="utf-8",
    )
    (repo / "helper.py").write_text("def double(value):\n    return value * 2\n", encoding="utf-8")
    git(repo, "init")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "add", ".")
    git(repo, "commit", "-m", f"{name} fixture")
    initialize(repo, output, "markdown", [], [], 1, "both", [])
    review_all(output)
    finalize(output)
    install_agent_protocol(output, [project], python=Path(sys.executable), ckb=ROOT / "scripts/ckb.py")
    return project, repo, output


def downgrade_protocol(output: Path, workspace: Path, version: str) -> None:
    record_path = output / "workspace-meta/agent-protocol.json"
    record = json_load(record_path)
    python = Path(record["python"])
    ckb = Path(record["ckb"])
    repository = str(record["repository"])
    texts = adapter_texts_for_version(version, output, repository, python, ckb)
    for root_name in INTERNAL_ROOT_NAMES:
        root = output if root_name == "output" else output / root_name
        for key, relative in ADAPTER_PATHS.items():
            path = root / relative
            path.write_text(texts[key], encoding="utf-8", newline="\n")
    for key, relative in ADAPTER_PATHS.items():
        path = workspace / relative
        path.write_bytes(_replace_workspace_block_bytes(path.read_bytes(), texts[key], path))
    record["protocol_version"] = version
    record["commands"] = command_examples_for_version(version, output, python, ckb)
    json_write(record_path, record)


def manifest_project(project_id: str, output: Path, workspace: Path, source_version: str) -> dict[str, Any]:
    record_path = output / "workspace-meta/agent-protocol.json"
    return {
        "project_id": project_id,
        "output": str(output.resolve()),
        "workspace_roots": [str(workspace.resolve())],
        "source_version": source_version,
        "target_version": AGENT_PROTOCOL_VERSION,
        "harnesses": ["codex", "claude", "opencode", "opencode-v2", "dsh", "gemini", "copilot", "cursor", "generic"],
        "python": str(Path(sys.executable).resolve()),
        "ckb": str((ROOT / "scripts/ckb.py").resolve()),
        "expected_digest": hashlib.sha256(record_path.read_bytes()).hexdigest(),
    }


def fixed_hashes(output: Path) -> dict[str, str]:
    paths = ("graph.json", "facts/graph.json", "machine/knowledge.sqlite", "agent-index.sqlite")
    return {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in paths}


def invoke(records: list[dict[str, Any]], *arguments: str, expected: set[int] = {0}) -> dict[str, Any]:
    command = [sys.executable, "-X", "utf8", str(ROOT / "scripts/ckb.py"), *arguments]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    record = {
        "command": command,
        "exit_status": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    records.append(record)
    if completed.returncode not in expected:
        raise RuntimeError(f"command failed ({completed.returncode}): {command}\n{completed.stdout}\n{completed.stderr}")
    return json.loads(completed.stdout)


def run(work_root: Path, report_path: Path) -> dict[str, Any]:
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    previous_provider = os.environ.get("CKB_TEST_PROVIDER")
    os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
    commands: list[dict[str, Any]] = []
    try:
        workspace_a, _repo_a, output_a = build_output(work_root, "project-a")
        workspace_b, _repo_b, output_b = build_output(work_root, "project-b")
        fixed_before = {"a": fixed_hashes(output_a), "b": fixed_hashes(output_b)}
        version_runs = []
        for version in ("1.0.0", "1.3.0", "1.4.0", "1.5.0"):
            downgrade_protocol(output_a, workspace_a, version)
            manifest = work_root / f"manifest-{version}.json"
            plan = work_root / f"plan-{version}.json"
            state = work_root / f"state-{version}.json"
            json_write(
                manifest,
                {
                    "schema_version": 1,
                    "allowed_roots": [str(work_root.resolve())],
                    "projects": [manifest_project("project-a", output_a, workspace_a, version)],
                },
            )
            before_plan = snapshot_digest(snapshot_files(output_a, [workspace_a]))
            planned = invoke(commands, "agent-policy", "batch", "plan", "--manifest", str(manifest), "--write", str(plan))
            after_plan = snapshot_digest(snapshot_files(output_a, [workspace_a]))
            if before_plan != after_plan:
                raise RuntimeError(f"dry-run wrote target bytes for {version}")
            applied = invoke(commands, "agent-policy", "batch", "apply", "--plan", str(plan), "--state", str(state))
            status = invoke(commands, "agent-policy", "batch", "status", "--state", str(state))
            audited = invoke(commands, "agent-policy", "batch", "audit", "--state", str(state))
            policy = invoke(commands, "agent-policy", "check", "--out", str(output_a))
            maintained = invoke(commands, "maintain", "--out", str(output_a))
            version_run = {
                "version": version,
                "upgrade_path": planned["projects"][0]["upgrade_path"],
                "apply_status": applied["status"],
                "project_status": status["projects"][0]["status"],
                "audit_status": audited["status"],
                "agent_policy_status": policy["status"],
                "maintain_status": maintained["status"],
                "dry_run_digest_unchanged": before_plan == after_plan,
            }
            if version != AGENT_PROTOCOL_VERSION:
                rollback = invoke(
                    commands,
                    "agent-policy",
                    "batch",
                    "rollback",
                    "--state",
                    str(state),
                    "--project",
                    "project-a",
                )
                version_run["rollback_status"] = rollback["status"]
                version_run["rollback_version"] = json_load(output_a / "workspace-meta/agent-protocol.json")["protocol_version"]
            version_runs.append(version_run)

        downgrade_protocol(output_a, workspace_a, "1.3.0")
        downgrade_protocol(output_b, workspace_b, "1.4.0")
        agent_index_b = (output_b / "agent-index.sqlite").read_bytes()
        (output_b / "agent-index.sqlite").unlink()
        multi_manifest = work_root / "manifest-multi.json"
        multi_plan = work_root / "plan-multi.json"
        multi_state = work_root / "state-multi.json"
        json_write(
            multi_manifest,
            {
                "schema_version": 1,
                "allowed_roots": [str(work_root.resolve())],
                "projects": [
                    manifest_project("project-a", output_a, workspace_a, "1.3.0"),
                    manifest_project("project-b", output_b, workspace_b, "1.4.0"),
                ],
            },
        )
        multi_planned = invoke(commands, "agent-policy", "batch", "plan", "--manifest", str(multi_manifest), "--write", str(multi_plan))
        baseline_b = next(item for item in multi_planned["projects"] if item["project_id"] == "project-b")["observed_digest"]
        partial = invoke(
            commands,
            "agent-policy",
            "batch",
            "apply",
            "--plan",
            str(multi_plan),
            "--state",
            str(multi_state),
            expected={5},
        )
        partial_by_id = {item["project_id"]: item for item in partial["projects"]}
        restored_b = snapshot_digest(snapshot_files(output_b, [workspace_b]))
        (output_b / "agent-index.sqlite").write_bytes(agent_index_b)
        resumed = invoke(commands, "agent-policy", "batch", "apply", "--plan", str(multi_plan), "--state", str(multi_state))
        multi_audit = invoke(commands, "agent-policy", "batch", "audit", "--state", str(multi_state))
        maintain_a = invoke(commands, "maintain", "--out", str(output_a))
        maintain_b = invoke(commands, "maintain", "--out", str(output_b))
        rollback_a = invoke(
            commands,
            "agent-policy",
            "batch",
            "rollback",
            "--state",
            str(multi_state),
            "--project",
            "project-a",
        )
        version_b_after_subset = json_load(output_b / "workspace-meta/agent-protocol.json")["protocol_version"]
        rollback_b = invoke(
            commands,
            "agent-policy",
            "batch",
            "rollback",
            "--state",
            str(multi_state),
            "--project",
            "project-b",
        )
        fixed_after = {"a": fixed_hashes(output_a), "b": fixed_hashes(output_b)}
        report = {
            "schema_version": 1,
            "status": "passed",
            "runtime": str(Path(sys.executable).resolve()),
            "ckb": str((ROOT / "scripts/ckb.py").resolve()),
            "version_runs": version_runs,
            "multi_project": {
                "initial_status": partial["status"],
                "project_a_status": partial_by_id["project-a"]["status"],
                "project_b_status": partial_by_id["project-b"]["status"],
                "project_b_failure": partial_by_id["project-b"]["failure"]["category"],
                "failed_project_baseline_restored": restored_b == baseline_b,
                "resume_status": resumed["status"],
                "audit_status": multi_audit["status"],
                "maintain_a": maintain_a["status"],
                "maintain_b": maintain_b["status"],
                "rollback_a": rollback_a["status"],
                "unselected_b_version": version_b_after_subset,
                "rollback_b": rollback_b["status"],
            },
            "fixed_hashes_before": fixed_before,
            "fixed_hashes_after": fixed_after,
            "fixed_hashes_unchanged": fixed_before == fixed_after,
            "commands": commands,
        }
        if not report["fixed_hashes_unchanged"]:
            raise RuntimeError("fixed graph or SQLite digest changed during protocol-only E2E")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        json_write(report_path, report)
        return report
    finally:
        if previous_provider is None:
            os.environ.pop("CKB_TEST_PROVIDER", None)
        else:
            os.environ["CKB_TEST_PROVIDER"] = previous_provider


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.work_root.resolve(), args.report.resolve())
    print(json.dumps({key: value for key, value in report.items() if key != "commands"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
