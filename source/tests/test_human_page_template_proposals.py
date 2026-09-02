from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from ckb_core.common import CkbError
from ckb_core.human_page_template_proposals import (
    audit_template_proposal,
    list_templates,
    normalize_template_proposal,
    propose_template,
    rollback_template_extension,
    show_template,
    template_proposal_skeleton,
    validate_template_proposal,
    write_template_proposal_skeleton,
)
from ckb_core.human_page_templates import human_page_template_registry_sha256


FIXTURES = SKILL_ROOT / "tests/fixtures/human-page-template-proposals"


def _fixture() -> dict[str, object]:
    return json.loads((FIXTURES / "valid-proposal.json").read_text(encoding="utf-8"))


class TemplateProposalStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        self.output.mkdir()
        (self.output / "state.json").write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self, value: dict[str, object], name: str = "proposal.json") -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def test_init_writes_a_complete_target_pinned_skeleton_without_store_changes(self) -> None:
        target = self.root / "skeleton.json"
        result = write_template_proposal_skeleton(self.output, target, "local-guide")
        self.assertEqual("written", result["status"])
        skeleton = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual("local-guide", skeleton["template_name"])
        self.assertEqual(human_page_template_registry_sha256(), skeleton["target"]["registry_sha256"])
        for field in (
            "reader_task", "fields", "sections", "budgets", "links", "evidence", "examples",
            "failure_examples", "migration_impact", "applicability_boundary", "rollback",
        ):
            self.assertIn(field, skeleton)
        self.assertFalse((self.output / "workspace-meta/human-page-template-proposals").exists())

    def test_validate_is_offline_read_only_and_rejects_unknown_old_or_incomplete_documents(self) -> None:
        valid_path = self._write(_fixture())
        result = validate_template_proposal(self.output, valid_path)
        self.assertEqual("passed", result["status"])
        self.assertEqual(0, result["writes"])
        self.assertFalse((self.output / "workspace-meta/human-page-template-proposals").exists())

        cases: list[tuple[str, dict[str, object], str]] = []
        unknown = _fixture()
        unknown["unexpected"] = True
        cases.append(("unknown", unknown, "unknown fields"))
        old = _fixture()
        old["schema_version"] = 0
        cases.append(("old", old, "unsupported template proposal schema_version"))
        for field, message in (
            ("examples", "requires at least one examples"),
            ("failure_examples", "requires at least one failure_examples"),
        ):
            missing = _fixture()
            missing[field] = []
            cases.append((field, missing, message))
        migration = _fixture()
        del migration["migration_impact"]
        cases.append(("migration", migration, "missing required fields"))
        for name, value, message in cases:
            with self.subTest(name=name), self.assertRaisesRegex(CkbError, message):
                normalize_template_proposal(value)

    def test_builtin_name_and_target_drift_are_hard_failures(self) -> None:
        conflict = _fixture()
        conflict["template_name"] = "analysis"
        with self.assertRaisesRegex(CkbError, "cannot override or weaken builtin"):
            normalize_template_proposal(conflict)
        drift = _fixture()
        drift["target"]["registry_sha256"] = "0" * 64  # type: ignore[index]
        with self.assertRaisesRegex(CkbError, "target drift"):
            normalize_template_proposal(drift)

    def test_agent_and_human_proposals_remain_pending_and_exact_content_is_idempotent(self) -> None:
        path = self._write(_fixture())
        first = propose_template(self.output, path)
        second = propose_template(self.output, path)
        self.assertEqual("pending", first["status"])
        self.assertEqual("pending", second["status"])
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["proposal_id"], second["proposal_id"])
        listing = list_templates(self.output)
        self.assertEqual(14, listing["counts"]["builtin"])
        self.assertEqual(1, listing["counts"]["pending"])
        self.assertEqual(15, listing["count"])
        shown = show_template(self.output, str(first["proposal_id"]))
        self.assertEqual("pending", shown["template"]["status"])
        self.assertEqual("agent", shown["template"]["proposal"]["proposer"]["kind"])

        human = _fixture()
        human["template_name"] = "human-checklist"
        human["proposer"] = {"kind": "human", "id": "reviewer-fixture"}
        human_result = propose_template(self.output, self._write(human, "human.json"))
        self.assertEqual("pending", human_result["status"])
        self.assertEqual(2, list_templates(self.output, "pending")["count"])

    def test_same_name_content_requires_a_strictly_new_version(self) -> None:
        propose_template(self.output, self._write(_fixture()))
        same_version = _fixture()
        same_version["reader_task"] = "不同内容。"
        with self.assertRaisesRegex(CkbError, "name/version already has different content"):
            propose_template(self.output, self._write(same_version, "same-version.json"))
        old_version = _fixture()
        old_version["version"] = "0.9.0"
        old_version["reader_task"] = "旧版本内容。"
        with self.assertRaisesRegex(CkbError, "version must advance"):
            propose_template(self.output, self._write(old_version, "old-version.json"))

    def test_concurrent_writers_preserve_unique_events_and_replayable_index(self) -> None:
        paths = []
        for index in range(8):
            value = _fixture()
            value["template_name"] = f"parallel-{index}"
            paths.append(self._write(value, f"parallel-{index}.json"))
        errors: list[BaseException] = []

        def submit(path: Path) -> None:
            try:
                propose_template(self.output, path)
            except BaseException as exc:  # pragma: no cover - surfaced below
                errors.append(exc)

        threads = [threading.Thread(target=submit, args=(path,)) for path in paths]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if errors:
            raise errors[0]
        listing = list_templates(self.output, "pending")
        self.assertEqual(8, listing["count"])
        sequences = [item["sequence"] for item in listing["templates"]]
        self.assertEqual(list(range(1, 9)), sorted(sequences))
        store = self.output / "workspace-meta/human-page-template-proposals"
        self.assertEqual(8, len((store / "operations.jsonl").read_text(encoding="utf-8").splitlines()))
        self.assertEqual(8, json.loads((store / "index.json").read_text(encoding="utf-8"))["event_count"])

    def _audit(
        self,
        proposal: dict[str, object],
        decision: str = "approve",
        *,
        reviewer_kind: str = "human",
        reviewer_id: str = "human-reviewer",
        conclusion: str = "人工逐项审阅完成。",
    ) -> dict[str, object]:
        return audit_template_proposal(
            self.output,
            str(proposal["proposal_id"]),
            decision,
            reviewer_kind,
            reviewer_id,
            conclusion,
            str(proposal.get("version") or "1.0.0"),
            str(proposal["content_hash"]),
        )

    def test_only_explicit_human_audit_can_approve_and_freezes_activation_contract(self) -> None:
        submitted = propose_template(self.output, self._write(_fixture()))
        submitted["version"] = "1.0.0"
        with self.assertRaisesRegex(CkbError, "reviewer.kind=human"):
            self._audit(submitted, reviewer_kind="agent")
        with self.assertRaisesRegex(CkbError, "must be non-empty text"):
            self._audit(submitted, reviewer_id="")
        approved = self._audit(submitted)
        self.assertEqual("approved", approved["status"])
        self.assertTrue(approved["active"])
        self.assertEqual("1.0.0", approved["frozen_version"])
        self.assertEqual(submitted["content_hash"], approved["frozen_content_hash"])
        audit = json.loads(Path(str(approved["audit"])).read_text(encoding="utf-8"))
        self.assertEqual("human", audit["reviewer"]["kind"])
        self.assertEqual("1.0.0", audit["frozen_activation"]["version"])
        self.assertEqual(_fixture()["migration_impact"], audit["frozen_activation"]["migration_impact"])
        self.assertEqual(_fixture()["rollback"], audit["frozen_activation"]["rollback"])
        shown = show_template(self.output, str(submitted["proposal_id"]))
        self.assertEqual(["proposal", "audit"], [event["event_type"] for event in shown["template"]["history"]])

    def test_reject_and_return_are_terminal_history_preserving_states(self) -> None:
        rejected_doc = _fixture()
        rejected_doc["template_name"] = "rejected-template"
        rejected = propose_template(self.output, self._write(rejected_doc, "rejected.json"))
        rejected["version"] = "1.0.0"
        self.assertEqual("rejected", self._audit(rejected, "reject", conclusion="人工审阅确认不采用。")["status"])

        returned_doc = _fixture()
        returned_doc["template_name"] = "returned-template"
        returned = propose_template(self.output, self._write(returned_doc, "returned.json"))
        returned["version"] = "1.0.0"
        self.assertEqual(
            "superseded",
            self._audit(returned, "return", conclusion="人工审阅要求修改后新版本再提交。")["status"],
        )
        listing = list_templates(self.output)
        self.assertEqual(1, listing["counts"]["rejected"])
        self.assertEqual(1, listing["counts"]["superseded"])
        store = self.output / "workspace-meta/human-page-template-proposals"
        self.assertEqual(4, len((store / "operations.jsonl").read_text(encoding="utf-8").splitlines()))

    def test_new_approval_supersedes_old_version_and_rollback_only_deactivates_active_approval(self) -> None:
        first = propose_template(self.output, self._write(_fixture(), "v1.json"))
        first["version"] = "1.0.0"
        self._audit(first)

        second_doc = _fixture()
        second_doc["version"] = "2.0.0"
        second_doc["reader_task"] = "让读者确认第二版决策、依据和验证入口。"
        second = propose_template(self.output, self._write(second_doc, "v2.json"))
        second["version"] = "2.0.0"
        self._audit(second, conclusion="人工审阅批准第二版。")
        approved = list_templates(self.output, "approved")
        superseded = list_templates(self.output, "superseded")
        self.assertEqual([second["proposal_id"]], [item["id"] for item in approved["templates"]])
        self.assertIn(first["proposal_id"], [item["id"] for item in superseded["templates"]])

        rolled_back = rollback_template_extension(
            self.output,
            str(second["proposal_id"]),
            "human",
            "human-reviewer",
            "第二版启用行为需要撤销。",
            str(second["content_hash"]),
        )
        self.assertEqual("rolled-back", rolled_back["status"])
        self.assertEqual("superseded", rolled_back["template_status"])
        self.assertFalse(rolled_back["active"])
        self.assertTrue(rolled_back["history_retained"])
        repeated = rollback_template_extension(
            self.output,
            str(second["proposal_id"]),
            "human",
            "human-reviewer",
            "第二版启用行为需要撤销。",
            str(second["content_hash"]),
        )
        self.assertTrue(repeated["idempotent"])
        self.assertEqual(0, list_templates(self.output, "approved")["count"])
        self.assertEqual(2, list_templates(self.output, "superseded")["count"])
        shown = show_template(self.output, str(second["proposal_id"]))
        self.assertEqual(
            ["proposal", "audit", "rollback"],
            [event["event_type"] for event in shown["template"]["history"]],
        )

    def test_rollback_rejects_pending_and_target_drift_blocks_audit(self) -> None:
        pending = propose_template(self.output, self._write(_fixture()))
        with self.assertRaisesRegex(CkbError, "active approved extension"):
            rollback_template_extension(
                self.output,
                str(pending["proposal_id"]),
                "human",
                "human-reviewer",
                "未批准内容不能回滚。",
                str(pending["content_hash"]),
            )
        with mock.patch(
            "ckb_core.human_page_template_proposals.human_page_template_registry_sha256",
            return_value="0" * 64,
        ):
            pending["version"] = "1.0.0"
            with self.assertRaisesRegex(CkbError, "schema or builtin registry target drifted"):
                self._audit(pending)

    def test_cli_success_and_failure_samples_cover_all_commands(self) -> None:
        ckb = SKILL_ROOT / "scripts/ckb.py"
        skeleton = self.root / "cli-skeleton.json"

        def run(*arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(ckb), "template", *arguments],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        initialized = run("init", "--out", str(self.output), "--write", str(skeleton), "--name", "cli-template")
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        self.assertTrue(skeleton.is_file())
        proposal_path = self._write(_fixture(), "cli-proposal.json")
        validated = run("validate", "--out", str(self.output), "--proposal", str(proposal_path))
        self.assertEqual(0, validated.returncode, validated.stderr)
        proposed = run("propose", "--out", str(self.output), "--proposal", str(proposal_path))
        self.assertEqual(0, proposed.returncode, proposed.stderr)
        proposed_json = json.loads(proposed.stdout)
        listed = run("list", "--out", str(self.output), "--status", "pending")
        self.assertEqual(1, json.loads(listed.stdout)["count"])
        shown = run("show", "--out", str(self.output), "--template", proposed_json["proposal_id"])
        self.assertEqual("pending", json.loads(shown.stdout)["template"]["status"])

        missing_reviewer = run(
            "audit", "--out", str(self.output), "--proposal", proposed_json["proposal_id"],
            "--decision", "approve", "--version", "1.0.0",
            "--expected-content-hash", proposed_json["content_hash"], "--conclusion", "人工批准。",
        )
        self.assertEqual(2, missing_reviewer.returncode)
        self.assertIn("--reviewer-kind", missing_reviewer.stderr)
        audited = run(
            "audit", "--out", str(self.output), "--proposal", proposed_json["proposal_id"],
            "--decision", "approve", "--reviewer-kind", "human", "--reviewer-id", "cli-human",
            "--conclusion", "人工逐项检查后批准。", "--version", "1.0.0",
            "--expected-content-hash", proposed_json["content_hash"],
        )
        self.assertEqual(0, audited.returncode, audited.stderr)
        self.assertEqual("approved", json.loads(audited.stdout)["status"])
        rolled_back = run(
            "rollback", "--out", str(self.output), "--proposal", proposed_json["proposal_id"],
            "--reviewer-kind", "human", "--reviewer-id", "cli-human",
            "--reason", "人工决定撤销启用。", "--expected-content-hash", proposed_json["content_hash"],
        )
        self.assertEqual(0, rolled_back.returncode, rolled_back.stderr)
        self.assertEqual("rolled-back", json.loads(rolled_back.stdout)["status"])
        self.assertFalse((self.output / "human").exists())
        self.assertFalse((self.output / "markdown").exists())


if __name__ == "__main__":
    unittest.main()
