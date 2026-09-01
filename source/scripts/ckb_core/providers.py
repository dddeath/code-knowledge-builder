from __future__ import annotations

import json
import importlib.metadata
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, unquote, urlparse

from .common import CkbError, DependencyError, background_process_options, command_version, run, stable_id, utc_now


EXPECTED = {
    "python": ("pyright-langserver", "1.1.413"),
    "javascript": ("typescript-language-server", "6.0.0"),
    "c": ("clangd", "22.1.8"),
    "cpp": ("clangd", "22.1.8"),
    "csharp": ("csharp-ls", "0.26.0"),
    "dotnet": ("dotnet", "10."),
    "logseq": ("logseq", "fab27740975dcda1e93dbca718d1f620eda543c7"),
}


def _version_matches(expected: str, output: str) -> bool:
    lowered = output.lower()
    return expected.lower() in lowered or (len(expected) == 40 and expected[:7].lower() in lowered)


def private_runtime_root() -> Path:
    override = os.environ.get("CKB_RUNTIME_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".codex" / "cache" / "code-knowledge-builder" / "runtime" / "win-x64"


def _runtime_bin_candidates() -> list[Path]:
    root = private_runtime_root()
    if not root.is_dir():
        return []
    result: list[Path] = []
    for lock_dir in sorted(root.iterdir(), reverse=True):
        for rel in ("bin", "node", "python", "llvm/bin", "logseq", "dotnet", "dotnet-tools"):
            path = lock_dir / rel
            if path.is_dir():
                result.append(path)
    return result


def resolve_executable(name: str) -> str | None:
    env_name = "CKB_" + re.sub(r"[^A-Za-z0-9]", "_", name).upper() + "_COMMAND"
    if os.environ.get(env_name):
        return os.environ[env_name]
    names = [name]
    if os.name == "nt":
        names.extend([name + ".cmd", name + ".exe"])
    for directory in _runtime_bin_candidates():
        for candidate in names:
            path = directory / candidate
            if path.is_file():
                return str(path.resolve())
    for candidate in names:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def doctor_report() -> dict[str, Any]:
    tools: dict[str, Any] = {}
    for key, (command, expected) in EXPECTED.items():
        path = resolve_executable(command)
        if not path:
            tools[key] = {"status": "missing", "command": command, "expected": expected}
            continue
        args = ["--version"]
        if command.endswith("langserver"):
            args = ["--version"]
        tool_env = os.environ.copy()
        if key == "csharp":
            dotnet_path = resolve_executable("dotnet")
            if dotnet_path:
                tool_env["DOTNET_ROOT"] = str(Path(dotnet_path).resolve().parent)
                tool_env.update({"DOTNET_NOLOGO": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1"})
        completed = run([path, *args], env=tool_env, timeout=30)
        output = (completed.stdout or completed.stderr).strip().splitlines()
        joined_output = "\n".join(output)
        tools[key] = {
            "status": "ready" if completed.returncode == 0 and _version_matches(expected, joined_output) else ("incompatible" if completed.returncode == 0 else "broken"),
            "command": command,
            "path": path,
            "version": output[0] if output else None,
            "expected": expected,
            "exit_status": completed.returncode,
        }
    python_completed = run([sys.executable, "--version"], timeout=20)
    python_lines = (python_completed.stdout or python_completed.stderr).strip().splitlines()
    python_version = python_lines[0] if python_lines else None
    python_tool = {
        "status": "ready" if python_completed.returncode == 0 and "3.14.6" in (python_version or "") else ("incompatible" if python_completed.returncode == 0 else "broken"),
        "command": "python",
        "path": str(Path(sys.executable).resolve()),
        "version": python_version,
        "expected": "3.14.6",
        "exit_status": python_completed.returncode,
    }
    node_path = resolve_executable("node")
    if node_path:
        node_completed = run([node_path, "--version"], timeout=20)
        node_lines = (node_completed.stdout or node_completed.stderr).strip().splitlines()
        node_version = node_lines[0] if node_lines else None
        node_tool = {
            "status": "ready" if node_completed.returncode == 0 and "24.19.0" in (node_version or "") else ("incompatible" if node_completed.returncode == 0 else "broken"),
            "command": "node",
            "path": str(Path(node_path).resolve()),
            "version": node_version,
            "expected": "24.19.0",
            "exit_status": node_completed.returncode,
        }
    else:
        node_tool = {"status": "missing", "command": "node", "expected": "24.19.0"}
    git_tool = command_version("git")
    tls_command = resolve_executable("typescript-language-server")
    compiler_candidates: list[Path] = []
    explicit_compiler = os.environ.get("CKB_TYPESCRIPT_PACKAGE_JSON")
    if explicit_compiler:
        compiler_candidates.append(Path(explicit_compiler).expanduser())
    if tls_command:
        compiler_candidates.append(Path(tls_command).resolve().parent.parent / "typescript" / "package.json")
    compiler_package = next((path for path in compiler_candidates if path.is_file()), None)
    compiler_version = None
    if compiler_package:
        try:
            compiler_version = json.loads(compiler_package.read_text(encoding="utf-8"))["version"]
        except Exception:
            compiler_version = None
    typescript_tool = {
        "status": "ready" if compiler_version == "7.0.2" else ("incompatible" if compiler_version else "missing"),
        "version": compiler_version,
        "expected": "7.0.2",
        "package_json": str(compiler_package.resolve()) if compiler_package else None,
    }
    explicit_tsserver = os.environ.get("CKB_TYPESCRIPT_TSSERVER_PATH")
    tsserver_candidates: list[Path] = []
    if explicit_tsserver:
        tsserver_candidates.append(Path(explicit_tsserver).expanduser())
    if tls_command:
        command_path = Path(tls_command).resolve()
        tsserver_candidates.extend(
            [
                command_path.parent.parent / "typescript" / "lib" / "tsserver.js",
                command_path.parent / "tsserver" / "node_modules" / "typescript" / "lib" / "tsserver.js",
            ]
        )
    tsserver_path = next((path.resolve() for path in tsserver_candidates if path.is_file()), None)
    tsserver_package = tsserver_path.parent.parent / "package.json" if tsserver_path and tsserver_path.is_file() else None
    tsserver_version = None
    if tsserver_package and tsserver_package.is_file():
        try:
            tsserver_version = json.loads(tsserver_package.read_text(encoding="utf-8"))["version"]
        except Exception:
            tsserver_version = None
    tsserver_tool = {
        "status": "ready" if tsserver_version == "6.0.3" else ("incompatible" if tsserver_version else "missing"),
        "version": tsserver_version,
        "expected": "6.0.3",
        "path": str(tsserver_path) if tsserver_path else None,
    }
    try:
        import tree_sitter

        ts_version = importlib.metadata.version("tree-sitter")
        expected_grammars = {
            "tree_sitter_c": ("tree-sitter-c", "0.24.2"),
            "tree_sitter_cpp": ("tree-sitter-cpp", "0.23.4"),
            "tree_sitter_javascript": ("tree-sitter-javascript", "0.25.0"),
            "tree_sitter_python": ("tree-sitter-python", "0.25.0"),
            "tree_sitter_c_sharp": ("tree-sitter-c-sharp", "0.23.5"),
        }
        grammars = {}
        for module, (distribution, expected_version) in expected_grammars.items():
            try:
                __import__(module)
                actual_version = importlib.metadata.version(distribution)
                grammars[module] = {"status": "ready" if actual_version == expected_version else "incompatible", "version": actual_version, "expected": expected_version}
            except Exception as exc:
                grammars[module] = {"status": "missing", "detail": str(exc), "expected": expected_version}
        tree_sitter_status = {
            "status": "ready" if ts_version == "0.26.0" and all(v["status"] == "ready" for v in grammars.values()) else "incompatible",
            "version": ts_version,
            "expected": "0.26.0",
            "grammars": grammars,
        }
    except Exception as exc:
        tree_sitter_status = {"status": "missing", "detail": str(exc)}
    try:
        from .graphify_core import GRAPHIFY_COMMIT, GRAPHIFY_VERSION, _networkx_modules

        nx, cluster, _labels, _scores = _networkx_modules()
        graphify_probe = nx.Graph()
        graphify_probe.add_edges_from([("source", "entity"), ("entity", "target")])
        graphify_partition = cluster(graphify_probe)
        graphify_status = {
            "status": "ready" if sorted(node for members in graphify_partition.values() for node in members) == ["entity", "source", "target"] else "incompatible",
            "version": GRAPHIFY_VERSION,
            "source_commit": GRAPHIFY_COMMIT,
            "networkx_version": nx.__version__,
            "mode": "vendored-community-projection",
        }
    except Exception as exc:
        graphify_status = {"status": "missing", "detail": str(exc)}
    try:
        probe = sqlite3.connect(":memory:")
        probe.execute("CREATE VIRTUAL TABLE fts_probe USING fts5(value, tokenize='trigram')")
        probe.execute("INSERT INTO fts_probe(value) VALUES('代码知识索引')")
        matched = probe.execute("SELECT count(*) FROM fts_probe WHERE fts_probe MATCH '代码知'").fetchone()[0]
        probe.close()
        agent_index_status = {
            "status": "ready" if matched == 1 else "incompatible",
            "sqlite_version": sqlite3.sqlite_version,
            "features": ["fts5", "trigram"],
        }
    except Exception as exc:
        agent_index_status = {"status": "missing", "detail": str(exc), "features": ["fts5", "trigram"]}
    tools.update({"python": python_tool, "node": node_tool, "git": git_tool, "tree_sitter": tree_sitter_status, "typescript": typescript_tool, "typescript_tsserver": tsserver_tool, "graphify_core": graphify_status, "agent_index": agent_index_status})
    required_scan = ["git", "tree_sitter", "python", "node", "javascript", "typescript", "typescript_tsserver", "c", "cpp", "csharp", "dotnet", "logseq", "graphify_core", "agent_index"]
    return {
        "schema_version": 2,
        "checked_at_utc": utc_now(),
        "status": "ready" if all(tools[name]["status"] == "ready" for name in required_scan) else "missing",
        "tools": tools,
        "private_runtime_root": str(private_runtime_root()),
    }


def path_to_uri(path: Path) -> str:
    value = path.resolve().as_posix()
    if os.name == "nt":
        return "file:///" + quote(value, safe="/:@")
    return "file://" + quote(value, safe="/:@")


def uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    value = unquote(parsed.path)
    if os.name == "nt" and value.startswith("/") and len(value) > 2 and value[2] == ":":
        value = value[1:]
    return Path(value).resolve()


class LspClient:
    def __init__(self, command: list[str], cwd: Path, env: dict[str, str] | None = None):
        self.command = command
        self.cwd = cwd
        self.env = env
        self.process: subprocess.Popen[bytes] | None = None
        self._id = 0
        self._messages: "queue.Queue[dict[str, Any]]" = queue.Queue()
        self._pending: dict[int, dict[str, Any]] = {}
        self.transcript: list[dict[str, Any]] = []
        self.stderr: list[str] = []

    def start(self) -> None:
        self.process = subprocess.Popen(
            self.command,
            cwd=str(self.cwd),
            env=self.env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **background_process_options(),
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.process and self.process.stdout
        stream = self.process.stdout
        while True:
            headers: dict[str, str] = {}
            while True:
                line = stream.readline()
                if not line:
                    return
                if line in (b"\r\n", b"\n"):
                    break
                key, value = line.decode("ascii", errors="replace").split(":", 1)
                headers[key.lower()] = value.strip()
            length = int(headers.get("content-length", "0"))
            body = stream.read(length)
            if not body:
                return
            message = json.loads(body.decode("utf-8"))
            self.transcript.append({"direction": "in", "message": message})
            self._messages.put(message)

    def _read_stderr(self) -> None:
        assert self.process and self.process.stderr
        for line in iter(self.process.stderr.readline, b""):
            self.stderr.append(line.decode("utf-8", errors="replace").rstrip())

    def send(self, message: dict[str, Any]) -> None:
        assert self.process and self.process.stdin
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.transcript.append({"direction": "out", "message": message})
        self.process.stdin.write(header + body)
        self.process.stdin.flush()

    def notify(self, method: str, params: Any) -> None:
        self.send({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method: str, params: Any, timeout: int = 60) -> Any:
        self._id += 1
        request_id = self._id
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if request_id in self._pending:
                message = self._pending.pop(request_id)
            else:
                try:
                    message = self._messages.get(timeout=min(0.5, max(0.01, deadline - time.monotonic())))
                except queue.Empty:
                    continue
            if message.get("method") and "id" in message:
                server_method = message.get("method")
                if server_method == "workspace/configuration":
                    items = (message.get("params") or {}).get("items") or []
                    server_result: Any = [{} for _ in items]
                elif server_method in {"client/registerCapability", "client/unregisterCapability", "window/workDoneProgress/create"}:
                    server_result = None
                else:
                    server_result = None
                self.send({"jsonrpc": "2.0", "id": message["id"], "result": server_result})
                continue
            if message.get("id") == request_id:
                if "error" in message:
                    raise CkbError(f"LSP {method} failed: {message['error']}")
                return message.get("result")
            if "id" in message:
                self._pending[int(message["id"])] = message
        raise CkbError(f"LSP request timed out: {method}")

    def stop(self) -> int | None:
        if not self.process:
            return None
        try:
            self.request("shutdown", None, timeout=10)
            self.notify("exit", None)
        except Exception:
            pass
        try:
            return self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
        try:
            return self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            return self.process.wait(timeout=5)


def _provider_spec(language: str, repo: Path, options: dict[str, Any] | None = None) -> tuple[list[str], str, dict[str, Any], str, Path, dict[str, str]]:
    environment = os.environ.copy()
    if language == "python":
        command = resolve_executable("pyright-langserver")
        if not command:
            raise DependencyError("pyright-langserver is required for Python semantic evidence")
        return [command, "--stdio"], "python", {}, "exact", repo, environment
    if language == "javascript":
        command = resolve_executable("typescript-language-server")
        if not command:
            raise DependencyError("typescript-language-server is required for JavaScript semantic evidence")
        command_path = Path(command).resolve()
        node_modules = command_path.parent.parent
        explicit_tsserver = os.environ.get("CKB_TYPESCRIPT_TSSERVER_PATH")
        candidates = [
            Path(explicit_tsserver).expanduser() if explicit_tsserver else None,
            node_modules / "typescript" / "lib" / "tsserver.js",
            command_path.parent / "tsserver" / "node_modules" / "typescript" / "lib" / "tsserver.js",
        ]
        tsserver_path = next((item.resolve() for item in candidates if item and item.is_file()), None)
        initialization = {"tsserver": {"path": str(tsserver_path)}} if tsserver_path else {}
        return [command, "--stdio"], "javascript", initialization, "exact", repo, environment
    if language == "csharp":
        command = resolve_executable("csharp-ls")
        dotnet = resolve_executable("dotnet")
        if not command or not dotnet:
            raise DependencyError("csharp-ls 0.26.0 and .NET 10 SDK are required for C# semantic evidence")
        workspace = (options or {}).get("csharp_workspace") or {}
        workspace_root = Path(workspace.get("workspace_root") or repo).resolve()
        kind = workspace.get("kind", "folder")
        selected = workspace.get("path")
        server_cwd = workspace_root
        command_line = [command, "--loglevel", "warning", "--locale", "en-US"]
        if kind == "solution" and selected:
            command_line.extend(["--solution", selected])
        elif kind in {"project", "fallback-project"} and selected:
            server_cwd = (workspace_root / Path(*PurePosixPath(selected).parent.parts)).resolve()
        dotnet_path = Path(dotnet).resolve()
        if dotnet_path.parent.name.lower() == "dotnet" or (dotnet_path.parent / "host").is_dir():
            environment["DOTNET_ROOT"] = str(dotnet_path.parent)
        restore = workspace.get("restore") or {}
        if restore.get("performed"):
            runtime_root = workspace_root.parent
            environment["NUGET_PACKAGES"] = str((runtime_root / "nuget-packages").resolve())
            environment["DOTNET_CLI_HOME"] = str((runtime_root / "dotnet-home").resolve())
        environment.update({"DOTNET_NOLOGO": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_CLI_UI_LANGUAGE": "en-US"})
        initialization = {"workspace": workspace, "restoreAllowed": bool(restore.get("requested")), "networkRestorePerformed": bool(restore.get("network_restore"))}
        return command_line, "csharp", initialization, workspace.get("precision", "bounded-approximate"), server_cwd, environment
    command = resolve_executable("clangd")
    if not command:
        raise DependencyError("clangd is required for C/C++ semantic evidence")
    compile_db = None
    for candidate in (repo / "compile_commands.json", repo / "build" / "compile_commands.json"):
        if candidate.is_file():
            compile_db = candidate.parent
            break
    if compile_db:
        return [command, f"--compile-commands-dir={compile_db}", "--log=verbose"], "c" if language == "c" else "cpp", {"compilationDatabasePath": str(compile_db)}, "exact", repo, environment
    flags, evidence = _fallback_flags(repo, language)
    return [command, "--log=verbose"], "c" if language == "c" else "cpp", {"fallbackFlags": flags, "fallbackEvidence": evidence}, "bounded-approximate", repo, environment


def _fallback_flags(repo: Path, language: str) -> tuple[list[str], dict[str, Any]]:
    """Resolve a unique language standard from build files or use the bounded default."""
    candidates: set[str] = set()
    evidence: list[dict[str, str]] = []
    patterns = (
        ((r"CXX_STANDARD\s+([0-9]+)", r"cxx_std_([0-9]+)", r"-std=c\+\+([0-9]+)"), "c++")
        if language == "cpp"
        else ((r"(?<!X)C_STANDARD\s+([0-9]+)", r"c_std_([0-9]+)", r"-std=c([0-9]+)"), "c")
    )
    regexes, prefix = patterns
    build_names = {"CMakeLists.txt", "meson.build", "Makefile", "makefile", "SConstruct", "SConscript"}
    paths = [path for path in repo.rglob("*") if path.is_file() and (path.name in build_names or path.suffix.lower() in {".cmake", ".vcxproj", ".mk"})]
    for path in sorted(paths)[:500]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in regexes:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = match.group(1)
                standard = f"{prefix}{value}"
                candidates.add(standard)
                evidence.append({"path": path.relative_to(repo).as_posix(), "match": match.group(0), "standard": standard})
    default_standard = "c17" if language == "c" else "c++17"
    selected = next(iter(candidates)) if len(candidates) == 1 else default_standard
    resolution = "build-config-unique" if len(candidates) == 1 else ("fallback-no-evidence" if not candidates else "fallback-ambiguous-evidence")
    flags = ["-x", "c" if language == "c" else "c++", f"-std={selected}"]
    return flags, {"resolution": resolution, "candidates": sorted(candidates), "matches": evidence, "selected": selected}


def _flatten_symbols(values: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(values, list):
        return result
    for item in values:
        if not isinstance(item, dict):
            continue
        result.append(item)
        result.extend(_flatten_symbols(item.get("children")))
    return result


def _provider_status(
    fatal_diagnostics: list[dict[str, Any]],
    fatal_stderr: list[str],
) -> str:
    """Classify a completed LSP run without rejecting valid empty documents.

    ``textDocument/documentSymbol`` returning an empty list is a successful LSP
    response for modules that contain only imports or executable statements.
    Request failures already raise from ``LspClient.request``.  Key-page
    definition coverage is checked independently by the semantic audit gate.
    """
    return "failed" if fatal_diagnostics or fatal_stderr else "passed"


def collect_semantics(
    repo: Path,
    language: str,
    files: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if os.environ.get("CKB_TEST_PROVIDER") == "deterministic-fixture":
        covered = [e["id"] for e in entities if e["kind"] != "file" and e["language"] == language]
        return {
            "provider": {"name": "deterministic-fixture", "language": language, "status": "passed", "precision": "test-only", "covered_entity_ids": covered},
            "links": [],
            "diagnostics": [],
            "transcript": [],
            "stderr": [],
        }
    command, language_id, initialization, precision, server_cwd, environment = _provider_spec(language, repo, options)
    document_root = Path(((options or {}).get("csharp_workspace") or {}).get("workspace_root") or repo).resolve() if language == "csharp" else repo
    client = LspClient(command, server_cwd, environment)
    client.start()
    result_payload: dict[str, Any] | None = None
    diagnostics: list[dict[str, Any]] = []
    symbol_counts: dict[str, int] = {}
    covered: set[str] = set()
    semantic_links: list[dict[str, Any]] = []
    entity_by_position: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for entity in entities:
        entity_by_position.setdefault((entity["path"], entity["range"].get("name_line", entity["range"]["start_line"]) - 1), []).append(entity)
    try:
        result = client.request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": path_to_uri(document_root),
                "workspaceFolders": [{"uri": path_to_uri(document_root), "name": document_root.name}],
                "capabilities": {"workspace": {"configuration": True}, "textDocument": {"documentSymbol": {"hierarchicalDocumentSymbolSupport": True}}},
                "initializationOptions": initialization,
            },
            timeout=90,
        )
        client.notify("initialized", {})
        for file_entry in files:
            path = (document_root / file_entry["path"]).resolve()
            uri = path_to_uri(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            client.notify(
                "textDocument/didOpen",
                {"textDocument": {"uri": uri, "languageId": language_id, "version": 1, "text": text}},
            )
            symbols = client.request("textDocument/documentSymbol", {"textDocument": {"uri": uri}}, timeout=90)
            flat = _flatten_symbols(symbols)
            symbol_counts[file_entry["path"]] = len(flat)
            for item in flat:
                selection = item.get("selectionRange") or item.get("range") or {}
                start = selection.get("start") or {}
                for entity in entity_by_position.get((file_entry["path"], int(start.get("line", -1))), []):
                    if entity["name"] == item.get("name") or entity["name"] in str(item.get("name", "")):
                        covered.add(entity["id"])
            for entity in [e for e in entities if e["path"] == file_entry["path"] and e["kind"] != "file" and e["candidate_classification"] == "page"]:
                position = {"line": entity["range"].get("name_line", entity["range"]["start_line"]) - 1, "character": entity["range"].get("name_column_utf8", 0)}
                try:
                    definitions = client.request("textDocument/definition", {"textDocument": {"uri": uri}, "position": position}, timeout=30)
                    references = client.request("textDocument/references", {"textDocument": {"uri": uri}, "position": position, "context": {"includeDeclaration": False}}, timeout=30)
                except CkbError:
                    definitions, references = [], []
                if definitions:
                    covered.add(entity["id"])
                for location in references or []:
                    target_uri = location.get("uri") or (location.get("targetUri") if isinstance(location, dict) else None)
                    target_range = location.get("range") or location.get("targetSelectionRange") or {}
                    if not target_uri:
                        continue
                    try:
                        rel = uri_to_path(target_uri).relative_to(document_root).as_posix()
                    except ValueError:
                        continue
                    line = int((target_range.get("start") or {}).get("line", -1))
                    for source_entity in entity_by_position.get((rel, line), []):
                        if source_entity["id"] == entity["id"]:
                            continue
                        semantic_links.append({
                            "id": stable_id("link", source_entity["id"], entity["id"], "references", language),
                            "type": "references",
                            "source": source_entity["id"],
                            "target": entity["id"],
                            "provider": command[0],
                            "evidence": {"uri": target_uri, "line": line, "queried_entity": entity["id"]},
                        })
        time.sleep(0.2)
        for event in client.transcript:
            message = event.get("message", {})
            if event.get("direction") == "in" and message.get("method") == "textDocument/publishDiagnostics":
                params = message.get("params", {})
                diagnostics.extend(params.get("diagnostics", []))
        fatal_patterns = (
            "invalid ast",
            "file not found",
            "could not build compilerinvocation",
            "pp_file_not_found",
            "failed to create target",
            "could not be loaded",
            "project file does not exist",
            "assets file",
            "failed to load project",
            "failed to load solution",
        )
        fatal = [d for d in diagnostics if any(p in str(d.get("message", "")).lower() for p in fatal_patterns)]
        fatal_stderr = [line for line in client.stderr if any(pattern in line.lower() for pattern in fatal_patterns)]
        provider = {
            "name": Path(command[0]).name,
            "language": language,
            "command": command,
            "initialization_options": initialization,
            "server_cwd": str(server_cwd),
            "document_root": str(document_root),
            "precision": precision,
            "status": _provider_status(fatal, fatal_stderr),
            "covered_entity_ids": sorted(covered),
            "document_symbol_counts": symbol_counts,
            "diagnostic_count": len(diagnostics),
            "fatal_diagnostics": fatal,
            "fatal_stderr": fatal_stderr,
            "capabilities": result.get("capabilities", {}) if isinstance(result, dict) else {},
        }
        result_payload = {"provider": provider, "links": semantic_links, "diagnostics": diagnostics, "transcript": client.transcript, "stderr": client.stderr}
        return result_payload
    finally:
        exit_status = client.stop()
        if result_payload is not None:
            result_payload["provider"]["exit_status"] = exit_status
