"""
Tests for Graph Selector - LLM-based automatic graph selection

Coverage target: 80%+
Testing strategy: Mock LLM calls to test selection logic
"""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.graph_selector import (
    GraphSelection,
    GraphType,
    auto_select_graph,
    explain_selection,
    select_graph_with_llm,
)

# ============================================================================
# Test GraphSelection Pydantic Model
# ============================================================================


class TestGraphSelectionModel:
    """Test the GraphSelection Pydantic model"""

    def test_valid_graph_selection(self):
        """Should create valid GraphSelection with valid graph type"""
        selection = GraphSelection(
            selected_graph="deep_research",
            reasoning="Complex query requires hierarchical research",
        )
        assert selection.selected_graph == "deep_research"
        assert "Complex" in selection.reasoning

    def test_all_graph_types(self):
        """Should accept all valid graph types"""
        valid_types: list[GraphType] = [
            "code_execution",
            "causal_inference",
            "comparative",
            "fact_check",
            "quick_research",
            "deep_research",
        ]
        for graph_type in valid_types:
            selection = GraphSelection(
                selected_graph=graph_type,
                reasoning=f"Test for {graph_type}",
            )
            assert selection.selected_graph == graph_type

    def test_invalid_graph_type(self):
        """Should reject invalid graph types"""
        with pytest.raises(ValueError):
            GraphSelection(
                selected_graph="invalid_graph",  # type: ignore
                reasoning="This should fail",
            )


# ============================================================================
# Test select_graph_with_llm()
# ============================================================================


class TestSelectGraphWithLLM:
    """Test LLM-based graph selection"""

    @patch("src.utils.graph_selector.ChatPromptTemplate")
    @patch("src.utils.graph_selector.get_graph_selector_model")
    def test_successful_selection(self, mock_get_model: MagicMock, mock_prompt_class: MagicMock):
        """Should return selection from LLM"""
        # Setup mock chain that returns GraphSelection
        mock_selection = GraphSelection(
            selected_graph="code_execution",
            reasoning="Query requires calculation",
        )
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_selection

        # Mock prompt template to return our mock chain when | is used
        mock_prompt = MagicMock()
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_messages.return_value = mock_prompt

        # Mock model
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_get_model.return_value = mock_llm

        # Execute
        result = select_graph_with_llm("Calculate the average")

        # Verify
        assert result["selected_graph"] == "code_execution"
        assert "calculation" in result["reasoning"]

    @patch("src.utils.graph_selector.ChatPromptTemplate")
    @patch("src.utils.graph_selector.get_graph_selector_model")
    def test_fallback_on_llm_failure(self, mock_get_model: MagicMock, mock_prompt_class: MagicMock):
        """Should fallback to deep_research on LLM failure"""
        # Setup mock chain that raises exception
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("LLM error")

        # Mock prompt template
        mock_prompt = MagicMock()
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_messages.return_value = mock_prompt

        # Mock model
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_get_model.return_value = mock_llm

        # Execute
        result = select_graph_with_llm("Any query")

        # Verify fallback
        assert result["selected_graph"] == "deep_research"
        assert "failed" in result["reasoning"].lower()


# ============================================================================
# Test auto_select_graph()
# ============================================================================


class TestAutoSelectGraph:
    """Test automatic graph selection wrapper"""

    @patch("src.utils.graph_selector.select_graph_with_llm")
    def test_returns_llm_selection(self, mock_select: MagicMock):
        """Should return graph from LLM selection"""
        mock_select.return_value = {
            "selected_graph": "comparative",
            "reasoning": "Comparison detected",
        }

        result = auto_select_graph("Compare React vs Vue")

        assert result == "comparative"
        mock_select.assert_called_once_with("Compare React vs Vue")

    @patch("src.utils.graph_selector.select_graph_with_llm")
    def test_uses_default_on_exception(self, mock_select: MagicMock):
        """Should use default when LLM fails"""
        mock_select.side_effect = Exception("Network error")

        result = auto_select_graph("Any query", default="quick_research")

        assert result == "quick_research"

    @patch("src.utils.graph_selector.select_graph_with_llm")
    def test_default_is_deep_research(self, mock_select: MagicMock):
        """Default should be deep_research"""
        mock_select.side_effect = Exception("Error")

        result = auto_select_graph("Any query")

        assert result == "deep_research"


# ============================================================================
# Test explain_selection()
# ============================================================================


class TestExplainSelection:
    """Test selection explanation generation"""

    @patch("src.utils.graph_selector.select_graph_with_llm")
    def test_returns_llm_reasoning(self, mock_select: MagicMock):
        """Should return reasoning from LLM"""
        mock_select.return_value = {
            "selected_graph": "causal_inference",
            "reasoning": "Query asks why something happened",
        }

        explanation = explain_selection("Why is the server slow?", "causal_inference")

        assert "causal_inference" in explanation
        assert "why" in explanation.lower()

    @patch("src.utils.graph_selector.select_graph_with_llm")
    def test_fallback_explanation_on_mismatch(self, mock_select: MagicMock):
        """Should return generic explanation if graph doesn't match"""
        mock_select.return_value = {
            "selected_graph": "deep_research",
            "reasoning": "Complex query",
        }

        explanation = explain_selection("Query", "quick_research")

        assert "quick_research" in explanation
        assert "intent analysis" in explanation.lower()

    @patch("src.utils.graph_selector.select_graph_with_llm")
    def test_fallback_explanation_on_error(self, mock_select: MagicMock):
        """Should return generic explanation on error"""
        mock_select.side_effect = Exception("Error")

        explanation = explain_selection("Query", "fact_check")

        assert "fact_check" in explanation
        assert "intent analysis" in explanation.lower()


# ============================================================================
# Test GraphType Literal
# ============================================================================


class TestGraphType:
    """Test GraphType type definition"""

    def test_graph_type_values(self):
        """Verify all expected graph types are defined"""
        expected_types = {
            "code_execution",
            "causal_inference",
            "comparative",
            "fact_check",
            "quick_research",
            "deep_research",
        }

        # GraphType is a Literal, we can check it via GraphSelection validation
        for graph_type in expected_types:
            selection = GraphSelection(
                selected_graph=graph_type,  # type: ignore
                reasoning="Test",
            )
            assert selection.selected_graph == graph_type
