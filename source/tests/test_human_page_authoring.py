from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ckb_core.human_page_authoring import (  # noqa: E402
    _package_route,
    init_page_author,
    inspect_page_author,
    package_page_author,
    render_page_author,
    validate_page_author,
)
from ckb_core.human_page_templates import (  # noqa: E402
    get_human_page_template,
    list_human_page_types,
)


FIXTURES = ROOT / "tests/fixtures/human-page-authoring"


def _cli_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return environment


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _payload(page_type: str, title: str, bodies: dict[str, str]) -> dict[str, object]:
    contract = get_human_page_template(page_type)
    return {
        "schema_version": 1,
        "contract_version": "1.0.0",
        "page_type": page_type,
        "mode": "new",
        "title": title,
        "sections": {section_id: {"body": body} for section_id, body in bodies.items()},
        "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
        "validation_context": {"key_entities": [], "links": [], "current_facts": []},
        "applicability_boundary": contract.applicability_boundary,
    }


def _change_payload() -> dict[str, object]:
    payload = _payload(
        "change",
        "页面编写命令变更",
        {
            "what": "页面编写命令生成完整候选并执行合同检查。",
            "when": "合并时间记录在验证清单。",
            "why": "原流程缺少按页面类型收集字段的入口。",
            "how": "`human_page_authoring` 负责骨架、渲染和检查。",
            "features": "该入口与冻结模板注册表直接关联。",
            "verification-boundary": "固定样例通过；结论只覆盖 schema 化输入。",
            "source-ranges": "- `human_page_authoring.py`：承担确定性页面编写。",
        },
    )
    payload["validation_context"] = {
        "key_entities": ["human_page_authoring"],
        "links": [],
        "current_facts": [],
    }
    return payload


class HumanPageAuthoringInitTests(unittest.TestCase):
    def test_all_fourteen_types_return_minimal_skeletons_for_three_modes(self) -> None:
        self.assertEqual(14, len(list_human_page_types()))
        for page_type in list_human_page_types():
            for mode in ("new", "supplement", "revise"):
                with self.subTest(page_type=page_type, mode=mode):
                    result = init_page_author(page_type, mode)
                    self.assertEqual("ready", result["status"])
                    self.assertEqual(page_type, result["page_type"])
                    self.assertEqual(mode, result["mode"])
                    skeleton = result["skeleton"]
                    self.assertEqual(page_type, skeleton["page_type"])
                    if mode == "new":
                        self.assertIn("title", skeleton)
                        self.assertEqual(
                            {section.section_id for section in get_human_page_template(page_type).required_sections},
                            set(skeleton["sections"]),
                        )
                    elif mode == "supplement":
                        self.assertNotIn("title", skeleton)
                        self.assertEqual({}, skeleton["sections"])
                    else:
                        self.assertNotIn("title", skeleton)
                        self.assertEqual([], skeleton["revisions"])

    def test_change_and_readme_keep_user_accepted_headings(self) -> None:
        change = init_page_author("change", "new")["skeleton"]
        readme = init_page_author("README", "new")["skeleton"]
        self.assertEqual("修改内容", get_human_page_template("change").required_sections[0].heading)
        self.assertIn("what", change["sections"])
        self.assertEqual(
            (
                "先选择你要完成的任务",
                "了解本项目知识库结构",
                "让 Agent 安装本项目",
                "让 Agent 解释自己的项目",
            ),
            tuple(section.heading for section in get_human_page_template("README").required_sections),
        )
        self.assertIn("explain-own-project", readme["sections"])


