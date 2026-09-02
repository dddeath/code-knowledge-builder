from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.common import CkbError
from ckb_core.human_maintenance_prompts import (
    HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
    active_command_steps,
    audit_human_maintenance_delivery,
    get_human_maintenance_action,
    human_maintenance_delivery_template,
    human_maintenance_registry_document,
    human_maintenance_registry_sha256,
    list_human_maintenance_actions,
    render_human_maintenance_prompt,
    serialize_human_maintenance_registry,
    validate_human_maintenance_invocation,
)
from ckb_core.management_agent import management_human_maintenance_prompt_contract


FIXTURES = ROOT / "tests/fixtures/human-maintenance-prompts"
CLI = ROOT / "scripts/ckb.py"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _valid_maintain_summary() -> dict[str, object]:
    items = [
        "knowledge_base=C:/work/project/knowledge-base",
        "scope=single-output",
        "confirm=maintain",
        "python=C:/tools/python.exe",
        "ckb=C:/tools/ckb.py",
    ]
    summary = human_maintenance_delivery_template("maintain", items)
    for command in summary["commands"]:
        command["literal_output"] = json.dumps({"status": "passed"})
        command["exit_status"] = 0
    summary["requirements"]["maintain"]["evidence"] = ["commands:maintain"]
    for field in summary["acceptance"]:
        summary["acceptance"][field] = f"verified:{field}"
    return summary


def _template_review_parameters(operation: str, confirmation: str) -> list[str]:
    return [
        "knowledge_base=C:/work/project/knowledge-base",
        "proposal_file=C:/work/template-proposal.json",
        "page_type=change",
        "page_mode=new",
        "authoring_input=C:/work/page-author-input.json",
        "page_source=C:/work/source-page.md",
        "workspace_root=C:/work",
        "source_sha256=" + "b" * 64,
        "staging=C:/work/staging/page-package",
        "contract_version=1.0.0",
        "schema_version=1",
        f"operation={operation}",
        "proposal_id=template-proposal-fixture",
        "decision=approve",
        "reviewer_kind=human",
        "reviewer_id=human-reviewer",
        "conclusion=人工逐项核对版本和内容哈希后批准。",
        "version=1.0.0",
        "content_hash=" + "a" * 64,
        f"human_confirmation={confirmation}",
        "scope=output-local-template-store",
        "python=C:/tools/python.exe",
        "ckb=C:/tools/ckb.py",
    ]


def _valid_template_audit_summary() -> dict[str, object]:
    summary = human_maintenance_delivery_template(
        "template", _template_review_parameters("audit", "template-audit")
    )
    statuses = {"template-review-show": "ready", "template-audit": "approved"}
    for command in summary["commands"]:
        command["literal_output"] = json.dumps({"status": statuses[command["step_id"]]})
        command["exit_status"] = 0
    summary["requirements"]["source"]["evidence"] = ["commands:template-review-show"]
    summary["requirements"]["human_review"]["evidence"] = ["commands:template-audit"]
    for field in summary["acceptance"]:
        summary["acceptance"][field] = f"verified:{field}"
    summary["rollback"]["evidence"] = ["existing-command:template rollback"]
    return summary


