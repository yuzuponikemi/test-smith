"""
SearXNG Search Provider

Queries a self-hosted SearXNG meta-search instance via
``langchain_community.utilities.SearxSearchWrapper``. The host URL is
read from the ``SEARXNG_URL`` environment variable (default
``http://localhost:8888``).

Ported from local-deepR (``ollama_deep_researcher.utils.searxng_search``)
as part of the workspace agent-layer consolidation (Phase 5).
"""

from __future__ import annotations

import os

from langchain_community.utilities import SearxSearchWrapper

from .base_provider import BaseSearchProvider, SearchResult


class SearxngProvider(BaseSearchProvider):
    """Provider backed by a SearXNG instance."""

    DEFAULT_HOST = "http://localhost:8888"

    def __init__(self, host: str | None = None):
        # No API key — health is governed by the host URL only.
        super().__init__(api_key=None)
        self.host = host or os.environ.get("SEARXNG_URL", self.DEFAULT_HOST)

    @property
    def name(self) -> str:
        return "searxng"

    @property
    def requires_api_key(self) -> bool:
        return False

    def is_configured(self) -> bool:
        # The instance is "configured" as long as we have a host URL.
        # Reachability is checked separately by health_check().
        return bool(self.host)

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            wrapper = SearxSearchWrapper(searx_host=self.host)
            raw_results = wrapper.results(query, num_results=max_results)
        except Exception as e:
            raise Exception(
                f"SearXNG search failed against {self.host}: {e}"
            ) from e

        results: list[SearchResult] = []
        for r in raw_results:
            url = r.get("link") or ""
            title = r.get("title") or ""
            snippet = r.get("snippet") or ""
            if not (url and title):
                continue
            results.append(
                SearchResult(title=title, url=url, content=snippet, score=None)
            )
        return results