class HumanPageAuthoringRenderTests(unittest.TestCase):
    def test_new_change_renders_and_immediately_validates(self) -> None:
        result = render_page_author(_change_payload())
        self.assertEqual("ready", result["status"], result)
        self.assertEqual("passed", result["validation"]["status"])
        self.assertIn("## 修改内容", result["markdown"])
        self.assertEqual(_digest(result["markdown"]), result["markdown_sha256"])

    def test_readme_renders_with_accepted_title_and_sections(self) -> None:
        payload = _payload(
            "README",
            "Code Knowledge Builder",
            {
                "task-choice": "选择了解结构、安装或解释项目。",
                "structure": "区分人类入口与机器入口。",
                "install": "安装指令只完成安装验收。",
                "explain-own-project": "解释指令为目标仓库建库并回答问题。",
            },
        )
        payload["validation_context"] = {
            "key_entities": ["结构", "安装", "解释"],
            "links": [],
            "current_facts": [],
        }
        result = render_page_author(payload)
        self.assertEqual("ready", result["status"], result)
        self.assertTrue(result["markdown"].startswith("# Code Knowledge Builder\n"))
        self.assertIn("## 让 Agent 解释自己的项目", result["markdown"])

    def test_missing_fields_returns_only_the_field_list_without_partial_markdown(self) -> None:
        payload = _change_payload()
        del payload["sections"]["why"]
        result = render_page_author(payload)
        self.assertEqual("missing-fields", result["status"])
        self.assertEqual(["sections.why.body"], result["missing_fields"])
        self.assertNotIn("markdown", result)
        self.assertNotIn("validation", result)

    def test_supplement_reuses_title_and_adds_only_missing_section(self) -> None:
        existing = """# 页面编写命令变更

## 修改内容
页面编写命令生成完整候选并执行合同检查。
## 修改时间
合并时间记录在验证清单。
## 修改方式
`human_page_authoring` 负责骨架、渲染和检查。
## 关联特性
该入口与冻结模板注册表直接关联。
## 验证结果与适用边界
固定样例通过；结论只覆盖 schema 化输入。
## 关键源码范围
- `human_page_authoring.py`：承担确定性页面编写。
"""
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"
            draft.write_text(existing, encoding="utf-8")
            inspected = inspect_page_author("change", "supplement", draft, workspace_root=root)
            self.assertEqual(["sections.why.body"], inspected["missing_fields"])
            payload = {
                "schema_version": 1,
                "contract_version": "1.0.0",
                "page_type": "change",
                "mode": "supplement",
                "source_path": "draft.md",
                "source_sha256": inspected["source"]["sha256"],
                "sections": {"why": {"body": "原流程缺少按页面类型收集字段的入口。"}},
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {
                    "key_entities": ["human_page_authoring"],
                    "links": [],
                    "current_facts": [],
                },
                "applicability_boundary": contract.applicability_boundary,
            }
            result = render_page_author(payload, workspace_root=root)
            self.assertEqual("ready", result["status"], result)
            self.assertEqual(1, result["markdown"].count("# 页面编写命令变更"))
            self.assertIn("## 修改原因", result["markdown"])

    def test_revise_requires_exact_current_paragraph_and_source(self) -> None:
        initial = render_page_author(_change_payload())["markdown"]
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"
            draft.write_text(initial, encoding="utf-8")
            payload = {
                "schema_version": 1,
                "contract_version": "1.0.0",
                "page_type": "change",
                "mode": "revise",
                "source_path": "draft.md",
                "source_sha256": _digest(initial),
                "revisions": [
                    {
                        "section_id": "why",
                        "current": "原流程缺少按页面类型收集字段的入口。",
                        "replacement": "原流程缺少按页面类型收集和复核字段的入口。",
                        "source": "review-record:fixture",
                    }
                ],
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {
                    "key_entities": ["human_page_authoring"],
                    "links": [],
                    "current_facts": [],
                },
                "applicability_boundary": contract.applicability_boundary,
            }
            result = render_page_author(payload, workspace_root=root)
            self.assertEqual("ready", result["status"], result)
            self.assertIn("收集和复核字段", result["markdown"])
            self.assertNotIn("原流程缺少按页面类型收集字段的入口。", result["markdown"])

            payload["revisions"][0]["source"] = ""
            missing_source = render_page_author(payload, workspace_root=root)
            self.assertEqual("missing-fields", missing_source["status"])
            self.assertEqual(["revisions[0].source"], missing_source["missing_fields"])
            self.assertNotIn("markdown", missing_source)

    def test_cli_stdout_is_one_json_document(self) -> None:
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
        self.assertEqual("ready", parsed["status"])
        self.assertEqual("", completed.stderr)


