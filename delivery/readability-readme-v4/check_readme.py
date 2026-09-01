#!/usr/bin/env python3
"""Deterministic acceptance checks for the human-first README rewrite."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


EXPECTED_SAMPLE_SHA256 = "c2bca48989e740130e2bfaba4011ea61d264cb26e774fcb94dbed1f2a3663ea5"
EXPECTED_SAMPLE_BYTES = 5467
EXPECTED_BASELINE_SHA256 = "63b5f320d600f92c4aa83dc71aa45f464773e685c5706b41f1b71d7c04ac0135"
EXPECTED_README_SHA256 = "255ff54a543a1658da678fc6bdfb4b526b58bce6ebd55d0a620c1ea2891c0b8a"
EXPECTED_H2 = [
    "先选择你要完成的任务",
    "了解本项目知识库结构",
    "让 Agent 安装本项目",
    "让 Agent 解释自己的项目",
]
EXPECTED_H3 = ["安装后的解释与使用", "建库后的维护"]
OLD_OVERLAP_HEADINGS = ["五分钟开始", "发布目录分别保存什么", "阅读现有知识库", "构建新的知识库", "进一步阅读"]
OLD_READER_TERMS = ["普通读者", "普通用户", "最终用户", "读者"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dotted(value: dict[str, Any], key: str) -> Any:
    current: Any = value
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def github_slug(title: str) -> str:
    value = re.sub(r"\s+", "-", title.strip().lower())
    return re.sub(r"[^\w\-\u4e00-\u9fff]", "", value)


def headings_outside_fences(lines: list[str]) -> tuple[list[dict[str, Any]], list[int], bool]:
    headings: list[dict[str, Any]] = []
    fence_lines: list[int] = []
    fence: str | None = None
    for line_number, line in enumerate(lines, 1):
        fence_match = re.match(r"^(```+|~~~+)", line)
        if fence_match:
            marker = fence_match.group(1)
            fence_lines.append(line_number)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is not None:
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            headings.append({"line": line_number, "level": len(heading.group(1)), "title": heading.group(2)})
    return headings, fence_lines, fence is None


def main() -> int:
    parser = argparse.ArgumentParser()
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--sample", type=Path)
    parser.add_argument("--claims", type=Path)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    artifact = root / "delivery/readability-readme-v4"
    readme = root / "README.md"
    sample = args.sample.resolve() if args.sample else None
    claims_path = (args.claims or artifact / "supported-claims.json").resolve()
    baseline = artifact / "README.baseline.md"
    publication_path = root / "publication-manifest.json"

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    required_inputs = [readme, claims_path, baseline, publication_path]
    if sample is not None:
        required_inputs.append(sample)
    missing_inputs = [str(path) for path in required_inputs if not path.is_file()]
    check("required-inputs", not missing_inputs, {"missing": missing_inputs})
    if missing_inputs:
        result = {"schema_version": 1, "status": "failed", "root": str(root), "checks": checks}
        print("README_CHECK status=failed checks=0/1 reason=missing-input")
        return 5

    readme_bytes = readme.read_bytes()
    sample_bytes = sample.read_bytes() if sample is not None else readme_bytes[:EXPECTED_SAMPLE_BYTES]
    text = readme_bytes.decode("utf-8")
    lines = text.splitlines()
    sample_text = sample_bytes.decode("utf-8")
    publication = load_json(publication_path)
    claims = load_json(claims_path)

    check(
        "approved-first-screen-sha256",
        hashlib.sha256(sample_bytes).hexdigest() == EXPECTED_SAMPLE_SHA256
        and len(sample_bytes) == EXPECTED_SAMPLE_BYTES,
        {
            "expected": EXPECTED_SAMPLE_SHA256,
            "actual": hashlib.sha256(sample_bytes).hexdigest(),
            "bytes": len(sample_bytes),
            "source": str(sample) if sample is not None else "README.md byte prefix",
        },
    )
    check(
        "first-screen-byte-prefix",
        readme_bytes.startswith(sample_bytes),
        {"sample_bytes": len(sample_bytes), "readme_bytes": len(readme_bytes)},
    )
    check(
        "baseline-readme-sha256",
        sha256(baseline) == EXPECTED_BASELINE_SHA256,
        {"expected": EXPECTED_BASELINE_SHA256, "actual": sha256(baseline)},
    )
    check(
        "modified-readme-sha256",
        sha256(readme) == EXPECTED_README_SHA256,
        {"expected": EXPECTED_README_SHA256, "actual": sha256(readme)},
    )

    headings, fence_lines, fences_closed = headings_outside_fences(lines)
    titles = [item["title"] for item in headings]
    h2 = [item["title"] for item in headings if item["level"] == 2]
    h3 = [item["title"] for item in headings if item["level"] == 3]
    check("unique-headings", len(titles) == len(set(titles)), {"headings": headings})
    check("three-task-entry-sections", h2 == EXPECTED_H2, {"expected": EXPECTED_H2, "actual": h2})
    check("advanced-stage-sections", h3 == EXPECTED_H3, {"expected": EXPECTED_H3, "actual": h3})

    current_h3: str | None = None
    unclassified_h4: list[dict[str, Any]] = []
    for item in headings:
        if item["level"] == 3:
            current_h3 = item["title"]
        elif item["level"] == 4 and current_h3 not in EXPECTED_H3:
            unclassified_h4.append(item)
    check("advanced-headings-classified", not unclassified_h4, {"unclassified": unclassified_h4})

    anchors = {github_slug(item["title"]) for item in headings}
    nav = re.findall(r"\[[^\]]+\]\(#([^)]+)\)", sample_text)
    check(
        "task-navigation-anchors",
        len(nav) == 3 and all(anchor in anchors for anchor in nav),
        {"navigation": nav, "available": sorted(anchors)},
    )

    missing_links: list[dict[str, Any]] = []
    link_labels: list[str] = []
    relative_link_count = 0
    for line_number, line in enumerate(lines, 1):
        for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", line):
            link_labels.append(label.strip())
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_link_count += 1
            relative = target.split("#", 1)[0]
            if not (root / relative).resolve().is_file():
                missing_links.append({"line": line_number, "target": target})
    check("relative-links", not missing_links, {"count": relative_link_count, "missing": missing_links})
    isolated_labels = [label for label in link_labels if label in {"这里", "详情", "继续浏览"}]
    check("descriptive-link-labels", not isolated_labels, {"isolated": isolated_labels})

    details_open = text.count("<details>")
    details_close = text.count("</details>")
    summary_open = text.count("<summary>")
    summary_close = text.count("</summary>")
    check(
        "folding-blocks-closed",
        details_open == details_close == summary_open == summary_close == 2,
        {
            "details_open": details_open,
            "details_close": details_close,
            "summary_open": summary_open,
            "summary_close": summary_close,
        },
    )
    check("fenced-blocks-closed", fences_closed and len(fence_lines) % 2 == 0, {"fence_lines": fence_lines})

    check(
        "old-overlap-headings-absent",
        all(title not in titles for title in OLD_OVERLAP_HEADINGS),
        {"forbidden": OLD_OVERLAP_HEADINGS},
    )
    reader_hits = [term for term in OLD_READER_TERMS if term in text]
    check("human-reader-wording", not reader_hits, {"forbidden_hits": reader_hits, "required": "人类"})
    check(
        "single-install-flow",
        "git clone --branch" not in text
        and "git lfs install" not in text
        and text.count("请安装 Code Knowledge Builder 项目及其 code-knowledge-builder Skill。") == 1,
        {
            "install_prompt_count": text.count("请安装 Code Knowledge Builder 项目及其 code-knowledge-builder Skill。"),
            "manual_clone_present": "git clone --branch" in text,
        },
    )

    fence = "`" * 3
    install_start = text.index("请安装 Code Knowledge Builder 项目及其 code-knowledge-builder Skill。")
    install_prompt = text[install_start : text.index(fence, install_start)]
    explain_start = text.index("请使用已安装的 $code-knowledge-builder")
    explain_prompt = text[explain_start : text.index(fence, explain_start)]
    check(
        "prompt-role-separation",
        "不要为其他仓库建立知识库" in install_prompt
        and "不重复安装 Code Knowledge Builder" in explain_prompt
        and "下载指定发布分支" not in explain_prompt,
        {
            "install_prompt_sha256": hashlib.sha256(install_prompt.encode("utf-8")).hexdigest(),
            "explain_prompt_sha256": hashlib.sha256(explain_prompt.encode("utf-8")).hexdigest(),
        },
    )

    advanced_index = text.index("### 安装后的解释与使用")
    definitions = text[len(sample_text) : advanced_index]
    required_definitions = [
        "`Skill` 是 Agent 可发现",
        "`Git LFS`（Git Large File Storage）用于",
        "`Harness` 是承载 Agent 会话",
    ]
    check(
        "term-definitions-before-advanced-use",
        all(value in definitions for value in required_definitions),
        {"required": required_definitions},
    )
    check(
        "task-order",
        text.index("## 了解本项目知识库结构")
        < text.index("## 让 Agent 安装本项目")
        < text.index("## 让 Agent 解释自己的项目")
        < advanced_index
        < text.index("### 建库后的维护"),
        {"status": "ordered"},
    )

    claim_results: list[dict[str, Any]] = []
    for claim in claims.get("claims", []):
        errors: list[dict[str, Any]] = []
        for needle in claim.get("readme_contains", []):
            if needle not in text:
                errors.append({"reason": "readme-needle-missing", "needle": needle})
        for key, expected in claim.get("manifest_fields", {}).items():
            actual = dotted(publication, key)
            if actual != expected:
                errors.append({"reason": "manifest-field", "field": key, "expected": expected, "actual": actual})
        for evidence in claim.get("evidence", []):
            path = root / evidence["path"]
            if not path.is_file():
                errors.append({"reason": "evidence-file-missing", "path": evidence["path"]})
                continue
            evidence_text = path.read_text(encoding="utf-8-sig")
            for needle in evidence.get("contains", []):
                if needle not in evidence_text:
                    errors.append({"reason": "evidence-needle-missing", "path": evidence["path"], "needle": needle})
        claim_results.append({"id": claim.get("id"), "passed": not errors, "errors": errors})
    check("supported-claims", bool(claim_results) and all(item["passed"] for item in claim_results), claim_results)

    failed = [item for item in checks if not item["passed"]]
    result = {
        "schema_version": 1,
        "status": "passed" if not failed else "failed",
        "root": str(root),
        "inputs": {
            "readme": str(readme),
            "readme_sha256": sha256(readme),
            "sample": str(sample) if sample is not None else "README.md byte prefix",
            "sample_sha256": hashlib.sha256(sample_bytes).hexdigest(),
            "baseline": str(baseline),
            "baseline_sha256": sha256(baseline),
            "publication_manifest": str(publication_path),
            "publication_manifest_sha256": sha256(publication_path),
            "supported_claims": str(claims_path),
            "supported_claims_sha256": sha256(claims_path),
        },
        "summary": {"passed": len(checks) - len(failed), "failed": len(failed), "total": len(checks)},
        "checks": checks,
    }
    if args.write:
        target = args.write if args.write.is_absolute() else root / args.write
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        reopened = load_json(target)
        if reopened.get("status") != result["status"] or reopened.get("summary") != result["summary"]:
            raise RuntimeError("README verification record did not reopen with the verified state")
    summary = result["summary"]
    print(
        f"README_CHECK status={result['status']} "
        f"checks={summary['passed']}/{summary['total']} failed={summary['failed']} "
        f"readme_sha256={result['inputs']['readme_sha256']}"
    )
    return 0 if result["status"] == "passed" else 5


if __name__ == "__main__":
    raise SystemExit(main())
