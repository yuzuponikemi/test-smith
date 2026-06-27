"""
Perplexity Search Provider

Wraps the Perplexity AI ``sonar-pro`` chat-completion API. Unlike pure
search engines, Perplexity returns an LLM-synthesised answer plus a list
of citation URLs; we surface the answer as the first SearchResult and
each citation as subsequent results so that downstream rankers can see
all sources.

Ported from local-deepR (``ollama_deep_researcher.utils.perplexity_search``)
as part of the workspace agent-layer consolidation (Phase 5).
"""

from __future__ import annotations

import os

import requests

from .base_provider import BaseSearchProvider, SearchResult


class PerplexityProvider(BaseSearchProvider):
    """Perplexity sonar-pro provider."""

    DEFAULT_MODEL = "sonar-pro"
    ENDPOINT = "https://api.perplexity.ai/chat/completions"
    SYSTEM_MESSAGE = "Search the web and provide factual information with sources."

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = 30.0,
    ):
        super().__init__(api_key=api_key or os.environ.get("PERPLEXITY_API_KEY"))
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "perplexity"

    @property
    def requires_api_key(self) -> bool:
        return True

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.api_key:
            raise ValueError("Perplexity API key is required")

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_MESSAGE},
                {"role": "user", "content": query},
            ],
        }

        try:
            response = requests.post(
                self.ENDPOINT,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Perplexity request failed: {e}") from e

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected Perplexity response shape: {data!r}") from e

        citations: list[str] = data.get("citations") or ["https://perplexity.ai"]

        results: list[SearchResult] = [
            SearchResult(
                title=f"Perplexity synthesis (source 1)",
                url=citations[0],
                content=content,
                score=None,
            )
        ]
        for i, citation in enumerate(citations[1:max_results], start=2):
            results.append(
                SearchResult(
                    title=f"Perplexity citation (source {i})",
                    url=citation,
                    content="See source 1 for the synthesised answer.",
                    score=None,
                )
            )

        # Cap to max_results overall.
        return results[:max_results]
