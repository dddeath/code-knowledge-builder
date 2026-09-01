"""Session-owned supervisor for the local CKB JSONL stdio server.

The short-lived Harness adapters never pretend to own a session process.  A
real CKB request starts one supervisor for a bounded lifecycle key; that
supervisor owns the stdio child, its pipes and reader threads until an explicit
session close or a reliable Harness parent PID disappears.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from typing import Any, TextIO
import uuid

from .common import CkbError, background_process_options, json_load, json_write, utc_now
from .stdio_server import STDIO_RETRIEVAL_PROTOCOL, STDIO_RETRIEVAL_PROTOCOL_VERSION


SESSION_STDIO_SCHEMA_VERSION = 1
DEFAULT_START_TIMEOUT_SECONDS = 15.0
DEFAULT_REQUEST_TIMEOUT_SECONDS = 45.0
DEFAULT_CLOSE_TIMEOUT_SECONDS = 8.0
POLL_SECONDS = 0.025
_FORBIDDEN_STATE_KEYS = {
    "prompt",
    "assistant",
    "assistant_message",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
    "transcript",
    "tool_input",
}


class _StartGate:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.users = 0


_START_GATES_GUARD = threading.Lock()
_START_GATES: dict[str, _StartGate] = {}


def _retain_start_gate(key: str) -> _StartGate:
    with _START_GATES_GUARD:
        gate = _START_GATES.get(key)
        if gate is None:
            gate = _StartGate()
            _START_GATES[key] = gate
        gate.users += 1
        return gate


def _release_start_gate(key: str, gate: _StartGate) -> None:
    with _START_GATES_GUARD:
        gate.users -= 1
        if gate.users == 0 and _START_GATES.get(key) is gate:
            _START_GATES.pop(key, None)


def default_session_stdio_root() -> Path:
    configured = os.environ.get("CKB_SESSION_STDIO_ROOT")
    return (Path(configured).expanduser() if configured else Path.home() / ".ckb" / "session-stdio").resolve()


def _path_identity(path: Path | str) -> str:
    value = str(Path(path).expanduser().resolve()).replace("\\", "/").rstrip("/")
    return value.casefold() if os.name == "nt" else value


def _digest(*values: object) -> str:
    text = "\0".join(str(value) for value in values)
    return hashlib.sha256(text.encode("utf-8", errors="strict")).hexdigest()


def session_digest(session_id: str) -> str:
    value = session_id.strip()
    if not value:
        raise CkbError("session stdio requires a non-empty session id")
    return _digest("session", value)


def lifecycle_key(
    harness: str,
    session_id: str,
    output: Path,
    *,
    executable: Path | None = None,
    ckb: Path | None = None,
) -> str:
    python_value = executable or Path(sys.executable)
    ckb_value = ckb or Path(__file__).resolve().parents[1] / "ckb.py"
    identity = _digest(
        _path_identity(python_value),
        _path_identity(ckb_value),
        STDIO_RETRIEVAL_PROTOCOL,
        STDIO_RETRIEVAL_PROTOCOL_VERSION,
    )
    return "stdio-" + _digest(harness.strip().casefold(), session_digest(session_id), _path_identity(output), identity)


def _lifecycle_directory(root: Path, key: str) -> Path:
    return root.resolve() / key


def _lease_path(directory: Path) -> Path:
    return directory / "lease.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json_load(path)
        return value if isinstance(value, dict) else None
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _write_lease(directory: Path, value: dict[str, Any], timeout: float = 3.0) -> None:
    """Replace lease state despite short Windows reader sharing conflicts."""

    path = _lease_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                os.replace(temporary, path)
                return
            except OSError as exc:
                sharing_conflict = os.name == "nt" and getattr(exc, "winerror", None) in {5, 32}
                if not sharing_conflict or time.monotonic() >= deadline:
                    raise
                time.sleep(POLL_SECONDS)
    finally:
        temporary.unlink(missing_ok=True)


def pid_exists(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            handle = ctypes.windll.kernel32.OpenProcess(0x00100000 | 0x1000, False, pid)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return False
                return int(exit_code.value) == 259  # STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _force_terminate_pid(pid: int) -> bool:
    if not pid_exists(pid):
        return True
    if os.name == "nt":
        try:
            import ctypes

            process = ctypes.windll.kernel32.OpenProcess(0x0001 | 0x00100000, False, pid)
            if not process:
                return not pid_exists(pid)
            try:
                ctypes.windll.kernel32.TerminateProcess(process, 143)
                ctypes.windll.kernel32.WaitForSingleObject(process, 3000)
            finally:
                ctypes.windll.kernel32.CloseHandle(process)
            return not pid_exists(pid)
        except Exception:
            return False
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    deadline = time.monotonic() + 2.0
    while pid_exists(pid) and time.monotonic() < deadline:
        time.sleep(POLL_SECONDS)
    if pid_exists(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return not pid_exists(pid)


def process_metrics(pid: int | None = None) -> dict[str, Any]:
    """Return RSS and handle counts using only the locked runtime's stdlib."""

    process_id = int(pid or os.getpid())
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, process_id)
        if not handle:
            raise CkbError(f"session stdio metrics cannot open process: pid={process_id}")
        try:
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                raise CkbError(f"session stdio RSS metric is unavailable: pid={process_id}")
            count = wintypes.DWORD()
            if not ctypes.windll.kernel32.GetProcessHandleCount(handle, ctypes.byref(count)):
                raise CkbError(f"session stdio handle metric is unavailable: pid={process_id}")
            return {
                "pid": process_id,
                "rss_bytes": int(counters.WorkingSetSize),
                "handles": int(count.value),
                "source": "windows-kernel32-psapi",
            }
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    status = Path(f"/proc/{process_id}/status")
    handles = Path(f"/proc/{process_id}/fd")
    if not status.is_file() or not handles.is_dir():
        raise CkbError(f"session stdio process metrics are unavailable: pid={process_id}")
    rss_line = next((line for line in status.read_text(encoding="utf-8").splitlines() if line.startswith("VmRSS:")), None)
    if rss_line is None:
        raise CkbError(f"session stdio RSS metric is unavailable: pid={process_id}")
    rss_bytes = int(rss_line.split()[1]) * 1024
    return {"pid": process_id, "rss_bytes": rss_bytes, "handles": len(list(handles.iterdir())), "source": "procfs"}


