from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PROTOTYPE = REPO / "prototypes" / "ckb-tag-navigation"
FIXTURE = REPO / "tests" / "fixtures" / "tag-navigation"
CLI = PROTOTYPE / "scripts" / "ckb_tag_navigation.py"
sys.path.insert(0, str(PROTOTYPE))

from ckb_tag_navigation.contracts import TagNavigationError, validate_assertion, validate_policy
from ckb_tag_navigation.store import replay_with_rollback


def assertions() -> list[dict]:
    return [json.loads(line) for line in (FIXTURE / "assertions.jsonl").read_text(encoding="utf-8").splitlines()]


class TagNavigationContractTests(unittest.TestCase):
    def test_five_schemas_are_strict_json_objects(self) -> None:
        schema_root = PROTOTYPE / "schemas"
        schemas = sorted(schema_root.glob("*.schema.json"))
        self.assertEqual(5, len(schemas))
        for path in schemas:
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("object", value["type"])
            self.assertFalse(value["additionalProperties"], path.name)

    def test_assertion_schema_excludes_conversation_and_secret_fields(self) -> None:
        sample = assertions()[0]
        validate_assertion(copy.deepcopy(sample))
        for field in ("conversation", "prompt", "secret"):
            invalid = copy.deepcopy(sample)
            invalid[field] = "forbidden"
            with self.assertRaises(TagNavigationError) as raised:
                validate_assertion(invalid)
            self.assertEqual("INVALID_SCHEMA", raised.exception.reason)

    def test_paths_tags_and_policy_are_bounded(self) -> None:
        sample = assertions()[0]
        invalid = copy.deepcopy(sample)
        invalid["target"]["path"] = "E:\\vault\\page.md"
        with self.assertRaises(TagNavigationError) as raised:
            validate_assertion(invalid)
        self.assertEqual("INVALID_PATH", raised.exception.reason)
        invalid = copy.deepcopy(sample)
        invalid["tag"] = "#topic/navigation"
        with self.assertRaises(TagNavigationError) as raised:
            validate_assertion(invalid)
        self.assertEqual("INVALID_TAG", raised.exception.reason)
        validate_policy(json.loads((FIXTURE / "policy.json").read_text(encoding="utf-8")))

    def test_replay_deduplicates_identical_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-tag-contract-") as temporary:
            root = Path(temporary)
            result = replay_with_rollback(FIXTURE / "assertions.jsonl", root / "tags.sqlite", root / "rollback.json")
            self.assertEqual(25, result["inserted"])
            self.assertEqual(1, result["duplicates"])
            self.assertEqual("ok", result["integrity_check"])

    def test_idempotency_conflict_rolls_back_entire_new_database(self) -> None:
        values = assertions()[:2]
        values[1] = copy.deepcopy(values[1])
        values[1]["assertion_id"] = "conflicting-assertion"
        values[1]["tag"] = "topic/other"
        values[1]["idempotency_key"] = values[0]["idempotency_key"]
        with tempfile.TemporaryDirectory(prefix="ckb-tag-conflict-") as temporary:
            root = Path(temporary)
            source = root / "conflict.jsonl"
            source.write_text("\n".join(json.dumps(value, ensure_ascii=False) for value in values) + "\n", encoding="utf-8")
            database = root / "tags.sqlite"
            with self.assertRaises(TagNavigationError) as raised:
                replay_with_rollback(source, database, root / "rollback.json")
            self.assertEqual("IDEMPOTENCY_CONFLICT", raised.exception.reason)
            self.assertFalse(database.exists())

    def test_cli_rejects_output_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-tag-cli-") as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            outside = root / "outside"
            workspace.mkdir()
            outside.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "replay",
                    "--input",
                    str(FIXTURE / "assertions.jsonl"),
                    "--database",
                    str(outside / "outside.sqlite"),
                    "--rollback-manifest",
                    str(workspace / "rollback.json"),
                    "--workspace-root",
                    str(workspace),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual("OUTPUT_OUTSIDE_WORKSPACE", json.loads(completed.stdout)["reason"])

            missing_root = subprocess.run(
                [sys.executable, str(CLI), "rollback", "--manifest", str(workspace / "rollback.json")],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(2, missing_root.returncode)
            self.assertIn("--workspace-root", missing_root.stderr)

            def digest(data: bytes) -> str:
                return hashlib.sha256(data).hexdigest()

            def run_rollback(manifest: Path) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "rollback",
                        "--manifest",
                        str(manifest),
                        "--workspace-root",
                        str(workspace),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )

            outside_target = outside / "target.bin"
            outside_target.write_bytes(b"outside-target")
            target_bytes = outside_target.read_bytes()
            target_outside_manifest = workspace / "target-outside.json"
            target_outside_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "target_path": str(outside_target),
                        "baseline_state": "absent",
                        "baseline_sha256": None,
                        "backup_path": None,
                        "generated_sha256": digest(target_bytes),
                    }
                ),
                encoding="utf-8",
            )
            target_result = run_rollback(target_outside_manifest)
            self.assertEqual(2, target_result.returncode)
            self.assertEqual("ROLLBACK_PATH_OUTSIDE_WORKSPACE", json.loads(target_result.stdout)["reason"])
            self.assertEqual(target_bytes, outside_target.read_bytes())

            inside_target = workspace / "target.bin"
            inside_target.write_bytes(b"inside-target")
            inside_bytes = inside_target.read_bytes()
            manifest_outside = outside / "manifest-outside.json"
            manifest_outside.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "target_path": str(inside_target),
                        "baseline_state": "absent",
                        "baseline_sha256": None,
                        "backup_path": None,
                        "generated_sha256": digest(inside_bytes),
                    }
                ),
                encoding="utf-8",
            )
            manifest_result = run_rollback(manifest_outside)
            self.assertEqual(2, manifest_result.returncode)
            self.assertEqual("ROLLBACK_PATH_OUTSIDE_WORKSPACE", json.loads(manifest_result.stdout)["reason"])
            self.assertEqual(inside_bytes, inside_target.read_bytes())

            outside_backup = outside / "baseline.bin"
            outside_backup.write_bytes(b"outside-baseline")
            backup_outside_manifest = workspace / "backup-outside.json"
            backup_outside_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "target_path": str(inside_target),
                        "baseline_state": "present",
                        "baseline_sha256": digest(outside_backup.read_bytes()),
                        "backup_path": str(outside_backup),
                        "generated_sha256": digest(inside_bytes),
                    }
                ),
                encoding="utf-8",
            )
            backup_result = run_rollback(backup_outside_manifest)
            self.assertEqual(2, backup_result.returncode)
            self.assertEqual("ROLLBACK_PATH_OUTSIDE_WORKSPACE", json.loads(backup_result.stdout)["reason"])
            self.assertEqual(inside_bytes, inside_target.read_bytes())


if __name__ == "__main__":
    unittest.main()
