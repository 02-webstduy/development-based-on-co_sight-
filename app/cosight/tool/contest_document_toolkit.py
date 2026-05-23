# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

"""Document retrieval + programmatic text analysis for contest Q4/Q10."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urljoin

import requests

from app.common.http_timeout import get_http_timeout
from app.common.logger_util import logger
from app.cosight.tool.document_processing_toolkit import DocumentProcessingToolkit
from app.cosight.tool.search_toolkit import SearchToolkit

DEFAULT_USER_AGENT = os.environ.get(
    "WIKIPEDIA_USER_AGENT",
    "CoSight/1.0 (https://github.com; research bot) Python requests",
)
ABSTRACT_PATTERNS = (
    re.compile(r"(?is)\babstract\b[:\s]*(.{100,8000}?)(?:\n\s*\n|\bkeywords\b|\bkey words\b|\bintroduction\b|\b1\.\s|\bsummary\b|\Z)"),
    re.compile(r"(?is)\bantr(?:as|ra)t(?:as|is)\b[:\s]*(.{100,8000}?)(?:\n\s*\n|\brakt(?:iniai|iniai)\b|\b1\.\s|\Z)"),
)
YEAR_PATTERN = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
ARCHIVE_SEARCH_URL = "https://archive.org/advancedsearch.php"


class ContestDocumentToolkit:
    def __init__(self):
        proxy = os.environ.get("PROXY")
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.http_timeout = get_http_timeout()
        self.headers = {"User-Agent": DEFAULT_USER_AGENT}
        self.doc_toolkit = DocumentProcessingToolkit()
        self.search_toolkit = SearchToolkit()

    def lookup_book_publication_year(self, book_title: str) -> str:
        """Return publication year for a book via Open Library then Wikipedia."""
        year = self._open_library_publication_year(book_title)
        source = "open_library"
        if year is None:
            year = self._wikipedia_publication_year(book_title)
            source = "wikipedia_summary"
        return json.dumps(
            {
                "book_title": book_title,
                "publication_year": year,
                "source": source,
                "method": "programmatic_metadata_lookup",
            },
            ensure_ascii=False,
        )

    def count_term_occurrences(self, text: str, term: str, case_sensitive: bool = False) -> str:
        """Count non-overlapping occurrences of *term* in *text*."""
        if not case_sensitive:
            count = len(re.findall(re.escape(term), text, re.IGNORECASE))
        else:
            count = text.count(term)
        return json.dumps(
            {
                "term": term,
                "occurrence_count": count,
                "text_length": len(text),
                "method": "regex_count" if not case_sensitive else "literal_count",
            },
            ensure_ascii=False,
        )

    def extract_abstract_from_text(self, text: str) -> str:
        """Extract abstract section from academic paper plain text."""
        for pattern in ABSTRACT_PATTERNS:
            match = pattern.search(text)
            if match:
                abstract = match.group(1).strip()
                return json.dumps(
                    {
                        "abstract": abstract[:6000],
                        "abstract_length": len(abstract),
                        "truncated": len(abstract) > 6000,
                        "method": "abstract_heading_regex",
                    },
                    ensure_ascii=False,
                )
        preview = text[:4000].strip()
        return json.dumps(
            {
                "abstract": preview,
                "abstract_length": len(preview),
                "truncated": True,
                "warning": "abstract_heading_not_found_using_leading_text",
                "method": "fallback_leading_text",
            },
            ensure_ascii=False,
        )

    def count_reference_year_in_paper_abstract(
        self,
        paper_title: str,
        author: str,
        reference_book_title: str,
        document_url: str = "",
    ) -> str:
        """Q4 pipeline: find paper abstract, lookup book year, count year mentions."""
        book_meta = json.loads(self.lookup_book_publication_year(reference_book_title))
        year = book_meta.get("publication_year")
        if year is None:
            return json.dumps(
                {
                    "error": "reference_book_year_not_found",
                    "paper_title": paper_title,
                    "reference_book_title": reference_book_title,
                    "book_lookup": book_meta,
                },
                ensure_ascii=False,
            )
        year_str = str(year)

        doc_text, doc_source = self._fetch_paper_text(paper_title, author, document_url)
        if not doc_text:
            return json.dumps(
                {
                    "error": "paper_text_not_found",
                    "paper_title": paper_title,
                    "author": author,
                    "document_url": document_url,
                    "reference_book_title": reference_book_title,
                    "publication_year": year,
                },
                ensure_ascii=False,
            )

        abstract_payload = json.loads(self.extract_abstract_from_text(doc_text))
        abstract = abstract_payload.get("abstract", "")
        count_payload = json.loads(
            self.count_term_occurrences(abstract, year_str, case_sensitive=False)
        )

        return json.dumps(
            {
                "paper_title": paper_title,
                "author": author,
                "reference_book_title": reference_book_title,
                "publication_year": year,
                "document_source": doc_source,
                "abstract_extraction": abstract_payload.get("method"),
                "abstract_preview": abstract[:500],
                "year_mention_count": count_payload["occurrence_count"],
                "method": "abstract_year_programmatic_count",
            },
            ensure_ascii=False,
        )

    def search_book_page_for_text(
        self,
        book_title: str,
        edition_year: int,
        search_phrases: List[str],
        pdf_url: str = "",
    ) -> str:
        """Q10 pipeline: locate phrase in a specific book edition PDF; return page number."""
        phrases = [p.strip() for p in search_phrases if p and p.strip()]
        if not phrases:
            return json.dumps({"error": "search_phrases_required"}, ensure_ascii=False)

        resolved_url = pdf_url.strip() if pdf_url else ""
        archive_meta: Dict[str, Any] = {}
        if not resolved_url:
            resolved_url, archive_meta = self._find_archive_pdf(book_title, edition_year)

        if not resolved_url:
            return json.dumps(
                {
                    "error": "pdf_not_found",
                    "book_title": book_title,
                    "edition_year": edition_year,
                    "search_phrases": phrases,
                    "archive_search": archive_meta,
                },
                ensure_ascii=False,
            )

        local_path = self._download_pdf(resolved_url)
        if not local_path:
            return json.dumps(
                {
                    "error": "pdf_download_failed",
                    "pdf_url": resolved_url,
                    "book_title": book_title,
                },
                ensure_ascii=False,
            )

        matches = self._search_pdf_pages(local_path, phrases)
        best = matches[0] if matches else None
        return json.dumps(
            {
                "book_title": book_title,
                "edition_year": edition_year,
                "search_phrases": phrases,
                "pdf_url": resolved_url,
                "pdf_local_path": local_path,
                "archive_search": archive_meta,
                "match_count": len(matches),
                "best_match": best,
                "page_number": best["page_number"] if best else None,
                "all_matches": matches[:10],
                "method": "pdf_page_text_search",
                "note": "page_number is 1-based PDF page index; verify against printed page if footer visible",
            },
            ensure_ascii=False,
        )

    # --- helpers ---

    def _open_library_publication_year(self, book_title: str) -> Optional[int]:
        try:
            resp = requests.get(
                "https://openlibrary.org/search.json",
                params={"q": book_title, "limit": 5},
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.http_timeout,
            )
            resp.raise_for_status()
            docs = resp.json().get("docs") or []
            for doc in docs:
                year = doc.get("first_publish_year")
                if year:
                    return int(year)
                for y in doc.get("publish_year") or []:
                    return int(y)
        except Exception as exc:
            logger.warning(f"Open Library lookup failed: {exc}")
        return None

    def _wikipedia_publication_year(self, book_title: str) -> Optional[int]:
        try:
            summary = self.search_toolkit.search_wiki(book_title)
            match = YEAR_PATTERN.search(summary)
            if match:
                return int(match.group(1))
        except Exception as exc:
            logger.warning(f"Wikipedia year lookup failed: {exc}")
        return None

    def _fetch_paper_text(
        self, paper_title: str, author: str, document_url: str
    ) -> Tuple[str, str]:
        if document_url:
            text = self._extract_doc_text(document_url)
            if text:
                return text, document_url

        query = f"{paper_title} {author} abstract pdf"
        for url in self._search_result_urls(query, max_results=8):
            if not any(ext in url.lower() for ext in (".pdf", ".doc", ".docx", "pdf")):
                continue
            text = self._extract_doc_text(url)
            if text and len(text) > 200:
                return text, url

        for url in self._search_result_urls(query, max_results=5):
            text = self._extract_doc_text(url)
            if text and len(text) > 300:
                return text, url
        return "", ""

    def _extract_doc_text(self, path_or_url: str) -> str:
        try:
            content = self.doc_toolkit.extract_document_content(path_or_url)
            if isinstance(content, tuple):
                ok, text = content
                return str(text) if ok and text else ""
            return str(content) if content else ""
        except Exception as exc:
            logger.warning(f"extract_document_content failed for {path_or_url}: {exc}")
            return ""

    def _search_result_urls(self, query: str, max_results: int = 5) -> List[str]:
        urls: List[str] = []
        if os.environ.get("TAVILY_API_KEY"):
            try:
                raw = self.search_toolkit.tavily_search(query)
                items = raw if isinstance(raw, list) else []
                for item in items:
                    link = item.get("url") or item.get("link")
                    if link:
                        urls.append(link)
            except Exception as exc:
                logger.warning(f"tavily search failed: {exc}")

        if not urls and os.environ.get("GOOGLE_API_KEY") and os.environ.get("SEARCH_ENGINE_ID"):
            try:
                raw = self.search_toolkit.search_google(query)
                if isinstance(raw, list):
                    for item in raw:
                        link = item.get("link") or item.get("url")
                        if link:
                            urls.append(link)
            except Exception as exc:
                logger.warning(f"google search failed: {exc}")

        return urls[:max_results]

    def _find_archive_pdf(self, book_title: str, edition_year: int) -> Tuple[str, Dict[str, Any]]:
        query = f'title:"{book_title}" AND year:{edition_year}'
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "year", "creator"],
            "rows": 10,
            "output": "json",
        }
        try:
            resp = requests.get(
                ARCHIVE_SEARCH_URL,
                params=params,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.http_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            docs = data.get("response", {}).get("docs") or []
            meta = {"query": query, "candidates": docs}
            for doc in docs:
                identifier = doc.get("identifier")
                if not identifier:
                    continue
                pdf_url = f"https://archive.org/download/{identifier}/{identifier}.pdf"
                head = requests.head(
                    pdf_url,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=self.http_timeout,
                    allow_redirects=True,
                )
                if head.status_code == 200:
                    return pdf_url, meta
            return "", meta
        except Exception as exc:
            logger.warning(f"Archive.org search failed: {exc}")
            return "", {"query": query, "error": str(exc)}

    def _download_pdf(self, url: str) -> str:
        cache_dir = "tmp/contest_docs"
        os.makedirs(cache_dir, exist_ok=True)
        name = re.sub(r"[^\w.-]+", "_", url.split("/")[-1])[:80] or "book.pdf"
        path = os.path.join(cache_dir, name)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return path
        try:
            resp = requests.get(
                url,
                stream=True,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.http_timeout,
            )
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
        except Exception as exc:
            logger.error(f"PDF download failed: {exc}")
            return ""

    def _search_pdf_pages(self, pdf_path: str, phrases: List[str]) -> List[Dict[str, Any]]:
        from pypdf import PdfReader

        lowered = [p.lower() for p in phrases]
        matches: List[Dict[str, Any]] = []
        reader = PdfReader(pdf_path)
        for idx, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                continue
            text_lower = text.lower()
            if all(p in text_lower for p in lowered):
                snippet_start = max(text_lower.find(lowered[0]), 0)
                matches.append(
                    {
                        "page_number": idx,
                        "snippet": text[snippet_start : snippet_start + 240].strip(),
                    }
                )
        return matches
