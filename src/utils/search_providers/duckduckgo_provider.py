"""
DuckDuckGo Search Provider

Free search provider with no API key required.
Uses DuckDuckGo's instant answer API.
"""

from typing import List
from langchain_community.tools import DuckDuckGoSearchResults
from .base_provider import BaseSearchProvider, SearchResult


class DuckDuckGoProvider(BaseSearchProvider):
    """DuckDuckGo search provider implementation"""

    @property
    def name(self) -> str:
        return "duckduckgo"

    @property
    def requires_api_key(self) -> bool:
        return False

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute search using DuckDuckGo

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If search fails
        """
        try:
            search = DuckDuckGoSearchResults(max_results=max_results)
            raw_results = search.invoke({"query": query})

            # Convert to standardized format
            results = []
            for item in raw_results:
                # Handle both dict and string formats
                if isinstance(item, dict):
                    results.append(
                        SearchResult(
                            title=item.get("title", item.get("snippet", "")[:50] if item.get("snippet") else ""),
                            url=item.get("link", item.get("url", "")),
                            content=item.get("snippet", item.get("content", "")),
                        )
                    )
                elif isinstance(item, str):
                    # Fallback for string results
                    results.append(
                        SearchResult(
                            title="",
                            url="",
                            content=item,
                        )
                    )

            return results

        except Exception as e:
            raise Exception(f"DuckDuckGo search failed: {str(e)}") from e
