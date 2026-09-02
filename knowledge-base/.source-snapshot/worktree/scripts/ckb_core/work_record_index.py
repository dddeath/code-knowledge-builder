"""Human-first navigation for durable Agent work records.

The index treats every analysis, change, pitfall, experiment, and session note
uniformly.  It never receives task-specific keywords or a hand-picked result
set; titles and one-line descriptions come from the existing reviewed notes.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .common import CkbError, json_write
from .obsidian import NOTE_DIRECTORIES


WORK_RECORD_INDEX = "RECORDS.md"
WORK_RECORD_TAG = "#类型/导览"
LONG_HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{40,}(?![0-9A-Fa-f])")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
SECTIONS = {
    "analysis": ("分析与决策", "查找已经形成的结论、方案比较、边界和后续判断。"),
    "changes": ("实现与变更", "查找已经修改的内容、修改原因、验证结果和交付范围。"),
    "experiments": ("实验与量化结果", "查找测试协议、性能数字、对照结果和适用限制。"),
    "pitfalls": ("踩坑与限制", "查找失败原因、环境差异、规避条件和复现入口。"),
    "sessions": ("会话与任务过程", "查找一次任务的目标、执行范围、结果和待继续事项。"),
}
SECTION_ORDER = ("analysis", "changes", "experiments", "pitfalls", "sessions")


def _contains_chinese(value: str) -> bool:
    return len(CHINESE_RE.findall(value)) >= 2


def _title(text: str, fallback: str) -> str:
    first = text.splitlines()[0] if text else ""
    return first.removeprefix("# ").strip() or fallback


def _plain_text(value: str) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]", r"\1", value)
    value = re.sub(r"[`*>#]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _first_narrative(text: str) -> str:
    if "\n## 后续补充\n" in text:
        text = text.rsplit("\n## 后续补充\n", 1)[1]
    paragraphs: list[str] = []
    current: list[str] = []
    fenced = False
    for raw in text.splitlines()[1:]:
        line = raw.strip()
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if line.startswith(("#", "标签：", "- [[", "- [打开源码：", "|", "<!--")):
            continue
        if re.match(r"^[-*+]\s+", line) or re.match(r"^\d+[.)]\s+", line):
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    for paragraph in paragraphs:
        value = _plain_text(paragraph)
        if not _contains_chinese(value):
            continue
        sentence = re.match(r"^(.{12,140}?[。！？；])(?:\s|$)", value)
        if sentence:
            return sentence.group(1)
        if len(value) <= 120:
            return value
        return value[:117].rstrip("，、；： ") + "……"
    return "本记录保存一次经过审阅的任务结论、实现变化或验证结果。"


def collect_work_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for directory in SECTION_ORDER:
        for path in sorted((root / directory).glob("*.md"), key=lambda item: item.name.casefold()):
            text = path.read_text(encoding="utf-8-sig")
            title = _title(text, path.stem)
            if title == "工作记录导览":
                raise CkbError("work record title conflicts with generated navigation: 工作记录导览")
            if title in seen_titles:
                raise CkbError(f"work record title must be unique: {title}")
            seen_titles.add(title)
            records.append(
                {
                    "title": title,
                    "directory": directory,
                    "file": path.relative_to(root).as_posix(),
                    "summary": _first_narrative(text),
                }
            )
    return records


def render_work_record_index(root: Path) -> tuple[str, list[dict[str, Any]]]:
    records = collect_work_records(root)
    lines = [
        "# 工作记录导览",
        "",
        f"标签：{WORK_RECORD_TAG}",
        "",
        "> 这里按任务目的汇总全部分析、变更、实验、踩坑和会话记录；每条记录都使用同一套确定性规则进入导览。",
        "",
        "## 先按任务选择",
        "",
        "- 需要理解已有结论或设计边界时，查看“分析与决策”。",
        "- 需要确认已经修改什么以及如何验证时，查看“实现与变更”。",
        "- 需要比较性能、召回、上下文或其他量化结果时，查看“实验与量化结果”。",
        "- 需要避开已知失败和环境差异时，查看“踩坑与限制”。",
        "- 需要恢复一次任务的上下文时，查看“会话与任务过程”。",
        "",
        "## 快速查找",
        "",
        "在 Obsidian 中先使用本页标题浏览；记录较多时，再用核心搜索输入任务中的两个或三个稳定关键词。需要定位源码时，转到首页的确定性检索入口。",
        "",
    ]
    from .research_gaps import gap_navigation_counts

    gap_counts = gap_navigation_counts(root)
    if gap_counts is not None:
        lines.extend(
            [
                "## 研究缺口与待补来源",
                "",
                "这里仅汇总待验证主张，不把缺口写成已确认事实，也不为每个缺口创建页面。使用 `gaps list` 查看机器记录和证据路径。",
                "",
                f"- 当前共 {gap_counts['total']} 项：待补证据 {gap_counts['open']} 项，暂缓 {gap_counts['deferred']} 项，已关闭 {gap_counts['resolved']} 项。",
                "",
            ]
        )
    by_directory = {directory: [] for directory in NOTE_DIRECTORIES}
    for record in records:
        by_directory[record["directory"]].append(record)
    for directory in SECTION_ORDER:
        heading, description = SECTIONS[directory]
        lines.extend([f"## {heading}", "", description, ""])
        items = by_directory[directory]
        if items:
            lines.extend(f"- [[{item['title']}]] — {item['summary']}" for item in items)
        else:
            lines.append("- 当前没有这一类记录。")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", records


def write_work_record_index(root: Path) -> dict[str, Any]:
    text, records = render_work_record_index(root)
    target = root / WORK_RECORD_INDEX
    target.write_text(text, encoding="utf-8", newline="\n")
    return {
        "status": "ready",
        "file": str(target.resolve()),
        "record_count": len(records),
        "sections": {directory: sum(1 for item in records if item["directory"] == directory) for directory in NOTE_DIRECTORIES},
    }


def refresh_work_record_index(output: Path) -> dict[str, Any]:
    markdown = output / "markdown"
    human = output / "human"
    if not markdown.is_dir() or not human.is_dir():
        raise CkbError("work record navigation requires human and markdown roots")
    text, records = render_work_record_index(markdown)
    for root in (markdown, human):
        (root / WORK_RECORD_INDEX).write_text(text, encoding="utf-8", newline="\n")
    audit = audit_work_record_index(output)
    json_write(output / "workspace-meta/work-record-index-audit.json", audit)
    if audit["status"] != "passed":
        raise CkbError(f"work record navigation audit failed: {audit['errors'][:10]}")
    return {"status": "passed", "record_count": len(records), "audit": audit}


def audit_work_record_root(root: Path) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    target = root / WORK_RECORD_INDEX
    try:
        expected, records = render_work_record_index(root)
    except CkbError as exc:
        return {"status": "failed", "record_count": 0, "errors": [{"reason": "work-record-collection", "detail": str(exc)}]}
    if not target.is_file():
        errors.append({"reason": "work-record-index-missing"})
        actual = ""
    else:
        actual = target.read_text(encoding="utf-8-sig")
        if actual != expected:
            errors.append({"reason": "work-record-index-stale"})
        if actual.startswith("---\n"):
            errors.append({"reason": "work-record-index-frontmatter"})
        if actual.count(WORK_RECORD_TAG) != 1:
            errors.append({"reason": "work-record-index-tag", "count": actual.count(WORK_RECORD_TAG)})
        if LONG_HEX.search(actual):
            errors.append({"reason": "work-record-index-hash"})
    expected_titles = {item["title"] for item in records}
    linked_titles = set(re.findall(r"\[\[([^\]|#]+)", actual))
    if linked_titles != expected_titles:
        errors.append(
            {
                "reason": "work-record-index-link-set",
                "missing": sorted(expected_titles - linked_titles),
                "extra": sorted(linked_titles - expected_titles),
            }
        )
    missing_summaries = [item["title"] for item in records if not _contains_chinese(item["summary"])]
    if missing_summaries:
        errors.append({"reason": "work-record-index-summary-not-chinese", "titles": missing_summaries})
    return {
        "status": "passed" if not errors else "failed",
        "record_count": len(records),
        "linked_record_count": len(linked_titles & expected_titles),
        "section_counts": {directory: sum(1 for item in records if item["directory"] == directory) for directory in NOTE_DIRECTORIES},
        "errors": errors,
    }


def audit_work_record_index(output: Path) -> dict[str, Any]:
    markdown = output / "markdown"
    human = output / "human"
    result = audit_work_record_root(markdown)
    errors = list(result["errors"])
    left = markdown / WORK_RECORD_INDEX
    right = human / WORK_RECORD_INDEX
    if not left.is_file() or not right.is_file():
        errors.append({"reason": "work-record-index-mirror-missing"})
    elif left.read_bytes() != right.read_bytes():
        errors.append({"reason": "work-record-index-mirror-differs"})
    return {**result, "status": "passed" if not errors else "failed", "errors": errors}
