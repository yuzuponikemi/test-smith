"""
Base Search Provider Interface

Defines the abstract interface that all search providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class SearchResult:
    """Standardized search result format"""

    def __init__(self, title: str, url: str, content: str, score: Optional[float] = None):
        self.title = title
        self.url = url
        self.content = content
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format compatible with existing code"""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
        }


class BaseSearchProvider(ABC):
    """Abstract base class for search providers"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._is_available: Optional[bool] = None  # Cache for availability status

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'tavily', 'duckduckgo')"""
        pass

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key"""
        pass

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """
        Execute search query

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If search fails
        """
        pass

    def health_check(self) -> bool:
        """
        Check if provider is available and working

        Returns:
            True if provider is healthy, False otherwise
        """
        if self._is_available is not None:
            return self._is_available

        try:
            # Perform a simple test search
            self.search("test", max_results=1)
            self._is_available = True
            return True
        except Exception as e:
            print(f"  [{self.name}] Health check failed: {e}")
            self._is_available = False
            return False

    def is_configured(self) -> bool:
        """
        Check if provider is properly configured

        Returns:
            True if provider has necessary configuration
        """
        if self.requires_api_key:
            return self.api_key is not None and len(self.api_key) > 0
        return True

    def reset_availability_cache(self):
        """Reset the cached availability status"""
        self._is_available = None
