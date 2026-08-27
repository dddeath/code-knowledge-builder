"""Package completed human-readable projections as a portable Chinese showcase."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile
from typing import Any

from . import VERSION
from .common import CkbError, json_load, sha256_file


SHOWCASE_PREFIX = f"code-knowledge-builder-human-readable-showcase-{VERSION}"


def _parse_sample(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise CkbError(f"showcase sample must use LABEL=OUTPUT: {value}")
    label, raw = value.split("=", 1)
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-.")
    if not label or not raw.strip():
        raise CkbError(f"showcase sample must use LABEL=OUTPUT: {value}")
    return label, Path(raw).resolve()


def _root_wiki(samples: list[dict[str, Any]]) -> str:
    lines = [
        "# Code Knowledge Builder 人类可读展示",
        "",
        "> 这些样例展示如何把完整机器知识库投影成面向人的简体中文类、函数和职责聚合页面。",
        "",
        "## 展示内容",
        "",
    ]
    lines.extend(f"- [{item['title']}]({item['label']}/INDEX.md)" for item in samples)
    lines.extend(
        [
            "",
            "## 阅读重点",
            "",
            "1. 页面标题直接使用类名、函数名或职责名称，不添加技术前缀。",
            "2. 页面没有内部 ID、版本哈希、分类和解析器属性。",
            "3. 辅助实现按样例配置收纳在折叠或展开附录中，每项只有符号和一句话作用。",
            "4. 每页只有一个页面类型标签，源码位置提供可点击的本地编辑器链接。",
            "5. 双链关系使用自然中文描述，不展示机器关系类型和计数。",
            "6. 分析、变更、踩坑、实验和会话笔记保存在独立目录，并主动链接代码知识页。",
            "7. 每个样例都附有规范化页面配置、中文阅读 Wiki、Graphify 职责群导览和可读性审计结果。",
            "8. 所有叙述使用简体中文；英文只保留在专有名词、API、代码符号、命令和路径中。",
            "",
            "## 机器与人类分层",
            "",
            "完整构建输出中的 `machine/knowledge.sqlite` 保存全部实体、关系、源码范围、中文分节和过程记录；本展示包只携带受页面配额约束的人类阅读层。Agent 日常定位使用纯确定性的 `fast` 检索，复杂跨模块问题使用同样可重复的 `precise` 检索；向量模型留在后续 benchmark 阶段。",
            "",
            "## 真实性边界",
            "",
            "展示包只携带人类阅读层。完整 Skill 输出仍在机器审计层保存来源、实体、关系和审阅证据，并在这些门全部通过后才标记完成。",
            "",
        ]
    )
    return "\n".join(lines)


def package_showcase(dist: Path, sample_values: list[str]) -> dict[str, Any]:
    if not sample_values:
        raise CkbError("showcase requires at least one --sample LABEL=OUTPUT")
    samples: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in sample_values:
        label, output = _parse_sample(value)
        if label in seen:
            raise CkbError(f"duplicate showcase label: {label}")
        seen.add(label)
        complete = output / ".complete"
        markdown = output / "human" if (output / "human/projection.json").is_file() else output / "markdown"
        readability_path = markdown / "readability-audit.json"
        if not complete.is_file() or json_load(complete).get("status") != "complete":
            raise CkbError(f"showcase sample is not complete: {output}")
        if not readability_path.is_file() or json_load(readability_path).get("status") != "passed":
            raise CkbError(f"showcase sample has not passed human readability: {output}")
        for required in (
            output / "page-config.json",
            markdown / "INDEX.md",
            markdown / "WIKI.md",
            markdown / "pages",
            output / "graphify-out/GRAPH_REPORT.md",
            markdown / "logseq/config.edn",
            markdown / ".obsidian/app.json",
            markdown / ".obsidian/core-plugins.json",
            markdown / ".obsidian/appearance.json",
            markdown / ".obsidian/snippets/ckb.css",
        ):
            if not required.exists():
                raise CkbError(f"showcase sample artifact is missing: {required}")
        title = markdown.joinpath("INDEX.md").read_text(encoding="utf-8").splitlines()[0].removeprefix("# ").strip()
        samples.append({"label": label, "output": output, "title": title, "readability": json_load(readability_path)})

    files: dict[str, bytes] = {"WIKI.md": _root_wiki(samples).encode("utf-8")}
    for sample in samples:
        label = sample["label"]
        output: Path = sample["output"]
        markdown = output / "human" if (output / "human/projection.json").is_file() else output / "markdown"
        files[f"{label}/INDEX.md"] = (markdown / "INDEX.md").read_bytes()
        wiki = (markdown / "WIKI.md").read_text(encoding="utf-8").replace(
            "[项目关系导览](../graphify-out/GRAPH_REPORT.md)",
            "[项目关系导览](项目关系导览.md)",
        )
        files[f"{label}/WIKI.md"] = wiki.encode("utf-8")
        files[f"{label}/项目关系导览.md"] = (output / "graphify-out/GRAPH_REPORT.md").read_bytes()
        files[f"{label}/page-config.json"] = (output / "page-config.json").read_bytes()
        files[f"{label}/readability-audit.json"] = json.dumps(sample["readability"], ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        files[f"{label}/logseq/config.edn"] = (markdown / "logseq/config.edn").read_bytes()
        for relative in (".obsidian/app.json", ".obsidian/core-plugins.json", ".obsidian/appearance.json", ".obsidian/snippets/ckb.css"):
            files[f"{label}/{relative}"] = (markdown / relative).read_bytes()
        for page in sorted((markdown / "pages").glob("*.md")):
            files[f"{label}/pages/{page.name}"] = page.read_bytes()
        for directory in ("analysis", "changes", "pitfalls", "experiments", "sessions"):
            for note in sorted((markdown / directory).glob("*.md")):
                files[f"{label}/{directory}/{note.name}"] = note.read_bytes()

    markdown_text = "\n".join(data.decode("utf-8") for path, data in files.items() if path.endswith(".md"))
    if re.search(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", markdown_text, flags=re.IGNORECASE):
        raise CkbError("showcase Markdown exposes a commit identifier")
    if any(line.startswith(("# 实体 ·", "# 文件 ·", "# 模块 ·", "# 仓库 ·", "# 边界 ·")) for line in markdown_text.splitlines()):
        raise CkbError("showcase Markdown exposes a technical page prefix")
    if "\n---\n" in "\n" + markdown_text or markdown_text.startswith("---\n"):
        raise CkbError("showcase Markdown exposes frontmatter")

    manifest_files = [
        {"path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for path, data in sorted(files.items())
    ]
    manifest = {
        "schema_version": 1,
        "name": "code-knowledge-builder-human-readable-showcase",
        "version": VERSION,
        "status": "passed",
        "language": "zh-CN",
        "samples": [{"label": item["label"], "title": item["title"], "readability_status": item["readability"]["status"]} for item in samples],
        "files": manifest_files,
    }
    files["MANIFEST.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    dist = dist.resolve()
    dist.mkdir(parents=True, exist_ok=True)
    archive = dist / f"{SHOWCASE_PREFIX}.zip"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative, data in sorted(files.items()):
            info = zipfile.ZipInfo(str(PurePosixPath(SHOWCASE_PREFIX) / PurePosixPath(relative)), date_time=(2026, 8, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip():
            raise CkbError("showcase ZIP CRC verification failed")
        archived = json.loads(bundle.read(f"{SHOWCASE_PREFIX}/MANIFEST.json"))
        if archived != manifest:
            raise CkbError("showcase manifest changed during packaging")
    result = {
        "status": "passed",
        "archive": str(archive),
        "size": archive.stat().st_size,
        "sha256": sha256_file(archive),
        "sample_count": len(samples),
        "human_file_count": len(files),
        "manifest": manifest,
    }
    external = dist / f"{SHOWCASE_PREFIX}.manifest.json"
    external.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result
