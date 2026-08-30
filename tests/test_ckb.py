from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
CLI = SKILL_ROOT / "scripts" / "ckb.py"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from ckb_core.common import CkbError, background_process_options, run, stable_id
from ckb_core.feedback import (
    audit_feedback,
    create_feedback,
    list_feedback,
    locate_feedback,
    resolve_feedback,
)
from ckb_core.graphify_core import GRAPHIFY_COMMIT, audit_graphify
from ckb_core.machine_knowledge import FAST_RETRIEVAL_OVERSCAN, retrieve_machine, search_terms
from ckb_core.llm_wiki_capabilities import (
    CAPABILITY_STATUSES,
    capability_matrix,
    render_capability_matrix_markdown,
)
from ckb_core.navigation import DIRECT_RELATION_LIMIT, estimated_tokens
from ckb_core.obsidian_plugin import (
    deploy_obsidian_plugin,
    deploy_obsidian_plugin_to_vault,
    obsidian_plugin_status,
    register_obsidian_plugin,
    remove_obsidian_plugin,
)
from ckb_core.output_contract import audit_output_contract, project_output_contract
from ckb_core.page_config import DEFAULT_PAGE_CONFIG, page_config_sha256
from ckb_core.pipeline import (
    LOGSEQ_FILE_GRAPH_CONFIG_COMMIT,
    LOGSEQ_FILE_GRAPH_CONFIG_SHA256,
    _audit_markdown,
    _logical_projection,
)
from ckb_core.providers import _fallback_flags, _provider_status
from ckb_core.stdio_server import _record_explanation, serve_stdio
from ckb_core.work_record_index import audit_work_record_index, refresh_work_record_index

PYTHON = Path(os.environ.get("CKB_TEST_PYTHON", sys.executable))
TOOLS_PYTHON = Path(os.environ.get("CKB_TEST_PYTHONPATH", ""))


