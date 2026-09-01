from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.agent_protocol import ADAPTER_PATHS, AGENT_PROTOCOL_VERSION, INTERNAL_ROOT_NAMES, POLICY_BEGIN, POLICY_END
from ckb_core.agent_protocol_batch import (
    PROTOCOL_RELEASES,
    adapter_texts_for_version,
    apply_batch_plan,
    audit_batch_state,
    batch_status,
    command_examples_for_version,
    create_batch_plan,
    protocol_text_for_version,
    rollback_batch_state,
    supported_upgrade_path,
    version_matrix,
)
import ckb_core.agent_protocol_batch as batch_module
from ckb_core.common import CkbError, json_write
from ckb_core.output_contract import audit_output_contract


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
        digest.update(str(stat.S_IMODE(path.stat().st_mode)).encode("ascii"))
    return digest.hexdigest()


def create_protocol_fixture(root: Path, version: str, project_id: str = "fixture") -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
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


def install_fake_plugin(vault: Path) -> None:
    plugin = vault / ".obsidian/plugins/code-knowledge-builder-companion"
    plugin.mkdir(parents=True, exist_ok=True)
    for name in ("main.js", "manifest.json", "styles.css", "LICENSE", "NOTICE.md"):
        (plugin / name).write_text("{}\n" if name == "manifest.json" else f"fixture {name}\n", encoding="utf-8")
    json_write(vault / ".obsidian/community-plugins.json", ["code-knowledge-builder-companion"])


