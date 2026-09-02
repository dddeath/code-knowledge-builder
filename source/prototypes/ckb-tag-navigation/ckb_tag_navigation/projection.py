from __future__ import annotations

from collections import defaultdict
from typing import Any

from .contracts import TagNavigationError, validate_policy


def build_projection(audit: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    if not isinstance(audit, dict) or audit.get("schema_version") != 1 or audit.get("status") != "passed":
        raise TagNavigationError("INVALID_AUDIT", "审计对象未通过")
    results = audit.get("results")
    if not isinstance(results, list):
        raise TagNavigationError("INVALID_AUDIT", "results 必须为数组")
    by_page: dict[str, list[dict[str, Any]]] = defaultdict(list)
    excluded_by_state: dict[str, int] = defaultdict(int)
    for result in results:
        if not isinstance(result, dict) or result.get("state") not in {"candidate", "confirmed", "contested", "deprecated"}:
            raise TagNavigationError("INVALID_AUDIT", "结果状态非法")
        if result["state"] == "confirmed":
            by_page[result["target"]["path"]].append(result)
        else:
            excluded_by_state[result["state"]] += 1
    entries: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    limit = policy["max_tags_per_page"]
    for page in sorted(by_page):
        ranked = sorted(
            by_page[page],
            key=lambda result: (
                -result["metrics"]["support_votes"],
                result["metrics"]["opposition_ratio"],
                -result["metrics"]["independent_support_sources"],
                result["tag"],
            ),
        )
        selected = ranked[:limit]
        entries.append(
            {
                "page": page,
                "tags": [
                    {"tag": result["tag"], "display": f"#导航/{result['tag']}", "search": f"tag:#导航/{result['tag']}"}
                    for result in selected
                ],
            }
        )
        for result in ranked[limit:]:
            suppressed.append({"page": page, "tag": result["tag"], "reason_code": "PAGE_TAG_QUOTA_EXCEEDED"})
    return {
        "schema_version": 1,
        "status": "passed",
        "production_integration": "disabled",
        "page_tag_limit": limit,
        "entries": entries,
        "suppressed": suppressed,
        "excluded_by_state": {state: excluded_by_state.get(state, 0) for state in ("candidate", "contested", "deprecated")},
    }
