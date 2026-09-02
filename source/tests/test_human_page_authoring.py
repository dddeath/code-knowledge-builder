from __future__ import annotations

import hashlib
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ckb_core.human_page_authoring import (  # noqa: E402
    HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
    _package_route,
    init_page_author,
    inspect_page_author,
    package_page_author,
    render_page_author,
    validate_page_author,
)
from ckb_core.human_page_templates import (  # noqa: E402
    HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    get_human_page_template,
    list_human_page_types,
)


FIXTURES = ROOT / "tests/fixtures/human-page-authoring"
DEEP_TARGET = "INDEX.md#让-Agent-精确定位"


def _cli_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return environment


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _section(
    human_summary: str,
    *,
    key_entities: list[str] | None = None,
    links: list[dict[str, str]] | None = None,
    metrics: list[str] | None = None,
    source_refs: list[dict[str, str]] | None = None,
    machine_evidence_refs: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "human_summary": human_summary,
        "key_entities": key_entities or [],
        "links": links or [],
        "metrics": metrics or [],
        "source_refs": source_refs or [],
        "machine_evidence_refs": machine_evidence_refs or [],
    }


def _payload(page_type: str, title: str, bodies: dict[str, str | dict[str, object]]) -> dict[str, object]:
    contract = get_human_page_template(page_type)
    sections = {
        section_id: value if isinstance(value, dict) else _section(value)
        for section_id, value in bodies.items()
    }
    return {
        "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "page_type": page_type,
        "mode": "new",
        "title": title,
        "sections": sections,
        "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
        "validation_context": {"sections": {}, "current_facts": []},
        "applicability_boundary": contract.applicability_boundary,
    }


def _change_payload() -> dict[str, object]:
    return _payload(
        "change",
        "页面编写命令变更",
        {
            "what": "页面编写入口生成完整候选并执行合同检查。",
            "when": "该描述绑定 V3 合同。",
            "why": "原流程缺少按章节收集字段的入口。",
            "implementation": _section("`human_page_authoring` 负责骨架、渲染和检查。", key_entities=["human_page_authoring"]),
            "features": "该入口与冻结模板注册表直接关联。",
            "result": "候选页面会返回章节约束检查结果。",
            "boundary": "结论只覆盖 schema 化 V3 输入。",
            "deep-reading": _section(
                f"[让 Agent 按本页问题继续定位]({DEEP_TARGET})。",
                links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}],
            ),
        },
    )


class HumanPageAuthoringInitTests(unittest.TestCase):
    def test_all_fourteen_types_return_v3_skeletons_and_section_constraints(self) -> None:
        self.assertEqual(3, HUMAN_PAGE_AUTHORING_SCHEMA_VERSION)
        self.assertEqual(14, len(list_human_page_types()))
        for page_type in list_human_page_types():
            for mode in ("new", "supplement", "revise"):
                with self.subTest(page_type=page_type, mode=mode):
                    result = init_page_author(page_type, mode)
                    self.assertEqual("ready", result["status"])
                    self.assertEqual("3.0.0", result["contract_version"])
                    self.assertEqual(3, result["schema_version"])
                    self.assertEqual(page_type, result["page_type"])
                    self.assertTrue(result["section_constraints"])
                    for value in result["section_constraints"].values():
                        self.assertIn("required_content", value)
                        self.assertIn("length_budget", value)
                        self.assertIn("disclosure_level", value)
                        self.assertIn("empty_behavior", value)
                    skeleton = result["skeleton"]
                    self.assertEqual({"sections": {}, "current_facts": []}, skeleton["validation_context"])
                    if mode == "new":
                        first = next(iter(skeleton["sections"].values()))
                        self.assertEqual(
                            {"human_summary", "key_entities", "links", "metrics", "source_refs", "machine_evidence_refs"}
                            | ({"heading"} if "heading" in first else set()),
                            set(first),
                        )
                    elif mode == "supplement":
                        self.assertEqual({}, skeleton["sections"])
                    else:
                        self.assertEqual([], skeleton["revisions"])

    def test_change_and_readme_keep_confirmed_v3_headings(self) -> None:
        self.assertEqual(
            ("修改内容", "修改时间", "修改原因", "实现概述", "关联特性", "当前结果", "适用边界", "深入阅读"),
            tuple(value.heading for value in get_human_page_template("change").required_sections),
        )
        self.assertEqual(
            ("先选择你要完成的任务", "了解本项目知识库结构", "让 Agent 安装本项目", "让 Agent 解释自己的项目", "安装后继续指挥 Agent"),
            tuple(value.heading for value in get_human_page_template("README").required_sections),
        )
        readme = init_page_author("README", "new")["skeleton"]
        self.assertIn("continue", readme["sections"])
        self.assertNotIn("experiments", readme["sections"])

    def test_old_contract_input_is_a_stable_migration_failure(self) -> None:
        result = init_page_author("change", "new", contract_version="1.0.0", schema_version=1)
        self.assertEqual("failed", result["status"])
        self.assertEqual("contract-version-incompatible", result["errors"][0]["reason"])
        self.assertEqual("explicit-rewrite", result["errors"][0]["migration"]["mode"])


