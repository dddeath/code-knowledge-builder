import argparse, json, os, pathlib, subprocess, sys
parser = argparse.ArgumentParser(description="Run the Windows acceptance suite or selected entry probes.")
parser.add_argument("root", type=pathlib.Path)
parser.add_argument("evidence", type=pathlib.Path)
parser.add_argument("git", type=pathlib.Path)
parser.add_argument("--test", action="append", dest="tests", help="Run only this unittest selector; repeat for multiple probes.")
args = parser.parse_args()
root = args.root.resolve()
evidence = args.evidence.resolve()
git = args.git.resolve()
evidence.mkdir(parents=True, exist_ok=True)
environment = os.environ.copy()
environment['PATH'] = str(git.parent) + os.pathsep + environment.get('PATH', '')
test_runner = """
import pathlib, sys, unittest
root = pathlib.Path(sys.argv[1])
sys.path[:0] = [str(root / 'tests'), str(root / 'scripts')]
unittest.main(module=None, argv=['unittest', *sys.argv[2:]])
"""
default_tests = [
    "test_recruitment_migration_provenance", "test_migration", "test_knowledge_batch_migration", "test_recruitment_output_contract",
    "test_ckb.CodeKnowledgeBuilderTests.test_reviewed_text_reference_is_searchable_revisioned_and_reversible",
    "test_reference_pdf", "test_reference_pdf_effect_benchmark", "test_reference_pdf_ocr_fidelity_benchmark",
    "test_reference_web",
]
commands = [
    [str(git), "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-C", str(root), "rev-parse", "--show-toplevel"],
    [str(git), "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-C", str(root), "branch", "--show-current"],
    [str(git), "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-C", str(root), "rev-parse", "HEAD"],
    [sys.executable, "-X", "utf8", "-c", test_runner, str(root),
     *(args.tests or default_tests), "-v"],
]
records = []
for command in commands:
    result = subprocess.run(command, cwd=root, capture_output=True, env=environment)
    records.append({"command": command, "actual_pwd": str(root), "exit_status": result.returncode,
                    "stdout": result.stdout.decode("utf-8", errors="replace"),
                    "stderr": result.stderr.decode("utf-8", errors="replace")})
(evidence / "windows-native-v3.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "passed" if all(r["exit_status"] == 0 for r in records) else "failed",
                  "record": str(evidence / "windows-native-v3.json"),
                  "exit_statuses": [r["exit_status"] for r in records]}, ensure_ascii=False))
raise SystemExit(0 if all(r["exit_status"] == 0 for r in records) else 1)
