"""
Test configuration and fixtures for test-smith.

This module provides:
- Mock LLM implementations to avoid API calls
- Common test fixtures (state, models, etc.)
- Test environment configuration
- Assertion helpers
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import BaseModel

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


# ==================== Mock LLM Classes ====================


class MockLLMResponse:
    """Mock response from LLM with structured output support."""

    def __init__(self, content: str = "", structured_output: Optional[BaseModel] = None):
        self.content = content
        self.structured_output = structured_output


class MockChatModel:
    """
    Mock LLM for testing without API calls.

    Supports both text responses and structured outputs.
    """

    def __init__(
        self,
        response: str = "Mock LLM response",
        structured_response: Optional[BaseModel] = None,
        temperature: float = 0.7
    ):
        self.response = response
        self.structured_response = structured_response
        self.temperature = temperature
        self._call_count = 0
        self._call_history: List[Any] = []

    def invoke(self, messages: Any) -> MockLLMResponse:
        """Mock invoke method."""
        self._call_count += 1
        self._call_history.append(messages)

        if self.structured_response:
            return self.structured_response
        return MockLLMResponse(content=self.response)

    def with_structured_output(self, schema: type) -> "MockStructuredModel":
        """Mock structured output binding."""
        return MockStructuredModel(
            schema=schema,
            response=self.structured_response,
            parent=self
        )

    @property
    def call_count(self) -> int:
        """Number of times invoke was called."""
        return self._call_count

    @property
    def call_history(self) -> List[Any]:
        """History of all invoke calls."""
        return self._call_history


class MockStructuredModel:
    """Mock structured output model."""

    def __init__(self, schema: type, response: Optional[BaseModel] = None, parent: Optional[MockChatModel] = None):
        self.schema = schema
        self.response = response
        self.parent = parent

    def invoke(self, messages: Any) -> BaseModel:
        """Return the pre-configured structured response."""
        if self.parent:
            self.parent._call_count += 1
            self.parent._call_history.append(messages)

        if self.response:
            return self.response

        # Create a minimal valid instance of the schema
        return self._create_minimal_instance()

    def _create_minimal_instance(self) -> BaseModel:
        """Create a minimal valid instance of the schema for testing."""
        # Default values for common schemas
        if hasattr(self.schema, '__name__'):
            schema_name = self.schema.__name__

            if schema_name == 'StrategicPlan':
                from schemas import StrategicPlan
                return StrategicPlan(
                    rag_queries=["test rag query"],
                    web_queries=["test web query"],
                    strategy="Test strategy"
                )
            elif schema_name == 'Evaluation':
                from schemas import Evaluation
                return Evaluation(
                    is_sufficient=True,
                    reason="Test evaluation"
                )

        # Fallback: try to instantiate with empty values
        try:
            return self.schema()
        except Exception:
            # Last resort: return a mock
            return Mock(spec=self.schema)


# ==================== Fixtures: Environment ====================


@pytest.fixture(autouse=True)
def test_env():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ['MODEL_PROVIDER'] = 'ollama'  # Use mock, doesn't matter which
    os.environ['TAVILY_API_KEY'] = 'test-tavily-key'
    os.environ['LANGCHAIN_TRACING_V2'] = 'false'  # Disable tracing in tests

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ==================== Fixtures: Mock Models ====================


@pytest.fixture
def mock_llm():
    """Provide a basic mock LLM."""
    return MockChatModel(response="Test response from mock LLM")


@pytest.fixture
def mock_planner_model():
    """Mock planner model with StrategicPlan output."""
    from schemas import StrategicPlan

    response = StrategicPlan(
        rag_queries=["rag query 1", "rag query 2"],
        web_queries=["web query 1"],
        strategy="Mock strategic allocation: RAG for internal, web for external"
    )
    return MockChatModel(structured_response=response)


@pytest.fixture
def mock_evaluator_model():
    """Mock evaluator model with Evaluation output."""
    from schemas import Evaluation

    response = Evaluation(
        is_sufficient=True,
        reason="Mock evaluation: information is sufficient"
    )
    return MockChatModel(structured_response=response)


@pytest.fixture
def mock_analyzer_model():
    """Mock analyzer model."""
    return MockChatModel(
        response="Mock analysis: This is a synthesized summary of the search results."
    )


@pytest.fixture
def mock_synthesizer_model():
    """Mock synthesizer model."""
    return MockChatModel(
        response="# Mock Research Report\n\nThis is a comprehensive report on the query."
    )


# ==================== Fixtures: Test States ====================


@pytest.fixture
def basic_agent_state() -> Dict[str, Any]:
    """Provide a basic AgentState for testing."""
    return {
        "query": "What is test-driven development?",
        "web_queries": [],
        "rag_queries": [],
        "allocation_strategy": "",
        "search_results": [],
        "rag_results": [],
        "analyzed_data": [],
        "report": "",
        "evaluation": "",
        "loop_count": 0
    }


@pytest.fixture
def populated_agent_state(basic_agent_state) -> Dict[str, Any]:
    """Provide an AgentState with populated search results."""
    state = basic_agent_state.copy()
    state.update({
        "web_queries": ["modern TDD practices", "TDD tools 2024"],
        "rag_queries": ["test-driven development basics"],
        "search_results": [
            "Web search result 1: TDD is a software development process...",
            "Web search result 2: Modern TDD tools include pytest, jest..."
        ],
        "rag_results": [
            "KB result 1: Test-Driven Development (TDD) is a methodology..."
        ],
        "loop_count": 1
    })
    return state


@pytest.fixture
def hierarchical_state() -> Dict[str, Any]:
    """Provide a state for hierarchical research workflow testing."""
    return {
        "query": "What is LangGraph and how does it work?",
        "subtasks": [],
        "subtask_results": [],
        "current_subtask": None,
        "web_queries": [],
        "rag_queries": [],
        "search_results": [],
        "rag_results": [],
        "analyzed_data": [],
        "report": "",
        "loop_count": 0,
        "depth_evaluation": "",
        "drill_down_needed": False,
        "plan_revision": ""
    }


# ==================== Fixtures: Mock Data ====================


@pytest.fixture
def sample_search_results() -> List[str]:
    """Sample web search results for testing."""
    return [
        "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
        "LangGraph uses a graph structure where nodes are processing steps and edges define the flow.",
        "The library integrates with LangChain and supports cyclic workflows."
    ]


@pytest.fixture
def sample_rag_results() -> List[str]:
    """Sample RAG retrieval results for testing."""
    return [
        "Document chunk 1: LangGraph provides StateGraph for defining workflows...",
        "Document chunk 2: Nodes in LangGraph are Python functions that process state...",
        "Document chunk 3: Checkpointing allows persistence of conversation state..."
    ]


# ==================== Assertion Helpers ====================


def assert_valid_state(state: Dict[str, Any], required_keys: Optional[List[str]] = None):
    """
    Assert that a state dictionary has valid structure.

    Args:
        state: State dictionary to validate
        required_keys: Optional list of keys that must be present
    """
    assert isinstance(state, dict), "State must be a dictionary"

    if required_keys:
        for key in required_keys:
            assert key in state, f"State missing required key: {key}"


def assert_llm_called(mock_model: MockChatModel, min_calls: int = 1):
    """
    Assert that a mock LLM was called at least min_calls times.

    Args:
        mock_model: Mock model to check
        min_calls: Minimum number of expected calls
    """
    assert mock_model.call_count >= min_calls, \
        f"Expected at least {min_calls} LLM calls, got {mock_model.call_count}"


def assert_state_updated(state: Dict[str, Any], key: str, expected_type: type = None):
    """
    Assert that a state key was updated.

    Args:
        state: State dictionary
        key: Key to check
        expected_type: Optional expected type for the value
    """
    assert key in state, f"State missing key: {key}"

    value = state[key]
    if expected_type == list:
        assert isinstance(value, list), f"Expected {key} to be a list"
        assert len(value) > 0, f"Expected {key} to be non-empty"
    elif expected_type == str:
        assert isinstance(value, str), f"Expected {key} to be a string"
        assert len(value) > 0, f"Expected {key} to be non-empty"
    elif expected_type is not None:
        assert isinstance(value, expected_type), \
            f"Expected {key} to be {expected_type}, got {type(value)}"


# ==================== Pytest Configuration ====================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests (may make API calls)")
    config.addinivalue_line("markers", "requires_api: Tests requiring API keys")