class HumanMaintenancePromptRegistryTests(unittest.TestCase):
    def test_registry_covers_the_fixed_action_order_and_contract_fields(self) -> None:
        expected = (
            "install-project",
            "adopt-existing",
            "build-new",
            "explain",
            "record",
            "feedback",
            "reference",
            "gap",
            "maintain",
            "migrate",
            "template",
        )
        self.assertEqual(expected, list_human_maintenance_actions())
        registry = human_maintenance_registry_document()
        self.assertEqual(HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION, registry["contract_version"])
        self.assertEqual(list(expected), registry["action_order"])
        for action in registry["actions"]:
            self.assertTrue(action["purpose_zh"])
            self.assertTrue(action["parameters"])
            self.assertTrue(action["execution_steps"])
            self.assertTrue(action["stop_conditions"])
            self.assertEqual({"brief", "source", "maintain", "human_review"}, set(action["requirements"]))
            self.assertIn(action["rollback"]["requirement"], {"required", "conditional", "not-required", "dependency"})
            self.assertTrue(action["acceptance_summary_fields"])

    def test_registry_serialization_and_hash_are_byte_stable(self) -> None:
        first = serialize_human_maintenance_registry()
        second = serialize_human_maintenance_registry()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        self.assertEqual(hashlib.sha256(first.encode("utf-8")).hexdigest(), human_maintenance_registry_sha256())

    def test_manager_reads_the_same_registry_without_copying_a_state_machine(self) -> None:
        manager = management_human_maintenance_prompt_contract()
        self.assertEqual(human_maintenance_registry_sha256(), manager["registry_sha256"])
        self.assertEqual(list(list_human_maintenance_actions()), manager["action_order"])
        record = management_human_maintenance_prompt_contract("record")
        self.assertEqual("record", record["action"]["action"])
        self.assertEqual(human_maintenance_registry_sha256(), record["registry_sha256"])

    def test_template_maps_the_existing_proposal_state_machine_but_not_page_authoring(self) -> None:
        contract = get_human_maintenance_action("template")
        self.assertEqual("conditional", contract.rollback.requirement)
        self.assertEqual("conditional", dict(contract.requirements)["source"])
        self.assertEqual("conditional", dict(contract.requirements)["human_review"])
        existing = {step.step_id for step in contract.execution_steps if step.mapping == "existing-command"}
        self.assertTrue(
            {
                "template-list",
                "template-show",
                "template-init",
                "template-validate",
                "template-propose",
                "template-audit",
                "template-rollback",
                "page-author-init",
                "page-author-inspect",
                "page-author-render",
                "page-author-validate",
                "page-author-package",
            }.issubset(existing)
        )
        by_id = {step.step_id: step for step in contract.execution_steps}
        self.assertEqual(("pending",), by_id["template-propose"].result_statuses)
        required_review_inputs = {
            "proposal_id",
            "version",
            "content_hash",
            "reviewer_id",
            "conclusion",
            "human_confirmation",
        }
        self.assertTrue(required_review_inputs.issubset(set(by_id["template-audit"].input_parameters)))
        self.assertTrue(required_review_inputs.issubset(set(by_id["template-rollback"].input_parameters)))
        self.assertFalse([step for step in contract.execution_steps if step.mapping == "pending-capability"])
        parameters = {value.name: value for value in contract.parameters}
        self.assertEqual("3.0.0", parameters["contract_version"].default)
        self.assertEqual(3, parameters["schema_version"].default)
        self.assertIn("machine_evidence_refs", contract.purpose_zh)
        self.assertIn("disclosure_result", contract.acceptance_summary_fields)


