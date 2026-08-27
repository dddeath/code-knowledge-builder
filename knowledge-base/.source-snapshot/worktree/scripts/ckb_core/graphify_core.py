"""Graphify-compatible graph, community, report, and scoped-query projection.

The source-audited CKB graph remains the sole fact authority. This module adopts
Graphify's staged graph model and invokes its pinned deterministic community
detector after every successful Agent-reviewed merge. It deliberately does not
replace Git blob/range provenance or the CKB completion gates with fuzzy labels.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable

from .common import CkbError, json_load, json_write, sha256_file, utc_now


GRAPHIFY_UPSTREAM = "https://github.com/Graphify-Labs/graphify"
GRAPHIFY_COMMIT = "b2cd36267456c166788c95be6e68574064a92a42"
GRAPHIFY_VERSION = "0.9.48"
GRAPHIFY_PIPELINE = ["detect", "extract", "build", "cluster", "report", "export"]
GRAPHIFY_CONFIDENCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}
GRAPHIFY_PROJECTION_SCHEMA = 1
REPORT_COMMUNITY_LIMIT = 30
REPORT_MEMBER_LIMIT = 12
QUERY_DEFAULT_BUDGET = 1500
HUMAN_REPORT_KINDS = {"class", "struct", "interface", "record", "function", "method", "constructor", "destructor"}


def _networkx_modules():
    vendor = Path(__file__).resolve().parents[1] / "_vendor"
    if str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))
    import networkx as nx  # type: ignore
    from _vendor.graphify_vendor.cluster import (  # type: ignore
        cluster,
        label_communities_by_hub,
        score_all,
    )

    return nx, cluster, label_communities_by_hub, score_all


def _canonical_json_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _source_location(entity: dict[str, Any]) -> str:
    source_range = entity.get("range", {})
    start = int(source_range.get("start_line", 0) or 0)
    end = int(source_range.get("end_line", start) or start)
    return f"L{start}" if start == end else f"L{start}-L{end}"


def _node_label(entity: dict[str, Any]) -> str:
    if entity.get("kind") == "file":
        return str(entity.get("path", entity["id"]))
    return str(entity.get("qualified_name") or entity.get("name") or entity["id"])


def _description(entity: dict[str, Any]) -> str:
    return str(
        entity.get("meaning_zh")
        or entity.get("description_zh")
        or entity.get("role_zh")
        or ""
    )


def _confidence(link: dict[str, Any]) -> tuple[str, float, str]:
    """Map CKB provider evidence into Graphify's three deterministic tiers."""
    provider = str(link.get("provider", ""))
    relation = str(link.get("type", "references"))
    lowered = provider.lower()
    if "lexical-candidate" in lowered:
        return "INFERRED", 0.85, "deterministic lexical target resolution"
    if "ambiguous" in lowered or relation in {"possible-reference", "possible-call"}:
        return "AMBIGUOUS", 0.55, "provider marked the target ambiguous"
    return "EXTRACTED", 1.0, "AST/LSP or source-structural evidence"


def _graphify_node(entity: dict[str, Any]) -> dict[str, Any]:
    source_range = entity.get("range", {})
    return {
        "id": entity["id"],
        "label": _node_label(entity),
        "file_type": "code",
        "node_type": entity.get("kind"),
        "language": entity.get("language"),
        "source_file": entity.get("path"),
        "source_location": _source_location(entity),
        "source_range": {
            "start_byte": source_range.get("start_byte"),
            "end_byte": source_range.get("end_byte"),
            "start_line": source_range.get("start_line"),
            "end_line": source_range.get("end_line"),
        },
        "qualified_name": entity.get("qualified_name"),
        "classification": entity.get("classification"),
        "owner_page_id": entity.get("owner_page_id"),
        "description_zh": _description(entity),
        "meaning_zh": entity.get("meaning_zh"),
        "role_zh": entity.get("role_zh"),
        "change_when_zh": entity.get("change_when_zh"),
        "review_status": entity.get("review_status"),
        "commit": entity.get("commit"),
        "blob": entity.get("blob"),
        "chunk_id": entity.get("chunk_id"),
        "scope_classification": entity.get("classification"),
    }


