from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.llm_wiki_capabilities import compact_agent_brief
from ckb_core.scope_extension import attach_scope_extension_offer
from ckb_core.stdio_server import serve_stdio


class ScopeExtensionOfferTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-scope-offer-")
        self.output = Path(self.temporary.name) / "output"
        (self.output / "machine").mkdir(parents=True)
        (self.output / "machine/knowledge.sqlite").write_bytes(b"fixture")
        self.commit = "a" * 40
        repository = {"root": str(Path(self.temporary.name) / "repo"), "commit": self.commit}
        self._write_json(self.output / "state.json", {"status": "complete", "repository": repository})
        self._write_json(
            self.output / "scope.json",
            {
                "repository": repository,
                "selected_file_paths": ["inside.py"],
                "selected_entity_ids": ["entity-inside"],
                "selectors": {"entries": ["python:inside.py#inside"], "scope_paths": []},
            },
        )
        files = [
            self._file("inside.py", "b" * 40),
            self._file("extra.py", "c" * 40),
            self._file("ambiguous.py", "d" * 40),
            self._file("other.py", "e" * 40),
        ]
        entities = [
            self._entity("entity-inside", "inside.py", "inside"),
            self._entity("entity-extra", "extra.py", "second"),
            self._entity("entity-ambiguous-a", "ambiguous.py", "first"),
            self._entity("entity-ambiguous-b", "ambiguous.py", "second"),
            self._entity("entity-other", "other.py", "other"),
        ]
        self._write_json(
            self.output / "catalog.json",
            {"repository": repository, "files": files, "entities": entities},
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_json(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _file(path: str, blob: str) -> dict:
        return {
            "file": {
                "path": path,
                "language": "python",
                "blob": blob,
                "size": 10,
                "mode": "100644",
            },
            "parse": {"status": "passed"},
        }

    @staticmethod
    def _entity(entity_id: str, path: str, qualified_name: str) -> dict:
        return {
            "id": entity_id,
            "kind": "function",
            "language": "python",
            "path": path,
            "name": qualified_name,
            "qualified_name": qualified_name,
        }

    def retrieval(self, question: str, **updates) -> dict:
        value = {
            "schema_version": 5,
            "status": "needs-source-read",
            "question": question,
            "profile": "fast",
            "reason": "机器知识库没有来源绑定的候选，请按 scope 或源码路径继续读取。",
            "warnings": {"status": "complete", "warning_count": 0},
            "fact_freshness": {
                "state": "current",
                "bound_commit": self.commit,
                "current_head": self.commit,
            },
        }
        value.update(updates)
        return value

    def test_unique_out_of_scope_path_returns_confirmation_only_offer(self) -> None:
        result = attach_scope_extension_offer(self.output, self.retrieval("请审阅 extra.py 的实现"))
        offer = result["scope_extension_offer"]
        self.assertEqual(offer["schema_version"], 1)
        self.assertEqual(offer["status"], "confirmation-required")
        self.assertTrue(offer["requires_confirmation"])
        self.assertFalse(offer["next"]["automatic_scope_extension"])
        self.assertEqual(offer["selector"]["value"], "python:extra.py#second")
        self.assertEqual(offer["evidence"]["repository_commit"], self.commit)
        self.assertEqual(offer["evidence"]["tracked_blob"], "c" * 40)
        command = offer["on_confirmation"]["command"]
        self.assertEqual(command[command.index("--entry") + 1], "python:extra.py#second")
        self.assertEqual(offer["on_defer"]["action"], "continue-narrow-source-read")

    def test_unique_out_of_scope_entry_uses_same_canonical_selector(self) -> None:
        result = attach_scope_extension_offer(
            self.output,
            self.retrieval("请定位 python:extra.py#second"),
        )
        self.assertEqual(result["scope_extension_offer"]["selector"]["value"], "python:extra.py#second")

    def test_negative_matrix_does_not_offer_scope_extension(self) -> None:
        cases = [
            ("ordinary-zero-hit", self.retrieval("没有任何路径线索"), None),
            ("in-scope-miss", self.retrieval("继续查看 inside.py"), "already-in-scope"),
            ("ambiguous-path", self.retrieval("继续查看 ambiguous.py"), "ambiguous-path"),
            ("missing-git-path", self.retrieval("继续查看 missing.py"), "no-fixed-git-evidence"),
            (
                "stale",
                self.retrieval(
                    "继续查看 extra.py",
                    fact_freshness={
                        "state": "stale-committed",
                        "bound_commit": self.commit,
                        "current_head": "f" * 40,
                    },
                ),
                "fact-freshness-not-current",
            ),
            (
                "service-error",
                self.retrieval(
                    "继续查看 extra.py",
                    keyword_fallback={"status": "fallback", "provider": {"status": "failed", "failure_type": "timeout"}},
                ),
                "retrieval-service-failure",
            ),
            (
                "multiple-candidates",
                self.retrieval("比较 extra.py 和 other.py"),
                "multiple-candidates",
            ),
            (
                "path-escape",
                self.retrieval("查看 python:../extra.py#second"),
                "invalid-selector",
            ),
            (
                "absolute-path",
                self.retrieval("查看 /extra.py"),
                "invalid-selector",
            ),
            (
                "drive-path",
                self.retrieval("查看 python:C:/extra.py#second"),
                "invalid-selector",
            ),
        ]
        for name, retrieval, expected_code in cases:
            with self.subTest(name=name):
                result = attach_scope_extension_offer(self.output, retrieval)
                self.assertNotIn("scope_extension_offer", result)
                if expected_code is None:
                    self.assertNotIn("scope_extension_diagnostic", result)
                else:
                    self.assertEqual(result["scope_extension_diagnostic"]["code"], expected_code)

    def test_unrelated_cpp_compile_commands_warning_does_not_block_python_offer(self) -> None:
        warnings = {
            "status": "warning",
            "warning_count": 1,
            "examples": [
                {
                    "kind": "compile-commands-unavailable",
                    "language": "cpp",
                    "file": "compile_commands.json",
                    "range": None,
                    "diagnostic_categories": [],
                    "diagnostic_count": 0,
                    "coverage": {},
                    "precision": "bounded-approximate",
                    "build_evidence": {"resolution": "fallback-no-evidence", "selected": None, "paths": []},
                    "affected_entity_count": 0,
                    "absence_inference_allowed": False,
                }
            ],
            "omitted_warning_count": 0,
            "absence_inference_allowed": False,
            "message_zh": "警告范围或有界近似语义结果不完整，不可据此推断未检出事实在源码中不存在。",
        }
        retrieval = self.retrieval("继续查看 extra.py", warnings=warnings)
        result = attach_scope_extension_offer(self.output, retrieval)
        self.assertEqual(result["warnings"], warnings)
        self.assertEqual(result["scope_extension_offer"]["selector"]["path"], "extra.py")
        self.assertNotIn("scope_extension_diagnostic", result)

    def test_candidate_path_warning_with_absence_false_suppresses_offer(self) -> None:
        warnings = {
            "status": "warning",
            "warning_count": 1,
            "examples": [
                {
                    "kind": "tree-sitter-local-syntax",
                    "language": None,
                    "file": "extra.py",
                    "range": {"start_byte": 0, "end_byte": 8, "start_line": 1, "end_line": 1},
                    "diagnostic_categories": ["missing"],
                    "diagnostic_count": 1,
                    "coverage": {"error_bytes": 8, "source_bytes": 10},
                    "precision": None,
                    "build_evidence": {},
                    "affected_entity_count": 1,
                    "absence_inference_allowed": False,
                }
            ],
            "omitted_warning_count": 0,
            "absence_inference_allowed": False,
            "message_zh": "警告范围或有界近似语义结果不完整，不可据此推断未检出事实在源码中不存在。",
        }
        result = attach_scope_extension_offer(
            self.output,
            self.retrieval("继续查看 extra.py", warnings=warnings),
        )
        self.assertEqual(result["warnings"], warnings)
        self.assertNotIn("scope_extension_offer", result)
        diagnostic = result["scope_extension_diagnostic"]
        self.assertEqual(diagnostic["code"], "source-warning-present")
        self.assertEqual(diagnostic["evidence"]["candidate_path"], "extra.py")
        self.assertEqual(diagnostic["evidence"]["warnings"][0]["file"], "extra.py")
        self.assertFalse(diagnostic["evidence"]["warnings"][0]["absence_inference_allowed"])

    def test_passed_retrieval_without_explicit_selector_never_offers(self) -> None:
        retrieval = self.retrieval("请审阅当前实现", status="passed", pack="pack.md")
        result = attach_scope_extension_offer(self.output, retrieval)
        self.assertNotIn("scope_extension_offer", result)
        self.assertNotIn("scope_extension_diagnostic", result)

    def test_passed_broad_match_still_offers_for_explicit_out_of_scope_selector(self) -> None:
        retrieval = self.retrieval(
            "请审阅 extra.py 的实现",
            status="passed",
            pack="pack.md",
            selected_entities=[{"kind": "file", "source_path": "inside.py"}],
        )
        result = attach_scope_extension_offer(self.output, retrieval)
        self.assertEqual(
            result["scope_extension_offer"]["evidence"]["evidence_adequacy"],
            "insufficient-for-explicit-selector",
        )

    def test_brief_retains_offer_and_confirmation_next_action(self) -> None:
        retrieval = attach_scope_extension_offer(self.output, self.retrieval("请审阅 extra.py 的实现"))
        brief = compact_agent_brief(self.output, retrieval)
        self.assertEqual(brief["scope_extension_offer"], retrieval["scope_extension_offer"])
        self.assertEqual(brief["next"], "await-scope-extension-confirmation")
        self.assertIsNone(brief["pack"])
        self.assertFalse(brief["full_record_retained"])

    def test_stdio_returns_same_offer_once_then_suppresses_repeat(self) -> None:
        canonical = attach_scope_extension_offer(self.output, self.retrieval("请审阅 extra.py 的实现"))

        def fake_retrieve(path, question, budget, max_pages, profile):
            self.assertEqual(path, self.output.resolve())
            return json.loads(json.dumps(canonical, ensure_ascii=False))

        requests = "\n".join(
            [
                json.dumps({"id": "first", "method": "retrieve", "question": "请审阅 extra.py 的实现"}),
                json.dumps({"id": "second", "method": "retrieve", "question": "请审阅 extra.py 的实现"}),
                json.dumps({"id": "stop", "method": "shutdown"}),
            ]
        ) + "\n"
        destination = io.StringIO()
        summary = serve_stdio(
            self.output,
            input_stream=io.StringIO(requests),
            output_stream=destination,
            retrieve=fake_retrieve,
        )
        responses = [json.loads(line) for line in destination.getvalue().splitlines()]
        self.assertTrue(all(response["ok"] for response in responses))
        self.assertEqual(responses[0]["result"]["scope_extension_offer"], canonical["scope_extension_offer"])
        self.assertNotIn("scope_extension_offer", responses[1]["result"])
        self.assertEqual(
            responses[1]["result"]["scope_extension_diagnostic"]["code"],
            "offer-already-presented",
        )
        self.assertEqual(responses[1]["result"]["status"], "needs-source-read")
        self.assertEqual(summary["failed"], 0)


if __name__ == "__main__":
    unittest.main()
