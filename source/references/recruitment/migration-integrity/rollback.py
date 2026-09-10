"""仅回退已核验的来源迁移补丁；不触碰 Git 登记、其他修改或知识库。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    target, bundle = args.target.resolve(), args.bundle.resolve()
    manifest = json.loads((bundle / "patch-manifest.json").read_text(encoding="utf-8"))
    patch = bundle / "implementation.patch"
    if digest(patch) != manifest["patch_sha256"]:
        raise SystemExit("patch digest mismatch")
    for relative, record in manifest["files"].items():
        path = (target / relative).resolve()
        if not path.is_relative_to(target):
            raise SystemExit("path leaves rollback target")
        if digest(path) != record["modified_sha256"]:
            raise SystemExit("modified file drift: " + relative)
    for options in (["--reverse", "--check"], ["--reverse"]):
        command = ["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false",
                   "-C", str(target), "apply", *options, str(patch)]
        result = subprocess.run(command, text=True, capture_output=True)
        print(json.dumps({"command": command, "stdout": result.stdout, "stderr": result.stderr,
                          "exit_status": result.returncode}, ensure_ascii=False))
        if result.returncode:
            raise SystemExit(result.returncode)
    for relative, record in manifest["files"].items():
        if digest(target / relative) != record["baseline_sha256"]:
            raise SystemExit("restored file digest mismatch: " + relative)
    print(json.dumps({"status": "restored", "files": len(manifest["files"]),
                      "baseline": manifest["baseline"], "target": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
