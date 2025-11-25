"""Tests for graph compilation and basic functionality."""

import pytest

from src.graphs import get_default_graph, get_graph, list_graphs


def test_list_graphs() -> None:
    """Test that list_graphs returns available graphs."""
    graphs = list_graphs()
    assert isinstance(graphs, dict)
    assert len(graphs) > 0
    assert "deep_research" in graphs
    assert "quick_research" in graphs


def test_get_default_graph() -> None:
    """Test that get_default_graph returns a compiled graph."""
    graph = get_default_graph()
    assert graph is not None


def test_get_graph_deep_research() -> None:
    """Test that deep_research graph can be compiled."""
    graph = get_graph("deep_research")
    assert graph is not None


def test_get_graph_quick_research() -> None:
    """Test that quick_research graph can be compiled."""
    graph = get_graph("quick_research")
    assert graph is not None


def test_get_graph_invalid_name() -> None:
    """Test that invalid graph name raises KeyError."""
    with pytest.raises(KeyError):
        get_graph("nonexistent_graph")
