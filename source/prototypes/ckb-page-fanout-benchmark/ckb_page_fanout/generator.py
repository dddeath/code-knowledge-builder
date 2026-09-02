from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
from typing import Any

from .contracts import (
    FanoutError,
    atomic_write_json,
    canonical_json_bytes,
    ensure_within,
    exact_keys,
    has_chinese,
    load_object,
    normalize_topic,
    sha256_file,
    tree_manifest,
    utf8_size,
    validate_contract,
    validate_identifier,
    validate_relative_path,
)


WIKI_LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _source_lines(source_root: Path, document: dict[str, Any]) -> tuple[Path, list[str]]:
    path = ensure_within(source_root / validate_relative_path(document["path"], "document.path"), source_root, "document.path")
    if not path.is_file():
        raise FanoutError("SOURCE_NOT_FOUND", str(path))
    expected = document["source_sha256"]
    actual = sha256_file(path)
    if actual != expected:
        raise FanoutError("SOURCE_DRIFT", f"{document['document_id']} expected={expected} actual={actual}")
    try:
        return path, path.read_text(encoding="utf-8").splitlines()
    except UnicodeError as exc:
        raise FanoutError("SOURCE_NOT_UTF8", str(path)) from exc


def _validate_candidate(candidate: dict[str, Any], document: dict[str, Any], lines: list[str]) -> dict[str, Any]:
    exact_keys(candidate, {"candidate_id", "term", "claim_zh", "source_range", "source_text"}, "candidate")
    candidate_id = validate_identifier(candidate["candidate_id"], "candidate_id")
    term = candidate["term"]
    claim = candidate["claim_zh"]
    source_text = candidate["source_text"]
    if not all(isinstance(value, str) and value.strip() for value in (term, claim, source_text)):
        raise FanoutError("INVALID_CANDIDATE", f"{candidate_id} 文本字段为空")
    if not has_chinese(claim):
        raise FanoutError("CLAIM_NOT_CHINESE", candidate_id)
    locator = exact_keys(candidate["source_range"], {"start_line", "end_line"}, "candidate.source_range")
    start = locator["start_line"]
    end = locator["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 1 or end < start or end > len(lines):
        raise FanoutError("SOURCE_RANGE_INVALID", candidate_id)
    actual = "\n".join(lines[start - 1 : end])
    if actual != source_text:
        raise FanoutError("SOURCE_RANGE_DRIFT", candidate_id)
    if claim != source_text:
        raise FanoutError("CLAIM_NOT_ENTAILED", candidate_id)
    if term not in actual:
        raise FanoutError("TERM_NOT_EXPLICIT", candidate_id)
    return {
        "candidate_id": candidate_id,
        "term": term.strip(),
        "claim_zh": claim.strip(),
        "source_path": document["path"],
        "source_sha256": document["source_sha256"],
        "start_line": start,
        "end_line": end,
        "source_text": source_text,
        "document_id": document["document_id"],
        "conservative_page": document["conservative_page"],
    }


def _validate_corpus(value: dict[str, Any], source_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exact_keys(value, {"schema_version", "scope", "documents"}, "corpus")
    if value["schema_version"] != 1 or value["scope"] != "isolated-page-fanout-benchmark":
        raise FanoutError("INVALID_CORPUS", "schema_version/scope 非法")
    if not isinstance(value["documents"], list) or len(value["documents"]) < 3:
        raise FanoutError("INVALID_CORPUS", "至少需要三类单文档输入")
    documents: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    seen_documents: set[str] = set()
    seen_candidates: set[str] = set()
    seen_categories: set[str] = set()
    for document in value["documents"]:
        exact_keys(
            document,
            {"document_id", "category", "path", "conservative_page", "origin", "license", "source_sha256", "candidates"},
            "document",
        )
        document_id = validate_identifier(document["document_id"], "document_id")
        category = validate_identifier(document["category"], "category")
        if document_id in seen_documents:
            raise FanoutError("DUPLICATE_DOCUMENT", document_id)
        if category in seen_categories:
            raise FanoutError("DUPLICATE_CATEGORY", category)
        seen_documents.add(document_id)
        seen_categories.add(category)
        validate_relative_path(document["conservative_page"], "document.conservative_page")
        if not isinstance(document["origin"], str) or not document["origin"].startswith("fixture://"):
            raise FanoutError("UNTRUSTED_FIXTURE_ORIGIN", document_id)
        if document["license"] != "CC0-1.0":
            raise FanoutError("UNREVIEWED_FIXTURE_LICENSE", document_id)
        if not isinstance(document["source_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", document["source_sha256"]):
            raise FanoutError("INVALID_SOURCE_HASH", document_id)
        _path, lines = _source_lines(source_root, document)
        if not isinstance(document["candidates"], list) or not document["candidates"]:
            raise FanoutError("EMPTY_CANDIDATES", document_id)
        for candidate in document["candidates"]:
            normalized = _validate_candidate(candidate, document, lines)
            if normalized["candidate_id"] in seen_candidates:
                raise FanoutError("DUPLICATE_CANDIDATE_ID", normalized["candidate_id"])
            seen_candidates.add(normalized["candidate_id"])
            candidates.append(normalized)
        documents.append(document)
    return documents, sorted(candidates, key=lambda item: (item["document_id"], item["candidate_id"]))


def _existing_titles(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*.md")):
        match = TITLE.search(path.read_text(encoding="utf-8"))
        if match:
            normalized = normalize_topic(match.group(1).strip())
            if normalized:
                result[normalized] = path.relative_to(root).as_posix()
    return result


def _render_concept(candidate: dict[str, Any]) -> str:
    start = candidate["start_line"]
    end = candidate["end_line"]
    line_label = f"{start}-{end}"
    reference = PurePosixPath(candidate["conservative_page"])
    backlink = PurePosixPath("../") / reference
    return (
        f"# {candidate['term']}\n\n"
        "本页是隔离 benchmark 从单一原文显式术语生成的候选页。\n\n"
        "## 来源主张\n\n"
        f"主张：{candidate['claim_zh']}\n"
        f"来源：`{candidate['source_path']}:{line_label}`\n"
        f"原文：{candidate['source_text']}\n\n"
        "## 导航\n\n"
        f"- [[{backlink.as_posix()}|返回单文档摘要]]\n"
    )


def _resolve_link(page: str, target: str) -> str:
    target_path = PurePosixPath(target)
    if target_path.suffix != ".md":
        target_path = target_path.with_suffix(".md")
    if target.startswith("/"):
        candidate = target_path.relative_to("/")
    else:
        candidate = PurePosixPath(page).parent / target_path
    stack: list[str] = []
    for part in candidate.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not stack:
                raise FanoutError("LINK_OUTSIDE_OUTPUT", f"{page} -> {target}")
            stack.pop()
        else:
            stack.append(part)
    return PurePosixPath(*stack).as_posix()


def _audit_links(root: Path, maximum: int) -> None:
    pages = {path.relative_to(root).as_posix() for path in root.rglob("*.md")}
    for page in sorted(pages):
        text = (root / page).read_text(encoding="utf-8")
        targets = WIKI_LINK.findall(text)
        if len(targets) > maximum:
            raise FanoutError("PAGE_LINK_QUOTA", f"{page} count={len(targets)} limit={maximum}")
        for target in targets:
            resolved = _resolve_link(page, target.strip())
            if resolved not in pages:
                raise FanoutError("BROKEN_LINK", f"{page} -> {resolved}")


def _reject(candidate: dict[str, Any], reason: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "document_id": candidate["document_id"],
        "term": candidate["term"],
        "reason": reason,
        "detail": detail,
    }


def generate_fanout(
    *,
    contract_path: Path,
    corpus_path: Path,
    source_root: Path,
    conservative_root: Path,
    output_root: Path,
    rollback_manifest: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    workspace = workspace_root.resolve()
    source = ensure_within(source_root, workspace, "source-root")
    conservative = ensure_within(conservative_root, workspace, "conservative-root")
    output = ensure_within(output_root, workspace, "out")
    rollback_path = ensure_within(rollback_manifest, workspace, "rollback-manifest")
    if output.exists():
        raise FanoutError("OUTPUT_EXISTS", str(output))
    if rollback_path.exists():
        raise FanoutError("ROLLBACK_MANIFEST_EXISTS", str(rollback_path))
    contract = validate_contract(load_object(contract_path, "contract"))
    corpus = load_object(corpus_path, "corpus")
    documents, candidates = _validate_corpus(corpus, source)
    baseline = tree_manifest(conservative)
    policy = contract["fanout_policy"]
    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        raise FanoutError("STAGING_EXISTS", str(staging))
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    accepted_by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    try:
        shutil.copytree(conservative, staging)
        titles = _existing_titles(staging)
        accepted_topics: list[tuple[str, str]] = []
        threshold = float(policy["duplicate_topic_similarity_threshold"])
        for candidate in candidates:
            normalized = normalize_topic(candidate["term"])
            if not normalized:
                raise FanoutError("INVALID_TOPIC", candidate["candidate_id"])
            if normalized in titles:
                rejected.append(_reject(candidate, "TITLE_CONFLICT", {"existing_page": titles[normalized]}))
                continue
            duplicate = None
            for topic, candidate_id in accepted_topics:
                score = SequenceMatcher(None, normalized, topic, autojunk=False).ratio()
                if score >= threshold:
                    duplicate = {"candidate_id": candidate_id, "similarity": round(score, 6), "threshold": threshold}
                    break
            if duplicate:
                rejected.append(_reject(candidate, "DUPLICATE_TOPIC", duplicate))
                continue
            document_count = len(accepted_by_document[candidate["document_id"]])
            if document_count >= int(policy["max_pages_per_document"]):
                rejected.append(
                    _reject(
                        candidate,
                        "DOCUMENT_PAGE_QUOTA",
                        {"count": document_count, "limit": int(policy["max_pages_per_document"])},
                    )
                )
                continue
            if len(accepted) >= int(policy["max_total_new_pages"]):
                rejected.append(
                    _reject(candidate, "GLOBAL_PAGE_QUOTA", {"count": len(accepted), "limit": int(policy["max_total_new_pages"])})
                )
                continue
            page = f"concepts/{candidate['candidate_id']}.md"
            if (staging / page).exists():
                rejected.append(_reject(candidate, "TITLE_CONFLICT", {"existing_page": page}))
                continue
            record = {**candidate, "page": page}
            accepted.append(record)
            accepted_by_document[candidate["document_id"]].append(record)
            accepted_topics.append((normalized, candidate["candidate_id"]))
            target = staging / page
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_render_concept(record), encoding="utf-8", newline="\n")

        for document in documents:
            values = accepted_by_document.get(document["document_id"], [])
            if not values:
                continue
            page = staging / document["conservative_page"]
            if not page.is_file():
                raise FanoutError("CONSERVATIVE_PAGE_NOT_FOUND", document["conservative_page"])
            additions = ["", "## 概念入口", ""]
            for candidate in values:
                relative = PurePosixPath("../concepts") / f"{candidate['candidate_id']}.md"
                additions.append(f"- [[{relative.as_posix()}|{candidate['term']}]]")
            page.write_text(page.read_text(encoding="utf-8").rstrip() + "\n" + "\n".join(additions) + "\n", encoding="utf-8", newline="\n")

        _audit_links(staging, int(policy["max_links_per_page"]))
        base_projection = load_object(conservative / "projection.json", "conservative projection")
        changed_paths = sorted(
            [candidate["page"] for candidate in accepted]
            + [document["conservative_page"] for document in documents if accepted_by_document.get(document["document_id"])]
        )
        generated_output_bytes = sum((staging / path).stat().st_size for path in changed_paths)
        generation_context_bytes = sum(
            utf8_size((candidate["term"], candidate["claim_zh"], candidate["source_text"])) for candidate in candidates
        )
        pages = list(base_projection["pages"])
        pages.extend({"path": item["page"], "title": item["term"], "kind": "concept"} for item in accepted)
        projection = {
            "schema_version": 1,
            "scope": "isolated-page-fanout-benchmark",
            "arm_id": "arm_b",
            "start_page": base_projection["start_page"],
            "source_count": len(documents),
            "page_count": len(pages),
            "new_page_count": len(accepted),
            "page_limit_per_source": base_projection["page_limit_per_source"],
            "generation_context_bytes": generation_context_bytes,
            "generated_output_bytes": generated_output_bytes,
            "pages": pages,
            "accepted_candidates": accepted,
            "rejected_candidates": rejected,
            "baseline_tree": {key: baseline[key] for key in ("sha256", "file_count", "total_bytes")},
            "policy": policy,
        }
        (staging / "projection.json").write_bytes(canonical_json_bytes(projection))
        json.loads((staging / "projection.json").read_text(encoding="utf-8"))
        os.replace(staging, output)
        output_tree = tree_manifest(output)
        rollback = {
            "schema_version": 1,
            "action": "remove-isolated-output",
            "workspace_root": workspace.as_posix(),
            "output": output.relative_to(workspace).as_posix(),
            "baseline_input": conservative.relative_to(workspace).as_posix(),
            "baseline_tree": baseline,
            "output_tree": output_tree,
        }
        try:
            atomic_write_json(rollback_path, rollback)
        except Exception:
            shutil.rmtree(output)
            raise
        return {
            "schema_version": 1,
            "status": "passed",
            "output": str(output),
            "output_tree_sha256": output_tree["sha256"],
            "rollback_manifest": str(rollback_path),
            "baseline_tree_sha256": baseline["sha256"],
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "rejection_reasons": sorted({item["reason"] for item in rejected}),
            "page_count": projection["page_count"],
            "generation_context_bytes": generation_context_bytes,
            "generated_output_bytes": generated_output_bytes,
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def rollback_fanout(manifest_path: Path, workspace_root: Path) -> dict[str, Any]:
    workspace = workspace_root.resolve()
    manifest_file = ensure_within(manifest_path, workspace, "manifest")
    manifest = load_object(manifest_file, "rollback manifest")
    exact_keys(
        manifest,
        {"schema_version", "action", "workspace_root", "output", "baseline_input", "baseline_tree", "output_tree"},
        "rollback manifest",
    )
    if manifest["schema_version"] != 1 or manifest["action"] != "remove-isolated-output":
        raise FanoutError("INVALID_ROLLBACK", "schema_version/action 非法")
    if manifest["workspace_root"] != workspace.as_posix():
        raise FanoutError("ROLLBACK_WORKSPACE_MISMATCH", manifest["workspace_root"])
    output = ensure_within(workspace / validate_relative_path(manifest["output"], "manifest.output"), workspace, "manifest.output")
    if not output.is_dir():
        raise FanoutError("ROLLBACK_OUTPUT_NOT_FOUND", str(output))
    current = tree_manifest(output)
    expected = manifest["output_tree"]
    if current != expected:
        raise FanoutError("ROLLBACK_DRIFT", f"expected={expected.get('sha256')} actual={current['sha256']}")
    shutil.rmtree(output)
    if output.exists():
        raise FanoutError("ROLLBACK_INCOMPLETE", str(output))
    return {
        "schema_version": 1,
        "status": "rolled-back",
        "removed": str(output),
        "verified_output_sha256": current["sha256"],
        "baseline_input_preserved": manifest["baseline_input"],
        "baseline_tree_sha256": manifest["baseline_tree"]["sha256"],
    }
