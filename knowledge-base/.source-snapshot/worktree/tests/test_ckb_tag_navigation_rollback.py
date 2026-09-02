from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
PROTOTYPE = REPO / "prototypes" / "ckb-tag-navigation"
FIXTURE = REPO / "tests" / "fixtures" / "tag-navigation"
sys.path.insert(0, str(PROTOTYPE))

from ckb_tag_navigation.contracts import TagNavigationError, sha256_file
import ckb_tag_navigation.store as store_module
from ckb_tag_navigation.store import connect, initialize, replay_with_rollback, rollback


class TagNavigationRollbackTests(unittest.TestCase):
    def test_absent_target_returns_to_absent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-tag-rollback-absent-") as temporary:
            root = Path(temporary)
            database = root / "tags.sqlite"
            replay_with_rollback(FIXTURE / "assertions.jsonl", database, root / "rollback.json")
            result = rollback(root / "rollback.json", root)
            self.assertEqual("absent", result["restored"])
            self.assertFalse(database.exists())

            fault_database = root / "fault.sqlite"
            fault_manifest = root / "fault.rollback.json"

            def fail_manifest_write(path: Path, value: dict) -> None:
                path.with_name(path.name + ".tmp").write_text("partial", encoding="utf-8")
                path.write_text("partial", encoding="utf-8")
                raise OSError("injected manifest write failure")

            with mock.patch.object(store_module, "atomic_write_json", side_effect=fail_manifest_write):
                with self.assertRaisesRegex(OSError, "injected manifest write failure"):
                    replay_with_rollback(FIXTURE / "assertions.jsonl", fault_database, fault_manifest)
            self.assertFalse(fault_database.exists())
            self.assertFalse(fault_manifest.exists())
            self.assertFalse(fault_manifest.with_name(fault_manifest.name + ".tmp").exists())

    def test_present_target_returns_to_byte_identical_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-tag-rollback-present-") as temporary:
            root = Path(temporary)
            database = root / "tags.sqlite"
            connection = connect(database)
            initialize(connection)
            connection.close()
            baseline = sha256_file(database)
            replay_with_rollback(FIXTURE / "assertions.jsonl", database, root / "rollback.json")
            result = rollback(root / "rollback.json", root)
            self.assertEqual(baseline, result["restored"])
            self.assertEqual(baseline, sha256_file(database))

            fault_database = root / "fault.sqlite"
            connection = connect(fault_database)
            initialize(connection)
            connection.close()
            fault_baseline = fault_database.read_bytes()
            fault_manifest = root / "fault.rollback.json"

            def fail_manifest_write(path: Path, value: dict) -> None:
                path.with_name(path.name + ".tmp").write_text("partial", encoding="utf-8")
                path.write_text("partial", encoding="utf-8")
                raise OSError("injected manifest write failure")

            with mock.patch.object(store_module, "atomic_write_json", side_effect=fail_manifest_write):
                with self.assertRaisesRegex(OSError, "injected manifest write failure"):
                    replay_with_rollback(FIXTURE / "assertions.jsonl", fault_database, fault_manifest)
            self.assertEqual(fault_baseline, fault_database.read_bytes())
            self.assertFalse(fault_database.with_name(fault_database.name + ".baseline").exists())
            self.assertFalse(fault_manifest.exists())
            self.assertFalse(fault_manifest.with_name(fault_manifest.name + ".tmp").exists())

            copy_failure_database = root / "copy-failure.sqlite"
            connection = connect(copy_failure_database)
            initialize(connection)
            connection.close()
            copy_failure_baseline = copy_failure_database.read_bytes()
            copy_failure_manifest = root / "copy-failure.rollback.json"
            copy_failure_state: dict[str, bytes] = {}
            real_copy2 = store_module.shutil.copy2

            def fail_manifest_before_restore_copy(path: Path, value: dict) -> None:
                copy_failure_state["database_after_manifest_failure"] = copy_failure_database.read_bytes()
                path.with_name(path.name + ".tmp").write_text("partial", encoding="utf-8")
                path.write_text("partial", encoding="utf-8")
                raise OSError("injected manifest write failure before restore copy")

            def fail_restore_copy(source: Path, target: Path) -> None:
                if Path(target).name.endswith(".restore.tmp"):
                    raise OSError("injected restore copy failure")
                real_copy2(source, target)

            with mock.patch.object(store_module, "atomic_write_json", side_effect=fail_manifest_before_restore_copy):
                with mock.patch.object(store_module.shutil, "copy2", side_effect=fail_restore_copy):
                    with self.assertRaises(TagNavigationError) as raised:
                        replay_with_rollback(
                            FIXTURE / "assertions.jsonl",
                            copy_failure_database,
                            copy_failure_manifest,
                        )
            self.assertEqual("REPLAY_RECOVERY_FAILED", raised.exception.reason)
            self.assertIn("injected restore copy failure", raised.exception.detail)
            self.assertEqual(copy_failure_state["database_after_manifest_failure"], copy_failure_database.read_bytes())
            copy_failure_backup = copy_failure_database.with_name(copy_failure_database.name + ".baseline")
            self.assertTrue(copy_failure_backup.exists())
            self.assertEqual(copy_failure_baseline, copy_failure_backup.read_bytes())
            self.assertTrue(copy_failure_manifest.exists())
            self.assertTrue(copy_failure_manifest.with_name(copy_failure_manifest.name + ".tmp").exists())

            hash_failure_database = root / "hash-failure.sqlite"
            connection = connect(hash_failure_database)
            initialize(connection)
            connection.close()
            hash_failure_baseline = hash_failure_database.read_bytes()
            hash_failure_manifest = root / "hash-failure.rollback.json"
            hash_failure_state: dict[str, bytes] = {}
            real_sha256_file = store_module.sha256_file

            def fail_manifest_before_restore_hash(path: Path, value: dict) -> None:
                hash_failure_state["database_after_manifest_failure"] = hash_failure_database.read_bytes()
                path.with_name(path.name + ".tmp").write_text("partial", encoding="utf-8")
                path.write_text("partial", encoding="utf-8")
                raise OSError("injected manifest write failure before restore hash")

            def fail_restore_hash(path: Path) -> str:
                if Path(path).name.endswith(".restore.tmp"):
                    return "0" * 64
                return real_sha256_file(path)

            with mock.patch.object(store_module, "atomic_write_json", side_effect=fail_manifest_before_restore_hash):
                with mock.patch.object(store_module, "sha256_file", side_effect=fail_restore_hash):
                    with self.assertRaises(TagNavigationError) as raised:
                        replay_with_rollback(
                            FIXTURE / "assertions.jsonl",
                            hash_failure_database,
                            hash_failure_manifest,
                        )
            self.assertEqual("REPLAY_RECOVERY_FAILED", raised.exception.reason)
            self.assertIn("restore 临时文件 hash 不等于 baseline", raised.exception.detail)
            self.assertEqual(hash_failure_state["database_after_manifest_failure"], hash_failure_database.read_bytes())
            hash_failure_backup = hash_failure_database.with_name(hash_failure_database.name + ".baseline")
            self.assertTrue(hash_failure_backup.exists())
            self.assertEqual(hash_failure_baseline, hash_failure_backup.read_bytes())
            self.assertTrue(hash_failure_manifest.exists())
            self.assertTrue(hash_failure_manifest.with_name(hash_failure_manifest.name + ".tmp").exists())
            self.assertTrue(hash_failure_database.with_name(hash_failure_database.name + ".restore.tmp").exists())

    def test_drift_blocks_rollback_and_preserves_current_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-tag-rollback-drift-") as temporary:
            root = Path(temporary)
            database = root / "tags.sqlite"
            replay_with_rollback(FIXTURE / "assertions.jsonl", database, root / "rollback.json")
            database.write_bytes(database.read_bytes() + b"manual-drift")
            drifted = database.read_bytes()
            with self.assertRaises(TagNavigationError) as raised:
                rollback(root / "rollback.json", root)
            self.assertEqual("ROLLBACK_DRIFT", raised.exception.reason)
            self.assertEqual(drifted, database.read_bytes())


if __name__ == "__main__":
    unittest.main()
