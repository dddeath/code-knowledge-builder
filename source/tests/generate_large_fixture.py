from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--modules", type=int, default=30)
    parser.add_argument("--files-per-module", type=int, default=40)
    parser.add_argument("--declarations-per-file", type=int, default=10)
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    suffixes = ("py", "js", "c", "cpp")
    for module_index in range(args.modules):
        suffix = suffixes[module_index % len(suffixes)]
        module = root / f"module_{module_index:02d}"
        module.mkdir()
        for file_index in range(args.files_per_module):
            path = module / f"file_{file_index:03d}.{suffix}"
            if suffix == "py":
                body = "\n\n".join(f"def function_{module_index}_{file_index}_{n}(value):\n    return value + {n}" for n in range(args.declarations_per_file))
            elif suffix == "js":
                body = "\n".join(f"export function function_{module_index}_{file_index}_{n}(value) {{ return value + {n}; }}" for n in range(args.declarations_per_file))
            elif suffix == "c":
                body = "\n".join(f"int function_{module_index}_{file_index}_{n}(int value) {{ return value + {n}; }}" for n in range(args.declarations_per_file))
            else:
                body = "\n".join(f"int function_{module_index}_{file_index}_{n}(int value) {{ return value + {n}; }}" for n in range(args.declarations_per_file))
            path.write_text(body + "\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "-C", str(root), "init"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "large@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Large Fixture"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "large fixture"], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
