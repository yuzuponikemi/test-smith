"""
Unit tests for analyzer_node.

Tests the analyzer's data merging and summarization logic.
"""

from unittest.mock import Mock, patch

import pytest

from src.nodes.analyzer_node import analyzer_node
from tests.conftest import MockChatModel


class TestAnalyzerNode:
    """Test the analyzer node."""

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_merges_web_and_rag_results(self, mock_get_model, populated_agent_state):
        """Test analyzer merges both web and RAG results."""
        mock_response = Mock()
        mock_response.content = "Synthesized analysis combining web and RAG sources."

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Run analyzer
        result = analyzer_node(populated_agent_state)

        # Assertions
        assert 'analyzed_data' in result
        assert isinstance(result['analyzed_data'], list)
        assert len(result['analyzed_data']) == 1
        assert 'Synthesized analysis' in result['analyzed_data'][0]

        # Verify model was called
        assert mock_model.invoke.called

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_uses_allocation_strategy(self, mock_get_model, populated_agent_state):
        """Test that analyzer considers the allocation strategy."""
        mock_response = Mock()
        mock_response.content = "Analysis based on strategic allocation"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Add allocation strategy
        state = populated_agent_state.copy()
        state['allocation_strategy'] = "RAG for basics, web for current info"

        # Run analyzer
        analyzer_node(state)

        # Verify strategy was included in prompt
        call_args = mock_model.invoke.call_args[0][0]
        assert 'RAG for basics' in call_args

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_handles_empty_results(self, mock_get_model, basic_agent_state):
        """Test analyzer handles empty search results."""
        mock_response = Mock()
        mock_response.content = "No results to analyze."

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # State with empty results
        state = basic_agent_state.copy()
        state['search_results'] = []
        state['rag_results'] = []

        # Run analyzer
        result = analyzer_node(state)

        # Should still return structured output
        assert 'analyzed_data' in result
        assert isinstance(result['analyzed_data'], list)
        assert len(result['analyzed_data']) == 1

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_includes_web_queries_context(self, mock_get_model, populated_agent_state):
        """Test that analyzer includes web queries in prompt for context."""
        mock_response = Mock()
        mock_response.content = "Analysis"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Run analyzer
        analyzer_node(populated_agent_state)

        # Verify web queries included in prompt
        call_args = mock_model.invoke.call_args[0][0]
        for query in populated_agent_state['web_queries']:
            assert query in call_args

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_includes_rag_queries_context(self, mock_get_model, populated_agent_state):
        """Test that analyzer includes RAG queries in prompt for context."""
        mock_response = Mock()
        mock_response.content = "Analysis"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Run analyzer
        analyzer_node(populated_agent_state)

        # Verify RAG queries included in prompt
        call_args = mock_model.invoke.call_args[0][0]
        for query in populated_agent_state['rag_queries']:
            assert query in call_args

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_with_code_execution_results(self, mock_get_model, populated_agent_state):
        """Test analyzer includes code execution results when available."""
        mock_response = Mock()
        mock_response.content = "Analysis including code results"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Add code execution results
        state = populated_agent_state.copy()
        state['code_execution_results'] = [
            {
                'success': True,
                'output': 'Hello, World!',
                'execution_mode': 'safe',
                'code': 'print("Hello, World!")'
            }
        ]

        # Run analyzer
        analyzer_node(state)

        # Verify code results included in prompt
        call_args = mock_model.invoke.call_args[0][0]
        assert 'CODE EXECUTION RESULTS' in call_args
        assert 'Hello, World!' in call_args
        assert 'safe' in call_args

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_output_structure(self, mock_get_model, populated_agent_state):
        """Test that analyzer returns correctly structured output."""
        mock_response = Mock()
        mock_response.content = "Analyzed content"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        result = analyzer_node(populated_agent_state)

        # Verify structure
        assert isinstance(result, dict)
        assert 'analyzed_data' in result
        assert isinstance(result['analyzed_data'], list)
        assert all(isinstance(item, str) for item in result['analyzed_data'])

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_handles_multiple_code_results(self, mock_get_model, basic_agent_state):
        """Test analyzer formats multiple code execution results correctly."""
        mock_response = Mock()
        mock_response.content = "Analysis"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Add multiple code results
        state = basic_agent_state.copy()
        state['code_execution_results'] = [
            {'success': True, 'output': 'Result 1', 'execution_mode': 'safe'},
            {'success': False, 'output': 'Error', 'execution_mode': 'safe'}
        ]

        # Run analyzer
        analyzer_node(state)

        # Verify both results included
        call_args = mock_model.invoke.call_args[0][0]
        assert 'Result 1' in call_args
        assert 'Result 2' in call_args


@pytest.mark.unit
class TestAnalyzerEdgeCases:
    """Test edge cases for analyzer node."""

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_with_missing_optional_keys(self, mock_get_model, basic_agent_state):
        """Test analyzer handles missing optional keys gracefully."""
        mock_response = Mock()
        mock_response.content = "Basic analysis"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        # Remove optional keys
        state = {
            "query": "Test query"
        }

        # Should not crash
        result = analyzer_node(state)

        assert 'analyzed_data' in result

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_with_none_values(self, mock_get_model, basic_agent_state):
        """Test analyzer handles None values in state."""
        mock_response = Mock()
        mock_response.content = "Analysis"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        state = basic_agent_state.copy()
        state['search_results'] = None
        state['rag_results'] = None
        state['allocation_strategy'] = None

        # Should handle None gracefully
        result = analyzer_node(state)

        assert 'analyzed_data' in result

    @patch('src.nodes.analyzer_node.get_analyzer_model')
    def test_analyzer_preserves_original_query(self, mock_get_model, populated_agent_state):
        """Test that analyzer uses original query in analysis."""
        mock_response = Mock()
        mock_response.content = "Query-specific analysis"

        mock_model = MockChatModel()
        mock_model.invoke = Mock(return_value=mock_response)
        mock_get_model.return_value = mock_model

        original_query = populated_agent_state['query']

        analyzer_node(populated_agent_state)

        # Verify original query in prompt
        call_args = mock_model.invoke.call_args[0][0]
        assert original_query in call_args
