from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


TESTS_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = TESTS_ROOT.parent
sys.path.insert(0, str(TESTS_ROOT))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from test_ckb import invoke, make_repo, review_all
from ckb_core import record_replace as record_replace_module
from ckb_core.common import CkbError
from ckb_core.record_replace import replace_note


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _owned_snapshot(output: Path, title: str) -> dict[str, object]:
    meta = json.loads((output / "workspace-meta/notes" / f"{title}.json").read_text(encoding="utf-8"))
    relative = Path("changes") / f"{title}.md"
    files = {
        name: _sha(output / path)
        for name, path in {
            "human": Path("human") / relative,
            "markdown": Path("markdown") / relative,
            "metadata": Path("workspace-meta/notes") / f"{title}.json",
            "human_records": Path("human/RECORDS.md"),
            "markdown_records": Path("markdown/RECORDS.md"),
            "record_audit": Path("workspace-meta/work-record-index-audit.json"),
        }.items()
    }
    agent = sqlite3.connect(output / "agent-index.sqlite")
    try:
        agent_rows = {
            "note": agent.execute("SELECT * FROM notes WHERE note_title=?", (title,)).fetchall(),
            "links": agent.execute("SELECT * FROM note_links WHERE note_title=? ORDER BY page_title", (title,)).fetchall(),
            "fts": agent.execute("SELECT note_title,title,content FROM note_fts WHERE note_title=?", (title,)).fetchall(),
        }
    finally:
        agent.close()
    machine = sqlite3.connect(output / "machine/knowledge.sqlite")
    try:
        document_id = machine.execute("SELECT document_id FROM documents WHERE title=? AND kind='change'", (title,)).fetchone()[0]
        machine_rows = {
            "document": machine.execute("SELECT * FROM documents WHERE document_id=?", (document_id,)).fetchall(),
            "sections": machine.execute("SELECT * FROM sections WHERE document_id=? ORDER BY ordinal", (document_id,)).fetchall(),
            "links": machine.execute("SELECT * FROM document_links WHERE source_document_id=? ORDER BY target_title", (document_id,)).fetchall(),
            "fts": machine.execute("SELECT section_id,document_id,heading,content,source_path FROM section_fts WHERE document_id=? ORDER BY rowid", (document_id,)).fetchall(),
        }
    finally:
        machine.close()
    return {"files": files, "metadata": meta, "agent": agent_rows, "machine": machine_rows}


