#!/usr/bin/env python3
"""Rebuild the Claudian-based Obsidian companion from pinned source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def background_process_options() -> dict[str, int]:
    if os.name != "nt":
        return {}
    creation_flag = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return {"creationflags": creation_flag} if creation_flag else {}


def run(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **background_process_options(),
    )
    record: dict[str, object] = {
        "command": command,
        "cwd": str(cwd.resolve()),
        "exit_status": completed.returncode,
        "output": completed.stdout,
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(record, ensure_ascii=False, indent=2))
    return record


def copy_overlay(work: Path) -> None:
    overlay = ROOT / "overlay"
    for source in sorted(overlay.rglob("*")):
        if not source.is_file():
            continue
        target = work / source.relative_to(overlay)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def validate_selection_provider_routing(work: Path) -> None:
    service = (work / "src/features/selection-learning/SelectionLearningService.ts").read_text(
        encoding="utf-8",
    )
    provider = (work / "src/features/selection-learning/SelectionLearningProvider.ts").read_text(
        encoding="utf-8",
    )
    settings = (work / "src/features/settings/ClaudianSettings.ts").read_text(
        encoding="utf-8",
    )
    registry = (work / "src/core/providers/ProviderRegistry.ts").read_text(
        encoding="utf-8",
    )
    inline_edit = (work / "src/core/auxiliary/InlineEditService.ts").read_text(
        encoding="utf-8",
    )
    controller = (work / "src/core/auxiliary/AuxiliarySessionController.ts").read_text(
        encoding="utf-8",
    )
    view = (work / "src/features/selection-learning/SelectionLearningView.ts").read_text(
        encoding="utf-8",
    )
    main = (work / "src/main.ts").read_text(encoding="utf-8")
    codex_support = (work / "src/providers/codex/runtime/codexAppServerSupport.ts").read_text(
        encoding="utf-8",
    )
    stdio_client = (work / "src/features/selection-learning/CkbStdioClient.ts").read_text(
        encoding="utf-8",
    )
    markers = {
        "SelectionLearningService.ts": (
            "resolveSelectionLearningProviderContext(this.plugin.settings)",
            "ProviderRegistry.createSelectionLearningService(",
            "service.setModelOverride?.(providerContext.modelOverride)",
            "providerLabel,",
            "CKB_PRODUCT_NAME = 'CKB'",
            "正在检索知识库",
            "CKB 解释失败：",
            "this.progress.setStage({",
            "this.progress.complete(audited.explanation, learningFile.path)",
            "service.setProgressCallback?.((text)",
            "禁止调用任何工具、Shell、grep、ripgrep、文件读取、Skill 或子 Agent",
            "this.stdio.recordExplanation({",
            "workspace-meta${path.sep}stdio${path.sep}explanations",
            "不得创建 analysis 页面",
            "buildSelectionFollowUpInstruction(",
            "service.continueConversation(",
            "followUp: true",
            "setFollowUpHandler(question => this.followUp(question))",
            "---CKB_AGENT_PACK---",
            "retrievalRequestId: retrieval.requestId",
        ),
        "SelectionLearningProvider.ts": (
            "resolveNewConversationModel(settings)",
            "source: 'default-model'",
            "source: 'fixed-provider'",
        ),
        "ClaudianSettings.ts": (
            "右键解释 provider",
            "FOLLOW_DEFAULT_SELECTION_PROVIDER",
            "selectionLearningProvider = value",
        ),
        "ProviderRegistry.ts": (
            "createSelectionLearningService(",
            "externalWorkspaceRoots: [outputRoot]",
            "toolPolicy: { kind: 'passive' }",
        ),
        "InlineEditService.ts": (
            "externalWorkspaceRoots: this.externalWorkspaceRoots",
            "options.toolPolicy ?? { kind: 'read-only' }",
        ),
        "AuxiliarySessionController.ts": (
            "externalWorkspaceRoots?: readonly string[]",
            "externalWorkspaceRoots: request.externalWorkspaceRoots",
        ),
        "SelectionLearningView.ts": (
            "SELECTION_LEARNING_VIEW_TYPE = 'ckb-selection-learning-view'",
            "workspace.getRightLeaf(true)",
            "MarkdownRenderer.render(",
            "生成中的解释",
            "执行过程",
            "CKB_PRODUCT_NAME = 'CKB'",
            "retrieve --profile fast",
            "知识库检索证据",
            "继续追问",
            "追问并记录",
            "submitFollowUp(question)",
        ),
        "main.ts": (
            "new SelectionLearningViewController(this.app)",
            "new SelectionLearningView(",
            "id: 'open-selection-learning-view'",
        ),
        "codexAppServerSupport.ts": (
            "mergeWslEnvironmentPassThrough",
            "WSLENV: wslEnv",
            "normalized === 'PATH'",
        ),
        "CkbStdioClient.ts": (
            "parseCkbOutputContract",
            "path.join(vaultRoot, '.ckb', 'output-contract.json')",
            "code-knowledge-builder-output",
            "CKB 输出契约无效",
            "PYTHONIOENCODING: 'utf-8'",
            "PYTHONUTF8: '1'",
        ),
    }
    source_by_name = {
        "SelectionLearningService.ts": service,
        "SelectionLearningProvider.ts": provider,
        "ClaudianSettings.ts": settings,
        "ProviderRegistry.ts": registry,
        "InlineEditService.ts": inline_edit,
        "AuxiliarySessionController.ts": controller,
        "SelectionLearningView.ts": view,
        "main.ts": main,
        "codexAppServerSupport.ts": codex_support,
        "CkbStdioClient.ts": stdio_client,
    }
    for name, required in markers.items():
        for marker in required:
            if marker not in source_by_name[name]:
                raise RuntimeError(f"selection Provider routing marker is missing from {name}: {marker}")


def npm_command(node: Path, npm_cli: Path, *args: str) -> list[str]:
    return [str(node.resolve()), str(npm_cli.resolve()), *args]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--npm-cli", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    lock = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
    os.environ["PATH"] = str(args.node.resolve().parent) + os.pathsep + os.environ.get("PATH", "")
    work = args.work.resolve()
    output = args.out.resolve()
    if work.exists():
        if not args.force:
            raise RuntimeError(f"build work directory already exists: {work}")
        shutil.rmtree(work)
    work.parent.mkdir(parents=True, exist_ok=True)
    logs: list[dict[str, object]] = []
    logs.append(run(["git", "clone", lock["claudian"]["url"], str(work)], work.parent))
    logs.append(run(["git", "checkout", "--detach", lock["claudian"]["commit"]], work))
    actual_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=work,
        text=True,
        encoding="utf-8",
        **background_process_options(),
    ).strip()
    if actual_commit != lock["claudian"]["commit"]:
        raise RuntimeError(f"Claudian commit differs: {actual_commit}")
    logs.append(run(["git", "apply", str((ROOT / "patches/claudian-base.patch").resolve())], work))
    copy_overlay(work)
    validate_selection_provider_routing(work)

    logs.append(run(npm_command(args.node, args.npm_cli, "ci"), work))
    logs.append(run(npm_command(args.node, args.npm_cli, "run", "typecheck"), work))
    logs.append(run(npm_command(args.node, args.npm_cli, "run", "lint"), work))
    logs.append(
        run(
            npm_command(
                args.node,
                args.npm_cli,
                "run",
                "test:unit",
                "--",
                "--runTestsByPath",
                "tests/unit/features/selection-learning/LearningNoteDocument.test.ts",
                "tests/unit/features/selection-learning/SelectionLearningProvider.test.ts",
                "tests/unit/features/selection-learning/SelectionLearningProgress.test.ts",
                "tests/unit/features/settings/ClaudianSettings.display.test.ts",
                "tests/unit/providers/codex/runtime/codexAppServerSupport.test.ts",
                "--runInBand",
            ),
            work,
        )
    )
    logs.append(run(npm_command(args.node, args.npm_cli, "run", "build"), work))

    output.mkdir(parents=True, exist_ok=True)
    for name in ("main.js", "styles.css"):
        shutil.copy2(work / name, output / name)
    for name in ("manifest.json", "LICENSE", "NOTICE.md", "deploy.py"):
        shutil.copy2(ROOT / name, output / name)
    required = ("main.js", "styles.css", "manifest.json", "LICENSE", "NOTICE.md", "deploy.py")
    files = []
    for name in required:
        path = output / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"plugin artifact is missing: {path}")
        files.append(
            {
                "path": name,
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    main_text = (output / "main.js").read_text(encoding="utf-8", errors="replace")
    for marker in (
        "explain-selection-to-daily-note",
        "open-today-learning-note",
        "editor-menu",
        "markdown-preview-view",
        "promptReadingSelection",
        "使用知识库解释选中文本",
        "右键解释 provider",
        "follow-default",
        "lastSelectedChatModel",
        "CKB_RETRIEVAL: passed",
        "CKB_GENERATION: passed",
        "CKB_STDIO_REQUEST:",
        "CKB_STDIO_PACK:",
        "record-explanation",
        "learning-explanation-evidence",
        "PYTHONIOENCODING",
        "不得创建 analysis 页面",
        "继续追问",
        "追问并记录",
        "保持同一 Provider 会话",
        "code-knowledge-builder-output",
        "output-contract.json",
        "---CKB_AGENT_PACK---",
        "禁止调用任何工具",
        "ckb-stdio-retrieval",
        "学习笔记",
        "ckb-selection-learning-view",
        "打开知识库解释视图",
        "生成中的解释",
        "知识库检索证据",
        "retrieve --profile fast",
        "正在检索知识库",
        "CKB 解释失败：",
    ):
        if marker not in main_text:
            raise RuntimeError(f"compiled plugin marker is missing: {marker}")
    record = {
        "schema_version": 1,
        "status": "passed",
        "claudian_commit": actual_commit,
        "files": files,
        "commands": logs,
    }
    (output / "build-record.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PLUGIN_BUILD_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
