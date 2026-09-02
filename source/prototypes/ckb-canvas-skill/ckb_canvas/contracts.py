"""Schema 1 的确定性字段校验与稳定命令结果。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMA_NAMES = frozenset(
    {
        "benchmark-run.schema.json",
        "benchmark-session-result.schema.json",
        "benchmark-summary.schema.json",
        "canvas-failure.schema.json",
        "canvas-request.schema.json",
        "canvas-rollback-manifest.schema.json",
        "canvas-success.schema.json",
        "canvas-validation-manifest.schema.json",
        "json-canvas-1.0-ckb-subset.schema.json",
    }
)


class SchemaValidationError(ValueError):
    """一个 JSON 值不满足冻结 schema。"""

    def __init__(self, path: str, detail: str) -> None:
        super().__init__(f"{path}: {detail}")
        self.path = path
        self.detail = detail


def load_schema(name: str) -> dict[str, Any]:
    """读取一个固定名称的原型 schema。"""

    if name not in SCHEMA_NAMES:
        raise SchemaValidationError("$", f"unknown schema: {name}")
    try:
        value = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SchemaValidationError("$", f"schema cannot be loaded: {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise SchemaValidationError("$", f"schema root is not an object: {name}")
    return value


def _kind_matches(kind: str, value: Any) -> bool:
    if kind == "object":
        return isinstance(value, dict)
    if kind == "array":
        return isinstance(value, list)
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "null":
        return value is None
    return False


def _type_label(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return type(value).__name__


def _matches(schema: dict[str, Any], value: Any, path: str) -> bool:
    try:
        _validate(schema, value, path)
    except SchemaValidationError:
        return False
    return True


def _validate(schema: dict[str, Any], value: Any, path: str) -> None:
    """执行本原型九个 schema 使用到的 Draft 2020-12 子集。"""

    if "allOf" in schema:
        for index, subschema in enumerate(schema["allOf"]):
            _validate(subschema, value, f"{path}<allOf[{index}]>")
    if "if" in schema and _matches(schema["if"], value, path):
        if "then" in schema:
            _validate(schema["then"], value, f"{path}<then>")
    if "oneOf" in schema:
        matches = sum(1 for item in schema["oneOf"] if _matches(item, value, path))
        if matches != 1:
            raise SchemaValidationError(path, f"oneOf matched {matches} branches")

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(path, f"expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(path, f"value is outside enum: {value!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = [expected_type] if isinstance(expected_type, str) else list(expected_type)
        if not any(_kind_matches(kind, value) for kind in allowed):
            raise SchemaValidationError(path, f"expected {'|'.join(allowed)}, got {_type_label(value)}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                raise SchemaValidationError(path, f"missing required field: {name}")
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise SchemaValidationError(path, f"unknown field: {unknown[0]}")
        for name, subschema in properties.items():
            if name in value:
                _validate(subschema, value[name], f"{path}.{name}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            raise SchemaValidationError(path, f"requires at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            raise SchemaValidationError(path, f"allows at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            seen: set[str] = set()
            for item in value:
                marker = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                if marker in seen:
                    raise SchemaValidationError(path, "array items must be unique")
                seen.add(marker)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate(item_schema, item, f"{path}[{index}]")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            raise SchemaValidationError(path, f"string is shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            raise SchemaValidationError(path, f"string is longer than {schema['maxLength']}")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            raise SchemaValidationError(path, f"string does not match {schema['pattern']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaValidationError(path, f"value is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise SchemaValidationError(path, f"value is above {schema['maximum']}")


def validate_instance(schema_name: str, value: Any) -> None:
    """按固定 schema 名校验一个内存 JSON 值。"""

    _validate(load_schema(schema_name), value, "$")


EXIT_BY_REASON = {
    "invalid_request": 2,
    "unsupported_record_schema": 2,
    "pack_record_mismatch": 2,
    "input_drift": 2,
    "snapshot_mismatch": 2,
    "source_outside_scope": 2,
    "target_exists": 2,
    "missing_backlink": 2,
    "missing_target": 2,
    "invalid_source_range": 2,
    "budget_exceeded": 5,
    "duplicate_id": 5,
    "dangling_edge": 5,
    "invalid_canvas": 5,
    "promotion_drift": 6,
    "rollback_drift": 6,
    "io_failure": 7,
}

RECOVERY_BY_REASON: dict[str, tuple[str, tuple[str, ...]]] = {
    "invalid_request": ("correct-request", ("canvas-request.json",)),
    "unsupported_record_schema": ("regenerate-request", ("machine record schema 3",)),
    "pack_record_mismatch": ("use-matching-pack-record", ("matching pack and record",)),
    "input_drift": ("restore-input", ("original frozen input bytes",)),
    "snapshot_mismatch": ("use-fixed-snapshot", ("matching state, SQLite meta, and snapshot",)),
    "source_outside_scope": ("move-into-scope", ("authorized in-scope path",)),
    "target_exists": ("choose-new-target-or-pin-baseline", ("new target or complete replace baseline",)),
    "missing_backlink": ("supply-reviewed-backlink", ("reviewed human page or source range",)),
    "missing_target": ("restore-target", ("missing frozen file",)),
    "invalid_source_range": ("correct-source-range", ("valid record source range",)),
    "budget_exceeded": ("reduce-required-set", ("required entries within frozen budget",)),
    "duplicate_id": ("fix-generator", ("collision-free canonical targets",)),
    "dangling_edge": ("fix-generator", ("closed edge endpoints",)),
    "invalid_canvas": ("fix-generator", ("valid canonical Canvas",)),
    "promotion_drift": ("rebaseline-after-review", ("reviewed current target hash",)),
    "rollback_drift": ("manual-review-current-bytes", ("current role and backup hashes",)),
    "io_failure": ("retry-io", ("writable staging and backup paths",)),
}


def artifact_state(path: Path) -> dict[str, Any]:
    """返回 schema 化的文件存在性与 hash；读失败由调用方处理。"""

    if not path.exists():
        return {"state": "absent"}
    if not path.is_file():
        return {"state": "unavailable"}
    from scripts.ckb_core.common import sha256_file

    return {"state": "present", "sha256": sha256_file(path)}


@dataclass
class CanvasFailure(Exception):
    """可直接转换为冻结失败 schema 的命令错误。"""

    reason: str
    phase: str
    detail: str
    operation: str = "generate"
    target_path: str = "TARGET.canvas"
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    changed: bool = False
    required_inputs: Iterable[str] | None = None

    @property
    def exit_code(self) -> int:
        return EXIT_BY_REASON[self.reason]

    def to_dict(self) -> dict[str, Any]:
        action, default_inputs = RECOVERY_BY_REASON[self.reason]
        value = {
            "schema_version": 1,
            "status": "failed",
            "operation": self.operation,
            "reason": self.reason,
            "phase": self.phase,
            "exit_code": self.exit_code,
            "detail": self.detail[:1000] or self.reason,
            "target_state": {
                "path": self.target_path if len(self.target_path) >= 3 else "TARGET.canvas",
                "before": self.before or {"state": "unavailable"},
                "after": self.after or self.before or {"state": "unavailable"},
                "changed": bool(self.changed),
            },
            "recovery": {
                "action": action,
                "required_inputs": list(self.required_inputs or default_inputs),
            },
        }
        validate_instance("canvas-failure.schema.json", value)
        return value


@dataclass(frozen=True)
class CanvasSuccess:
    """已通过 schema 的成功 stdout 对象。"""

    value: dict[str, Any]

    def __post_init__(self) -> None:
        validate_instance("canvas-success.schema.json", self.value)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.value)
