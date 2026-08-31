from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.agent_protocol import ADAPTER_PATHS, AGENT_PROTOCOL_VERSION, INTERNAL_ROOT_NAMES, POLICY_BEGIN, POLICY_END
from ckb_core.agent_protocol_batch import (
    PROTOCOL_RELEASES,
    adapter_texts_for_version,
    command_examples_for_version,
    create_batch_plan,
    protocol_text_for_version,
    supported_upgrade_path,
    version_matrix,
)
from ckb_core.common import CkbError, json_write


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
        digest.update(str(stat.S_IMODE(path.stat().st_mode)).encode("ascii"))
    return digest.hexdigest()


def create_protocol_fixture(root: Path, version: str, project_id: str = "fixture") -> tuple[Path, Path, Path]:
    output = root / f"{project_id}-output"
    repository = root / "repo"
    workspace = root
    repository.mkdir(exist_ok=True)
    output.mkdir()
    for name in ("human", "markdown"):
        (output / name).mkdir()
    python = Path(sys.executable).resolve()
    ckb = (ROOT / "scripts/ckb.py").resolve()
    texts = adapter_texts_for_version(version, output, str(repository.resolve()), python, ckb)
    internal: dict[str, dict[str, object]] = {}
    for root_name in INTERNAL_ROOT_NAMES:
        target_root = output if root_name == "output" else output / root_name
        internal[root_name] = {"root": str(target_root.resolve()), "files": []}
        for key, relative in ADAPTER_PATHS.items():
            path = target_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(texts[key], encoding="utf-8", newline="\n")
            internal[root_name]["files"].append(relative.as_posix())
    workspace_files = []
    for key, relative in ADAPTER_PATHS.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        block = f"{POLICY_BEGIN}\n{texts[key].rstrip()}\n{POLICY_END}\n"
        path.write_text(f"# 用户自有前言\n\n{block}\n## 用户自有结尾\n\n保留中文。\n", encoding="utf-8", newline="\n")
        workspace_files.append({"path": str(path.resolve()), "relative_path": relative.as_posix(), "created": False})
    record = {
        "schema_version": 1,
        "protocol_version": version,
        "status": "installed",
        "output": str(output.resolve()),
        "repository": str(repository.resolve()),
        "python": str(python),
        "ckb": str(ckb),
        "internal_roots": internal,
        "workspace_roots": [{"root": str(workspace.resolve()), "files": workspace_files}],
        "commands": command_examples_for_version(version, output, python, ckb),
        "harness_contract": {"codex": "AGENTS.md", "generic": "read AGENTS.md before knowledge-base access"},
    }
    json_write(output / "workspace-meta/agent-protocol.json", record)
    json_write(output / "state.json", {"repository": {"root": str(repository.resolve())}})
    for name in ("human", "markdown"):
        json_write(output / name / ".ckb-generated-files.json", {"files": sorted(path.as_posix() for path in ADAPTER_PATHS.values())})
        json_write(output / name / ".obsidian/app.json", {"userIgnoreFilters": ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/", ".cursor/"]})
        css = output / name / ".obsidian/snippets/ckb.css"
        css.parent.mkdir(parents=True, exist_ok=True)
        css.write_text(".nav-file-title { display: none; }\n", encoding="utf-8")
    expected = hashlib.sha256((output / "workspace-meta/agent-protocol.json").read_bytes()).hexdigest()
    manifest = root / f"{project_id}-manifest.json"
    json_write(
        manifest,
        {
            "schema_version": 1,
            "allowed_roots": [str(root.resolve())],
            "projects": [
                {
                    "project_id": project_id,
                    "output": str(output.resolve()),
                    "workspace_roots": [str(workspace.resolve())],
                    "source_version": version,
                    "target_version": AGENT_PROTOCOL_VERSION,
                    "harnesses": ["codex", "claude", "gemini", "copilot", "cursor", "generic"],
                    "python": str(python),
                    "ckb": str(ckb),
                    "expected_digest": expected,
                }
            ],
        },
    )
    return output, manifest, workspace


class AgentProtocolBatchMatrixTests(unittest.TestCase):
    def test_frozen_historical_fixtures_match_matrix(self) -> None:
        fixture_path = ROOT / "tests/fixtures/agent-protocol-batch/versions.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(fixture["current_version"], AGENT_PROTOCOL_VERSION)
        self.assertEqual(len(fixture["fixtures"]), 4)
        self.assertEqual(len([item for item in fixture["fixtures"] if item["version"] != AGENT_PROTOCOL_VERSION]), 3)
        for item in fixture["fixtures"]:
            release = PROTOCOL_RELEASES[item["version"]]
            self.assertEqual(item["source_commit"], release.source_commit)
            self.assertEqual(item["output_contract"], release.output_contract)
            self.assertEqual(item["upgrade_path"], supported_upgrade_path(item["version"], AGENT_PROTOCOL_VERSION))
            rendered = protocol_text_for_version(
                item["version"], Path("X:/fixture/output"), "X:/fixture/repo", Path("X:/runtime/python.exe"), Path("X:/skill/ckb.py")
            )
            self.assertEqual(item["protocol_sha256"], hashlib.sha256(rendered.encode("utf-8")).hexdigest())
        self.assertEqual(version_matrix()["current_version"], AGENT_PROTOCOL_VERSION)

    def test_unknown_and_backward_paths_are_rejected(self) -> None:
        for version in ("0.9.0", "1.1.0", "1.2.0", "2.0.0"):
            with self.assertRaises(CkbError):
                supported_upgrade_path(version, AGENT_PROTOCOL_VERSION)
        with self.assertRaises(CkbError):
            supported_upgrade_path("1.5.0", "1.4.0")


class AgentProtocolBatchPlanTests(unittest.TestCase):
    def test_plan_is_byte_stable_and_does_not_write_target(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-") as value:
            root = Path(value)
            output, manifest, _workspace = create_protocol_fixture(root, "1.0.0")
            before = tree_digest(output)
            first = create_batch_plan(manifest)
            second = create_batch_plan(manifest)
            self.assertEqual(first, second)
            self.assertEqual(first["status"], "ready")
            self.assertTrue(first["dry_run"])
            self.assertEqual(first["projects"][0]["upgrade_path"], ["1.0.0", "1.3.0", "1.4.0", "1.5.0"])
            self.assertEqual(tree_digest(output), before)
            plan_path = root / "batch-plan.json"
            written = create_batch_plan(manifest, plan_path)
            self.assertEqual(written["plan_path"], str(plan_path.resolve()))
            self.assertEqual(json.loads(plan_path.read_text(encoding="utf-8"))["plan_digest"], first["plan_digest"])
            self.assertEqual(tree_digest(output), before)

    def test_manifest_and_project_failures_have_stable_categories(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-fail-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.3.0")
            value_doc = json.loads(manifest.read_text(encoding="utf-8"))
            value_doc["unexpected"] = True
            json_write(manifest, value_doc)
            with self.assertRaises(CkbError):
                create_batch_plan(manifest)
            value_doc.pop("unexpected")
            value_doc["projects"][0]["expected_digest"] = "0" * 64
            json_write(manifest, value_doc)
            failed = create_batch_plan(manifest)
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(failed["projects"][0]["failure"]["category"], "expected-digest-mismatch")
            value_doc["projects"][0]["expected_digest"] = hashlib.sha256(
                (output / "workspace-meta/agent-protocol.json").read_bytes()
            ).hexdigest()
            agents = workspace / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + f"\n{POLICY_BEGIN}\n重复\n{POLICY_END}\n", encoding="utf-8")
            json_write(manifest, value_doc)
            duplicate = create_batch_plan(manifest)
            self.assertEqual(duplicate["projects"][0]["failure"]["category"], "managed-block-duplicate")


if __name__ == "__main__":
    unittest.main()
