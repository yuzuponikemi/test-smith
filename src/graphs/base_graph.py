"""
Base classes and utilities for building LangGraph workflows.

This module provides:
- BaseGraphBuilder: Abstract class for creating graph workflows
- BaseAgentState: Minimal state that all graphs must support
- Utilities for state management and graph composition
"""

import operator
from abc import ABC, abstractmethod
from typing import Annotated, Any, TypedDict

from langgraph.graph import StateGraph


class BaseAgentState(TypedDict):
    """
    Minimal state that all graph workflows must support.

    Individual graphs can extend this by adding their own fields.
    """

    query: str  # Original user query
    report: str  # Final output report


class BaseGraphBuilder(ABC):
    """
    Abstract base class for building LangGraph workflows.

    Subclasses must implement:
    - get_state_class(): Return the TypedDict class for this graph's state
    - build(): Construct and return the compiled workflow

    Optional overrides:
    - get_metadata(): Return metadata about this graph (name, description, etc.)
    """

    @abstractmethod
    def get_state_class(self) -> type:
        """
        Return the TypedDict class that defines this graph's state.

        Must inherit from or be compatible with BaseAgentState.

        Returns:
            TypedDict class defining state schema
        """
        pass

    @abstractmethod
    def build(self) -> StateGraph:
        """
        Build and return the compiled LangGraph workflow.

        Returns:
            Compiled StateGraph ready for execution
        """
        pass

    def get_metadata(self) -> dict[str, Any]:
        """
        Return metadata about this graph workflow.

        Override to provide human-readable information about your graph.

        Returns:
            Dictionary with metadata (name, description, use_cases, etc.)
        """
        return {
            "name": self.__class__.__name__,
            "description": "No description provided",
            "use_cases": [],
            "complexity": "medium",
            "supports_streaming": True,
        }

    def get_uncompiled_graph(self) -> StateGraph:
        """
        Return the uncompiled StateGraph for external compilation.

        Useful when you need to apply custom checkpointers or configuration
        before compilation. Default implementation returns the compiled graph,
        but subclasses can override to return the uncompiled version.

        Returns:
            StateGraph instance (may be compiled or uncompiled depending on implementation)
        """
        return self.build()


class ExtendedAgentState(BaseAgentState):
    """
    Extended state with common fields used across many graph workflows.

    This is a convenience class that includes frequently-used fields.
    Graphs can use this instead of BaseAgentState to avoid redefining common fields.
    """

    # Query processing
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str

    # Results accumulation (uses operator.add for automatic merging)
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]

    # Evaluation and control flow
    evaluation: str
    reason: str
    loop_count: int


def create_simple_state(additional_fields: dict[str, type] = None) -> type:
    """
    Utility function to create a custom state class by extending BaseAgentState.

    Args:
        additional_fields: Dictionary of field_name -> field_type to add

    Returns:
        New TypedDict class with base fields + additional fields

    Example:
        CustomState = create_simple_state({
            "custom_field": str,
            "counter": int,
        })
    """
    if additional_fields is None:
        additional_fields = {}

    # Create new TypedDict class dynamically
    return TypedDict(  # type: ignore[operator]
        "CustomAgentState", {**BaseAgentState.__annotations__, **additional_fields}
    )