def _state_counts(
    *,
    lease: int,
    process: int,
    pending: int,
    readers: int,
    pipes: int,
) -> dict[str, int]:
    return {
        "active_leases": lease,
        "processes": process,
        "pending_requests": pending,
        "reader_threads": readers,
        "timers": 0,
        "listeners": 0,
        "pipes": pipes,
        "session_mappings": lease,
        "cache_references": lease,
    }


def _base_lease(
    *,
    key: str,
    harness: str,
    opaque_session: str,
    output: Path,
    executable: Path,
    ckb: Path,
    parent_pid: int | None,
) -> dict[str, Any]:
    stamp = utc_now()
    return {
        "schema_version": SESSION_STDIO_SCHEMA_VERSION,
        "lifecycle_key": key,
        "harness": harness.strip().casefold(),
        "session_digest": opaque_session,
        "output": str(output.resolve()),
        "state": "starting",
        "supervisor_pid": os.getpid(),
        "server_pid": None,
        "protocol": STDIO_RETRIEVAL_PROTOCOL,
        "protocol_version": STDIO_RETRIEVAL_PROTOCOL_VERSION,
        "executable_identity": _digest(_path_identity(executable), _path_identity(ckb)),
        "parent_pid": parent_pid,
        "parent_monitor": "pid" if parent_pid else "unavailable",
        "created_at_utc": stamp,
        "last_used_at_utc": stamp,
        "closed_at_utc": None,
        "fallback": {"active": False, "reason": None},
        "close_reason": None,
        "object_counts": _state_counts(lease=1, process=0, pending=0, readers=0, pipes=0),
    }


class _Reader(threading.Thread):
    def __init__(self, stream: TextIO, destination: queue.Queue[str] | list[str], name: str) -> None:
        super().__init__(name=name, daemon=False)
        self.stream = stream
        self.destination = destination

    def run(self) -> None:
        try:
            for line in self.stream:
                if isinstance(self.destination, queue.Queue):
                    self.destination.put(line)
                elif len(self.destination) < 200:
                    self.destination.append(line.rstrip("\r\n")[:2000])
        finally:
            if isinstance(self.destination, queue.Queue):
                self.destination.put("")


@dataclass
class _Transport:
    executable: Path
    ckb: Path
    output: Path
    process: subprocess.Popen[str] | None = None
    stdout_queue: queue.Queue[str] | None = None
    stdout_reader: _Reader | None = None
    stderr_reader: _Reader | None = None
    stderr_lines: list[str] | None = None
    pending: int = 0

    def start(self, timeout: float) -> dict[str, Any]:
        command = [str(self.executable), "-X", "utf8", str(self.ckb), "serve", "--stdio", "--out", str(self.output)]
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            bufsize=1,
            **background_process_options(),
        )
        assert self.process.stdout is not None and self.process.stderr is not None
        self.stdout_queue = queue.Queue()
        self.stderr_lines = []
        self.stdout_reader = _Reader(self.process.stdout, self.stdout_queue, "ckb-stdio-stdout")
        self.stderr_reader = _Reader(self.process.stderr, self.stderr_lines, "ckb-stdio-stderr")
        self.stdout_reader.start()
        self.stderr_reader.start()
        response = self.request({"id": "handshake", "method": "ping"}, timeout)
        result = response.get("result") if response.get("ok") else None
        if not isinstance(result, dict):
            raise CkbError("session stdio handshake did not return a result")
        if result.get("protocol") != STDIO_RETRIEVAL_PROTOCOL:
            raise CkbError("session stdio handshake protocol mismatch")
        if result.get("protocol_version") != STDIO_RETRIEVAL_PROTOCOL_VERSION:
            raise CkbError("session stdio handshake protocol version mismatch")
        if _path_identity(result.get("output", "")) != _path_identity(self.output):
            raise CkbError("session stdio handshake output mismatch")
        return response

    def request(self, request: dict[str, Any], timeout: float) -> dict[str, Any]:
        if self.process is None or self.process.poll() is not None:
            raise CkbError("session stdio child is not running")
        if self.process.stdin is None or self.stdout_queue is None:
            raise CkbError("session stdio child pipes are unavailable")
        self.pending += 1
        try:
            self.process.stdin.write(json.dumps(request, ensure_ascii=True, separators=(",", ":")) + "\n")
            self.process.stdin.flush()
            deadline = time.monotonic() + timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CkbError("session stdio response timeout")
                try:
                    line = self.stdout_queue.get(timeout=min(remaining, 0.1))
                except queue.Empty:
                    if self.process.poll() is not None:
                        raise CkbError("session stdio stdout closed before a response")
                    continue
                if not line:
                    raise CkbError("session stdio stdout reached EOF")
                try:
                    response = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CkbError("session stdio returned invalid JSON") from exc
                if not isinstance(response, dict) or response.get("id") != request.get("id"):
                    raise CkbError("session stdio response id mismatch")
                return response
        finally:
            self.pending -= 1

    def close(self, timeout: float) -> dict[str, Any]:
        process = self.process
        escalation = "already-exited"
        if process is not None and process.poll() is None:
            try:
                response = self.request({"id": "shutdown", "method": "shutdown"}, min(timeout, 2.0))
                escalation = "shutdown" if response.get("ok") else "shutdown-error"
            except Exception:
                escalation = "shutdown-error"
            try:
                process.wait(timeout=max(0.2, timeout / 2))
            except subprocess.TimeoutExpired:
                process.terminate()
                escalation = "terminate"
                try:
                    process.wait(timeout=max(0.2, timeout / 3))
                except subprocess.TimeoutExpired:
                    process.kill()
                    escalation = "kill"
                    process.wait(timeout=max(0.2, timeout / 3))
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        for reader in (self.stdout_reader, self.stderr_reader):
            if reader is not None:
                reader.join(timeout=2.0)
        exit_code = process.returncode if process is not None else None
        pid = process.pid if process is not None else None
        stderr = list(self.stderr_lines or [])[-20:]
        self.process = None
        self.stdout_queue = None
        self.stdout_reader = None
        self.stderr_reader = None
        self.stderr_lines = None
        self.pending = 0
        return {"escalation": escalation, "server_pid": pid, "exit_code": exit_code, "stderr": stderr}


