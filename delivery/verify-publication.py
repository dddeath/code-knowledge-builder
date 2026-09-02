#!/usr/bin/env python3
"""Read-only verification for a fresh CKB source and stable-knowledge clone."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


TARGET_COMMIT = "c533dd7c53224a637b1438ea72ee25da887fc6de"
LEARNING_NOTES = {
    "2026-08-29.md": "62059c19c42a0969e116c66d747627c6fae1b9fef3ef412e2c0ed03ced45ceeb",
    "2026-08-30.md": "dc7e8eb4791816b8d7989bb7bb82e97f50d6cbdb2f586f769422baf79ea91e67",
}
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def file_inventory(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): {"size": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def verify_inventory(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    expected = {item["path"]: {"size": item["size"], "sha256": item["sha256"]} for item in manifest["files"]}
    actual = file_inventory(root)
    changed = [path for path in sorted(set(expected) & set(actual)) if expected[path] != actual[path]]
    return {
        "passed": expected == actual,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": sorted(set(expected) - set(actual)),
        "extra": sorted(set(actual) - set(expected)),
        "changed": changed,
    }


def sqlite_check(path: Path, expected_schema: str) -> dict[str, Any]:
    if path.read_bytes()[: len(LFS_PREFIX)] == LFS_PREFIX:
        return {"path": str(path), "passed": False, "reason": "unexpanded-lfs-pointer"}
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
    finally:
        connection.close()
    return {
        "path": str(path),
        "passed": integrity == "ok" and not foreign_keys and meta.get("schema_version") == expected_schema,
        "integrity_check": integrity,
        "foreign_key_error_count": len(foreign_keys),
        "schema_version": meta.get("schema_version"),
        "sha256": sha256(path),
    }


def mirror_check(knowledge: Path) -> dict[str, Any]:
    excluded = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
    layers: dict[str, dict[str, Path]] = {}
    for layer in ("human", "markdown"):
        root = knowledge / layer
        layers[layer] = {
            path.relative_to(root).as_posix(): path
            for path in root.rglob("*.md")
            if path.relative_to(root).as_posix() not in excluded
            and not path.relative_to(root).as_posix().startswith((".github/", ".cursor/", ".obsidian/"))
        }
    errors: list[dict[str, Any]] = []
    if set(layers["human"]) != set(layers["markdown"]):
        errors.append({
            "reason": "file-set",
            "human_only": sorted(set(layers["human"]) - set(layers["markdown"])),
            "markdown_only": sorted(set(layers["markdown"]) - set(layers["human"])),
        })
    for relative in sorted(set(layers["human"]) & set(layers["markdown"])):
        if layers["human"][relative].read_bytes() != layers["markdown"][relative].read_bytes():
            errors.append({"reason": "byte-drift", "path": relative})
    return {"passed": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    source = root / "source"
    knowledge = root / "knowledge-base"
    source_manifest = load(root / "delivery/source-files.json")
    knowledge_manifest = load(root / "delivery/knowledge-files.json")
    publication = load(root / "publication-manifest.json")
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    source_files = verify_inventory(source, source_manifest)
    check("source-files", source_files["passed"], source_files)
    knowledge_files = verify_inventory(knowledge, knowledge_manifest)
    check("knowledge-files", knowledge_files["passed"], knowledge_files)
    state = load(knowledge / "state.json")
    check("fixed-source-commit", state.get("repository", {}).get("commit") == TARGET_COMMIT, state.get("repository"))
    check("completion-markers", all(load(knowledge / name).get("status") == "complete" for name in (".complete", ".machine.complete", ".human.complete")), "three markers")
    check("global-audit", load(knowledge / "audit/global.json").get("status") == "passed", load(knowledge / "audit/global.json").get("status"))
    sqlite_rows = [
        sqlite_check(knowledge / "agent-index.sqlite", "1"),
        sqlite_check(knowledge / "machine/knowledge.sqlite", "3"),
    ]
    check("double-sqlite", all(item["passed"] for item in sqlite_rows), sqlite_rows)
    mirror = mirror_check(knowledge)
    check("human-markdown-mirror", mirror["passed"], mirror)
    readability = load(knowledge / "human/readability-audit.json")
    check("readability", readability.get("status") == "passed" and not readability.get("errors"), readability.get("errors"))
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    experimental = publication.get("experiments", {})
    surface = {
        "canvas_skill": source / "prototypes/ckb-canvas-skill/SKILL.md",
        "canvas_cli": source / "prototypes/ckb-canvas-skill/scripts/ckb_canvas.py",
        "canvas_schema": source / "prototypes/ckb-canvas-skill/schemas/canvas-request.schema.json",
        "record_replace": source / "scripts/ckb_core/record_replace.py",
        "record_replace_test": source / "tests/test_record_replace.py",
        "record_replace_note": knowledge / "human/changes/增加受控的工作记录正文替换与回滚.md",
        "canvas_release_note": knowledge / "human/changes/将 Obsidian Canvas 原型纳入实验发布.md",
        "page_fanout_benchmark": source / "prototypes/ckb-page-fanout-benchmark/ckb_page_fanout/benchmark.py",
        "page_fanout_result": source / "references/benchmarks/page-fanout/benchmark-result.json",
        "page_fanout_note": knowledge / "human/experiments/单文档自动页面扩张对照实验.md",
        "semantic_vector_benchmark": source / "prototypes/ckb-semantic-vector-benchmark/benchmark.py",
        "semantic_vector_result": source / "prototypes/ckb-semantic-vector-benchmark/results/fixed-v1/report.json",
        "semantic_vector_note": knowledge / "human/experiments/真实语义向量检索三臂对照实验.md",
    }
    surface_detail = {
        "files": {name: path.is_file() for name, path in surface.items()},
        "canvas_status": experimental.get("obsidian_canvas", {}).get("status"),
        "page_fanout_status": experimental.get("page_fanout", {}).get("status"),
        "semantic_vector_status": experimental.get("semantic_vector", {}).get("status"),
        "readme_human_entry_headings": all(
            heading in readme_text
            for heading in (
                "## 了解本项目知识库结构",
                "## 让 Agent 安装本项目",
                "## 让 Agent 解释自己的项目",
            )
        ),
    }
    check(
        "experimental-canvas-and-record-replace-surface",
        all(surface_detail["files"].values())
        and surface_detail["canvas_status"] == "experimental-awaiting-user-feedback"
        and surface_detail["page_fanout_status"] == "negative-result"
        and surface_detail["semantic_vector_status"] == "regression-observed"
        and surface_detail["readme_human_entry_headings"],
        surface_detail,
    )
    fanout = load(surface["page_fanout_result"])
    semantic = load(surface["semantic_vector_result"])
    experiment_detail = {
        "page_fanout_recommendation": fanout.get("recommendation"),
        "semantic_status": semantic.get("status"),
        "semantic_failed_checks": [name for name, passed in semantic.get("checks", {}).items() if not passed],
        "semantic_decision": semantic.get("decision"),
    }
    check(
        "negative-experiment-results",
        experiment_detail["page_fanout_recommendation"] == "retain-conservative"
        and experiment_detail["semantic_status"] == "failed"
        and experiment_detail["semantic_failed_checks"] == ["extra_child_processes_within_limit"]
        and experiment_detail["semantic_decision"].get("result") == "regression-observed"
        and experiment_detail["semantic_decision"].get("production_default_changed") is False,
        experiment_detail,
    )
    records = list((knowledge / "workspace-meta/notes").glob("*.json"))
    references = list((knowledge / "references/manifests").glob("*.json"))
    gaps = list((knowledge / "workspace-meta/gaps/records").glob("*.json"))
    expected_records = int(publication.get("knowledge_state", {}).get("records", 0))
    expected_references = int(publication.get("knowledge_state", {}).get("references", 0))
    expected_gaps = int(publication.get("knowledge_state", {}).get("research_gaps", 0))
    check("durable-counts", len(records) == expected_records and len(references) == expected_references and len(gaps) == expected_gaps, {"records": len(records), "expected_records": expected_records, "references": len(references), "expected_references": expected_references, "research_gaps": len(gaps), "expected_research_gaps": expected_gaps})
    notes = []
    for name, digest in LEARNING_NOTES.items():
        row = {"name": name, "expected": digest}
        for layer in ("human", "markdown"):
            path = knowledge / layer / "学习笔记" / name
            row[layer] = sha256(path) if path.is_file() else None
        row["passed"] = row["human"] == digest and row["markdown"] == digest
        notes.append(row)
    check("learning-note-originals", all(item["passed"] for item in notes), notes)
    transient = [path.relative_to(knowledge).as_posix() for path in knowledge.rglob("*") if path.is_file() and (path.name == ".git" or path.name.endswith((".sqlite-wal", ".sqlite-shm")))]
    check("no-transient-git-or-sqlite-state", not transient, transient)
    credential_scan = load(root / "delivery/credential-scan.json")
    check(
        "credential-scan",
        credential_scan.get("status") == "passed" and not credential_scan.get("findings"),
        {
            "status": credential_scan.get("status"),
            "scanned_text_files": credential_scan.get("scanned_text_files"),
            "findings": credential_scan.get("findings"),
            "allowlisted_test_fixtures": len(credential_scan.get("allowlisted_test_fixtures", [])),
        },
    )
    lfs_files = [root / item["path"] for item in publication.get("lfs_files", [])]
    lfs_errors = [str(path) for path in lfs_files if not path.is_file() or path.read_bytes()[: len(LFS_PREFIX)] == LFS_PREFIX]
    check("lfs-objects-materialized", not lfs_errors, lfs_errors)
    status = "passed" if all(item["passed"] for item in checks) else "failed"
    result = {"schema_version": 1, "status": status, "root": str(root), "checks": checks}
    if args.write:
        target = args.write if args.write.is_absolute() else root / args.write
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "passed" else 5


if __name__ == "__main__":
    raise SystemExit(main())