class HumanMaintenancePromptValidationTests(unittest.TestCase):
    def test_validate_rejects_unknown_duplicate_and_missing_confirmation(self) -> None:
        unknown = validate_human_maintenance_invocation("maintain", ["knowledge_base=C:/kb", "confirm=maintain", "mystery=x"])
        self.assertEqual("failed", unknown["status"])
        self.assertIn("unknown-parameter", [error["reason"] for error in unknown["errors"]])
        duplicate = validate_human_maintenance_invocation(
            "maintain", ["knowledge_base=C:/kb", "knowledge_base=D:/kb", "confirm=maintain"]
        )
        self.assertIn("duplicate-parameter", [error["reason"] for error in duplicate["errors"]])
        missing = validate_human_maintenance_invocation("maintain", ["knowledge_base=C:/kb"])
        self.assertIn("missing-human-confirmation", [error["reason"] for error in missing["errors"]])

    def test_validate_rejects_install_build_mixing_and_conflicting_scope(self) -> None:
        mixed = validate_human_maintenance_invocation(
            "install-project",
            [
                "source=https://example.invalid/repo",
                "release_branch=release",
                "confirm=install-project",
                "repository=C:/business",
            ],
        )
        self.assertIn("mixed-install-build-responsibility", [error["reason"] for error in mixed["errors"]])
        scope = validate_human_maintenance_invocation(
            "explain", ["knowledge_base=C:/kb", "question=怎么工作", "scope=write"]
        )
        self.assertIn("conflicting-scope", [error["reason"] for error in scope["errors"]])

    def test_validate_rejects_accepted_feedback_without_applied_record(self) -> None:
        result = validate_human_maintenance_invocation(
            "feedback",
            ["knowledge_base=C:/kb", "confirm=feedback", "decision=accepted"],
        )
        self.assertIn("missing-applied-record", [error["reason"] for error in result["errors"]])

    def test_template_audit_and_rollback_require_explicit_human_review_fields(self) -> None:
        missing_confirmation = validate_human_maintenance_invocation(
            "template",
            [item for item in _template_review_parameters("audit", "template-audit") if not item.startswith("human_confirmation=")],
        )
        self.assertIn("missing-human-confirmation", [error["reason"] for error in missing_confirmation["errors"]])
        audit = validate_human_maintenance_invocation(
            "template", _template_review_parameters("audit", "template-audit")
        )
        self.assertEqual("passed", audit["status"])
        rollback = validate_human_maintenance_invocation(
            "template", _template_review_parameters("rollback", "template-rollback")
        )
        self.assertEqual("passed", rollback["status"])
        self.assertIn("version", rollback["parameters"])
        self.assertIn("content_hash", rollback["parameters"])

    def test_page_package_requires_confirmation_and_forbids_managed_projection_targets(self) -> None:
        parameters = [
            "knowledge_base=C:/work/knowledge-base",
            "operation=page-package",
            "authoring_input=C:/work/page-author-input.json",
            "workspace_root=C:/work",
            "staging=C:/work/staging/page-package",
            "human_confirmation=page-package",
            "python=C:/tools/python.exe",
            "ckb=C:/tools/ckb.py",
        ]
        valid = validate_human_maintenance_invocation("template", parameters)
        self.assertEqual("passed", valid["status"], valid["errors"])
        delivery = human_maintenance_delivery_template("template", parameters)
        self.assertEqual("dependency-ready", delivery["rollback"]["status"])
        self.assertEqual("external-dependency", delivery["rollback"]["mapping"])
        self.assertIsNone(delivery["rollback"]["command"])
        missing = validate_human_maintenance_invocation(
            "template", [item for item in parameters if not item.startswith("human_confirmation=")]
        )
        self.assertIn("missing-human-confirmation", [error["reason"] for error in missing["errors"]])
        managed = validate_human_maintenance_invocation(
            "template", ["staging=C:/work/human/changes/page", *[item for item in parameters if not item.startswith("staging=")]]
        )
        self.assertIn("managed-target-forbidden", [error["reason"] for error in managed["errors"]])

    def test_page_init_rejects_old_contract_instead_of_silently_using_v3_headings(self) -> None:
        result = validate_human_maintenance_invocation(
            "template",
            [
                "operation=page-init",
                "page_type=change",
                "page_mode=new",
                "contract_version=1.0.0",
                "schema_version=1",
            ],
        )
        self.assertIn("page-author-v3-required", [error["reason"] for error in result["errors"]])


class HumanMaintenancePromptRenderTests(unittest.TestCase):
    def test_same_input_produces_identical_prompt_bytes(self) -> None:
        items = ["knowledge_base=C:/kb", "question=解释检索路径"]
        first = render_human_maintenance_prompt("explain", items)
        second = render_human_maintenance_prompt("explain", items)
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertIn(f"registry_sha256={human_maintenance_registry_sha256()}", first)
        self.assertIn("action=explain", first)
        self.assertIn("profile=fast", first)
        self.assertIn("budget=1800", first)

    def test_install_and_build_prompts_keep_responsibilities_separate(self) -> None:
        install = render_human_maintenance_prompt(
            "install-project",
            ["source=https://example.invalid/ckb", "release_branch=release", "confirm=install-project"],
        )
        build = render_human_maintenance_prompt(
            "build-new",
            ["repository=C:/repo", "knowledge_base=C:/kb", "question=解释项目", "confirm=build-new"],
        )
        self.assertIn("只安装 Code Knowledge Builder 项目、Skill 与运行环境", install)
        self.assertNotIn("run --repo", install)
        self.assertIn("从已经安装的 Skill 开始", build)
        self.assertNotIn("Git LFS", build)
        self.assertNotIn("install-project", build)

    def test_render_uses_only_active_operation_steps(self) -> None:
        result = validate_human_maintenance_invocation(
            "feedback", ["knowledge_base=C:/kb", "confirm=feedback", "operation=create"]
        )
        self.assertEqual("passed", result["status"])
        steps = active_command_steps(get_human_maintenance_action("feedback"), result["parameters"])
        ids = {step.step_id for step in steps}
        self.assertIn("feedback-create", ids)
        self.assertNotIn("feedback-resolve", ids)

    def test_invalid_render_raises_one_input_error(self) -> None:
        with self.assertRaises(CkbError):
            render_human_maintenance_prompt("maintain", ["knowledge_base=C:/kb"])