def _write_response(directory: Path, token: str, value: dict[str, Any]) -> None:
    json_write(directory / "responses" / f"{token}.json", value)


def _clear_transient(directory: Path) -> None:
    for name in ("requests", "responses", "control"):
        current = directory / name
        if not current.is_dir():
            continue
        for path in current.iterdir():
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            except OSError:
                pass


def controller_main(
    *,
    root: Path,
    key: str,
    harness: str,
    opaque_session: str,
    output: Path,
    executable: Path,
    ckb: Path,
    parent_pid: int | None,
    start_timeout: float = DEFAULT_START_TIMEOUT_SECONDS,
    close_timeout: float = DEFAULT_CLOSE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    directory = _lifecycle_directory(root, key)
    for name in ("requests", "responses", "control"):
        (directory / name).mkdir(parents=True, exist_ok=True)
    lease = _base_lease(
        key=key,
        harness=harness,
        opaque_session=opaque_session,
        output=output,
        executable=executable,
        ckb=ckb,
        parent_pid=parent_pid,
    )
    _write_lease(directory, lease)
    transport = _Transport(executable=executable, ckb=ckb, output=output)
    close_reason = "controller-stop"
    restart_budget = 1
    try:
        try:
            transport.start(start_timeout)
        except Exception as exc:
            close_info = transport.close(close_timeout)
            lease.update(
                {
                    "state": "fallback",
                    "fallback": {"active": True, "reason": f"startup:{type(exc).__name__}:{str(exc)[:300]}"},
                    "server_pid": None,
                    "object_counts": _state_counts(lease=1, process=0, pending=0, readers=0, pipes=0),
                    "close_detail": close_info,
                    "last_used_at_utc": utc_now(),
                }
            )
            _write_lease(directory, lease)
            return lease
        assert transport.process is not None
        lease.update(
            {
                "state": "ready",
                "server_pid": transport.process.pid,
                "object_counts": _state_counts(lease=1, process=1, pending=0, readers=2, pipes=3),
                "last_used_at_utc": utc_now(),
            }
        )
        _write_lease(directory, lease)
        while True:
            if parent_pid and not pid_exists(parent_pid):
                close_reason = "parent-death"
                break
            controls = sorted((directory / "control").glob("close-*.json"))
            if controls:
                control = _read_json(controls[0]) or {}
                close_reason = str(control.get("reason") or "explicit-close")[:120]
                break
            request_paths = sorted((directory / "requests").glob("*.json"))
            if not request_paths:
                time.sleep(POLL_SECONDS)
                continue
            request_path = request_paths[0]
            envelope = _read_json(request_path)
            if envelope is None:
                try:
                    request_path.unlink()
                except OSError:
                    pass
                continue
            token = str(envelope.get("request_token") or request_path.stem)
            request = envelope.get("request")
            if not isinstance(request, dict):
                _write_response(directory, token, {"status": "failed", "reason": "invalid-request-envelope"})
                request_path.unlink(missing_ok=True)
                continue
            lease["object_counts"] = _state_counts(lease=1, process=1, pending=1, readers=2, pipes=3)
            lease["last_used_at_utc"] = utc_now()
            _write_lease(directory, lease)
            response_value: dict[str, Any]
            try:
                response = transport.request(request, float(envelope.get("timeout_seconds") or DEFAULT_REQUEST_TIMEOUT_SECONDS))
                response_value = {
                    "schema_version": SESSION_STDIO_SCHEMA_VERSION,
                    "status": "passed" if response.get("ok") else "failed",
                    "mode": "resident-stdio",
                    "resident": True,
                    "lifecycle_key": key,
                    "supervisor_pid": os.getpid(),
                    "server_pid": transport.process.pid if transport.process else None,
                    "response": response,
                    "fallback": {"active": False, "reason": None},
                }
            except Exception as first_exc:
                response_value = {}
                if restart_budget > 0:
                    restart_budget -= 1
                    transport.close(close_timeout)
                    try:
                        transport.start(start_timeout)
                        assert transport.process is not None
                        lease["server_pid"] = transport.process.pid
                        response = transport.request(request, float(envelope.get("timeout_seconds") or DEFAULT_REQUEST_TIMEOUT_SECONDS))
                        response_value = {
                            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
                            "status": "passed" if response.get("ok") else "failed",
                            "mode": "resident-stdio",
                            "resident": True,
                            "lifecycle_key": key,
                            "supervisor_pid": os.getpid(),
                            "server_pid": transport.process.pid,
                            "response": response,
                            "fallback": {"active": False, "reason": None},
                            "restart_count": 1,
                        }
                    except Exception as second_exc:
                        response_value = {
                            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
                            "status": "transport-failed",
                            "mode": "cli-fallback-required",
                            "resident": False,
                            "lifecycle_key": key,
                            "supervisor_pid": os.getpid(),
                            "server_pid": None,
                            "fallback": {
                                "active": True,
                                "reason": f"request:{type(first_exc).__name__}:{str(first_exc)[:160]}; restart:{type(second_exc).__name__}:{str(second_exc)[:160]}",
                            },
                        }
                if not response_value:
                    response_value = {
                        "schema_version": SESSION_STDIO_SCHEMA_VERSION,
                        "status": "transport-failed",
                        "mode": "cli-fallback-required",
                        "resident": False,
                        "lifecycle_key": key,
                        "supervisor_pid": os.getpid(),
                        "server_pid": None,
                        "fallback": {"active": True, "reason": f"request:{type(first_exc).__name__}:{str(first_exc)[:300]}"},
                    }
            _write_response(directory, token, response_value)
            request_path.unlink(missing_ok=True)
            if response_value.get("status") == "transport-failed":
                lease["fallback"] = response_value["fallback"]
                close_reason = "transport-failed"
                break
            lease["object_counts"] = _state_counts(lease=1, process=1, pending=0, readers=2, pipes=3)
            lease["last_used_at_utc"] = utc_now()
            _write_lease(directory, lease)
    finally:
        lease["state"] = "closing"
        lease["close_reason"] = close_reason
        lease["object_counts"] = _state_counts(
            lease=1,
            process=1 if transport.process and transport.process.poll() is None else 0,
            pending=transport.pending,
            readers=sum(reader is not None for reader in (transport.stdout_reader, transport.stderr_reader)),
            pipes=3 if transport.process else 0,
        )
        _write_lease(directory, lease)
        close_detail = transport.close(close_timeout)
        lease.update(
            {
                "state": "closed",
                "server_pid": None,
                # Retain the supervisor PID until another process observes
                # that it has really exited; cleanup then clears the reference.
                "supervisor_pid": os.getpid(),
                "closed_at_utc": utc_now(),
                "last_used_at_utc": utc_now(),
                "close_detail": close_detail,
                "object_counts": _state_counts(lease=0, process=0, pending=0, readers=0, pipes=0),
            }
        )
        _write_lease(directory, lease)
        for path in (directory / "requests").glob("*.json"):
            envelope = _read_json(path) or {}
            token = str(envelope.get("request_token") or path.stem)
            _write_response(
                directory,
                token,
                {
                    "schema_version": SESSION_STDIO_SCHEMA_VERSION,
                    "status": "transport-failed",
                    "mode": "cli-fallback-required",
                    "resident": False,
                    "lifecycle_key": key,
                    "fallback": {"active": True, "reason": f"closed:{close_reason}"},
                },
            )
            path.unlink(missing_ok=True)
    return lease


def _supervisor_process_options() -> dict[str, Any]:
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        return {"creationflags": flags} if flags else {}
    return {"start_new_session": True}


def _reap_supervisor(process: subprocess.Popen[Any]) -> None:
    try:
        process.wait()
    except OSError:
        pass


def _acquire_start_lock(directory: Path, timeout: float) -> Any | None:
    lock = directory / "start.lock"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        handle = lock.open("a+b")
        try:
            if lock.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            handle.seek(0)
            handle.write(
                json.dumps({"pid": os.getpid(), "created_at_utc": utc_now()}, separators=(",", ":")).encode("utf-8")
            )
            handle.truncate()
            handle.flush()
            return handle
        except OSError:
            handle.close()
            time.sleep(POLL_SECONDS)
    return None


def _release_start_lock(lock: Any | None) -> None:
    if lock is not None and not lock.closed:
        try:
            lock.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            lock.close()


def _active_lease(directory: Path) -> dict[str, Any] | None:
    lease = _read_json(_lease_path(directory))
    if not lease:
        return None
    # The supervisor owns child health and the one permitted restart.  A dead
    # server with a live ready supervisor is therefore still the active lease;
    # clients must queue the request instead of racing a second supervisor.
    if lease.get("state") == "ready" and (
        pid_exists(lease.get("supervisor_pid")) or pid_exists(lease.get("server_pid"))
    ):
        return lease
    return None


def activate_session_stdio(
    *,
    harness: str,
    session_id: str,
    output: Path,
    root: Path | None = None,
    executable: Path | None = None,
    ckb: Path | None = None,
    parent_pid: int | None = None,
    start_timeout: float = DEFAULT_START_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Start and handshake the lifecycle at the first exact Skill application."""

    output_value = output.expanduser().resolve()
    executable_value = (executable or Path(sys.executable)).expanduser().resolve()
    ckb_value = (ckb or Path(__file__).resolve().parents[1] / "ckb.py").expanduser().resolve()
    root_value = (root or default_session_stdio_root()).expanduser().resolve()
    normalized_harness = harness.strip().casefold()
    opaque_session = session_digest(session_id)
    key = lifecycle_key(normalized_harness, session_id, output_value, executable=executable_value, ckb=ckb_value)
    if not (output_value / "machine" / "knowledge.sqlite").is_file():
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "fallback",
            "mode": "cli-fallback",
            "resident": False,
            "created": False,
            "lifecycle_key": key,
            "supervisor_pid": None,
            "server_pid": None,
            "protocol": None,
            "protocol_version": None,
            "parent_monitor": "pid" if parent_pid else "unavailable",
            "fallback": {"active": True, "reason": "startup:machine-knowledge-missing"},
        }
    directory = _lifecycle_directory(root_value, key)
    root_value.mkdir(parents=True, exist_ok=True)
    try:
        lease = _active_lease(directory)
        created = lease is None
        if lease is None:
            lease = _start_supervisor(
                directory=directory,
                root=root_value,
                key=key,
                harness=normalized_harness,
                opaque_session=opaque_session,
                output=output_value,
                executable=executable_value,
                ckb=ckb_value,
                parent_pid=parent_pid,
                timeout=start_timeout,
            )
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "ready",
            "mode": "resident-stdio",
            "resident": True,
            "created": created,
            "lifecycle_key": key,
            "supervisor_pid": lease.get("supervisor_pid"),
            "server_pid": lease.get("server_pid"),
            "protocol": lease.get("protocol"),
            "protocol_version": lease.get("protocol_version"),
            "parent_monitor": lease.get("parent_monitor"),
            "fallback": {"active": False, "reason": None},
        }
    except Exception as exc:
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "fallback",
            "mode": "cli-fallback",
            "resident": False,
            "created": False,
            "lifecycle_key": key,
            "supervisor_pid": None,
            "server_pid": None,
            "protocol": None,
            "protocol_version": None,
            "parent_monitor": "pid" if parent_pid else "unavailable",
            "fallback": {"active": True, "reason": f"startup:{type(exc).__name__}:{str(exc)[:300]}"},
        }


def _activation_exists(output: Path, harness: str, session_id: str) -> bool:
    database = output.resolve() / "machine" / "automation.sqlite"
    if not database.is_file():
        return False
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            row = connection.execute(
                "SELECT 1 FROM skill_activations WHERE harness=? AND external_session_id=? AND skill_name=? LIMIT 1",
                (harness.strip().casefold(), session_id, "code-knowledge-builder"),
            ).fetchone()
            return row is not None
        finally:
            connection.close()
    except sqlite3.Error:
        return False


def _start_supervisor_locked(
    *,
    directory: Path,
    root: Path,
    key: str,
    harness: str,
    opaque_session: str,
    output: Path,
    executable: Path,
    ckb: Path,
    parent_pid: int | None,
    timeout: float,
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    lock = _acquire_start_lock(directory, timeout)
    if lock is None:
        raise CkbError("session stdio single-flight start lock timeout")
    try:
        active = _active_lease(directory)
        if active:
            return active
        cleanup_sessions(root=root, only_key=key)
        previous = _read_json(_lease_path(directory)) or {}
        previous_pid = previous.get("supervisor_pid")
        previous_deadline = time.monotonic() + timeout
        while pid_exists(previous_pid) and time.monotonic() < previous_deadline:
            time.sleep(POLL_SECONDS)
        if pid_exists(previous_pid):
            raise CkbError("session stdio previous supervisor did not exit before restart")
        cleanup_sessions(root=root, only_key=key)
        log_root = directory / "logs"
        log_root.mkdir(parents=True, exist_ok=True)
        command = [
            str(executable),
            "-X",
            "utf8",
            str(ckb),
            "stdio-session",
            "_controller",
            "--root",
            str(root),
            "--key",
            key,
            "--harness",
            harness,
            "--session-digest",
            opaque_session,
            "--out",
            str(output),
            "--python",
            str(executable),
            "--ckb",
            str(ckb),
        ]
        if parent_pid:
            command.extend(["--parent-pid", str(parent_pid)])
        with (log_root / "supervisor.stdout.log").open("a", encoding="utf-8", newline="\n") as stdout_log, (
            log_root / "supervisor.stderr.log"
        ).open("a", encoding="utf-8", newline="\n") as stderr_log:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=stdout_log,
                stderr=stderr_log,
                close_fds=True,
                **_supervisor_process_options(),
            )
        threading.Thread(
            target=_reap_supervisor,
            args=(process,),
            name=f"ckb-stdio-reap-{process.pid}",
            daemon=True,
        ).start()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            lease = _read_json(_lease_path(directory))
            if lease and lease.get("state") == "ready" and pid_exists(lease.get("server_pid")):
                return lease
            if lease and lease.get("state") in {"fallback", "closed"}:
                reason = (lease.get("fallback") or {}).get("reason") or lease.get("close_reason") or "startup-failed"
                raise CkbError(f"session stdio supervisor did not become ready: {reason}")
            if process.poll() is not None:
                raise CkbError(f"session stdio supervisor exited during start: exit={process.returncode}")
            time.sleep(POLL_SECONDS)
        raise CkbError("session stdio supervisor start timeout")
    finally:
        _release_start_lock(lock)


def _start_supervisor(**arguments: Any) -> dict[str, Any]:
    key = str(arguments["key"])
    timeout = float(arguments["timeout"])
    gate = _retain_start_gate(key)
    acquired = gate.lock.acquire(timeout=timeout)
    if not acquired:
        _release_start_gate(key, gate)
        raise CkbError("session stdio in-process single-flight timeout")
    try:
        return _start_supervisor_locked(**arguments)
    finally:
        gate.lock.release()
        _release_start_gate(key, gate)


def _fallback_command(executable: Path, ckb: Path, output: Path, request: dict[str, Any]) -> tuple[list[str] | None, str | None]:
    method = request.get("method")
    if method in {"retrieve", "brief"}:
        question = request.get("question")
        if not isinstance(question, str) or not question.strip():
            return None, "fallback-retrieve-requires-question"
        command = [str(executable), "-X", "utf8", str(ckb), str(method), "--out", str(output), question]
        command.extend(["--budget", str(request.get("budget", 1800 if method == "brief" else 1500))])
        command.extend(["--max-pages", str(request.get("max_pages", 8)), "--profile", str(request.get("profile", "fast"))])
        return command, None
    if method in {"entity", "source", "neighbors"}:
        selector = request.get("selector")
        if not isinstance(selector, str) or not selector.strip():
            return None, f"fallback-{method}-requires-selector"
        command = [str(executable), "-X", "utf8", str(ckb), str(method), "--out", str(output), selector]
        if method == "source":
            command.extend(["--context-lines", str(request.get("context_lines", 3))])
        elif method == "neighbors":
            command.extend(["--depth", str(request.get("depth", 1)), "--limit", str(request.get("limit", 50))])
            if request.get("relation"):
                command.extend(["--relation", str(request["relation"])])
        return command, None
    if method == "changes":
        command = [str(executable), "-X", "utf8", str(ckb), "changes", "--out", str(output), "--limit", str(request.get("limit", 20))]
        if request.get("kind"):
            command.extend(["--kind", str(request["kind"])])
        return command, None
    if method == "ping":
        return [], None
    return None, f"fallback-unsupported-method:{method}"


def _run_cli_fallback(
    *,
    executable: Path,
    ckb: Path,
    output: Path,
    request: dict[str, Any],
    reason: str,
    timeout: float,
) -> dict[str, Any]:
    command, error = _fallback_command(executable, ckb, output, request)
    if error:
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "failed",
            "mode": "cli-fallback",
            "resident": False,
            "fallback": {"active": True, "reason": reason},
            "error": {"type": "CkbError", "message": error, "exit_code": 2},
        }
    if command == []:
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "passed",
            "mode": "cli-fallback",
            "resident": False,
            "fallback": {"active": True, "reason": reason},
            "response": {
                "id": request.get("id"),
                "ok": True,
                "method": "ping",
                "result": {"status": "available-via-cli", "protocol": None, "protocol_version": None},
            },
        }
    environment = os.environ.copy()
    environment["CKB_STDIO_FALLBACK"] = "1"
    try:
        completed = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=environment,
            **background_process_options(),
        )
    except subprocess.TimeoutExpired:
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "failed",
            "mode": "cli-fallback",
            "resident": False,
            "fallback": {"active": True, "reason": reason},
            "error": {"type": "TimeoutExpired", "message": "per-command CLI fallback timed out", "exit_code": 2},
        }
    try:
        value = json.loads(completed.stdout) if completed.stdout.strip() else None
    except json.JSONDecodeError:
        value = None
    ok = completed.returncode == 0 and isinstance(value, dict)
    return {
        "schema_version": SESSION_STDIO_SCHEMA_VERSION,
        "status": "passed" if ok else "failed",
        "mode": "cli-fallback",
        "resident": False,
        "fallback": {"active": True, "reason": reason},
        "response": {
            "id": request.get("id"),
            "ok": ok,
            "method": request.get("method"),
            "result": value if ok else None,
            "error": None
            if ok
            else {
                "type": "CliFallbackError",
                "message": (completed.stderr or completed.stdout or "fallback failed").strip()[:1000],
                "exit_code": completed.returncode,
            },
        },
        "cli_exit_status": completed.returncode,
    }


def request_session(
    *,
    harness: str,
    session_id: str,
    output: Path,
    request: dict[str, Any],
    root: Path | None = None,
    executable: Path | None = None,
    ckb: Path | None = None,
    parent_pid: int | None = None,
    start_timeout: float = DEFAULT_START_TIMEOUT_SECONDS,
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    require_activation: bool = True,
) -> dict[str, Any]:
    output_value = output.expanduser().resolve()
    executable_value = (executable or Path(sys.executable)).expanduser().resolve()
    ckb_value = (ckb or Path(__file__).resolve().parents[1] / "ckb.py").expanduser().resolve()
    root_value = (root or default_session_stdio_root()).expanduser().resolve()
    if not (output_value / "machine" / "knowledge.sqlite").is_file():
        raise CkbError(f"session stdio requires machine/knowledge.sqlite: {output_value}")
    if not executable_value.is_file() or not ckb_value.is_file():
        raise CkbError("session stdio executable identity is missing")
    if not isinstance(request, dict):
        raise CkbError("session stdio request must be one JSON object")
    request = dict(request)
    if not isinstance(request.get("id"), (str, int)) or isinstance(request.get("id"), bool):
        request["id"] = "request-" + uuid.uuid4().hex
    normalized_harness = harness.strip().casefold()
    if require_activation and not _activation_exists(output_value, normalized_harness, session_id):
        return {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "status": "ignored",
            "mode": "not-started",
            "resident": False,
            "reason": "skill-not-applied-in-session",
            "fallback": {"active": False, "reason": None},
        }
    opaque_session = session_digest(session_id)
    key = lifecycle_key(normalized_harness, session_id, output_value, executable=executable_value, ckb=ckb_value)
    directory = _lifecycle_directory(root_value, key)
    root_value.mkdir(parents=True, exist_ok=True)
    try:
        lease = _active_lease(directory)
        if lease is None:
            lease = _start_supervisor(
                directory=directory,
                root=root_value,
                key=key,
                harness=normalized_harness,
                opaque_session=opaque_session,
                output=output_value,
                executable=executable_value,
                ckb=ckb_value,
                parent_pid=parent_pid,
                timeout=start_timeout,
            )
    except Exception as exc:
        return _run_cli_fallback(
            executable=executable_value,
            ckb=ckb_value,
            output=output_value,
            request=request,
            reason=f"startup:{type(exc).__name__}:{str(exc)[:300]}",
            timeout=request_timeout,
        )
    token = uuid.uuid4().hex
    request_path = directory / "requests" / f"{token}.json"
    response_path = directory / "responses" / f"{token}.json"
    json_write(
        request_path,
        {
            "schema_version": SESSION_STDIO_SCHEMA_VERSION,
            "request_token": token,
            "timeout_seconds": request_timeout,
            "created_at_utc": utc_now(),
            "request": request,
        },
    )
    deadline = time.monotonic() + request_timeout + 2.0
    try:
        while time.monotonic() < deadline:
            response = _read_json(response_path)
            if response is not None:
                if response.get("status") == "transport-failed":
                    reason = str((response.get("fallback") or {}).get("reason") or "transport-failed")
                    return _run_cli_fallback(
                        executable=executable_value,
                        ckb=ckb_value,
                        output=output_value,
                        request=request,
                        reason=reason,
                        timeout=request_timeout,
                    )
                return response
            current = _read_json(_lease_path(directory)) or lease
            if current.get("state") in {"fallback", "closed"} or not pid_exists(current.get("supervisor_pid")):
                reason = str((current.get("fallback") or {}).get("reason") or current.get("close_reason") or "supervisor-exited")
                return _run_cli_fallback(
                    executable=executable_value,
                    ckb=ckb_value,
                    output=output_value,
                    request=request,
                    reason=reason,
                    timeout=request_timeout,
                )
            time.sleep(POLL_SECONDS)
        return _run_cli_fallback(
            executable=executable_value,
            ckb=ckb_value,
            output=output_value,
            request=request,
            reason="client-response-timeout",
            timeout=request_timeout,
        )
    finally:
        request_path.unlink(missing_ok=True)
        response_path.unlink(missing_ok=True)


def environment_session() -> tuple[str, str, int | None] | None:
    """Resolve only documented or explicit Harness identity environment fields."""

    explicit_harness = str(os.environ.get("CKB_HARNESS") or "").strip().casefold()
    candidates = [
        ("codex", ("CODEX_SESSION_ID", "CODEX_THREAD_ID")),
        ("claude", ("CLAUDE_SESSION_ID",)),
        ("opencode", ("OPENCODE_SESSION_ID",)),
        ("dsh", ("DSH_SESSION_ID",)),
        ("gemini", ("GEMINI_SESSION_ID",)),
        ("copilot", ("COPILOT_SESSION_ID",)),
        ("cursor", ("CURSOR_SESSION_ID",)),
        ("generic", ("CKB_SESSION_ID",)),
    ]
    if explicit_harness:
        candidates.sort(key=lambda item: item[0] != explicit_harness)
    for harness, names in candidates:
        if explicit_harness and harness != explicit_harness:
            continue
        for name in ("CKB_SESSION_ID", *names):
            session = str(os.environ.get(name) or "").strip()
            if session:
                parent_text = str(os.environ.get("CKB_HARNESS_PID") or "").strip()
                parent_pid = int(parent_text) if parent_text.isdigit() and int(parent_text) > 0 else None
                return harness, session, parent_pid
    return None


def maybe_request_session(output: Path, request: dict[str, Any]) -> dict[str, Any] | None:
    """Route an ordinary CKB CLI query through an already activated session."""

    if os.environ.get("CKB_STDIO_FALLBACK") == "1":
        return None
    identity = environment_session()
    if identity is None:
        return None
    harness, session_id, parent_pid = identity
    if not _activation_exists(output.resolve(), harness, session_id):
        return None
    return request_session(
        harness=harness,
        session_id=session_id,
        output=output,
        request=request,
        parent_pid=parent_pid,
    )


def list_sessions(*, root: Path | None = None, active_only: bool = False) -> dict[str, Any]:
    root_value = (root or default_session_stdio_root()).expanduser().resolve()
    leases: list[dict[str, Any]] = []
    if root_value.is_dir():
        for path in sorted(root_value.glob("stdio-*/lease.json")):
            lease = _read_json(path)
            if not lease:
                continue
            active = lease.get("state") in {"starting", "ready", "closing"} and pid_exists(lease.get("supervisor_pid"))
            if active_only and not active:
                continue
            value = dict(lease)
            value["active"] = active
            leases.append(value)
    return {
        "schema_version": SESSION_STDIO_SCHEMA_VERSION,
        "status": "passed",
        "root": str(root_value),
        "count": len(leases),
        "active": sum(1 for item in leases if item["active"]),
        "leases": leases,
    }


def close_session(
    *,
    harness: str,
    session_id: str,
    output: Path,
    root: Path | None = None,
    reason: str = "explicit-close",
    timeout: float = DEFAULT_CLOSE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root_value = (root or default_session_stdio_root()).expanduser().resolve()
    opaque = session_digest(session_id)
    output_identity = _path_identity(output)
    matches: list[Path] = []
    if root_value.is_dir():
        for path in root_value.glob("stdio-*/lease.json"):
            lease = _read_json(path)
            if not lease:
                continue
            if (
                lease.get("harness") == harness.strip().casefold()
                and lease.get("session_digest") == opaque
                and _path_identity(lease.get("output", "")) == output_identity
            ):
                matches.append(path.parent)
    closed: list[dict[str, Any]] = []
    for directory in sorted(matches):
        lease = _read_json(_lease_path(directory)) or {}
        if lease.get("state") == "closed" and not pid_exists(lease.get("supervisor_pid")) and not pid_exists(lease.get("server_pid")):
            closed.append({"lifecycle_key": lease.get("lifecycle_key"), "status": "already-closed"})
            continue
        token = uuid.uuid4().hex
        json_write(directory / "control" / f"close-{token}.json", {"reason": reason[:120], "requested_at_utc": utc_now()})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current = _read_json(_lease_path(directory)) or lease
            if (
                current.get("state") == "closed"
                and not pid_exists(current.get("server_pid"))
                and not pid_exists(current.get("supervisor_pid"))
            ):
                cleanup_sessions(root=root_value, only_key=str(current.get("lifecycle_key") or directory.name))
                current = _read_json(_lease_path(directory)) or current
                closed.append({"lifecycle_key": current.get("lifecycle_key"), "status": "closed", "lease": current})
                break
            if not pid_exists(current.get("supervisor_pid")):
                cleanup_sessions(root=root_value, only_key=str(current.get("lifecycle_key") or directory.name))
            time.sleep(POLL_SECONDS)
        else:
            current = _read_json(_lease_path(directory)) or lease
            _force_terminate_pid(int(current.get("supervisor_pid") or 0))
            _force_terminate_pid(int(current.get("server_pid") or 0))
            cleanup_sessions(root=root_value, only_key=str(current.get("lifecycle_key") or directory.name))
            closed.append({"lifecycle_key": current.get("lifecycle_key"), "status": "forced-cleanup"})
    return {
        "schema_version": SESSION_STDIO_SCHEMA_VERSION,
        "status": "closed" if matches else "not-found",
        "reason": reason[:120],
        "matched": len(matches),
        "closed": closed,
    }


def cleanup_sessions(*, root: Path | None = None, only_key: str | None = None) -> dict[str, Any]:
    root_value = (root or default_session_stdio_root()).expanduser().resolve()
    cleaned: list[dict[str, Any]] = []
    if not root_value.is_dir():
        return {"schema_version": SESSION_STDIO_SCHEMA_VERSION, "status": "passed", "root": str(root_value), "cleaned": []}
    directories = [root_value / only_key] if only_key else sorted(path for path in root_value.glob("stdio-*") if path.is_dir())
    for directory in directories:
        lease = _read_json(_lease_path(directory))
        if not lease:
            continue
        supervisor_pid = lease.get("supervisor_pid")
        server_pid = lease.get("server_pid")
        parent_pid = lease.get("parent_pid")
        parent_dead = bool(parent_pid) and not pid_exists(parent_pid)
        supervisor_dead = bool(supervisor_pid) and not pid_exists(supervisor_pid)
        if lease.get("state") in {"starting", "ready", "closing"} and pid_exists(supervisor_pid) and parent_dead:
            json_write(directory / "control" / f"close-cleanup-{uuid.uuid4().hex}.json", {"reason": "parent-death-cleanup"})
            cleaned.append({"lifecycle_key": lease.get("lifecycle_key"), "action": "close-requested"})
            continue
        if (supervisor_dead or not supervisor_pid) and lease.get("state") in {"fallback", "closed"}:
            deadline = time.monotonic() + 1.5
            while pid_exists(server_pid) and time.monotonic() < deadline:
                time.sleep(POLL_SECONDS)
            forced = False
            if pid_exists(server_pid):
                forced = _force_terminate_pid(int(server_pid))
            lease.update(
                {
                    "state": "closed",
                    "supervisor_pid": None,
                    "server_pid": None,
                    "closed_at_utc": lease.get("closed_at_utc") or utc_now(),
                    "close_reason": lease.get("close_reason") or "stale-cleanup",
                    "object_counts": _state_counts(lease=0, process=0, pending=0, readers=0, pipes=0),
                }
            )
            _write_lease(directory, lease)
            _clear_transient(directory)
            cleaned.append({"lifecycle_key": lease.get("lifecycle_key"), "action": "stale-cleaned", "forced_server": forced})
    return {"schema_version": SESSION_STDIO_SCHEMA_VERSION, "status": "passed", "root": str(root_value), "cleaned": cleaned}


def audit_sessions(*, root: Path | None = None) -> dict[str, Any]:
    listing = list_sessions(root=root)
    errors: list[str] = []
    totals = _state_counts(lease=0, process=0, pending=0, readers=0, pipes=0)
    for lease in listing["leases"]:
        serialized = json.dumps(lease, ensure_ascii=False, sort_keys=True).casefold()
        for field in _FORBIDDEN_STATE_KEYS:
            if f'"{field}"' in serialized:
                errors.append(f"forbidden-state-field:{field}:{lease.get('lifecycle_key')}")
        counts = lease.get("object_counts") or {}
        if lease.get("active"):
            for name in totals:
                totals[name] += int(counts.get(name, 0))
        elif lease.get("state") == "closed" and any(int(counts.get(name, 0)) for name in totals):
            errors.append(f"closed-object-count:{lease.get('lifecycle_key')}")
        if lease.get("state") == "ready" and not pid_exists(lease.get("server_pid")):
            errors.append(f"ready-server-missing:{lease.get('lifecycle_key')}")
    return {
        "schema_version": SESSION_STDIO_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "root": listing["root"],
        "active": listing["active"],
        "object_counts": totals,
        "errors": errors,
    }