class HumanPageAuthoringValidationFailureTests(unittest.TestCase):
    def _validation_payload(self, page_type: str, markdown: str) -> dict[str, object]:
        contract = get_human_page_template(page_type)
        return {
            "schema_version": 1,
            "contract_version": "1.0.0",
            "page_type": page_type,
            "markdown": markdown,
            "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
            "validation_context": {"key_entities": [], "links": [], "current_facts": []},
            "applicability_boundary": contract.applicability_boundary,
        }

    def test_validate_returns_all_six_contract_checks(self) -> None:
        rendered = render_page_author(_change_payload())
        payload = self._validation_payload("change", rendered["markdown"])
        payload["validation_context"] = _change_payload()["validation_context"]
        result = validate_page_author(payload)
        self.assertEqual("passed", result["status"], result)
        self.assertEqual(
            {
                "structure",
                "budget",
                "links",
                "current_fact_evidence",
                "contract_evidence",
                "applicability_boundary",
                "validation_context",
            },
            set(result["checks"]),
        )
        self.assertTrue(all(check["status"] == "passed" for check in result["checks"].values()))

    def test_unknown_field_type_and_version_fail_stably(self) -> None:
        unknown_type = validate_page_author({"page_type": "unknown", "markdown": "# X"})
        self.assertEqual("unknown-page-type", unknown_type["errors"][0]["reason"])
        incompatible = validate_page_author(
            {"page_type": "analysis", "markdown": "# X", "contract_version": "2.0.0"}
        )
        self.assertEqual("contract-version-incompatible", incompatible["errors"][0]["reason"])
        payload = self._validation_payload("analysis", "# X")
        payload["invented"] = True
        unknown_field = validate_page_author(payload)
        self.assertEqual("unknown-field", unknown_field["errors"][0]["reason"])

    def test_entity_budget_and_current_fact_evidence_fail_in_named_checks(self) -> None:
        change = render_page_author(_change_payload())["markdown"]
        over_budget = self._validation_payload("change", change)
        over_budget["validation_context"] = {
            "key_entities": ["A", "B", "C", "D"],
            "links": [],
            "current_facts": [],
        }
        budget_result = validate_page_author(over_budget)
        self.assertEqual("failed", budget_result["status"])
        self.assertEqual("failed", budget_result["checks"]["budget"]["status"])
        self.assertIn("key-entity-budget", {error["reason"] for error in budget_result["errors"]})

        current_fact = self._validation_payload(
            "analysis", (FIXTURES / "analysis-current-fact.md").read_text(encoding="utf-8")
        )
        current_result = validate_page_author(current_fact)
        self.assertEqual("failed", current_result["checks"]["current_fact_evidence"]["status"])
        self.assertIn("current-fact-unverified", {error["reason"] for error in current_result["errors"]})

    def test_purposeless_link_fails_link_check(self) -> None:
        markdown = """# 外部资料

## 这份资料讲什么
资料说明确定性检索方法。
## 关键结论
- 每项结论回链原文。
## 来源
- [这里](vscode://file/E:/fixture/source.md:1:1)
"""
        payload = self._validation_payload("reference", markdown)
        result = validate_page_author(payload)
        self.assertEqual("failed", result["checks"]["links"]["status"])
        self.assertIn("link-purpose-missing", {error["reason"] for error in result["errors"]})

    def test_duplicate_title_path_escape_and_target_drift_are_distinct_failures(self) -> None:
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw, tempfile.TemporaryDirectory() as outside_raw:
            root = Path(raw)
            draft = root / "draft.md"
            text = (FIXTURES / "change-missing-reason.md").read_text(encoding="utf-8")
            draft.write_text(text, encoding="utf-8")
            outside = Path(outside_raw) / "outside.md"
            outside.write_text(text, encoding="utf-8")
            escaped = inspect_page_author("change", "supplement", outside, workspace_root=root)
            self.assertEqual("path-outside-workspace", escaped["errors"][0]["reason"])
            base = {
                "schema_version": 1,
                "contract_version": "1.0.0",
                "page_type": "change",
                "mode": "supplement",
                "source_path": "draft.md",
                "source_sha256": _digest(text),
                "sections": {"why": {"body": "补充修改原因。"}},
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {
                    "key_entities": ["human_page_authoring"],
                    "links": [],
                    "current_facts": [],
                },
                "applicability_boundary": contract.applicability_boundary,
            }
            duplicate = render_page_author({**base, "title": "页面编写命令变更"}, workspace_root=root)
            self.assertEqual("duplicate-title", duplicate["errors"][0]["reason"])
            drifted = render_page_author({**base, "source_sha256": "0" * 64}, workspace_root=root)
            self.assertEqual("target-drift", drifted["errors"][0]["reason"])

    def test_inspect_reports_conflicts_and_managed_page_never_allows_direct_edit(self) -> None:
        text = (FIXTURES / "change-complete.md").read_text(encoding="utf-8")
        text += "\n## 修改原因\n重复章节。\n"
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

    def test_supplement_rejects_a_section_already_present(self) -> None:
        text = (FIXTURES / "change-complete.md").read_text(encoding="utf-8")
        contract = get_human_page_template("change")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"
            draft.write_text(text, encoding="utf-8")
            payload = {
                "schema_version": 1,
                "contract_version": "1.0.0",
                "page_type": "change",
                "mode": "supplement",
                "source_path": "draft.md",
                "source_sha256": _digest(text),
                "sections": {"why": {"body": "重复补充。"}},
                "evidence": {field: "fixture-evidence" for field in contract.evidence_requirements.required_fields},
                "validation_context": {
                    "key_entities": ["human_page_authoring"],
                    "links": [],
                    "current_facts": [],
                },
                "applicability_boundary": contract.applicability_boundary,
            }
            result = render_page_author(payload, workspace_root=root)
            self.assertEqual("field-already-satisfied", result["errors"][0]["reason"])


