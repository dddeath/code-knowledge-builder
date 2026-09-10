from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from statistics import median
import sys


ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE = ROOT / "prototypes" / "ckb-tag-navigation"
sys.path.insert(0, str(PROTOTYPE))

from ckb_tag_navigation.contracts import canonical_json_bytes, validate_policy
from ckb_tag_navigation.projection import build_projection
from ckb_tag_navigation.state_machine import audit_database
from ckb_tag_navigation.store import read_assertion_jsonl


CONDITIONS = ("no_tag", "machine_tag", "confirmed_tag")


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"根字段不是对象: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(result: Path) -> dict:
    report = _load(result / "report.json")
    raw = _load(result / "raw-results.json")
    protocol = _load(result / "protocol.json")
    policy = validate_policy(_load(result / "policy.json"))
    audit = _load(result / "audit.json")
    projection = _load(result / "projection.json")
    before = _load(result / "source-before.json")
    after = _load(result / "source-after.json")
    determinism = _load(result / "determinism-audit.json")
    rollback = _load(result / "rollback-verification.json")
    study_command = _load(result / "study-command-output.json")
    study_command_rollback = _load(result / "study-command-rollback-output.json")
    assertions = read_assertion_jsonl(result / "assertions.jsonl")

    rows_by_condition: dict[str, list[dict]] = defaultdict(list)
    for row in raw["records"]:
        rows_by_condition[row["condition"]].append(row)
    recomputed_navigation: dict[str, dict] = {}
    for condition in CONDITIONS:
        rows = rows_by_condition[condition]
        steps = [row["jump_steps"] for row in rows if row["jump_steps"] is not None]
        recomputed_navigation[condition] = {
            "task_count": len(rows),
            "discoverable_count": sum(bool(row["discoverable_within_budget"]) for row in rows),
            "discoverability_rate": round(sum(bool(row["discoverable_within_budget"]) for row in rows) / len(rows), 6),
            "total_jump_steps": sum(steps),
            "median_jump_steps": median(steps) if steps else None,
            "error_navigation_count": sum(row["error_navigation_count"] for row in rows),
        }
    recorded_navigation = {
        condition: {field: report["conditions"][condition][field] for field in recomputed_navigation[condition]}
        for condition in CONDITIONS
    }
    regenerated_audit = audit_database(
        result / "tags.sqlite",
        policy,
        protocol["source"]["expected_commit"],
        protocol["execution"]["as_of"],
    )
    regenerated_projection = build_projection(regenerated_audit, policy)
    connection = sqlite3.connect(result / "tags.sqlite")
    try:
        database_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        database_rows = int(connection.execute("SELECT COUNT(*) FROM assertions").fetchone()[0])
    finally:
        connection.close()
    machine_pairs = {
        (item["target"]["path"], item["tag"])
        for item in assertions
        if item["action"] == "propose"
    }
    confirmed_pairs = {
        (item["target"]["path"], item["tag"])
        for item in audit["results"]
        if item["state"] == "confirmed"
    }
    failure_expectations = {
        "source-drift.json": "SOURCE_DRIFT",
        "invalid-tag.json": "INVALID_TAG",
        "rollback-drift.json": "ROLLBACK_DRIFT",
    }
    failure_checks = {}
    for name, reason in failure_expectations.items():
        sample = _load(result / "failure-samples" / name)
        expected_output_created = name == "rollback-drift.json"
        failure_checks[name] = (
            sample["status"] == "expected-failure"
            and sample["exit_code"] == 2
            and sample["result"]["reason"] == reason
            and sample["output_created"] is expected_output_created
        )
    checks = {
        "report_passed": report["status"] == "passed",
        "production_default_unchanged": report["production_default_changed"] is False,
        "system_claim_only": report["effect_claim"] == "system-navigation-proxy-only",
        "human_result_pending": report["human_result"] == "pending-human-validation",
        "fixed_conditions": protocol["conditions"] == list(CONDITIONS),
        "fixed_task_order": raw["task_order"] == protocol["execution"]["task_order"],
        "fixed_budget": raw["step_budget"] == protocol["execution"]["step_budget"] == 2,
        "navigation_metrics_recomputed": recomputed_navigation == recorded_navigation,
        "audit_byte_recomputed": canonical_json_bytes(regenerated_audit) == canonical_json_bytes(audit),
        "projection_byte_recomputed": canonical_json_bytes(regenerated_projection) == canonical_json_bytes(projection),
        "sqlite_integrity": database_integrity == "ok",
        "assertion_line_count": len(assertions) == 53,
        "database_deduplicated_count": database_rows == 52,
        "machine_pair_count": len(machine_pairs) == 18,
        "confirmed_pair_count": len(confirmed_pairs) == 12,
        "state_counts": audit["summary"] == {"candidate": 2, "confirmed": 12, "contested": 2, "deprecated": 2},
        "source_vault_unchanged": before["vault"]["tree_sha256"] == after["vault"]["tree_sha256"],
        "source_machine_unchanged": before["machine_sha256"] == after["machine_sha256"],
        "source_completion_unchanged": before["complete_sha256"] == after["complete_sha256"],
        "source_commit_frozen": before["commit"] == protocol["source"]["expected_commit"],
        "repeat_run_deterministic": determinism["status"] == "passed" and all(determinism["checks"].values()),
        "rollback_executed_twice": rollback["status"] == "passed" and len(rollback["runs"]) == 2 and all(item["exit_code"] == 0 for item in rollback["runs"]),
        "recorded_study_command_passed": study_command["exit_code"] == 0 and study_command["stdout"]["status"] == "passed" and study_command["stderr"] == "",
        "recorded_study_command_rolled_back": study_command_rollback["exit_code"] == 0 and study_command_rollback["stdout"]["status"] == "rolled-back" and study_command_rollback["stderr"] == "",
        "failure_samples_passed": all(failure_checks.values()),
        "runtime_vaults_not_committed": all(item["retained_in_git"] is False for item in report["isolation"]["vaults"].values()),
    }
    artifact_names = [
        "assertions.jsonl",
        "audit.json",
        "determinism-audit.json",
        "failure-samples/invalid-tag.json",
        "failure-samples/rollback-drift.json",
        "failure-samples/source-drift.json",
        "implementation.patch",
        "policy.json",
        "projection.json",
        "protocol.json",
        "raw-results.json",
        "report.json",
        "rollback.ps1",
        "rollback-verification.json",
        "runtime-report.json",
        "source-after.json",
        "source-before.json",
        "study-command-output.json",
        "study-command-rollback-output.json",
        "summary.md",
        "tags.sqlite",
        "verification-record.json",
        "verify_results.py",
    ]
    return {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "failure_checks": failure_checks,
        "recomputed_navigation": recomputed_navigation,
        "artifact_sha256": {name: _sha256(result / name) for name in artifact_names},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path)
    arguments = parser.parse_args()
    value = verify(arguments.result.resolve())
    output = arguments.out.resolve() if arguments.out else None
    if output:
        output.write_bytes(canonical_json_bytes(value))
        if _load(output) != value:
            raise ValueError("验证记录重开不一致")
    sys.stdout.buffer.write(canonical_json_bytes(value))
    return 0 if value["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
