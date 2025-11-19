"""
Graph Registry and Discovery System

This module provides a central registry for all available graph workflows.
Graphs self-register when imported, making them automatically discoverable.

Usage:
    from src.graphs import get_graph, list_graphs

    # Get a specific graph
    builder = get_graph("deep_research")
    workflow = builder.build()

    # List all available graphs
    graphs = list_graphs()
    for name, metadata in graphs.items():
        print(f"{name}: {metadata['description']}")
"""

from typing import Dict, Optional
from .base_graph import BaseGraphBuilder, BaseAgentState, ExtendedAgentState

# Global registry of available graphs
_GRAPH_REGISTRY: Dict[str, BaseGraphBuilder] = {}


def register_graph(name: str, builder: BaseGraphBuilder):
    """
    Register a graph workflow in the global registry.

    Args:
        name: Unique identifier for this graph (e.g., "deep_research")
        builder: Instance of BaseGraphBuilder that creates this graph

    Raises:
        ValueError: If a graph with this name is already registered
    """
    if name in _GRAPH_REGISTRY:
        raise ValueError(f"Graph '{name}' is already registered")

    _GRAPH_REGISTRY[name] = builder
    print(f"[GraphRegistry] Registered graph: {name}")


def get_graph(name: str) -> BaseGraphBuilder:
    """
    Retrieve a graph builder by name.

    Args:
        name: Identifier of the graph to retrieve

    Returns:
        BaseGraphBuilder instance for the requested graph

    Raises:
        KeyError: If no graph with this name is registered
    """
    if name not in _GRAPH_REGISTRY:
        available = ", ".join(_GRAPH_REGISTRY.keys())
        raise KeyError(
            f"Graph '{name}' not found. Available graphs: {available}"
        )

    return _GRAPH_REGISTRY[name]


def list_graphs() -> Dict[str, dict]:
    """
    List all registered graphs with their metadata.

    Returns:
        Dictionary mapping graph names to their metadata

    Example:
        {
            "deep_research": {
                "name": "Deep Research",
                "description": "Hierarchical multi-agent research",
                "use_cases": ["complex queries", "multi-faceted topics"],
                ...
            },
            ...
        }
    """
    return {
        name: builder.get_metadata()
        for name, builder in _GRAPH_REGISTRY.items()
    }


def get_default_graph() -> str:
    """
    Get the name of the default graph to use.

    Returns:
        Name of the default graph (currently "deep_research")
    """
    return "deep_research"


# Import and register all available graphs
# This happens automatically when src.graphs is imported
def _auto_register_graphs():
    """
    Automatically import and register all graph modules.

    This function is called at module initialization to ensure
    all graphs are available in the registry.
    """
    try:
        from .deep_research_graph import DeepResearchGraphBuilder
        register_graph("deep_research", DeepResearchGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load deep_research graph: {e}")

    try:
        from .quick_research_graph import QuickResearchGraphBuilder
        register_graph("quick_research", QuickResearchGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load quick_research graph: {e}")

    try:
        from .fact_check_graph import FactCheckGraphBuilder
        register_graph("fact_check", FactCheckGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load fact_check graph: {e}")

    try:
        from .comparative_graph import ComparativeResearchGraphBuilder
        register_graph("comparative", ComparativeResearchGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load comparative graph: {e}")

    try:
        from .causal_inference_graph import CausalInferenceGraphBuilder
        register_graph("causal_inference", CausalInferenceGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load causal_inference graph: {e}")

    try:
        from .code_execution_graph import CodeExecutionGraphBuilder
        register_graph("code_execution", CodeExecutionGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load code_execution graph: {e}")


# Auto-register graphs on module import
_auto_register_graphs()


__all__ = [
    'BaseGraphBuilder',
    'BaseAgentState',
    'ExtendedAgentState',
    'register_graph',
    'get_graph',
    'list_graphs',
    'get_default_graph',
]
