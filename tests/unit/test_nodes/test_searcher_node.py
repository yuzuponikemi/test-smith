"""
Tests for Searcher Node - Web search execution with provider fallback

Coverage target: 100%
Testing strategy: Mock SearchProviderManager and test all code paths
"""

from typing import Any
from unittest.mock import MagicMock, patch

from src.nodes.searcher_node import searcher

# ============================================================================
# Test Searcher Node
# ============================================================================


class TestSearcherNode:
    """Test searcher node logic"""

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_no_web_queries_skips_search(self, mock_manager_class, mock_print_header):
        """Should skip search when no web_queries in state"""
        # Arrange
        state: dict[str, Any] = {"web_queries": []}

        # Act
        result = searcher(state)

        # Assert
        assert result == {"search_results": [], "web_sources": []}
        mock_print_header.assert_called_once_with("SEARCHER")
        mock_manager_class.assert_not_called()  # Should not initialize manager

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_missing_web_queries_key_skips_search(self, mock_manager_class, mock_print_header):
        """Should skip search when web_queries key is missing"""
        # Arrange
        state: dict[str, Any] = {}  # No web_queries key

        # Act
        result = searcher(state)

        # Assert
        assert result == {"search_results": [], "web_sources": []}
        mock_print_header.assert_called_once_with("SEARCHER")
        mock_manager_class.assert_not_called()

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_successful_single_search(self, mock_manager_class, mock_print_header):
        """Should execute successful search with single query"""
        # Arrange
        state: dict[str, Any] = {"web_queries": ["What is machine learning?"]}

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily", "duckduckgo"]
        mock_manager.search.return_value = [
            {"content": "ML is...", "url": "https://example.com/ml"},
            {"content": "Machine learning...", "url": "https://example.com/ml2"},
        ]
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        assert len(result["search_results"]) == 1
        assert result["search_results"][0] == [
            {"content": "ML is...", "url": "https://example.com/ml"},
            {"content": "Machine learning...", "url": "https://example.com/ml2"},
        ]

        mock_manager_class.assert_called_once()
        mock_manager.get_available_providers.assert_called_once()
        mock_manager.search.assert_called_once_with(
            "What is machine learning?", max_results=5, attempt_all=True
        )

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_successful_multiple_searches(self, mock_manager_class, mock_print_header):
        """Should execute multiple successful searches"""
        # Arrange
        state: dict[str, Any] = {
            "web_queries": [
                "Python programming",
                "JavaScript frameworks",
                "Docker containers",
            ]
        }

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily"]
        mock_manager.search.side_effect = [
            [{"content": "Python is...", "url": "https://example.com/python"}],
            [{"content": "JavaScript...", "url": "https://example.com/js"}],
            [{"content": "Docker is...", "url": "https://example.com/docker"}],
        ]
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        assert len(result["search_results"]) == 3
        assert result["search_results"][0] == [
            {"content": "Python is...", "url": "https://example.com/python"}
        ]
        assert result["search_results"][1] == [
            {"content": "JavaScript...", "url": "https://example.com/js"}
        ]
        assert result["search_results"][2] == [
            {"content": "Docker is...", "url": "https://example.com/docker"}
        ]

        assert mock_manager.search.call_count == 3

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_manager_initialization_failure(self, mock_manager_class, mock_print_header):
        """Should handle manager initialization failure gracefully"""
        # Arrange
        state: dict[str, Any] = {"web_queries": ["Test query"]}

        # Mock manager class to raise exception
        mock_manager_class.side_effect = Exception("Failed to initialize providers")

        # Act
        result = searcher(state)

        # Assert
        assert result == {"search_results": [], "web_sources": []}
        mock_manager_class.assert_called_once()

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_individual_search_failure(self, mock_manager_class, mock_print_header):
        """Should handle individual search failure gracefully"""
        # Arrange
        state: dict[str, Any] = {"web_queries": ["Query that will fail"]}

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily", "duckduckgo"]
        mock_manager.search.side_effect = Exception(
            "All search providers failed (tavily, duckduckgo). Last error: API rate limit"
        )
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        assert len(result["search_results"]) == 1
        error_info = result["search_results"][0]

        # Should return error info
        assert len(error_info) == 1
        assert "⚠️ Web search failed for query: Query that will fail" in error_info[0]["content"]
        assert "All search providers failed" in error_info[0]["content"]
        assert error_info[0]["url"] == ""

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_mixed_success_and_failure(self, mock_manager_class, mock_print_header):
        """Should handle mix of successful and failed searches"""
        # Arrange
        state: dict[str, Any] = {
            "web_queries": [
                "Successful query 1",
                "Failed query",
                "Successful query 2",
            ]
        }

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily"]
        mock_manager.search.side_effect = [
            [{"content": "Success 1", "url": "https://example.com/1"}],  # First succeeds
            Exception("Search failed"),  # Second fails
            [{"content": "Success 2", "url": "https://example.com/2"}],  # Third succeeds
        ]
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        assert len(result["search_results"]) == 3

        # First result: successful
        assert result["search_results"][0] == [
            {"content": "Success 1", "url": "https://example.com/1"}
        ]

        # Second result: error info
        error_info = result["search_results"][1]
        assert len(error_info) == 1
        assert "⚠️ Web search failed for query: Failed query" in error_info[0]["content"]
        assert error_info[0]["url"] == ""

        # Third result: successful
        assert result["search_results"][2] == [
            {"content": "Success 2", "url": "https://example.com/2"}
        ]

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_empty_search_results(self, mock_manager_class, mock_print_header):
        """Should handle empty search results (no results found)"""
        # Arrange
        state: dict[str, Any] = {"web_queries": ["Very obscure query"]}

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["duckduckgo"]
        mock_manager.search.return_value = []  # No results
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        assert len(result["search_results"]) == 1
        assert result["search_results"][0] == []  # Empty list is valid

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_search_with_max_results_parameter(self, mock_manager_class, mock_print_header):
        """Should pass max_results=5 parameter to search method"""
        # Arrange
        state: dict[str, Any] = {"web_queries": ["Test query"]}

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily"]
        mock_manager.search.return_value = [
            {"content": "Result 1", "url": "https://example.com/1"},
            {"content": "Result 2", "url": "https://example.com/2"},
            {"content": "Result 3", "url": "https://example.com/3"},
            {"content": "Result 4", "url": "https://example.com/4"},
            {"content": "Result 5", "url": "https://example.com/5"},
        ]
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        mock_manager.search.assert_called_once_with("Test query", max_results=5, attempt_all=True)
        assert len(result["search_results"][0]) == 5

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_search_with_attempt_all_parameter(self, mock_manager_class, mock_print_header):
        """Should pass attempt_all=True parameter to enable fallback"""
        # Arrange
        state: dict[str, Any] = {"web_queries": ["Test query"]}

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily", "duckduckgo"]
        mock_manager.search.return_value = [{"content": "Result", "url": "https://example.com"}]
        mock_manager_class.return_value = mock_manager

        # Act
        searcher(state)

        # Assert
        # Verify attempt_all=True is passed (enables automatic fallback)
        mock_manager.search.assert_called_once_with("Test query", max_results=5, attempt_all=True)

    @patch("src.nodes.searcher_node.print_node_header")
    @patch("src.nodes.searcher_node.SearchProviderManager")
    def test_search_results_ordering_preserved(self, mock_manager_class, mock_print_header):
        """Should preserve order of search results"""
        # Arrange
        state: dict[str, Any] = {
            "web_queries": [
                "Query A",
                "Query B",
                "Query C",
            ]
        }

        # Mock manager instance
        mock_manager = MagicMock()
        mock_manager.get_available_providers.return_value = ["tavily"]
        mock_manager.search.side_effect = [
            [{"content": "Result A", "url": "https://a.com"}],
            [{"content": "Result B", "url": "https://b.com"}],
            [{"content": "Result C", "url": "https://c.com"}],
        ]
        mock_manager_class.return_value = mock_manager

        # Act
        result = searcher(state)

        # Assert
        # Results should be in same order as queries
        assert result["search_results"][0][0]["content"] == "Result A"
        assert result["search_results"][1][0]["content"] == "Result B"
        assert result["search_results"][2][0]["content"] == "Result C"
