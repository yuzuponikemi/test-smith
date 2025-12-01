"""
Unit tests for planner_node.

Tests the strategic planner's query allocation logic between RAG and web sources.
"""

from unittest.mock import Mock, patch

import pytest

from src.nodes.planner_node import check_kb_contents, planner
from src.schemas import StrategicPlan
from tests.conftest import MockChatModel


class TestCheckKBContents:
    """Test the KB contents checking functionality."""

    @patch("os.path.exists")
    def test_kb_not_found(self, mock_exists):
        """Test when KB directory doesn't exist."""
        mock_exists.return_value = False

        result = check_kb_contents()

        assert result["available"] is False
        assert result["total_chunks"] == 0
        assert "not found" in result["summary"].lower()

    @patch("os.path.exists")
    @patch("src.nodes.planner_node.Chroma")
    @patch("src.nodes.planner_node.OllamaEmbeddings")
    def test_kb_empty(self, mock_embeddings, mock_chroma, mock_exists):
        """Test when KB exists but is empty."""
        mock_exists.return_value = True

        # Mock Chroma collection
        mock_collection = Mock()
        mock_collection.count.return_value = 0

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection
        mock_chroma.return_value = mock_vectorstore

        result = check_kb_contents()

        assert result["available"] is False
        assert result["total_chunks"] == 0
        assert "empty" in result["summary"].lower()

    @patch("os.path.exists")
    @patch("src.nodes.planner_node.Chroma")
    @patch("src.nodes.planner_node.OllamaEmbeddings")
    def test_kb_with_contents(self, mock_embeddings, mock_chroma, mock_exists):
        """Test when KB has documents."""
        mock_exists.return_value = True

        # Mock Chroma collection with documents
        mock_collection = Mock()
        mock_collection.count.return_value = 150
        mock_collection.peek.return_value = {
            "metadatas": [
                {"source": "/path/to/doc1.md"},
                {"source": "/path/to/doc2.pdf"},
                {"source": "/path/to/doc3.txt"},
            ]
        }

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection
        mock_chroma.return_value = mock_vectorstore

        result = check_kb_contents()

        assert result["available"] is True
        assert result["total_chunks"] == 150
        assert len(result["document_types"]) > 0
        assert "150 chunks" in result["summary"]

    @patch("os.path.exists")
    @patch("src.nodes.planner_node.Chroma")
    def test_kb_exception_handling(self, mock_chroma, mock_exists):
        """Test exception handling when KB access fails."""
        mock_exists.return_value = True
        mock_chroma.side_effect = Exception("Connection error")

        result = check_kb_contents()

        assert result["available"] is False
        assert "could not access" in result["summary"].lower()