class HumanMaintenancePromptFixtureTests(unittest.TestCase):
    def test_every_action_has_minimal_full_invalid_prompt_and_invalid_summary_fixtures(self) -> None:
        document = _fixture("actions.json")
        self.assertEqual(human_maintenance_registry_sha256(), document["registry_sha256"])
        self.assertEqual(list(list_human_maintenance_actions()), document["action_order"])
        cases = document["cases"]
        self.assertEqual(set(list_human_maintenance_actions()), set(cases))
        for action in list_human_maintenance_actions():
            case = cases[action]
            minimal = case["minimal_parameters"]
            full = case["full_parameters"]
            self.assertEqual("passed", validate_human_maintenance_invocation(action, minimal)["status"], action)
            self.assertEqual("passed", validate_human_maintenance_invocation(action, full)["status"], action)
            self.assertEqual(case["minimal_prompt"].encode("utf-8"), render_human_maintenance_prompt(action, minimal).encode("utf-8"), action)
            self.assertEqual(case["full_prompt"].encode("utf-8"), render_human_maintenance_prompt(action, full).encode("utf-8"), action)
            self.assertEqual("failed", validate_human_maintenance_invocation(action, case["invalid_parameters"])["status"], action)
            self.assertEqual("failed", audit_human_maintenance_delivery(action, case["invalid_summary"])["status"], action)
            for operation_case in case.get("operation_cases", []):
                parameters = operation_case["parameters"]
                self.assertEqual("passed", validate_human_maintenance_invocation(action, parameters)["status"])
                self.assertEqual(
                    operation_case["prompt"].encode("utf-8"),
                    render_human_maintenance_prompt(action, parameters).encode("utf-8"),
                )

    def test_readme_v4_install_and_explain_fixtures_keep_accepted_responsibility_split(self) -> None:
        fixture = _fixture("readme-v4.json")
        install = fixture["install"]["prompt"]
        explain = fixture["explain"]["prompt"]
        self.assertEqual("install-project", fixture["install"]["action"])
        self.assertIn("本次只完成 Code Knowledge Builder 安装", install)
        self.assertNotIn("repository=", install)
        self.assertNotIn("run --repo", install)
        self.assertEqual("explain", fixture["explain"]["action"])
        self.assertIn("请使用已安装的 $code-knowledge-builder", explain)
        self.assertIn("本次从已经安装的 Skill 开始", explain)
        self.assertNotIn("项目来源：", explain)
        self.assertNotIn("下载指定发布分支", explain)

    def test_readme_v5_fixture_contains_only_agent_direction_and_direct_human_results(self) -> None:
        fixture = _fixture("readme-v5.json")
        self.assertEqual(3, fixture["schema_version"])
        self.assertEqual("3.0.0", fixture["contract_version"])
        self.assertEqual(
            [
                "先选择你要完成的任务",
                "了解本项目知识库结构",
                "让 Agent 安装本项目",
                "让 Agent 解释自己的项目",
                "安装后继续指挥 Agent",
            ],
            fixture["headings"],
        )
        self.assertEqual(3, len(fixture["first_screen_tasks"]))
        self.assertEqual(
            ["了解本项目知识库结构", "让 Agent 安装本项目", "让 Agent 解释自己的项目"],
            [value["task"] for value in fixture["first_screen_tasks"]],
        )
        cards = fixture["task_cards"]
        self.assertEqual({"structure", "install", "explain", "continue"}, set(cards))
        for value in cards.values():
            self.assertTrue(value["direct_result"])
            self.assertTrue(value["copy_to_agent"])
        install = cards["install"]["copy_to_agent"]
        explain = cards["explain"]["copy_to_agent"]
        continuation = cards["continue"]["copy_to_agent"]
        self.assertIn("只返回项目位置", install)
        self.assertIn("不为业务仓库建立知识库", install)
        self.assertIn("建立或接管知识库", explain)
        self.assertIn("不重复安装项目", explain)
        self.assertIn("完整验证明细仅在我明确要求时读取", continuation)
        combined = "\n".join(value["copy_to_agent"] for value in cards.values())
        self.assertNotIn("ckb.py", combined)
        self.assertNotIn("python.exe", combined)
        self.assertNotRegex(combined, r"\b\d+\s*/\s*\d+\b")


