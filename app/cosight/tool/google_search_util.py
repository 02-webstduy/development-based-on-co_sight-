# Copyright 2025 ZTE Corporation.
# All Rights Reserved.
#
# DEPRECATED: Use SearchToolkit.search_google (Custom Search API) instead.
# This module scrapes Google via googlesearch-python and can hang without strict limits.

import warnings
from typing import List, Dict, Any
import os
from googlesearch import search
from bs4 import BeautifulSoup
import random
import asyncio
import aiohttp
from .scrape_website_toolkit import is_valid_url
from app.common.logger_util import logger
from app.common.http_timeout import get_http_timeout, get_tool_exec_timeout, run_with_timeout


def _deprecated_search_warning() -> None:
    warnings.warn(
        "google_search_util is deprecated and may hang on rate limits. "
        "Use app.cosight.tool.search_toolkit.SearchToolkit.search_google instead.",
        DeprecationWarning,
        stacklevel=3,
    )


async def fetch_url_content(url: str) -> str:
    """Fetch and parse content from a given URL"""
    try:
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        proxy = os.environ.get("PROXY")
        if not is_valid_url(url):
            return f'current url is valid {url}'
        connect_timeout, read_timeout = get_http_timeout()
        timeout = aiohttp.ClientTimeout(
            total=read_timeout,
            connect=connect_timeout,
            sock_read=read_timeout,
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' not in content_type:
                        return f"Non-HTML content: {content_type}"

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
                        element.decompose()

                    text = soup.get_text(separator='\n')
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)

                    return text
                else:
                    return f"HTTP Error: {response.status}"

    except asyncio.TimeoutError as e:
        logger.error(f"Request timed out: {str(e)}", exc_info=True)
        return "Request timed out"
    except Exception as e:
        logger.error(f"Error fetching content: {str(e)}", exc_info=True)
        return f"Error fetching content: {str(e)}"


def _search_google_impl(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    _deprecated_search_warning()
    logger.info(f"search google for {query}")
    responses: List[Dict[str, Any]] = []

    max_retries = 3
    proxy = os.environ.get("PROXY")
    for attempt in range(max_retries):
        try:
            links = list(search(query, num_results=max_results, proxy=proxy, advanced=True))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def process_links():
                tasks = []
                for i, link in enumerate(links, start=1):
                    tasks.append((i, link, fetch_url_content(link.url)))
                fetch_results = await asyncio.gather(*[task[2] for task in tasks])
                for idx, (i, link, _) in enumerate(tasks):
                    response = {
                        "result_id": i,
                        "title": link.title,
                        "description": link.description,
                        "url": link.url,
                        "content": fetch_results[idx]
                    }
                    responses.append(response)

            loop.run_until_complete(process_links())
            loop.close()
            break
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            if attempt == max_retries - 1:
                responses.append({"error": f"Google search failed after {max_retries} attempts: {e}"})
    logger.info(f"search google for {responses}")
    return responses


def search_google(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Deprecated scraper-based Google search. Prefer SearchToolkit.search_google."""
    try:
        return run_with_timeout(_search_google_impl, get_tool_exec_timeout(), query, max_results)
    except TimeoutError:
        logger.error(f"search_google timed out for query: {query}", exc_info=True)
        return [{"error": f"Google search timed out after {get_tool_exec_timeout()}s"}]
