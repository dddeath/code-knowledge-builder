from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator

from .common import DependencyError, stable_id


DECLARATION_TYPES = {
    "python": {
        "function_definition": "function",
        "class_definition": "class",
    },
    "javascript": {
        "function_declaration": "function",
        "generator_function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "variable_declarator": "variable",
    },
    "c": {
        "function_definition": "function",
        "declaration": "declaration",
        "struct_specifier": "class",
        "enum_specifier": "enum",
        "type_definition": "type",
    },
    "cpp": {
        "function_definition": "function",
        "function_declarator": "function",
        "class_specifier": "class",
        "struct_specifier": "class",
        "enum_specifier": "enum",
        "namespace_definition": "namespace",
        "type_definition": "type",
    },
    "csharp": {
        "namespace_declaration": "namespace",
        "file_scoped_namespace_declaration": "namespace",
        "class_declaration": "class",
        "struct_declaration": "struct",
        "record_declaration": "record",
        "interface_declaration": "interface",
        "delegate_declaration": "delegate",
        "enum_declaration": "enum",
        "enum_member_declaration": "enum_member",
        "method_declaration": "method",
        "local_function_statement": "local_function",
        "constructor_declaration": "constructor",
        "operator_declaration": "operator",
        "conversion_operator_declaration": "conversion_operator",
        "property_declaration": "property",
        "indexer_declaration": "indexer",
        "event_declaration": "event",
        "event_field_declaration": "event",
        "accessor_declaration": "accessor",
        "field_declaration": "field",
    },
}

NAME_FIELDS = ("name", "declarator", "type")


def _language(language: str):
    try:
        from tree_sitter import Language
        modules = {
            "python": "tree_sitter_python",
            "javascript": "tree_sitter_javascript",
            "c": "tree_sitter_c",
            "cpp": "tree_sitter_cpp",
            "csharp": "tree_sitter_c_sharp",
        }
        module = __import__(modules[language])
        return Language(module.language())
    except Exception as exc:
        raise DependencyError(f"Tree-sitter runtime for {language} is unavailable: {exc}") from exc


def _walk(node) -> Iterator[Any]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _byte_position(source: bytes, byte_offset: int) -> tuple[int, int]:
    """Compute 1-based line and UTF-8 byte column without Node Point access."""
    previous_newline = source.rfind(b"\n", 0, byte_offset)
    return source.count(b"\n", 0, byte_offset) + 1, byte_offset - (previous_newline + 1)


def _find_name(node, source: bytes, retained_nodes: list[Any]) -> tuple[str, int, int] | None:
    for field in NAME_FIELDS:
        child = node.child_by_field_name(field)
        if child is not None:
            candidates = [child, *_walk(child)]
            retained_nodes.extend(candidates)
            for value in candidates:
                if value.type in {"identifier", "type_identifier", "field_identifier", "property_identifier", "namespace_identifier"}:
                    line, column = _byte_position(source, value.start_byte)
                    return _node_text(value, source), line, column
    fallback_nodes = list(_walk(node))
    retained_nodes.extend(fallback_nodes)
    for child in fallback_nodes:
        if child.type in {"identifier", "type_identifier", "field_identifier", "property_identifier", "namespace_identifier"}:
            line, column = _byte_position(source, child.start_byte)
            return _node_text(child, source), line, column
    return None


def _public_evidence(language: str, source_text: str, node_text: str, name: str) -> bool:
    if language == "python":
        return not name.startswith("_")
    if language == "javascript":
        return bool(re.search(r"\bexport\b", source_text[max(0, source_text.find(node_text) - 80) : source_text.find(node_text) + 20]))
    return bool(re.search(r"\b(public|protected|internal|extern)\b", node_text)) or language in {"c", "cpp"}


PAGE_ELIGIBLE_KINDS = {
    "class",
    "struct",
    "record",
    "interface",
    "delegate",
    "function",
    "method",
    "local_function",
    "constructor",
    "operator",
    "conversion_operator",
    "property",
    "indexer",
    "event",
    "accessor",
}


def _single_statement_shape(node, source: bytes, kind: str) -> str | None:
    """Return a small deterministic hard-exclusion reason for thin declarations."""
    if kind == "accessor":
        return "accessor"
    if kind not in {"function", "method", "local_function", "constructor", "operator", "conversion_operator", "property", "indexer", "event"}:
        return None
    body = node.child_by_field_name("body")
    if body is None:
        # Expression-bodied C# members and declarations without a block.
        text = _node_text(node, source)
        if "=>" in text:
            return "single-expression-body"
        return None
    named = [child for child in body.named_children if child.type not in {"comment"}]
    if len(named) != 1:
        return None
    statement = named[0]
    text = _node_text(statement, source)
    if statement.type in {"return_statement", "expression_statement"}:
        if not re.search(r"\b(if|for|foreach|while|switch|try|catch|await|yield|throw|lock)\b", text):
            return "single-return-or-call"
    if statement.type in {"assignment_expression", "local_declaration_statement"}:
        return "single-assignment"
    return None