def invoke(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    if TOOLS_PYTHON:
        process_env["PYTHONPATH"] = str(TOOLS_PYTHON) + os.pathsep + process_env.get("PYTHONPATH", "")
    process_env["PYTHONUTF8"] = "1"
    process_env["PYTHONDONTWRITEBYTECODE"] = "1"
    process_env["CKB_TEST_PROVIDER"] = "deterministic-fixture"
    if env:
        process_env.update(env)
    return subprocess.run(
        [str(PYTHON), str(CLI), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=process_env,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def git(repo: Path, *args: str) -> None:
    completed = subprocess.run(["git", "-C", str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        raise RuntimeError(completed.stderr)


def make_repo(root: Path) -> Path:
    repo = root / "fixture"
    repo.mkdir()
    write(
        repo / "py" / "service.py",
        """
from .helper import helper_value

class OrderService:
    def save_order(self, value):
        with open("orders.txt", "a") as handle:
            handle.write(str(value))
        return helper_value(value)

def run_order(value):
    return OrderService().save_order(value)
""",
    )
    write(
        repo / "py" / "helper.py",
        """
from enum import Enum

class Mode(Enum):
    FAST = 1

def helper_value(value):
    return value > 0
""",
    )
    write(
        repo / "js" / "main.js",
        """
export class AppController {
  async start(value) {
    return saveValue(value);
  }
}
export function saveValue(value) {
  return value + 1;
}
""",
    )
    write(
        repo / "native" / "math.c",
        """
int add_value(int left, int right) {
  return left + right;
}
""",
    )
    write(
        repo / "native" / "engine.cpp",
        """
class Engine {
public:
  int start(int value) { return value + 1; }
};
""",
    )
    write(repo / "native" / "api.h", "int api_value(int value);")
    write(repo / "native" / "api.hpp", "class ApiModel { public: int value; };")
    write(repo / "native" / "extra.cc", "int extra_cc(int value) { return value; }")
    write(repo / "native" / "extra.cxx", "int extra_cxx(int value) { return value; }")
    write(repo / "js" / "module.mjs", "export function moduleValue(value) { return value; }")
    write(repo / "js" / "common.cjs", "exports.commonValue = function commonValue(value) { return value; };")
    write(repo / "node_modules" / "ignored.js", "export function ignored() { return 1; }")
    write(repo / "scripts" / "_vendor" / "ignored.py", "def ignored_vendor(): return 1")
    git(repo, "init")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture")
    return repo


def review_all(output: Path) -> None:
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    for chunk in state["chunks"]:
        chunk_id = chunk["id"]
        built = invoke("build-chunk", "--out", str(output), "--chunk", chunk_id)
        if built.returncode:
            raise AssertionError(f"build failed {built.returncode}: {built.stdout}\n{built.stderr}")
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    for pack in state["review_packs"]:
        template_path = Path(pack["review_template_path"])
        review = json.loads(template_path.read_text(encoding="utf-8"))
        for item in review["reviews"]:
            if pack["kind"] == "appendix-review":
                item["description_zh"] = "该附属实体在固定源码范围内完成一项明确的局部处理。"
            else:
                item.update({
                    "meaning_zh": "该实体表示测试仓库中可从固定 Git 来源定位的代码定义。",
                    "role_zh": "该实体承担测试数据流中的具体处理职责并连接相邻代码关系。",
                    "change_when_zh": "当对应功能、输入输出或相邻调用关系发生变化时检查并修改此实体。",
                })
            item.update({"evidence_note": "已重新读取模板记录的 Git 源码范围并核对实体名称和职责。", "status": "agent-reviewed"})
        review_path = output / "review-packs" / pack["id"] / "review.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
        submitted = invoke("review-pack", "--out", str(output), "--pack", pack["id"], "--review", str(review_path))
        if submitted.returncode:
            raise AssertionError(f"review failed {submitted.returncode}: {submitted.stdout}\n{submitted.stderr}")


class CodeKnowledgeBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-test-")
        self.root = Path(self.temp.name)
        self.repo = make_repo(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_noninteractive_subprocesses_use_the_platform_background_flag(self) -> None:
        options = background_process_options()
        self.assertEqual(background_process_options(visible=True), {})
        if os.name == "nt" and getattr(subprocess, "CREATE_NO_WINDOW", 0):
            self.assertEqual(options, {"creationflags": subprocess.CREATE_NO_WINDOW})
        else:
            self.assertEqual(options, {})
        completed = subprocess.CompletedProcess(["fixture"], 0, "ok", "")
        with (
            patch("ckb_core.common.background_process_options", return_value={"creationflags": 12345}),
            patch("ckb_core.common.subprocess.run", return_value=completed) as launched,
        ):
            result = run(["fixture"], timeout=2)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(launched.call_args.kwargs["creationflags"], 12345)

    def test_llm_wiki_capability_matrix_has_closed_four_state_boundaries(self) -> None:
        matrix = capability_matrix()
        self.assertEqual(matrix["status_order"], list(CAPABILITY_STATUSES))
        self.assertEqual(sum(matrix["counts"].values()), len(matrix["capabilities"]))
        self.assertEqual(len({item["id"] for item in matrix["capabilities"]}), len(matrix["capabilities"]))
        required = {
            "id", "area", "name", "status", "input", "output", "dependencies",
            "license", "data_boundary", "completion_gate", "batch",
        }
        for item in matrix["capabilities"]:
            self.assertEqual(set(item), required)
            self.assertIn(item["status"], CAPABILITY_STATUSES)
            self.assertTrue(all(str(item[field]).strip() for field in required))
        reference = SKILL_ROOT / "references/llm-wiki-capability-matrix.md"
        self.assertEqual(reference.read_text(encoding="utf-8"), render_capability_matrix_markdown())

    def test_reviewed_text_reference_is_searchable_revisioned_and_reversible(self) -> None:
        output = self.root / "reference-output"
        initialized = invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown")
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        review_all(output)
        self.assertEqual(invoke("merge", "--out", str(output)).returncode, 0)
        finalized = invoke("finalize", "--out", str(output))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)

        source = self.root / "stellar-compression.md"
        source.write_text(
            "# 星河压缩协议\n\n"
            "## 核心方法\n"
            "星河压缩协议先建立稳定词典，再对重复片段执行有界替换。\n"
            "该方法要求解码端保留同一词典版本。\n\n"
            "## 约束\n"
            "资料强调任何摘要都必须回到原文范围。\n",
            encoding="utf-8",
        )
        ingested = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(source),
            "--title", "星河压缩协议", "--origin", "本地测试资料", "--license", "CC0-1.0",
            "--author", "Fixture Author",
        )
        self.assertEqual(ingested.returncode, 4, ingested.stderr)
        record = json.loads(ingested.stdout)
        self.assertEqual(record["status"], "pending-agent-review")
        reference_id = record["reference_id"]
        self.assertTrue(Path(record["source"]).is_file())
        self.assertFalse((output / "human/references/星河压缩协议.md").exists())
        pending_audit = invoke("reference", "audit", "--out", str(output))
        self.assertEqual(pending_audit.returncode, 4, pending_audit.stderr)
        self.assertEqual(json.loads(pending_audit.stdout)["status"], "pending-agent-review")
        pending_maintenance = invoke("maintain", "--out", str(output))
        self.assertEqual(pending_maintenance.returncode, 5)
        self.assertIn("references", json.loads(pending_maintenance.stdout)["failed_checks"])

        repeated = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(source),
            "--title", "星河压缩协议", "--origin", "本地测试资料", "--license", "CC0-1.0",
        )
        self.assertEqual(repeated.returncode, 4)
        self.assertTrue(json.loads(repeated.stdout)["idempotent"])
        invalid_license = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(source),
            "--title", "无许可资料", "--origin", "本地测试资料二", "--license", "unknown",
        )
        self.assertEqual(invalid_license.returncode, 2)
        binary = self.root / "fixture.pdf"
        binary.write_bytes(b"%PDF fixture")
        invalid_type = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(binary),
            "--title", "PDF 资料", "--origin", "本地 PDF", "--license", "CC0-1.0",
        )
        self.assertEqual(invalid_type.returncode, 2)

        review_path = self.root / "reference-review.json"
        exported_template = self.root / "reference-review-template.json"
        template_export = invoke(
            "reference", "review-template", "--out", str(output), "--reference", reference_id,
            "--write", str(exported_template),
        )
        self.assertEqual(template_export.returncode, 0, template_export.stderr)
        template = json.loads(exported_template.read_text(encoding="utf-8"))
        template.update(
            {
                "status": "agent-reviewed",
                "summary_zh": "这份资料说明星河压缩协议如何通过稳定词典执行有界替换，并要求解码端保持版本一致。",
                "claims": [
                    {
                        "claim_zh": "协议先建立稳定词典，再对重复片段执行有界替换，并要求解码端使用同一词典版本。",
                        "start_line": 4,
                        "end_line": 5,
                        "source_text": "错误的原文文本",
                        "evidence_note": "已重新打开归档原文第 4 至 5 行并核对压缩和解码约束。",
                    }
                ],
            }
        )
        review_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        invalid_review = invoke("reference", "review", "--out", str(output), "--review", str(review_path))
        self.assertEqual(invalid_review.returncode, 2)
        template["claims"][0]["source_text"] = (
            "星河压缩协议先建立稳定词典，再对重复片段执行有界替换。\n"
            "该方法要求解码端保留同一词典版本。"
        )
        review_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        reviewed = invoke("reference", "review", "--out", str(output), "--review", str(review_path))
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        reviewed_record = json.loads(reviewed.stdout)
        self.assertEqual(reviewed_record["audit"]["status"], "passed")
        page = output / "human/references/星河压缩协议.md"
        mirror = output / "markdown/references/星河压缩协议.md"
        self.assertEqual(Path(reviewed_record["human_file"]), page.resolve())
        self.assertEqual(Path(reviewed_record["compatibility_file"]), mirror.resolve())
        self.assertTrue(page.is_file())
        self.assertEqual(page.read_bytes(), mirror.read_bytes())
        page_text = page.read_text(encoding="utf-8")
        self.assertIn("标签：#类型/资料", page_text)
        self.assertIn("原文第 4–5 行", page_text)
        self.assertIn("CC0-1.0", page_text)
        self.assertNotIn(reference_id, page_text)
        self.assertTrue((output / "human/REFERENCES.md").is_file())
        self.assertIn("参考资料导览", (output / "human/INDEX.md").read_text(encoding="utf-8"))
        self.assertEqual(len(list((output / "human/references").glob("*.md"))), 1)
        self.assertEqual(len(list((output / "markdown/references").glob("*.md"))), 1)

        connection = sqlite3.connect(output / "machine/knowledge.sqlite")
        try:
            self.assertEqual(connection.execute("SELECT count(*) FROM reference_sources").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM documents WHERE kind='reference'").fetchone()[0], 1)
            self.assertGreater(connection.execute("SELECT count(*) FROM section_fts WHERE section_fts MATCH '星河压缩协议'").fetchone()[0], 0)
        finally:
            connection.close()
        retrieved = invoke("retrieve", "--out", str(output), "星河压缩协议稳定词典", "--budget", "1200", "--profile", "fast")
        self.assertEqual(retrieved.returncode, 0, retrieved.stderr)
        retrieval = json.loads(retrieved.stdout)
        self.assertTrue(any(item["kind"] == "reference" for item in retrieval["related_documents"]))
        self.assertIn("已审阅参考资料", Path(retrieval["pack"]).read_text(encoding="utf-8"))
        brief = invoke("brief", "--out", str(output), "星河压缩协议稳定词典", "--budget", "1200", "--profile", "fast")
        self.assertEqual(brief.returncode, 0, brief.stderr)
        self.assertIn("星河压缩协议", Path(json.loads(brief.stdout)["pack"]).read_text(encoding="utf-8"))
        maintained = invoke("maintain", "--out", str(output))
        self.assertEqual(maintained.returncode, 0, maintained.stdout + maintained.stderr)

        source_v2 = self.root / "stellar-compression-v2.md"
        source_v2.write_text(
            "# 星河压缩协议\n\n## 核心方法\n"
            "第二版增加词典校验步骤，并在替换前验证版本。\n"
            "解码端仍需使用同一词典版本。\n",
            encoding="utf-8",
        )
        missing_revision = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(source_v2),
            "--title", "星河压缩协议", "--origin", "本地测试资料", "--license", "CC0-1.0",
        )
        self.assertEqual(missing_revision.returncode, 2)
        revision_ingest = invoke(
            "reference", "ingest", "--out", str(output), "--source", str(source_v2),
            "--title", "星河压缩协议", "--origin", "本地测试资料", "--license", "CC0-1.0",
            "--revision-of", reference_id,
        )
        self.assertEqual(revision_ingest.returncode, 4, revision_ingest.stderr)
        revision = json.loads(revision_ingest.stdout)
        revision_template = json.loads(Path(revision["review_template"]).read_text(encoding="utf-8"))
        revision_template.update(
            {
                "status": "agent-reviewed",
                "summary_zh": "第二版资料新增词典版本校验，并继续要求解码端保持相同版本。",
                "claims": [
                    {
                        "claim_zh": "第二版在替换前增加词典版本校验。",
                        "start_line": 4,
                        "end_line": 4,
                        "source_text": "第二版增加词典校验步骤，并在替换前验证版本。",
                        "evidence_note": "已重新打开第二版归档原文第 4 行并核对新增校验步骤。",
                    }
                ],
            }
        )
        revision_review = self.root / "reference-review-v2.json"
        revision_review.write_text(json.dumps(revision_template, ensure_ascii=False, indent=2), encoding="utf-8")
        reviewed_v2 = invoke("reference", "review", "--out", str(output), "--review", str(revision_review))
        self.assertEqual(reviewed_v2.returncode, 0, reviewed_v2.stderr)
        self.assertIn("第二版资料新增词典版本校验", page.read_text(encoding="utf-8"))
        listed = json.loads(invoke("reference", "list", "--out", str(output), "--status", "all").stdout)
        self.assertEqual({item["status"] for item in listed["records"]}, {"agent-reviewed", "superseded"})
        rolled_revision = invoke("reference", "rollback", "--out", str(output), "--reference", revision["reference_id"])
        self.assertEqual(rolled_revision.returncode, 0, rolled_revision.stderr)
        self.assertIn("这份资料说明星河压缩协议", page.read_text(encoding="utf-8"))
        rolled_initial = invoke("reference", "rollback", "--out", str(output), "--reference", reference_id)
        self.assertEqual(rolled_initial.returncode, 0, rolled_initial.stderr)
        self.assertFalse(page.exists())
        self.assertFalse((output / "human/REFERENCES.md").exists())
        self.assertNotIn("参考资料导览", (output / "human/INDEX.md").read_text(encoding="utf-8"))
        final_audit = json.loads(invoke("reference", "audit", "--out", str(output)).stdout)
        self.assertEqual(final_audit["status"], "passed")
        self.assertEqual(final_audit["counts"]["total"], 0)

    def test_empty_document_symbols_are_not_a_provider_failure(self) -> None:
        # A module such as ``__main__.py`` may contain imports and a call but no
        # named declaration.  A successful ``documentSymbol`` response is then
        # an empty list; semantic key-page coverage remains a separate gate.
        self.assertEqual(_provider_status([], []), "passed")
        self.assertEqual(
            _provider_status([{"message": "invalid AST"}], []), "failed"
        )

    def test_python_attribute_accessors_stay_in_the_file_appendix(self) -> None:
        write(
            self.repo / "py" / "module_access.py",
            """
def __getattr__(name):
    if name == "version":
        return "1.0"
    raise AttributeError(name)
""",
        )
        git(self.repo, "add", "py/module_access.py")
        git(self.repo, "commit", "-m", "add module accessor")
        output = self.root / "python-accessor"
        initialized = invoke(
            "init",
            "--repo",
            str(self.repo),
            "--out",
            str(output),
            "--format",
            "markdown",
            "--scope-path",
            "py/module_access.py",
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
        accessor = next(
            entity for entity in catalog["entities"] if entity["name"] == "__getattr__"
        )
        self.assertEqual(accessor["hard_exclusion"], "python-attribute-accessor")
        plan = json.loads((output / "navigation-plan.json").read_text(encoding="utf-8"))
        decision = next(
            item for item in plan["decisions"] if item["entity_id"] == accessor["id"]
        )
        self.assertEqual(decision["classification"], "appendix")

    def test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server(self) -> None:
        output = self.root / "stdio-output"
        (output / "machine").mkdir(parents=True)
        (output / "machine" / "knowledge.sqlite").write_bytes(b"fixture")
        calls = []
        record_calls = []

        def fake_retrieve(path, question, budget, max_pages, profile):
            calls.append((path, question, budget, max_pages, profile))
            return {
                "status": "passed",
                "question": question,
                "estimated_tokens": 120,
                "selected_entities": [],
                "retrieval_stats": {"static_cache_hit": bool(len(calls) > 1)},
                "pack": str(output / "machine" / "agent-packs" / f"pack-{len(calls)}.json"),
                "record": str(output / "machine" / "agent-packs" / f"pack-{len(calls)}.record.json"),
            }

        def fake_record(path, request, retrieval):
            record_calls.append((path, request, retrieval))
            return {"status": "passed", "record": "human/analysis/test.md"}

        requests = "\n".join(
            [
                json.dumps({"id": "ping-1", "method": "ping"}),
                "{not-json",
                json.dumps({"id": "bad-1", "method": "unknown"}),
                json.dumps(
                    {
                        "id": "retrieve-1",
                        "method": "retrieve",
                        "question": "定位订单写入流程",
                        "budget": 1800,
                        "max_pages": 6,
                        "profile": "fast",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "id": "retrieve-surrogate",
                        "method": "retrieve",
                        "question": "异常\udca6文本",
                    }
                ),
                json.dumps(
                    {
                        "id": "record-1",
                        "method": "record-explanation",
                        "retrieval_request_id": "retrieve-1",
                    }
                ),
                json.dumps({"id": "stop-1", "method": "shutdown"}),
                json.dumps({"id": "ignored", "method": "ping"}),
            ]
        ) + "\n"
        destination = io.StringIO()
        summary = serve_stdio(
            output,
            input_stream=io.StringIO(requests),
            output_stream=destination,
            retrieve=fake_retrieve,
            record_explanation=fake_record,
        )
        responses = [json.loads(line) for line in destination.getvalue().splitlines()]
        self.assertIn("\\ufffd", destination.getvalue())
        self.assertEqual(
            [item["id"] for item in responses],
            ["ping-1", None, "bad-1", "retrieve-1", "retrieve-surrogate", "record-1", "stop-1"],
        )
        self.assertEqual([item["ok"] for item in responses], [True, False, False, True, True, True, True])
        self.assertEqual(responses[0]["result"]["protocol"], "ckb-stdio-retrieval")
        self.assertIn("record-explanation", responses[0]["result"]["methods"])
        self.assertEqual(responses[3]["result"]["question"], "定位订单写入流程")
        self.assertEqual(responses[4]["result"]["question"], "异常�文本")
        self.assertEqual(
            calls,
            [
                (output.resolve(), "定位订单写入流程", 1800, 6, "fast"),
                (output.resolve(), "异常�文本", 1500, 8, "fast"),
            ],
        )
        self.assertEqual(record_calls[0][2]["request_id"], "retrieve-1")
        self.assertEqual(summary["requests"], 7)
        self.assertEqual(summary["succeeded"], 5)
        self.assertEqual(summary["failed"], 2)
        self.assertTrue(summary["shutdown_requested"])

    def test_record_explanation_writes_utf8_machine_evidence_not_analysis_page(self) -> None:
        output = self.root / "explanation-evidence-output"
        pack_root = output / "machine" / "agent-packs"
        pack_root.mkdir(parents=True)
        pack = pack_root / "pack.md"
        pack.write_text("# Agent pack\n", encoding="utf-8")
        query_record = pack_root / "pack.json"
        query_record.write_text(
            json.dumps({"status": "passed", "source_grounded": True}, ensure_ascii=False),
            encoding="utf-8",
        )
        retrieval = {
            "request_id": "retrieve-utf8-1",
            "pack": str(pack),
            "record": str(query_record),
        }
        request = {
            "retrieval_request_id": "retrieve-utf8-1",
            "pack": str(pack),
            "question": "当前检索词项由脚本还是模型构造？",
            "selected_text": "学习解释必须保持简体中文。",
            "source_path": "学习笔记/来源.md",
            "source_title": "来源页面",
            "explanation": "词项由确定性脚本构造，模型只负责解释。",
            "idempotency_key": "utf8-evidence-1",
            "title": "GUI 瀛︿範瑙ｉ噴 2026-08-30",
        }
        with (
            patch("ckb_core.stdio_server.audit_feedback", return_value={"status": "passed"}),
            patch("ckb_core.stdio_server.audit_agent_protocol", return_value={"status": "passed"}),
        ):
            result = _record_explanation(output, request, retrieval)
        evidence = Path(result["evidence"])
        value = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(value["status"], "passed")
        self.assertEqual(value["question"], request["question"])
        self.assertEqual(value["selected_text"], request["selected_text"])
        self.assertEqual(value["explanation"], request["explanation"])
        self.assertEqual(result["record"], result["evidence"])
        self.assertFalse((output / "human/analysis").exists())
        self.assertFalse((output / "markdown/analysis").exists())

    def test_obsidian_plugin_package_can_be_registered_deployed_and_removed(self) -> None:
        package = self.root / "obsidian-package"
        package.mkdir()
        write(
            package / "manifest.json",
            json.dumps(
                {
                    "id": "code-knowledge-builder-companion",
                    "name": "Code Knowledge Builder Companion",
                    "version": "9.9.9",
                }
            ),
        )
        for name in ("main.js", "styles.css", "LICENSE", "NOTICE.md"):
            write(package / name, f"fixture {name}")
        output = self.root / "plugin-output"
        (output / "human").mkdir(parents=True)
        write(output / "state.json", json.dumps({"status": "complete"}))
        registry = self.root / "plugin-registry.json"
        registered = register_obsidian_plugin(package, registry)
        self.assertEqual(registered["status"], "registered")
        deployed = deploy_obsidian_plugin(output, registry)
        self.assertEqual(deployed["status"], "deployed")
        target = output / "human/.obsidian/plugins/code-knowledge-builder-companion"
        contract_path = output / "human/.ckb/output-contract.json"
        self.assertEqual(json.loads((target / "manifest.json").read_text(encoding="utf-8"))["version"], "9.9.9")
        self.assertEqual(
            json.loads((output / "human/.obsidian/community-plugins.json").read_text(encoding="utf-8")),
            ["code-knowledge-builder-companion"],
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["contract"], "code-knowledge-builder-output")
        self.assertEqual(Path(contract["output"]), output.resolve())
        self.assertEqual(Path(contract["vault"]), (output / "human").resolve())
        self.assertEqual(contract["stdio"]["minimum_version"], 2)
        self.assertIn("record-explanation", contract["stdio"]["methods"])
        status = obsidian_plugin_status(output, registry)
        self.assertEqual(status["deployed"]["status"], "deployed")
        self.assertEqual(status["output_contract"]["status"], "passed")
        removed = remove_obsidian_plugin(output)
        self.assertEqual(removed["status"], "removed")
        self.assertFalse(target.exists())
        self.assertFalse(contract_path.exists())

    def test_obsidian_plugin_deploy_falls_back_when_vault_directory_is_locked(self) -> None:
        package = self.root / "locked-obsidian-package"
        package.mkdir()
        write(
            package / "manifest.json",
            json.dumps(
                {
                    "id": "code-knowledge-builder-companion",
                    "name": "Code Knowledge Builder Companion",
                    "version": "9.9.8",
                }
            ),
        )
        for name in ("main.js", "styles.css", "LICENSE", "NOTICE.md"):
            write(package / name, f"locked fixture {name}")
        vault = self.root / "locked-vault"
        vault.mkdir()
        registry = self.root / "locked-plugin-registry.json"
        register_obsidian_plugin(package, registry)

        with patch.object(Path, "replace", side_effect=PermissionError("vault directory is open")):
            deployed = deploy_obsidian_plugin_to_vault(vault, registry)

        target = vault / ".obsidian/plugins/code-knowledge-builder-companion"
        self.assertEqual(deployed["status"], "deployed")
        self.assertEqual(deployed["install_mode"], "in-place-copy")
        self.assertEqual(json.loads((target / "manifest.json").read_text(encoding="utf-8"))["version"], "9.9.8")
        self.assertEqual((target / "main.js").read_text(encoding="utf-8"), "locked fixture main.js\n")

    def test_obsidian_output_contract_is_not_required_without_installed_plugin(self) -> None:
        output = self.root / "plugin-free-output"
        vault = output / "human"
        vault.mkdir(parents=True)
        write(output / "state.json", json.dumps({"status": "complete"}))
        projected = project_output_contract(output, vault)
        self.assertEqual(projected["status"], "not-required")
        self.assertFalse(projected["required"])
        self.assertFalse((vault / ".ckb/output-contract.json").exists())
        audited = audit_output_contract(output, vault)
        self.assertEqual(audited["status"], "not-required")
        self.assertEqual(audited["errors"], [])

    def test_non_git_path_reminds_then_opt_in_creates_one_initial_commit(self) -> None:
        source = self.root / "plain-source"
        source.mkdir()
        write(source / "app.py", "def start(value):\n    return value + 1")
        output = self.root / "plain-output"
        isolated_git_env = {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(self.root / "missing-global-gitconfig"),
        }

        reminder = invoke(
            "init",
            "--repo",
            str(source),
            "--out",
            str(output),
            "--format",
            "markdown",
            env=isolated_git_env,
        )
        self.assertEqual(reminder.returncode, 2)
        self.assertIn("not a Git repository", reminder.stderr)
        self.assertIn("--init-git", reminder.stderr)
        self.assertFalse((source / ".git").exists())
        self.assertFalse(output.exists())

        initialized = invoke(
            "init",
            "--repo",
            str(source),
            "--out",
            str(output),
            "--format",
            "markdown",
            "--init-git",
            "--initial-commit-message",
            "initial source snapshot",
            env=isolated_git_env,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        self.assertTrue((source / ".git").is_dir())
        count = subprocess.run(
            ["git", "-C", str(source), "rev-list", "--count", "HEAD"],
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            check=True,
            env={**os.environ, **isolated_git_env},
        ).stdout.strip()
        self.assertEqual(count, "1")
        log = subprocess.run(
            ["git", "-C", str(source), "log", "-1", "--format=%an%x00%ae%x00%s"],
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            check=True,
            env={**os.environ, **isolated_git_env},
        ).stdout.strip().split("\0")
        self.assertEqual(log, ["Code Knowledge Builder", "code-knowledge-builder@local.invalid", "initial source snapshot"])
        self.assertEqual(
            subprocess.run(
                ["git", "-C", str(source), "status", "--porcelain=v1", "--untracked-files=all"],
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                check=True,
                env={**os.environ, **isolated_git_env},
            ).stdout,
            "",
        )
        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        bootstrap = state["repository"]["git_bootstrap"]
        self.assertTrue(bootstrap["repository_created"])
        self.assertTrue(bootstrap["initial_commit_created"])
        self.assertEqual(bootstrap["commit_count"], 1)
        self.assertEqual(bootstrap["author"]["name_source"], "local-fallback")

        second_output = self.root / "plain-output-second"
        second = invoke(
            "init",
            "--repo",
            str(source),
            "--out",
            str(second_output),
            "--format",
            "markdown",
            "--init-git",
            env=isolated_git_env,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        second_state = json.loads((second_output / "state.json").read_text(encoding="utf-8"))
        self.assertFalse(second_state["repository"]["git_bootstrap"]["performed"])
        second_count = subprocess.run(
            ["git", "-C", str(source), "rev-list", "--count", "HEAD"],
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            check=True,
            env={**os.environ, **isolated_git_env},
        ).stdout.strip()
        self.assertEqual(second_count, "1")

    def test_unborn_git_repo_requires_opt_in_and_existing_dirty_repo_is_not_committed(self) -> None:
        source = self.root / "unborn"
        source.mkdir()
        write(source / "main.js", "export function main(value) { return value; }")
        git(source, "init")
        reminder = invoke("init", "--repo", str(source), "--out", str(self.root / "unborn-reminder"), "--format", "markdown")
        self.assertEqual(reminder.returncode, 2)
        self.assertIn("has no commit", reminder.stderr)
        created = invoke(
            "init",
            "--repo",
            str(source),
            "--out",
            str(self.root / "unborn-created"),
            "--format",
            "markdown",
            "--init-git",
            "--git-author-name",
            "Fixture Author",
            "--git-author-email",
            "fixture-author@example.invalid",
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        write(source / "dirty.py", "def dirty():\n    return True")
        commit_before = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        dirty = invoke(
            "init",
            "--repo",
            str(source),
            "--out",
            str(self.root / "dirty-output"),
            "--format",
            "markdown",
            "--init-git",
        )
        self.assertEqual(dirty.returncode, 6)
        self.assertIn("worktree is not clean", dirty.stderr)
        commit_after = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.assertEqual(commit_after, commit_before)
        self.assertFalse((self.root / "dirty-output").exists())

    def test_fast_run_can_bootstrap_non_git_source_and_stops_for_review(self) -> None:
        source = self.root / "plain-fast-source"
        source.mkdir()
        write(source / "main.py", "def main(value):\n    return value")
        output = self.root / "plain-fast-output"
        result = invoke(
            "run",
            "--repo",
            str(source),
            "--out",
            str(output),
            "--format",
            "markdown",
            "--init-git",
            "--git-author-name",
            "Fast Fixture",
            "--git-author-email",
            "fast-fixture@example.invalid",
        )
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertIn("review-template.json", result.stderr)
        self.assertTrue((output / ".pending-agent-review").is_file())
        count = subprocess.run(
            ["git", "-C", str(source), "rev-list", "--count", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.assertEqual(count, "1")
        rejected_resume = invoke("run", "--out", str(output), "--resume", "--init-git")
        self.assertEqual(rejected_resume.returncode, 2)
        self.assertIn("only to the initial run", rejected_resume.stderr)

    def test_feedback_anchor_mirroring_audit_and_archive_are_deterministic(self) -> None:
        output = self.root / "feedback-output"
        for root_name in ("human", "markdown"):
            target = output / root_name / "pages" / "订单服务.md"
            write(
                target,
                """
# 订单服务

标签：#类型/代码

订单服务负责保存订单并调用辅助判断。
""",
            )
        comment = self.root / "feedback-comment.md"
        comment.write_text("这段说明应补充失败路径以及对应测试入口。\n", encoding="utf-8")
        created = create_feedback(
            output,
            Path("pages/订单服务.md"),
            5,
            5,
            comment,
            "warn",
            "测试用户",
            "obsidian-plugin",
        )
        feedback_id = created["id"]
        self.assertEqual(created["anchor"]["status"], "line-range")
        self.assertEqual(list_feedback(output, "open")["count"], 1)
        self.assertEqual(audit_feedback(output)["status"], "passed")
        visible = Path(created["visible_files"][0])
        self.assertFalse(visible.read_text(encoding="utf-8").startswith("---\n"))
        self.assertEqual(visible.read_bytes(), Path(created["visible_files"][1]).read_bytes())

        for root_name in ("human", "markdown"):
            target = output / root_name / "pages" / "订单服务.md"
            target.write_text("前置说明。\n" + target.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        relocated = locate_feedback(output, feedback_id)
        self.assertEqual(relocated["status"], "passed")
        self.assertEqual(relocated["anchor"]["status"], "unique-text")

        resolution = self.root / "feedback-resolution.md"
        resolution.write_text("当前建议与固定页面职责不一致，因此保留原有说明并归档理由。\n", encoding="utf-8")
        resolved = resolve_feedback(output, feedback_id, "rejected", resolution)
        self.assertEqual(resolved["status"], "resolved")
        self.assertFalse((output / "workspace-meta/feedback/open" / f"{feedback_id}.json").exists())
        self.assertTrue((output / "workspace-meta/feedback/resolved" / f"{feedback_id}.json").is_file())
        self.assertEqual(audit_feedback(output)["status"], "passed")

        second = create_feedback(
            output,
            Path("pages/订单服务.md"),
            6,
            6,
            comment,
            "suggest",
            "测试用户",
            "manual",
        )
        with self.assertRaises(CkbError):
            resolve_feedback(output, second["id"], "accepted", resolution)
        applied_title = "反馈落实记录"
        applied_relative = Path("analysis/反馈落实记录.md")
        for root_name in ("human", "markdown"):
            write(
                output / root_name / applied_relative,
                """
# 反馈落实记录

标签：#类型/分析

这条中文记录说明反馈已经依据目标页完成核验和落实。
""",
            )
        metadata = output / "workspace-meta/notes/反馈落实记录.json"
        metadata.parent.mkdir(parents=True, exist_ok=True)
        metadata.write_text(
            json.dumps({"status": "agent-reviewed", "title": applied_title, "kind": "analysis"}, ensure_ascii=False),
            encoding="utf-8",
        )
        accepted = resolve_feedback(output, second["id"], "accepted", resolution, output / "human" / applied_relative)
        self.assertEqual(accepted["decision"], "accepted")
        self.assertEqual(audit_feedback(output)["status"], "passed")
        third = create_feedback(
            output,
            Path("pages/订单服务.md"),
            6,
            6,
            comment,
            "suggest",
            "测试用户",
            "manual",
        )
        for root_name in ("human", "markdown"):
            target = output / root_name / "pages" / "订单服务.md"
            target.write_text(target.read_text(encoding="utf-8").replace("订单服务负责保存订单并调用辅助判断。", "这段目标文字已经发生变化。"), encoding="utf-8", newline="\n")
        failed = audit_feedback(output)
        self.assertEqual(failed["status"], "failed")
        self.assertIn("feedback-anchor-stale", {item["reason"] for item in failed["errors"]})

    def test_work_record_index_covers_every_note_with_one_chinese_summary(self) -> None:
        output = self.root / "record-index-output"
        for root_name in ("human", "markdown"):
            for directory in ("analysis", "changes", "pitfalls", "experiments", "sessions"):
                (output / root_name / directory).mkdir(parents=True, exist_ok=True)
            write(
                output / root_name / "analysis" / "方案判断.md",
                """
# 方案判断

标签：#类型/分析

## 结论

这份分析说明当前方案的适用边界和下一步判断入口。
""",
            )
            write(
                output / root_name / "experiments" / "性能复测.md",
                """
# 性能复测

标签：#类型/实验

本实验记录固定协议下的性能结果和仍需保留的限制。
""",
            )
        result = refresh_work_record_index(output)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["record_count"], 2)
        text = (output / "human/RECORDS.md").read_text(encoding="utf-8")
        self.assertIn("## 分析与决策", text)
        self.assertIn("## 实验与量化结果", text)
        self.assertEqual(text.count("[[方案判断]]"), 1)
        self.assertEqual(text.count("[[性能复测]]"), 1)
        self.assertIn("适用边界和下一步判断入口", text)
        self.assertEqual(audit_work_record_index(output)["status"], "passed")
        self.assertEqual(
            (output / "human/RECORDS.md").read_bytes(),
            (output / "markdown/RECORDS.md").read_bytes(),
        )

    def test_markdown_whole_repository_and_completion_gate(self) -> None:
        output = self.root / "whole"
        init = invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown")
        self.assertEqual(init.returncode, 0, init.stderr)
        scope = json.loads((output / "scope.json").read_text(encoding="utf-8"))
        self.assertNotIn("node_modules/ignored.js", scope["selected_file_paths"])
        self.assertTrue(any(item["path"] == "node_modules/ignored.js" for item in scope["excluded"]))
        self.assertNotIn("scripts/_vendor/ignored.py", scope["selected_file_paths"])
        self.assertTrue(any(item["path"] == "scripts/_vendor/ignored.py" for item in scope["excluded"]))
        pre_finalize = invoke("finalize", "--out", str(output))
        self.assertIn(pre_finalize.returncode, {4, 5})
        self.assertFalse((output / ".complete").exists())
        review_all(output)
        merged = invoke("merge", "--out", str(output))
        self.assertEqual(merged.returncode, 0, merged.stderr)
        final = invoke("finalize", "--out", str(output))
        self.assertEqual(final.returncode, 0, final.stderr)
        self.assertTrue((output / ".complete").is_file())
        self.assertTrue((output / ".machine.complete").is_file())
        self.assertTrue((output / ".human.complete").is_file())
        self.assertTrue((output / "markdown" / "INDEX.md").is_file())
        self.assertTrue((output / "markdown" / "RECORDS.md").is_file())
        self.assertTrue((output / "human" / "INDEX.md").is_file())
        self.assertEqual((output / "human/INDEX.md").read_bytes(), (output / "markdown/INDEX.md").read_bytes())
        self.assertTrue((output / "facts/graph.json").is_file())
        self.assertEqual((output / "facts/graph.json").read_bytes(), (output / "graph.json").read_bytes())
        self.assertTrue((output / "machine/knowledge.sqlite").is_file())
        normalized_edn = output / "markdown" / "normalized.edn"
        self.assertTrue(normalized_edn.is_file())
        self.assertIn(":pages-and-blocks", normalized_edn.read_text(encoding="utf-8"))
        logseq_config = output / "markdown" / "logseq" / "config.edn"
        import_root_config = output / "logseq" / "config.edn"
        self.assertTrue(logseq_config.is_file())
        self.assertTrue(import_root_config.is_file())
        self.assertTrue(logseq_config.read_text(encoding="utf-8").startswith("{:meta/version 1"))
        self.assertEqual(hashlib.sha256(logseq_config.read_bytes()).hexdigest(), LOGSEQ_FILE_GRAPH_CONFIG_SHA256)
        self.assertEqual(import_root_config.read_bytes(), logseq_config.read_bytes())
        audit = json.loads((output / "audit" / "global.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "passed")
        self.assertTrue(next(item for item in audit["checks"] if item["name"] == "simplified-chinese-description-contract")["passed"])
        self.assertTrue(next(item for item in audit["checks"] if item["name"] == "facts-layer-valid")["passed"])
        self.assertTrue(next(item for item in audit["checks"] if item["name"] == "human-layer-valid")["passed"])
        self.assertTrue(next(item for item in audit["checks"] if item["name"] == "machine-layer-valid")["passed"])
        self.assertTrue(next(item for item in audit["checks"] if item["name"] == "agent-protocol-valid")["passed"])
        for root in (output, output / "markdown", output / "human"):
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertTrue((root / "CLAUDE.md").is_file())
            self.assertTrue((root / "GEMINI.md").is_file())
            self.assertTrue((root / ".github/copilot-instructions.md").is_file())
            self.assertTrue((root / ".cursor/rules/code-knowledge-builder.mdc").is_file())
        protocol_text = (output / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("brief --out", protocol_text)
        self.assertIn("不把候选实体、词项和得分展开", protocol_text)
        self.assertIn("record --out", protocol_text)
        self.assertIn("feedback list --out", protocol_text)
        self.assertIn("maintain --out", protocol_text)
        initial_policy_check = invoke("agent-policy", "check", "--out", str(output))
        self.assertEqual(initial_policy_check.returncode, 0, initial_policy_check.stderr)
        self.assertEqual(json.loads(initial_policy_check.stdout)["status"], "passed")
        (self.root / "AGENTS.md").write_text("# 原有项目要求\n\n保留这段已有说明。\n", encoding="utf-8")
        policy_install = invoke(
            "agent-policy", "install", "--out", str(output), "--workspace-root", str(self.root)
        )
        self.assertEqual(policy_install.returncode, 0, policy_install.stderr)
        repeated_policy_install = invoke(
            "agent-policy", "install", "--out", str(output), "--workspace-root", str(self.root)
        )
        self.assertEqual(repeated_policy_install.returncode, 0, repeated_policy_install.stderr)
        workspace_agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("保留这段已有说明", workspace_agents)
        self.assertEqual(workspace_agents.count("<!-- CKB-AGENT-PROTOCOL:BEGIN -->"), 1)
        self.assertEqual(workspace_agents.count("<!-- CKB-AGENT-PROTOCOL:END -->"), 1)
        graph = json.loads((output / "graph.json").read_text(encoding="utf-8"))
        connection = sqlite3.connect(output / "machine/knowledge.sqlite")
        try:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertFalse(connection.execute("PRAGMA foreign_key_check").fetchall())
            self.assertEqual(connection.execute("SELECT count(*) FROM entities").fetchone()[0], len(graph["entities"]))
            self.assertEqual(connection.execute("SELECT count(*) FROM relations").fetchone()[0], len(graph["links"]))
            self.assertEqual(connection.execute("SELECT count(*) FROM human_projection").fetchone()[0], len(graph["entities"]))
            english_only = connection.execute(
                "SELECT count(*) FROM entities WHERE (classification='appendix' AND description_zh NOT GLOB '*[一-龥]*') OR (classification<>'appendix' AND (meaning_zh NOT GLOB '*[一-龥]*' OR role_zh NOT GLOB '*[一-龥]*' OR change_when_zh NOT GLOB '*[一-龥]*'))"
            ).fetchone()[0]
            self.assertEqual(english_only, 0)
        finally:
            connection.close()
        graphify_record = audit["projections"]["graphify"]
        graphify_graph_path = output / "graphify-out" / "graph.json"
        graphify_communities_path = output / "graphify-out" / "communities.json"
        graphify_report_path = output / "graphify-out" / "GRAPH_REPORT.md"
        self.assertTrue(graphify_graph_path.is_file())
        self.assertTrue(graphify_communities_path.is_file())
        self.assertTrue(graphify_report_path.is_file())
        graphify_graph = json.loads(graphify_graph_path.read_text(encoding="utf-8"))
        graphify_communities = json.loads(graphify_communities_path.read_text(encoding="utf-8"))
        self.assertEqual(graphify_graph["graph"]["graphify_commit"], GRAPHIFY_COMMIT)
        self.assertEqual(graphify_graph["built_at_commit"], graph["repository"]["commit"])
        self.assertEqual({item["id"] for item in graphify_graph["nodes"]}, {item["id"] for item in graph["entities"]})
        self.assertEqual({item["id"] for item in graphify_graph["links"]}, {item["id"] for item in graph["links"]})
        self.assertTrue(all(item["confidence"] in {"EXTRACTED", "INFERRED", "AMBIGUOUS"} for item in graphify_graph["links"]))
        community_members = [member for community in graphify_communities["communities"] for member in community["members"]]
        self.assertEqual(len(community_members), len(set(community_members)))
        self.assertEqual(set(community_members), {item["id"] for item in graph["entities"]})
        graphify_report = graphify_report_path.read_text(encoding="utf-8")
        self.assertNotIn(GRAPHIFY_COMMIT, graphify_report)
        self.assertNotIn(graph["repository"]["commit"], graphify_report)
        self.assertIn("# 项目关系导览", graphify_report)
        self.assertIn("## 按职责群浏览", graphify_report)
        self.assertFalse(audit_graphify(output, graph, graphify_record))
        graphify_hashes = (
            hashlib.sha256(graphify_graph_path.read_bytes()).hexdigest(),
            hashlib.sha256(graphify_communities_path.read_bytes()).hexdigest(),
            hashlib.sha256(graphify_report_path.read_bytes()).hexdigest(),
        )
        query = invoke("query", "--out", str(output), "run_order helper", "--budget", "1500")
        self.assertEqual(query.returncode, 0, query.stderr)
        query_doc = json.loads(query.stdout)
        self.assertEqual(query_doc["status"], "passed")
        self.assertLessEqual(query_doc["estimated_tokens"], 1500)
        self.assertTrue(query_doc["source_files"])
        self.assertTrue(query_doc["links"])
        explain = invoke("explain", "--out", str(output), graphify_graph["nodes"][0]["id"])
        self.assertEqual(explain.returncode, 0, explain.stderr)
        first_link = graphify_graph["links"][0]
        path_result = invoke("path", "--out", str(output), first_link["source"], first_link["target"])
        self.assertEqual(path_result.returncode, 0, path_result.stderr)
        self.assertGreaterEqual(json.loads(path_result.stdout)["hop_count"], 1)
        helper = next(item for item in graph["entities"] if item["name"] == "helper_value")
        self.assertEqual(helper["classification"], "appendix")
        projection = json.loads((output / "markdown" / "projection.json").read_text(encoding="utf-8"))
        self.assertTrue(any(page["page_type"] == "repository" for page in projection["pages"]))
        self.assertTrue(any(page["page_type"] == "module" for page in projection["pages"]))
        self.assertTrue(all(page["human_page_kind"] in {"code-unit", "code-unit-aggregate"} for page in projection["pages"]))
        self.assertTrue(all(not page["title"].startswith(("实体 ·", "文件 ·", "模块 ·", "仓库 ·", "边界 ·")) for page in projection["pages"]))
        self.assertEqual(len(projection["source_manifest"]), len(graph["entities"]))
        self.assertEqual(Path(projection["normalized_edn"]), normalized_edn.resolve())
        self.assertEqual(projection["normalized_edn_sha256"], hashlib.sha256(normalized_edn.read_bytes()).hexdigest())
        self.assertEqual(Path(projection["logseq_file_graph"]["graph_root"]), (output / "markdown").resolve())
        self.assertEqual(Path(projection["logseq_file_graph"]["config"]), logseq_config.resolve())
        self.assertEqual(projection["logseq_file_graph"]["config_relative_path"], "logseq/config.edn")
        self.assertEqual(projection["logseq_file_graph"]["config_sha256"], LOGSEQ_FILE_GRAPH_CONFIG_SHA256)
        self.assertEqual(projection["logseq_file_graph"]["source_commit"], LOGSEQ_FILE_GRAPH_CONFIG_COMMIT)
        self.assertEqual(Path(projection["logseq_import_root"]["graph_root"]), output.resolve())
        self.assertEqual(Path(projection["logseq_import_root"]["config"]), import_root_config.resolve())
        self.assertEqual(projection["logseq_import_root"]["config_relative_path"], "logseq/config.edn")
        self.assertEqual(projection["logseq_import_root"]["config_sha256"], LOGSEQ_FILE_GRAPH_CONFIG_SHA256)
        selected_relative_paths = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
        self.assertIn("logseq/config.edn", selected_relative_paths)
        index_text = (output / "markdown" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("## 按任务选择入口", index_text)
        self.assertIn("[工作记录导览](RECORDS.md)", index_text)
        self.assertIn("[logseq/config.edn](logseq/config.edn)", index_text)
        wiki_text = (output / "markdown" / "WIKI.md").read_text(encoding="utf-8")
        self.assertIn("## 页面只保留什么", wiki_text)
        self.assertIn("## 工作记录如何查找", wiki_text)
        self.assertIn("## Graphify 关系导览", wiki_text)
        readability = json.loads((output / "markdown" / "readability-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(readability["status"], "passed")
        self.assertFalse(readability["errors"])
        self.assertTrue(all(value == 0 for key, value in readability["metrics"].items() if key in {"frontmatter_pages", "prefixed_titles", "visible_commit_identifiers", "machine_markers", "raw_relation_labels", "page_property_lines", "invalid_page_tags", "missing_source_links", "visible_hash_identifiers", "non_chinese_narrative_fields"}))
        self.assertNotIn("CKB 页面 ID", normalized_edn.read_text(encoding="utf-8"))
        self.assertNotIn(graph["repository"]["commit"], normalized_edn.read_text(encoding="utf-8"))
        self.assertEqual(projection["expected_counts"]["pages"], len(projection["pages"]))
        owner_page = next(page for page in projection["pages"] if page["id"] == projection["entity_owner_pages"][helper["id"]])
        owner_text = (output / "markdown" / owner_page["file"]).read_text(encoding="utf-8")
        self.assertIn("<details><summary>", owner_text)
        self.assertIn("该附属实体在固定源码范围内完成一项明确的局部处理。", owner_text)
        self.assertNotIn(helper["id"], owner_text)
        self.assertFalse(owner_text.startswith("---\n"))
        self.assertNotIn("条机器关系", owner_text)
        self.assertRegex(owner_text, r"标签：#类型/(?:代码|职责|边界)")
        self.assertIn("vscode://file/", owner_text)
        self.assertTrue((output / "markdown/.obsidian/app.json").is_file())
        self.assertTrue((output / "markdown/.obsidian/core-plugins.json").is_file())
        self.assertIn(
            "body .inline-title { display: none; }",
            (output / "markdown/.obsidian/snippets/ckb.css").read_text(encoding="utf-8"),
        )
        self.assertTrue((output / "agent-index.sqlite").is_file())
        coverage = invoke("coverage", "--out", str(output))
        self.assertEqual(coverage.returncode, 0, coverage.stderr)
        coverage_record = json.loads(coverage.stdout)
        self.assertEqual(coverage_record["status"], "passed")
        self.assertEqual(coverage_record["coverage_ratio"], 1.0)
        retrieved = invoke("retrieve", "--out", str(output), "OrderService 服务修改", "--budget", "1200", "--profile", "fast")
        self.assertEqual(retrieved.returncode, 0, retrieved.stderr)
        retrieve_record = json.loads(retrieved.stdout)
        self.assertEqual(retrieve_record["status"], "passed")
        self.assertTrue(retrieve_record["deterministic"])
        self.assertTrue(retrieve_record["source_grounded"])
        self.assertTrue(retrieve_record["selected_entities"])
        self.assertLessEqual(retrieve_record["estimated_tokens"], 1200)
        self.assertTrue(Path(retrieve_record["pack"]).is_file())
        brief = invoke("brief", "--out", str(output), "OrderService 服务修改", "--budget", "1200", "--profile", "fast")
        self.assertEqual(brief.returncode, 0, brief.stderr)
        brief_record = json.loads(brief.stdout)
        self.assertEqual(brief_record["status"], "passed")
        self.assertTrue(Path(brief_record["pack"]).is_file())
        self.assertTrue(Path(brief_record["record"]).is_file())
        self.assertNotIn("terms", brief_record)
        self.assertNotIn("selected_entities", brief_record)
        self.assertNotIn("retrieval_stats", brief_record)
        self.assertLess(len(brief.stdout.encode("utf-8")), len(retrieved.stdout.encode("utf-8")))
        self.assertEqual(brief_record["reading_entries"]["index"], str((output / "human/INDEX.md").resolve()))
        capabilities = invoke("capabilities", "--format", "json")
        self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
        capability_record = json.loads(capabilities.stdout)
        self.assertEqual(capability_record["status_order"], list(CAPABILITY_STATUSES))
        self.assertIn("订单服", search_terms("订单服务修改"))
        retrieval_stats = retrieve_record["retrieval_stats"]
        self.assertEqual(retrieval_stats["overscan_limit"], FAST_RETRIEVAL_OVERSCAN)
        self.assertLessEqual(retrieval_stats["materialized_candidates"], FAST_RETRIEVAL_OVERSCAN)
        self.assertEqual(retrieval_stats["selected_entities"], len(retrieve_record["selected_entities"]))
        self.assertEqual(
            retrieval_stats["source_link_cache_entries"],
            len({item["source_path"] for item in retrieve_record["selected_entities"]}),
        )
        self.assertLessEqual(retrieval_stats["selected_entities"], retrieval_stats["budgeted_entity_limit"])
        repeated = invoke("retrieve", "--out", str(output), "OrderService 服务修改", "--budget", "1200", "--profile", "fast")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        repeated_record = json.loads(repeated.stdout)
        self.assertEqual(
            [(item["entity_id"], item["score"], item["score_breakdown"]) for item in retrieve_record["selected_entities"]],
            [(item["entity_id"], item["score"], item["score_breakdown"]) for item in repeated_record["selected_entities"]],
        )
        direct_first = retrieve_machine(output, "OrderService 服务修改", 1200, 8, "fast")
        direct_second = retrieve_machine(output, "OrderService 服务修改", 1200, 8, "fast")
        self.assertFalse(direct_first["retrieval_stats"]["static_cache_hit"])
        self.assertTrue(direct_second["retrieval_stats"]["static_cache_hit"])
        precise = invoke("retrieve", "--out", str(output), "OrderService 服务修改", "--budget", "1200", "--profile", "precise")
        self.assertEqual(precise.returncode, 0, precise.stderr)
        self.assertTrue(json.loads(precise.stdout)["deterministic"])
        entity_result = invoke("entity", "--out", str(output), "OrderService")
        self.assertEqual(entity_result.returncode, 0, entity_result.stderr)
        self.assertEqual(len(json.loads(entity_result.stdout)["candidates"]), 1)
        source_result = invoke("source", "--out", str(output), "OrderService")
        self.assertEqual(source_result.returncode, 0, source_result.stderr)
        self.assertIn("class OrderService", json.loads(source_result.stdout)["excerpt"])
        neighbor_result = invoke("neighbors", "--out", str(output), "OrderService", "--depth", "2")
        self.assertEqual(neighbor_result.returncode, 0, neighbor_result.stderr)
        self.assertEqual(json.loads(neighbor_result.stdout)["status"], "passed")
        body = self.root / "analysis-body.md"
        body.write_text("## 结论\n\n订单服务通过明确的调用关系连接保存逻辑和辅助判断。\n", encoding="utf-8")
        recorded = invoke(
            "record",
            "--out",
            str(output),
            "--kind",
            "analysis",
            "--title",
            "订单服务分析",
            "--body",
            str(body),
            "--from-pack",
            retrieve_record["record"],
        )
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        note_record = json.loads(recorded.stdout)
        note_path = Path(note_record["file"])
        self.assertIn("human", note_path.parts)
        self.assertTrue(Path(note_record["compatibility_file"]).is_file())
        note_text = note_path.read_text(encoding="utf-8")
        self.assertIn("标签：#类型/分析", note_text)
        self.assertIn("[[", note_text)
        self.assertIn("obsidian://open?path=", note_record["obsidian_uri"])
        records_text = (output / "human/RECORDS.md").read_text(encoding="utf-8")
        self.assertIn("[[订单服务分析]]", records_text)
        self.assertEqual(audit_work_record_index(output)["status"], "passed")
        preserved_before = {
            path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for root_name in ("human", "markdown")
            for directory in ("pages", "analysis", "changes", "pitfalls", "experiments", "sessions")
            for path in (output / root_name / directory).glob("*.md")
        }
        refreshed_human = invoke("human-refresh", "--out", str(output))
        self.assertEqual(refreshed_human.returncode, 0, refreshed_human.stderr)
        refresh_record = json.loads(refreshed_human.stdout)
        self.assertEqual(refresh_record["status"], "passed")
        self.assertEqual(refresh_record["work_record_index"]["record_count"], 1)
        preserved_after = {
            path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for root_name in ("human", "markdown")
            for directory in ("pages", "analysis", "changes", "pitfalls", "experiments", "sessions")
            for path in (output / root_name / directory).glob("*.md")
        }
        self.assertEqual(preserved_after, preserved_before)
        feedback_comment = self.root / "page-feedback.md"
        feedback_comment.write_text("这个页面应明确说明附属判断与主保存流程之间的关系。\n", encoding="utf-8")
        feedback_created = invoke(
            "feedback", "create", "--out", str(output), "--target", owner_page["file"],
            "--start-line", "1", "--end-line", "1", "--comment", str(feedback_comment),
            "--severity", "warn", "--author", "Fixture Reviewer", "--source", "manual",
        )
        self.assertEqual(feedback_created.returncode, 0, feedback_created.stderr)
        feedback_record = json.loads(feedback_created.stdout)
        self.assertEqual(feedback_record["status"], "open")
        self.assertEqual(json.loads(invoke("feedback", "list", "--out", str(output), "--status", "open").stdout)["count"], 1)
        feedback_retrieved = invoke("retrieve", "--out", str(output), "开放人工反馈", "--budget", "1200")
        self.assertEqual(feedback_retrieved.returncode, 0, feedback_retrieved.stderr)
        feedback_retrieval = json.loads(feedback_retrieved.stdout)
        self.assertEqual(feedback_retrieval["open_feedback"], 1)
        self.assertTrue(any(item["kind"] == "feedback" for item in feedback_retrieval["related_documents"]))
        rejected_accept = invoke(
            "feedback", "resolve", "--out", str(output), "--feedback", feedback_record["id"],
            "--decision", "accepted", "--resolution", str(feedback_comment),
        )
        self.assertEqual(rejected_accept.returncode, 2)
        feedback_resolution = self.root / "page-feedback-resolution.md"
        feedback_resolution.write_text("该建议已通过分析记录确认并落实，现将反馈归档。\n", encoding="utf-8")
        feedback_resolved = invoke(
            "feedback", "resolve", "--out", str(output), "--feedback", feedback_record["id"],
            "--decision", "accepted", "--resolution", str(feedback_resolution), "--applied-record", str(note_path),
        )
        self.assertEqual(feedback_resolved.returncode, 0, feedback_resolved.stderr)
        self.assertEqual(json.loads(feedback_resolved.stdout)["status"], "resolved")
        self.assertEqual(invoke("feedback", "audit", "--out", str(output)).returncode, 0)
        maintained = invoke("agent-policy", "check", "--out", str(output))
        self.assertEqual(maintained.returncode, 0, maintained.stderr)
        (output / "human/.obsidian/appearance.json").write_text(
            json.dumps({"theme": "obsidian", "user_owned": True}), encoding="utf-8"
        )
        page_hashes_before_maintenance = {
            path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for root_name in ("human", "markdown")
            for path in (output / root_name).rglob("*.md")
        }
        maintenance = invoke("maintain", "--out", str(output))
        self.assertEqual(maintenance.returncode, 0, maintenance.stderr)
        maintenance_record = json.loads(maintenance.stdout)
        self.assertEqual(maintenance_record["status"], "passed")
        self.assertEqual(maintenance_record["page_writes"], 0)
        self.assertTrue(Path(maintenance_record["report"]).is_file())
        self.assertEqual(maintenance_record["failed_checks"], [])
        self.assertIn(
            ".obsidian/appearance.json",
            maintenance_record["checks"]["human_layer"]["ignored_user_state_differences"],
        )
        page_hashes_after_maintenance = {
            path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for root_name in ("human", "markdown")
            for path in (output / root_name).rglob("*.md")
        }
        self.assertEqual(page_hashes_after_maintenance, page_hashes_before_maintenance)
        rogue = output / "human/analysis/绕过受控写入.md"
        rogue.write_text("# 绕过受控写入\n\n标签：#类型/分析\n\n这是一条没有镜像、元数据和索引记录的直接写入。\n", encoding="utf-8")
        rejected_rogue = invoke("agent-policy", "check", "--out", str(output))
        self.assertEqual(rejected_rogue.returncode, 5)
        rogue_errors = json.loads(rejected_rogue.stdout)["errors"]
        self.assertIn("agent-note-mirror-set-mismatch", {item["reason"] for item in rogue_errors})
        rogue.unlink()
        self.assertEqual(invoke("agent-policy", "check", "--out", str(output)).returncode, 0)
        (output / "AGENTS.md").write_text("# 漂移\n", encoding="utf-8")
        drifted = invoke("agent-policy", "check", "--out", str(output))
        self.assertEqual(drifted.returncode, 5)
        drift_errors = json.loads(drifted.stdout)["errors"]
        self.assertIn("agent-protocol-adapter-drift", {item["reason"] for item in drift_errors})
        repaired_policy = invoke("agent-policy", "install", "--out", str(output))
        self.assertEqual(repaired_policy.returncode, 0, repaired_policy.stderr)
        english_body = self.root / "english-only.md"
        english_body.write_text("Only an English explanation of OrderService behavior.\n", encoding="utf-8")
        english_note = invoke(
            "record", "--out", str(output), "--kind", "analysis", "--title", "English only",
            "--body", str(english_body), "--from-pack", retrieve_record["record"],
        )
        self.assertEqual(english_note.returncode, 2)
        self.assertIn("Simplified Chinese", english_note.stderr)
        session_start = invoke(
            "workspace", "session-start", "--out", str(output), "--repo", str(self.repo),
            "--question", "分析 OrderService 保存订单时的修改入口", "--budget", "1200", "--profile", "fast",
        )
        self.assertEqual(session_start.returncode, 0, session_start.stderr)
        session = json.loads(session_start.stdout)
        self.assertEqual(session["status"], "active")
        self.assertEqual(session["session_note"]["mode"], "materialized")
        with (self.repo / "py/service.py").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n# 会话测试修改\n")
        summary = self.root / "session-summary.md"
        summary.write_text(
            "## 修改内容\n\n为订单服务加入测试注释以验证工作树覆盖层。\n\n"
            "## 修改原因\n\n需要证明 Agent 会话可以在固定知识基线旁记录真实修改。\n\n"
            "## 验证结果\n\n工作树同步、中文记录和知识页回链均通过脚本检查。\n",
            encoding="utf-8",
        )
        session_finish = invoke(
            "workspace", "session-finish", "--out", str(output), "--repo", str(self.repo),
            "--session", session["session_id"], "--summary", str(summary), "--title", "订单服务会话修改",
        )
        self.assertEqual(session_finish.returncode, 0, session_finish.stderr)
        finished = json.loads(session_finish.stdout)
        self.assertEqual(finished["status"], "complete")
        self.assertIn("py/service.py", finished["changed_paths"])
        self.assertTrue(Path(finished["finish_note"]["file"]).is_file())
        sessions = invoke("workspace", "sessions", "--out", str(output))
        self.assertEqual(sessions.returncode, 0, sessions.stderr)
        self.assertEqual(json.loads(sessions.stdout)["complete"], 1)
        changes = invoke("changes", "--out", str(output), "--kind", "change")
        self.assertEqual(changes.returncode, 0, changes.stderr)
        self.assertTrue(any(item["title"] == "订单服务会话修改" for item in json.loads(changes.stdout)["documents"]))
        showcase = invoke("showcase", "--dist", str(self.root / "showcase-dist"), "--sample", f"fixture={output}")
        self.assertEqual(showcase.returncode, 0, showcase.stderr)
        showcase_record = json.loads(showcase.stdout)
        self.assertEqual(showcase_record["status"], "passed")
        with zipfile.ZipFile(showcase_record["archive"]) as archive:
            names = archive.namelist()
            self.assertTrue(any(name.endswith("/WIKI.md") for name in names))
            self.assertTrue(any(name.endswith("/readability-audit.json") for name in names))
        logseq_config.unlink()
        markdown_errors = _audit_markdown(output, graph, _logical_projection(graph))
        self.assertIn("logseq-markdown-root-config-missing", {item["reason"] for item in markdown_errors})
        logseq_config.write_text("{:meta/version 1}\n", encoding="utf-8", newline="\n")
        markdown_errors = _audit_markdown(output, graph, _logical_projection(graph))
        self.assertIn("logseq-markdown-root-config-content-mismatch", {item["reason"] for item in markdown_errors})
        self.assertIn("logseq-markdown-root-config-hash-mismatch", {item["reason"] for item in markdown_errors})
        import_root_config.unlink()
        markdown_errors = _audit_markdown(output, graph, _logical_projection(graph))
        self.assertIn("logseq-import-root-config-missing", {item["reason"] for item in markdown_errors})
        graphify_graph_path.unlink()
        graphify_errors = audit_graphify(output, graph, graphify_record)
        self.assertIn("graphify-graph-missing", {item["reason"] for item in graphify_errors})
        indexed_without_graph_json = invoke("retrieve", "--out", str(output), "OrderService", "--budget", "800")
        self.assertEqual(indexed_without_graph_json.returncode, 0, indexed_without_graph_json.stderr)
        re_audit = invoke("audit", "--out", str(output), "--global")
        self.assertEqual(re_audit.returncode, 0, re_audit.stderr)
        self.assertTrue(logseq_config.is_file())
        self.assertTrue(import_root_config.is_file())
        self.assertTrue(graphify_graph_path.is_file())
        self.assertTrue(note_path.is_file())
        self.assertEqual(
            graphify_hashes,
            (
                hashlib.sha256(graphify_graph_path.read_bytes()).hexdigest(),
                hashlib.sha256(graphify_communities_path.read_bytes()).hexdigest(),
                hashlib.sha256(graphify_report_path.read_bytes()).hexdigest(),
            ),
        )
        self.assertFalse((output / ".complete").exists())
        self.assertTrue((output / ".pending-agent-review").is_file())
        self.assertEqual(invoke("finalize", "--out", str(output)).returncode, 0)
        self.assertTrue(note_path.is_file())
        self.assertTrue((output / ".machine.complete").is_file())
        self.assertTrue((output / ".human.complete").is_file())

    def test_local_scope_has_one_hop_boundary(self) -> None:
        output = self.root / "local"
        init = invoke(
            "init",
            "--repo",
            str(self.repo),
            "--out",
            str(output),
            "--format",
            "markdown",
            "--scope-path",
            "py/service.py",
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        boundary = json.loads((output / "boundary.json").read_text(encoding="utf-8"))
        self.assertTrue(any(item["name"] == "helper_value" for item in boundary["entities"]))
        self.assertFalse(any(item["path"] == "py/helper.py" and item["kind"] == "file" for item in boundary["entities"]))

    def test_entry_scope_uses_fixed_snapshot_while_live_worktree_changes(self) -> None:
        output = self.root / "entry"
        init = invoke(
            "init",
            "--repo",
            str(self.repo),
            "--out",
            str(output),
            "--format",
            "markdown",
            "--entry",
            "python:py/service.py#run_order",
            "--expand-depth",
            "1",
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        snapshot_root = Path(state["source_snapshot"]["root"])
        snapshot_source = (snapshot_root / "py" / "service.py").read_text(encoding="utf-8")
        (self.repo / "py" / "service.py").write_text("# dirty\n", encoding="utf-8")
        current = invoke("status", "--out", str(output), "--json")
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertEqual((snapshot_root / "py" / "service.py").read_text(encoding="utf-8"), snapshot_source)
        synced = invoke("workspace", "sync", "--out", str(output), "--repo", str(self.repo))
        self.assertEqual(synced.returncode, 0, synced.stderr)
        overlay = json.loads(synced.stdout)
        self.assertEqual(overlay["status"], "dirty")
        self.assertIn("py/service.py", overlay["changed_paths"])
        early_session = invoke(
            "workspace", "session-start", "--out", str(output), "--repo", str(self.repo),
            "--question", "在分段构建期间分析 run_order 的修改边界",
        )
        self.assertEqual(early_session.returncode, 0, early_session.stderr)
        early_record = json.loads(early_session.stdout)
        self.assertEqual(early_record["session_note"]["mode"], "queued-until-human-projection")
        self.assertEqual(early_record["retrieval"]["status"], "waiting-for-machine-layer")
        self.assertTrue(Path(early_record["session_note"]["record"]).is_file())
        first_chunk = state["chunks"][0]["id"]
        built = invoke("build-chunk", "--out", str(output), "--chunk", first_chunk)
        self.assertEqual(built.returncode, 0, built.stderr)
        review_all(output)
        self.assertEqual(invoke("merge", "--out", str(output)).returncode, 0)
        self.assertEqual(invoke("finalize", "--out", str(output)).returncode, 0)
        pending = json.loads(Path(early_record["session_note"]["record"]).read_text(encoding="utf-8"))
        self.assertEqual(pending["status"], "materialized")
        early_summary = self.root / "early-session-summary.md"
        early_summary.write_text(
            "## 修改内容\n\n在活动工作树中修改服务入口，用于验证构建中会话的延迟落页。\n\n"
            "## 修改原因\n\n需要证明固定快照完成后，早期会话仍能按变化路径链接知识页。\n\n"
            "## 验证结果\n\n分段构建、待处理会话落页和修改记录均通过。\n",
            encoding="utf-8",
        )
        early_finish = invoke(
            "workspace", "session-finish", "--out", str(output), "--repo", str(self.repo),
            "--session", early_record["session_id"], "--summary", str(early_summary),
        )
        self.assertEqual(early_finish.returncode, 0, early_finish.stderr)
        early_finish_record = json.loads(early_finish.stdout)
        self.assertEqual(early_finish_record["finish_note"]["kind"], "change")
        self.assertTrue(early_finish_record["finish_note"]["linked_pages"])

    def test_review_set_mismatch_fails(self) -> None:
        output = self.root / "bad-review"
        self.assertEqual(invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown").returncode, 0)
        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        chunk = state["chunks"][0]["id"]
        self.assertEqual(invoke("build-chunk", "--out", str(output), "--chunk", chunk).returncode, 0)
        review = json.loads((output / "chunks" / chunk / "review-template.json").read_text(encoding="utf-8"))
        review["reviews"] = review["reviews"][:-1]
        bad = output / "bad.json"
        bad.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        submitted = invoke("review-chunk", "--out", str(output), "--chunk", chunk, "--review", str(bad))
        self.assertEqual(submitted.returncode, 5)
        self.assertTrue((output / ".failed").is_file())

    def test_runtime_plan_lite(self) -> None:
        result = invoke("runtime", "plan", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertIn(plan["status"], {"payload-missing", "permission-required", "ready"})
        doctor = invoke("doctor", "--json")
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        graphify_core = json.loads(doctor.stdout)["tools"]["graphify_core"]
        self.assertEqual(graphify_core["status"], "ready")
        self.assertEqual(graphify_core["version"], "0.9.48")
        self.assertEqual(graphify_core["networkx_version"], "3.5")

    def test_obsidian_companion_distribution_reuses_pinned_claudian(self) -> None:
        root = SKILL_ROOT / "plugins/obsidian-code-knowledge-builder"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        lock = json.loads((root / "upstream.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "code-knowledge-builder-companion")
        self.assertEqual(manifest["version"], "0.8.0")
        self.assertEqual(manifest["author"], "DDDeath")
        self.assertTrue(manifest["isDesktopOnly"])
        self.assertEqual(lock["claudian"]["commit"], "f4bbba7fd326cbc68a6c8f0edfea6d14ea9ba0ac")
        self.assertEqual(lock["claudian"]["license"], "MIT")
        self.assertIn("no source files redistributed", lock["llm_wiki_reference"]["reuse"])
        self.assertGreater((root / "patches/claudian-base.patch").stat().st_size, 1000)
        patch = (root / "patches/claudian-base.patch").read_text(encoding="utf-8")
        self.assertIn("recordExplanation", patch)
        self.assertIn("parseCkbOutputContract", patch)
        self.assertIn("output-contract.json", patch)
        self.assertIn("PYTHONIOENCODING: 'utf-8'", patch)
        self.assertIn("learning-explanation-evidence", patch)
        self.assertIn("不得创建 analysis 页面", patch)
        self.assertIn("buildSelectionFollowUpInstruction", patch)
        self.assertIn("service.continueConversation", patch)
        self.assertIn("追问并记录", patch)
        self.assertIn("toolPolicy: { kind: 'passive' }", patch)
        self.assertTrue((root / "deploy.py").is_file())
        dist = root / "dist"
        for name in ("main.js", "manifest.json", "styles.css", "LICENSE", "NOTICE.md", "build-record.json", "deploy.py"):
            self.assertTrue((dist / name).is_file(), name)
            self.assertGreater((dist / name).stat().st_size, 0, name)
        self.assertEqual((root / "manifest.json").read_bytes(), (dist / "manifest.json").read_bytes())
        main = (dist / "main.js").read_text(encoding="utf-8", errors="replace")
        self.assertIn("explain-selection-to-daily-note", main)
        self.assertIn("open-today-learning-note", main)
        self.assertIn("editor-menu", main)
        self.assertIn("markdown-preview-view", main)
        self.assertIn("promptReadingSelection", main)
        self.assertIn("使用知识库解释选中文本", main)
        self.assertIn("CKB_RETRIEVAL: passed", main)
        self.assertIn("CKB_GENERATION: passed", main)
        self.assertIn("CKB_STDIO_REQUEST:", main)
        self.assertIn("CKB_STDIO_PACK:", main)
        self.assertIn("record-explanation", main)
        self.assertIn("---CKB_AGENT_PACK---", main)
        self.assertIn("ckb-stdio-retrieval", main)
        self.assertIn("学习笔记", main)
        self.assertIn("profile: 'fast'", patch)
        self.assertIn("budget: 1800", patch)
        self.assertIn("max_pages: 8", patch)
        self.assertIn("parseAuditedExplanation", patch)
        self.assertIn("validateCkbEvidence", patch)
        self.assertIn("readPassedAudit", patch)
        self.assertIn("serve', '--out'", patch)
        self.assertIn("method: 'retrieve'", patch)
        self.assertIn("method: 'record-explanation'", patch)
        self.assertIn("method: 'shutdown'", patch)
        self.assertIn("utf8SafeText", patch)
        self.assertIn("0xD800", patch)
        styles = (dist / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".ckb-selection-learning-modal", styles)
        build_record = json.loads((dist / "build-record.json").read_text(encoding="utf-8"))
        self.assertEqual(build_record["status"], "passed")
        self.assertEqual(build_record["claudian_commit"], lock["claudian"]["commit"])

    def test_required_format_duplicate_entry_and_syntax_stage(self) -> None:
        missing_format = invoke("init", "--repo", str(self.repo), "--out", str(self.root / "missing-format"))
        self.assertEqual(missing_format.returncode, 2)
        write(self.repo / "duplicate.py", "def run_order(value):\n    return value")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "duplicate symbol")
        duplicate = invoke("init", "--repo", str(self.repo), "--out", str(self.root / "duplicate"), "--format", "markdown", "--entry", "run_order")
        self.assertEqual(duplicate.returncode, 2)
        self.assertIn("candidates=", duplicate.stderr)
        output = self.root / "syntax-stage"
        self.assertEqual(invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown").returncode, 0)
        chunk = json.loads((output / "state.json").read_text(encoding="utf-8"))["chunks"][0]["id"]
        syntax = invoke("build-chunk", "--out", str(output), "--chunk", chunk, "--stage", "syntax")
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertEqual(json.loads((output / "chunks" / chunk / "syntax.json").read_text(encoding="utf-8"))["status"], "passed")

    def test_oversized_file_splits_on_declarations_without_duplicate_ids(self) -> None:
        repo = self.root / "large-file"
        repo.mkdir()
        write(repo / "many.py", "\n".join(f"def function_{i}(value):\n    return value + {i}\n" for i in range(205)))
        git(repo, "init")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "oversized")
        output = self.root / "oversized"
        result = invoke("init", "--repo", str(repo), "--out", str(output), "--format", "markdown")
        self.assertEqual(result.returncode, 0, result.stderr)
        chunks = json.loads((output / "state.json").read_text(encoding="utf-8"))["chunks"]
        entity_ids = [entity_id for chunk in chunks for entity_id in chunk["entity_ids"]]
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(entity_ids), len(set(entity_ids)))
        self.assertTrue(all(chunk["entity_count"] <= 2000 for chunk in chunks))
        review_packs = json.loads((output / "state.json").read_text(encoding="utf-8"))["review_packs"]
        self.assertGreater(len(review_packs), 1)
        self.assertTrue(any(pack["kind"] == "appendix-review" for pack in review_packs))

    def test_both_projection_parity_with_cli_contract_double(self) -> None:
        output = self.root / "both"
        self.assertEqual(invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "both").returncode, 0)
        review_all(output)
        self.assertEqual(invoke("merge", "--out", str(output)).returncode, 0)
        fake_cmd = self.root / "fake-logseq.cmd"
        fake_cmd.write_text(f'@"{PYTHON}" "{SKILL_ROOT / "tests" / "fake_logseq.py"}" %*\n', encoding="utf-8")
        final = invoke("finalize", "--out", str(output), env={"CKB_LOGSEQ_COMMAND": str(fake_cmd)})
        self.assertEqual(final.returncode, 0, final.stderr)
        audit = json.loads((output / "audit" / "global.json").read_text(encoding="utf-8"))
        parity = next(item for item in audit["checks"] if item["name"] == "dual-projection-parity")
        self.assertTrue(parity["passed"])
        self.assertTrue(parity["detail"]["entity_ownership_equal"])
        self.assertTrue(parity["detail"]["source_manifest_equal"])
        self.assertTrue(parity["detail"]["normalized_edn_equal"])
        markdown_edn = Path(audit["projections"]["markdown"]["normalized_edn"])
        logseq_edn = Path(audit["projections"]["logseq-db"]["normalized_edn"])
        self.assertEqual(markdown_edn.read_bytes(), logseq_edn.read_bytes())
        db_path = Path(audit["projections"]["logseq-db"]["db_path"])
        self.assertEqual(db_path.read_bytes()[:16], b"SQLite format 3\x00")
        self.assertTrue((output / "agent-index.sqlite").is_file())
        self.assertEqual(audit["projections"]["agent-index"]["projection_format"], "markdown")

    def test_logseq_only_projection_has_format_neutral_agent_index(self) -> None:
        output = self.root / "logseq-only"
        self.assertEqual(invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "logseq-db").returncode, 0)
        review_all(output)
        self.assertEqual(invoke("merge", "--out", str(output)).returncode, 0)
        fake_cmd = self.root / "fake-logseq-only.cmd"
        fake_cmd.write_text(f'@"{PYTHON}" "{SKILL_ROOT / "tests" / "fake_logseq.py"}" %*\n', encoding="utf-8")
        final = invoke("finalize", "--out", str(output), env={"CKB_LOGSEQ_COMMAND": str(fake_cmd)})
        self.assertEqual(final.returncode, 0, final.stderr)
        self.assertTrue((output / "markdown/INDEX.md").is_file())
        self.assertTrue((output / "human/INDEX.md").is_file())
        self.assertTrue((output / "machine/knowledge.sqlite").is_file())
        self.assertTrue((output / "agent-index.sqlite").is_file())
        audit = json.loads((output / "audit" / "global.json").read_text(encoding="utf-8"))
        index_record = audit["projections"]["agent-index"]
        self.assertEqual(index_record["status"], "passed")
        self.assertEqual(index_record["projection_format"], "logseq-db")
        retrieved = invoke("retrieve", "--out", str(output), "OrderService save_order", "--budget", "1000")
        self.assertEqual(retrieved.returncode, 0, retrieved.stderr)
        record = json.loads(retrieved.stdout)
        self.assertEqual(record["status"], "passed")
        self.assertTrue(record["selected_entities"])
        self.assertTrue(all(entity["human_page_title"] for entity in record["selected_entities"]))
        self.assertIn("vscode://file/", Path(record["pack"]).read_text(encoding="utf-8"))

    def test_english_only_agent_review_is_rejected(self) -> None:
        output = self.root / "english-review"
        self.assertEqual(invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown").returncode, 0)
        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        first_batch = state["chunks"][0]["id"]
        self.assertEqual(invoke("build-chunk", "--out", str(output), "--chunk", first_batch).returncode, 0)
        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        page_pack = next(pack for pack in state["review_packs"] if pack["kind"] == "page-review" and first_batch in pack["parse_batch_ids"])
        review = json.loads(Path(page_pack["review_template_path"]).read_text(encoding="utf-8"))
        for item in review["reviews"]:
            item.update(
                {
                    "meaning_zh": "English-only meaning for the source entity.",
                    "role_zh": "English-only role for the source entity.",
                    "change_when_zh": "Change this entity when behavior changes.",
                    "evidence_note": "English-only source review note.",
                    "status": "agent-reviewed",
                }
            )
        review_path = output / "english-review.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        submitted = invoke("review-pack", "--out", str(output), "--pack", page_pack["id"], "--review", str(review_path))
        self.assertEqual(submitted.returncode, 5)
        audit = json.loads((output / "review-packs" / page_pack["id"] / "audit.json").read_text(encoding="utf-8"))
        self.assertTrue(any("not-substantive" in item["reason"] for item in audit["errors"]))

    def test_navigation_page_quota_relation_budget_and_context_bundle(self) -> None:
        output = self.root / "navigation"
        self.assertEqual(invoke("init", "--repo", str(self.repo), "--out", str(output), "--format", "markdown").returncode, 0)
        plan = json.loads((output / "navigation-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["status"], "passed")
        self.assertTrue(all(count <= 1 for count in plan["page_count_by_path"].values()))
        review_all(output)
        self.assertEqual(invoke("merge", "--out", str(output)).returncode, 0)
        self.assertEqual(invoke("finalize", "--out", str(output)).returncode, 0)
        context = invoke("context", "--out", str(output), "--module", "py")
        self.assertEqual(context.returncode, 0, context.stderr)
        context_record = json.loads(context.stdout)
        self.assertEqual(context_record["mode"], "full-module")
        self.assertLessEqual(context_record["budget"]["estimated_tokens"], 80_000)
        self.assertEqual(estimated_tokens(Path(context_record["path"]).read_text(encoding="utf-8")), context_record["budget"]["estimated_tokens"])

        entities = []
        for index in range(36):
            path = f"m/file_{index}.py"
            entities.append(
                {
                    "id": f"file-{index}", "kind": "file", "name": f"file_{index}.py", "qualified_name": path,
                    "language": "python", "path": path, "blob": f"blob-{index}", "commit": "c" * 40,
                    "range": {"start_byte": 0, "end_byte": 10, "start_line": 1, "end_line": 1},
                    "parent_id": None, "classification": "page", "owner_page_id": f"file-{index}",
                    "meaning_zh": "文件含义说明。", "role_zh": "文件作用说明。", "change_when_zh": "文件变化时修改。",
                }
            )
        links = [
            {"id": f"l-{index}", "type": "references", "source": "file-0", "target": f"file-{index}"}
            for index in range(1, 36)
        ]
        logical = _logical_projection({"repository": {"root": str(self.repo), "commit": "c" * 40}, "entities": entities, "links": links})
        source_page = next(page for page in logical["pages"] if page["id"] == "file-0")
        direct = [link for link in source_page["outgoing"] if link.get("category") == "direct"]
        self.assertEqual(len(direct), DIRECT_RELATION_LIMIT)
        self.assertEqual(source_page["relation_summary"]["direct"]["hidden_groups"], 15)

    def test_page_configuration_controls_quotas_content_and_is_pinned(self) -> None:
        repo = self.root / "configured-pages"
        repo.mkdir()
        write(
            repo / "service.py",
            """
def first_operation(value):
    next_value = value + 1
    return second_operation(next_value)

def second_operation(value):
    next_value = value * 2
    return third_operation(next_value)

def third_operation(value):
    result = value - 3
    return result
""",
        )
        git(repo, "init")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "configured pages")

        supplied = self.root / "page-config.partial.json"
        supplied.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "page_limits": {
                        "ordinary_file": 2,
                        "core_file": 3,
                        "adjacent_file": 2,
                        "core_per_entry": 3,
                        "adjacent_per_entry": 2,
                    },
                    "content": {
                        "code_page_sections": ["overview", "source_location", "appendix"],
                        "overview_fields": ["role"],
                        "appendix_mode": "expanded",
                        "headings": {"source_location": "源码落点", "appendix": "辅助代码"},
                    },
                    "relation_limits": {"direct": 2},
                    "context": {
                        "module_max_tokens": 60000,
                        "task_max_tokens": 10000,
                        "total_max_tokens": 80000,
                        "reserved_agent_tokens": 20000,
                    },
                    "review_packs": {"page": {"max_items": 1}},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        validated = invoke("page-config", "--validate", str(supplied))
        self.assertEqual(validated.returncode, 0, validated.stderr)
        normalized = json.loads(validated.stdout)["normalized"]
        self.assertEqual(normalized["page_limits"]["ordinary_file"], 2)
        self.assertEqual(normalized["relation_limits"]["aggregate"], DEFAULT_PAGE_CONFIG["relation_limits"]["aggregate"])

        output = self.root / "configured-output"
        initialized = invoke(
            "init",
            "--repo",
            str(repo),
            "--out",
            str(output),
            "--format",
            "markdown",
            "--page-config",
            str(supplied),
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        pinned = json.loads((output / "page-config.json").read_text(encoding="utf-8"))
        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["page_config"]["sha256"], page_config_sha256(pinned))
        plan = json.loads((output / "navigation-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["page_limits"], pinned["page_limits"])
        self.assertEqual(plan["page_count_by_path"]["service.py"], 2)
        self.assertGreaterEqual(len([pack for pack in state["review_packs"] if pack["kind"] == "page-review"]), 3)

        review_all(output)
        self.assertEqual(invoke("merge", "--out", str(output)).returncode, 0)
        final = invoke("finalize", "--out", str(output))
        self.assertEqual(final.returncode, 0, final.stderr)
        complete = json.loads((output / ".complete").read_text(encoding="utf-8"))
        self.assertEqual(complete["page_config"]["sha256"], state["page_config"]["sha256"])
        audit = json.loads((output / "audit" / "global.json").read_text(encoding="utf-8"))
        config_gate = next(check for check in audit["checks"] if check["name"] == "page-configuration-pinned")
        self.assertTrue(config_gate["passed"])
        page_text = "\n".join(path.read_text(encoding="utf-8") for path in (output / "markdown" / "pages").glob("*.md"))
        self.assertIn("## 源码落点", page_text)
        self.assertIn("## 辅助代码", page_text)
        self.assertNotIn("## 什么时候需要修改", page_text)
        self.assertNotIn("<details>", page_text)

        (output / "page-config.json").write_text("{}\n", encoding="utf-8")
        drifted = invoke("status", "--out", str(output), "--json")
        self.assertEqual(drifted.returncode, 6)
        self.assertIn("configuration drifted", drifted.stderr)

        invalid = self.root / "invalid-page-config.json"
        invalid.write_text(
            json.dumps({"schema_version": 1, "content": {"code_page_sections": ["overview", "appendix"]}}),
            encoding="utf-8",
        )
        rejected = invoke("page-config", "--validate", str(invalid))
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("required sections", rejected.stderr)

    def test_csharp_project_selection_partial_types_and_generated_exclusions(self) -> None:
        repo = self.root / "csharp"
        repo.mkdir()
        write(repo / "Demo.sln", "Microsoft Visual Studio Solution File, Format Version 12.00")
        write(repo / "src" / "Demo.csproj", '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        write(
            repo / "src" / "Core.cs",
            """
namespace Demo;
public partial class Core {
    public int Value => 1;
    public int Execute(int value) {
        var next = value + 1;
        return next;
    }
}
public enum Mode { Fast, Slow }
""",
        )
        write(
            repo / "src" / "More.cs",
            """
namespace Demo;
public partial class Core {
    public int ExecuteMore(int value) {
        var next = value + 2;
        return next;
    }
}
""",
        )
        write(repo / "src" / "Generated.g.cs", "namespace Demo; public class Generated { public void Run() {} }")
        write(repo / "bin" / "Ignored.cs", "namespace Demo; public class Ignored {}")
        git(repo, "init")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "csharp")
        output = self.root / "csharp-output"
        initialized = invoke(
            "init", "--repo", str(repo), "--out", str(output), "--format", "markdown",
            "--entry", "csharp:src/More.cs#Demo.Core.ExecuteMore",
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        scope = json.loads((output / "scope.json").read_text(encoding="utf-8"))
        self.assertNotIn("src/Generated.g.cs", scope["selected_file_paths"])
        self.assertNotIn("bin/Ignored.cs", scope["selected_file_paths"])
        self.assertEqual(scope["csharp_workspace"]["selection"], "unique-auto")
        self.assertEqual(scope["csharp_workspace"]["path"], "Demo.sln")
        catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
        partial = next(entity for entity in catalog["entities"] if entity.get("partial") and entity["qualified_name"] == "Demo.Core")
        self.assertEqual(len(partial["fragments"]), 2)
        plan = json.loads((output / "navigation-plan.json").read_text(encoding="utf-8"))
        self.assertLessEqual(plan["page_count_by_path"].get(partial["path"], 0), 4)
        self.assertTrue(all(count <= (4 if path in plan["core_paths"] else 1) for path, count in plan["page_count_by_path"].items()))

        ambiguous = self.root / "csharp-ambiguous"
        shutil.copytree(repo, ambiguous, ignore=shutil.ignore_patterns(".git"))
        write(ambiguous / "Other.sln", "Microsoft Visual Studio Solution File, Format Version 12.00")
        git(ambiguous, "init")
        git(ambiguous, "config", "user.email", "fixture@example.invalid")
        git(ambiguous, "config", "user.name", "Fixture")
        git(ambiguous, "add", ".")
        git(ambiguous, "commit", "-m", "ambiguous")
        rejected = invoke("init", "--repo", str(ambiguous), "--out", str(self.root / "ambiguous-output"), "--format", "markdown")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("multiple tracked C# solutions", rejected.stderr)

    def test_csharp_property_and_enum_land_in_class_or_file_aggregation(self) -> None:
        repo = self.root / "csharp-entry-kinds"
        repo.mkdir()
        write(repo / "Demo.csproj", '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        write(repo / "Core.cs", "namespace Demo; public class Core { public int Value => 1; } public enum Mode { Fast }")
        git(repo, "init")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "entries")
        property_out = self.root / "property-out"
        result = invoke("init", "--repo", str(repo), "--out", str(property_out), "--format", "markdown", "--entry", "csharp:Core.cs#Demo.Core.Value")
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads((property_out / "catalog.json").read_text(encoding="utf-8"))
        value = next(entity for entity in catalog["entities"] if entity["qualified_name"] == "Demo.Core.Value")
        decision = next(item for item in json.loads((property_out / "navigation-plan.json").read_text(encoding="utf-8"))["decisions"] if item["entity_id"] == value["id"])
        core = next(entity for entity in catalog["entities"] if entity["qualified_name"] == "Demo.Core")
        self.assertEqual(decision["classification"], "appendix")
        self.assertEqual(decision["owner_page_id"], core["id"])

        enum_out = self.root / "enum-out"
        result = invoke("init", "--repo", str(repo), "--out", str(enum_out), "--format", "markdown", "--entry", "csharp:Core.cs#Demo.Mode")
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads((enum_out / "catalog.json").read_text(encoding="utf-8"))
        enum = next(entity for entity in catalog["entities"] if entity["qualified_name"] == "Demo.Mode")
        file_entity = next(entity for entity in catalog["entities"] if entity["kind"] == "file" and entity["path"] == "Core.cs")
        decision = next(item for item in json.loads((enum_out / "navigation-plan.json").read_text(encoding="utf-8"))["decisions"] if item["entity_id"] == enum["id"])
        self.assertEqual(decision["classification"], "appendix")
        self.assertEqual(decision["owner_page_id"], file_entity["id"])

    def test_fallback_standard_derivation_and_stable_ids(self) -> None:
        build_repo = self.root / "build-flags"
        build_repo.mkdir()
        write(build_repo / "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 20)\nset(CMAKE_C_STANDARD 17)")
        cpp_flags, cpp_evidence = _fallback_flags(build_repo, "cpp")
        c_flags, c_evidence = _fallback_flags(build_repo, "c")
        self.assertIn("-std=c++20", cpp_flags)
        self.assertIn("-std=c17", c_flags)
        self.assertEqual(cpp_evidence["resolution"], "build-config-unique")
        self.assertEqual(c_evidence["resolution"], "build-config-unique")
        first = stable_id("entity", "commit", "path", 1, 2)
        second = stable_id("entity", "commit", "path", 1, 2)
        changed = stable_id("entity", "commit", "path", 1, 3)
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)


if __name__ == "__main__":
    unittest.main()
