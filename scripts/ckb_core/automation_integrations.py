"""Generate host-specific adapters for the CKB automation protocol."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from .automation import SUPPORTED_HARNESSES
from .common import CkbError, json_write


INTEGRATION_VERSION = "1.2.0"


def _looks_windows(path: Path) -> bool:
    text = str(path)
    return (len(text) >= 3 and text[1:3] in {":\\", ":/"}) or text.startswith("\\\\")


def _commands(python: Path, ckb: Path, harness: str, registry: Path) -> tuple[str, str]:
    args = [str(python), "-X", "utf8", str(ckb), "automation", "hook", "--harness", harness, "--registry", str(registry)]
    return shlex.join(args), subprocess.list2cmdline(args)


def _powershell_command(python: Path, ckb: Path, harness: str, registry: Path) -> str:
    def quote(value: Path | str) -> str:
        return "'" + str(value).replace("'", "''") + "'"

    return " ".join(
        [
            "&",
            quote(python),
            "-X",
            "utf8",
            quote(ckb),
            "automation",
            "hook",
            "--harness",
            harness,
            "--registry",
            quote(registry),
        ]
    )


def _handler(posix: str, windows: str, timeout: int, status: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "command",
        "command": posix,
        "commandWindows": windows,
        "timeout": timeout,
    }
    if status:
        result["statusMessage"] = status
    return result


def _codex_hooks(posix: str, windows: str, *, dsh_subset: bool = False) -> dict[str, Any]:
    hooks: dict[str, Any] = {
        "SessionStart": [
            {
                "matcher": "startup|resume|clear|compact",
                "hooks": [_handler(posix, windows, 8, "正在恢复 CKB 自动化上下文")],
            }
        ],
        "UserPromptSubmit": [{"hooks": [_handler(posix, windows, 8)]}],
        "PostToolUse": [
            {
                "matcher": "Bash|apply_patch|Edit|Write",
                "hooks": [_handler(posix, windows, 8, "正在记录修改证据")],
            }
        ],
        "Stop": [{"hooks": [_handler(posix, windows, 15, "正在形成机器层待审阅记录")]}],
    }
    if not dsh_subset:
        hooks.update(
            {
                "PreCompact": [{"matcher": "manual|auto", "hooks": [_handler(posix, windows, 8)]}],
                "PostCompact": [{"matcher": "manual|auto", "hooks": [_handler(posix, windows, 8)]}],
                "SessionEnd": [{"hooks": [_handler(posix, windows, 3)]}],
            }
        )
    return {
        "description": "仅在当前会话明确应用 code-knowledge-builder Skill 后，将已登记项目的会话与修改证据同步到机器知识库。",
        "hooks": hooks,
    }


def _claude_hooks(command: str) -> dict[str, Any]:
    def handler(timeout: int) -> dict[str, Any]:
        return {"type": "command", "command": command, "timeout": timeout}

    return {
        "hooks": {
            "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [handler(8)]}],
            "UserPromptSubmit": [{"hooks": [handler(8)]}],
            "UserPromptExpansion": [{"matcher": "code-knowledge-builder", "hooks": [handler(8)]}],
            "PreToolUse": [{"matcher": "Skill", "hooks": [handler(8)]}],
            "PostToolUse": [{"matcher": "Write|Edit|Bash|NotebookEdit", "hooks": [handler(8)]}],
            "PostToolUseFailure": [{"matcher": "Write|Edit|Bash|NotebookEdit", "hooks": [handler(8)]}],
            "FileChanged": [{"hooks": [handler(8)]}],
            "Stop": [{"hooks": [handler(15)]}],
            "StopFailure": [{"hooks": [handler(15)]}],
            "PreCompact": [{"matcher": "manual|auto", "hooks": [handler(8)]}],
            "PostCompact": [{"matcher": "manual|auto", "hooks": [handler(8)]}],
            "SessionEnd": [{"hooks": [handler(3)]}],
        }
    }


def _gemini_hooks(command: str) -> dict[str, Any]:
    def handler(timeout_ms: int) -> dict[str, Any]:
        return {"type": "command", "command": command, "timeout": timeout_ms}

    return {
        "hooks": {
            "SessionStart": [{"matcher": "startup|resume|clear", "hooks": [handler(8_000)]}],
            "BeforeAgent": [{"hooks": [handler(8_000)]}],
            "AfterTool": [{"matcher": ".*", "hooks": [handler(8_000)]}],
            "AfterAgent": [{"hooks": [handler(15_000)]}],
            "PreCompress": [{"hooks": [handler(8_000)]}],
            "SessionEnd": [{"hooks": [handler(3_000)]}],
        }
    }


def _copilot_hooks(posix: str, powershell: str) -> dict[str, Any]:
    def handler(timeout: int, matcher: str | None = None) -> dict[str, Any]:
        value: dict[str, Any] = {
            "type": "command",
            "bash": posix,
            "powershell": powershell,
            "timeoutSec": timeout,
        }
        if matcher:
            value["matcher"] = matcher
        return value

    # PascalCase selects Copilot's VS Code-compatible snake_case payloads,
    # which keeps the adapter aligned with Codex/Claude without pretending the
    # event names or output decisions are otherwise interchangeable.
    return {
        "version": 1,
        "hooks": {
            "SessionStart": [handler(8)],
            "UserPromptSubmit": [handler(8)],
            "PostToolUse": [handler(8, "Bash|Edit|Write|NotebookEdit")],
            "PostToolUseFailure": [handler(8, "Bash|Edit|Write|NotebookEdit")],
            "Stop": [handler(15)],
            "PreCompact": [handler(8)],
            "SessionEnd": [handler(3)],
        },
    }


def _cursor_hooks(command: str) -> dict[str, Any]:
    def handler(matcher: str | None = None, timeout: int = 8) -> dict[str, Any]:
        value: dict[str, Any] = {"command": command, "timeout": timeout}
        if matcher:
            value["matcher"] = matcher
        return value

    return {
        "version": 1,
        "hooks": {
            "sessionStart": [handler()],
            "beforeSubmitPrompt": [handler("UserPromptSubmit")],
            "postToolUse": [handler("Shell|Write|Delete|MCP:.*")],
            "postToolUseFailure": [handler("Shell|Write|Delete|MCP:.*")],
            "afterFileEdit": [handler("Write")],
            "afterAgentResponse": [handler()],
            "preCompact": [handler()],
            "stop": [handler("Stop", 15)],
            "sessionEnd": [handler(timeout=3)],
        },
    }


def _opencode_stable_plugin(python: Path, ckb: Path, registry: Path) -> str:
    command_args = ["-X", "utf8", str(ckb), "automation", "hook", "--harness", "opencode", "--registry", str(registry)]
    return f'''import {{ spawnSync }} from "node:child_process"

const PYTHON = {json.dumps(str(python))}
const ARGS = {json.dumps(command_args)}

function value(object, keys) {{
  if (!object || typeof object !== "object") return undefined
  for (const key of keys) if (object[key] !== undefined && object[key] !== null) return object[key]
  for (const child of Object.values(object)) {{
    const found = value(child, keys)
    if (found !== undefined) return found
  }}
}}

function text(object) {{
  if (typeof object === "string") return object
  if (Array.isArray(object)) return object.map(text).filter(Boolean).join("\\n")
  if (!object || typeof object !== "object") return ""
  if (typeof object.text === "string") return object.text
  for (const key of ["content", "parts", "message", "delta"]) {{
    const found = text(object[key])
    if (found) return found
  }}
  return ""
}}

function emit(payload) {{
  try {{
    spawnSync(PYTHON, ARGS, {{ input: JSON.stringify(payload), encoding: "utf8", timeout: 8000, windowsHide: true }})
  }} catch {{}}
}}

export const CodeKnowledgeBuilderSync = async ({{ directory, worktree }}) => {{
  const cwd = worktree || directory || process.cwd()
  const assistants = new Map()
  return {{
    event: async ({{ event }}) => {{
      const data = event?.properties ?? event?.data ?? event ?? {{}}
      const info = data?.info ?? data
      const sessionID = String(value(info, ["sessionID", "sessionId", "session_id", "id"]) ?? "session-unknown")
      const base = {{ session_id: sessionID, cwd }}
      if (event?.type === "session.created") emit({{ ...base, hook_event_name: "SessionStart", source: "startup", event_id: `session-created:${{sessionID}}` }})
      if (event?.type === "message.updated") {{
        const role = String(value(info, ["role"]) ?? "").toLowerCase()
        const body = text(info)
        const messageID = String(value(info, ["messageID", "messageId", "id"]) ?? "")
        if (role === "user") emit({{ ...base, hook_event_name: "UserPromptSubmit", prompt: body, event_id: `message:${{messageID}}` }})
        if (role === "assistant") {{
          assistants.set(sessionID, body)
          emit({{ ...base, hook_event_name: "AssistantMessage", assistant_message: body, event_id: `message:${{messageID}}` }})
        }}
      }}
      if (event?.type === "command.executed") {{
        const commandName = String(value(data, ["command", "commandName", "name"]) ?? "")
        if (commandName.replace(/^[$/]/, "") === "code-knowledge-builder") emit({{ ...base, hook_event_name: "SkillApplied", skill_name: "code-knowledge-builder", ckb_skill_applied: true, event_id: `skill:${{sessionID}}:${{commandName}}` }})
      }}
      if (event?.type === "file.edited") emit({{ ...base, hook_event_name: "FileChanged", file_path: value(data, ["file", "filePath", "path"]), event: "change" }})
      if (event?.type === "session.compacted") emit({{ ...base, hook_event_name: "PostCompact", trigger: "auto" }})
      if (event?.type === "session.idle") emit({{ ...base, hook_event_name: "Stop", last_assistant_message: assistants.get(sessionID) ?? "", stop_hook_active: false }})
      if (event?.type === "session.deleted") emit({{ ...base, hook_event_name: "SessionEnd", reason: "other" }})
    }},
    "tool.execute.after": async (input, output) => {{
      emit({{
        session_id: String(input?.sessionID ?? input?.sessionId ?? "session-unknown"),
        cwd,
        hook_event_name: "PostToolUse",
        tool_name: String(input?.tool ?? "unknown"),
        tool_use_id: String(input?.callID ?? input?.toolCallID ?? input?.id ?? ""),
        tool_input: input?.args ?? input?.input ?? input,
        tool_response: output,
        status: "completed",
      }})
    }},
  }}
}}
'''


def _opencode_v2_plugin(python: Path, ckb: Path, registry: Path) -> str:
    command_args = ["-X", "utf8", str(ckb), "automation", "hook", "--harness", "opencode-v2", "--registry", str(registry)]
    return f'''import {{ spawnSync }} from "node:child_process"
import {{ Plugin }} from "@opencode-ai/plugin"

const PYTHON = {json.dumps(str(python))}
const ARGS = {json.dumps(command_args)}

function emit(payload) {{
  try {{ spawnSync(PYTHON, ARGS, {{ input: JSON.stringify(payload), encoding: "utf8", timeout: 8000, windowsHide: true }}) }} catch {{}}
}}

function messageText(message) {{
  const parts = message?.parts ?? message?.content ?? []
  if (typeof parts === "string") return parts
  return Array.isArray(parts) ? parts.map((part) => typeof part === "string" ? part : part?.text ?? "").filter(Boolean).join("\\n") : ""
}}

function unwrapMessages(value) {{
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.data)) return value.data
  if (Array.isArray(value?.messages)) return value.messages
  return []
}}

function eventSessionID(event) {{
  return String(event?.sessionID ?? event?.properties?.sessionID ?? event?.data?.sessionID ?? "session-unknown")
}}

function eventCwd(event) {{
  return String(event?.cwd ?? event?.location?.directory ?? event?.properties?.cwd ?? event?.data?.cwd ?? process.cwd())
}}

export default Plugin.define({{
  id: "code-knowledge-builder.sync",
  setup: async (ctx) => {{
    const seenSessions = new Set()
    await ctx.session.hook("context", (event) => {{
      const sessionID = String(event.sessionID ?? "session-unknown")
      const cwd = eventCwd(event)
      if (!seenSessions.has(sessionID)) {{
        seenSessions.add(sessionID)
        emit({{ session_id: sessionID, cwd, hook_event_name: "SessionStart", source: "startup", event_id: `session:${{sessionID}}` }})
      }}
      const messages = Array.isArray(event.messages) ? event.messages : []
      const latest = [...messages].reverse().find((item) => item?.role === "user")
      if (latest) emit({{ session_id: sessionID, cwd, hook_event_name: "UserPromptSubmit", prompt: messageText(latest), event_id: `message:${{latest.id ?? latest.messageID ?? "latest"}}` }})
    }})
    await ctx.tool.hook("execute.after", (event) => {{
      emit({{
        session_id: String(event.sessionID ?? "session-unknown"),
        cwd: String(event.cwd ?? process.cwd()),
        hook_event_name: "PostToolUse",
        tool_name: String(event.tool ?? "unknown"),
        tool_use_id: String(event.toolCallID ?? event.callID ?? ""),
        tool_input: event.input,
        tool_response: event.status === "error" ? event.error : event.result,
        output_paths: event.outputPaths ?? [],
        status: event.status ?? "completed",
      }})
    }})
    const controller = new AbortController()
    void (async () => {{
      try {{
        for await (const event of ctx.event.subscribe({{ signal: controller.signal }})) {{
          const sessionID = eventSessionID(event)
          const cwd = eventCwd(event)
          if (event.type === "command.executed") {{
            const commandName = String(event?.command ?? event?.properties?.command ?? event?.data?.command ?? "")
            if (commandName.replace(/^[$/]/, "") === "code-knowledge-builder") emit({{ session_id: sessionID, cwd, hook_event_name: "SkillApplied", skill_name: "code-knowledge-builder", ckb_skill_applied: true, event_id: `skill:${{sessionID}}:${{commandName}}` }})
          }}
          if (["session.execution.succeeded", "session.execution.succeeded.1", "session.idle"].includes(event.type)) {{
            const messages = unwrapMessages(await ctx.session.context({{ sessionID }}))
            const latest = [...messages].reverse().find((item) => item?.role === "assistant")
            emit({{ session_id: sessionID, cwd, hook_event_name: "Stop", last_assistant_message: messageText(latest), stop_hook_active: false, event_id: `stop:${{sessionID}}:${{latest?.id ?? event.id ?? event.type}}` }})
          }}
          if (["session.execution.failed", "session.execution.failed.1"].includes(event.type)) emit({{ session_id: sessionID, cwd, hook_event_name: "StopFailure", last_assistant_message: String(event.error?.message ?? event.error ?? "OpenCode 执行失败。"), event_id: `stop-failed:${{sessionID}}:${{event.id ?? event.type}}` }})
          if (event.type === "session.deleted") emit({{ session_id: sessionID, cwd, hook_event_name: "SessionEnd", reason: "other", event_id: `session-end:${{sessionID}}` }})
          if (event.type === "session.compacted") emit({{ session_id: sessionID, cwd, hook_event_name: "PostCompact", trigger: "auto", event_id: `compact:${{sessionID}}:${{event.id ?? "auto"}}` }})
        }}
      }} catch {{}}
    }})()
    return () => controller.abort()
  }},
}})
'''


def _generic_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://code-knowledge-builder.local/automation-event.schema.json",
        "title": "Code Knowledge Builder canonical automation event",
        "type": "object",
        "required": ["canonical_type", "session_id", "cwd"],
        "properties": {
            "canonical_type": {
                "enum": [
                    "skill.applied",
                    "session.start",
                    "turn.prompt",
                    "turn.assistant",
                    "tool.result",
                    "file.changed",
                    "turn.stop",
                    "compact.before",
                    "compact.after",
                    "session.end",
                ]
            },
            "event_id": {"type": "string", "minLength": 1},
            "session_id": {"type": "string", "minLength": 1},
            "turn_id": {"type": "string"},
            "cwd": {"type": "string", "minLength": 1},
            "prompt": {"type": "string"},
            "assistant_message": {"type": "string"},
            "tool_name": {"type": "string"},
            "tool_use_id": {"type": "string"},
            "tool_input": {},
            "tool_output": {},
            "changed_paths": {"type": "array", "items": {"type": "string"}},
            "skill_name": {"type": "string", "const": "code-knowledge-builder"},
            "ckb_skill_applied": {"type": "boolean", "const": True},
        },
        "additionalProperties": True,
    }


def render_integration(
    harness: str,
    destination: Path,
    python: Path | None = None,
    ckb: Path | None = None,
    registry: Path | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    if harness not in SUPPORTED_HARNESSES:
        raise CkbError(f"unsupported integration harness: {harness}")
    destination = destination.resolve()
    python = (python or Path(sys.executable)).expanduser().resolve()
    ckb = (ckb or Path(__file__).resolve().parents[1] / "ckb.py").expanduser().resolve()
    registry = (registry or Path.home() / ".ckb" / "automation-registry.json").expanduser().resolve()
    if not python.is_file():
        raise CkbError(f"integration Python executable is missing: {python}")
    if not ckb.is_file():
        raise CkbError(f"integration CKB entrypoint is missing: {ckb}")
    if destination.exists() and any(destination.iterdir()) and not force:
        raise CkbError(f"integration destination is not empty: {destination}; use --force to replace generated files")
    destination.mkdir(parents=True, exist_ok=True)
    posix, windows = _commands(python, ckb, harness, registry)
    powershell = _powershell_command(python, ckb, harness, registry)
    files: list[Path] = []

    def write(relative: str, value: str | dict[str, Any]) -> Path:
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(value, ensure_ascii=False, indent=2) + "\n" if isinstance(value, dict) else value
        path.write_text(text, encoding="utf-8", newline="\n")
        files.append(path)
        return path

    if harness == "codex":
        write(
            ".codex-plugin/plugin.json",
            {
                "name": "code-knowledge-builder-sync",
                "version": INTEGRATION_VERSION,
                "description": "仅在会话明确应用 code-knowledge-builder Skill 后，同步已登记项目的 Codex 会话和修改证据。",
                "author": {"name": "Code Knowledge Builder"},
                "interface": {
                    "displayName": "Code Knowledge Builder Sync",
                    "shortDescription": "同步明确应用 CKB Skill 的项目会话",
                    "longDescription": "会话明确应用 code-knowledge-builder Skill 后，把 Codex 生命周期事件写入脱敏机器队列，并等待 Agent 中文审阅后再进入人类知识库。",
                    "developerName": "Code Knowledge Builder",
                    "category": "Productivity",
                    "capabilities": ["Read", "Write"],
                    "defaultPrompt": "检查当前项目的 Code Knowledge Builder 自动同步状态。",
                },
            },
        )
        write("hooks/hooks.json", _codex_hooks(posix, windows))
    elif harness == "claude":
        command = windows if _looks_windows(python) else posix
        write(".claude/settings.json", _claude_hooks(command))
    elif harness == "opencode":
        write(".opencode/plugins/code-knowledge-builder-sync.mjs", _opencode_stable_plugin(python, ckb, registry))
    elif harness == "opencode-v2":
        write(".opencode/plugins/code-knowledge-builder-sync-v2.mjs", _opencode_v2_plugin(python, ckb, registry))
    elif harness == "dsh":
        # The current DSH Codex bridge intentionally reads `command` and ignores
        # Codex's `commandWindows` extension, so stamp the platform command into
        # both fields when rendering on Windows.
        dsh_command = windows if _looks_windows(python) else posix
        write("hooks.json", _codex_hooks(dsh_command, dsh_command, dsh_subset=True))
        config_path = (destination / "hooks.json").as_posix()
        write(
            "cordis.yml.fragment",
            "- dsh-hooks-codex:\n"
            f"    configPath: {json.dumps(config_path)}\n"
            "    model: ckb-sync\n",
        )
    elif harness == "gemini":
        command = windows if _looks_windows(python) else posix
        write(".gemini/settings.json", _gemini_hooks(command))
    elif harness == "copilot":
        write(".github/hooks/code-knowledge-builder.json", _copilot_hooks(posix, powershell))
    elif harness == "cursor":
        command = windows if _looks_windows(python) else posix
        write(".cursor/hooks.json", _cursor_hooks(command))
    else:
        write("automation-event.schema.json", _generic_schema())
        write(
            "example-event.json",
            {
                "canonical_type": "skill.applied",
                "event_id": "HARNESS_EVENT_ID",
                "session_id": "HARNESS_SESSION_ID",
                "cwd": "/absolute/project/path",
                "skill_name": "code-knowledge-builder",
                "ckb_skill_applied": True,
            },
        )
    manifest = {
        "schema_version": 1,
        "status": "rendered",
        "integration_version": INTEGRATION_VERSION,
        "harness": harness,
        "python": str(python),
        "ckb": str(ckb),
        "registry": str(registry),
        "project_opt_in_required": True,
        "session_skill_activation_required": True,
        "required_skill": "code-knowledge-builder",
        "transcript_parsing": False,
        "files": [str(path.relative_to(destination).as_posix()) for path in files],
    }
    manifest_path = write("integration.json", manifest)
    return {**manifest, "destination": str(destination), "manifest": str(manifest_path)}
