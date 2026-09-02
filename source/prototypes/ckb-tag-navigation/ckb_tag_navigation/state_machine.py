from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any

from .contracts import HEX40, TagNavigationError, parse_timestamp, validate_policy
from .store import connect, load_assertions


STATE_ORDER = {"candidate": 0, "confirmed": 1, "contested": 2, "deprecated": 3}


def _group_key(assertion: dict[str, Any]) -> tuple[str, str]:
    return assertion["target"]["path"], assertion["tag"]


def _replay(assertions: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], set[str]]:
    by_id: dict[str, dict[str, Any]] = {}
    retracted: set[str] = set()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for assertion in assertions:
        if assertion["action"] == "retract":
            target_id = assertion["retracts"]
            target = by_id.get(target_id)
            if target is None or target["action"] == "retract":
                raise TagNavigationError("INVALID_RETRACTION", f"{assertion['assertion_id']} 指向不存在或非法事件")
            if target_id in retracted:
                raise TagNavigationError("INVALID_RETRACTION", f"{target_id} 已撤销")
            if _group_key(target) != _group_key(assertion) or target["actor"]["key"] != assertion["actor"]["key"]:
                raise TagNavigationError("INVALID_RETRACTION", f"{assertion['assertion_id']} 跨 actor/target/tag")
            retracted.add(target_id)
        by_id[assertion["assertion_id"]] = assertion
        grouped[_group_key(assertion)].append(assertion)
    return grouped, retracted


def _classify(
    events: list[dict[str, Any]],
    retracted: set[str],
    policy: dict[str, Any],
    current_commit: str,
    as_of: datetime,
) -> dict[str, Any]:
    active_proposals = [event for event in events if event["action"] == "propose" and event["assertion_id"] not in retracted]
    latest_votes: dict[str, dict[str, Any]] = {}
    vote_events = [event for event in events if event["action"] == "vote"]
    for event in vote_events:
        if event["assertion_id"] not in retracted:
            latest_votes[event["actor"]["key"]] = event
    active_votes = list(latest_votes.values())
    usable: list[dict[str, Any]] = []
    stale_count = 0
    drift_count = 0
    for vote in active_votes:
        observed = parse_timestamp(vote["evidence"]["observed_at"], "evidence.observed_at")
        age_seconds = (as_of - observed).total_seconds()
        if age_seconds < 0:
            raise TagNavigationError("FUTURE_EVIDENCE", vote["assertion_id"])
        stale = age_seconds > policy["max_evidence_age_days"] * 86400
        drift = vote["evidence"]["commit"] != current_commit
        stale_count += int(stale)
        drift_count += int(drift)
        if not stale and not drift:
            usable.append(vote)
    support = [vote for vote in usable if vote["stance"] == "support"]
    oppose = [vote for vote in usable if vote["stance"] == "oppose"]
    support_agents = {vote["actor"]["key"] for vote in support}
    support_sources = {vote["evidence"]["source_id"] for vote in support}
    denominator = len(support) + len(oppose)
    opposition_ratio = len(oppose) / denominator if denominator else 0.0
    reasons: list[str] = []
    if not active_votes:
        if active_proposals:
            state = "candidate"
            reasons.append("PROPOSAL_ONLY")
        else:
            state = "deprecated"
            if vote_events and all(event["assertion_id"] in retracted for event in vote_events):
                reasons.append("ALL_SUPPORT_RETRACTED")
            reasons.append("NO_ACTIVE_SUPPORT")
    elif not support:
        state = "deprecated"
        reasons.append("NO_ACTIVE_SUPPORT")
        if stale_count:
            reasons.append("STALE_EVIDENCE")
        if drift_count:
            reasons.append("COMMIT_DRIFT")
    elif opposition_ratio > policy["max_opposition_ratio"]:
        state = "contested"
        reasons.append("OPPOSITION_RATIO_EXCEEDED")
        if stale_count:
            reasons.append("STALE_EVIDENCE")
        if drift_count:
            reasons.append("COMMIT_DRIFT")
    else:
        if len(support) < policy["min_support_votes"]:
            reasons.append("SUPPORT_VOTES_BELOW_MINIMUM")
        if len(support_agents) < policy["min_independent_agents"]:
            reasons.append("INDEPENDENT_AGENTS_BELOW_MINIMUM")
        if len(support_sources) < policy["min_independent_sources"]:
            reasons.append("INDEPENDENT_SOURCES_BELOW_MINIMUM")
        if stale_count:
            reasons.append("STALE_EVIDENCE")
        if drift_count:
            reasons.append("COMMIT_DRIFT")
        if reasons:
            state = "candidate"
        else:
            state = "confirmed"
            reasons.append("CONFIRMED_THRESHOLDS_MET")
    return {
        "state": state,
        "reason_codes": sorted(set(reasons)),
        "metrics": {
            "proposal_count": len(active_proposals),
            "active_vote_count": len(active_votes),
            "support_votes": len(support),
            "oppose_votes": len(oppose),
            "independent_support_agents": len(support_agents),
            "independent_support_sources": len(support_sources),
            "opposition_ratio": round(opposition_ratio, 6),
            "stale_active_votes": stale_count,
            "drifted_active_votes": drift_count,
            "retracted_vote_count": sum(1 for event in vote_events if event["assertion_id"] in retracted),
            "superseded_vote_count": max(0, len([event for event in vote_events if event["assertion_id"] not in retracted]) - len(active_votes)),
        },
    }


def audit_assertions(
    assertions: list[dict[str, Any]],
    policy: dict[str, Any],
    current_commit: str,
    as_of_value: str,
) -> dict[str, Any]:
    validate_policy(policy)
    if not isinstance(current_commit, str) or not HEX40.fullmatch(current_commit):
        raise TagNavigationError("INVALID_COMMIT", "current_commit 必须为 40 位小写十六进制")
    as_of = parse_timestamp(as_of_value, "as_of")
    grouped, retracted = _replay(assertions)
    results: list[dict[str, Any]] = []
    for (target, tag), events in sorted(grouped.items()):
        classified = _classify(events, retracted, policy, current_commit, as_of)
        results.append({"target": {"kind": "page", "path": target}, "tag": tag, **classified})
    counts = Counter(result["state"] for result in results)
    return {
        "schema_version": 1,
        "status": "passed",
        "current_commit": current_commit,
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "policy": dict(policy),
        "summary": {state: counts.get(state, 0) for state in ("candidate", "confirmed", "contested", "deprecated")},
        "results": results,
    }


def audit_database(database: Path, policy: dict[str, Any], current_commit: str, as_of_value: str) -> dict[str, Any]:
    try:
        connection = connect(database)
        try:
            assertions = load_assertions(connection)
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise TagNavigationError("INVALID_DATABASE", str(exc)) from exc
    return audit_assertions(assertions, policy, current_commit, as_of_value)
