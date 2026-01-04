"""
Tests for Search Provider Manager - Multi-provider search with automatic fallback

Coverage target: High coverage on provider_manager.py
Testing strategy: Mock provider classes and test fallback logic
"""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.search_providers.base_provider import SearchResult
from src.utils.search_providers.provider_manager import SearchProviderManager

# ============================================================================
# Test Search Provider Manager
# ============================================================================


class TestSearchProviderManager:
    """Test search provider manager logic"""

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_initialization_default_priority(self, mock_ddg_class, mock_tavily_class):
        """Should initialize with default priority from environment"""
        # Act
        manager = SearchProviderManager()

        # Assert
        assert manager.priority == ["tavily", "duckduckgo"]
        assert "tavily" in manager.providers
        assert "duckduckgo" in manager.providers
        mock_tavily_class.assert_called_once_with(api_key=None)
        mock_ddg_class.assert_called_once()

    @patch.dict("os.environ", {"SEARCH_PROVIDER_PRIORITY": "duckduckgo,tavily"}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_initialization_env_priority(self, mock_ddg_class, mock_tavily_class):
        """Should initialize with priority from environment variable"""
        # Act
        manager = SearchProviderManager()

        # Assert
        assert manager.priority == ["duckduckgo", "tavily"]

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_initialization_custom_priority(self, mock_ddg_class, mock_tavily_class):
        """Should initialize with custom priority parameter"""
        # Act
        manager = SearchProviderManager(priority=["duckduckgo"])

        # Assert
        assert manager.priority == ["duckduckgo"]

    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_initialization_with_api_keys(self, mock_ddg_class, mock_tavily_class):
        """Should pass API keys to providers from environment"""
        # Act
        SearchProviderManager()

        # Assert
        mock_tavily_class.assert_called_once_with(api_key="test-key")

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_get_available_providers_all_configured(self, mock_ddg_class, mock_tavily_class):
        """Should return all configured providers"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        available = manager.get_available_providers()

        # Assert
        assert available == ["tavily", "duckduckgo"]

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_get_available_providers_some_not_configured(self, mock_ddg_class, mock_tavily_class):
        """Should filter out non-configured providers"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = False  # Not configured
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True  # Configured
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        available = manager.get_available_providers()

        # Assert
        assert available == ["duckduckgo"]  # Only DDG is configured

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_search_successful_first_provider(self, mock_ddg_class, mock_tavily_class):
        """Should return results from first successful provider"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        result1 = SearchResult(title="Result 1", url="https://example.com/1", content="Content 1")
        result2 = SearchResult(title="Result 2", url="https://example.com/2", content="Content 2")
        mock_tavily.search.return_value = [result1, result2]
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        results = manager.search("test query", max_results=5)

        # Assert
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[1]["title"] == "Result 2"
        mock_tavily.search.assert_called_once_with("test query", 5)
        mock_ddg.search.assert_not_called()  # Should not try second provider

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_search_fallback_to_second_provider(self, mock_ddg_class, mock_tavily_class):
        """Should fallback to second provider when first fails"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        mock_tavily.search.side_effect = Exception("Tavily API error")
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        result_ddg = SearchResult(
            title="DDG Result", url="https://ddg.com/1", content="DDG Content"
        )
        mock_ddg.search.return_value = [result_ddg]
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        results = manager.search("test query", max_results=5, attempt_all=True)

        # Assert
        assert len(results) == 1
        assert results[0]["title"] == "DDG Result"
        mock_tavily.search.assert_called_once()
        mock_ddg.search.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_search_all_providers_fail(self, mock_ddg_class, mock_tavily_class):
        """Should raise exception when all providers fail"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        mock_tavily.search.side_effect = Exception("Tavily error")
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg.search.side_effect = Exception("DDG error")
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            manager.search("test query", max_results=5, attempt_all=True)

        assert "All search providers failed" in str(exc_info.value)
        assert "tavily, duckduckgo" in str(exc_info.value)

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_search_no_providers_available(self, mock_ddg_class, mock_tavily_class):
        """Should raise exception when no providers are configured"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = False  # Not configured
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = False  # Not configured
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            manager.search("test query", max_results=5)

        assert "No search providers available" in str(exc_info.value)

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_search_attempt_all_false(self, mock_ddg_class, mock_tavily_class):
        """Should not attempt second provider when attempt_all=False"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        mock_tavily.search.side_effect = Exception("Tavily error")
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            manager.search("test query", max_results=5, attempt_all=False)

        assert "Tavily error" in str(exc_info.value)
        mock_tavily.search.assert_called_once()
        mock_ddg.search.assert_not_called()  # Should NOT attempt second provider

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_health_check_all(self, mock_ddg_class, mock_tavily_class):
        """Should check health of all providers"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        mock_tavily.health_check.return_value = True
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg.health_check.return_value = False  # Unhealthy
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        status = manager.health_check_all()

        # Assert
        assert status == {"tavily": True, "duckduckgo": False, "mcp": False}

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_health_check_not_configured_providers(self, mock_ddg_class, mock_tavily_class):
        """Should mark non-configured providers as unhealthy"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = False  # Not configured
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg.health_check.return_value = True
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        status = manager.health_check_all()

        # Assert
        assert status == {"tavily": False, "duckduckgo": True, "mcp": False}
        mock_tavily.health_check.assert_not_called()  # Should not check unconfigured provider

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_get_status_report(self, mock_ddg_class, mock_tavily_class):
        """Should generate human-readable status report"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = True
        mock_tavily.requires_api_key = True
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg.requires_api_key = False
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        report = manager.get_status_report()

        # Assert
        assert "Search Provider Status" in report
        assert "tavily: Configured and ready" in report
        assert "duckduckgo: Configured and ready" in report
        assert "Priority order: tavily → duckduckgo" in report

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.utils.search_providers.provider_manager.TavilyProvider")
    @patch("src.utils.search_providers.provider_manager.DuckDuckGoProvider")
    def test_get_status_report_not_configured(self, mock_ddg_class, mock_tavily_class):
        """Should show not configured status in report"""
        # Arrange
        mock_tavily = MagicMock()
        mock_tavily.is_configured.return_value = False
        mock_tavily.requires_api_key = True
        mock_tavily_class.return_value = mock_tavily

        mock_ddg = MagicMock()
        mock_ddg.is_configured.return_value = True
        mock_ddg_class.return_value = mock_ddg

        manager = SearchProviderManager()

        # Act
        report = manager.get_status_report()

        # Assert
        assert "Not configured" in report
        assert "missing API key" in report