def _graphify_link(link: dict[str, Any], entity_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    confidence, score, reason = _confidence(link)
    source_entity = entity_by_id[link["source"]]
    return {
        "id": link["id"],
        "source": link["source"],
        "target": link["target"],
        "relation": link.get("type", "references"),
        "confidence": confidence,
        "confidence_score": score,
        "confidence_reason": reason,
        "source_file": link.get("evidence", {}).get("source_path") or source_entity.get("path"),
        "provider": link.get("provider"),
        "evidence": link.get("evidence", {}),
        "cross_chunk": bool(link.get("cross_chunk")),
    }


def _build_networkx(nodes: list[dict[str, Any]], links: list[dict[str, Any]]):
    nx, _cluster, _labels, _scores = _networkx_modules()
    graph = nx.MultiDiGraph()
    for node in nodes:
        attrs = {key: value for key, value in node.items() if key != "id"}
        graph.add_node(node["id"], **attrs)
    for link in links:
        attrs = {key: value for key, value in link.items() if key not in {"source", "target"}}
        graph.add_edge(link["source"], link["target"], key=link["id"], **attrs)
    return graph


def _community_records(graph, communities: dict[int, list[str]], labels: dict[int, str], scores: dict[int, float]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for community_id in sorted(communities):
        members = sorted(communities[community_id])
        hubs = sorted(members, key=lambda value: (-graph.degree(value), value))[:REPORT_MEMBER_LIMIT]
        records.append(
            {
                "id": community_id,
                "label": labels[community_id],
                "members": members,
                "member_count": len(members),
                "cohesion": scores[community_id],
                "hub_ids": hubs,
                "membership_sha256": _canonical_json_sha256(members),
            }
        )
    return records


def _report(
    canonical: dict[str, Any],
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    communities: list[dict[str, Any]],
    graph,
) -> str:
    by_id = {node["id"]: node for node in nodes}
    readable_nodes = [
        node
        for node in nodes
        if node.get("node_type") in HUMAN_REPORT_KINDS and str(node.get("description_zh") or "").strip()
    ]
    hub_candidates = sorted(
        readable_nodes,
        key=lambda node: (0 if node.get("classification") == "page" else 1, -graph.degree(node["id"]), node["label"], node["id"]),
    )
    hubs: list[dict[str, Any]] = []
    hub_labels: set[str] = set()
    for node in hub_candidates:
        if node["label"] in hub_labels:
            continue
        hub_labels.add(node["label"])
        hubs.append(node)
        if len(hubs) == 12:
            break
    lines = [
        "# 项目关系导览",
        "",
        "> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。",
        "",
        "## 建议先看的代码",
        "",
    ]
    for node in hubs:
        description = str(node.get("description_zh") or "").strip()
        lines.append(f"- **{node['label']}**：{description}")
    if not hubs:
        lines.append("- 从项目代码导览开始，沿自然双链进入相关职责。")
    lines.extend(["", "## 按职责群浏览", ""])
    for community in communities[:REPORT_COMMUNITY_LIMIT]:
        member_candidates = sorted(
            [value for value in community["members"] if by_id[value].get("node_type") in HUMAN_REPORT_KINDS],
            key=lambda value: (
                0 if by_id[value].get("classification") == "page" else 1,
                0 if str(by_id[value].get("description_zh") or "").strip() else 1,
                -graph.degree(value),
                by_id[value]["label"],
                value,
            ),
        )
        member_ids: list[str] = []
        member_labels: set[str] = set()
        for value in member_candidates:
            if by_id[value]["label"] in member_labels:
                continue
            member_labels.add(by_id[value]["label"])
            member_ids.append(value)
            if len(member_ids) == 8:
                break
        heading = by_id[member_ids[0]]["label"] if member_ids else community["label"]
        lines.append(f"### {heading} 相关职责")
        lines.append("")
        for node_id in member_ids:
            node = by_id[node_id]
            description = str(node.get("description_zh") or "").strip()
            lines.append(f"- **{node['label']}**" + (f"：{description}" if description else ""))
        lines.append("")
    if len(communities) > REPORT_COMMUNITY_LIMIT:
        lines.append("> 为保持阅读节奏，这里只展开最主要的职责群；图查询仍会使用完整关系。")
        lines.append("")
    lines.extend(
        [
            "## 围绕任务继续缩小范围",
            "",
            "```powershell",
            '& PYTHON scripts\\ckb.py query --out OUTPUT "职责关键词" --budget 1500',
            '& PYTHON scripts\\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"',
            '& PYTHON scripts\\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"',
            "```",
            "",
            "查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。",
            "",
        ]
    )
    return "\n".join(lines)


def project_graphify(output: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    """Build the Graphify-compatible projection from the reviewed canonical graph."""
    root = output / "graphify-out"
    root.mkdir(parents=True, exist_ok=True)
    entity_by_id = {entity["id"]: entity for entity in canonical["entities"]}
    nodes = [_graphify_node(entity) for entity in canonical["entities"]]
    links = [_graphify_link(link, entity_by_id) for link in canonical["links"]]
    nodes.sort(key=lambda item: item["id"])
    links.sort(key=lambda item: item["id"])

    graph = _build_networkx(nodes, links)
    _nx, cluster, label_communities_by_hub, score_all = _networkx_modules()
    grouped = cluster(graph)
    labels = label_communities_by_hub(graph, grouped)
    scores = score_all(graph.to_undirected(), grouped)
    communities = _community_records(graph, grouped, labels, scores)
    community_by_node = {
        node_id: community["id"]
        for community in communities
        for node_id in community["members"]
    }
    for node in nodes:
        node["community"] = community_by_node[node["id"]]
        node["community_name"] = labels[community_by_node[node["id"]]]
        node["norm_label"] = node["label"].casefold()

    graph_doc = {
        "directed": True,
        "multigraph": True,
        "graph": {
            "schema": "graphify-node-link",
            "schema_version": GRAPHIFY_PROJECTION_SCHEMA,
            "generator": "code-knowledge-builder",
            "graphify_upstream": GRAPHIFY_UPSTREAM,
            "graphify_commit": GRAPHIFY_COMMIT,
            "graphify_version": GRAPHIFY_VERSION,
            "pipeline": GRAPHIFY_PIPELINE,
            "source_graph": str((output / "graph.json").resolve()),
            "scope": canonical["scope"].get("mode"),
        },
        "nodes": nodes,
        "links": links,
        "hyperedges": [],
        "built_at_commit": canonical["repository"]["commit"],
    }
    graph_path = root / "graph.json"
    communities_path = root / "communities.json"
    report_path = root / "GRAPH_REPORT.md"
    json_write(graph_path, graph_doc)
    json_write(
        communities_path,
        {
            "schema_version": GRAPHIFY_PROJECTION_SCHEMA,
            "graphify_commit": GRAPHIFY_COMMIT,
            "communities": communities,
        },
    )
    report_path.write_text(
        _report(canonical, nodes, links, communities, graph),
        encoding="utf-8",
        newline="\n",
    )
    record = {
        "schema_version": GRAPHIFY_PROJECTION_SCHEMA,
        "status": "projected",
        "root": str(root.resolve()),
        "graph": str(graph_path.resolve()),
        "graph_sha256": sha256_file(graph_path),
        "communities": str(communities_path.resolve()),
        "communities_sha256": sha256_file(communities_path),
        "report": str(report_path.resolve()),
        "report_sha256": sha256_file(report_path),
        "node_count": len(nodes),
        "link_count": len(links),
        "community_count": len(communities),
        "confidence_counts": dict(sorted(Counter(link["confidence"] for link in links).items())),
        "graphify_upstream": GRAPHIFY_UPSTREAM,
        "graphify_commit": GRAPHIFY_COMMIT,
        "graphify_version": GRAPHIFY_VERSION,
        "networkx_version": _nx.__version__,
        "generated_at_utc": utc_now(),
    }
    json_write(root / "projection.json", record)
    return record


def audit_graphify(output: Path, canonical: dict[str, Any], record: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate full-set parity, source provenance, confidence, and communities."""
    errors: list[dict[str, Any]] = []
    root = output / "graphify-out"
    paths = {
        "graph": root / "graph.json",
        "communities": root / "communities.json",
        "report": root / "GRAPH_REPORT.md",
        "projection": root / "projection.json",
    }
    for name, path in paths.items():
        if not path.is_file():
            errors.append({"reason": f"graphify-{name}-missing", "path": str(path)})
    if errors:
        return errors

    projected = json_load(paths["graph"])
    community_doc = json_load(paths["communities"])
    projection_doc = json_load(paths["projection"])
    if projection_doc != record:
        errors.append({"reason": "graphify-projection-record-mismatch"})
    canonical_entities = {entity["id"]: entity for entity in canonical["entities"]}
    projected_nodes = {node["id"]: node for node in projected.get("nodes", [])}
    if set(projected_nodes) != set(canonical_entities):
        errors.append(
            {
                "reason": "graphify-node-set-mismatch",
                "missing": sorted(set(canonical_entities) - set(projected_nodes)),
                "extra": sorted(set(projected_nodes) - set(canonical_entities)),
            }
        )
    for entity_id in sorted(set(canonical_entities) & set(projected_nodes)):
        entity = canonical_entities[entity_id]
        node = projected_nodes[entity_id]
        source_range = entity.get("range", {})
        expected = {
            "source_file": entity.get("path"),
            "source_location": _source_location(entity),
            "commit": entity.get("commit"),
            "blob": entity.get("blob"),
            "classification": entity.get("classification"),
            "owner_page_id": entity.get("owner_page_id"),
            "source_range": {
                "start_byte": source_range.get("start_byte"),
                "end_byte": source_range.get("end_byte"),
                "start_line": source_range.get("start_line"),
                "end_line": source_range.get("end_line"),
            },
        }
        if any(node.get(key) != value for key, value in expected.items()):
            errors.append({"reason": "graphify-node-provenance-mismatch", "id": entity_id})

    canonical_links = {link["id"]: link for link in canonical["links"]}
    projected_links = {link["id"]: link for link in projected.get("links", [])}
    if set(projected_links) != set(canonical_links):
        errors.append(
            {
                "reason": "graphify-link-set-mismatch",
                "missing": sorted(set(canonical_links) - set(projected_links)),
                "extra": sorted(set(projected_links) - set(canonical_links)),
            }
        )
    for link_id in sorted(set(canonical_links) & set(projected_links)):
        source = canonical_links[link_id]
        link = projected_links[link_id]
        if link.get("source") != source["source"] or link.get("target") != source["target"] or link.get("relation") != source.get("type"):
            errors.append({"reason": "graphify-link-fact-mismatch", "id": link_id})
        if link.get("confidence") not in GRAPHIFY_CONFIDENCE:
            errors.append({"reason": "graphify-confidence-invalid", "id": link_id})
        if not link.get("provider") or not link.get("source_file"):
            errors.append({"reason": "graphify-link-evidence-missing", "id": link_id})
        if link.get("source") not in projected_nodes or link.get("target") not in projected_nodes:
            errors.append({"reason": "graphify-link-dangling", "id": link_id})

    memberships = [
        node_id
        for community in community_doc.get("communities", [])
        for node_id in community.get("members", [])
    ]
    if len(memberships) != len(set(memberships)) or set(memberships) != set(projected_nodes):
        errors.append({"reason": "graphify-community-cover-mismatch"})
    for community in community_doc.get("communities", []):
        if community.get("membership_sha256") != _canonical_json_sha256(sorted(community.get("members", []))):
            errors.append({"reason": "graphify-community-signature-mismatch", "id": community.get("id")})
    if record.get("community_count") != len(community_doc.get("communities", [])):
        errors.append({"reason": "graphify-community-count-contract-mismatch"})

    if projected.get("built_at_commit") != canonical["repository"]["commit"]:
        errors.append({"reason": "graphify-commit-mismatch"})
    graph_meta = projected.get("graph", {})
    if graph_meta.get("graphify_commit") != GRAPHIFY_COMMIT or graph_meta.get("pipeline") != GRAPHIFY_PIPELINE:
        errors.append({"reason": "graphify-upstream-provenance-mismatch"})
    if record.get("graphify_commit") != GRAPHIFY_COMMIT or record.get("graphify_version") != GRAPHIFY_VERSION:
        errors.append({"reason": "graphify-projection-upstream-mismatch"})
    hash_expectations = {
        "graph_sha256": paths["graph"],
        "communities_sha256": paths["communities"],
        "report_sha256": paths["report"],
    }
    for field, path in hash_expectations.items():
        if record.get(field) != sha256_file(path):
            errors.append({"reason": f"graphify-{field}-mismatch"})
    if record.get("node_count") != len(projected_nodes) or record.get("link_count") != len(projected_links):
        errors.append({"reason": "graphify-count-contract-mismatch"})
    report = paths["report"].read_text(encoding="utf-8")
    if GRAPHIFY_COMMIT in report or canonical["repository"]["commit"] in report:
        errors.append({"reason": "graphify-report-exposes-machine-commit"})
    required_headings = ("# 项目关系导览", "## 建议先看的代码", "## 按职责群浏览", "## 围绕任务继续缩小范围")
    if any(heading not in report for heading in required_headings):
        errors.append({"reason": "graphify-human-report-incomplete"})
    if any(marker in report for marker in ("degree `", "cohesion=", "分类 `", "EXTRACTED：", "INFERRED：", "AMBIGUOUS：")):
        errors.append({"reason": "graphify-report-exposes-machine-properties"})
    return errors


def _load_projected_graph(output: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    path = output / "graphify-out" / "graph.json"
    if not path.is_file():
        raise CkbError(f"finalize must create Graphify projection first: {path}")
    graph = json_load(path)
    nodes = {node["id"]: node for node in graph.get("nodes", [])}
    links = graph.get("links", [])
    if not nodes:
        raise CkbError(f"Graphify projection has no nodes: {path}")
    return graph, nodes, links


def _terms(text: str) -> list[str]:
    terms = {
        token.casefold()
        for token in re.findall(r"[\w.$:/\\-]+", text, flags=re.UNICODE)
        if len(token) >= 2
    }
    # Standard-library deterministic CJK segmentation: retain each complete run
    # and add adjacent bigrams, so "订单库存处理" can match separate "订单" and
    # "库存" evidence without jieba, an LLM, or host-specific tokenization.
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        terms.update(run[index : index + 2] for index in range(max(0, len(run) - 1)))
    return sorted(terms, key=lambda value: (-len(value), value))


def _seed_scores(question: str, nodes: dict[str, dict[str, Any]]) -> list[tuple[int, str]]:
    terms = _terms(question)
    lowered_question = question.casefold()
    scored: list[tuple[int, str]] = []
    for node_id, node in nodes.items():
        label = str(node.get("label", "")).casefold()
        qname = str(node.get("qualified_name", "")).casefold()
        path = str(node.get("source_file", "")).casefold()
        description = str(node.get("description_zh", "")).casefold()
        haystacks = (label, qname, path, description)
        score = 0
        if lowered_question in haystacks or any(value and value in lowered_question for value in (label, qname)):
            score += 100
        for term in terms:
            if term == label or term == qname:
                score += 30
            elif term in label or term in qname:
                score += 12
            elif term in path:
                score += 6
            elif term in description:
                score += 3
        if score:
            scored.append((score, node_id))
    return sorted(scored, key=lambda value: (-value[0], value[1]))


def _adjacency(nodes: dict[str, dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    result: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for link in links:
        if link["source"] in nodes and link["target"] in nodes:
            result[link["source"]].append((link["target"], link))
            result[link["target"]].append((link["source"], link))
    for node_id in result:
        result[node_id].sort(key=lambda row: (row[0], row[1]["id"]))
    return result


def _query_size(nodes: Iterable[dict[str, Any]], links: Iterable[dict[str, Any]]) -> int:
    payload = {"nodes": list(nodes), "links": list(links)}
    return math.ceil(len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) / 3)


def query_graph(output: Path, question: str, budget: int = QUERY_DEFAULT_BUDGET, dfs: bool = False) -> dict[str, Any]:
    if budget <= 0:
        raise CkbError("query budget must be positive")
    _graph, nodes, links = _load_projected_graph(output)
    scored = _seed_scores(question, nodes)
    if not scored:
        raise CkbError(f"no Graphify node matched query: {question}")
    seeds = [node_id for _score, node_id in scored[:5]]
    adjacency = _adjacency(nodes, links)
    primary_seed = next((seed for seed in seeds if adjacency.get(seed)), seeds[0])
    # Traverse from one structurally connected seed. Enqueuing all fuzzy seeds
    # first spends a small budget on disconnected labels before BFS can include
    # the relations that explain why the first match matters.
    frontier: deque[tuple[str, int]] = deque([(primary_seed, 0)])
    selected: list[str] = []
    selected_set: set[str] = set()
    max_depth = 4
    while frontier:
        node_id, depth = frontier.pop() if dfs else frontier.popleft()
        if node_id in selected_set:
            continue
        candidate_ids = selected + [node_id]
        candidate_set = set(candidate_ids)
        candidate_links = [link for link in links if link["source"] in candidate_set and link["target"] in candidate_set]
        if selected and _query_size((nodes[value] for value in candidate_ids), candidate_links) > budget:
            continue
        selected.append(node_id)
        selected_set.add(node_id)
        if depth >= max_depth:
            continue
        neighbors = adjacency.get(node_id, [])
        ordered = reversed(neighbors) if dfs else neighbors
        for neighbor, _link in ordered:
            if neighbor not in selected_set:
                frontier.append((neighbor, depth + 1))
    selected_links = [link for link in links if link["source"] in selected_set and link["target"] in selected_set]
    selected_nodes = [nodes[node_id] for node_id in selected]
    files = sorted({node.get("source_file") for node in selected_nodes if node.get("source_file")})
    result = {
        "schema_version": GRAPHIFY_PROJECTION_SCHEMA,
        "status": "passed",
        "question": question,
        "traversal": "dfs" if dfs else "bfs",
        "budget": budget,
        "estimated_tokens": _query_size(selected_nodes, selected_links),
        "seed_ids": seeds,
        "primary_seed_id": primary_seed,
        "nodes": selected_nodes,
        "links": selected_links,
        "source_files": files,
        "graphify_commit": GRAPHIFY_COMMIT,
    }
    query_dir = output / "graphify-out" / "queries"
    query_dir.mkdir(parents=True, exist_ok=True)
    query_id = hashlib.sha256(f"{question}\0{budget}\0{dfs}".encode("utf-8")).hexdigest()[:16]
    json_write(query_dir / f"query-{query_id}.json", result)
    result["record"] = str((query_dir / f"query-{query_id}.json").resolve())
    return result


def _resolve_node(term: str, nodes: dict[str, dict[str, Any]]) -> str:
    if term in nodes:
        return term
    folded = term.casefold()
    exact = sorted(
        node_id
        for node_id, node in nodes.items()
        if folded in {str(node.get("label", "")).casefold(), str(node.get("qualified_name", "")).casefold()}
    )
    if len(exact) == 1:
        return exact[0]
    exact_pages = [node_id for node_id in exact if nodes[node_id].get("classification") == "page"]
    if len(exact_pages) == 1:
        return exact_pages[0]
    partial = sorted(
        node_id
        for node_id, node in nodes.items()
        if folded in str(node.get("label", "")).casefold()
        or folded in str(node.get("qualified_name", "")).casefold()
        or folded in str(node.get("source_file", "")).casefold()
    )
    candidates = exact or partial
    candidate_pages = [node_id for node_id in candidates if nodes[node_id].get("classification") == "page"]
    if len(candidate_pages) == 1:
        return candidate_pages[0]
    if len(candidates) != 1:
        raise CkbError(f"node selector must match exactly one node: {term}; candidates={candidates[:20]}")
    return candidates[0]


def shortest_path(output: Path, source: str, target: str) -> dict[str, Any]:
    _graph, nodes, links = _load_projected_graph(output)
    source_id = _resolve_node(source, nodes)
    target_id = _resolve_node(target, nodes)
    adjacency = _adjacency(nodes, links)
    queue: deque[str] = deque([source_id])
    previous: dict[str, tuple[str, str] | None] = {source_id: None}
    while queue and target_id not in previous:
        current = queue.popleft()
        for neighbor, link in adjacency.get(current, []):
            if neighbor not in previous:
                previous[neighbor] = (current, link["id"])
                queue.append(neighbor)
    if target_id not in previous:
        raise CkbError(f"no graph path between {source} and {target}")
    node_ids: list[str] = []
    link_ids: list[str] = []
    cursor = target_id
    while True:
        node_ids.append(cursor)
        step = previous[cursor]
        if step is None:
            break
        cursor, link_id = step
        link_ids.append(link_id)
    node_ids.reverse()
    link_ids.reverse()
    link_by_id = {link["id"]: link for link in links}
    return {
        "schema_version": GRAPHIFY_PROJECTION_SCHEMA,
        "status": "passed",
        "source": source_id,
        "target": target_id,
        "node_ids": node_ids,
        "nodes": [nodes[node_id] for node_id in node_ids],
        "links": [link_by_id[link_id] for link_id in link_ids],
        "hop_count": len(link_ids),
        "graphify_commit": GRAPHIFY_COMMIT,
    }


def explain_node(output: Path, selector: str) -> dict[str, Any]:
    _graph, nodes, links = _load_projected_graph(output)
    node_id = _resolve_node(selector, nodes)
    related = [link for link in links if link["source"] == node_id or link["target"] == node_id]
    related.sort(key=lambda item: (item["relation"], item["id"]))
    neighbor_ids = sorted(
        {
            link["target"] if link["source"] == node_id else link["source"]
            for link in related
        }
    )
    return {
        "schema_version": GRAPHIFY_PROJECTION_SCHEMA,
        "status": "passed",
        "node": nodes[node_id],
        "neighbors": [nodes[value] for value in neighbor_ids],
        "links": related,
        "graphify_commit": GRAPHIFY_COMMIT,
    }