class HumanMaintenanceDeliveryAuditTests(unittest.TestCase):
    def test_complete_summary_with_exact_command_inputs_output_and_exit_status_passes(self) -> None:
        result = audit_human_maintenance_delivery("maintain", _valid_maintain_summary())
        self.assertEqual("passed", result["status"])
        self.assertEqual(["maintain"], result["checked_command_steps"])
        self.assertEqual([], result["errors"])

    def test_command_start_or_placeholder_is_not_completion(self) -> None:
        summary = _valid_maintain_summary()
        summary["commands"][0]["literal_output"] = json.dumps({"status": "started"})
        result = audit_human_maintenance_delivery("maintain", summary)
        self.assertEqual("failed", result["status"])
        self.assertIn("command-result-not-complete", [error["reason"] for error in result["errors"]])
        summary = _valid_maintain_summary()
        summary["acceptance"]["maintenance_result"] = "<value:maintenance_result>"
        result = audit_human_maintenance_delivery("maintain", summary)
        self.assertIn("missing-acceptance-value", [error["reason"] for error in result["errors"]])

    def test_summary_must_return_the_same_action_and_registry_hash(self) -> None:
        summary = _valid_maintain_summary()
        summary["action"] = "explain"
        summary["registry_sha256"] = "0" * 64
        result = audit_human_maintenance_delivery("maintain", summary)
        reasons = [error["reason"] for error in result["errors"]]
        self.assertIn("delivery-action-mismatch", reasons)
        self.assertIn("registry-hash-mismatch", reasons)

    def test_template_approve_audit_requires_human_evidence_and_ready_rollback(self) -> None:
        summary = _valid_template_audit_summary()
        result = audit_human_maintenance_delivery("template", summary)
        self.assertEqual("passed", result["status"], result["errors"])
        self.assertEqual(["template-audit", "template-review-show"], result["required_command_steps"])
        summary["parameters"]["human_confirmation"] = "none"
        failed = audit_human_maintenance_delivery("template", summary)
        self.assertIn("invalid-summary-parameters", [error["reason"] for error in failed["errors"]])


class HumanMaintenancePromptCliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-B", str(CLI), "prompt", *arguments],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_list_show_render_and_validate_have_one_utf8_stdout_document(self) -> None:
        listed = self.run_cli("list")
        self.assertEqual(0, listed.returncode, listed.stderr.decode(errors="replace"))
        list_value = json.loads(listed.stdout.decode("utf-8"))
        self.assertEqual(human_maintenance_registry_sha256(), list_value["registry_sha256"])
        shown = self.run_cli("show", "record")
        self.assertEqual(0, shown.returncode)
        self.assertEqual("record", json.loads(shown.stdout.decode("utf-8"))["action"]["action"])
        rendered = self.run_cli("render", "explain", "knowledge_base=C:/kb", "question=Q")
        self.assertEqual(0, rendered.returncode)
        self.assertTrue(rendered.stdout.decode("utf-8").startswith("# Code Knowledge Builder 人类维护 Prompt\n"))
        invalid = self.run_cli("validate", "maintain", "knowledge_base=C:/kb")
        self.assertEqual(2, invalid.returncode)
        self.assertEqual("failed", json.loads(invalid.stdout.decode("utf-8"))["status"])

    def test_audit_exit_status_is_zero_only_for_verified_completion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-human-prompt-") as temporary:
            path = Path(temporary) / "summary.json"
            path.write_text(json.dumps(_valid_maintain_summary(), ensure_ascii=False), encoding="utf-8")
            passed = self.run_cli("audit", "maintain", "--summary", str(path))
            self.assertEqual(0, passed.returncode, passed.stderr.decode(errors="replace"))
            self.assertEqual("passed", json.loads(passed.stdout.decode("utf-8"))["status"])
            invalid = _valid_maintain_summary()
            invalid["commands"][0]["literal_output"] = "command started"
            path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            failed = self.run_cli("audit", "maintain", "--summary", str(path))
            self.assertEqual(5, failed.returncode)
            value = json.loads(failed.stdout.decode("utf-8"))
            self.assertEqual("failed", value["status"])
            self.assertIn("command-start-is-not-completion", [error["reason"] for error in value["errors"]])


if __name__ == "__main__":
    unittest.main()