def _csharp_fallback_name(node, source: bytes, kind: str) -> tuple[str, int, int] | None:
    text = _node_text(node, source)
    if kind == "indexer":
        line, column = _byte_position(source, node.start_byte)
        return "this", line, column
    if kind == "accessor":
        match = re.search(r"\b(get|set|init|add|remove)\b", text)
        if match:
            absolute = node.start_byte + len(text[: match.start()].encode("utf-8"))
            line, column = _byte_position(source, absolute)
            return match.group(1), line, column
    if kind in {"operator", "conversion_operator"}:
        match = re.search(r"\boperator\s+([^\s({]+)", text)
        label = f"operator {match.group(1)}" if match else kind.replace("_", " ")
        line, column = _byte_position(source, node.start_byte)
        return label, line, column
    return None


def _has_ancestor(node: Any, node_type: str) -> bool:
    current = node.parent
    while current is not None:
        if current.type == node_type:
            return True
        current = current.parent
    return False


def _cpp_function_declarator_kind(node: Any) -> str | None:
    """Classify C++ function-shaped nodes that require parent context."""
    if _has_ancestor(node, "template_instantiation"):
        return None
    parent = node.parent
    if parent is not None and parent.type == "reference_declarator" and _has_ancestor(node, "compound_statement"):
        # Tree-sitter intentionally resolves the declaration/expression ambiguity
        # without a symbol table.  In a block, ``const T &x(expr);`` is retained as
        # a declaration fact rather than promoted to a standalone function.
        return "declaration"
    return "function"


def _cpp_explicit_class_instantiation_recovery(node: Any, source: bytes) -> dict[str, Any] | None:
    """Recognize the pinned grammar's sole missing-node shape for ``template class``."""
    if not node.is_missing or node.type != "identifier":
        return None
    parent = node.parent
    if parent is None or parent.type != "template_instantiation":
        return None
    type_node = parent.child_by_field_name("type")
    if type_node is None or type_node.type not in {"class_specifier", "struct_specifier"}:
        return None
    name_node = type_node.child_by_field_name("name")
    if name_node is None or name_node.type != "template_type":
        return None
    text = _node_text(parent, source).strip()
    if not re.match(r"^template\s+(?:class|struct)\b", text) or not text.endswith(";"):
        return None
    start_line, _ = _byte_position(source, parent.start_byte)
    end_line, _ = _byte_position(source, parent.end_byte)
    return {
        "kind": "tree-sitter-cpp-explicit-class-template-instantiation",
        "node_type": node.type,
        "start_line": start_line,
        "end_line": end_line,
    }


