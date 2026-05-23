# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

"""Compress tool outputs before they enter LLM context."""

from __future__ import annotations

import json
from typing import Any, Dict

# Per-tool max chars injected into agent context
EVIDENCE_LIMITS: Dict[str, int] = {
    "get_wikipedia_revisions": 4000,
    "count_wikipedia_edits_in_year": 800,
    "get_wikipedia_revision_content": 6000,
    "count_wikipedia_references": 400,
    "count_references_for_revision": 400,
    "extract_wikipedia_section": 2500,
    "extract_section_from_revision": 2500,
    "compute_wikipedia_reference_delta": 800,
    "find_wikipedia_revision_by_size_delta": 800,
    "get_wikipedia_revision_before_date": 600,
    "count_train_line_station_connections": 3500,
    "lookup_book_publication_year": 500,
    "count_term_occurrences": 400,
    "extract_abstract_from_text": 2500,
    "count_reference_year_in_paper_abstract": 1200,
    "search_book_page_for_text": 1500,
    "search_wiki": 1200,
    "search_google": 1500,
    "tavily_search": 1500,
    "search_baidu": 1500,
    "fetch_website_content": 1500,
    "deep_search": 2000,
    "default": 2000,
}

WIKI_STRUCTURED_TOOLS = {
    "get_wikipedia_revisions",
    "count_wikipedia_edits_in_year",
    "get_wikipedia_revision_content",
    "count_wikipedia_references",
    "count_references_for_revision",
    "extract_wikipedia_section",
    "extract_section_from_revision",
    "compute_wikipedia_reference_delta",
    "find_wikipedia_revision_by_size_delta",
    "get_wikipedia_revision_before_date",
}

CONTEST_STRUCTURED_TOOLS = WIKI_STRUCTURED_TOOLS | {
    "count_train_line_station_connections",
    "lookup_book_publication_year",
    "count_term_occurrences",
    "extract_abstract_from_text",
    "count_reference_year_in_paper_abstract",
    "search_book_page_for_text",
}


def reduce_tool_result(tool_name: str, tool_result: str) -> str:
    """Return evidence-safe text for LLM context."""
    raw = "" if tool_result is None else str(tool_result)
    limit = EVIDENCE_LIMITS.get(tool_name, EVIDENCE_LIMITS["default"])

    if tool_name in WIKI_STRUCTURED_TOOLS:
        try:
            obj = json.loads(raw)
            compact = _compact_wiki_payload(tool_name, obj)
            text = json.dumps(compact, ensure_ascii=False)
        except json.JSONDecodeError:
            text = raw
    elif tool_name in CONTEST_STRUCTURED_TOOLS:
        try:
            obj = json.loads(raw)
            compact = _compact_contest_payload(tool_name, obj)
            text = json.dumps(compact, ensure_ascii=False)
        except json.JSONDecodeError:
            text = raw
    else:
        text = _web_evidence_snippet(raw, limit)

    if len(text) > limit:
        text = text[:limit] + f"\n...[evidence truncated at {limit} chars]"
    return text


def _compact_wiki_payload(tool_name: str, obj: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "get_wikipedia_revisions":
        revs = obj.get("revisions") or []
        return {
            "title": obj.get("title"),
            "revision_count": obj.get("revision_count"),
            "sample": revs[:5],
            "note": f"total {len(revs)} revisions; full list omitted from context",
        }
    if tool_name == "get_wikipedia_revision_content":
        return {
            "revid": obj.get("revid"),
            "content_length": obj.get("content_length"),
            "truncated": obj.get("truncated"),
            "wikitext_preview": (obj.get("wikitext") or "")[:1500],
        }
    return obj


def _compact_contest_payload(tool_name: str, obj: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "count_train_line_station_connections":
        compact = {
            "train_page_title": obj.get("train_page_title"),
            "as_of_date": obj.get("as_of_date"),
            "connection_count": obj.get("connection_count"),
            "unique_connecting_lines": obj.get("unique_connecting_lines"),
            "station_count": obj.get("station_count"),
            "error": obj.get("error"),
            "note": "full per-station map omitted from context",
        }
        # When count is 0 or error, keep diagnostics so the model can retry/debug.
        if obj.get("error") or obj.get("connection_count") == 0:
            compact["stations"] = (obj.get("stations") or [])[:8]
            compact["connections_by_station"] = {
                k: v
                for k, v in list((obj.get("connections_by_station") or {}).items())[:5]
            }
            debug = obj.get("pipeline_debug") or {}
            compact["pipeline_debug"] = debug.get("stage", [])[-1:] if debug else None
        return compact
    if tool_name == "search_book_page_for_text":
        return {
            "book_title": obj.get("book_title"),
            "edition_year": obj.get("edition_year"),
            "page_number": obj.get("page_number"),
            "best_match": obj.get("best_match"),
            "error": obj.get("error"),
            "pdf_url": obj.get("pdf_url"),
        }
    if tool_name in ("count_reference_year_in_paper_abstract",):
        return {
            k: obj.get(k)
            for k in (
                "paper_title",
                "reference_book_title",
                "publication_year",
                "year_mention_count",
                "error",
                "abstract_preview",
            )
        }
    return obj


def _web_evidence_snippet(text: str, limit: int) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return (
        stripped[:limit]
        + "\n\n[evidence: web snippet only — do not treat as complete source]"
    )
