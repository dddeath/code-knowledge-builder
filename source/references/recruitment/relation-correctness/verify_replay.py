"""在独立临时目录核对固定基线、补丁应用和真实回滚。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = 'b6c36ee11efeff75021782a82babf7a5c6452276'
ROOT = Path(__file__).resolve().parents[3]
TEST = 'tests/test_recruitment_relation_scope.py'
SEED = ['scripts/ckb_core/__init__.py', 'scripts/ckb_core/common.py',
        'scripts/ckb_core/parsers.py', 'scripts/ckb_core/llm_wiki_capabilities.py',
        'tests/test_management_agent.py']
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']

ROLLBACK = '''import hashlib, json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1]).resolve()
artifacts = pathlib.Path(__file__).resolve().parent
assert (root / '.relation-replay-fixture').read_text() == 'isolated-relation-probe'
manifest = json.loads((artifacts / 'modified-files.json').read_text())
for name, digest in manifest.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
patch = artifacts / 'relation-correctness.patch'
base = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(root), 'apply', '--reverse']
subprocess.run(base + ['--check', str(patch)], check=True)
subprocess.run(base + [str(patch)], check=True)
print('ROLLBACK_APPLIED: scoped patch reversed after exact modified-byte checks')
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    records = []

    def run(command, cwd):
        p = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        records.append({'command': [str(c) for c in command], 'cwd': str(cwd),
                        'stdout': p.stdout, 'stderr': p.stderr, 'exit_status': p.returncode})
        (out / 'replay.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
        return p

    head = subprocess.check_output(GIT + ['-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    patch = out / 'relation-correctness.patch'
    patch.write_bytes(subprocess.check_output(GIT + ['-C', str(ROOT), 'diff', '--binary', BASE, head]))
    (out / 'rollback.py').write_text(ROLLBACK)
    assert 'ROLLBACK_APPLIED' in (out / 'rollback.py').read_text()
    test_source = (ROOT / TEST).read_bytes()
    with tempfile.TemporaryDirectory(prefix='ckb-relation-replay-') as tmp:
        root = Path(tmp)
        (root / '.relation-replay-fixture').write_text('isolated-relation-probe')
        original = {}
        for path in SEED:
            data = subprocess.check_output(GIT + ['-C', str(ROOT), 'show', BASE + ':' + path])
            dest = root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            original[path] = hashlib.sha256(data).hexdigest()
        test = root / TEST
        test.write_bytes(test_source)
        baseline = run([sys.executable, TEST], root)
        baseline_metrics = run([sys.executable, TEST, '--measure'], root)
        assert baseline.returncode == 1 and 'test_real_maintenance_append' in baseline.stderr
        assert baseline_metrics.returncode == 0
        test.unlink()
        assert run(GIT + ['-C', str(root), 'apply', '--check', str(patch)], root).returncode == 0
        assert run(GIT + ['-C', str(root), 'apply', str(patch)], root).returncode == 0
        modified = run([sys.executable, TEST], root)
        modified_metrics = run([sys.executable, TEST, '--measure'], root)
        assert modified.returncode == modified_metrics.returncode == 0
        paths = subprocess.check_output(GIT + ['-C', str(ROOT), 'diff', '--name-only', BASE, head], text=True).splitlines()
        hashes = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}
        (out / 'modified-files.json').write_text(json.dumps(hashes, indent=2))
        result = run([sys.executable, str(out / 'rollback.py'), str(root)], root)
        assert result.returncode == 0
        assert all(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest for path, digest in original.items())
        assert all(not (root / path).exists() for path in paths if path not in original)
        test.write_bytes(test_source)
        reverted = run([sys.executable, TEST], root)
        reverted_metrics = run([sys.executable, TEST, '--measure'], root)
        assert reverted.returncode == 1 and 'test_real_maintenance_append' in reverted.stderr
        assert reverted_metrics.returncode == 0
        assert json.loads(baseline_metrics.stdout) == json.loads(reverted_metrics.stdout)
        summary = {'baseline': BASE, 'head': head, 'baseline_original_sha256': original,
                   'modified_sha256': hashes, 'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
                   'baseline': {'commit': BASE, 'metrics': json.loads(baseline_metrics.stdout)},
                   'modified': {'commit': head, 'metrics': json.loads(modified_metrics.stdout)},
                   'rollback': {'status': 'passed', 'baseline_bytes_restored': True,
                                'baseline_metrics_restored': True, 'real_error_reproduced': True},
                   'temporary_fixture_cleaned_on_exit': True}
        (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    assert not root.exists()
    print(json.dumps({'status': 'passed', 'head': head, 'out': str(out), 'rollback': summary['rollback']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
