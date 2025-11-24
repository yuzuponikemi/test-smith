"""
Unit tests for evaluator_node.

Tests the evaluator's logic for assessing information sufficiency.
"""

import pytest
from unittest.mock import Mock, patch
from src.nodes.evaluator_node import evaluator_node
from src.schemas import Evaluation
from tests.conftest import MockChatModel, assert_state_updated


class TestEvaluatorNode:
    """Test the evaluator node."""

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_sufficient_information(self, mock_get_model, populated_agent_state):
        """Test evaluator when information is sufficient."""
        # Mock evaluation response
        evaluation = Evaluation(
            is_sufficient=True,
            reason="The analyzed data provides comprehensive coverage of TDD concepts and practices."
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        # Add analyzed data to state
        state = populated_agent_state.copy()
        state['analyzed_data'] = [
            "Analysis 1: TDD is a development methodology...",
            "Analysis 2: Modern TDD tools include pytest, jest..."
        ]

        # Run evaluator
        result = evaluator_node(state)

        # Assertions
        assert 'evaluation' in result
        assert 'reason' in result
        assert result['evaluation'] == 'sufficient'
        assert 'comprehensive' in result['reason'].lower()

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_insufficient_information(self, mock_get_model, populated_agent_state):
        """Test evaluator when information is insufficient."""
        # Mock evaluation response
        evaluation = Evaluation(
            is_sufficient=False,
            reason="Missing information about modern TDD tools and frameworks."
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        # Add limited analyzed data
        state = populated_agent_state.copy()
        state['analyzed_data'] = [
            "Basic TDD definition found..."
        ]
        state['loop_count'] = 1

        # Run evaluator
        result = evaluator_node(state)

        # Assertions
        assert result['evaluation'] == 'insufficient'
        assert 'missing' in result['reason'].lower()

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_uses_loop_count(self, mock_get_model, basic_agent_state):
        """Test that evaluator considers loop count in evaluation."""
        evaluation = Evaluation(
            is_sufficient=True,
            reason="Maximum iterations reached, using available information."
        )

        # Create mock that tracks invocations
        mock_structured = Mock()
        mock_structured.invoke.return_value = evaluation

        mock_model = Mock()
        mock_model.with_structured_output.return_value = mock_structured
        mock_get_model.return_value = mock_model

        # Test with different loop counts
        for count in [0, 1, 2]:
            state = basic_agent_state.copy()
            state['loop_count'] = count
            state['analyzed_data'] = ["Some analysis"]

            evaluator_node(state)

            # Verify loop count was included in prompt
            call_args = mock_structured.invoke.call_args[0][0]
            assert str(count) in call_args

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_considers_allocation_strategy(self, mock_get_model, populated_agent_state):
        """Test that evaluator considers the allocation strategy."""
        evaluation = Evaluation(
            is_sufficient=True,
            reason="Both RAG and web sources provided complementary information."
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        # Add allocation strategy
        state = populated_agent_state.copy()
        state['allocation_strategy'] = "RAG for fundamentals, web for current tools"
        state['analyzed_data'] = ["Comprehensive analysis"]

        # Run evaluator
        result = evaluator_node(state)

        # Should produce evaluation based on strategy
        assert 'evaluation' in result
        assert 'reason' in result

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_fallback_on_error(self, mock_get_model, basic_agent_state):
        """Test evaluator fallback when structured output fails."""
        # Mock structured output failure
        mock_structured = Mock()
        mock_structured.invoke.side_effect = Exception("Structured output failed")

        # But regular invoke works
        mock_response = Mock()
        mock_response.content = "Information appears sufficient for creating a basic report."

        mock_model = Mock()
        mock_model.with_structured_output.return_value = mock_structured
        mock_model.invoke.return_value = mock_response
        mock_get_model.return_value = mock_model

        state = basic_agent_state.copy()
        state['analyzed_data'] = ["Some data"]

        # Run evaluator
        result = evaluator_node(state)

        # Should use fallback
        assert 'evaluation' in result
        assert 'reason' in result
        assert result['reason'] == 'Fallback evaluation used'

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_with_empty_analyzed_data(self, mock_get_model, basic_agent_state):
        """Test evaluator behavior with no analyzed data."""
        evaluation = Evaluation(
            is_sufficient=False,
            reason="No analyzed data available to evaluate."
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        state = basic_agent_state.copy()
        state['analyzed_data'] = []

        # Run evaluator
        result = evaluator_node(state)

        # Should indicate insufficient
        assert result['evaluation'] == 'insufficient'

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_output_structure(self, mock_get_model, populated_agent_state):
        """Test that evaluator returns correctly structured output."""
        evaluation = Evaluation(
            is_sufficient=True,
            reason="Test reason"
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        state = populated_agent_state.copy()
        state['analyzed_data'] = ["Data"]

        result = evaluator_node(state)

        # Verify structure
        assert isinstance(result, dict)
        assert 'evaluation' in result
        assert 'reason' in result
        assert isinstance(result['evaluation'], str)
        assert isinstance(result['reason'], str)
        assert len(result['reason']) > 0


@pytest.mark.unit
class TestEvaluatorEdgeCases:
    """Test edge cases for evaluator node."""

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_truncates_long_reason_in_output(self, mock_get_model, basic_agent_state):
        """Test that evaluator handles very long reason strings."""
        # Create a very long reason
        long_reason = "A" * 500

        evaluation = Evaluation(
            is_sufficient=True,
            reason=long_reason
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        state = basic_agent_state.copy()
        state['analyzed_data'] = ["Data"]

        result = evaluator_node(state)

        # Full reason should still be in result
        assert len(result['reason']) == 500

    @patch('src.nodes.evaluator_node.get_evaluation_model')
    def test_evaluator_with_missing_state_keys(self, mock_get_model):
        """Test evaluator handles missing state keys gracefully."""
        evaluation = Evaluation(
            is_sufficient=False,
            reason="Minimal state provided"
        )

        mock_model = MockChatModel(structured_response=evaluation)
        mock_get_model.return_value = mock_model

        # Minimal state
        state = {
            "query": "Test query"
        }

        # Should not crash
        result = evaluator_node(state)

        assert 'evaluation' in result
        assert 'reason' in result
