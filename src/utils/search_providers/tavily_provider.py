"""
Tavily Search Provider

High-quality search API optimized for LLM applications.
Requires API key (free tier: 1000 searches/month)
"""

from typing import List
from langchain_community.tools import TavilySearchResults
from .base_provider import BaseSearchProvider, SearchResult


class TavilyProvider(BaseSearchProvider):
    """Tavily search provider implementation"""

    @property
    def name(self) -> str:
        return "tavily"

    @property
    def requires_api_key(self) -> bool:
        return True

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute search using Tavily API

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If API call fails
        """
        if not self.api_key:
            raise ValueError("Tavily API key is required")

        try:
            search = TavilySearchResults(max_results=max_results, api_key=self.api_key)
            raw_results = search.invoke({"query": query})

            # Convert to standardized format
            results = []
            for item in raw_results:
                # Handle both dict and string formats
                if isinstance(item, dict):
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            content=item.get("content", ""),
                            score=item.get("score"),
                        )
                    )
                elif isinstance(item, str):
                    # Fallback for string results
                    results.append(
                        SearchResult(
                            title="",
                            url="",
                            content=item,
                            score=None,
                        )
                    )

            return results

        except Exception as e:
            # Provide more specific error messages
            error_msg = str(e)
            if "432" in error_msg or "Client Error" in error_msg:
                raise Exception(
                    f"Tavily API error: API key may be invalid, expired, or out of credits. "
                    f"Visit https://tavily.com/ to check your account."
                ) from e
            raise
