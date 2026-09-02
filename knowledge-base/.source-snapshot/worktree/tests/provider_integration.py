#!/usr/bin/env python3
"""Exercise available real semantic providers and emit a machine-readable record."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "ckb.py"


def execute(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    values = os.environ.copy()
    values.pop("CKB_TEST_PROVIDER", None)
    if env:
        values.update(env)
    return subprocess.run(command, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=values)


def git(repo: Path, *args: str) -> None:
    result = execute(["git", "-C", str(repo), *args])
    if result.returncode:
        raise RuntimeError(result.stderr)


def provider_case(root: Path, language: str, relative: str, source: str, env: dict[str, str]) -> dict:
    repo = root / f"repo-{language}"
    repo.mkdir()
    source_path = repo / relative
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8", newline="\n")
    git(repo, "init")
    git(repo, "config", "user.email", "provider@example.invalid")
    git(repo, "config", "user.name", "Provider Fixture")
    git(repo, "add", ".")
    git(repo, "commit", "-m", language)
    output = root / f"out-{language}"
    init = execute([sys.executable, str(CLI), "init", "--repo", str(repo), "--out", str(output), "--format", "markdown"], env=env)
    if init.returncode:
        return {"status": "failed", "language": language, "stage": "init", "exit_status": init.returncode, "stdout": init.stdout, "stderr": init.stderr}
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    chunk_id = state["chunks"][0]["id"]
    built = execute([sys.executable, str(CLI), "build-chunk", "--out", str(output), "--chunk", chunk_id, "--stage", "all"], env=env)
    if built.returncode:
        return {"status": "failed", "language": language, "stage": "build", "exit_status": built.returncode, "stdout": built.stdout, "stderr": built.stderr}
    candidate = json.loads((output / "chunks" / chunk_id / "candidate.json").read_text(encoding="utf-8"))
    provider = next(item for item in candidate["providers"] if item["language"] == language)
    declarations = {item["id"] for item in candidate["entities"] if item["kind"] != "file" and item["language"] == language}
    covered = set(provider.get("covered_entity_ids", []))
    passed = provider.get("status") == "passed" and declarations <= covered and provider.get("document_symbol_counts", {}).get(relative, 0) > 0
    return {
        "status": "passed" if passed else "failed",
        "language": language,
        "provider": provider,
        "declaration_count": len(declarations),
        "covered_count": len(declarations & covered),
        "output": str(output.resolve()),
    }


def clangd_case(
    root: Path,
    name: str,
    source: str,
    clangd: Path,
    mode: str,
    *,
    language: str = "c",
    build_files: dict[str, str] | None = None,
    expected_fallback_standard: str | None = None,
) -> dict:
    repo = root / f"repo-{name}"
    repo.mkdir()
    relative = "main.cpp" if language == "cpp" else "main.c"
    (repo / relative).write_text(source, encoding="utf-8", newline="\n")
    for build_path, build_text in (build_files or {}).items():
        target = repo / build_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_text, encoding="utf-8", newline="\n")
    if mode == "exact":
        standard = "c++20" if language == "cpp" else "c17"
        (repo / "compile_commands.json").write_text(
            json.dumps(
                [
                    {
                        "directory": str(repo.resolve()),
                        "command": f"clang -std={standard} -I. -c {relative}",
                        "file": relative,
                    }
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    git(repo, "init")
    git(repo, "config", "user.email", "provider@example.invalid")
    git(repo, "config", "user.name", "Provider Fixture")
    git(repo, "add", ".")
    git(repo, "commit", "-m", name)
    output = root / f"out-{name}"
    env = {"CKB_CLANGD_COMMAND": str(clangd.resolve())}
    init = execute([sys.executable, str(CLI), "init", "--repo", str(repo), "--out", str(output), "--format", "markdown"], env=env)
    if init.returncode:
        return {"status": "failed", "case": name, "stage": "init", "exit_status": init.returncode, "stdout": init.stdout, "stderr": init.stderr}
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    chunk_id = state["chunks"][0]["id"]
    built = execute([sys.executable, str(CLI), "build-chunk", "--out", str(output), "--chunk", chunk_id, "--stage", "all"], env=env)
    if built.returncode:
        return {"status": "failed", "case": name, "stage": "build", "exit_status": built.returncode, "stdout": built.stdout, "stderr": built.stderr}
    candidate = json.loads((output / "chunks" / chunk_id / "candidate.json").read_text(encoding="utf-8"))
    provider = next(item for item in candidate["providers"] if item["language"] == language)
    declarations = {item["id"] for item in candidate["entities"] if item["kind"] != "file" and item["language"] == language}
    covered = set(provider.get("covered_entity_ids", []))
    fatal_count = len(provider.get("fatal_diagnostics", [])) + len(provider.get("fatal_stderr", []))
    if mode == "failure":
        passed = provider.get("status") == "failed" and fatal_count > 0 and provider.get("exit_status") == 0
    else:
        passed = (
            provider.get("status") == "passed"
            and provider.get("precision") == mode
            and provider.get("exit_status") == 0
            and declarations <= covered
            and provider.get("document_symbol_counts", {}).get(relative, 0) > 0
        )
        initialization = provider.get("initialization_options", {})
        if mode == "exact":
            passed = passed and "compilationDatabasePath" in initialization and "fallbackFlags" not in initialization
            passed = passed and not provider.get("warnings")
        if mode == "bounded-approximate":
            precision_warnings = provider.get("warnings", [])
            passed = passed and any(
                item.get("kind") == "compile-commands-unavailable"
                and item.get("precision") == "bounded-approximate"
                and item.get("absence_inference_allowed") is False
                for item in precision_warnings
            )
        if expected_fallback_standard is not None:
            fallback_evidence = initialization.get("fallbackEvidence", {})
            matches = fallback_evidence.get("matches", [])
            passed = passed and (
                initialization.get("fallbackFlags") == ["-x", "c++" if language == "cpp" else "c", f"-std={expected_fallback_standard}"]
                and fallback_evidence.get("selected") == expected_fallback_standard
                and fallback_evidence.get("resolution") == "build-config-unique"
                and {item.get("path") for item in matches} == {"SConstruct", "src/SConscript"}
                and any(
                    set(item.get("build_evidence", {}).get("paths", [])) == {"SConstruct", "src/SConscript"}
                    for item in provider.get("warnings", [])
                    if item.get("kind") == "compile-commands-unavailable"
                )
            )
    return {
        "status": "passed" if passed else "failed",
        "case": name,
        "language": language,
        "expected": mode,
        "provider": provider,
        "declaration_count": len(declarations),
        "covered_count": len(declarations & covered),
        "fatal_count": fatal_count,
        "output": str(output.resolve()),
    }


def csharp_case(root: Path, csharp_ls: Path, dotnet: Path, mode: str) -> dict:
    repo = root / f"repo-csharp-{mode}"
    repo.mkdir()
    if mode == "exact":
        (repo / "Demo.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>\n', encoding="utf-8", newline="\n")
    (repo / "Service.cs").write_text(
        "namespace Demo;\npublic class Service {\n public int Execute(int value) { var next = value + 1; return next; }\n}\n",
        encoding="utf-8",
        newline="\n",
    )
    env = {
        "CKB_CSHARP_LS_COMMAND": str(csharp_ls.resolve()),
        "CKB_DOTNET_COMMAND": str(dotnet.resolve()),
        "DOTNET_ROOT": str(dotnet.resolve().parent),
        "DOTNET_CLI_HOME": str((root / "dotnet-home").resolve()),
        "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_NOLOGO": "1",
    }
    # The fixture explicitly prepares its own project assets; CKB itself is then
    # exercised without --allow-dotnet-restore.
    if mode == "exact":
        restore = execute([str(dotnet.resolve()), "restore", str(repo / "Demo.csproj"), "--ignore-failed-sources", "--nologo"], env=env)
        if restore.returncode:
            return {"status": "failed", "language": "csharp", "stage": "fixture-restore", "exit_status": restore.returncode, "stdout": restore.stdout, "stderr": restore.stderr}
    git(repo, "init")
    git(repo, "config", "user.email", "provider@example.invalid")
    git(repo, "config", "user.name", "Provider Fixture")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "csharp")
    output = root / f"out-csharp-{mode}"
    init_command = [sys.executable, str(CLI), "init", "--repo", str(repo), "--out", str(output), "--format", "markdown"]
    if mode == "exact":
        init_command.extend(["--csharp-project", "Demo.csproj"])
    init = execute(init_command, env=env)
    if init.returncode:
        return {"status": "failed", "language": "csharp", "stage": "init", "exit_status": init.returncode, "stdout": init.stdout, "stderr": init.stderr}
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    chunk_id = state["chunks"][0]["id"]
    built = execute([sys.executable, str(CLI), "build-chunk", "--out", str(output), "--chunk", chunk_id, "--stage", "all"], env=env)
    if built.returncode:
        return {"status": "failed", "language": "csharp", "stage": "build", "exit_status": built.returncode, "stdout": built.stdout, "stderr": built.stderr}
    candidate = json.loads((output / "chunks" / chunk_id / "candidate.json").read_text(encoding="utf-8"))
    provider = next(item for item in candidate["providers"] if item["language"] == "csharp")
    key_entities = {item["id"] for item in candidate["entities"] if item["language"] == "csharp" and item["kind"] != "file" and item["classification"] == "page"}
    covered = set(provider.get("covered_entity_ids", []))
    expected_precision = "exact" if mode == "exact" else "bounded-approximate"
    passed = provider.get("status") == "passed" and provider.get("precision") == expected_precision and key_entities <= covered and provider.get("document_symbol_counts", {}).get("Service.cs", 0) > 0
    return {"status": "passed" if passed else "failed", "language": "csharp", "case": mode, "provider": provider, "key_entity_count": len(key_entities), "covered_count": len(key_entities & covered), "output": str(output.resolve())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyright", type=Path, required=True)
    parser.add_argument("--typescript-language-server", type=Path, required=True)
    parser.add_argument("--tsserver", type=Path, required=True)
    parser.add_argument("--clangd", type=Path, required=True)
    parser.add_argument("--csharp-ls", type=Path, required=True)
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    required = [args.pyright, args.typescript_language_server, args.tsserver, args.clangd, args.csharp_ls, args.dotnet]
    if any(not path.is_file() for path in required):
        record = {"status": "dependency-missing", "required": [str(path.resolve()) for path in required]}
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 3
    with tempfile.TemporaryDirectory(prefix="ckb-provider-") as value:
        root = Path(value)
        pyright = provider_case(
            root,
            "python",
            "service.py",
            "def public_service(value):\n    return value + 1\n",
            {"CKB_PYRIGHT_LANGSERVER_COMMAND": str(args.pyright.resolve())},
        )
        javascript = provider_case(
            root,
            "javascript",
            "service.js",
            "export function publicService(value) { return value + 1; }\n",
            {
                "CKB_TYPESCRIPT_LANGUAGE_SERVER_COMMAND": str(args.typescript_language_server.resolve()),
                "CKB_TYPESCRIPT_TSSERVER_PATH": str(args.tsserver.resolve()),
            },
        )
        clangd_exact = clangd_case(
            root,
            "c-exact",
            "int public_service(int value) { return value + 1; }\nint main(void) { return public_service(1); }\n",
            args.clangd,
            "exact",
        )
        clangd_bounded = clangd_case(
            root,
            "c-bounded",
            "int public_service(int value) { return value + 1; }\n",
            args.clangd,
            "bounded-approximate",
        )
        clangd_missing_header = clangd_case(
            root,
            "c-missing-header",
            '#include "missing_project_header.h"\nint public_service(void) { return 1; }\n',
            args.clangd,
            "failure",
        )
        scons_build_files = {
            "SConstruct": "env = Environment(CXXFLAGS=['-std=c++20'])\nenv.SConscript('src/SConscript')\n",
            "src/SConscript": "env.Append(CXXFLAGS=['-std=c++20'])\n",
        }
        clangd_cpp_exact = clangd_case(
            root,
            "cpp-exact-with-scons",
            "template <typename T> class Box {};\ntemplate class Box<int>;\nint public_service(int value) { return value + 1; }\n",
            args.clangd,
            "exact",
            language="cpp",
            build_files=scons_build_files,
        )
        clangd_cpp_scons_bounded = clangd_case(
            root,
            "cpp-scons-bounded",
            "#ifndef NDEBUG\ntemplate <typename T> class Box {};\ntemplate class Box<int>;\n#endif\nint public_service(int value) { return value + 1; }\n",
            args.clangd,
            "bounded-approximate",
            language="cpp",
            build_files=scons_build_files,
            expected_fallback_standard="c++20",
        )
        clangd_cpp_missing_header = clangd_case(
            root,
            "cpp-missing-header",
            '#include "missing_project_header.hpp"\nint public_service() { return 1; }\n',
            args.clangd,
            "failure",
            language="cpp",
            build_files=scons_build_files,
        )
        csharp_exact = csharp_case(root, args.csharp_ls, args.dotnet, "exact")
        csharp_bounded = csharp_case(root, args.csharp_ls, args.dotnet, "bounded")
    providers = [
        pyright,
        javascript,
        clangd_exact,
        clangd_bounded,
        clangd_missing_header,
        clangd_cpp_exact,
        clangd_cpp_scons_bounded,
        clangd_cpp_missing_header,
        csharp_exact,
        csharp_bounded,
    ]
    record = {
        "status": "passed" if all(item["status"] == "passed" for item in providers) else "failed",
        "providers": providers,
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record["status"] == "passed" else 5


if __name__ == "__main__":
    raise SystemExit(main())
