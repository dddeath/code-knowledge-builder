"""Fixed three-arm SQLite, semantic-vector, and QMD retrieval benchmark."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import socket
import sqlite3
import statistics
import subprocess
import sys
import threading
import time
from typing import Any, Iterator


SCHEMA_VERSION = 1
ARM_IDS = ("sqlite-current", "semantic-vector", "qmd-vsearch")
PYTHON_ARM_IDS = ("sqlite-current", "semantic-vector")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_ROOT = Path(__file__).resolve().parent
QMD_ADAPTER = PROTOTYPE_ROOT / "qmd_adapter.mjs"


class EngineUnavailable(RuntimeError):
    """The frozen embedding engine is absent or has the wrong identity."""


class ModelUnavailable(RuntimeError):
    """The frozen local model snapshot is absent or drifted."""


class QmdUnavailable(RuntimeError):
    """The pinned QMD package, Node runtime, or GGUF model is absent or drifted."""


class QmdExecutionFailed(RuntimeError):
    """The pinned QMD adapter exited unsuccessfully."""


class QmdOutputDrift(RuntimeError):
    """The pinned QMD adapter returned a different machine-output shape."""


def json_load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _readonly_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def _sqlite_backup(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with _readonly_connection(source) as left, sqlite3.connect(target) as right:
        left.backup(right)


def copy_corpus(source: Path, target: Path) -> dict[str, Any]:
    if target.exists():
        raise ValueError(f"benchmark corpus target already exists: {target}")
    target.mkdir(parents=True)
    source_machine = source / "machine/knowledge.sqlite"
    source_legacy = source / "agent-index.sqlite"
    _sqlite_backup(source_machine, target / "machine/knowledge.sqlite")
    _sqlite_backup(source_legacy, target / "agent-index.sqlite")
    for name in ("state.json", "local-openers.json"):
        if (source / name).is_file():
            shutil.copy2(source / name, target / name)
    shutil.copytree(source / "human", target / "human")
    shutil.copytree(source / "human", target / "markdown")
    integrity: dict[str, str] = {}
    for name, path in (
        ("machine", target / "machine/knowledge.sqlite"),
        ("legacy", target / "agent-index.sqlite"),
    ):
        with _readonly_connection(path) as connection:
            integrity[name] = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    with _readonly_connection(target / "machine/knowledge.sqlite") as connection:
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
    return {
        "source": str(source.resolve()),
        "repository_commit": meta.get("repository_commit"),
        "source_machine_sha256_before": sha256(source_machine),
        "source_legacy_sha256_before": sha256(source_legacy),
        "copied_machine_sha256": sha256(target / "machine/knowledge.sqlite"),
        "copied_legacy_sha256": sha256(target / "agent-index.sqlite"),
        "integrity": integrity,
    }


def validate_model_artifacts(model_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json_load(manifest_path)
    if manifest.get("status") != "verified-local-snapshot":
        raise ModelUnavailable("model artifact manifest is not verified-local-snapshot")
    if not model_dir.is_dir():
        raise ModelUnavailable(f"model snapshot directory is missing: {model_dir}")
    expected = {item["path"]: item for item in manifest.get("files", [])}
    if not expected:
        raise ModelUnavailable("model artifact manifest has no files")
    actual_paths = {
        item.relative_to(model_dir).as_posix()
        for item in model_dir.rglob("*")
        if item.is_file() and ".cache" not in item.relative_to(model_dir).parts
    }
    missing = sorted(set(expected) - actual_paths)
    extra = sorted(actual_paths - set(expected))
    mismatches = []
    for relative, item in sorted(expected.items()):
        path = model_dir / relative
        if path.is_file() and (
            path.stat().st_size != int(item["bytes"]) or sha256(path) != item["sha256"]
        ):
            mismatches.append(relative)
    if missing or extra or mismatches:
        raise ModelUnavailable(
            f"model snapshot identity drift: missing={missing}, extra={extra}, mismatches={mismatches}"
        )
    total = sum((model_dir / relative).stat().st_size for relative in expected)
    if total != int(manifest["total_bytes"]):
        raise ModelUnavailable("model snapshot total bytes differ from manifest")
    return {
        "repository": manifest["repository"],
        "revision": manifest["revision"],
        "files": len(expected),
        "total_bytes": total,
        "manifest_sha256": sha256(manifest_path),
    }


def engine_identity(expected_version: str) -> dict[str, Any]:
    try:
        version = importlib.metadata.version("fastembed")
        numpy_version = importlib.metadata.version("numpy")
        onnxruntime_version = importlib.metadata.version("onnxruntime")
    except importlib.metadata.PackageNotFoundError as error:
        raise EngineUnavailable(f"embedding engine dependency is missing: {error.name}") from error
    if version != expected_version:
        raise EngineUnavailable(f"fastembed version drift: expected {expected_version}, actual {version}")
    return {
        "fastembed": version,
        "numpy": numpy_version,
        "onnxruntime": onnxruntime_version,
    }


def qmd_runtime_identity(
    package_root: Path,
    model_path: Path,
    manifest_path: Path,
    node_executable: Path,
    adapter_path: Path = QMD_ADAPTER,
) -> dict[str, Any]:
    manifest = json_load(manifest_path)
    if manifest.get("status") != "verified-local-runtime":
        raise QmdUnavailable("QMD runtime manifest is not verified-local-runtime")
    if not node_executable.is_file():
        raise QmdUnavailable(f"Node executable is missing: {node_executable}")
    package_json_path = package_root / "package.json"
    build_info_path = package_root / "dist/cli/build-info.json"
    sdk_path = package_root / "dist/index.js"
    for required in (package_json_path, build_info_path, sdk_path, adapter_path):
        if not required.is_file():
            raise QmdUnavailable(f"QMD runtime file is missing: {required}")
    package_json = json_load(package_json_path)
    build_info = json_load(build_info_path)
    expected_package = manifest["package"]
    if package_json.get("name") != expected_package["name"]:
        raise QmdUnavailable("QMD package name drift")
    if package_json.get("version") != expected_package["version"]:
        raise QmdUnavailable("QMD package version drift")
    if build_info.get("commit") != expected_package["build_commit"]:
        raise QmdUnavailable("QMD package build commit drift")
    if sha256(adapter_path) != manifest["adapter"]["sha256"]:
        raise QmdUnavailable("QMD adapter digest drift")
    runtime_lock = REPOSITORY_ROOT / manifest["package_lock"]["path"]
    if not runtime_lock.is_file() or sha256(runtime_lock) != manifest["package_lock"]["sha256"]:
        raise QmdUnavailable("QMD package lock digest drift")
    if not model_path.is_file():
        raise QmdUnavailable(f"QMD model is missing: {model_path}")
    expected_model = manifest["model"]
    if model_path.stat().st_size != int(expected_model["bytes"]):
        raise QmdUnavailable("QMD model byte length drift")
    if sha256(model_path) != expected_model["sha256"]:
        raise QmdUnavailable("QMD model digest drift")
    with model_path.open("rb") as stream:
        magic = stream.read(4)
    if magic != b"GGUF":
        raise QmdUnavailable("QMD model is not a GGUF file")
    process = subprocess.run(
        [str(node_executable), "--version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    node_version = process.stdout.strip()
    if process.returncode != 0 or node_version != manifest["node"]["version"]:
        raise QmdUnavailable(
            f"Node version drift: expected {manifest['node']['version']}, actual {node_version or process.returncode}"
        )
    return {
        "package_name": package_json["name"],
        "package_version": package_json["version"],
        "package_git_head": expected_package["git_head"],
        "package_build_commit": build_info["commit"],
        "package_dist_integrity": expected_package["dist_integrity"],
        "package_lock_sha256": manifest["package_lock"]["sha256"],
        "node_version": node_version,
        "model_name": expected_model["name"],
        "model_repository": expected_model["repository"],
        "model_revision": expected_model["revision"],
        "model_bytes": model_path.stat().st_size,
        "model_sha256": expected_model["sha256"],
        "adapter_sha256": manifest["adapter"]["sha256"],
    }


def _schema_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")]


def validate_protocol(
    protocol_path: Path,
    source_corpus: Path,
    model_manifest: Path,
    model_dir: Path,
    qmd_manifest: Path,
    qmd_package: Path,
    qmd_model: Path,
    node_executable: Path,
) -> dict[str, Any]:
    protocol = json_load(protocol_path)
    if protocol.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("protocol schema version mismatch")
    if protocol.get("status") != "frozen" or protocol.get("frozen_before_effect_run") is not True:
        raise ValueError("protocol must be frozen before the effect run")
    if tuple(item.get("id") for item in protocol.get("arms", [])) != ARM_IDS:
        raise ValueError("protocol arm identities or order differ from the fixed contract")
    execution = protocol.get("execution") or {}
    if execution.get("cold_runs") != 1 or execution.get("hot_runs") != 5:
        raise ValueError("protocol requires one cold and five hot runs")
    if (
        execution.get("max_results") != 8
        or execution.get("profile") != "fast"
        or execution.get("budget_tokens") != 2400
    ):
        raise ValueError("protocol requires fast profile, budget 2400, and top 8")
    if execution.get("ranking_truncation") != "source-path-deduplicate-then-budget-then-top-k":
        raise ValueError("protocol ranking truncation drift")
    if int(protocol.get("qmd", {}).get("candidate_depth", 0)) != int(
        protocol["corpus"]["entity_rows_with_source_path"]
    ):
        raise ValueError("QMD candidate depth must equal the frozen document count")
    if int(protocol.get("random_seed", -1)) != 0:
        raise ValueError("protocol random seed drift")
    questions = protocol.get("questions")
    if not isinstance(questions, list) or len(questions) != 12:
        raise ValueError("protocol requires exactly twelve fixed questions")
    if len({item.get("id") for item in questions}) != 12:
        raise ValueError("protocol question ids must be unique")
    for item in questions:
        if not isinstance(item.get("question"), str) or not item["question"]:
            raise ValueError("each protocol question requires text")
        labels = item.get("relevance")
        if not isinstance(labels, list) or not labels:
            raise ValueError(f"question {item.get('id')} has no relevance labels")
        if any(label.get("grade") not in {1, 2, 3} for label in labels):
            raise ValueError(f"question {item.get('id')} has an invalid relevance grade")
    source_questions = REPOSITORY_ROOT / protocol["questions_source"]["path"]
    if sha256(source_questions) != protocol["questions_source"]["sha256"]:
        raise ValueError("source question fixture digest drift")
    source_value = json_load(source_questions)
    if source_value.get("questions") != questions:
        raise ValueError("copied questions or relevance labels drifted from the fixed source")
    expected = protocol["corpus"]
    machine_path = source_corpus / "machine/knowledge.sqlite"
    legacy_path = source_corpus / "agent-index.sqlite"
    if sha256(machine_path) != expected["machine_sqlite_sha256"]:
        raise ValueError("source machine SQLite digest differs from the frozen protocol")
    if sha256(legacy_path) != expected["agent_index_sqlite_sha256"]:
        raise ValueError("source agent-index SQLite digest differs from the frozen protocol")
    with _readonly_connection(machine_path) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("source machine SQLite integrity check failed")
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
        required = protocol["document_contract"]["fields_in_order"]
        columns = _schema_columns(connection, "entities")
        if any(name not in columns for name in ["entity_id", *required]):
            raise ValueError("source entities schema differs from the document contract")
        entity_count = int(
            connection.execute("SELECT count(*) FROM entities WHERE source_path <> ''").fetchone()[0]
        )
    with _readonly_connection(legacy_path) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("source agent-index SQLite integrity check failed")
    if meta.get("repository_commit") != expected["bound_repository_commit"]:
        raise ValueError("source repository commit differs from the frozen protocol")
    if entity_count != expected["entity_rows_with_source_path"]:
        raise ValueError("source entity count differs from the frozen protocol")
    if protocol["model"]["artifact_revision"] != json_load(model_manifest).get("revision"):
        raise ModelUnavailable("protocol and model artifact manifest revisions differ")
    model = validate_model_artifacts(model_dir, model_manifest)
    engine = engine_identity(protocol["model"]["engine_version"])
    qmd = qmd_runtime_identity(
        qmd_package,
        qmd_model,
        qmd_manifest,
        node_executable,
    )
    if protocol["qmd"]["package_version"] != qmd["package_version"]:
        raise QmdUnavailable("protocol and QMD package versions differ")
    if protocol["qmd"]["model_sha256"] != qmd["model_sha256"]:
        raise QmdUnavailable("protocol and QMD model digests differ")
    return {
        "protocol": protocol,
        "model": model,
        "engine": engine,
        "qmd": qmd,
        "entity_count": entity_count,
    }


def render_documents(machine_path: Path, protocol: dict[str, Any]) -> list[dict[str, str]]:
    contract = protocol["document_contract"]
    fields = list(contract["fields_in_order"])
    select = ["entity_id", *fields]
    sql = f"SELECT {', '.join(select)} FROM entities WHERE source_path <> '' ORDER BY entity_id"
    if sql != contract["selection_sql"]:
        raise ValueError("document selection SQL differs from the frozen contract")
    with _readonly_connection(machine_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(sql).fetchall()
    documents = []
    for row in rows:
        lines = []
        for field in fields:
            value = str(row[field] or "").strip()
            if value:
                lines.append(f"{field}: {value}")
        documents.append(
            {
                "entity_id": str(row["entity_id"]),
                "source_path": str(row["source_path"]).replace("\\", "/"),
                "qualified_name": str(row["qualified_name"]),
                "text": "\n".join(lines),
            }
        )
    if len(documents) != int(protocol["corpus"]["entity_rows_with_source_path"]):
        raise ValueError("rendered document count differs from the frozen protocol")
    return documents


def documents_digest(documents: list[dict[str, str]]) -> str:
    encoded = json.dumps(documents, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@contextmanager
def network_guard() -> Iterator[list[str]]:
    attempts: list[str] = []
    original_connect = socket.socket.connect
    original_create = socket.create_connection

    def blocked_connect(sock: socket.socket, address: Any) -> None:
        attempts.append(repr(address))
        raise RuntimeError("network is disabled during the fixed semantic-vector measurement")

    def blocked_create(address: Any, *args: Any, **kwargs: Any) -> None:
        attempts.append(repr(address))
        raise RuntimeError("network is disabled during the fixed semantic-vector measurement")

    socket.socket.connect = blocked_connect  # type: ignore[method-assign]
    socket.create_connection = blocked_create  # type: ignore[assignment]
    try:
        yield attempts
    finally:
        socket.socket.connect = original_connect  # type: ignore[method-assign]
        socket.create_connection = original_create  # type: ignore[assignment]


def load_model(protocol: dict[str, Any], model_dir: Path) -> Any:
    try:
        from fastembed import TextEmbedding
    except ImportError as error:
        raise EngineUnavailable(f"fastembed import failed: {error}") from error
    model = protocol["model"]
    return TextEmbedding(
        model["registered_name"],
        specific_model_path=str(model_dir),
        local_files_only=True,
        threads=int(model["threads"]),
        providers=[model["provider"]],
        cuda=False,
    )


def _as_normalized_matrix(values: Any, expected_rows: int, dimension: int) -> Any:
    import numpy as np

    matrix = np.asarray(list(values), dtype=np.float32)
    if matrix.shape != (expected_rows, dimension):
        raise ValueError(f"embedding shape mismatch: {matrix.shape}")
    if not np.isfinite(matrix).all():
        raise ValueError("embedding matrix contains non-finite values")
    norms = np.linalg.norm(matrix, axis=1)
    if not np.allclose(norms, np.ones_like(norms), atol=1e-4, rtol=1e-4):
        raise ValueError("embedding engine output is not L2 normalized")
    return matrix


def query_vector(model: Any, protocol: dict[str, Any], question: str) -> Any:
    text = protocol["model"]["query_instruction"] + question
    return _as_normalized_matrix(
        model.embed([text], batch_size=1, parallel=None),
        1,
        int(protocol["model"]["dimension"]),
    )[0]


def _vector_ranking(vectors: Any, documents: list[dict[str, str]], query: Any, top_k: int) -> list[dict[str, Any]]:
    import numpy as np

    scores = vectors @ query
    order = np.lexsort(
        (np.array([item["entity_id"] for item in documents], dtype=object), -scores)
    )
    ranked = []
    seen: set[str] = set()
    for index in order:
        document = documents[int(index)]
        key = document["source_path"].casefold()
        if key in seen:
            continue
        seen.add(key)
        ranked.append(
            {
                "rank": len(ranked) + 1,
                "source_path": document["source_path"],
                "entity_id": document["entity_id"],
                "qualified_name": document["qualified_name"],
                "score": round(float(scores[int(index)]), 9),
                "context_text": document["text"],
            }
        )
        if len(ranked) == top_k:
            break
    return ranked


def _load_index(index_dir: Path, protocol: dict[str, Any]) -> tuple[Any, list[dict[str, str]], dict[str, Any]]:
    import numpy as np

    manifest_path = index_dir / "index-manifest.json"
    documents_path = index_dir / "documents.json"
    vectors_path = index_dir / "vectors.npy"
    manifest = json_load(manifest_path)
    if sha256(documents_path) != manifest["files"]["documents.json"]["sha256"]:
        raise ValueError("index documents digest drift")
    if sha256(vectors_path) != manifest["files"]["vectors.npy"]["sha256"]:
        raise ValueError("index vectors digest drift")
    documents = json.loads(documents_path.read_text(encoding="utf-8"))
    vectors = np.load(vectors_path, allow_pickle=False)
    expected_shape = [len(documents), int(protocol["model"]["dimension"])]
    if list(vectors.shape) != expected_shape or str(vectors.dtype) != protocol["model"]["dtype"]:
        raise ValueError("index vector shape or dtype drift")
    if documents_digest(documents) != manifest["documents_digest"]:
        raise ValueError("index rendered-document digest drift")
    return vectors, documents, manifest


def index_size_accounting(index_dir: Path, protocol: dict[str, Any]) -> dict[str, int]:
    manifest_path = index_dir / "index-manifest.json"
    manifest = json_load(manifest_path)
    if "index_bytes" in manifest:
        raise ValueError("index manifest must not contain the self-referential index_bytes field")
    payload_names = [name for name in protocol["index"]["files"] if name != manifest_path.name]
    payload_bytes = sum((index_dir / name).stat().st_size for name in payload_names)
    if int(manifest.get("payload_bytes", -1)) != payload_bytes:
        raise ValueError("index manifest payload bytes differ from final payload files")
    manifest_bytes = manifest_path.stat().st_size
    return {
        "index_payload_bytes": payload_bytes,
        "index_manifest_bytes": manifest_bytes,
        "index_bytes": payload_bytes + manifest_bytes,
    }


def _visible_tokens(hits: list[dict[str, Any]]) -> int:
    characters = sum(len(str(item.get("context_text") or "")) for item in hits)
    return math.ceil(characters / 4)


def apply_common_truncation(
    hits: list[dict[str, Any]],
    documents: list[dict[str, str]],
    budget_tokens: int,
    top_k: int,
) -> list[dict[str, Any]]:
    by_entity = {item["entity_id"]: item for item in documents}
    by_path: dict[str, dict[str, str]] = {}
    for item in documents:
        by_path.setdefault(item["source_path"].casefold(), item)
    selected = []
    seen: set[str] = set()
    used_tokens = 0
    for hit in hits:
        source_path = str(hit.get("source_path") or "").replace("\\", "/")
        key = source_path.casefold()
        if not source_path or key in seen:
            continue
        document = by_entity.get(str(hit.get("entity_id") or "")) or by_path.get(key)
        context_text = str((document or {}).get("text") or hit.get("context_text") or source_path)
        item_tokens = math.ceil(len(context_text) / 4)
        if used_tokens + item_tokens > budget_tokens:
            break
        seen.add(key)
        used_tokens += item_tokens
        selected.append(
            {
                **hit,
                "rank": len(selected) + 1,
                "source_path": source_path,
                "context_text": context_text,
                "estimated_tokens": item_tokens,
            }
        )
        if len(selected) == top_k:
            break
    return selected


def write_qmd_projection(
    target: Path, documents: list[dict[str, str]], protocol: dict[str, Any]
) -> dict[str, Any]:
    if target.exists():
        raise ValueError(f"QMD projection target already exists: {target}")
    target.mkdir(parents=True)
    mapping: dict[str, dict[str, str]] = {}
    file_hashes = []
    for index, document in enumerate(documents):
        name = f"{index:06d}.md"
        data = (document["text"] + "\n").encode("utf-8")
        (target / name).write_bytes(data)
        mapping[name] = document
        file_hashes.append({"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    if len(mapping) != int(protocol["corpus"]["entity_rows_with_source_path"]):
        raise ValueError("QMD projection document count drift")
    mapping_path = target.parent / "qmd-documents.json"
    json_write(mapping_path, {"schema_version": 1, "documents": mapping})
    return {
        "documents": len(mapping),
        "documents_digest": documents_digest(documents),
        "mapping_sha256": sha256(mapping_path),
        "projection_sha256": hashlib.sha256(
            json.dumps(file_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "projection_bytes": sum(item["bytes"] for item in file_hashes),
    }


def _qmd_identity_matches(payload: dict[str, Any], expected: dict[str, Any]) -> bool:
    identity = payload.get("identity") or {}
    return identity == {
        "package_name": expected["package_name"],
        "package_version": expected["package_version"],
        "build_commit": expected["package_build_commit"],
        "node_version": expected["node_version"],
    }


def validate_qmd_build_payload(
    payload: Any, expected_identity: dict[str, Any], expected_documents: int, collection: str
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise QmdOutputDrift("QMD build output is not an object")
    if payload.get("schema_version") != 1 or payload.get("kind") != "qmd-build":
        raise QmdOutputDrift("QMD build output envelope drift")
    if not _qmd_identity_matches(payload, expected_identity):
        raise QmdOutputDrift("QMD build identity drift")
    if payload.get("collection") != collection:
        raise QmdOutputDrift("QMD build collection drift")
    if payload.get("expected_documents") != expected_documents:
        raise QmdOutputDrift("QMD build expected-document count drift")
    if payload.get("indexed_documents") != expected_documents:
        raise QmdOutputDrift("QMD build indexed-document count drift")
    update = payload.get("update")
    embed = payload.get("embed")
    if not isinstance(update, dict) or int(update.get("indexed", -1)) != expected_documents:
        raise QmdOutputDrift("QMD update result drift")
    if not isinstance(embed, dict) or int(embed.get("errors", -1)) != 0:
        raise QmdOutputDrift("QMD embed result drift")
    if int(embed.get("docsProcessed", -1)) <= 0:
        raise QmdOutputDrift("QMD embedded no documents")
    status = payload.get("status")
    if not isinstance(status, dict):
        raise QmdOutputDrift("QMD status result drift")
    if (
        int(status.get("totalDocuments", -1)) != expected_documents
        or int(status.get("needsEmbedding", -1)) != 0
        or status.get("hasVectorIndex") is not True
    ):
        raise QmdOutputDrift("QMD index status drift")
    if not isinstance(payload.get("wall_ms"), (int, float)):
        raise QmdOutputDrift("QMD build wall time drift")
    return payload


def validate_qmd_query_payload(
    payload: Any,
    expected_identity: dict[str, Any],
    question_id: str,
    cache_state: str,
    run_index: int,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise QmdOutputDrift("QMD query output is not an object")
    if payload.get("schema_version") != 1 or payload.get("kind") != "qmd-query":
        raise QmdOutputDrift("QMD query output envelope drift")
    if not _qmd_identity_matches(payload, expected_identity):
        raise QmdOutputDrift("QMD query identity drift")
    expected = (question_id, cache_state, run_index)
    actual = (payload.get("question_id"), payload.get("cache_state"), payload.get("run_index"))
    if actual != expected:
        raise QmdOutputDrift(f"QMD query run identity drift: expected {expected}, actual {actual}")
    if not isinstance(payload.get("latency_ms"), (int, float)):
        raise QmdOutputDrift("QMD query latency drift")
    results = payload.get("results")
    if not isinstance(results, list):
        raise QmdOutputDrift("QMD query results are not a list")
    for item in results:
        if not isinstance(item, dict) or set(item) != {
            "file",
            "filepath",
            "score",
            "source",
            "chunk_pos",
        }:
            raise QmdOutputDrift("QMD query result field drift")
        if not isinstance(item["file"], str) or not isinstance(item["score"], (int, float)):
            raise QmdOutputDrift("QMD query result type drift")
        if item["source"] != "vec":
            raise QmdOutputDrift("QMD query result source drift")
    return payload


def _build_index(protocol: dict[str, Any], corpus: Path, model_dir: Path, index_dir: Path) -> dict[str, Any]:
    import numpy as np

    if index_dir.exists():
        raise ValueError(f"index target already exists: {index_dir}")
    index_dir.mkdir(parents=True)
    documents = render_documents(corpus / "machine/knowledge.sqlite", protocol)
    model = load_model(protocol, model_dir)
    started = time.perf_counter_ns()
    vectors = _as_normalized_matrix(
        model.embed(
            [item["text"] for item in documents],
            batch_size=int(protocol["model"]["batch_size"]),
            parallel=None,
        ),
        len(documents),
        int(protocol["model"]["dimension"]),
    )
    encode_seconds = (time.perf_counter_ns() - started) / 1_000_000_000
    vectors_path = index_dir / "vectors.npy"
    documents_path = index_dir / "documents.json"
    with vectors_path.open("wb") as stream:
        np.save(stream, vectors, allow_pickle=False)
    documents_path.write_bytes(
        (json.dumps(documents, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
    )
    target_path = protocol["questions"][0]["relevance"][0]["source_path"].casefold()
    target_index = next(
        index for index, item in enumerate(documents) if item["source_path"].casefold() == target_path
    )
    question = protocol["questions"][0]["question"]
    query = query_vector(model, protocol, question)
    before = _vector_ranking(vectors, documents, query, int(protocol["index"]["top_k"]))
    probe = vectors.copy()
    incremental_started = time.perf_counter_ns()
    replacement = _as_normalized_matrix(
        model.embed([documents[target_index]["text"]], batch_size=1, parallel=None),
        1,
        int(protocol["model"]["dimension"]),
    )[0]
    probe[target_index] = replacement
    probe_path = index_dir / "incremental-probe.npy"
    with probe_path.open("wb") as stream:
        np.save(stream, probe, allow_pickle=False)
    incremental_seconds = (time.perf_counter_ns() - incremental_started) / 1_000_000_000
    after = _vector_ranking(probe, documents, query, int(protocol["index"]["top_k"]))
    incremental = {
        "entity_id": documents[target_index]["entity_id"],
        "source_path": documents[target_index]["source_path"],
        "seconds": round(incremental_seconds, 9),
        "replacement_vector_equal": bool(np.array_equal(vectors[target_index], replacement)),
        "ranking_unchanged": [item["source_path"] for item in before]
        == [item["source_path"] for item in after],
        "probe_bytes": probe_path.stat().st_size,
    }
    probe_path.unlink()
    manifest = {
        "schema_version": 1,
        "status": "passed"
        if incremental["replacement_vector_equal"] and incremental["ranking_unchanged"]
        else "failed",
        "algorithm": protocol["index"]["algorithm"],
        "documents": len(documents),
        "dimension": int(protocol["model"]["dimension"]),
        "dtype": protocol["model"]["dtype"],
        "normalized": True,
        "documents_digest": documents_digest(documents),
        "corpus_machine_sha256": sha256(corpus / "machine/knowledge.sqlite"),
        "files": {
            "vectors.npy": {"bytes": vectors_path.stat().st_size, "sha256": sha256(vectors_path)},
            "documents.json": {
                "bytes": documents_path.stat().st_size,
                "sha256": sha256(documents_path),
            },
        },
        "payload_bytes": vectors_path.stat().st_size + documents_path.stat().st_size,
        "encode_seconds": round(encode_seconds, 9),
        "incremental_probe": incremental,
        "network_attempts": [],
    }
    json_write(index_dir / "index-manifest.json", manifest)
    return manifest


def unique_sqlite_documents(result: dict[str, Any]) -> list[dict[str, Any]]:
    documents = []
    seen: set[str] = set()
    for entity in result.get("selected_entities") or []:
        source_path = str(entity.get("source_path") or "").replace("\\", "/")
        key = source_path.casefold()
        if not source_path or key in seen:
            continue
        seen.add(key)
        documents.append(
            {
                "rank": len(documents) + 1,
                "source_path": source_path,
                "entity_id": entity.get("entity_id"),
                "qualified_name": entity.get("qualified_name"),
                "score": entity.get("score"),
            }
        )
    return documents


def quality_for_ranking(
    documents: list[dict[str, Any]], relevance: list[dict[str, Any]], k: int = 8
) -> dict[str, Any]:
    grades = {
        item["source_path"].replace("\\", "/").casefold(): int(item["grade"])
        for item in relevance
    }
    ranked = documents[:k]
    hits = [
        {
            "source_path": item["source_path"],
            "rank": int(item["rank"]),
            "grade": grades[item["source_path"].casefold()],
        }
        for item in ranked
        if item["source_path"].casefold() in grades
    ]
    recalled = {item["source_path"].casefold() for item in hits}
    recall = len(recalled) / len(grades)
    reciprocal_rank = 1.0 / hits[0]["rank"] if hits else 0.0
    dcg = sum((2 ** item["grade"] - 1) / math.log2(item["rank"] + 1) for item in hits)
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(ideal))
    selected_paths = {item["source_path"].casefold() for item in ranked}
    missing = [
        {
            "source_path": item["source_path"].replace("\\", "/"),
            "grade": item["grade"],
            "reason": "outside-top-8"
            if item["source_path"].replace("\\", "/").casefold() in selected_paths
            else "not-selected",
        }
        for item in relevance
        if item["source_path"].replace("\\", "/").casefold() not in recalled
    ]
    return {
        "recall_at_8": round(recall, 9),
        "mrr_at_8": round(reciprocal_rank, 9),
        "ndcg_at_8": round(dcg / idcg if idcg else 0.0, 9),
        "relevant_hits": hits,
        "missing": missing,
    }


def result_signature(documents: list[dict[str, Any]]) -> str:
    value = [
        (
            item["source_path"],
            item.get("entity_id"),
            item.get("qualified_name"),
            item.get("score"),
        )
        for item in documents
    ]
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _load_sqlite_retriever() -> Any:
    scripts = REPOSITORY_ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from ckb_core import machine_knowledge

    return machine_knowledge


def _hybrid_ranking(
    sqlite_hits: list[dict[str, Any]],
    vector_hits: list[dict[str, Any]],
    documents: list[dict[str, str]],
    rrf_k: int,
    top_k: int,
) -> list[dict[str, Any]]:
    context_by_path: dict[str, dict[str, str]] = {}
    for item in documents:
        context_by_path.setdefault(item["source_path"].casefold(), item)
    contributions: dict[str, dict[str, Any]] = {}
    for source, hits in (("sqlite_rank", sqlite_hits), ("vector_rank", vector_hits)):
        for item in hits:
            key = item["source_path"].casefold()
            entry = contributions.setdefault(
                key,
                {
                    "source_path": item["source_path"],
                    "entity_id": item.get("entity_id"),
                    "qualified_name": item.get("qualified_name"),
                    "rrf_score": 0.0,
                    "sqlite_rank": None,
                    "vector_rank": None,
                },
            )
            entry[source] = int(item["rank"])
            entry["rrf_score"] += 1.0 / (rrf_k + int(item["rank"]))
            if source == "vector_rank":
                entry["entity_id"] = item.get("entity_id")
                entry["qualified_name"] = item.get("qualified_name")
    ordered = sorted(
        contributions.values(), key=lambda item: (-item["rrf_score"], item["source_path"].casefold())
    )[:top_k]
    result = []
    for rank, item in enumerate(ordered, 1):
        context = context_by_path.get(item["source_path"].casefold(), {})
        result.append(
            {
                "rank": rank,
                "source_path": item["source_path"],
                "entity_id": item.get("entity_id"),
                "qualified_name": item.get("qualified_name"),
                "score": round(float(item["rrf_score"]), 12),
                "sqlite_rank": item["sqlite_rank"],
                "vector_rank": item["vector_rank"],
                "context_text": context.get("text", item["source_path"]),
            }
        )
    return result


def _worker_rows(
    arm: str,
    question: dict[str, Any],
    protocol: dict[str, Any],
    corpus: Path,
    index_dir: Path,
    model_dir: Path,
) -> list[dict[str, Any]]:
    with network_guard() as attempts:
        top_k = int(protocol["execution"]["max_results"])
        machine = None
        model = None
        vectors, documents, _manifest = _load_index(index_dir, protocol)
        if arm == "sqlite-current":
            machine = _load_sqlite_retriever()
            machine._RETRIEVAL_STATIC_CACHE.clear()
        if arm == "semantic-vector":
            model = load_model(protocol, model_dir)

        def invoke() -> tuple[list[dict[str, Any]], int]:
            sqlite_hits: list[dict[str, Any]] = []
            vector_hits: list[dict[str, Any]] = []
            sqlite_tokens = 0
            if machine is not None:
                result = machine.retrieve_machine(
                    corpus,
                    question["question"],
                    int(protocol["execution"]["budget_tokens"]),
                    top_k,
                    protocol["execution"]["profile"],
                )
                sqlite_hits = unique_sqlite_documents(result)
                sqlite_tokens = int(result.get("estimated_tokens") or 0)
            if model is not None and vectors is not None:
                vector_hits = _vector_ranking(
                    vectors,
                    documents,
                    query_vector(model, protocol, question["question"]),
                    top_k,
                )
            raw_hits = sqlite_hits if arm == "sqlite-current" else vector_hits
            hits = apply_common_truncation(
                raw_hits,
                documents,
                int(protocol["execution"]["budget_tokens"]),
                top_k,
            )
            if arm == "sqlite-current":
                return hits, min(sqlite_tokens, _visible_tokens(hits))
            return hits, _visible_tokens(hits)

        rows = []
        for run_index in range(1 + int(protocol["execution"]["hot_runs"])):
            started = time.perf_counter_ns()
            hits, tokens = invoke()
            latency_ms = round((time.perf_counter_ns() - started) / 1_000_000, 6)
            quality = quality_for_ranking(hits, question["relevance"], top_k)
            rows.append(
                {
                    "question_id": question["id"],
                    "question": question["question"],
                    "arm": arm,
                    "cache_state": "cold" if run_index == 0 else "hot",
                    "run_index": 1 if run_index == 0 else run_index,
                    "latency_ms": latency_ms,
                    "selected_documents": hits,
                    "quality": quality,
                    "first_pack_estimated_tokens": tokens,
                    "result_signature": result_signature(hits),
                    "network_attempts": [],
                }
            )
        for row in rows:
            row["network_attempts"] = list(attempts)
    return rows


def _emit_worker_rows(arguments: argparse.Namespace) -> int:
    protocol = json_load(arguments.protocol)
    question = next(item for item in protocol["questions"] if item["id"] == arguments.question_id)
    rows = _worker_rows(
        arguments.arm,
        question,
        protocol,
        arguments.corpus,
        arguments.index,
        arguments.model_dir,
    )
    for row in rows:
        print(json.dumps(row, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0


def _sample_process(process: subprocess.Popen[str], state: dict[str, Any]) -> None:
    try:
        import psutil
    except ImportError as error:
        state["sampler_error"] = str(error)
        return

    try:
        root = psutil.Process(process.pid)
    except psutil.Error:
        return
    while process.poll() is None:
        rss = 0
        children = []
        try:
            rss += root.memory_info().rss
            children = root.children(recursive=True)
            for child in children:
                try:
                    rss += child.memory_info().rss
                except psutil.Error:
                    pass
        except psutil.Error:
            pass
        state["peak_rss_bytes"] = max(state["peak_rss_bytes"], rss)
        state["peak_extra_child_processes"] = max(
            state["peak_extra_child_processes"], len(children)
        )
        connections = state.setdefault("network_connections", set())
        for current in [root, *children]:
            try:
                for connection in current.net_connections(kind="inet"):
                    if connection.raddr:
                        connections.add(f"{connection.raddr.ip}:{connection.raddr.port}")
            except (psutil.Error, AttributeError):
                pass
        time.sleep(0.01)


def _run_worker_process(
    arm: str,
    question_id: str,
    protocol_path: Path,
    corpus: Path,
    index_dir: Path,
    model_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "worker",
        "--arm",
        arm,
        "--question-id",
        question_id,
        "--protocol",
        str(protocol_path),
        "--corpus",
        str(corpus),
        "--index",
        str(index_dir),
        "--model-dir",
        str(model_dir),
    ]
    started = time.perf_counter_ns()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "HF_HUB_OFFLINE": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    state = {"peak_rss_bytes": 0, "peak_extra_child_processes": 0}
    sampler = threading.Thread(target=_sample_process, args=(process, state), daemon=True)
    sampler.start()
    rows = []
    assert process.stdout is not None
    for line in process.stdout:
        if not line.strip():
            continue
        row = json.loads(line)
        if not rows:
            row["worker_latency_ms"] = row["latency_ms"]
            row["latency_ms"] = round((time.perf_counter_ns() - started) / 1_000_000, 6)
        rows.append(row)
    assert process.stderr is not None
    stderr = process.stderr.read()
    exit_status = process.wait()
    sampler.join(timeout=1)
    if exit_status != 0:
        raise RuntimeError(
            f"worker failed for {arm}/{question_id} with exit {exit_status}: {stderr[-2000:]}"
        )
    expected_rows = 1 + int(json_load(protocol_path)["execution"]["hot_runs"])
    if len(rows) != expected_rows:
        raise RuntimeError(f"worker returned {len(rows)} rows, expected {expected_rows}")
    invocation_id = hashlib.sha256(f"{arm}:{question_id}".encode()).hexdigest()[:16]
    for row in rows:
        row["worker_invocation_id"] = invocation_id
    resource = {
        "worker_invocation_id": invocation_id,
        "arm": arm,
        "question_id": question_id,
        "exit_status": exit_status,
        "peak_rss_bytes": state["peak_rss_bytes"],
        "peak_extra_child_processes": state["peak_extra_child_processes"],
        "stderr": stderr,
    }
    return rows, resource


def _run_build_process(
    protocol_path: Path,
    corpus: Path,
    model_dir: Path,
    index_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "build-index",
        "--protocol",
        str(protocol_path),
        "--corpus",
        str(corpus),
        "--model-dir",
        str(model_dir),
        "--index",
        str(index_dir),
    ]
    started = time.perf_counter_ns()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "HF_HUB_OFFLINE": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    state = {"peak_rss_bytes": 0, "peak_extra_child_processes": 0}
    sampler = threading.Thread(target=_sample_process, args=(process, state), daemon=True)
    sampler.start()
    stdout, stderr = process.communicate()
    exit_status = process.returncode
    sampler.join(timeout=1)
    wall_seconds = round((time.perf_counter_ns() - started) / 1_000_000_000, 9)
    if exit_status != 0:
        raise RuntimeError(f"index builder failed with exit {exit_status}: {stderr[-2000:]}")
    lines = [line for line in stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise RuntimeError(f"index builder returned {len(lines)} stdout lines")
    manifest = json.loads(lines[0])
    return manifest, {
        "exit_status": exit_status,
        "wall_seconds": wall_seconds,
        "peak_rss_bytes": state["peak_rss_bytes"],
        "peak_extra_child_processes": state["peak_extra_child_processes"],
        "stderr": stderr,
    }


def _qmd_environment(qmd_root: Path, qmd_model: Path) -> dict[str, str]:
    blocked_proxy = "http://127.0.0.1:9"
    return {
        **os.environ,
        "ALL_PROXY": blocked_proxy,
        "HTTP_PROXY": blocked_proxy,
        "HTTPS_PROXY": blocked_proxy,
        "NO_PROXY": "",
        "QMD_EMBED_MODEL": str(qmd_model.resolve()),
        "QMD_EMBED_PARALLELISM": "4",
        "QMD_FORCE_CPU": "0",
        "QMD_LLAMA_GPU": "vulkan",
        "XDG_CACHE_HOME": str((qmd_root / "cache").resolve()),
    }


def _run_qmd_build_process(
    protocol: dict[str, Any],
    documents: list[dict[str, str]],
    qmd_package: Path,
    qmd_model: Path,
    node_executable: Path,
    qmd_root: Path,
    qmd_identity: dict[str, Any],
    adapter_path: Path = QMD_ADAPTER,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if qmd_root.exists():
        raise ValueError(f"QMD index target already exists: {qmd_root}")
    qmd_root.mkdir(parents=True)
    projection = write_qmd_projection(qmd_root / "corpus", documents, protocol)
    collection = protocol["qmd"]["collection"]
    command = [
        str(node_executable),
        str(adapter_path),
        "build",
        "--package-root",
        str(qmd_package),
        "--db",
        str(qmd_root / "index.sqlite"),
        "--corpus",
        str(qmd_root / "corpus"),
        "--collection",
        collection,
        "--model",
        str(qmd_model),
        "--expected-documents",
        str(len(documents)),
    ]
    started = time.perf_counter_ns()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_qmd_environment(qmd_root, qmd_model),
    )
    state: dict[str, Any] = {
        "peak_rss_bytes": 0,
        "peak_extra_child_processes": 0,
        "network_connections": set(),
    }
    sampler = threading.Thread(target=_sample_process, args=(process, state), daemon=True)
    sampler.start()
    stdout, stderr = process.communicate()
    exit_status = process.returncode
    sampler.join(timeout=1)
    wall_seconds = round((time.perf_counter_ns() - started) / 1_000_000_000, 9)
    if exit_status != 0:
        raise QmdExecutionFailed(f"QMD build failed with exit {exit_status}: {stderr[-2000:]}")
    lines = [line for line in stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise QmdOutputDrift(f"QMD build returned {len(lines)} stdout lines")
    try:
        value = json.loads(lines[0])
    except json.JSONDecodeError as error:
        raise QmdOutputDrift(f"QMD build returned invalid JSON: {error}") from error
    payload = validate_qmd_build_payload(value, qmd_identity, len(documents), collection)
    if state.get("sampler_error"):
        raise QmdExecutionFailed(f"QMD resource sampler unavailable: {state['sampler_error']}")
    resource = {
        "exit_status": exit_status,
        "wall_seconds": wall_seconds,
        "peak_rss_bytes": state["peak_rss_bytes"],
        "peak_extra_child_processes": state["peak_extra_child_processes"],
        "network_connections": sorted(state["network_connections"]),
        "stderr": stderr,
    }
    return payload, projection, resource


def _qmd_ranking(
    payload: dict[str, Any],
    mapping: dict[str, dict[str, str]],
    candidate_depth: int,
) -> list[dict[str, Any]]:
    results = payload["results"]
    if len(results) != candidate_depth:
        raise QmdOutputDrift(
            f"QMD query returned {len(results)} candidates, expected {candidate_depth}"
        )
    candidates = []
    for result in results:
        document = mapping.get(result["file"])
        if document is None:
            raise QmdOutputDrift(f"QMD query returned unknown projection file: {result['file']}")
        candidates.append(
            {
                "source_path": document["source_path"],
                "entity_id": document["entity_id"],
                "qualified_name": document["qualified_name"],
                "score": round(float(result["score"]), 9),
                "qmd_file": result["file"],
                "qmd_chunk_pos": result["chunk_pos"],
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["entity_id"]))
    return candidates


def _run_qmd_worker_process(
    question: dict[str, Any],
    protocol: dict[str, Any],
    qmd_package: Path,
    qmd_model: Path,
    node_executable: Path,
    qmd_root: Path,
    qmd_identity: dict[str, Any],
    documents: list[dict[str, str]],
    adapter_path: Path = QMD_ADAPTER,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapping_value = json_load(qmd_root / "qmd-documents.json")
    mapping = mapping_value.get("documents")
    if not isinstance(mapping, dict) or len(mapping) != len(documents):
        raise QmdOutputDrift("QMD projection mapping drift")
    collection = protocol["qmd"]["collection"]
    candidate_depth = int(protocol["qmd"]["candidate_depth"])
    hot_runs = int(protocol["execution"]["hot_runs"])
    command = [
        str(node_executable),
        str(adapter_path),
        "query",
        "--package-root",
        str(qmd_package),
        "--db",
        str(qmd_root / "index.sqlite"),
        "--corpus",
        str(qmd_root / "corpus"),
        "--collection",
        collection,
        "--model",
        str(qmd_model),
        "--question-id",
        question["id"],
        "--question",
        question["question"],
        "--candidate-depth",
        str(candidate_depth),
        "--hot-runs",
        str(hot_runs),
    ]
    started = time.perf_counter_ns()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_qmd_environment(qmd_root, qmd_model),
    )
    state: dict[str, Any] = {
        "peak_rss_bytes": 0,
        "peak_extra_child_processes": 0,
        "network_connections": set(),
    }
    sampler = threading.Thread(target=_sample_process, args=(process, state), daemon=True)
    sampler.start()
    rows = []
    assert process.stdout is not None
    for output_index, line in enumerate(process.stdout):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            process.kill()
            raise QmdOutputDrift(f"QMD query returned invalid JSON: {error}") from error
        cache_state = "cold" if output_index == 0 else "hot"
        run_index = 1 if output_index == 0 else output_index
        payload = validate_qmd_query_payload(
            value,
            qmd_identity,
            question["id"],
            cache_state,
            run_index,
        )
        ranked = _qmd_ranking(payload, mapping, candidate_depth)
        hits = apply_common_truncation(
            ranked,
            documents,
            int(protocol["execution"]["budget_tokens"]),
            int(protocol["execution"]["max_results"]),
        )
        latency_ms = float(payload["latency_ms"])
        worker_latency_ms = None
        if output_index == 0:
            worker_latency_ms = latency_ms
            latency_ms = round((time.perf_counter_ns() - started) / 1_000_000, 6)
        rows.append(
            {
                "question_id": question["id"],
                "question": question["question"],
                "arm": "qmd-vsearch",
                "cache_state": cache_state,
                "run_index": run_index,
                "latency_ms": latency_ms,
                "worker_latency_ms": worker_latency_ms,
                "selected_documents": hits,
                "quality": quality_for_ranking(hits, question["relevance"]),
                "first_pack_estimated_tokens": _visible_tokens(hits),
                "result_signature": result_signature(hits),
                "qmd_candidate_count": len(payload["results"]),
                "network_attempts": [],
            }
        )
    assert process.stderr is not None
    stderr = process.stderr.read()
    exit_status = process.wait()
    sampler.join(timeout=1)
    if exit_status != 0:
        raise QmdExecutionFailed(
            f"QMD query failed for {question['id']} with exit {exit_status}: {stderr[-2000:]}"
        )
    expected_rows = 1 + hot_runs
    if len(rows) != expected_rows:
        raise QmdOutputDrift(f"QMD query returned {len(rows)} rows, expected {expected_rows}")
    if state.get("sampler_error"):
        raise QmdExecutionFailed(f"QMD resource sampler unavailable: {state['sampler_error']}")
    attempts = sorted(state["network_connections"])
    invocation_id = hashlib.sha256(f"qmd-vsearch:{question['id']}".encode()).hexdigest()[:16]
    for row in rows:
        row["worker_invocation_id"] = invocation_id
        row["network_attempts"] = attempts
    resource = {
        "worker_invocation_id": invocation_id,
        "arm": "qmd-vsearch",
        "question_id": question["id"],
        "exit_status": exit_status,
        "peak_rss_bytes": state["peak_rss_bytes"],
        "peak_extra_child_processes": state["peak_extra_child_processes"],
        "network_connections": attempts,
        "stderr": stderr,
    }
    return rows, resource


def aggregate_arm(
    protocol: dict[str, Any],
    rows: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    arm: str,
) -> dict[str, Any]:
    arm_rows = [row for row in rows if row["arm"] == arm]
    per_question: dict[str, Any] = {}
    for question in protocol["questions"]:
        question_rows = [row for row in arm_rows if row["question_id"] == question["id"]]
        cold = next(row for row in question_rows if row["cache_state"] == "cold")
        per_question[question["id"]] = {
            "question": question["question"],
            "selected_documents": cold["selected_documents"],
            "relevant_hits": cold["quality"]["relevant_hits"],
            "missing": cold["quality"]["missing"],
            "recall_at_8": cold["quality"]["recall_at_8"],
            "mrr_at_8": cold["quality"]["mrr_at_8"],
            "ndcg_at_8": cold["quality"]["ndcg_at_8"],
            "first_pack_estimated_tokens": cold["first_pack_estimated_tokens"],
            "deterministic_across_cold_and_hot": len(
                {row["result_signature"] for row in question_rows}
            )
            == 1,
        }
    cold_latencies = [row["latency_ms"] for row in arm_rows if row["cache_state"] == "cold"]
    hot_latencies = [row["latency_ms"] for row in arm_rows if row["cache_state"] == "hot"]
    arm_resources = [item for item in resources if item["arm"] == arm]
    return {
        "questions": len(per_question),
        "runs": len(arm_rows),
        "recall_at_8": round(statistics.mean(x["recall_at_8"] for x in per_question.values()), 9),
        "mrr_at_8": round(statistics.mean(x["mrr_at_8"] for x in per_question.values()), 9),
        "ndcg_at_8": round(statistics.mean(x["ndcg_at_8"] for x in per_question.values()), 9),
        "first_pack_estimated_tokens": statistics.median(
            x["first_pack_estimated_tokens"] for x in per_question.values()
        ),
        "cold_latency_ms_p50": round(percentile(cold_latencies, 0.50), 6),
        "cold_latency_ms_p95": round(percentile(cold_latencies, 0.95), 6),
        "hot_latency_ms_p50": round(percentile(hot_latencies, 0.50), 6),
        "hot_latency_ms_p95": round(percentile(hot_latencies, 0.95), 6),
        "worker_process_starts": len(arm_resources),
        "peak_rss_bytes": max(item["peak_rss_bytes"] for item in arm_resources),
        "peak_extra_child_processes": max(
            item["peak_extra_child_processes"] for item in arm_resources
        ),
        "deterministic_question_rate": round(
            statistics.mean(x["deterministic_across_cold_and_hot"] for x in per_question.values()),
            9,
        ),
        "per_question": per_question,
    }


def comparison(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    deltas = {
        name: round(right[name] - left[name], 9)
        for name in ("recall_at_8", "mrr_at_8", "ndcg_at_8")
    }
    if all(value >= 0 for value in deltas.values()) and any(value > 0 for value in deltas.values()):
        claim = "improvement-demonstrated"
    elif all(value == 0 for value in deltas.values()):
        claim = "point-metric-non-inferior"
    else:
        claim = "regression-observed"
    return {
        "evidence_class": "verified-real-local-model",
        "functional_status": "available",
        "quality_delta": deltas,
        "quality_claim": claim,
    }


def _decision(comparisons: dict[str, dict[str, Any]], checks: dict[str, bool]) -> dict[str, Any]:
    eligible = [
        name
        for name, item in comparisons.items()
        if item["quality_claim"] == "improvement-demonstrated"
    ]
    worth = bool(eligible) and all(checks.values())
    if worth:
        result = "worth-entering-production-experiment"
    elif any(item["quality_claim"] == "regression-observed" for item in comparisons.values()):
        result = "regression-observed"
    else:
        result = "point-metric-non-inferior"
    return {
        "result": result,
        "eligible_arms": eligible,
        "reason_zh": (
            "至少一条真实模型路线在 Recall@8、MRR@8、nDCG@8 中有正增益且其余质量项不回退，完整性、资源和确定性门均通过。"
            if worth
            else "冻结质量与完成门没有同时形成进入生产实验的证据。"
        ),
        "production_default_changed": False,
    }


def evaluate_resource_limits(resources: dict[str, Any], limits: dict[str, Any]) -> dict[str, bool]:
    return {
        "index_build_within_limit": float(resources["first_index_seconds"])
        <= float(limits["index_build_seconds_max"]),
        "peak_rss_within_limit": int(resources["peak_rss_bytes"])
        <= int(limits["peak_rss_bytes_max"]),
        "index_bytes_within_limit": int(resources["index_bytes"])
        <= int(limits["index_bytes_max"]),
        "runtime_and_model_bytes_within_limit": int(resources["runtime_and_model_bytes"])
        <= int(limits["runtime_and_model_bytes_max"]),
        "extra_child_processes_within_limit": int(resources["peak_extra_child_processes"])
        <= int(limits["extra_child_processes_max"]),
        "network_attempts_within_limit": int(resources["network_attempts"])
        <= int(limits["network_calls_during_measurement_max"]),
    }


def run_benchmark(
    protocol_path: Path,
    model_manifest: Path,
    model_dir: Path,
    qmd_manifest: Path,
    qmd_package: Path,
    qmd_model: Path,
    node_executable: Path,
    source_corpus: Path,
    output: Path,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    preflight = validate_protocol(
        protocol_path,
        source_corpus,
        model_manifest,
        model_dir,
        qmd_manifest,
        qmd_package,
        qmd_model,
        node_executable,
    )
    protocol = preflight["protocol"]
    output.mkdir(parents=True)
    corpus = output / "corpus"
    corpus_info = copy_corpus(source_corpus, corpus)
    if corpus_info["repository_commit"] != protocol["corpus"]["bound_repository_commit"]:
        raise ValueError("copied corpus repository commit drift")
    index_dir = output / "index"
    bge_index_dir = index_dir / "bge"
    build_manifest, build_resource = _run_build_process(
        protocol_path, corpus, model_dir, bge_index_dir
    )
    documents = render_documents(corpus / "machine/knowledge.sqlite", protocol)
    qmd_root = index_dir / "qmd"
    qmd_build, qmd_projection, qmd_build_resource = _run_qmd_build_process(
        protocol,
        documents,
        qmd_package,
        qmd_model,
        node_executable,
        qmd_root,
        preflight["qmd"],
    )
    rows: list[dict[str, Any]] = []
    worker_resources: list[dict[str, Any]] = []
    for question_index, question in enumerate(protocol["questions"]):
        order = ARM_IDS[question_index % len(ARM_IDS) :] + ARM_IDS[: question_index % len(ARM_IDS)]
        for arm in order:
            if arm == "qmd-vsearch":
                current_rows, current_resource = _run_qmd_worker_process(
                    question,
                    protocol,
                    qmd_package,
                    qmd_model,
                    node_executable,
                    qmd_root,
                    preflight["qmd"],
                    documents,
                )
            else:
                current_rows, current_resource = _run_worker_process(
                    arm, question["id"], protocol_path, corpus, bge_index_dir, model_dir
                )
            rows.extend(current_rows)
            worker_resources.append(current_resource)
    summaries = {
        arm: aggregate_arm(protocol, rows, worker_resources, arm) for arm in ARM_IDS
    }
    comparisons = {
        "semantic-vector_vs_sqlite-current": comparison(
            summaries["sqlite-current"], summaries["semantic-vector"]
        ),
        "qmd-vsearch_vs_sqlite-current": comparison(
            summaries["sqlite-current"], summaries["qmd-vsearch"]
        ),
    }
    source_machine_after = sha256(source_corpus / "machine/knowledge.sqlite")
    source_legacy_after = sha256(source_corpus / "agent-index.sqlite")
    copied_machine_after = sha256(corpus / "machine/knowledge.sqlite")
    copied_legacy_after = sha256(corpus / "agent-index.sqlite")
    runtime_root = Path(sys.executable).resolve().parents[1]
    runtime_bytes = tree_bytes(runtime_root)
    model_bytes = preflight["model"]["total_bytes"]
    index_accounting = index_size_accounting(bge_index_dir, protocol)
    qmd_database_bytes = sum(
        item.stat().st_size for item in qmd_root.glob("index.sqlite*") if item.is_file()
    )
    qmd_runtime_bytes = tree_bytes(qmd_package.parents[1])
    qmd_model_bytes = qmd_model.stat().st_size
    index_bytes = index_accounting["index_bytes"] + qmd_database_bytes
    peak_rss = max(
        build_resource["peak_rss_bytes"],
        qmd_build_resource["peak_rss_bytes"],
        *(item["peak_rss_bytes"] for item in worker_resources),
    )
    peak_children = max(
        build_resource["peak_extra_child_processes"],
        qmd_build_resource["peak_extra_child_processes"],
        *(item["peak_extra_child_processes"] for item in worker_resources),
    )
    limits = protocol["resource_limits"]
    expected_rows = len(protocol["questions"]) * len(ARM_IDS) * (
        int(protocol["execution"]["cold_runs"]) + int(protocol["execution"]["hot_runs"])
    )
    resources = {
        "first_index_seconds": round(
            build_resource["wall_seconds"] + qmd_build_resource["wall_seconds"], 9
        ),
        "embedding_encode_seconds": build_manifest["encode_seconds"],
        "incremental_index_seconds": build_manifest["incremental_probe"]["seconds"],
        "index_bytes": index_bytes,
        "runtime_bytes": runtime_bytes + qmd_runtime_bytes,
        "model_bytes": model_bytes + qmd_model_bytes,
        "runtime_and_model_bytes": runtime_bytes
        + model_bytes
        + qmd_runtime_bytes
        + qmd_model_bytes,
        "bge": {
            "first_index_seconds": build_resource["wall_seconds"],
            "embedding_encode_seconds": build_manifest["encode_seconds"],
            "incremental_index_seconds": build_manifest["incremental_probe"]["seconds"],
            "index_bytes": index_accounting["index_bytes"],
            "runtime_bytes": runtime_bytes,
            "model_bytes": model_bytes,
        },
        "qmd": {
            "first_index_seconds": qmd_build_resource["wall_seconds"],
            "sdk_reported_wall_ms": qmd_build["wall_ms"],
            "sdk_reported_embed_duration_ms": qmd_build["embed"]["durationMs"],
            "index_database_bytes": qmd_database_bytes,
            "projection_bytes": qmd_projection["projection_bytes"],
            "runtime_bytes": qmd_runtime_bytes,
            "model_bytes": qmd_model_bytes,
            "network_connections": qmd_build_resource["network_connections"],
        },
        "bge_index": index_accounting,
        "peak_rss_bytes": peak_rss,
        "peak_extra_child_processes": peak_children,
        "worker_process_starts": len(worker_resources),
        "network_attempts": sum(len(row["network_attempts"]) for row in rows)
        + len(build_manifest["network_attempts"])
        + len(qmd_build_resource["network_connections"]),
        "limits": limits,
    }
    checks = {
        "raw_row_count_exact": len(rows) == expected_rows,
        "copied_sqlite_integrity": corpus_info["integrity"] == {"machine": "ok", "legacy": "ok"},
        "source_corpus_unchanged": source_machine_after
        == corpus_info["source_machine_sha256_before"]
        and source_legacy_after == corpus_info["source_legacy_sha256_before"],
        "copied_sqlite_unchanged": copied_machine_after == corpus_info["copied_machine_sha256"]
        and copied_legacy_after == corpus_info["copied_legacy_sha256"],
        "real_model_verified": preflight["model"]["revision"]
        == protocol["model"]["artifact_revision"],
        "qmd_runtime_and_model_verified": preflight["qmd"]["package_version"]
        == protocol["qmd"]["package_version"]
        and preflight["qmd"]["model_sha256"] == protocol["qmd"]["model_sha256"],
        "index_build_passed": build_manifest["status"] == "passed",
        "qmd_index_build_passed": qmd_build["status"]["needsEmbedding"] == 0
        and qmd_build["status"]["hasVectorIndex"] is True,
        "same_document_projection": qmd_projection["documents_digest"]
        == build_manifest["documents_digest"],
        "index_size_accounting_exact": index_bytes
        == index_accounting["index_payload_bytes"]
        + index_accounting["index_manifest_bytes"]
        + qmd_database_bytes,
        "all_rankings_deterministic": all(
            item["deterministic_question_rate"] == 1.0 for item in summaries.values()
        ),
        "same_budget_and_top_k": all(
            len(row["selected_documents"]) <= int(protocol["execution"]["max_results"])
            and row["first_pack_estimated_tokens"] <= int(protocol["execution"]["budget_tokens"])
            for row in rows
        ),
        "qmd_candidate_depth_exact": all(
            row.get("qmd_candidate_count") == int(protocol["qmd"]["candidate_depth"])
            for row in rows
            if row["arm"] == "qmd-vsearch"
        ),
        "network_attempts_zero": all(not row["network_attempts"] for row in rows)
        and not build_manifest["network_attempts"]
        and not qmd_build_resource["network_connections"],
        **evaluate_resource_limits(resources, limits),
    }
    raw = {
        "schema_version": SCHEMA_VERSION,
        "benchmark": protocol["benchmark"],
        "protocol_sha256": sha256(protocol_path),
        "model_manifest_sha256": sha256(model_manifest),
        "qmd_manifest_sha256": sha256(qmd_manifest),
        "corpus": {
            **corpus_info,
            "source_machine_sha256_after": source_machine_after,
            "source_legacy_sha256_after": source_legacy_after,
            "copied_machine_sha256_after": copied_machine_after,
            "copied_legacy_sha256_after": copied_legacy_after,
        },
        "rows": rows,
        "worker_resources": worker_resources,
        "index_build_resource": build_resource,
        "qmd_build": qmd_build,
        "qmd_projection": qmd_projection,
        "qmd_build_resource": qmd_build_resource,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if all(checks.values()) else "failed",
        "benchmark": protocol["benchmark"],
        "protocol_sha256": raw["protocol_sha256"],
        "model_status": {
            "semantic-vector": {
                "status": "verified-real-local-model",
                **preflight["model"],
                "engine": preflight["engine"],
            },
            "qmd-vsearch": {
                "status": "verified-real-local-model-and-runtime",
                **preflight["qmd"],
            },
        },
        "corpus": raw["corpus"],
        "checks": checks,
        "arms": summaries,
        "comparisons": comparisons,
        "resources": resources,
        "decision": _decision(comparisons, checks),
        "environment": {
            "measured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": sys.version,
            "python_executable": sys.executable,
            "node_executable": str(node_executable),
            "logical_processors": os.cpu_count(),
            "source_corpus": str(source_corpus),
            "output": str(output),
        },
        "artifacts": {
            "raw_results": str(output / "raw-results.json"),
            "report": str(output / "report.json"),
            "bge_index_manifest": str(bge_index_dir / "index-manifest.json"),
            "qmd_index": str(qmd_root / "index.sqlite"),
            "qmd_projection_manifest": str(qmd_root / "qmd-documents.json"),
        },
    }
    json_write(output / "raw-results.json", raw)
    json_write(output / "report.json", report)
    return report


def _write_unavailable(output: Path, kind: str, error: Exception) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": kind,
        "effect_claim": "not-measured",
        "error_type": type(error).__name__,
        "error": str(error),
    }
    json_write(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--protocol", type=Path, required=True)
    run.add_argument("--model-manifest", type=Path, required=True)
    run.add_argument("--model-dir", type=Path, required=True)
    run.add_argument("--qmd-manifest", type=Path, required=True)
    run.add_argument("--qmd-package", type=Path, required=True)
    run.add_argument("--qmd-model", type=Path, required=True)
    run.add_argument("--node-executable", type=Path, required=True)
    run.add_argument("--source-corpus", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    build = subparsers.add_parser("build-index")
    build.add_argument("--protocol", type=Path, required=True)
    build.add_argument("--corpus", type=Path, required=True)
    build.add_argument("--model-dir", type=Path, required=True)
    build.add_argument("--index", type=Path, required=True)
    worker = subparsers.add_parser("worker")
    worker.add_argument("--protocol", type=Path, required=True)
    worker.add_argument("--corpus", type=Path, required=True)
    worker.add_argument("--index", type=Path, required=True)
    worker.add_argument("--model-dir", type=Path, required=True)
    worker.add_argument("--arm", choices=PYTHON_ARM_IDS, required=True)
    worker.add_argument("--question-id", required=True)
    arguments = parser.parse_args()
    if arguments.command == "build-index":
        protocol = json_load(arguments.protocol)
        with network_guard() as attempts:
            result = _build_index(protocol, arguments.corpus, arguments.model_dir, arguments.index)
        result["network_attempts"] = attempts
        json_write(arguments.index / "index-manifest.json", result)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0 if result["status"] == "passed" else 1
    if arguments.command == "worker":
        return _emit_worker_rows(arguments)
    try:
        report = run_benchmark(
            arguments.protocol,
            arguments.model_manifest,
            arguments.model_dir,
            arguments.qmd_manifest,
            arguments.qmd_package,
            arguments.qmd_model,
            arguments.node_executable,
            arguments.source_corpus,
            arguments.output,
        )
    except EngineUnavailable as error:
        report = _write_unavailable(arguments.output, "engine-unavailable", error)
    except ModelUnavailable as error:
        report = _write_unavailable(arguments.output, "model-unavailable", error)
    except QmdUnavailable as error:
        report = _write_unavailable(arguments.output, "qmd-unavailable", error)
    except QmdExecutionFailed as error:
        report = _write_unavailable(arguments.output, "qmd-execution-failed", error)
    except QmdOutputDrift as error:
        report = _write_unavailable(arguments.output, "qmd-output-drift", error)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
