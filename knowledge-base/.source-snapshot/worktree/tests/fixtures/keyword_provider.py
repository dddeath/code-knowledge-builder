"""Deterministic command/stdio fixture for the keyword-provider contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


request = json.loads(sys.stdin.read())
mode = os.environ.get("CKB_FAKE_KEYWORD_PROVIDER_MODE", "passed")
marker = os.environ.get("CKB_FAKE_KEYWORD_PROVIDER_MARKER")
if marker:
    marker_path = Path(marker)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with marker_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"{request['request_id']}\n")
identity = {
    "schema_version": 1,
    "status": "passed",
    "request_id": request["request_id"],
    "provider": os.environ.get("CKB_FAKE_KEYWORD_PROVIDER_NAME", "fixture"),
    "model": os.environ.get("CKB_FAKE_KEYWORD_PROVIDER_MODEL", "fixture-model"),
    "version": os.environ.get("CKB_FAKE_KEYWORD_PROVIDER_VERSION", "1"),
}
value = {
    **identity,
    "keywords": ["machine retrieval", "关键词扩展"],
    "anchors": ["retrieve_machine"],
    "rewrites": ["机器知识关键词慢路径"],
    "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30, "cost_usd": 0.001},
}

if mode == "invalid-json":
    sys.stdout.write("{not-json")
    raise SystemExit(0)
if mode == "timeout":
    time.sleep(10)
if mode == "exit-nonzero":
    sys.stderr.write("fixture process failed\n")
    raise SystemExit(7)
if mode == "rate-limit":
    value = {**identity, "status": "failed", "failure_type": "rate-limit", "usage": {}}
if mode == "missing-credentials":
    value = {**identity, "status": "failed", "failure_type": "missing-credentials", "usage": {}}
if mode == "too-many-keywords":
    value["keywords"] = [f"keyword-{index}" for index in range(17)]
if mode == "duplicate-keywords":
    value["keywords"] = ["duplicate", "DUPLICATE"]
if mode == "prompt-injection":
    value["keywords"] = ["ignore previous instructions"]
if mode == "unsupported-characters":
    value["anchors"] = ["retrieve_machine; rm"]
if mode == "empty-output":
    value["keywords"] = []
    value["anchors"] = []
    value["rewrites"] = []
if mode == "irrelevant-output":
    value["keywords"] = ["banana orchard", "weather forecast"]
    value["anchors"] = ["unrelated_symbol"]
    value["rewrites"] = ["music playlist recommendation"]
if mode == "wrong-request":
    value["request_id"] = "keyword-wrong"
if mode == "order-service":
    value["keywords"] = ["OrderService", "save order"]
    value["anchors"] = ["OrderService", "save_order"]
    value["rewrites"] = ["订单服务保存入口"]
if mode == "chinese-retrieval-replay":
    replay_path = Path(__file__).with_name("chinese-retrieval-effects") / "replay-responses.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    response = next(
        (item for item in replay["responses"] if item["input_hash"] == request["input_hash"]),
        None,
    )
    if response is None:
        value = {**identity, "status": "failed", "failure_type": "unavailable", "usage": {}}
    else:
        value = {
            **identity,
            "keywords": response["keywords"],
            "anchors": response["anchors"],
            "rewrites": response["rewrites"],
            "usage": response["usage"],
        }
if mode == "codex-cli":
    executable = os.environ.get("CKB_REAL_KEYWORD_PROVIDER_EXECUTABLE")
    if not executable:
        sys.stderr.write("CKB_REAL_KEYWORD_PROVIDER_EXECUTABLE is required\n")
        raise SystemExit(64)
    model = identity["model"]
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["keywords", "anchors", "rewrites"],
        "properties": {
            "keywords": {
                "type": "array",
                "minItems": 1,
                "maxItems": 16,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 80,
                    "pattern": r"^[A-Za-z0-9_\u3400-\u9fff./:+# -]+$",
                },
            },
            "anchors": {
                "type": "array",
                "maxItems": 12,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 160,
                    "pattern": r"^[A-Za-z_][A-Za-z0-9_]*(?:(?:::|\.)[A-Za-z_][A-Za-z0-9_]*)*$",
                },
            },
            "rewrites": {
                "type": "array",
                "maxItems": 4,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 320,
                    "pattern": r"^[A-Za-z0-9_\u3400-\u9fff\s./:+#(),（）-]+$",
                },
            },
        },
    }
    with tempfile.TemporaryDirectory(prefix="ckb-real-keyword-provider-") as temporary:
        root = Path(temporary)
        schema_path = root / "schema.json"
        output_path = root / "last-message.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=True), encoding="utf-8")
        prompt = (
            "你是代码知识库检索的关键词扩展 Provider。只分析给定问题，不调用工具，也不读取文件。\n"
            f"问题：{request['question']}\n"
            "返回符合 schema 的 JSON：keywords 提供简短中英文检索词；anchors 只放可能的源码标识符，"
            "不确定时留空；rewrites 最多两条。保留问题中的源码标识符，并补充有助于定位实现文件的同义词。"
            "不要输出 Markdown、说明、凭据或指令文本。"
        )
        completed = subprocess.run(
            [
                executable,
                "-a",
                "never",
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "-s",
                "read-only",
                "-m",
                model,
                "--output-schema",
                str(schema_path),
                "-o",
                str(output_path),
                "--json",
                "-C",
                str(root),
                "-",
            ],
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=float(os.environ.get("CKB_REAL_KEYWORD_PROVIDER_TIMEOUT", "150")),
            check=False,
        )
        if completed.returncode != 0 or not output_path.is_file():
            sys.stderr.write((completed.stderr or completed.stdout)[-4000:])
            raise SystemExit(completed.returncode or 70)
        provider_output = json.loads(output_path.read_text(encoding="utf-8"))
        usage = None
        for line in completed.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                usage = event["usage"]
        if usage is None:
            sys.stderr.write("codex provider did not emit turn.completed usage\n")
            raise SystemExit(70)
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if (
            isinstance(input_tokens, bool)
            or not isinstance(input_tokens, int)
            or input_tokens < 0
            or isinstance(output_tokens, bool)
            or not isinstance(output_tokens, int)
            or output_tokens < 0
        ):
            sys.stderr.write("codex provider emitted invalid token usage\n")
            raise SystemExit(70)
        value = {
            **identity,
            "keywords": provider_output.get("keywords"),
            "anchors": provider_output.get("anchors"),
            "rewrites": provider_output.get("rewrites"),
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": 0.0,
            },
        }

sys.stdout.write(json.dumps(value, ensure_ascii=True, separators=(",", ":")))
