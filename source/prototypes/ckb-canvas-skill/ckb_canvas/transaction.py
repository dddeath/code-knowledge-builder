"""三角色 baseline、staging、promotion、重开验证与 rollback。"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable

from scripts.ckb_core.common import sha256_file

from .contracts import CanvasFailure, SchemaValidationError, artifact_state, validate_instance
from .freeze import FrozenInputs, recheck_frozen_inputs, resolve_scoped_path
from .graph import canonical_json_bytes


ROLE_ORDER = ("canvas", "validation_manifest", "rollback_manifest")
PROMOTION_ORDER = ("validation_manifest", "rollback_manifest", "canvas")
ROLE_SCHEMA = {
    "canvas": "json-canvas-1.0-ckb-subset.schema.json",
    "validation_manifest": "canvas-validation-manifest.schema.json",
    "rollback_manifest": "canvas-rollback-manifest.schema.json",
}
FaultHook = Callable[[str, str], None]


@dataclass(frozen=True)
class BaselineRole:
    role: str
    path: Path
    state: dict[str, Any]
    data: bytes | None
    backup_path: Path | None


@dataclass(frozen=True)
class ArtifactBaseline:
    roles: dict[str, BaselineRole]

    def request_states(self) -> dict[str, dict[str, Any]]:
        return {role: dict(self.roles[role].state) for role in ROLE_ORDER}

    def manifest_states(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for role in ROLE_ORDER:
            item = self.roles[role]
            if item.state["state"] == "absent":
                result[role] = {"state": "absent"}
            else:
                assert item.backup_path is not None
                result[role] = {
                    "state": "present",
                    "sha256": item.state["sha256"],
                    "backup_path": str(item.backup_path),
                    "backup_sha256": item.state["sha256"],
                }
        return result


@dataclass(frozen=True)
class StagedRole:
    role: str
    final_path: Path
    temporary_path: Path
    data: bytes
    sha256: str


@dataclass(frozen=True)
class StagedBundle:
    roles: dict[str, StagedRole]


@dataclass(frozen=True)
class PromotedBundle:
    roles: dict[str, StagedRole]


def _role_paths(frozen: FrozenInputs) -> dict[str, Path]:
    return {
        "canvas": frozen.target_canvas,
        "validation_manifest": frozen.validation_manifest,
        "rollback_manifest": frozen.rollback_manifest,
    }


def _same_state(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if actual.get("state") != expected.get("state"):
        return False
    return actual.get("state") != "present" or actual.get("sha256") == expected.get("sha256")


def _call_hook(hook: FaultHook | None, phase: str, role: str) -> None:
    if hook is not None:
        hook(phase, role)


def capture_baseline(frozen: FrozenInputs) -> ArtifactBaseline:
    """读取三个最终角色并与 request baseline 精确比较。"""

    expected = frozen.value["request"]["baseline"]
    replace = frozen.value["request"]["replace"]
    roles: dict[str, BaselineRole] = {}
    for role, path in _role_paths(frozen).items():
        actual = artifact_state(path)
        if actual["state"] == "unavailable":
            raise CanvasFailure(
                "io_failure", "baseline", f"target role is not a regular file: {path}", target_path=str(frozen.target_canvas)
            )
        if not _same_state(actual, expected[role]):
            reason = "target_exists" if not replace and actual["state"] == "present" else "promotion_drift"
            raise CanvasFailure(
                reason,
                "baseline",
                f"{role} baseline differs from request",
                target_path=str(frozen.target_canvas),
                before=expected["canvas"],
                after=artifact_state(frozen.target_canvas),
                changed=not _same_state(artifact_state(frozen.target_canvas), expected["canvas"]),
            )
        data: bytes | None = None
        backup_path: Path | None = None
        if actual["state"] == "present":
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise CanvasFailure(
                    "io_failure", "baseline", f"cannot read baseline: {path}: {exc}", target_path=str(frozen.target_canvas)
                ) from exc
            backup_path = frozen.backup_root / f"{role}.baseline"
        roles[role] = BaselineRole(role, path, actual, data, backup_path)

    if replace and frozen.backup_root.exists():
        if not frozen.backup_root.is_dir():
            raise CanvasFailure(
                "target_exists", "baseline", "backup_root exists and is not a directory", target_path=str(frozen.target_canvas)
            )
        try:
            if next(frozen.backup_root.iterdir(), None) is not None:
                raise CanvasFailure(
                    "target_exists", "baseline", "backup_root must be empty", target_path=str(frozen.target_canvas)
                )
        except OSError as exc:
            raise CanvasFailure(
                "io_failure", "baseline", f"cannot inspect backup_root: {exc}", target_path=str(frozen.target_canvas)
            ) from exc
    return ArtifactBaseline(roles)


def _write_temp(final_path: Path, data: bytes, role: str, hook: FaultHook | None) -> Path:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = -1
    temporary = ""
    try:
        _call_hook(hook, "before-write", role)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{final_path.name}.ckb-canvas-", suffix=".tmp", dir=final_path.parent)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(data)
            handle.flush()
            _call_hook(hook, "before-fsync", role)
            os.fsync(handle.fileno())
        _call_hook(hook, "after-write", role)
        reopened = Path(temporary).read_bytes()
        if reopened != data:
            raise OSError(f"staged bytes changed for {role}")
        return Path(temporary)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary:
            Path(temporary).unlink(missing_ok=True)
        raise


def _parse_and_validate(role: str, data: bytes, *, phase: str, target: Path) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
        validate_instance(ROLE_SCHEMA[role], value)
    except (UnicodeError, json.JSONDecodeError, SchemaValidationError) as exc:
        raise CanvasFailure("invalid_canvas", phase, f"{role} reopen validation failed: {exc}", target_path=str(target)) from exc
    return value


def stage_bundle(frozen: FrozenInputs, bytes_by_role: dict[str, bytes], *, fault_hook: FaultHook | None = None) -> StagedBundle:
    """三个角色同目录写临时文件，fsync、重开、parse 并核对 hash。"""

    if set(bytes_by_role) != set(ROLE_ORDER):
        raise CanvasFailure("invalid_canvas", "staging", "staged bundle roles are incomplete", target_path=str(frozen.target_canvas))
    staged: dict[str, StagedRole] = {}
    try:
        for role in ROLE_ORDER:
            final_path = _role_paths(frozen)[role]
            data = bytes_by_role[role]
            _parse_and_validate(role, data, phase="staging", target=frozen.target_canvas)
            temporary = _write_temp(final_path, data, role, fault_hook)
            digest = sha256_file(temporary)
            if digest != __import__("hashlib").sha256(data).hexdigest():
                raise OSError(f"staged hash changed for {role}")
            staged[role] = StagedRole(role, final_path, temporary, data, digest)
    except CanvasFailure:
        cleanup_staged(StagedBundle(staged))
        raise
    except OSError as exc:
        cleanup_staged(StagedBundle(staged))
        raise CanvasFailure(
            "io_failure", "staging", f"staging failed: {exc}", target_path=str(frozen.target_canvas)
        ) from exc
    return StagedBundle(staged)


def cleanup_staged(staged: StagedBundle) -> None:
    for item in staged.roles.values():
        try:
            item.temporary_path.unlink(missing_ok=True)
        except OSError:
            pass


def _assert_baseline(baseline: ArtifactBaseline, *, frozen: FrozenInputs, roles: tuple[str, ...] = ROLE_ORDER) -> None:
    for role in roles:
        expected = baseline.roles[role].state
        actual = artifact_state(baseline.roles[role].path)
        if not _same_state(actual, expected):
            before = baseline.roles["canvas"].state
            after = artifact_state(frozen.target_canvas)
            raise CanvasFailure(
                "promotion_drift",
                "promotion",
                f"{role} changed after baseline",
                target_path=str(frozen.target_canvas),
                before=before,
                after=after,
                changed=not _same_state(before, after),
            )


def _atomic_copy_bytes(path: Path, data: bytes, role: str, hook: FaultHook | None) -> None:
    temporary = _write_temp(path, data, role, hook)
    try:
        _call_hook(hook, "before-replace", role)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    if path.read_bytes() != data:
        raise OSError(f"atomic write verification failed for {role}")


def _write_backups(frozen: FrozenInputs, baseline: ArtifactBaseline, hook: FaultHook | None) -> None:
    present = [item for item in baseline.roles.values() if item.state["state"] == "present"]
    if not present:
        return
    frozen.backup_root.mkdir(parents=True, exist_ok=True)
    for item in present:
        assert item.data is not None and item.backup_path is not None
        _atomic_copy_bytes(item.backup_path, item.data, f"backup-{item.role}", hook)
        if sha256_file(item.backup_path) != item.state["sha256"]:
            raise OSError(f"backup hash mismatch for {item.role}")


def _restore_sidecars_after_pre_canvas_failure(
    promoted: list[str], baseline: ArtifactBaseline, staged: StagedBundle, hook: FaultHook | None
) -> None:
    for role in reversed(promoted):
        item = staged.roles[role]
        current = artifact_state(item.final_path)
        if current.get("state") != "present" or current.get("sha256") != item.sha256:
            continue  # 外部当前字节保留。
        base = baseline.roles[role]
        if base.state["state"] == "absent":
            item.final_path.unlink(missing_ok=True)
        else:
            assert base.data is not None
            _atomic_copy_bytes(item.final_path, base.data, f"compensate-{role}", hook)


def _verify_staged_role(item: StagedRole, frozen: FrozenInputs) -> None:
    """每次 replace 前重开临时角色，禁止 staging 漂移进入最终路径。"""

    try:
        data = item.temporary_path.read_bytes()
    except OSError as exc:
        raise CanvasFailure(
            "io_failure", "promotion", f"cannot reopen staged {item.role}: {exc}", target_path=str(frozen.target_canvas)
        ) from exc
    if __import__("hashlib").sha256(data).hexdigest() != item.sha256:
        try:
            _parse_and_validate(item.role, data, phase="reopen", target=frozen.target_canvas)
        except CanvasFailure:
            raise
        raise CanvasFailure(
            "invalid_canvas",
            "reopen",
            f"staged {item.role} bytes changed after validation",
            target_path=str(frozen.target_canvas),
        )
    _parse_and_validate(item.role, data, phase="reopen", target=frozen.target_canvas)
    if canonical_json_bytes(json.loads(data.decode("utf-8"))) != data:
        raise CanvasFailure(
            "invalid_canvas", "reopen", f"staged {item.role} is not canonical JSON", target_path=str(frozen.target_canvas)
        )


def promote_bundle(
    frozen: FrozenInputs,
    staged: StagedBundle,
    baseline: ArtifactBaseline,
    *,
    fault_hook: FaultHook | None = None,
) -> PromotedBundle:
    """重查输入/baseline，先 sidecar、后 Canvas 原子 promotion。"""

    promoted: list[str] = []
    try:
        recheck_frozen_inputs(frozen)
        _assert_baseline(baseline, frozen=frozen)
        _write_backups(frozen, baseline, fault_hook)
        _assert_baseline(baseline, frozen=frozen)
        for role in PROMOTION_ORDER:
            item = staged.roles[role]
            _assert_baseline(baseline, frozen=frozen, roles=(role,))
            _verify_staged_role(item, frozen)
            if role == "canvas":
                # Canvas 替换前两个 sidecar 仍必须是本次完整字节。
                for sidecar in ("validation_manifest", "rollback_manifest"):
                    current = artifact_state(staged.roles[sidecar].final_path)
                    expected = {"state": "present", "sha256": staged.roles[sidecar].sha256}
                    if not _same_state(current, expected):
                        raise CanvasFailure(
                            "promotion_drift",
                            "promotion",
                            f"promoted {sidecar} changed before Canvas promotion",
                            target_path=str(frozen.target_canvas),
                            before=baseline.roles["canvas"].state,
                            after=artifact_state(frozen.target_canvas),
                        )
            _call_hook(fault_hook, "promotion-ready", role)
            os.replace(item.temporary_path, item.final_path)
            promoted.append(role)
            if sha256_file(item.final_path) != item.sha256:
                raise CanvasFailure(
                    "promotion_drift",
                    "promotion",
                    f"{role} changed immediately after promotion",
                    target_path=str(frozen.target_canvas),
                    before=baseline.roles["canvas"].state,
                    after=artifact_state(frozen.target_canvas),
                    changed=not _same_state(baseline.roles["canvas"].state, artifact_state(frozen.target_canvas)),
                )
    except CanvasFailure:
        if "canvas" not in promoted:
            try:
                _restore_sidecars_after_pre_canvas_failure(promoted, baseline, staged, fault_hook)
            except OSError:
                pass
        cleanup_staged(staged)
        raise
    except OSError as exc:
        if "canvas" not in promoted:
            try:
                _restore_sidecars_after_pre_canvas_failure(promoted, baseline, staged, fault_hook)
            except OSError:
                pass
        cleanup_staged(staged)
        raise CanvasFailure(
            "io_failure",
            "promotion",
            f"promotion failed: {exc}",
            target_path=str(frozen.target_canvas),
            before=baseline.roles["canvas"].state,
            after=artifact_state(frozen.target_canvas),
            changed=not _same_state(baseline.roles["canvas"].state, artifact_state(frozen.target_canvas)),
        ) from exc
    return PromotedBundle(staged.roles)


def verify_promoted(promoted: PromotedBundle, *, frozen: FrozenInputs, baseline: ArtifactBaseline) -> None:
    """重开三个最终角色，核对 schema、hash 与规范字节。"""

    for role in ROLE_ORDER:
        item = promoted.roles[role]
        try:
            data = item.final_path.read_bytes()
        except OSError as exc:
            raise CanvasFailure(
                "io_failure",
                "reopen",
                f"cannot reopen {role}: {exc}",
                target_path=str(frozen.target_canvas),
                before=baseline.roles["canvas"].state,
                after=artifact_state(frozen.target_canvas),
                changed=not _same_state(baseline.roles["canvas"].state, artifact_state(frozen.target_canvas)),
            ) from exc
        if __import__("hashlib").sha256(data).hexdigest() != item.sha256:
            raise CanvasFailure(
                "promotion_drift",
                "reopen",
                f"{role} changed before reopen verification",
                target_path=str(frozen.target_canvas),
                before=baseline.roles["canvas"].state,
                after=artifact_state(frozen.target_canvas),
                changed=not _same_state(baseline.roles["canvas"].state, artifact_state(frozen.target_canvas)),
            )
        _parse_and_validate(role, data, phase="reopen", target=frozen.target_canvas)
        if canonical_json_bytes(json.loads(data.decode("utf-8"))) != data:
            raise CanvasFailure(
                "invalid_canvas", "reopen", f"{role} is not canonical JSON bytes", target_path=str(frozen.target_canvas)
            )


def _rollback_state(path: Path) -> dict[str, Any]:
    try:
        return artifact_state(path)
    except OSError:
        return {"state": "unavailable"}


def rollback_from_manifest(path: Path | str, expected_sha256: str, *, fault_hook: FaultHook | None = None) -> dict[str, Any]:
    """按完整 manifest hash guard 恢复三个角色并重开核对。"""

    manifest_path = Path(path).resolve()
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise CanvasFailure(
            "missing_target", "rollback", f"rollback manifest cannot be read: {exc}", operation="rollback", target_path=str(path)
        ) from exc
    full_hash = __import__("hashlib").sha256(manifest_bytes).hexdigest()
    if full_hash != expected_sha256:
        raise CanvasFailure(
            "rollback_drift",
            "rollback",
            f"rollback manifest hash differs: expected {expected_sha256}, got {full_hash}",
            operation="rollback",
            target_path=str(path),
        )
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        validate_instance("canvas-rollback-manifest.schema.json", manifest)
    except (UnicodeError, json.JSONDecodeError, SchemaValidationError) as exc:
        raise CanvasFailure(
            "invalid_request", "rollback", f"rollback manifest is invalid: {exc}", operation="rollback", target_path=str(path)
        ) from exc
    normalized = json.loads(json.dumps(manifest))
    normalized["guard"]["expected_manifest_content_sha256"] = "0" * 64
    content_hash = __import__("hashlib").sha256(canonical_json_bytes(normalized)).hexdigest()
    if content_hash != manifest["guard"]["expected_manifest_content_sha256"]:
        raise CanvasFailure(
            "rollback_drift", "rollback", "rollback manifest content guard differs", operation="rollback", target_path=str(path)
        )

    staging_root = Path(manifest["authorized_staging_root"]).resolve(strict=True)
    backup_root = resolve_scoped_path(staging_root, manifest["backup_root"], False)
    role_paths = {
        "canvas": resolve_scoped_path(staging_root, manifest["generated"]["canvas"]["path"], False),
        "validation_manifest": resolve_scoped_path(
            staging_root, manifest["generated"]["validation_manifest"]["path"], False
        ),
        "rollback_manifest": resolve_scoped_path(staging_root, manifest["rollback_manifest_path"], False),
    }
    expected_current = {
        "canvas": manifest["guard"]["expected_canvas_sha256"],
        "validation_manifest": manifest["guard"]["expected_validation_sha256"],
        "rollback_manifest": expected_sha256,
    }
    before_canvas = _rollback_state(role_paths["canvas"])
    for role in ROLE_ORDER:
        current = _rollback_state(role_paths[role])
        expected = {"state": "present", "sha256": expected_current[role]}
        if not _same_state(current, expected):
            raise CanvasFailure(
                "rollback_drift",
                "rollback",
                f"current {role} is not the generated role",
                operation="rollback",
                target_path=str(role_paths["canvas"]),
                before=before_canvas,
                after=current if role == "canvas" else before_canvas,
                changed=role == "canvas" and not _same_state(before_canvas, current),
            )

    backups: dict[str, bytes] = {}
    for role in ROLE_ORDER:
        baseline = manifest["baseline"][role]
        if baseline["state"] == "present":
            backup_path = resolve_scoped_path(backup_root, baseline["backup_path"], True)
            if sha256_file(backup_path) != baseline["backup_sha256"]:
                raise CanvasFailure(
                    "rollback_drift",
                    "rollback",
                    f"backup hash differs for {role}",
                    operation="rollback",
                    target_path=str(role_paths["canvas"]),
                    before=before_canvas,
                    after=before_canvas,
                )
            backups[role] = backup_path.read_bytes()

    try:
        for role in ROLE_ORDER:
            _call_hook(fault_hook, "rollback-ready", role)
            baseline = manifest["baseline"][role]
            if baseline["state"] == "absent":
                if sha256_file(role_paths[role]) != expected_current[role]:
                    raise CanvasFailure(
                        "rollback_drift",
                        "rollback",
                        f"{role} changed during rollback",
                        operation="rollback",
                        target_path=str(role_paths["canvas"]),
                        before=before_canvas,
                        after=_rollback_state(role_paths["canvas"]),
                    )
                role_paths[role].unlink()
            else:
                _atomic_copy_bytes(role_paths[role], backups[role], f"rollback-{role}", fault_hook)
        for role in ROLE_ORDER:
            actual = _rollback_state(role_paths[role])
            expected = manifest["baseline"][role]
            expected_state = {"state": expected["state"]}
            if expected["state"] == "present":
                expected_state["sha256"] = expected["sha256"]
            if not _same_state(actual, expected_state):
                raise OSError(f"rollback verification failed for {role}")
        if backup_root.exists():
            shutil.rmtree(backup_root)
    except CanvasFailure:
        raise
    except OSError as exc:
        raise CanvasFailure(
            "io_failure",
            "rollback",
            f"rollback I/O failed: {exc}",
            operation="rollback",
            target_path=str(role_paths["canvas"]),
            before=before_canvas,
            after=_rollback_state(role_paths["canvas"]),
            changed=not _same_state(before_canvas, _rollback_state(role_paths["canvas"])),
        ) from exc
    return {
        "schema_version": 1,
        "status": "passed",
        "operation": "rollback",
        "exit_code": 0,
        "manifest_path": str(manifest_path),
        "target_state": {
            "path": str(role_paths["canvas"]),
            "before": before_canvas,
            "after": _rollback_state(role_paths["canvas"]),
            "changed": not _same_state(before_canvas, _rollback_state(role_paths["canvas"])),
        },
        "roles_verified": 3,
    }