class RecordReplaceTests(unittest.TestCase):
    title = "旧变更记录"

    @classmethod
    def setUpClass(cls) -> None:
        cls.class_temp = tempfile.TemporaryDirectory(prefix="ckb-record-replace-class-")
        cls.class_root = Path(cls.class_temp.name)
        cls.repo = make_repo(cls.class_root)
        cls.completed = cls.class_root / "completed"
        initialized = invoke("init", "--repo", str(cls.repo), "--out", str(cls.completed), "--format", "markdown")
        if initialized.returncode:
            raise AssertionError(initialized.stderr)
        review_all(cls.completed)
        merged = invoke("merge", "--out", str(cls.completed))
        if merged.returncode:
            raise AssertionError(merged.stderr)
        finalized = invoke("finalize", "--out", str(cls.completed))
        if finalized.returncode:
            raise AssertionError(finalized.stderr)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.class_temp.cleanup()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-record-replace-")
        self.root = Path(self.temp.name)
        self.output = self.root / "output"
        shutil.copytree(self.completed, self.output)
        self.old_body = self.root / "old.md"
        self.old_body.write_text(
            "## 原始结论\n\n旧正文只说明原始变更行为，并保留既有审阅证据。\n",
            encoding="utf-8",
            newline="\n",
        )
        retrieval = invoke("retrieve", "--out", str(self.output), "OrderService 服务修改", "--budget", "1200", "--profile", "fast")
        self.assertEqual(retrieval.returncode, 0, retrieval.stderr)
        self.pack = Path(json.loads(retrieval.stdout)["record"])
        created = invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "change",
            "--title",
            self.title,
            "--body",
            str(self.old_body),
            "--from-pack",
            str(self.pack),
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        self.created = json.loads(created.stdout)
        self.baseline = _owned_snapshot(self.output, self.title)
        self.new_body = self.root / "new.md"
        self.new_body.write_text(
            "## 当前结论\n\n新正文明确替换旧结论，并验证所有受管角色同步更新。\n",
            encoding="utf-8",
            newline="\n",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _replace(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "change",
            "--title",
            self.title,
            "--body",
            str(self.new_body),
            "--replace",
            *extra,
        )

    def test_replace_updates_every_role_and_rollback_is_exact_and_idempotent(self) -> None:
        replaced = self._replace()
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        result = json.loads(replaced.stdout)
        self.assertEqual(result["status"], "replaced")
        self.assertEqual(
            set(result["changed_roles"]),
            {
                "human-note",
                "markdown-note",
                "note-metadata",
                "human-records",
                "markdown-records",
                "work-record-index-audit",
                "agent-index-note",
                "machine-knowledge-note",
                "operation-journal",
            },
        )
        manifest = Path(result["manifest"])
        self.assertTrue(manifest.is_file())
        manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest_value["status"], "completed")
        self.assertEqual(len(manifest_value["roles"]), 8)
        current = _owned_snapshot(self.output, self.title)
        self.assertNotEqual(current, self.baseline)
        page = self.output / "human/changes" / f"{self.title}.md"
        text = page.read_text(encoding="utf-8")
        self.assertNotIn("旧正文只说明", text)
        self.assertEqual(text.count("新正文明确替换旧结论"), 1)
        self.assertEqual(page.read_bytes(), (self.output / "markdown/changes" / f"{self.title}.md").read_bytes())
        self.assertEqual(current["metadata"]["record_id"], self.baseline["metadata"]["record_id"])
        self.assertEqual(current["metadata"]["created_at_utc"], self.baseline["metadata"]["created_at_utc"])
        self.assertEqual(current["metadata"]["linked_pages"], self.baseline["metadata"]["linked_pages"])
        rolled_back = invoke("record-rollback", "--out", str(self.output), "--manifest", str(manifest))
        self.assertEqual(rolled_back.returncode, 0, rolled_back.stderr)
        self.assertFalse(json.loads(rolled_back.stdout)["idempotent"])
        self.assertEqual(_owned_snapshot(self.output, self.title), self.baseline)
        repeated = invoke("record-rollback", "--out", str(self.output), "--manifest", str(manifest))
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertTrue(json.loads(repeated.stdout)["idempotent"])
        self.assertEqual(_owned_snapshot(self.output, self.title), self.baseline)

    def test_exact_target_kind_and_cli_mode_failures_do_not_change_owned_roles(self) -> None:
        missing = invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "change",
            "--title",
            "不存在的记录",
            "--body",
            str(self.new_body),
            "--replace",
            "--link",
            "OrderService",
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("target does not exist", missing.stderr)
        self.assertFalse((self.output / "human/changes/不存在的记录.md").exists())
        wrong_kind = invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "analysis",
            "--title",
            self.title,
            "--body",
            str(self.new_body),
            "--replace",
            "--link",
            "OrderService",
        )
        self.assertEqual(wrong_kind.returncode, 2)
        self.assertIn("kind mismatch", wrong_kind.stderr)
        conflicting = invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "change",
            "--title",
            self.title,
            "--body",
            str(self.new_body),
            "--append",
            "--replace",
        )
        self.assertEqual(conflicting.returncode, 2)
        self.assertIn("not allowed with argument", conflicting.stderr)
        self.assertEqual(_owned_snapshot(self.output, self.title), self.baseline)
        failed_operations = invoke(
            "operations",
            "list",
            "--out",
            str(self.output),
            "--operation",
            "record",
            "--status",
            "failed",
            "--limit",
            "10",
        )
        self.assertEqual(failed_operations.returncode, 0, failed_operations.stderr)
        events = json.loads(failed_operations.stdout)["operations"]
        self.assertGreaterEqual(len(events), 2)
        self.assertTrue(
            all(
                len(item["evidence_paths"]) == 1
                and item["evidence_paths"][0].startswith("workspace-meta/record-replace/")
                and item["evidence_paths"][0].endswith("/manifest.json")
                for item in events
            )
        )

    def test_body_and_explicit_evidence_validation_failures_are_stable(self) -> None:
        empty = self.root / "empty.md"
        empty.write_text("\n", encoding="utf-8")
        invalid = self.root / "invalid.md"
        invalid.write_bytes(b"\xff\xfe\x00")
        for path, expected in ((empty, "must not be empty"), (invalid, "valid UTF-8")):
            failed = invoke(
                "record",
                "--out",
                str(self.output),
                "--kind",
                "change",
                "--title",
                self.title,
                "--body",
                str(path),
                "--replace",
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn(expected, failed.stderr)
        missing_body = invoke(
            "record", "--out", str(self.output), "--kind", "change", "--title", self.title, "--replace"
        )
        self.assertEqual(missing_body.returncode, 2)
        self.assertIn("--body", missing_body.stderr)
        missing_link = self._replace("--link", "页面绝对不存在")
        self.assertEqual(missing_link.returncode, 2)
        self.assertIn("must match one page", missing_link.stderr)
        ambiguous_link = self._replace("--link", "")
        self.assertEqual(ambiguous_link.returncode, 2)
        self.assertIn("must match one page", ambiguous_link.stderr)
        self.assertEqual(_owned_snapshot(self.output, self.title), self.baseline)

    def test_promotion_failure_restores_all_roles_and_leaves_no_sqlite_sidecars(self) -> None:
        for fault in ("after-agent-index-note", "after-machine-knowledge-note"):
            with self.subTest(fault=fault):
                with self.assertRaisesRegex(CkbError, "injected record replace promotion failure"):
                    replace_note(self.output, "change", self.title, self.new_body, fault=fault)
                self.assertEqual(_owned_snapshot(self.output, self.title), self.baseline)
        for relative in ("agent-index.sqlite", "machine/knowledge.sqlite"):
            for suffix in ("-wal", "-shm", "-journal"):
                self.assertFalse(Path(str(self.output / relative) + suffix).exists())
        manifests = sorted((self.output / "workspace-meta/record-replace").glob("*/manifest.json"))
        self.assertTrue(manifests)
        failure = json.loads(manifests[-1].read_text(encoding="utf-8"))
        self.assertEqual(failure["status"], "failed-restored")
        self.assertEqual(failure["restore_errors"], [])

    def test_candidate_mirror_mismatch_blocks_promotion(self) -> None:
        with self.assertRaisesRegex(CkbError, "candidate audit failed"):
            replace_note(self.output, "change", self.title, self.new_body, fault="candidate-mirror-diff")
        self.assertEqual(_owned_snapshot(self.output, self.title), self.baseline)

    def test_rollback_detects_external_drift(self) -> None:
        replaced = self._replace()
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        result = json.loads(replaced.stdout)
        target = self.output / "human/changes" / f"{self.title}.md"
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("外部并发修改。\n")
        rollback = invoke("record-rollback", "--out", str(self.output), "--manifest", result["manifest"])
        self.assertEqual(rollback.returncode, 2)
        self.assertIn("rollback conflict", rollback.stderr)
        self.assertIn("外部并发修改", target.read_text(encoding="utf-8"))

    def test_explicit_evidence_replaces_old_links_and_create_append_remain_compatible(self) -> None:
        projection = json.loads((self.output / "markdown/projection.json").read_text(encoding="utf-8"))
        old_links = list(self.baseline["metadata"]["linked_pages"])
        replacement_title = next(page["title"] for page in projection["pages"] if page["title"] not in old_links)
        replaced = self._replace("--link", replacement_title)
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        metadata = json.loads((self.output / "workspace-meta/notes" / f"{self.title}.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["linked_pages"], [replacement_title])
        self.assertNotEqual(metadata["linked_pages"], old_links)
        second_body = self.root / "second.md"
        second_body.write_text("## 新建记录\n\n普通新建仍然通过受控入口写入完整角色。\n", encoding="utf-8")
        created = invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "analysis",
            "--title",
            "普通新建兼容记录",
            "--body",
            str(second_body),
            "--link",
            replacement_title,
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        append_body = self.root / "append.md"
        append_body.write_text("追加内容继续使用既有语义，并进入相同索引。\n", encoding="utf-8")
        appended = invoke(
            "record",
            "--out",
            str(self.output),
            "--kind",
            "analysis",
            "--title",
            "普通新建兼容记录",
            "--body",
            str(append_body),
            "--link",
            replacement_title,
            "--append",
        )
        self.assertEqual(appended.returncode, 0, appended.stderr)
        self.assertIn("追加内容继续使用既有语义", Path(json.loads(appended.stdout)["file"]).read_text(encoding="utf-8"))


class RecordReplaceLockTests(unittest.TestCase):
    def _wait_for(self, path: Path, process: subprocess.Popen[str]) -> None:
        deadline = time.monotonic() + 10.0
        while not path.is_file() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(path.is_file(), f"process={process.poll()}")

    def test_cross_process_owner_liveness_recovery_and_release_token_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-record-replace-owner-lock-") as value:
            root = Path(value)
            output = root / "output"
            ready = root / "live-ready.json"
            release = root / "live-release"
            holder_code = r"""
from pathlib import Path
import json,sys,time
sys.path.insert(0, sys.argv[1])
import ckb_core.record_replace as replace
with replace._replace_lock(Path(sys.argv[2])) as acquired:
    Path(sys.argv[3]).write_text(json.dumps({'pid': acquired['owner_pid'], 'token': acquired['owner_token']}), encoding='utf-8')
    while not Path(sys.argv[4]).exists():
        time.sleep(0.02)
"""
            holder = subprocess.Popen(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-c",
                    holder_code,
                    str((SKILL_ROOT / "scripts").resolve()),
                    str(output),
                    str(ready),
                    str(release),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            try:
                self._wait_for(ready, holder)
                owner = json.loads(ready.read_text(encoding="utf-8"))
                self.assertNotEqual(owner["pid"], os.getpid())
                lock = output / "workspace-meta/record-replace/.lock"
                old = time.time() - 10.0
                os.utime(lock, (old, old))
                before = lock.stat()
                with (
                    patch.object(record_replace_module, "REPLACE_LOCK_STALE_SECONDS", 0.05),
                    patch.object(record_replace_module, "REPLACE_LOCK_TIMEOUT_SECONDS", 0.10),
                ):
                    with self.assertRaises(record_replace_module.RecordReplaceLockError) as live:
                        with record_replace_module._replace_lock(output):
                            self.fail("aged live record replacement owner was stolen")
                self.assertIn(
                    live.exception.category,
                    {"concurrent-record-replace-lock", "record-replace-lock-owner-live"},
                )
                after = lock.stat()
                self.assertEqual((after.st_ino, after.st_size, after.st_mtime_ns), (before.st_ino, before.st_size, before.st_mtime_ns))
            finally:
                release.write_text("release", encoding="ascii")
                stdout, stderr = holder.communicate(timeout=15)
                self.assertEqual(holder.returncode, 0, stdout + stderr)
            self.assertFalse((output / "workspace-meta/record-replace/.lock").exists())

            dead_ready = root / "dead-ready"
            dead_code = r"""
from pathlib import Path
import os,sys
sys.path.insert(0, sys.argv[1])
import ckb_core.record_replace as replace
with replace._replace_lock(Path(sys.argv[2])):
    Path(sys.argv[3]).write_text('ready', encoding='ascii')
    os._exit(0)
"""
            dead = subprocess.Popen(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-c",
                    dead_code,
                    str((SKILL_ROOT / "scripts").resolve()),
                    str(output),
                    str(dead_ready),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            stdout, stderr = dead.communicate(timeout=15)
            self.assertEqual(dead.returncode, 0, stdout + stderr)
            lock = output / "workspace-meta/record-replace/.lock"
            self.assertTrue(lock.is_file())
            old = time.time() - 10.0
            os.utime(lock, (old, old))
            with (
                patch.object(record_replace_module, "REPLACE_LOCK_STALE_SECONDS", 0.05),
                patch.object(record_replace_module, "REPLACE_LOCK_TIMEOUT_SECONDS", 1.0),
            ):
                with record_replace_module._replace_lock(output) as recovered:
                    self.assertEqual(recovered["recovered_category"], "record-replace-lock-owner-dead")
            self.assertFalse(lock.exists())

            lock.parent.mkdir(parents=True, exist_ok=True)
            lock.write_text("{unverifiable-owner", encoding="utf-8")
            os.utime(lock, (old, old))
            with (
                patch.object(record_replace_module, "REPLACE_LOCK_STALE_SECONDS", 0.05),
                patch.object(record_replace_module, "REPLACE_LOCK_TIMEOUT_SECONDS", 0.05),
            ):
                with self.assertRaises(record_replace_module.RecordReplaceLockError) as unverifiable:
                    with record_replace_module._replace_lock(output):
                        self.fail("unverifiable stale record replacement lock was recovered")
            self.assertEqual(unverifiable.exception.category, "record-replace-lock-record-invalid")
            self.assertEqual(lock.read_text(encoding="utf-8"), "{unverifiable-owner")
            lock.unlink()

            drift_code = r"""
from pathlib import Path
import os,sys
path = Path(sys.argv[1])
offset = int(sys.argv[2])
with path.open('r+b', buffering=0) as handle:
    handle.seek(offset)
    handle.write(b'f' * 32)
    os.fsync(handle.fileno())
"""
            with self.assertRaises(record_replace_module.RecordReplaceLockError) as drift:
                with record_replace_module._replace_lock(output) as acquired:
                    lock = output / "workspace-meta/record-replace/.lock"
                    value = record_replace_module._owner_descriptor_bytes(acquired["_descriptor"])
                    offset = value.index(acquired["owner_token"].encode("ascii"))
                    if os.name == "nt":
                        offset += value[:offset].count(b"\n")
                    changed = subprocess.run(
                        [sys.executable, "-X", "utf8", "-c", drift_code, str(lock), str(offset)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                    )
                    self.assertEqual(changed.returncode, 0, changed.stdout + changed.stderr)
            self.assertEqual(drift.exception.category, "record-replace-lock-release-owner-token-drift")
            self.assertTrue(lock.is_file())
            drifted_record = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(drifted_record["owner_token"], "f" * 32)
            lock.unlink()


if __name__ == "__main__":
    unittest.main()
