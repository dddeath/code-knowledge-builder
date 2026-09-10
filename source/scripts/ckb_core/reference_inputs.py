"""Deterministic input adapters for local references and explicit Web snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import socket
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .common import CkbError, json_load, json_write, path_inside, sha256_file, utc_now


LOCAL_FILE_ADAPTER_ID = "local-file-v1"
WEB_INPUT_ADAPTER_ID = "web-snapshot-v1"
DEFAULT_WEB_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
DEFAULT_WEB_TIMEOUT_SECONDS = 20
WEB_MEDIA_TYPES = {"text/html", "application/xhtml+xml"}
WEB_RESPONSE_HEADER_OMIT = {"proxy-authenticate", "set-cookie", "www-authenticate"}
_EXCLUDED_TAGS = {"aside", "footer", "header", "nav", "noscript", "script", "style", "svg", "template"}
_NAVIGATION_ROLES = {"banner", "complementary", "contentinfo", "navigation", "search"}
_BLOCK_TAGS = {
    "address", "article", "blockquote", "dd", "div", "dl", "dt", "figcaption", "figure", "h1", "h2", "h3",
    "h4", "h5", "h6", "li", "main", "p", "pre", "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr",
}


class WebSnapshotError(CkbError):
    """One explicit Web snapshot could not be captured or validated."""


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


@dataclass(frozen=True)
class PreparedWebSnapshot:
    """A validated response body held in memory until reference commit begins."""

    raw_bytes: bytes
    decoded_text: str
    provenance: dict[str, Any]
    extraction: dict[str, Any]


class ReferenceInputAdapter(Protocol):
    """Prepare one immutable local artifact without reviewing its claims."""

    adapter_id: str

    def prepare(self, request: ReferenceInputRequest) -> PreparedReferenceInput:
        ...


def _validated_url(value: str, field: str) -> str:
    normalized = value.strip()
    parsed = urlsplit(normalized)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        raise WebSnapshotError(f"{field} must be an absolute HTTP or HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise WebSnapshotError(f"{field} must not contain embedded credentials")
    return normalized


def _validated_timestamp(value: str, field: str) -> str:
    normalized = value.strip()
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WebSnapshotError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise WebSnapshotError(f"{field} must include a UTC offset")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalized_response_headers(headers: Any) -> tuple[dict[str, list[str]], list[str]]:
    values: dict[str, list[str]] = {}
    omitted: set[str] = set()
    pairs = headers.raw_items() if hasattr(headers, "raw_items") else getattr(headers, "items", lambda: [])()
    for raw_name, raw_value in pairs:
        name = str(raw_name).strip().casefold()
        value = str(raw_value).strip()
        if not name or "\r" in value or "\n" in value:
            raise WebSnapshotError("response headers must use single-line names and values")
        if name in WEB_RESPONSE_HEADER_OMIT:
            omitted.add(name)
            continue
        values.setdefault(name, []).append(value)
    return {name: values[name] for name in sorted(values)}, sorted(omitted)


def _content_type_details(content_type: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in content_type.split(";")]
    media_type = parts[0].casefold()
    if media_type not in WEB_MEDIA_TYPES:
        raise WebSnapshotError(f"Web snapshot response must be HTML; received Content-Type {content_type!r}")
    charset = "utf-8"
    for part in parts[1:]:
        match = re.fullmatch(r"charset\s*=\s*[\"']?([^\"';\s]+)[\"']?", part, re.IGNORECASE)
        if match:
            charset = match.group(1).casefold()
            break
    try:
        "".encode(charset)
    except LookupError as exc:
        raise WebSnapshotError(f"Web snapshot declares an unsupported charset: {charset}") from exc
    return content_type.strip(), media_type, charset


def _decode_html(raw: bytes, charset: str) -> str:
    if not raw:
        raise WebSnapshotError("Web snapshot response body is empty")
    try:
        decoded = raw.decode(charset, errors="strict")
    except UnicodeDecodeError as exc:
        raise WebSnapshotError(f"Web snapshot body does not match declared charset {charset}: {exc}") from exc
    if "\x00" in decoded:
        raise WebSnapshotError("Web snapshot body contains a NUL character")
    return decoded.replace("\r\n", "\n").replace("\r", "\n")


class _HtmlBodyExtractor(HTMLParser):
    def __init__(self, source_lines: list[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.source_lines = source_lines
        self.stack: list[dict[str, Any]] = []
        self.fragments: list[dict[str, Any]] = []
        self.excluded_regions: list[dict[str, Any]] = []
        self.body_depth = 0
        self.body_start_line: int | None = None
        self.body_end_line: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.casefold()
        line = self.getpos()[0]
        attributes = {key.casefold(): (value or "") for key, value in attrs}
        role = attributes.get("role", "").casefold()
        reason = None
        if name in _EXCLUDED_TAGS:
            reason = "navigation-container" if name in {"aside", "footer", "header", "nav"} else "non-content-tag"
        elif role in _NAVIGATION_ROLES:
            reason = "navigation-role"
        self.stack.append({"tag": name, "start_line": line, "excluded_reason": reason})
        if name == "body":
            self.body_depth += 1
            if self.body_start_line is None:
                self.body_start_line = line

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        name = tag.casefold()
        line = self.getpos()[0]
        index = next((index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index]["tag"] == name), None)
        if index is None:
            return
        closed = self.stack[index:]
        del self.stack[index:]
        for entry in closed:
            if entry["excluded_reason"]:
                self.excluded_regions.append(
                    {
                        "tag": entry["tag"],
                        "reason": entry["excluded_reason"],
                        "source_range": {"start_line": entry["start_line"], "end_line": line},
                    }
                )
        if name == "body" and self.body_depth:
            self.body_depth -= 1
            self.body_end_line = line

    def handle_data(self, data: str) -> None:
        if self.body_depth < 1 or any(entry["excluded_reason"] for entry in self.stack):
            return
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        start_line = self.getpos()[0]
        end_line = start_line + data.count("\n")
        tag = next((entry["tag"] for entry in reversed(self.stack) if entry["tag"] in _BLOCK_TAGS), "body")
        source_text = "\n".join(self.source_lines[start_line - 1 : end_line]).strip()
        self.fragments.append(
            {
                "fragment_id": f"web-fragment-{len(self.fragments) + 1:04d}",
                "structure": tag,
                "text": text,
                "source_range": {"start_line": start_line, "end_line": end_line},
                "source_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                "boundary_basis": "html-parser-data-node",
            }
        )


def extract_web_snapshot(decoded_text: str) -> dict[str, Any]:
    """Extract body text while keeping auditable HTML line boundaries and exclusions."""

    source_lines = decoded_text.split("\n")
    parser = _HtmlBodyExtractor(source_lines)
    try:
        parser.feed(decoded_text)
        parser.close()
    except Exception as exc:
        raise WebSnapshotError(f"Web snapshot HTML parsing failed: {exc}") from exc
    if parser.body_start_line is None or parser.body_end_line is None:
        raise WebSnapshotError("Web snapshot HTML must contain a closed body element")
    if not parser.fragments:
        raise WebSnapshotError("Web snapshot body contains no reviewable text after noise exclusion")
    body_text = "\n".join(fragment["text"] for fragment in parser.fragments).rstrip() + "\n"
    return {
        "schema_version": 1,
        "status": "ready",
        "extractor": "stdlib-html-parser-v1",
        "body_boundary": {"start_line": parser.body_start_line, "end_line": parser.body_end_line},
        "body_snapshot_text": body_text,
        "body_snapshot_sha256": hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
        "body_snapshot_size": len(body_text.encode("utf-8")),
        "fragments": parser.fragments,
        "excluded_regions": sorted(
            parser.excluded_regions,
            key=lambda item: (item["source_range"]["start_line"], item["source_range"]["end_line"], item["tag"]),
        ),
    }


def _prepare_web_snapshot(
    raw: bytes,
    *,
    acquisition_mode: str,
    requested_url: str,
    final_url: str,
    requested_at_utc: str | None,
    retrieved_at_utc: str,
    status_code: int,
    content_type: str,
    response_headers: Any,
    omitted_response_headers: list[str] | None = None,
    redirects: list[dict[str, Any]] | None = None,
    max_response_bytes: int,
) -> PreparedWebSnapshot:
    if max_response_bytes < 1:
        raise WebSnapshotError("Web snapshot max_response_bytes must be positive")
    if len(raw) > max_response_bytes:
        raise WebSnapshotError(f"Web snapshot response exceeds max_response_bytes={max_response_bytes}")
    if not isinstance(status_code, int) or status_code < 200 or status_code > 299:
        raise WebSnapshotError(f"Web snapshot requires a successful final HTTP status; received {status_code}")
    requested_url = _validated_url(requested_url, "requested_url")
    final_url = _validated_url(final_url, "final_url")
    retrieved_at_utc = _validated_timestamp(retrieved_at_utc, "retrieved_at_utc")
    requested_at_utc = _validated_timestamp(requested_at_utc, "requested_at_utc") if requested_at_utc else None
    content_type, media_type, charset = _content_type_details(content_type)
    if isinstance(response_headers, dict) and all(isinstance(value, list) for value in response_headers.values()):
        normalized_headers = {}
        for raw_name, values in response_headers.items():
            name = str(raw_name).strip().casefold()
            normalized_values = [str(value).strip() for value in values]
            if not name or "\r" in name or "\n" in name or any("\r" in value or "\n" in value for value in normalized_values):
                raise WebSnapshotError("response headers must use single-line names and values")
            normalized_headers[name] = normalized_values
        omitted = sorted(set(omitted_response_headers or []))
    else:
        normalized_headers, omitted = _normalized_response_headers(response_headers)
    header_content_types = normalized_headers.get("content-type", [])
    if header_content_types and any(value.strip().casefold() != content_type.casefold() for value in header_content_types):
        raise WebSnapshotError("Web snapshot Content-Type conflicts with response_headers")
    normalized_headers["content-type"] = [content_type]
    decoded = _decode_html(raw, charset)
    extraction = extract_web_snapshot(decoded)
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    provenance = {
        "schema_version": 1,
        "adapter_id": WEB_INPUT_ADAPTER_ID,
        "acquisition_mode": acquisition_mode,
        "network_access": "explicit" if acquisition_mode == "live-url-fetch" else "not-used",
        "requested_url": requested_url,
        "final_url": final_url,
        "requested_at_utc": requested_at_utc,
        "retrieved_at_utc": retrieved_at_utc,
        "status_code": status_code,
        "content_type": content_type,
        "media_type": media_type,
        "charset": charset,
        "response_headers": {name: normalized_headers[name] for name in sorted(normalized_headers)},
        "omitted_response_headers": omitted,
        "response_size": len(raw),
        "raw_snapshot_sha256": raw_sha256,
        "body_snapshot_sha256": extraction["body_snapshot_sha256"],
        "redirect_chain": redirects or [],
        "max_response_bytes": max_response_bytes,
    }
    return PreparedWebSnapshot(raw_bytes=raw, decoded_text=decoded, provenance=provenance, extraction=extraction)


def prepare_static_web_snapshot(
    snapshot: Path,
    *,
    requested_url: str,
    final_url: str,
    retrieved_at_utc: str,
    status_code: int,
    content_type: str,
    response_headers: dict[str, str | list[str]] | None = None,
    max_response_bytes: int = DEFAULT_WEB_MAX_RESPONSE_BYTES,
) -> PreparedWebSnapshot:
    """Prepare a caller-provided response body without opening any network connection."""

    snapshot = snapshot.resolve()
    if not snapshot.is_file():
        raise WebSnapshotError(f"Web snapshot file does not exist: {snapshot}")
    with snapshot.open("rb") as handle:
        raw = handle.read(max_response_bytes + 1)
    normalized_headers: dict[str, list[str]] = {}
    omitted: list[str] = []
    for raw_name, raw_values in (response_headers or {}).items():
        name = str(raw_name).strip().casefold()
        if not name or "\r" in name or "\n" in name:
            raise WebSnapshotError("response headers must use single-line names and values")
        if name in WEB_RESPONSE_HEADER_OMIT:
            omitted.append(name)
            continue
        values = raw_values if isinstance(raw_values, list) else [raw_values]
        normalized_values = [str(value).strip() for value in values]
        if any("\r" in value or "\n" in value for value in normalized_values):
            raise WebSnapshotError("response headers must use single-line names and values")
        normalized_headers[name] = normalized_values
    return _prepare_web_snapshot(
        raw,
        acquisition_mode="provided-static-snapshot",
        requested_url=requested_url,
        final_url=final_url,
        requested_at_utc=None,
        retrieved_at_utc=retrieved_at_utc,
        status_code=status_code,
        content_type=content_type,
        response_headers=normalized_headers,
        omitted_response_headers=omitted,
        redirects=[],
        max_response_bytes=max_response_bytes,
    )


class _RecordingRedirectHandler(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redirects: list[dict[str, Any]] = []

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        resolved = urljoin(req.full_url, newurl)
        self.redirects.append(
            {"status_code": int(code), "from_url": req.full_url, "to_url": resolved, "location": str(headers.get("Location") or newurl)}
        )
        return super().redirect_request(req, fp, code, msg, headers, resolved)


def fetch_web_snapshot(
    url: str,
    *,
    timeout_seconds: int = DEFAULT_WEB_TIMEOUT_SECONDS,
    max_response_bytes: int = DEFAULT_WEB_MAX_RESPONSE_BYTES,
    accept_language: str | None = None,
    user_agent: str = "Code-Knowledge-Builder/web-snapshot-v1",
) -> PreparedWebSnapshot:
    """Explicitly fetch one URL; callers must choose this function rather than local ingest."""

    url = _validated_url(url, "url")
    if timeout_seconds < 1:
        raise WebSnapshotError("Web snapshot timeout_seconds must be positive")
    if max_response_bytes < 1:
        raise WebSnapshotError("Web snapshot max_response_bytes must be positive")
    request_headers = {
        "Accept": "text/html, application/xhtml+xml",
        "Accept-Encoding": "identity",
        "User-Agent": user_agent.strip() or "Code-Knowledge-Builder/web-snapshot-v1",
    }
    if accept_language and accept_language.strip():
        request_headers["Accept-Language"] = accept_language.strip()
    requested_at = utc_now()
    redirect_handler = _RecordingRedirectHandler()
    opener = build_opener(redirect_handler)
    try:
        with opener.open(Request(url, headers=request_headers, method="GET"), timeout=timeout_seconds) as response:
            status_code = int(response.getcode())
            final_url = str(response.geturl())
            content_type = str(response.headers.get("Content-Type") or "")
            headers, omitted = _normalized_response_headers(response.headers)
            raw = response.read(max_response_bytes + 1)
    except HTTPError as exc:
        raise WebSnapshotError(f"Web snapshot fetch returned HTTP status {exc.code} for {url}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise WebSnapshotError(f"Web snapshot fetch timed out after {timeout_seconds} seconds for {url}") from exc
    except URLError as exc:
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise WebSnapshotError(f"Web snapshot fetch timed out after {timeout_seconds} seconds for {url}") from exc
        raise WebSnapshotError(f"Web snapshot network request failed for {url}: {reason}") from exc
    return _prepare_web_snapshot(
        raw,
        acquisition_mode="live-url-fetch",
        requested_url=url,
        final_url=final_url,
        requested_at_utc=requested_at,
        retrieved_at_utc=utc_now(),
        status_code=status_code,
        content_type=content_type,
        response_headers=headers,
        omitted_response_headers=omitted,
        redirects=redirect_handler.redirects,
        max_response_bytes=max_response_bytes,
    )


def archive_web_extraction(
    prepared: PreparedWebSnapshot,
    reference_id: str,
    source_file: Path,
    extraction_root: Path,
) -> dict[str, Any]:
    """Write the extracted body and its manifest after a capture is fully validated."""

    extraction_root.mkdir(parents=True, exist_ok=True)
    body_path = extraction_root / "body.txt"
    body_path.write_text(prepared.extraction["body_snapshot_text"], encoding="utf-8", newline="\n")
    manifest_path = extraction_root / "manifest.json"
    manifest = {key: value for key, value in prepared.extraction.items() if key != "body_snapshot_text"}
    manifest.update(
        {
            "reference_id": reference_id,
            "source_file": str(source_file.resolve()),
            "source_sha256": prepared.provenance["raw_snapshot_sha256"],
            "body_snapshot_file": str(body_path.resolve()),
        }
    )
    json_write(manifest_path, manifest)
    return {
        "status": "ready",
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": sha256_file(manifest_path),
        "body_snapshot": str(body_path.resolve()),
        "body_snapshot_sha256": manifest["body_snapshot_sha256"],
        "fragment_count": len(manifest["fragments"]),
    }


def validate_web_extraction(output: Path, manifest: dict[str, Any], *, require_ready: bool = False) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Reopen a Web extraction and verify every path, hash, range, and body fragment."""

    errors: list[dict[str, Any]] = []
    reference_id = str(manifest.get("reference_id") or "")
    extraction_path = Path(str(manifest.get("extraction_file") or ""))
    expected_root = (output.resolve() / "references" / "extractions" / reference_id).resolve()
    expected_manifest = expected_root / "manifest.json"
    if extraction_path.resolve() != expected_manifest or not path_inside(extraction_path.resolve(), expected_root):
        return None, [{"reason": "reference-web-extraction-path", "reference_id": reference_id}]
    if not extraction_path.is_file():
        return None, [{"reason": "reference-web-extraction-missing", "reference_id": reference_id}]
    if sha256_file(extraction_path) != manifest.get("extraction_sha256"):
        errors.append({"reason": "reference-web-extraction-drift", "reference_id": reference_id})
    try:
        extraction = json_load(extraction_path)
    except Exception as exc:
        return None, [*errors, {"reason": "reference-web-extraction-invalid", "reference_id": reference_id, "detail": str(exc)}]
    body_path = Path(str(extraction.get("body_snapshot_file") or ""))
    if body_path.resolve() != expected_root / "body.txt" or not body_path.is_file():
        errors.append({"reason": "reference-web-body-path", "reference_id": reference_id})
    elif sha256_file(body_path) != extraction.get("body_snapshot_sha256") or extraction.get("body_snapshot_sha256") != manifest.get("body_snapshot_sha256"):
        errors.append({"reason": "reference-web-body-drift", "reference_id": reference_id})
    source_path = Path(str(manifest.get("source_file") or ""))
    if source_path.is_file():
        try:
            charset = str((manifest.get("web_capture") or {}).get("charset") or "utf-8")
            source_lines = _decode_html(source_path.read_bytes(), charset).split("\n")
            fragments = extraction.get("fragments")
            if not isinstance(fragments, list) or not fragments:
                errors.append({"reason": "reference-web-fragments-empty", "reference_id": reference_id})
            else:
                seen: set[str] = set()
                rebuilt: list[str] = []
                for fragment in fragments:
                    fragment_id = str(fragment.get("fragment_id") or "")
                    value = fragment.get("source_range") or {}
                    start, end = value.get("start_line"), value.get("end_line")
                    if fragment_id in seen or not fragment_id:
                        errors.append({"reason": "reference-web-fragment-id", "reference_id": reference_id})
                        continue
                    seen.add(fragment_id)
                    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(source_lines):
                        errors.append({"reason": "reference-web-fragment-range", "reference_id": reference_id, "fragment_id": fragment_id})
                        continue
                    source_text = "\n".join(source_lines[start - 1 : end]).strip()
                    if hashlib.sha256(source_text.encode("utf-8")).hexdigest() != fragment.get("source_text_sha256"):
                        errors.append({"reason": "reference-web-fragment-source-drift", "reference_id": reference_id, "fragment_id": fragment_id})
                    text = str(fragment.get("text") or "").strip()
                    if not text:
                        errors.append({"reason": "reference-web-fragment-empty", "reference_id": reference_id, "fragment_id": fragment_id})
                    else:
                        rebuilt.append(text)
                rebuilt_text = "\n".join(rebuilt).rstrip() + "\n"
                if hashlib.sha256(rebuilt_text.encode("utf-8")).hexdigest() != extraction.get("body_snapshot_sha256"):
                    errors.append({"reason": "reference-web-body-rebuild", "reference_id": reference_id})
        except CkbError as exc:
            errors.append({"reason": "reference-web-source-decode", "reference_id": reference_id, "detail": str(exc)})
    if require_ready and extraction.get("status") != "ready":
        errors.append({"reason": "reference-web-extraction-not-ready", "reference_id": reference_id})
    return (extraction if not errors else None), errors