class TestPlannerNode:
    """Test the strategic planner node."""

    @patch("src.nodes.planner_node.check_kb_contents")
    @patch("src.nodes.planner_node.get_planner_model")
    def test_planner_successful_allocation(self, mock_get_model, mock_check_kb, basic_agent_state):
        """Test successful query allocation."""
        # Mock KB availability
        mock_check_kb.return_value = {
            "available": True,
            "total_chunks": 100,
            "document_types": ["doc1.md", "doc2.pdf"],
            "summary": "KB contains 100 chunks",
        }

        # Mock model with structured output
        strategic_plan = StrategicPlan(
            rag_queries=["internal TDD documentation", "TDD best practices"],
            web_queries=["latest TDD tools 2024"],
            strategy="Use RAG for fundamentals, web for current tools",
        )

        mock_model = MockChatModel(structured_response=strategic_plan)
        mock_get_model.return_value = mock_model

        # Run planner
        result = planner(basic_agent_state)

        # Assertions
        assert "rag_queries" in result
        assert "web_queries" in result
        assert "allocation_strategy" in result
        assert len(result["rag_queries"]) == 2
        assert len(result["web_queries"]) == 1
        assert result["loop_count"] == 1

    @patch("src.nodes.planner_node.check_kb_contents")
    @patch("src.nodes.planner_node.get_planner_model")
    def test_planner_kb_unavailable(self, mock_get_model, mock_check_kb, basic_agent_state):
        """Test planner when KB is unavailable."""
        # Mock KB unavailability
        mock_check_kb.return_value = {
            "available": False,
            "total_chunks": 0,
            "document_types": [],
            "summary": "KB not available",
        }

        # Mock model
        strategic_plan = StrategicPlan(
            rag_queries=[],  # No RAG queries when KB unavailable
            web_queries=["test-driven development", "TDD practices"],
            strategy="KB unavailable, using web search only",
        )

        mock_model = MockChatModel(structured_response=strategic_plan)
        mock_get_model.return_value = mock_model

        # Run planner
        result = planner(basic_agent_state)

        # Assertions
        assert len(result["rag_queries"]) == 0
        assert len(result["web_queries"]) >= 1
        assert "allocation_strategy" in result

    @patch("src.nodes.planner_node.check_kb_contents")
    @patch("src.nodes.planner_node.get_planner_model")
    def test_planner_with_feedback(self, mock_get_model, mock_check_kb, basic_agent_state):
        """Test planner incorporating feedback from previous iteration."""
        # Add feedback to state
        state_with_feedback = basic_agent_state.copy()
        state_with_feedback["reason"] = "Need more information about TDD tools"
        state_with_feedback["loop_count"] = 1

        mock_check_kb.return_value = {
            "available": True,
            "total_chunks": 100,
            "summary": "KB available",
        }

        strategic_plan = StrategicPlan(
            rag_queries=[],
            web_queries=["TDD tools comparison", "popular TDD frameworks"],
            strategy="Based on feedback, focusing on tools",
        )

        mock_model = MockChatModel(structured_response=strategic_plan)
        mock_get_model.return_value = mock_model

        # Run planner
        result = planner(state_with_feedback)

        # Assertions
        assert result["loop_count"] == 2  # Incremented from 1
        assert len(result["web_queries"]) >= 1

    @patch("src.nodes.planner_node.check_kb_contents")
    @patch("src.nodes.planner_node.get_planner_model")
    def test_planner_fallback_on_error(self, mock_get_model, mock_check_kb, basic_agent_state):
        """Test planner fallback when structured output fails."""
        mock_check_kb.return_value = {
            "available": True,
            "total_chunks": 50,
            "summary": "KB available",
        }

        # Create a mock that raises exception on with_structured_output
        mock_model = Mock()
        mock_structured = Mock()
        mock_structured.invoke.side_effect = Exception("Structured output failed")
        mock_model.with_structured_output.return_value = mock_structured

        # But regular invoke returns JSON-like string
        mock_response = Mock()
        mock_response.content = """
        {
            "rag_queries": ["test query"],
            "web_queries": ["web test query"],
            "strategy": "Fallback strategy"
        }
        """
        mock_model.invoke.return_value = mock_response
        mock_get_model.return_value = mock_model

        # Run planner
        result = planner(basic_agent_state)

        # Assertions - should use fallback
        assert "rag_queries" in result
        assert "web_queries" in result
        assert isinstance(result["rag_queries"], list)
        assert isinstance(result["web_queries"], list)

    @patch("src.nodes.planner_node.check_kb_contents")
    @patch("src.nodes.planner_node.get_planner_model")
    def test_planner_increments_loop_count(self, mock_get_model, mock_check_kb, basic_agent_state):
        """Test that planner increments loop count."""
        mock_check_kb.return_value = {
            "available": True,
            "total_chunks": 100,
            "summary": "KB available",
        }

        strategic_plan = StrategicPlan(
            rag_queries=["query"], web_queries=["query"], strategy="Test"
        )

        mock_model = MockChatModel(structured_response=strategic_plan)
        mock_get_model.return_value = mock_model

        # Test with different starting loop counts
        for initial_count in [0, 1, 2]:
            state = basic_agent_state.copy()
            state["loop_count"] = initial_count

            result = planner(state)

            assert result["loop_count"] == initial_count + 1


@pytest.mark.unit
class TestPlannerNodeIntegration:
    """Integration-style tests for planner node with real prompt templates."""

    @patch("src.nodes.planner_node.check_kb_contents")
    @patch("src.nodes.planner_node.get_planner_model")
    def test_planner_uses_correct_prompt_variables(
        self, mock_get_model, mock_check_kb, basic_agent_state
    ):
        """Test that planner correctly formats prompt with all variables."""
        mock_check_kb.return_value = {
            "available": True,
            "total_chunks": 200,
            "summary": "Test KB summary",
        }

        strategic_plan = StrategicPlan(
            rag_queries=["query1"], web_queries=["query2"], strategy="test strategy"
        )

        # Create a mock that captures the invoke call
        mock_structured = Mock()
        mock_structured.invoke.return_value = strategic_plan

        mock_model = Mock()
        mock_model.with_structured_output.return_value = mock_structured
        mock_get_model.return_value = mock_model

        # Add feedback to state
        state = basic_agent_state.copy()
        state["reason"] = "Need more details"

        # Run planner
        planner(state)

        # Verify invoke was called with formatted prompt
        assert mock_structured.invoke.called
        prompt_arg = mock_structured.invoke.call_args[0][0]

        # Prompt should contain key information
        assert basic_agent_state["query"] in prompt_arg
        assert "Test KB summary" in prompt_arg
        assert "Need more details" in prompt_arg
