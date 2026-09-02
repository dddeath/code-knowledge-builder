"""请求、路径、hash、record、snapshot 与 evidence 的闭合。"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
from typing import Any
import unicodedata

from scripts.ckb_core.common import sha256_file
from scripts.ckb_core.source_links import SourceLinkRenderer

from .contracts import CanvasFailure, SchemaValidationError, artifact_state, validate_instance


RECORD_REQUIRED = frozenset(
    {
        "schema_version",
        "status",
        "question",
        "profile",
        "budget",
        "estimated_tokens",
        "terms",
        "anchors",
        "seed_entity_ids",
        "selected_entities",
        "related_documents",
        "open_feedback",
        "pack",
        "record",
        "retrieval",
        "deterministic",
        "source_grounded",
        "grep_fallback_required",
    }
)
RECORD_OPTIONAL = frozenset({"retrieval_stats", "pending_agent_review"})
ENTITY_FIELDS = frozenset(
    {
        "entity_id",
        "name",
        "qualified_name",
        "kind",
        "source_path",
        "start_line",
        "end_line",
        "human_page_title",
        "human_page_file",
        "display_mode",
        "score",
        "score_breakdown",
        "reasons",
        "sections",
    }
)
DOCUMENT_FIELDS = frozenset(
    {
        "document_id",
        "title",
        "kind",
        "status",
        "human_file",
        "source_path",
        "start_line",
        "end_line",
        "severity",
        "target",
        "content_excerpt",
    }
)
FIXED_INPUT_FIELDS = (
    ("state_path", "state_sha256"),
    ("machine_index_path", "machine_index_sha256"),
    ("agent_pack_path", "agent_pack_sha256"),
    ("record_path", "record_sha256"),
    ("human_projection_path", "human_projection_sha256"),
    ("human_manifest_path", "human_manifest_sha256"),
    ("local_openers_path", "local_openers_sha256"),
)


@dataclass(frozen=True)
class EvidenceFile:
    relative_path: str
    path: Path
    sha256: str


@dataclass(frozen=True)
class SourceRange:
    relative_path: str
    path: Path
    start_line: int
    end_line: int
    sha256: str
    line_count: int


@dataclass(frozen=True)
class FrozenInputs:
    request_path: Path
    request_bytes: bytes
    request_sha256: str
    value: dict[str, Any]
    output_root: Path
    human_root: Path
    snapshot_root: Path
    staging_root: Path
    backup_root: Path
    target_canvas: Path
    validation_manifest: Path
    rollback_manifest: Path
    state: dict[str, Any]
    projection: dict[str, Any]
    human_manifest_value: dict[str, Any]
    openers: dict[str, Any]
    renderer: SourceLinkRenderer
    record: dict[str, Any]
    pack_bytes: bytes
    human_files: dict[str, EvidenceFile]
    source_files: dict[str, EvidenceFile]
    fixed_paths: tuple[tuple[Path, str], ...]


def _fail(
    reason: str,
    phase: str,
    detail: str,
    *,
    operation: str,
    target: Path | str,
    before: dict[str, Any] | None = None,
) -> CanvasFailure:
    return CanvasFailure(
        reason,
        phase,
        detail,
        operation=operation,
        target_path=str(target),
        before=before,
        after=before,
    )


def _canonical(path: Path, *, strict: bool = False) -> Path:
    try:
        return path.resolve(strict=strict)
    except OSError as exc:
        raise exc


def _inside(path: Path, root: Path) -> bool:
    left = os.path.normcase(str(path))
    right = os.path.normcase(str(root))
    try:
        return os.path.commonpath([left, right]) == right
    except ValueError:
        return False


def resolve_scoped_path(root: Path, candidate: Path | str, must_exist: bool) -> Path:
    """解析现存父目录及链接，并保证最终路径仍在根内。"""

    resolved_root = _canonical(Path(root), strict=True)
    if not resolved_root.is_dir():
        raise CanvasFailure(
            "missing_target", "request", f"scope root is not a directory: {root}", target_path=str(candidate)
        )
    raw = Path(candidate)
    try:
        resolved = _canonical(raw, strict=must_exist)
    except (FileNotFoundError, OSError) as exc:
        if must_exist and not raw.exists():
            raise CanvasFailure(
                "missing_target", "freeze", f"required path is missing: {raw}", target_path=str(raw)
            ) from exc
        raise CanvasFailure("io_failure", "freeze", f"path resolution failed: {raw}: {exc}", target_path=str(raw)) from exc
    if not _inside(resolved, resolved_root):
        raise CanvasFailure(
            "source_outside_scope",
            "freeze",
            f"resolved path is outside scope: {raw}",
            target_path=str(raw),
        )
    return resolved


def _load_json(path: Path, *, reason: str, phase: str, operation: str, target: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise _fail("missing_target", phase, f"missing JSON input: {path}", operation=operation, target=target) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail(reason, phase, f"invalid JSON input: {path}: {exc}", operation=operation, target=target) from exc
    if not isinstance(value, dict):
        raise _fail(reason, phase, f"JSON root must be an object: {path}", operation=operation, target=target)
    return value


def _expect_hash(path: Path, expected: str, *, operation: str, target: Path) -> None:
    if not path.is_file():
        raise _fail("missing_target", "freeze", f"fixed input is missing: {path}", operation=operation, target=target)
    try:
        actual = sha256_file(path)
    except OSError as exc:
        raise _fail("io_failure", "freeze", f"cannot hash input: {path}: {exc}", operation=operation, target=target) from exc
    if actual != expected:
        raise _fail(
            "input_drift",
            "freeze",
            f"fixed input hash changed: {path}: expected {expected}, got {actual}",
            operation=operation,
            target=target,
        )


def _normalized_equal(left: Path | str, right: Path | str) -> bool:
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def _validate_record(record: dict[str, Any], *, operation: str, target: Path) -> None:
    keys = set(record)
    if keys - RECORD_REQUIRED - RECORD_OPTIONAL:
        unknown = sorted(keys - RECORD_REQUIRED - RECORD_OPTIONAL)[0]
        raise _fail(
            "unsupported_record_schema",
            "freeze",
            f"record has unknown field: {unknown}",
            operation=operation,
            target=target,
        )
    missing = RECORD_REQUIRED - keys
    if missing:
        raise _fail(
            "unsupported_record_schema",
            "freeze",
            f"record is missing field: {sorted(missing)[0]}",
            operation=operation,
            target=target,
        )
    if (
        record.get("schema_version") != 3
        or record.get("status") != "passed"
        or record.get("deterministic") is not True
        or record.get("source_grounded") is not True
        or record.get("grep_fallback_required") is not False
        or record.get("pending_agent_review", False) is not False
    ):
        raise _fail(
            "unsupported_record_schema",
            "freeze",
            "record is not the accepted deterministic machine schema 3 variant",
            operation=operation,
            target=target,
        )
    for key in ("selected_entities", "related_documents"):
        if not isinstance(record.get(key), list):
            raise _fail(
                "unsupported_record_schema", "freeze", f"record.{key} must be an array", operation=operation, target=target
            )
    for index, item in enumerate(record["selected_entities"]):
        if not isinstance(item, dict) or set(item) - ENTITY_FIELDS:
            raise _fail(
                "unsupported_record_schema",
                "freeze",
                f"selected_entities[{index}] has an unknown field or invalid shape",
                operation=operation,
                target=target,
            )
    for index, item in enumerate(record["related_documents"]):
        if not isinstance(item, dict) or set(item) - DOCUMENT_FIELDS:
            raise _fail(
                "unsupported_record_schema",
                "freeze",
                f"related_documents[{index}] has an unknown field or invalid shape",
                operation=operation,
                target=target,
            )


def _sqlite_meta(path: Path, *, operation: str, target: Path) -> dict[str, str]:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        rows = connection.execute("SELECT key, value FROM meta ORDER BY key").fetchall()
    except (sqlite3.Error, OSError) as exc:
        raise _fail("snapshot_mismatch", "freeze", f"SQLite meta cannot be read: {exc}", operation=operation, target=target) from exc
    finally:
        if connection is not None:
            connection.close()
    return {str(key): str(value) for key, value in rows}


def _projection_files(projection: dict[str, Any], manifest: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for page in projection.get("pages", []):
        if isinstance(page, dict) and isinstance(page.get("file"), str):
            values.add(page["file"])
    work_index = projection.get("work_record_index")
    if isinstance(work_index, dict) and isinstance(work_index.get("file"), str):
        values.add(work_index["file"])
    ownership = projection.get("generated_ownership")
    if isinstance(ownership, dict):
        for item in ownership.get("files", []):
            if isinstance(item, str):
                values.add(item)
            elif isinstance(item, dict) and isinstance(item.get("path"), str):
                values.add(item["path"])
    for item in manifest.get("generated_files", []):
        if isinstance(item, str):
            values.add(item)
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            values.add(item["path"])
    return values


def _relative_file(root: Path, item: dict[str, Any], *, operation: str, target: Path) -> EvidenceFile:
    relative = str(item["relative_path"])
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative:
        raise _fail("source_outside_scope", "freeze", f"invalid relative evidence path: {relative}", operation=operation, target=target)
    path = resolve_scoped_path(root, root.joinpath(*pure.parts), True)
    _expect_hash(path, str(item["sha256"]), operation=operation, target=target)
    return EvidenceFile(relative, path, str(item["sha256"]))


def load_and_freeze_request(path: Path | str, *, operation: str = "generate") -> FrozenInputs:
    """严格解析请求并闭合全部固定输入。"""

    request_path = Path(path).resolve()
    placeholder_target = str(request_path.with_suffix(".canvas"))
    try:
        request_bytes = request_path.read_bytes()
        value = json.loads(request_bytes.decode("utf-8"))
        validate_instance("canvas-request.schema.json", value)
    except FileNotFoundError as exc:
        raise CanvasFailure(
            "invalid_request", "request", f"request is missing: {request_path}", operation=operation, target_path=placeholder_target
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaValidationError) as exc:
        raise CanvasFailure(
            "invalid_request", "request", f"request is invalid: {exc}", operation=operation, target_path=placeholder_target
        ) from exc
    if not isinstance(value, dict):
        raise CanvasFailure(
            "invalid_request", "request", "request root must be an object", operation=operation, target_path=placeholder_target
        )

    ckb = value["ckb"]
    req = value["request"]
    req["title"] = unicodedata.normalize("NFC", req["title"])
    if any(ord(char) < 32 and char not in "\n\t" for char in req["title"]):
        raise _fail("invalid_request", "request", "title contains a control character", operation=operation, target=placeholder_target)

    target_canvas_raw = Path(req["target_canvas_path"])
    before = artifact_state(target_canvas_raw)
    if target_canvas_raw.suffix.lower() != ".canvas":
        raise _fail(
            "invalid_request", "request", "target_canvas_path must end with .canvas", operation=operation, target=target_canvas_raw, before=before
        )
    staging_root = Path(req["authorized_staging_root"]).resolve(strict=True)
    if not staging_root.is_dir():
        raise _fail("missing_target", "request", "authorized_staging_root must exist", operation=operation, target=target_canvas_raw, before=before)
    target_canvas = resolve_scoped_path(staging_root, target_canvas_raw, False)
    validation_manifest = resolve_scoped_path(staging_root, Path(str(target_canvas_raw) + ".validation.json"), False)
    rollback_manifest = resolve_scoped_path(staging_root, Path(str(target_canvas_raw) + ".rollback.json"), False)
    backup_root = resolve_scoped_path(staging_root, Path(req["backup_root"]), False)

    output_root = Path(ckb["output_root"]).resolve(strict=True)
    human_root = resolve_scoped_path(output_root, Path(ckb["human_root"]), True)
    expected_human_root = (output_root / "human").resolve(strict=True)
    if not _normalized_equal(human_root, expected_human_root):
        raise _fail("source_outside_scope", "freeze", "human_root is not output_root/human", operation=operation, target=target_canvas, before=before)

    fixed_paths: list[tuple[Path, str]] = []
    for path_field, hash_field in FIXED_INPUT_FIELDS:
        fixed_path = resolve_scoped_path(output_root, Path(ckb[path_field]), True)
        _expect_hash(fixed_path, ckb[hash_field], operation=operation, target=target_canvas)
        fixed_paths.append((fixed_path, ckb[hash_field]))

    fixed_by_name = {field: fixed_paths[index][0] for index, (field, _hash) in enumerate(FIXED_INPUT_FIELDS)}
    state_path = fixed_by_name["state_path"]
    index_path = fixed_by_name["machine_index_path"]
    pack_path = fixed_by_name["agent_pack_path"]
    record_path = fixed_by_name["record_path"]
    projection_path = fixed_by_name["human_projection_path"]
    manifest_path = fixed_by_name["human_manifest_path"]
    openers_path = fixed_by_name["local_openers_path"]

    expected_paths = {
        state_path: output_root / "state.json",
        index_path: output_root / "machine" / "knowledge.sqlite",
        projection_path: human_root / "projection.json",
        manifest_path: human_root / "manifest.json",
        openers_path: output_root / "local-openers.json",
    }
    for actual, expected in expected_paths.items():
        if not _normalized_equal(actual, expected):
            raise _fail("source_outside_scope", "freeze", f"fixed role uses unexpected path: {actual}", operation=operation, target=target_canvas, before=before)
    agent_pack_root = (output_root / "machine" / "agent-packs").resolve(strict=True)
    if not _inside(pack_path, agent_pack_root) or not _inside(record_path, agent_pack_root):
        raise _fail("source_outside_scope", "freeze", "pack or record is outside machine/agent-packs", operation=operation, target=target_canvas, before=before)

    state = _load_json(state_path, reason="snapshot_mismatch", phase="freeze", operation=operation, target=target_canvas)
    projection = _load_json(projection_path, reason="input_drift", phase="freeze", operation=operation, target=target_canvas)
    human_manifest_value = _load_json(manifest_path, reason="input_drift", phase="freeze", operation=operation, target=target_canvas)
    openers = _load_json(openers_path, reason="snapshot_mismatch", phase="freeze", operation=operation, target=target_canvas)
    record = _load_json(record_path, reason="unsupported_record_schema", phase="freeze", operation=operation, target=target_canvas)
    _validate_record(record, operation=operation, target=target_canvas)

    if pack_path.stem != record_path.stem or not _normalized_equal(record.get("pack", ""), pack_path) or not _normalized_equal(record.get("record", ""), record_path):
        raise _fail("pack_record_mismatch", "freeze", "pack and record path crosslinks do not match", operation=operation, target=target_canvas, before=before)

    repository = state.get("repository") if isinstance(state.get("repository"), dict) else {}
    snapshot = state.get("source_snapshot") if isinstance(state.get("source_snapshot"), dict) else {}
    if (
        repository.get("commit") != ckb["snapshot_commit"]
        or snapshot.get("commit") != ckb["snapshot_commit"]
        or repository.get("tree") != ckb["snapshot_tree"]
        or snapshot.get("tree") != ckb["snapshot_tree"]
    ):
        raise _fail("snapshot_mismatch", "freeze", "state commit/tree does not match request", operation=operation, target=target_canvas, before=before)
    meta = _sqlite_meta(index_path, operation=operation, target=target_canvas)
    if meta.get("status") != "ready" or meta.get("schema_version") != "3" or meta.get("repository_commit") != ckb["snapshot_commit"]:
        raise _fail("snapshot_mismatch", "freeze", "SQLite meta does not match schema/status/commit", operation=operation, target=target_canvas, before=before)

    if openers.get("schema_version") != 1 or openers.get("source_view") != "baseline":
        raise _fail("snapshot_mismatch", "freeze", "local-openers must be schema 1 baseline view", operation=operation, target=target_canvas, before=before)
    try:
        snapshot_root = Path(str(snapshot["root"])).resolve(strict=True)
        opener_snapshot = Path(str(openers["baseline_snapshot_root"])).resolve(strict=True)
        renderer = SourceLinkRenderer(openers)
    except (KeyError, OSError, ValueError, RuntimeError) as exc:
        raise _fail("snapshot_mismatch", "freeze", f"baseline source root is invalid: {exc}", operation=operation, target=target_canvas, before=before) from exc
    if not _normalized_equal(snapshot_root, opener_snapshot):
        raise _fail("snapshot_mismatch", "freeze", "state and opener baseline roots differ", operation=operation, target=target_canvas, before=before)

    allowed_human = _projection_files(projection, human_manifest_value)
    human_files: dict[str, EvidenceFile] = {}
    for item in ckb["frozen_evidence"]["human_files"]:
        evidence = _relative_file(human_root, item, operation=operation, target=target_canvas)
        if evidence.relative_path not in allowed_human:
            raise _fail("missing_backlink", "freeze", f"human evidence is absent from projection/manifest: {evidence.relative_path}", operation=operation, target=target_canvas, before=before)
        human_files[evidence.relative_path] = evidence
    if "INDEX.md" not in human_files:
        raise _fail("missing_backlink", "freeze", "frozen human evidence must include INDEX.md", operation=operation, target=target_canvas, before=before)

    source_files: dict[str, EvidenceFile] = {}
    for item in ckb["frozen_evidence"]["source_files"]:
        evidence = _relative_file(snapshot_root, item, operation=operation, target=target_canvas)
        source_files[evidence.relative_path] = evidence

    return FrozenInputs(
        request_path=request_path,
        request_bytes=request_bytes,
        request_sha256=sha256_file(request_path),
        value=value,
        output_root=output_root,
        human_root=human_root,
        snapshot_root=snapshot_root,
        staging_root=staging_root,
        backup_root=backup_root,
        target_canvas=target_canvas,
        validation_manifest=validation_manifest,
        rollback_manifest=rollback_manifest,
        state=state,
        projection=projection,
        human_manifest_value=human_manifest_value,
        openers=openers,
        renderer=renderer,
        record=record,
        pack_bytes=pack_path.read_bytes(),
        human_files=human_files,
        source_files=source_files,
        fixed_paths=tuple(fixed_paths),
    )


def recheck_frozen_inputs(frozen: FrozenInputs) -> None:
    """promotion 前重算请求、固定输入与 evidence hash。"""

    paths = [(frozen.request_path, frozen.request_sha256), *frozen.fixed_paths]
    paths.extend((item.path, item.sha256) for item in frozen.human_files.values())
    paths.extend((item.path, item.sha256) for item in frozen.source_files.values())
    for path, expected in paths:
        try:
            actual_path = path.resolve(strict=True)
        except (OSError, FileNotFoundError) as exc:
            raise CanvasFailure(
                "input_drift", "promotion", f"frozen input disappeared: {path}: {exc}", target_path=str(frozen.target_canvas)
            ) from exc
        root = frozen.staging_root if path == frozen.request_path and _inside(actual_path, frozen.staging_root) else None
        if root is not None and not _inside(actual_path, root):
            raise CanvasFailure(
                "source_outside_scope", "promotion", f"frozen input resolved outside scope: {path}", target_path=str(frozen.target_canvas)
            )
        try:
            actual = sha256_file(actual_path)
        except OSError as exc:
            raise CanvasFailure("io_failure", "promotion", f"cannot rehash input: {path}: {exc}", target_path=str(frozen.target_canvas)) from exc
        if actual != expected:
            raise CanvasFailure(
                "input_drift",
                "promotion",
                f"frozen input changed: {path}: expected {expected}, got {actual}",
                target_path=str(frozen.target_canvas),
            )


def validate_source_range(path: Path, start: int, end: int, *, kind: str = "entity", relative_path: str = "") -> SourceRange:
    """验证普通范围及唯一 file 末尾哨兵。"""

    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int):
        raise CanvasFailure("invalid_source_range", "freeze", "source range must use integer line numbers", target_path=str(path))
    try:
        with path.open("r", encoding="utf-8") as handle:
            line_count = sum(1 for _line in handle)
    except (OSError, UnicodeError) as exc:
        raise CanvasFailure("io_failure", "freeze", f"cannot read source range: {path}: {exc}", target_path=str(path)) from exc
    ordinary = 1 <= start <= end <= line_count
    sentinel = kind == "file" and start == 1 and end == line_count + 1
    if not (ordinary or sentinel):
        raise CanvasFailure(
            "invalid_source_range", "freeze", f"invalid source range {start}-{end} for {line_count} lines", target_path=str(path)
        )
    return SourceRange(relative_path, path, start, end, sha256_file(path), line_count)