class HumanPageAuthoringRenderTests(unittest.TestCase):
    def test_new_change_renders_only_human_summary_and_validates(self) -> None:
        payload = _change_payload()
        payload["sections"]["result"]["machine_evidence_refs"] = [  # type: ignore[index]
            {"target": "artifacts/verification.json", "purpose": "复查完整命令和结果", "kind": "log"}
        ]
        result = render_page_author(payload)
        self.assertEqual("ready", result["status"], result)
        self.assertEqual("passed", result["validation"]["status"])
        self.assertIn("## 实现概述", result["markdown"])
        self.assertNotIn("artifacts/verification.json", result["markdown"])
        self.assertEqual(_digest(result["markdown"]), result["markdown_sha256"])

    def test_readme_renders_human_tasks_without_command_tutorial(self) -> None:
        payload = _payload(
            "README",
            "Code Knowledge Builder",
            {
                "task-choice": "| 任务 | 你会直接得到 |\n|---|---|\n| 了解本项目知识库结构 | 人类入口与机器入口说明 |\n| 让 Agent 安装本项目 | 可使用的项目与卸载入口 |\n| 让 Agent 解释自己的项目 | 问题结论、来源与边界 |",
                "structure": "### 你会直接得到\n\n人类入口、机器入口和各自职责。\n\n### 复制给 Agent\n\n```text\n请说明这个知识库的人类入口与机器入口分别负责什么。\n```",
                "install": "### 你会直接得到\n\n可使用的项目、Skill 和卸载入口。\n\n### 复制给 Agent\n\n```text\n请安装项目，并返回安装结果与适用边界。\n```",
                "explain": "### 你会直接得到\n\n目标仓库的问题结论、来源和待核验边界。\n\n### 复制给 Agent\n\n```text\n请使用已安装的 Skill 解释 repository=<目标仓库> 中的 question=<项目问题>。\n```",
                "continue": "### 你会直接得到\n\n一次阅读、定位、修改或核验任务的结果。\n\n### 复制给 Agent\n\n```text\n请继续完成 task=<指定任务>，并返回结果、来源与边界。\n```",
            },
        )
        result = render_page_author(payload)
        self.assertEqual("ready", result["status"], result)
        self.assertIn("## 安装后继续指挥 Agent", result["markdown"])
        first = result["markdown"].split("## 了解本项目知识库结构", 1)[0]
        self.assertEqual(3, first.count("| 让 Agent") + first.count("| 了解本项目"))
        self.assertEqual(4, result["markdown"].count("### 你会直接得到"))
        self.assertEqual(4, result["markdown"].count("### 复制给 Agent"))
        self.assertNotIn("ckb.py", result["markdown"])

    def test_missing_fields_returns_human_summary_path_without_partial_markdown(self) -> None:
        payload = _change_payload()
        del payload["sections"]["why"]  # type: ignore[index]
        result = render_page_author(payload)
        self.assertEqual("missing-fields", result["status"])
        self.assertEqual(["sections.why.human_summary"], result["missing_fields"])
        self.assertNotIn("markdown", result)

    def test_supplement_uses_existing_context_and_adds_only_missing_section(self) -> None:
        existing = """# 页面编写命令变更

## 修改内容
页面编写入口生成完整候选并执行合同检查。
## 修改时间
该描述绑定 V3 合同。
## 实现概述
`human_page_authoring` 负责骨架、渲染和检查。
## 关联特性
该入口与冻结模板注册表直接关联。
## 当前结果
候选页面会返回章节约束检查结果。
## 适用边界
结论只覆盖 schema 化 V3 输入。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
"""
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"
            draft.write_text(existing, encoding="utf-8")
            inspected = inspect_page_author("change", "supplement", draft, workspace_root=root)
            self.assertEqual(["sections.why.human_summary"], inspected["missing_fields"])
            payload = {
                "schema_version": 3,
                "contract_version": "3.0.0",
                "page_type": "change",
                "mode": "supplement",
                "source_path": "draft.md",
                "source_sha256": inspected["source"]["sha256"],
                "sections": {"why": _section("原流程缺少按章节收集字段的入口。")},
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {
                    "sections": {
                        "implementation": {key: value for key, value in _section("", key_entities=["human_page_authoring"]).items() if key != "human_summary"},
                        "deep-reading": {key: value for key, value in _section("", links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}]).items() if key != "human_summary"},
                    },
                    "current_facts": [],
                },
                "applicability_boundary": contract.applicability_boundary,
            }
            result = render_page_author(payload, workspace_root=root)
            self.assertEqual("ready", result["status"], result)
            self.assertEqual(1, result["markdown"].count("# 页面编写命令变更"))
            self.assertIn("## 修改原因", result["markdown"])

    def test_revise_separates_human_summary_from_machine_evidence_refs(self) -> None:
        initial = render_page_author(_change_payload())["markdown"]
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"
            draft.write_text(initial, encoding="utf-8")
            payload = {
                "schema_version": 3,
                "contract_version": "3.0.0",
                "page_type": "change",
                "mode": "revise",
                "source_path": "draft.md",
                "source_sha256": _digest(initial),
                "revisions": [
                    {
                        "section_id": "why",
                        "current": "原流程缺少按章节收集字段的入口。",
                        "human_summary": "原流程缺少按章节收集和复核字段的入口。",
                        "key_entities": [],
                        "links": [],
                        "metrics": [],
                        "source_refs": [{"target": "review-record:fixture", "purpose": "核对修改原因", "kind": "review"}],
                        "machine_evidence_refs": [{"target": "verification.json", "purpose": "复查完整行为", "kind": "log"}],
                    }
                ],
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {
                    "sections": {
                        "implementation": {key: value for key, value in _section("", key_entities=["human_page_authoring"]).items() if key != "human_summary"},
                        "deep-reading": {key: value for key, value in _section("", links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}]).items() if key != "human_summary"},
                    },
                    "current_facts": [],
                },
                "applicability_boundary": contract.applicability_boundary,
            }
            result = render_page_author(payload, workspace_root=root)
            self.assertEqual("ready", result["status"], result)
            self.assertIn("收集和复核字段", result["markdown"])
            self.assertNotIn("verification.json", result["markdown"])
            payload["revisions"][0]["source_refs"] = []
            missing = render_page_author(payload, workspace_root=root)
            self.assertEqual(["revisions[0].source_refs"], missing["missing_fields"])

    def test_cli_defaults_to_v3_and_emits_one_json_document(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(ROOT / "scripts/ckb.py"), "page-author", "init", "--page-type", "change", "--mode", "new"],
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_cli_environment(),
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        parsed = json.loads(completed.stdout)
        self.assertEqual("3.0.0", parsed["contract_version"])
        self.assertEqual(3, parsed["schema_version"])
        self.assertEqual("", completed.stderr)


