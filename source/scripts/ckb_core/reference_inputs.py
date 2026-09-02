"""Stable input-adapter boundary for local references and future Web capture."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


LOCAL_FILE_ADAPTER_ID = "local-file-v1"
WEB_INPUT_ADAPTER_ID = "web-snapshot-v1"


@dataclass(frozen=True)
class ReferenceInputRequest:
    """Metadata shared by input adapters before reference review begins."""

    source: str
    title: str
    origin: str
    license_name: str
    author: str | None = None


@dataclass(frozen=True)
class PreparedReferenceInput:
    """An immutable local artifact produced by an input adapter."""

    adapter_id: str
    local_file: Path
    media_type: str
    provenance: dict[str, Any]


class ReferenceInputAdapter(Protocol):
    """Prepare one immutable local artifact without reviewing its claims."""

    adapter_id: str

    def prepare(self, request: ReferenceInputRequest) -> PreparedReferenceInput:
        ...


def web_input_adapter_contract() -> dict[str, Any]:
    """Return the frozen Web boundary; this module deliberately performs no fetch."""

    return {
        "schema_version": 1,
        "adapter_id": WEB_INPUT_ADAPTER_ID,
        "implementation_status": "not-implemented",
        "input": {
            "url": "absolute-http-or-https-url",
            "requested_at_utc": "rfc3339",
            "request_headers_allowlist": ["Accept", "Accept-Language", "User-Agent"],
            "max_response_bytes": "positive-integer",
            "timeout_seconds": "positive-integer",
        },
        "output": {
            "local_file": "immutable-response-body",
            "media_type": "validated-content-type",
            "provenance": [
                "requested_url",
                "final_url",
                "retrieved_at_utc",
                "response_sha256",
                "response_size",
                "status_code",
            ],
        },
        "boundary": [
            "adapter-only-produces-local-artifact",
            "redirects-and-network-policy-are-caller-owned",
            "output-still-requires-reference-ingest-and-agent-review",
            "web-content-never-becomes-a-code-entity",
        ],
    }