def _parse_diagnostics(language: str, root: Any, source: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split known pinned-grammar recoveries from unresolved syntax diagnostics."""
    error_nodes = [node for node in _walk(root) if node.is_error or node.is_missing]
    recoveries: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for node in error_nodes:
        recovery = _cpp_explicit_class_instantiation_recovery(node, source) if language == "cpp" else None
        if recovery is not None:
            recoveries.append(recovery)
            continue
        start_line, _ = _byte_position(source, node.start_byte)
        end_line, _ = _byte_position(source, node.end_byte)
        unresolved.append(
            {
                "node_type": node.type,
                "is_error": bool(node.is_error),
                "is_missing": bool(node.is_missing),
                "start_line": start_line,
                "end_line": end_line,
            }
        )
    if root.has_error and not error_nodes:
        unresolved.append(
            {
                "node_type": root.type,
                "is_error": True,
                "is_missing": False,
                "start_line": 1,
                "end_line": max(1, source.count(b"\n") + 1),
            }
        )
    return recoveries, unresolved


def parse_file(repository: dict[str, Any], file_entry: dict[str, Any], source: bytes) -> dict[str, Any]:
    try:
        from tree_sitter import Parser
    except Exception as exc:
        raise DependencyError(f"Tree-sitter Python binding is unavailable: {exc}") from exc
    # Keep the Language wrapper alive for the full tree/node lifetime.  The
    # native binding owns parser tables through this object; a temporary can be
    # collected during large traversals and invalidate later Node access.
    language = _language(file_entry["language"])
    parser = Parser(language)
    tree = parser.parse(source)
    root = tree.root_node
    recoveries, parse_diagnostics = _parse_diagnostics(file_entry["language"], root, source)
    source_text = source.decode("utf-8", errors="replace")
    file_entity = {
        "id": file_entry["id"],
        "kind": "file",
        "name": Path(file_entry["path"]).name,
        "qualified_name": file_entry["path"],
        "language": file_entry["language"],
        "path": file_entry["path"],
        "blob": file_entry["blob"],
        "commit": repository["commit"],
        "range": {
            "start_byte": 0,
            "end_byte": len(source),
            "start_line": 1,
            "end_line": max(1, source.count(b"\n") + 1),
        },
        "parent_id": None,
        "candidate_classification": "page",
        "classification_evidence": ["file-always-page"],
    }
    entities = [file_entity]
    entity_kind_by_id = {file_entity["id"]: "file"}
    ranges: list[tuple[int, int, str, str]] = []
    file_scoped_namespace: tuple[str, str, int] | None = None
    declarations = DECLARATION_TYPES[file_entry["language"]]
    seen: set[tuple[str, int, int]] = set()
    # Keep every wrapper alive until extraction finishes.  tree-sitter 0.26 on
    # Windows can release native node context too early when generator-produced
    # wrappers are destroyed during a long traversal.
    syntax_nodes = list(_walk(root))
    retained_nodes: list[Any] = list(syntax_nodes)
    for node in syntax_nodes:
        node_type = node.type
        kind = declarations.get(node_type)
        if not kind:
            continue
        if file_entry["language"] == "cpp":
            if _has_ancestor(node, "template_instantiation"):
                continue
            if node_type == "function_declarator":
                kind = _cpp_function_declarator_kind(node)
                if kind is None:
                    continue
        start_byte = node.start_byte
        end_byte = node.end_byte
        start_line, _start_column = _byte_position(source, start_byte)
        end_line, _end_column = _byte_position(source, end_byte)
        named = _find_name(node, source, retained_nodes) or _csharp_fallback_name(node, source, kind)
        if file_entry["language"] == "csharp" and kind == "namespace":
            namespace_name = node.child_by_field_name("name")
            if namespace_name is not None:
                line, column = _byte_position(source, namespace_name.start_byte)
                named = (_node_text(namespace_name, source).strip(), line, column)
        if not named:
            continue
        name, name_line, name_column = named
        if not name or len(name) > 240:
            continue
        key = (name, start_byte, end_byte)
        if key in seen:
            continue
        seen.add(key)
        parent_name = None
        parent_id = file_entity["id"]
        for start, end, candidate_name, candidate_id in reversed(ranges):
            if start <= start_byte and end_byte <= end:
                parent_name = candidate_name
                parent_id = candidate_id
                break
        if parent_name is None and file_scoped_namespace and start_byte >= file_scoped_namespace[2]:
            parent_name, parent_id, _namespace_end = file_scoped_namespace
        qualified = f"{parent_name}.{name}" if parent_name else name
        if node_type == "function_declarator" and kind == "function" and entity_kind_by_id.get(parent_id) == "function":
            continue
        node_text = source[start_byte:end_byte].decode("utf-8", errors="replace")
        line_count = end_line - start_line + 1
        hard_exclusion = (
            f"csharp-default-appendix:{kind}"
            if file_entry["language"] == "csharp" and kind in {"property", "indexer", "event", "accessor"}
            # Python exposes module and object access through these protocol
            # methods.  They are accessors rather than navigational landing
            # pages, even when a cross-file reference gives them a high graph
            # rank.  Keep constructors and other substantial dunder methods
            # eligible; only the four attribute-access hooks are deterministic
            # appendix entities.
            else "python-attribute-accessor"
            if file_entry["language"] == "python"
            and name in {"__getattr__", "__getattribute__", "__setattr__", "__delattr__"}
            else _single_statement_shape(node, source, kind)
        )
        simple = kind not in PAGE_ELIGIBLE_KINDS or hard_exclusion is not None
        public = _public_evidence(file_entry["language"], source_text, node_text, name)
        effects = bool(re.search(r"\b(open|write|save|delete|remove|request|fetch|socket|subprocess|exec|spawn|commit|send|recv)\b", node_text, re.I))
        evidence = []
        if public:
            evidence.append("public-or-exported")
        if kind == "class":
            evidence.append("class-boundary")
        if effects:
            evidence.append("side-effect-orchestration")
        if simple:
            evidence.append("simple-attached-entity")
        candidate = "page" if kind in PAGE_ELIGIBLE_KINDS and not simple else "appendix"
        entity_id = stable_id("ent", repository["commit"], file_entry["blob"], file_entry["path"], start_byte, end_byte, kind, name)
        entity = {
            "id": entity_id,
            "kind": kind,
            "name": name,
            "qualified_name": qualified,
            "language": file_entry["language"],
            "path": file_entry["path"],
            "blob": file_entry["blob"],
            "commit": repository["commit"],
            "range": {
                "start_byte": start_byte,
                "end_byte": end_byte,
                "start_line": start_line,
                "end_line": end_line,
                "name_line": name_line,
                "name_column_utf8": name_column,
            },
            "parent_id": parent_id,
            "candidate_classification": candidate,
            "classification_evidence": evidence or ["attached-by-default"],
            "page_eligible": kind in PAGE_ELIGIBLE_KINDS and hard_exclusion is None,
            "hard_exclusion": hard_exclusion,
            "is_public_or_exported": public,
            "is_partial": file_entry["language"] == "csharp" and bool(re.search(r"\bpartial\b", node_text[: min(len(node_text), 240)])),
        }
        entities.append(entity)
        entity_kind_by_id[entity_id] = kind
        ranges.append((start_byte, end_byte, qualified, entity_id))
        if node_type == "file_scoped_namespace_declaration":
            file_scoped_namespace = (qualified, entity_id, end_byte)
    return {
        "file": file_entry,
        "parse": {
            "status": "failed" if parse_diagnostics else "passed",
            "root_type": root.type,
            "has_error": bool(parse_diagnostics),
            "raw_has_error": bool(root.has_error),
            "recoveries": recoveries,
            "diagnostics": parse_diagnostics,
        },
        "entities": entities,
    }


def merge_csharp_partials(repository: dict[str, Any], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge partial C# type declarations into one logical entity with audited fragments."""
    type_kinds = {"class", "struct", "record", "interface"}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entity in entities:
        if entity.get("language") == "csharp" and entity.get("kind") in type_kinds and entity.get("is_partial"):
            groups.setdefault((entity["kind"], entity["qualified_name"]), []).append(entity)
    replacements: dict[str, str] = {}
    merged_by_old: dict[str, dict[str, Any]] = {}
    removed: set[str] = set()
    for (kind, qualified), values in sorted(groups.items()):
        if len(values) < 2:
            continue
        ordered = sorted(values, key=lambda item: (item["path"], item["range"]["start_byte"], item["id"]))
        primary = sorted(
            ordered,
            key=lambda item: (
                -sum(1 for child in entities if child.get("parent_id") == item["id"] and child.get("page_eligible")),
                item["path"],
                item["range"]["start_byte"],
                item["id"],
            ),
        )[0]
        logical_id = stable_id("ent", repository["commit"], "csharp-partial", kind, qualified)
        logical = dict(primary)
        logical["id"] = logical_id
        logical["partial"] = True
        logical["fragments"] = [
            {
                "fragment_id": value["id"],
                "path": value["path"],
                "blob": value["blob"],
                "range": value["range"],
            }
            for value in ordered
        ]
        logical["classification_evidence"] = sorted(set(logical.get("classification_evidence", []) + ["partial-logical-entity"]))
        for value in ordered:
            replacements[value["id"]] = logical_id
            merged_by_old[value["id"]] = logical
            removed.add(value["id"])
    if not replacements:
        return entities
    result: list[dict[str, Any]] = []
    emitted: set[str] = set()
    for entity in entities:
        if entity["id"] in removed:
            logical = merged_by_old[entity["id"]]
            if logical["id"] not in emitted:
                result.append(logical)
                emitted.add(logical["id"])
            continue
        value = dict(entity)
        if value.get("parent_id") in replacements:
            value["parent_id"] = replacements[value["parent_id"]]
        result.append(value)
    return result


def lexical_links(entities: list[dict[str, Any]], sources: dict[str, bytes]) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        if entity["kind"] != "file" and len(entity["name"]) >= 2:
            by_name.setdefault(entity["name"], []).append(entity)
    links: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for source_entity in entities:
        if source_entity["kind"] == "file":
            continue
        data = sources.get(source_entity["path"], b"")
        region = data[source_entity["range"]["start_byte"] : source_entity["range"]["end_byte"]].decode("utf-8", errors="replace")
        referenced_names = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", region))
        for name in sorted(referenced_names.intersection(by_name)):
            targets = by_name[name]
            if name == source_entity["name"]:
                continue
            if len(targets) != 1:
                continue
            target = targets[0]
            if target["id"] == source_entity["id"]:
                continue
            key = (source_entity["id"], target["id"], "references")
            if key in seen:
                continue
            seen.add(key)
            links.append({
                "id": stable_id("link", *key),
                "type": "references",
                "source": source_entity["id"],
                "target": target["id"],
                "provider": "tree-sitter-lexical-candidate",
                "evidence": {"name": name, "source_path": source_entity["path"]},
            })
    for entity in entities:
        if entity["parent_id"]:
            key = (entity["parent_id"], entity["id"], "contains")
            links.append({
                "id": stable_id("link", *key),
                "type": "contains",
                "source": entity["parent_id"],
                "target": entity["id"],
                "provider": "tree-sitter",
                "evidence": {"path": entity["path"], "range": entity["range"]},
            })
    return links