class HumanPageAuthoringValidationFailureTests(unittest.TestCase):
    def _validation_payload(self, page_type: str, markdown: str) -> dict[str, object]:
        contract = get_human_page_template(page_type)
        return {
            "schema_version": 3,
            "contract_version": "3.0.0",
            "page_type": page_type,
            "markdown": markdown,
            "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
            "validation_context": {"sections": {}, "current_facts": []},
            "applicability_boundary": contract.applicability_boundary,
        }

    def test_validate_returns_named_structure_budget_link_disclosure_and_evidence_checks(self) -> None:
        rendered = render_page_author(_change_payload())
        payload = self._validation_payload("change", rendered["markdown"])
        payload["validation_context"] = {
            "sections": {
                "implementation": {key: value for key, value in _section("", key_entities=["human_page_authoring"]).items() if key != "human_summary"},
                "deep-reading": {key: value for key, value in _section("", links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}]).items() if key != "human_summary"},
            },
            "current_facts": [],
        }
        result = validate_page_author(payload)
        self.assertEqual("passed", result["status"], result)
        self.assertEqual(
            {"structure", "budget", "links", "disclosure", "current_fact_evidence", "contract_evidence", "applicability_boundary", "validation_context"},
            set(result["checks"]),
        )
        self.assertTrue(all(check["status"] == "passed" for check in result["checks"].values()))

    def test_l4_test_total_and_full_command_fail_disclosure_check(self) -> None:
        payload = _change_payload()
        payload["sections"]["result"]["human_summary"] = "专项测试 268/268 通过。\n\npython.exe ckb.py maintain --out E:/kb"  # type: ignore[index]
        result = render_page_author(payload)
        self.assertEqual("failed", result["status"])
        self.assertEqual("failed", result["validation"]["checks"]["disclosure"]["status"])
        self.assertIn("l4-evidence-leak", {value["reason"] for value in result["errors"]})

    def test_entity_budget_and_current_fact_evidence_fail_in_named_checks(self) -> None:
        rendered = render_page_author(_change_payload())
        budget_payload = self._validation_payload("change", rendered["markdown"])
        budget_payload["validation_context"] = {
            "sections": {
                "implementation": {key: value for key, value in _section("", key_entities=["A", "B", "C", "D"]).items() if key != "human_summary"},
                "deep-reading": {key: value for key, value in _section("", links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}]).items() if key != "human_summary"},
            },
            "current_facts": [],
        }
        budget_result = validate_page_author(budget_payload)
        self.assertEqual("failed", budget_result["checks"]["budget"]["status"])
        self.assertIn("section-key-entity-budget", {value["reason"] for value in budget_result["errors"]})

        feedback = """# 反馈

## 反馈内容
请补充页面边界。
## 影响范围
影响分析页。
## 当前状态
当前状态已经处理完成。
## 后续行动
无需新增动作。
"""
        current_result = validate_page_author(self._validation_payload("feedback", feedback))
        self.assertEqual("failed", current_result["checks"]["current_fact_evidence"]["status"])
        self.assertIn("current-fact-unverified", {value["reason"] for value in current_result["errors"]})

    def test_eight_record_types_have_reopenable_four_case_failure_fixtures(self) -> None:
        expected_types = {"change", "analysis", "pitfall", "experiment", "session", "reference", "learning-note", "feedback"}
        root = FIXTURES / "v3-failures"
        paths = sorted(root.glob("*.json"))
        self.assertEqual(expected_types, {path.stem for path in paths})
        for path in paths:
            fixture = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(path.stem, fixture["page_type"])
            self.assertEqual(
                {"missing_section", "over_budget", "wrong_disclosure", "purposeless_link"},
                set(fixture["cases"]),
            )
            for name, case in fixture["cases"].items():
                with self.subTest(page_type=path.stem, case=name):
                    result = validate_page_author(case["payload"])
                    self.assertEqual("failed", result["status"])
                    self.assertIn(case["expected_reason"], {value["reason"] for value in result["errors"]})

    def test_v3_coverage_mapping_resolves_removed_baseline_methods(self) -> None:
        fixture = json.loads((FIXTURES / "v3-test-coverage-mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(268, fixture["baseline_discovered_tests"])
        self.assertEqual(266, fixture["pre_fix_discovered_tests"])
        self.assertEqual(2, len(fixture["restored_original_tests"]))
        self.assertEqual(29, fixture["removed_method_count"])
        current: set[str] = set()
        for path in (
            ROOT / "tests/test_human_page_templates.py",
            ROOT / "tests/test_human_page_authoring.py",
            ROOT / "tests/test_human_page_template_proposals.py",
            ROOT / "tests/test_human_maintenance_prompts.py",
        ):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            current.update(
                f"{path.stem}.{node.name}.{method.name}"
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                for method in node.body
                if isinstance(method, ast.FunctionDef) and method.name.startswith("test_")
            )
        for name in fixture["restored_original_tests"]:
            self.assertIn(name, current)
        for item in fixture["coverage_mapping"]:
            self.assertTrue(item["v3_tests"])
            for name in item["v3_tests"]:
                self.assertIn(name, current, item["baseline_test"])

    def test_unknown_field_old_version_and_purposeless_link_fail_stably(self) -> None:
        incompatible = validate_page_author({"page_type": "analysis", "markdown": "# X", "contract_version": "1.0.0", "schema_version": 1})
        self.assertEqual("contract-version-incompatible", incompatible["errors"][0]["reason"])
        rendered = render_page_author(_change_payload())
        payload = self._validation_payload("change", rendered["markdown"])
        payload["invented"] = True
        self.assertEqual("unknown-field", validate_page_author(payload)["errors"][0]["reason"])

        readme = _payload(
            "README",
            "Code Knowledge Builder",
            {
                "task-choice": "[这里](guide.md)",
                "structure": "区分人类与机器入口。",
                "install": "交给 Agent 安装。",
                "explain": "交给 Agent 回答问题。",
                "continue": "继续指挥 Agent 阅读。",
            },
        )
        readme["sections"]["task-choice"]["links"] = [  # type: ignore[index]
            {"target": "guide.md", "purpose": "", "kind": "internal"}
        ]
        result = render_page_author(readme)
        self.assertIn("link-purpose-missing", {value["reason"] for value in result["errors"]})

    def test_duplicate_title_path_escape_target_drift_and_existing_section_are_distinct(self) -> None:
        text = """# 页面编写命令变更

## 修改内容
页面编写入口生成完整候选并执行合同检查。
"""
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw, tempfile.TemporaryDirectory() as outside_raw:
            root = Path(raw)
            draft = root / "draft.md"
            draft.write_text(text, encoding="utf-8")
            outside = Path(outside_raw) / "outside.md"
            outside.write_text(text, encoding="utf-8")
            escaped = inspect_page_author("change", "supplement", outside, workspace_root=root)
            self.assertEqual("path-outside-workspace", escaped["errors"][0]["reason"])
            base = {
                "schema_version": 3,
                "contract_version": "3.0.0",
                "page_type": "change",
                "mode": "supplement",
                "source_path": "draft.md",
                "source_sha256": _digest(text),
                "sections": {"why": _section("补充修改原因。")},
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {"sections": {}, "current_facts": []},
                "applicability_boundary": contract.applicability_boundary,
            }
            self.assertEqual("duplicate-title", render_page_author({**base, "title": "重复标题"}, workspace_root=root)["errors"][0]["reason"])
            self.assertEqual("target-drift", render_page_author({**base, "source_sha256": "0" * 64}, workspace_root=root)["errors"][0]["reason"])
            present = {**base, "sections": {"what": _section("重复补充。")}}
            self.assertEqual("field-already-satisfied", render_page_author(present, workspace_root=root)["errors"][0]["reason"])

    def test_inspect_reports_conflicts_and_managed_page_never_allows_direct_edit(self) -> None:
        text = render_page_author(_change_payload())["markdown"] + "\n## 修改原因\n重复章节。\n"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            managed_dir = root / "human/changes"
            managed_dir.mkdir(parents=True)
            page = managed_dir / "change.md"
            page.write_text(text, encoding="utf-8")
            result = inspect_page_author("change", "revise", page, workspace_root=root)
            self.assertEqual("conflicted", result["status"])
            self.assertTrue(result["managed_page"])
            self.assertNotIn("direct-edit", result["allowed_actions"])
            self.assertIn("duplicate-heading", {item["reason"] for item in result["conflict_fields"]})


class HumanPageAuthoringPackageTests(unittest.TestCase):
    def test_all_fourteen_page_types_keep_one_existing_route(self) -> None:
        expected = {
            "INDEX": "INDEX-generator", "WIKI": "WIKI-generator", "RECORDS": "RECORDS-generator", "REFERENCES": "REFERENCES-generator",
            "responsibility": "responsibility-generator", "change": "record", "analysis": "record", "pitfall": "record", "experiment": "record",
            "session": "record", "reference": "reference", "learning-note": "learning-note-generator", "feedback": "feedback", "README": "README-submit",
        }
        for page_type, entrypoint in expected.items():
            self.assertEqual(entrypoint, _package_route(page_type)["entrypoint"])

    def test_package_writes_reopenable_body_and_manifest_and_is_reversible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_dir = root / "artifacts"
            evidence_dir.mkdir()
            source = evidence_dir / "source.md"
            verification = evidence_dir / "verification.json"
            source.write_text("来源说明。\n", encoding="utf-8")
            verification.write_text('{"status":"passed"}\n', encoding="utf-8")
            payload = _change_payload()
            payload["sections"]["result"]["source_refs"] = [  # type: ignore[index]
                {"target": "artifacts/source.md", "purpose": "核对修改来源", "kind": "source", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
                {"target": "reference:reviewed-fixture", "purpose": "核对已审阅资料", "kind": "review"},
            ]
            payload["sections"]["result"]["machine_evidence_refs"] = [  # type: ignore[index]
                {"target": "artifacts/verification.json", "purpose": "复查完整验证", "kind": "log", "sha256": hashlib.sha256(verification.read_bytes()).hexdigest()}
            ]
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            result = package_page_author(payload, "staging/change", workspace_root=root)
            self.assertEqual("ready", result["status"], result)
            package = root / "staging/change"
            body = (package / "body.md").read_bytes()
            manifest_bytes = (package / "manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            self.assertEqual(hashlib.sha256(body).hexdigest(), result["body_sha256"])
            self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), result["manifest_sha256"])
            self.assertEqual("3.0.0", manifest["contract_version"])
            self.assertFalse(manifest["direct_projection_write"])
            result_section = next(value for value in manifest["section_evidence"]["sections"] if value["section_id"] == "result")
            source_copy = next(value for value in result_section["source_refs"] if value["target_basis"] == "manifest-parent")
            uri_ref = next(value for value in result_section["source_refs"] if value["target_basis"] == "uri")
            machine_copy = result_section["machine_evidence_refs"][0]
            self.assertEqual("artifacts/source.md", source_copy["original_target"])
            self.assertEqual("artifacts/verification.json", machine_copy["original_target"])
            self.assertEqual("reference:reviewed-fixture", uri_ref["target"])
            self.assertEqual("uri", uri_ref["target_basis"])
            self.assertTrue(source_copy["target"].startswith("evidence/"))
            self.assertTrue(machine_copy["target"].startswith("evidence/"))
            for value in (source_copy, machine_copy):
                reopened = package / value["target"]
                self.assertTrue(reopened.is_file())
                self.assertEqual(value["sha256"], hashlib.sha256(reopened.read_bytes()).hexdigest())
            self.assertNotIn(b"artifacts/source.md", body)
            self.assertNotIn(b"artifacts/verification.json", body)
            evidence_bytes = (
                json.dumps(manifest["section_evidence"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            self.assertEqual(hashlib.sha256(evidence_bytes).hexdigest(), manifest["section_evidence_sha256"])
            self.assertEqual(manifest["section_evidence_sha256"], result["section_evidence_sha256"])
            self.assertEqual(
                sorted(["body.md", "manifest.json", source_copy["target"], machine_copy["target"]]),
                sorted(manifest["package_owned_paths"]),
            )

            moved = root / "relocated-package"
            shutil.move(package, moved)
            moved_manifest = json.loads((moved / "manifest.json").read_text(encoding="utf-8"))
            moved_section = next(value for value in moved_manifest["section_evidence"]["sections"] if value["section_id"] == "result")
            for value in moved_section["source_refs"] + moved_section["machine_evidence_refs"]:
                if value["target_basis"] == "manifest-parent":
                    reopened = moved / value["target"]
                    self.assertTrue(reopened.is_file())
                    self.assertEqual(value["sha256"], hashlib.sha256(reopened.read_bytes()).hexdigest())
                else:
                    self.assertEqual("reference:reviewed-fixture", value["target"])

            # Package rollback owns only the moved directory and its copied evidence.
            shutil.rmtree(moved)
            (root / "staging").rmdir()
            self.assertEqual(before, sorted(path.relative_to(root).as_posix() for path in root.rglob("*")))

    def test_package_rejects_reference_path_drift_and_invalid_machine_evidence_kind(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            verification = artifacts / "verification.json"
            verification.write_text('{"status":"passed"}\n', encoding="utf-8")
            payload = _change_payload()
            payload["sections"]["result"]["machine_evidence_refs"] = [  # type: ignore[index]
                {"target": "artifacts/verification.json", "purpose": "复查完整验证", "kind": "log", "sha256": "0" * 64}
            ]
            drift = package_page_author(payload, "staging/drift", workspace_root=root)
            self.assertEqual("reference-target-drift", drift["errors"][0]["reason"])
            self.assertFalse((root / "staging/drift").exists())

            payload["sections"]["result"]["machine_evidence_refs"] = [  # type: ignore[index]
                {"target": "machine-evidence:verification", "purpose": "复查完整验证", "kind": "unknown-kind"}
            ]
            invalid = package_page_author(payload, "staging/invalid-kind", workspace_root=root)
            self.assertEqual("validation-context-invalid", invalid["errors"][0]["reason"])
            self.assertFalse((root / "staging/invalid-kind").exists())

    def test_package_rejects_managed_and_existing_paths_and_cli_failure_uses_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertEqual("managed-target-forbidden", package_page_author(_change_payload(), "human/changes/candidate", workspace_root=root)["errors"][0]["reason"])
            (root / "staging/existing").mkdir(parents=True)
            self.assertEqual("staging-target-exists", package_page_author(_change_payload(), "staging/existing", workspace_root=root)["errors"][0]["reason"])
            input_path = root / "input.json"
            input_path.write_text(json.dumps({"page_type": "unknown", "markdown": "# X"}), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", str(ROOT / "scripts/ckb.py"), "page-author", "validate", "--input", str(input_path)],
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_cli_environment(),
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual("failed", json.loads(completed.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
