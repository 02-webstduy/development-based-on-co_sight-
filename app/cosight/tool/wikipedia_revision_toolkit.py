# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

"""MediaWiki revision API tools — program-computed stats, not search summaries."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from app.common.http_timeout import get_http_timeout
from app.common.logger_util import logger

DEFAULT_USER_AGENT = os.environ.get(
    "WIKIPEDIA_USER_AGENT",
    "CoSight/1.0 (https://github.com; research bot) Python requests",
)
REF_TAG_PATTERN = re.compile(r"<ref\b", re.IGNORECASE)
SECTION_HEADER_PATTERN = re.compile(r"^(=+)\s*(.+?)\s*\1\s*$", re.MULTILINE)


class WikipediaRevisionToolkit:
  def __init__(self, lang: str = "en"):
    self.lang = lang
    self.api_url = f"https://{lang}.wikipedia.org/w/api.php"
    proxy = os.environ.get("PROXY")
    self.proxies = {"http": proxy, "https": proxy} if proxy else None
    self.http_timeout = get_http_timeout()
    self.headers = {"User-Agent": DEFAULT_USER_AGENT}

  def _api_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
    base = {"format": "json", "formatversion": "2"}
    base.update(params)
    response = requests.get(
      self.api_url,
      params=base,
      headers=self.headers,
      proxies=self.proxies,
      timeout=self.http_timeout,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
      raise RuntimeError(f"MediaWiki API error: {data['error']}")
    return data

  def get_revisions(
    self,
    title: str,
    start: str,
    end: str,
    props: Optional[List[str]] = None,
  ) -> str:
    """Fetch all revisions in [start, end] (ISO timestamps). Returns compact JSON."""
    rvprop = "|".join(props or ["ids", "timestamp", "size", "comment", "user"])
    revisions: List[Dict[str, Any]] = []
    continue_token: Optional[str] = None

    while True:
      params: Dict[str, Any] = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvlimit": "500",
        "rvstart": start,
        "rvend": end,
        "rvdir": "newer",
        "rvprop": rvprop,
      }
      if continue_token:
        params["rvcontinue"] = continue_token

      data = self._api_get(params)
      pages = data.get("query", {}).get("pages", [])
      if not pages:
        break
      page = pages[0]
      if page.get("missing"):
        return json.dumps(
          {
            "title": title,
            "error": "page_not_found",
            "revision_count": 0,
            "revisions": [],
          },
          ensure_ascii=False,
        )
      batch = page.get("revisions", []) or []
      for rev in batch:
        revisions.append(
          {
            "revid": rev.get("revid"),
            "parentid": rev.get("parentid"),
            "timestamp": rev.get("timestamp"),
            "size": rev.get("size"),
            "user": rev.get("user"),
            "comment": (rev.get("comment") or "")[:200],
          }
        )
      cont = data.get("continue", {})
      continue_token = cont.get("rvcontinue")
      if not continue_token:
        break

    payload = {
      "title": title,
      "lang": self.lang,
      "start": start,
      "end": end,
      "revision_count": len(revisions),
      "revisions": revisions,
      "source": f"{self.api_url}?action=query&prop=revisions",
    }
    logger.info(f"get_revisions {title}: {len(revisions)} revisions")
    return json.dumps(payload, ensure_ascii=False)

  def count_wikipedia_edits_in_year(self, title: str, year: int) -> str:
    """Program count of edits in a calendar year (UTC)."""
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year}-12-31T23:59:59Z"
    raw = json.loads(self.get_revisions(title, start, end, props=["ids", "timestamp", "size"]))
    return json.dumps(
      {
        "title": title,
        "year": year,
        "edit_count": raw.get("revision_count", 0),
        "method": "mediawiki_revisions_api_paginated_count",
        "source": raw.get("source"),
      },
      ensure_ascii=False,
    )

  def get_revision_before_date(self, title: str, before: str) -> str:
    """Latest revision strictly before an ISO timestamp (UTC)."""
    data = self._api_get(
      {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvlimit": "1",
        "rvstart": before,
        "rvdir": "older",
        "rvprop": "ids|timestamp|size|comment",
      }
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
      return json.dumps(
        {"title": title, "before": before, "error": "page_not_found"},
        ensure_ascii=False,
      )
    revs = pages[0].get("revisions") or []
    if not revs:
      return json.dumps(
        {"title": title, "before": before, "error": "no_revision_before_date"},
        ensure_ascii=False,
      )
    rev = revs[0]
    return json.dumps(
      {
        "title": pages[0].get("title", title),
        "before": before,
        "revid": rev.get("revid"),
        "timestamp": rev.get("timestamp"),
        "size": rev.get("size"),
      },
      ensure_ascii=False,
    )

  def _fetch_full_revision_wikitext(self, revid: int) -> str:
    data = self._api_get(
      {
        "action": "query",
        "revids": str(revid),
        "prop": "revisions",
        "rvprop": "content",
      }
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or not pages[0].get("revisions"):
      return ""
    rev = pages[0]["revisions"][0]
    return rev.get("slots", {}).get("main", {}).get("*") or rev.get("content", "") or ""

  def get_revision_content(self, revid: int) -> str:
    """Wikitext preview for a specific oldid (truncated for LLM context only).

    Do NOT use this output for programmatic counting or section extraction —
    use count_references_for_revision / extract_section_from_revision instead.
    """
    content = self._fetch_full_revision_wikitext(revid)
    if not content:
      return json.dumps({"revid": revid, "error": "revision_not_found"}, ensure_ascii=False)
    return json.dumps(
      {
        "revid": revid,
        "content_length": len(content),
        "wikitext": content[:8000] if len(content) > 8000 else content,
        "truncated": len(content) > 8000,
        "note": "preview_only_not_for_computation",
      },
      ensure_ascii=False,
    )

  def count_wikipedia_references(self, wikitext: str) -> str:
    """Count <ref> tags in wikitext (programmatic)."""
    count = len(REF_TAG_PATTERN.findall(wikitext or ""))
    return json.dumps({"reference_count": count, "method": "ref_tag_regex"}, ensure_ascii=False)

  def count_references_for_revision(self, revid: int) -> str:
    wikitext = self._fetch_full_revision_wikitext(revid)
    if not wikitext:
      return json.dumps({"revid": revid, "error": "revision_not_found"}, ensure_ascii=False)
    ref = json.loads(self.count_wikipedia_references(wikitext))
    ref["revid"] = revid
    ref["content_length"] = len(wikitext)
    ref["method"] = "ref_tag_regex_full_wikitext"
    return json.dumps(ref, ensure_ascii=False)

  def extract_wikipedia_section(self, wikitext: str, section_title: str) -> str:
    """Extract one == Section == block only."""
    if not wikitext:
      return json.dumps({"section": section_title, "content": "", "error": "empty_wikitext"}, ensure_ascii=False)
    target = section_title.strip().lower()
    sections: List[tuple[int, str, int]] = []
    for match in SECTION_HEADER_PATTERN.finditer(wikitext):
      level = len(match.group(1))
      name = match.group(2).strip()
      sections.append((match.start(), name, level))

    for idx, (start, name, level) in enumerate(sections):
      if name.lower() != target and target not in name.lower():
        continue
      end = len(wikitext)
      for next_start, _, next_level in sections[idx + 1 :]:
        if next_level <= level:
          end = next_start
          break
      body = wikitext[start:end].strip()
      return json.dumps(
        {
          "section": name,
          "content": body[:4000],
          "content_length": len(body),
          "truncated": len(body) > 4000,
          "note": "section located on full wikitext; content capped for LLM context",
        },
        ensure_ascii=False,
      )
    return json.dumps(
      {"section": section_title, "content": "", "error": "section_not_found"},
      ensure_ascii=False,
    )

  def extract_section_from_revision(self, revid: int, section_title: str) -> str:
    wikitext = self._fetch_full_revision_wikitext(revid)
    if not wikitext:
      return json.dumps({"revid": revid, "error": "revision_not_found"}, ensure_ascii=False)
    return self.extract_wikipedia_section(wikitext, section_title)

  def _first_revision_in_year(self, title: str, year: int) -> Optional[Dict[str, Any]]:
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year}-12-31T23:59:59Z"
    data = json.loads(self.get_revisions(title, start, end, props=["ids", "timestamp", "size"]))
    revs = data.get("revisions") or []
    return revs[0] if revs else None

  def compute_wikipedia_reference_delta(self, title: str, year_a: int, year_b: int) -> str:
    """Reference count delta: first revision in year_b minus first in year_a."""
    rev_a = self._first_revision_in_year(title, year_a)
    rev_b = self._first_revision_in_year(title, year_b)
    if not rev_a or not rev_b:
      return json.dumps(
        {
          "title": title,
          "error": "missing_revision",
          "year_a": year_a,
          "year_b": year_b,
          "rev_a": rev_a,
          "rev_b": rev_b,
        },
        ensure_ascii=False,
      )
    count_a = json.loads(self.count_references_for_revision(rev_a["revid"]))["reference_count"]
    count_b = json.loads(self.count_references_for_revision(rev_b["revid"]))["reference_count"]
    return json.dumps(
      {
        "title": title,
        "year_a": year_a,
        "year_b": year_b,
        "revid_a": rev_a["revid"],
        "revid_b": rev_b["revid"],
        "reference_count_a": count_a,
        "reference_count_b": count_b,
        "delta": count_b - count_a,
        "method": "first_revision_per_year_ref_count",
      },
      ensure_ascii=False,
    )

  def find_wikipedia_revision_by_size_delta(self, title: str, year: int, target_delta: int) -> str:
    """Find revision in year whose size increase from parent equals target_delta."""
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year}-12-31T23:59:59Z"
    data = json.loads(self.get_revisions(title, start, end, props=["ids", "timestamp", "size", "parentid"]))
    revs = sorted(data.get("revisions") or [], key=lambda r: r.get("timestamp") or "")
    sizes = {r["revid"]: r.get("size") for r in revs}
    for rev in revs:
      parent = rev.get("parentid")
      if parent is None or parent not in sizes:
        continue
      delta = (rev.get("size") or 0) - (sizes.get(parent) or 0)
      if delta == target_delta:
        ts = rev.get("timestamp", "")
        date_str = ts[:10].replace("-", "/") if ts else ""
        return json.dumps(
          {
            "title": title,
            "year": year,
            "target_delta": target_delta,
            "matched": True,
            "revid": rev["revid"],
            "timestamp": ts,
            "date": date_str,
            "size_delta": delta,
          },
          ensure_ascii=False,
        )
    return json.dumps(
      {
        "title": title,
        "year": year,
        "target_delta": target_delta,
        "matched": False,
        "message": "no_revision_with_exact_size_delta_in_year",
      },
      ensure_ascii=False,
    )