class HumanPageAuthoringPackageTests(unittest.TestCase):
    def test_all_fourteen_page_types_have_one_expected_route(self) -> None:
        expected = {
            "INDEX": "INDEX-generator",
            "WIKI": "WIKI-generator",
            "RECORDS": "RECORDS-generator",
            "REFERENCES": "REFERENCES-generator",
            "responsibility": "responsibility-generator",
            "change": "record",
            "analysis": "record",
            "pitfall": "record",
            "experiment": "record",
            "session": "record",
            "reference": "reference",
            "learning-note": "learning-note-generator",
            "feedback": "feedback",
            "README": "README-submit",
        }
        self.assertEqual(set(list_human_page_types()), set(expected))
        for page_type, entrypoint in expected.items():
            with self.subTest(page_type=page_type):
                route = _package_route(page_type)
                self.assertEqual(entrypoint, route["entrypoint"])
                self.assertEqual(1, sum(key in route for key in ("command", "submission", "plugin_command")))
                if page_type not in {"README", "learning-note"}:
                    self.assertEqual("ckb.py", route["command"][0])

    def test_package_writes_only_reopenable_manifest_and_body_with_hashes(self) -> None:
        payload = _change_payload()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            result = package_page_author(payload, "staging/change", workspace_root=root)
            self.assertEqual("ready", result["status"], result)
            package = root / "staging/change"
            self.assertEqual(["body.md", "manifest.json"], sorted(path.name for path in package.iterdir()))
            body = (package / "body.md").read_bytes()
            manifest_bytes = (package / "manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            self.assertEqual(hashlib.sha256(body).hexdigest(), result["body_sha256"])
            self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), result["manifest_sha256"])
            self.assertFalse(manifest["direct_projection_write"])
            self.assertEqual("record", manifest["next_entry"]["entrypoint"])
            self.assertFalse(any(part in {"human", "markdown", "machine"} for path in root.rglob("*") for part in path.parts))

            # Isolated rollback fixture: delete only the two package-owned files,
            # then the two newly created directories and recover the exact baseline.
            (package / "body.md").unlink()
            (package / "manifest.json").unlink()
            package.rmdir()
            (root / "staging").rmdir()
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            self.assertEqual(before, after)

    def test_package_rejects_managed_projection_and_existing_staging_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            managed = package_page_author(_change_payload(), "human/changes/candidate", workspace_root=root)
            self.assertEqual("managed-target-forbidden", managed["errors"][0]["reason"])
            existing = root / "staging/existing"
            existing.mkdir(parents=True)
            collision = package_page_author(_change_payload(), existing, workspace_root=root)
            self.assertEqual("staging-target-exists", collision["errors"][0]["reason"])

    def test_cli_failure_is_one_json_document_with_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            input_path = Path(raw) / "input.json"
            input_path.write_text(json.dumps({"page_type": "unknown", "markdown": "# X"}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(ROOT / "scripts/ckb.py"),
                    "page-author",
                    "validate",
                    "--input",
                    str(input_path),
                ],
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_cli_environment(),
            )
            self.assertEqual(2, completed.returncode)
            parsed = json.loads(completed.stdout)
            self.assertEqual("failed", parsed["status"])
            self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
