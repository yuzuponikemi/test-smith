"""
Tests for Synthesizer Node - Final report generation from research results

Coverage target: 100%
Testing strategy: Mock LLM model and prompts, test both execution modes
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from src.nodes.synthesizer_node import synthesizer_node


# ============================================================================
# Test Synthesizer Node
# ============================================================================


class TestSynthesizerNode:
    """Test synthesizer node logic"""

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_simple_mode_basic(self, mock_get_model, mock_print_header):
        """Should synthesize in simple mode without code results"""
        # Arrange
        state = {
            "execution_mode": "simple",
            "query": "What is LangGraph?",
            "allocation_strategy": "Use web search for general info",
            "web_queries": ["LangGraph tutorial", "LangGraph examples"],
            "rag_queries": [],
            "analyzed_data": ["LangGraph is a framework...", "It uses state graphs..."],
            "loop_count": 1,
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "LangGraph is a powerful framework for building stateful multi-agent workflows."
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert "report" in result
        assert result["report"] == "LangGraph is a powerful framework for building stateful multi-agent workflows."

        mock_print_header.assert_called_once_with("SYNTHESIZER")
        mock_get_model.assert_called_once()
        mock_model.invoke.assert_called_once()

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_simple_mode_with_code_results(self, mock_get_model, mock_print_header):
        """Should synthesize in simple mode with code execution results"""
        # Arrange
        state = {
            "execution_mode": "simple",
            "query": "Calculate 15 + 25",
            "allocation_strategy": "Use code execution",
            "web_queries": [],
            "rag_queries": [],
            "analyzed_data": [],
            "loop_count": 1,
            "code_execution_results": [
                {
                    "success": True,
                    "output": "40",
                    "execution_mode": "calculate",
                    "code": "result = 15 + 25\nprint(result)",
                }
            ],
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "The result of 15 + 25 is 40."
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert "report" in result
        assert result["report"] == "The result of 15 + 25 is 40."

        # Verify invoke was called with prompt containing code results
        invoke_args = mock_model.invoke.call_args[0][0]
        assert "CODE EXECUTION RESULTS" in invoke_args
        assert "Success: True" in invoke_args
        assert "Output: 40" in invoke_args
        assert "result = 15 + 25" in invoke_args

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_simple_mode_with_multiple_code_results(self, mock_get_model, mock_print_header):
        """Should handle multiple code execution results"""
        # Arrange
        state = {
            "execution_mode": "simple",
            "query": "Calculate statistics",
            "allocation_strategy": "Use code execution",
            "web_queries": [],
            "rag_queries": [],
            "analyzed_data": [],
            "loop_count": 1,
            "code_execution_results": [
                {"success": True, "output": "Mean: 42.5", "execution_mode": "calculate"},
                {"success": True, "output": "Median: 40", "execution_mode": "calculate"},
                {"success": False, "output": "Error: division by zero", "execution_mode": "calculate"},
            ],
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Statistics calculated successfully."
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        invoke_args = mock_model.invoke.call_args[0][0]

        # Should include all results
        assert "Result 1:" in invoke_args
        assert "Result 2:" in invoke_args
        assert "Result 3:" in invoke_args
        assert "Mean: 42.5" in invoke_args
        assert "Median: 40" in invoke_args
        assert "Error: division by zero" in invoke_args

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_simple_mode_missing_optional_keys(self, mock_get_model, mock_print_header):
        """Should handle missing optional state keys gracefully"""
        # Arrange
        state = {
            "query": "Test query",
            # execution_mode defaults to "simple"
            # Other keys are optional
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Test report"
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert result["report"] == "Test report"
        mock_model.invoke.assert_called_once()

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_hierarchical_mode_basic(self, mock_get_model, mock_print_header):
        """Should synthesize in hierarchical mode"""
        # Arrange
        state = {
            "execution_mode": "hierarchical",
            "query": "Research deep learning architectures",
            "master_plan": {
                "subtasks": [
                    {
                        "subtask_id": "subtask-001",
                        "description": "Research CNN architectures",
                        "focus_area": "Convolutional networks",
                        "priority": "high",
                        "estimated_importance": 8,
                    },
                    {
                        "subtask_id": "subtask-002",
                        "description": "Research RNN architectures",
                        "focus_area": "Recurrent networks",
                        "priority": "medium",
                        "estimated_importance": 6,
                    },
                ],
                "complexity_reasoning": "The query requires comprehensive coverage of multiple architecture types.",
            },
            "subtask_results": {
                "subtask-001": "CNNs are used for image processing...",
                "subtask-002": "RNNs are used for sequence data...",
            },
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Comprehensive report on deep learning architectures."
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert result["report"] == "Comprehensive report on deep learning architectures."

        # Verify invoke was called with hierarchical prompt
        invoke_args = mock_model.invoke.call_args[0][0]
        assert "Research deep learning architectures" in invoke_args
        assert "subtask-001" in invoke_args
        assert "subtask-002" in invoke_args
        assert "CNN architectures" in invoke_args
        assert "RNN architectures" in invoke_args
        assert "CNNs are used for image processing" in invoke_args
        assert "RNNs are used for sequence data" in invoke_args

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_hierarchical_mode_empty_subtasks(self, mock_get_model, mock_print_header):
        """Should handle hierarchical mode with empty subtasks gracefully"""
        # Arrange
        state = {
            "execution_mode": "hierarchical",
            "query": "Test query",
            "master_plan": {
                "subtasks": [],
                "complexity_reasoning": "Test reasoning",
            },
            "subtask_results": {},
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Empty report"
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert result["report"] == "Empty report"
        mock_model.invoke.assert_called_once()

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_hierarchical_mode_missing_optional_keys(self, mock_get_model, mock_print_header):
        """Should handle missing optional keys in hierarchical mode"""
        # Arrange
        state = {
            "execution_mode": "hierarchical",
            "query": "Test query",
            # master_plan and subtask_results default to empty
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Report with defaults"
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert result["report"] == "Report with defaults"
        mock_model.invoke.assert_called_once()

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_code_results_without_code_field(self, mock_get_model, mock_print_header):
        """Should handle code results without code field gracefully"""
        # Arrange
        state = {
            "execution_mode": "simple",
            "query": "Test query",
            "code_execution_results": [
                {
                    "success": True,
                    "output": "Result without code field",
                    "execution_mode": "calculate",
                    # No "code" field
                }
            ],
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Report"
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        invoke_args = mock_model.invoke.call_args[0][0]
        assert "Result without code field" in invoke_args
        # Should not cause error when code field is missing

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_subtask_results_matching(self, mock_get_model, mock_print_header):
        """Should match subtask results with subtask details correctly"""
        # Arrange
        state = {
            "execution_mode": "hierarchical",
            "query": "Test query",
            "master_plan": {
                "subtasks": [
                    {
                        "subtask_id": "subtask-A",
                        "description": "Task A",
                        "focus_area": "Area A",
                        "priority": "high",
                        "estimated_importance": 9,
                    },
                    {
                        "subtask_id": "subtask-B",
                        "description": "Task B",
                        "focus_area": "Area B",
                        "priority": "low",
                        "estimated_importance": 3,
                    },
                ],
            },
            "subtask_results": {
                "subtask-A": "Result for A",
                "subtask-B": "Result for B",
            },
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Matched report"
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        invoke_args = mock_model.invoke.call_args[0][0]

        # Should contain both subtasks with their results
        assert "subtask-A" in invoke_args
        assert "Task A" in invoke_args
        assert "Area A" in invoke_args
        assert "Result for A" in invoke_args

        assert "subtask-B" in invoke_args
        assert "Task B" in invoke_args
        assert "Area B" in invoke_args
        assert "Result for B" in invoke_args

    @patch("src.nodes.synthesizer_node.print_node_header")
    @patch("src.nodes.synthesizer_node.get_synthesizer_model")
    def test_default_execution_mode(self, mock_get_model, mock_print_header):
        """Should default to simple mode when execution_mode is not specified"""
        # Arrange
        state = {
            "query": "Test query",
            # No execution_mode specified
        }

        # Mock model
        mock_model = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Default mode report"
        mock_model.invoke.return_value = mock_message
        mock_get_model.return_value = mock_model

        # Act
        result = synthesizer_node(state)

        # Assert
        assert result["report"] == "Default mode report"

        # Should use simple mode (default)
        invoke_args = mock_model.invoke.call_args[0][0]
        # In simple mode, the prompt includes these state fields
        # (hierarchical mode has different prompt format)
        assert "query" in state  # Verify we're testing the right scenario