def web_input_adapter_contract() -> dict[str, Any]:
    """Return the explicit local-snapshot/live-fetch boundary and preserved evidence contract."""

    return {
        "schema_version": 2,
        "adapter_id": WEB_INPUT_ADAPTER_ID,
        "implementation_status": "implemented",
        "input_modes": {
            "provided-static-snapshot": {
                "network_access": "not-used",
                "required": ["snapshot", "requested_url", "final_url", "retrieved_at_utc", "status_code", "content_type"],
            },
            "live-url-fetch": {
                "network_access": "explicit-only",
                "required": ["url", "timeout_seconds", "max_response_bytes"],
            },
        },
        "output": {
            "local_file": "immutable-raw-response-body",
            "media_type": sorted(WEB_MEDIA_TYPES),
            "provenance": [
                "acquisition_mode", "requested_url", "final_url", "requested_at_utc", "retrieved_at_utc",
                "status_code", "content_type", "response_headers", "response_size", "raw_snapshot_sha256",
                "body_snapshot_sha256", "redirect_chain",
            ],
            "extraction": ["body_boundary", "excluded_regions", "fragments", "source_range"],
        },
        "boundary": [
            "local-reference-ingest-never-fetches",
            "live-fetch-requires-explicit-command",
            "network-failure-commits-no-reference-artifact",
            "output-still-requires-reference-ingest-and-agent-review",
            "web-content-never-becomes-a-code-entity",
        ],
    }
