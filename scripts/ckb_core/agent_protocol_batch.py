"""Deterministic version matrix and batch upgrade contracts for Agent Protocol."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_protocol import AGENT_PROTOCOL_VERSION
from .common import CkbError


BATCH_MANIFEST_SCHEMA_VERSION = 1
BATCH_PLAN_SCHEMA_VERSION = 1
BATCH_STATE_SCHEMA_VERSION = 1
BATCH_EVIDENCE_SCHEMA_VERSION = 1

MANIFEST_KEYS = frozenset({"schema_version", "allowed_roots", "projects"})
PROJECT_KEYS = frozenset(
    {
        "project_id",
        "output",
        "workspace_roots",
        "source_version",
        "target_version",
        "harnesses",
        "python",
        "ckb",
        "expected_digest",
    }
)

SUPPORTED_HARNESSES = frozenset(
    {"codex", "claude", "opencode", "opencode-v2", "dsh", "gemini", "copilot", "cursor", "generic"}
)


@dataclass(frozen=True)
class ProtocolRelease:
    version: str
    source_commit: str
    next_version: str | None
    capabilities: tuple[str, ...]
    output_contract: bool


PROTOCOL_RELEASES: dict[str, ProtocolRelease] = {
    "1.0.0": ProtocolRelease(
        version="1.0.0",
        source_commit="c0e6cb650d707512d0edbcc481db373359a8f46f",
        next_version="1.3.0",
        capabilities=("retrieve-fast", "record", "agent-policy-check"),
        output_contract=False,
    ),
    "1.3.0": ProtocolRelease(
        version="1.3.0",
        source_commit="3f117b8a3565b24633b88799a3ee180d6b3451ab",
        next_version="1.4.0",
        capabilities=("brief-fast", "feedback", "maintain", "output-contract"),
        output_contract=True,
    ),
    "1.4.0": ProtocolRelease(
        version="1.4.0",
        source_commit="02b3f9bae10663f8d8d41626bb52454a226d4228",
        next_version="1.5.0",
        capabilities=("brief-fast", "feedback", "references", "maintain", "output-contract"),
        output_contract=True,
    ),
    "1.5.0": ProtocolRelease(
        version="1.5.0",
        source_commit="2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
        next_version=None,
        capabilities=("brief-fast", "feedback", "references", "research-gaps", "operations", "maintain", "output-contract"),
        output_contract=True,
    ),
}


if AGENT_PROTOCOL_VERSION not in PROTOCOL_RELEASES:
    raise RuntimeError(f"current Agent Protocol is absent from the batch version matrix: {AGENT_PROTOCOL_VERSION}")


def supported_upgrade_path(source_version: str, target_version: str) -> list[str]:
    """Return the frozen inclusive path, rejecting unknown or backward/jump-only routes."""
    if source_version not in PROTOCOL_RELEASES:
        raise CkbError(f"unsupported Agent Protocol source version: {source_version}")
    if target_version not in PROTOCOL_RELEASES:
        raise CkbError(f"unsupported Agent Protocol target version: {target_version}")
    path = [source_version]
    while path[-1] != target_version:
        next_version = PROTOCOL_RELEASES[path[-1]].next_version
        if next_version is None:
            raise CkbError(f"no Agent Protocol upgrade path: {source_version} -> {target_version}")
        path.append(next_version)
        if len(path) > len(PROTOCOL_RELEASES):
            raise RuntimeError("Agent Protocol version matrix contains a cycle")
    return path


def version_matrix() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "current_version": AGENT_PROTOCOL_VERSION,
        "releases": [
            {
                "version": release.version,
                "source_commit": release.source_commit,
                "next_version": release.next_version,
                "capabilities": list(release.capabilities),
                "output_contract": release.output_contract,
            }
            for release in PROTOCOL_RELEASES.values()
        ],
    }


def reject_unknown_fields(value: dict[str, Any], allowed: frozenset[str], location: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CkbError(f"unknown batch manifest field at {location}: {', '.join(unknown)}")


def require_absolute_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CkbError(f"batch manifest {field} must be a non-empty absolute path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise CkbError(f"batch manifest {field} must be absolute: {value}")
    return path.resolve()
