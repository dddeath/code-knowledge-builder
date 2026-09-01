"""Deterministic query terms for identifiers and Chinese prose."""

from __future__ import annotations

import re
import unicodedata


MAX_QUERY_TERMS = 64
DEFAULT_FTS_TERM_LIMIT = 16

# These fixed query-glue characters are not a segmentation dictionary.  They
# only prevent sliding grams from crossing common grammatical boundaries.  The
# complete CJK run is retained, so negation and exact short phrases remain
# available without promoting fragments such as ``包不满`` or ``回的检``.
_CJK_QUERY_GLUE = frozenset("的了和与及或并而在把被将向从到为对时是会否不")
_CODE_RUN = re.compile(r"[A-Za-z0-9_.$:/\\#+-]+")
_CODE_SEPARATOR = re.compile(r"[._$:/\\#+-]+")
_CJK_RUN = re.compile(r"[\u3400-\u9fff]+")
_CJK_GLUE_RUN = re.compile("[" + "".join(sorted(_CJK_QUERY_GLUE)) + "]+")


def _split_camel(value: str) -> list[str]:
    return [
        part
        for part in re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value).replace("::", " ").split()
        if part
    ]


def _ranked_terms(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text)
    priorities: dict[str, int] = {}

    def add(value: str, priority: int) -> None:
        if value:
            priorities[value] = min(priorities.get(value, priority), priority)

    for run in _CODE_RUN.findall(normalized):
        lowered = run.casefold().strip("._$:/\\#+-")
        if len(lowered) >= 2:
            add(lowered, 0)
        for part in _CODE_SEPARATOR.split(run):
            if len(part) >= 2:
                add(part.casefold(), 1)
            for camel in _split_camel(part):
                if len(camel) >= 2:
                    add(camel.casefold(), 1)

    for run in _CJK_RUN.findall(normalized):
        # Preserve the complete phrase, including a single explicit Han
        # character.  FTS filtering separately requires at least three code
        # points because every CKB FTS table uses the trigram tokenizer.
        add(run, 0)
        for span in (value for value in _CJK_GLUE_RUN.split(run) if value):
            if len(span) >= 2:
                add(span, 1)
            for width, priority in ((3, 2), (2, 3)):
                for index in range(max(0, len(span) - width + 1)):
                    add(span[index : index + width], priority)

    return sorted(priorities, key=lambda value: (priorities[value], -len(value), value))


def search_terms(text: str, limit: int = MAX_QUERY_TERMS) -> list[str]:
    """Return bounded query terms in fixed signal, length, and lexical order."""
    if limit < 0:
        raise ValueError("query term limit must be non-negative")
    return _ranked_terms(text)[:limit]


def index_terms(text: str) -> list[str]:
    """Return the same deterministic terms without the query-side cap."""
    return _ranked_terms(text)


def fts_query_terms(text: str, limit: int = DEFAULT_FTS_TERM_LIMIT) -> list[str]:
    """Select trigram-compatible terms from the bounded query ordering."""
    if limit < 0:
        raise ValueError("FTS term limit must be non-negative")
    return [term for term in search_terms(text) if len(term) >= 3][:limit]


def build_fts_query(text: str, limit: int = DEFAULT_FTS_TERM_LIMIT) -> str | None:
    values = fts_query_terms(text, limit)
    if not values:
        return None
    return " OR ".join('"' + value.replace('"', '""') + '"' for value in values)


def explicit_anchors(text: str) -> list[str]:
    """Retain explicit code anchors independently from prose term ranking."""
    normalized = unicodedata.normalize("NFKC", text)
    anchors: set[str] = set()
    for value in re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*(?:(?:::|[./#$:-])[A-Za-z0-9_]+)+|[A-Za-z_][A-Za-z0-9_]{2,}",
        normalized,
    ):
        if (
            any(character.isupper() for character in value[1:])
            or any(character in value for character in "_./#$:-")
            or any(character.isdigit() for character in value)
        ):
            anchors.add(value.casefold())
    return sorted(anchors)