def outside_managed_bytes(value: bytes) -> bytes:
    begin = value.index(POLICY_BEGIN.encode("utf-8"))
    end = value.index(POLICY_END.encode("utf-8"), begin) + len(POLICY_END.encode("utf-8"))
    return value[:begin] + value[end:]


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

    def test_required_failure_fixtures_are_classified_without_guessing(self) -> None:
        cases = []
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-cases-") as value:
            root = Path(value)

            missing_root = root / "missing-record"
            output, manifest, _ = create_protocol_fixture(missing_root, "1.3.0", "missing")
            (output / "workspace-meta/agent-protocol.json").unlink()
            cases.append((manifest, "protocol-record-missing"))

            unknown_root = root / "unknown-version"
            _output, manifest, _ = create_protocol_fixture(unknown_root, "1.3.0", "unknown")
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["projects"][0]["source_version"] = "9.9.9"
            json_write(manifest, doc)
            cases.append((manifest, "source-version-unsupported"))

            runtime_root = root / "missing-runtime"
            _output, manifest, _ = create_protocol_fixture(runtime_root, "1.3.0", "runtime")
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["projects"][0]["python"] = str((runtime_root / "missing-python.exe").resolve())
            json_write(manifest, doc)
            cases.append((manifest, "python-missing"))

            boundary_root = root / "boundary"
            _output, manifest, _ = create_protocol_fixture(boundary_root, "1.3.0", "boundary")
            outside = root / "outside-workspace"
            outside.mkdir()
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["projects"][0]["workspace_roots"] = [str(outside.resolve())]
            json_write(manifest, doc)
            cases.append((manifest, "workspace-root-out-of-bounds"))

            broken_root = root / "broken-marker"
            _output, manifest, workspace = create_protocol_fixture(broken_root, "1.3.0", "broken")
            agents = workspace / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8").replace(POLICY_END, ""), encoding="utf-8")
            cases.append((manifest, "managed-block-broken"))

            mixed_root = root / "mixed-content"
            _output, manifest, workspace = create_protocol_fixture(mixed_root, "1.3.0", "mixed")
            agents = workspace / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8").replace(POLICY_END, "用户内容误入管理区。\n" + POLICY_END, 1), encoding="utf-8")
            cases.append((manifest, "managed-block-source-drift"))

            for manifest_path, category in cases:
                with self.subTest(category=category):
                    result = create_batch_plan(manifest_path)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["projects"][0]["failure"]["category"], category)

    def test_duplicate_and_nested_outputs_fail_manifest_preflight(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-output-set-") as value:
            root = Path(value)
            _output, manifest, _ = create_protocol_fixture(root, "1.3.0", "one")
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            duplicated = dict(doc["projects"][0])
            duplicated["project_id"] = "two"
            doc["projects"].append(duplicated)
            json_write(manifest, doc)
            with self.assertRaises(CkbError):
                create_batch_plan(manifest)
            doc["projects"][1]["output"] = str((Path(doc["projects"][0]["output"]) / "nested").resolve())
            json_write(manifest, doc)
            with self.assertRaises(CkbError):
                create_batch_plan(manifest)


class AgentProtocolBatchApplyTests(unittest.TestCase):
    def test_current_version_fixture_is_audited_and_idempotently_skipped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-current-") as value:
            root = Path(value)
            _output, manifest, _workspace = create_protocol_fixture(root, AGENT_PROTOCOL_VERSION)
            plan_path = root / "plan.json"
            state_path = root / "state.json"
            plan = create_batch_plan(manifest, plan_path)
            self.assertEqual(plan["projects"][0]["action"], "noop")
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                result = apply_batch_plan(plan_path, state_path)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["summary"]["counts"], {"skipped": 1})

    def test_apply_rejects_plan_target_drift_before_transaction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-plan-drift-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.3.0")
            plan_path = root / "plan.json"
            state_path = root / "state.json"
            create_batch_plan(manifest, plan_path)
            agents = workspace / "AGENTS.md"
            agents.write_bytes(agents.read_bytes() + "\n计划之后的漂移。\n".encode("utf-8"))
            drifted = agents.read_bytes()
            result = apply_batch_plan(plan_path, state_path)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["projects"][0]["failure"]["category"], "plan-target-drift")
            self.assertEqual(agents.read_bytes(), drifted)
            self.assertEqual(json.loads((output / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], "1.3.0")

    def test_apply_updates_protocol_contract_and_preserves_user_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-apply-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.0.0")
            for vault_name in ("human", "markdown"):
                install_fake_plugin(output / vault_name)
            agents = workspace / "AGENTS.md"
            text = agents.read_text(encoding="utf-8")
            agents.write_bytes(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8"))
            user_bytes_before = outside_managed_bytes(agents.read_bytes())
            (output / "graph.json").write_bytes(b"fixed graph\n")
            (output / "machine").mkdir(exist_ok=True)
            (output / "machine/knowledge.sqlite").write_bytes(b"fixed machine sqlite\n")
            (output / "agent-index.sqlite").write_bytes(b"fixed agent sqlite\n")
            fixed_before = {
                name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                for name in ("graph.json", "machine/knowledge.sqlite", "agent-index.sqlite")
            }
            plan_path = root / "plan.json"
            state_path = root / "batch-state.json"
            plan = create_batch_plan(manifest, plan_path)
            baseline = plan["projects"][0]["observed_digest"]
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                applied = apply_batch_plan(plan_path, state_path)
            self.assertEqual(applied["status"], "completed")
            self.assertEqual(json.loads((output / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], AGENT_PROTOCOL_VERSION)
            self.assertEqual(outside_managed_bytes(agents.read_bytes()), user_bytes_before)
            self.assertTrue(agents.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertIn(b"\r\n", agents.read_bytes())
            for vault_name in ("human", "markdown"):
                contract = audit_output_contract(output, output / vault_name)
                self.assertEqual(contract["status"], "passed", contract)
            fixed_after = {
                name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                for name in ("graph.json", "machine/knowledge.sqlite", "agent-index.sqlite")
            }
            self.assertEqual(fixed_after, fixed_before)
            current = batch_status(state_path)
            self.assertEqual(current["summary"]["counts"], {"completed": 1})
            self.assertNotEqual(current["projects"][0]["current_digest"], baseline)
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                repeated = apply_batch_plan(plan_path, state_path)
            self.assertEqual(repeated["status"], "completed")
            self.assertEqual(repeated["summary"]["counts"], {"skipped": 1})
            journal_text = "".join(path.read_text(encoding="utf-8") for path in (output / "workspace-meta/operations").glob("*.jsonl"))
            self.assertNotIn("用户自有前言", journal_text)
            self.assertNotIn("token", journal_text.casefold())
            self.assertLessEqual(len(json.loads(state_path.read_text(encoding="utf-8"))["events"]), 256)

    def test_partial_failure_restores_failed_project_and_audits_each_result(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-partial-") as value:
            root = Path(value)
            output_a, manifest_a, _ = create_protocol_fixture(root / "a", "1.3.0", "a")
            output_b, manifest_b, _ = create_protocol_fixture(root / "b", "1.4.0", "b")
            doc_a = json.loads(manifest_a.read_text(encoding="utf-8"))
            doc_b = json.loads(manifest_b.read_text(encoding="utf-8"))
            manifest = root / "manifest.json"
            json_write(
                manifest,
                {
                    "schema_version": 1,
                    "allowed_roots": [str(root.resolve())],
                    "projects": [doc_a["projects"][0], doc_b["projects"][0]],
                },
            )
            plan_path = root / "plan.json"
            plan = create_batch_plan(manifest, plan_path)
            baseline_b = next(item for item in plan["projects"] if item["project_id"] == "b")["observed_digest"]

            def selective_audit(output: Path) -> dict[str, object]:
                return {"status": "failed", "errors": [{"reason": "fixture-mid-batch"}]} if output == output_b.resolve() else {"status": "passed", "errors": []}

            state_path = root / "state.json"
            with patch("ckb_core.agent_protocol.audit_agent_protocol", side_effect=selective_audit):
                result = apply_batch_plan(plan_path, state_path)
            self.assertEqual(result["status"], "partial")
            by_id = {item["project_id"]: item for item in result["projects"]}
            self.assertEqual(by_id["a"]["status"], "completed")
            self.assertEqual(by_id["b"]["status"], "failed")
            self.assertEqual(by_id["b"]["failure"]["category"], "post-upgrade-audit-failed")
            self.assertEqual(json.loads((output_a / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], AGENT_PROTOCOL_VERSION)
            self.assertEqual(json.loads((output_b / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], "1.4.0")
            current_b = batch_module.snapshot_digest(batch_module.snapshot_files(output_b, [root / "b"]))
            self.assertEqual(current_b, baseline_b)
            with patch("ckb_core.agent_protocol.audit_agent_protocol", side_effect=selective_audit):
                audited = audit_batch_state(state_path)
            self.assertEqual(audited["status"], "failed")
            audit_by_id = {item["project_id"]: item for item in audited["projects"]}
            self.assertEqual(audit_by_id["a"]["status"], "passed")
            self.assertEqual(audit_by_id["b"]["status"], "failed")

    def test_interrupted_apply_restores_baseline_then_resumes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-resume-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.3.0")
            plan_path = root / "plan.json"
            plan = create_batch_plan(manifest, plan_path)
            state_path = root / "state.json"
            original_commit = batch_module._commit_desired

            def interrupt_after_first_write(desired: dict[str, bytes | None]) -> None:
                first_path = sorted(path for path, content in desired.items() if content is not None)[0]
                path = Path(first_path)
                content = desired[first_path]
                assert content is not None
                batch_module._write_bytes_atomic(path, content, stat.S_IMODE(path.stat().st_mode) if path.is_file() else 0o644)
                raise SystemExit(91)

            with patch.object(batch_module, "_commit_desired", side_effect=interrupt_after_first_write):
                with self.assertRaises(SystemExit):
                    apply_batch_plan(plan_path, state_path)
            interrupted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(interrupted["projects"]["fixture"]["status"], "applying")
            with (
                patch.object(batch_module, "_commit_desired", side_effect=original_commit),
                patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}),
            ):
                resumed = apply_batch_plan(plan_path, state_path)
            self.assertEqual(resumed["status"], "completed")
            self.assertEqual(json.loads((output / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], AGENT_PROTOCOL_VERSION)
            events = json.loads(state_path.read_text(encoding="utf-8"))["events"]
            self.assertTrue(any(item["action"] == "resume" and item["status"] == "restored-baseline" for item in events))

    def test_existing_output_lock_reports_concurrent_failure_without_writes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-lock-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.4.0")
            plan_path = root / "plan.json"
            plan = create_batch_plan(manifest, plan_path)
            lock = output / "workspace-meta/agent-policy-batch.lock"
            lock.write_text("other-process", encoding="ascii")
            state_path = root / "state.json"
            with patch.object(batch_module, "LOCK_TIMEOUT_SECONDS", 0.01):
                result = apply_batch_plan(plan_path, state_path)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["projects"][0]["failure"]["category"], "output-lock-record-invalid")
            self.assertEqual(json.loads((output / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], "1.4.0")

    def test_live_cross_process_owner_is_not_stolen_after_stale_threshold(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-live-lock-") as value:
            root = Path(value)
            output, _manifest, _workspace = create_protocol_fixture(root, "1.4.0")
            ready = root / "holder-ready"
            release = root / "holder-release"
            code = r"""
from pathlib import Path
import json,os,sys,time
sys.path.insert(0, sys.argv[1])
import ckb_core.agent_protocol_batch as batch
batch.LOCK_STALE_SECONDS = 0.10
batch.LOCK_TIMEOUT_SECONDS = 1.0
with batch._output_lock(Path(sys.argv[2])) as acquired:
    Path(sys.argv[3]).write_text(json.dumps({'owner_pid': os.getpid(), 'owner_token': acquired['owner_token']}), encoding='utf-8')
    while not Path(sys.argv[4]).exists():
        time.sleep(0.02)
"""
            holder = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-c", code, str((ROOT / "scripts").resolve()), str(output), str(ready), str(release)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            try:
                deadline = time.monotonic() + 5.0
                while not ready.is_file() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(ready.is_file(), holder.poll())
                record = json.loads(ready.read_text(encoding="utf-8"))
                self.assertNotEqual(record["owner_pid"], os.getpid())
                lock = output / "workspace-meta/agent-policy-batch.lock"
                before = lock.stat()
                time.sleep(0.25)
                with (
                    patch.object(batch_module, "LOCK_STALE_SECONDS", 0.10),
                    patch.object(batch_module, "LOCK_TIMEOUT_SECONDS", 0.08),
                ):
                    with self.assertRaises(batch_module.BatchProjectError) as caught:
                        with batch_module._output_lock(output):
                            self.fail("second process acquired a live OUTPUT lock")
                self.assertEqual(caught.exception.category, "concurrent-output-lock")
                after = lock.stat()
                self.assertEqual((after.st_ino, after.st_size, after.st_mtime_ns), (before.st_ino, before.st_size, before.st_mtime_ns))
            finally:
                release.write_text("release", encoding="ascii")
                stdout, stderr = holder.communicate(timeout=10)
                self.assertEqual(holder.returncode, 0, stdout + stderr)
            self.assertFalse((output / "workspace-meta/agent-policy-batch.lock").exists())

    def test_dead_cross_process_owner_is_recovered_only_after_stale_threshold(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-dead-lock-") as value:
            root = Path(value)
            output, _manifest, _workspace = create_protocol_fixture(root, "1.4.0")
            ready = root / "dead-ready"
            code = r"""
from pathlib import Path
import os,sys
sys.path.insert(0, sys.argv[1])
import ckb_core.agent_protocol_batch as batch
with batch._output_lock(Path(sys.argv[2])):
    Path(sys.argv[3]).write_text('ready', encoding='ascii')
    os._exit(0)
"""
            holder = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-c", code, str((ROOT / "scripts").resolve()), str(output), str(ready)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            stdout, stderr = holder.communicate(timeout=10)
            self.assertEqual(holder.returncode, 0, stdout + stderr)
            lock = output / "workspace-meta/agent-policy-batch.lock"
            self.assertTrue(lock.is_file())
            recent = time.time()
            os.utime(lock, (recent, recent))
            with (
                patch.object(batch_module, "LOCK_STALE_SECONDS", 5.0),
                patch.object(batch_module, "LOCK_TIMEOUT_SECONDS", 0.05),
            ):
                with self.assertRaises(batch_module.BatchProjectError) as caught:
                    with batch_module._output_lock(output):
                        self.fail("recent dead-owner lock was recovered before stale threshold")
            self.assertEqual(caught.exception.category, "output-lock-owner-dead")
            old = time.time() - 10.0
            os.utime(lock, (old, old))
            with patch.object(batch_module, "LOCK_STALE_SECONDS", 0.10):
                with batch_module._output_lock(output) as acquired:
                    self.assertEqual(acquired["recovered_category"], "output-lock-owner-dead")
            self.assertFalse(lock.exists())

    def test_corrupt_pid_reused_unverifiable_and_release_drift_are_classified(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-lock-categories-") as value:
            root = Path(value)
            output, _manifest, _workspace = create_protocol_fixture(root, "1.4.0")
            lock = output / "workspace-meta/agent-policy-batch.lock"

            old = time.time() - 10.0
            lock.write_text(str(os.getpid()), encoding="ascii")
            os.utime(lock, (old, old))
            with (
                patch.object(batch_module, "LOCK_STALE_SECONDS", 0.10),
                patch.object(batch_module, "LOCK_TIMEOUT_SECONDS", 0.01),
            ):
                with self.assertRaises(batch_module.BatchProjectError) as legacy_live:
                    with batch_module._output_lock(output):
                        self.fail("legacy PID-only lock with live owner was recovered")
            self.assertEqual(legacy_live.exception.category, "output-lock-legacy-owner-live")
            self.assertEqual(lock.read_text(encoding="ascii"), str(os.getpid()))
            lock.unlink()

            lock.write_text("{broken-json", encoding="utf-8")
            with (
                patch.object(batch_module, "LOCK_STALE_SECONDS", 5.0),
                patch.object(batch_module, "LOCK_TIMEOUT_SECONDS", 0.01),
            ):
                with self.assertRaises(batch_module.BatchProjectError) as corrupt_recent:
                    with batch_module._output_lock(output):
                        self.fail("recent corrupt lock was recovered")
            self.assertEqual(corrupt_recent.exception.category, "output-lock-record-invalid")
            os.utime(lock, (old, old))
            with patch.object(batch_module, "LOCK_STALE_SECONDS", 0.10):
                with batch_module._output_lock(output) as recovered:
                    self.assertEqual(recovered["recovered_category"], "output-lock-record-invalid-stale")

            state, process_start = batch_module._process_start_identity(os.getpid())
            self.assertEqual(state, "alive")
            reused = {
                "schema_version": batch_module.OUTPUT_LOCK_SCHEMA_VERSION,
                "owner_pid": os.getpid(),
                "owner_token": "a" * 32,
                "owner_process_start": process_start + "-different",
                "owner_host": batch_module.socket.gethostname(),
                "created_at_utc": "2026-09-01T00:00:00Z",
            }
            json_write(lock, reused)
            os.utime(lock, (old, old))
            with patch.object(batch_module, "LOCK_STALE_SECONDS", 0.10):
                with batch_module._output_lock(output) as recovered:
                    self.assertEqual(recovered["recovered_category"], "output-lock-owner-pid-reused")

            valid = dict(reused)
            valid["owner_process_start"] = str(process_start)
            json_write(lock, valid)
            os.utime(lock, (old, old))
            with (
                patch.object(batch_module, "_process_start_identity", return_value=("unverifiable", None)),
                patch.object(batch_module, "LOCK_STALE_SECONDS", 0.10),
                patch.object(batch_module, "LOCK_TIMEOUT_SECONDS", 0.01),
            ):
                with self.assertRaises(batch_module.BatchProjectError) as unverifiable:
                    with batch_module._output_lock(output):
                        self.fail("unverifiable owner was recovered")
            self.assertEqual(unverifiable.exception.category, "output-lock-owner-unverifiable")
            self.assertTrue(lock.is_file())
            lock.unlink()

            with self.assertRaises(batch_module.BatchProjectError) as release_drift:
                with batch_module._output_lock(output) as acquired:
                    own = json.loads(batch_module._descriptor_bytes(acquired["_descriptor"]).decode("utf-8"))
                    own["owner_token"] = "f" * 32
                    batch_module._write_lock_descriptor(acquired["_descriptor"], own)
            self.assertEqual(release_drift.exception.category, "output-lock-release-owner-token-drift")
            self.assertTrue(lock.is_file())
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner_token"], "f" * 32)
            lock.unlink()

    def test_single_project_rollback_restores_bytes_modes_and_source_version(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-rollback-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.0.0")
            agents = workspace / "AGENTS.md"
            os_mode = 0o640
            os.chmod(agents, os_mode)
            tracked_before = {
                item["path"]: (Path(item["path"]).read_bytes() if item["exists"] else None, item["mode"])
                for item in batch_module.snapshot_files(output, [workspace])
            }
            plan_path = root / "plan.json"
            state_path = root / "state.json"
            create_batch_plan(manifest, plan_path)
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                applied = apply_batch_plan(plan_path, state_path)
            self.assertEqual(applied["status"], "completed")
            rolled_back = rollback_batch_state(state_path, ["fixture"])
            self.assertEqual(rolled_back["status"], "passed")
            self.assertEqual(json.loads((output / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], "1.0.0")
            for path_value, (content, mode) in tracked_before.items():
                path = Path(path_value)
                self.assertEqual(path.read_bytes() if path.is_file() else None, content, path_value)
                if content is not None:
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode, path_value)
            status = batch_status(state_path)
            self.assertEqual(status["summary"]["counts"], {"rolled-back": 1})
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                audited = audit_batch_state(state_path)
            self.assertEqual(audited["status"], "passed")

    def test_subset_rollback_keeps_unselected_success_applied(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-subset-") as value:
            root = Path(value)
            output_a, manifest_a, _ = create_protocol_fixture(root / "a", "1.3.0", "a")
            output_b, manifest_b, _ = create_protocol_fixture(root / "b", "1.4.0", "b")
            manifest = root / "manifest.json"
            json_write(
                manifest,
                {
                    "schema_version": 1,
                    "allowed_roots": [str(root.resolve())],
                    "projects": [
                        json.loads(manifest_a.read_text(encoding="utf-8"))["projects"][0],
                        json.loads(manifest_b.read_text(encoding="utf-8"))["projects"][0],
                    ],
                },
            )
            plan_path = root / "plan.json"
            state_path = root / "state.json"
            create_batch_plan(manifest, plan_path)
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                self.assertEqual(apply_batch_plan(plan_path, state_path)["status"], "completed")
            result = rollback_batch_state(state_path, ["a"])
            self.assertEqual(result["status"], "passed")
            self.assertEqual(json.loads((output_a / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], "1.3.0")
            self.assertEqual(json.loads((output_b / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], AGENT_PROTOCOL_VERSION)
            counts = batch_status(state_path)["summary"]["counts"]
            self.assertEqual(counts, {"completed": 1, "rolled-back": 1})

    def test_rollback_refuses_post_batch_user_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-agent-policy-batch-rollback-drift-") as value:
            root = Path(value)
            output, manifest, workspace = create_protocol_fixture(root, "1.4.0")
            plan_path = root / "plan.json"
            state_path = root / "state.json"
            create_batch_plan(manifest, plan_path)
            with patch("ckb_core.agent_protocol.audit_agent_protocol", return_value={"status": "passed", "errors": []}):
                self.assertEqual(apply_batch_plan(plan_path, state_path)["status"], "completed")
            agents = workspace / "AGENTS.md"
            agents.write_bytes(agents.read_bytes() + "\n批次之后的用户修改。\n".encode("utf-8"))
            drifted = agents.read_bytes()
            result = rollback_batch_state(state_path, ["fixture"])
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["projects"][0]["failure"]["category"], "rollback-external-drift")
            self.assertEqual(agents.read_bytes(), drifted)
            self.assertEqual(json.loads((output / "workspace-meta/agent-protocol.json").read_text(encoding="utf-8"))["protocol_version"], AGENT_PROTOCOL_VERSION)


if __name__ == "__main__":
    unittest.main()
