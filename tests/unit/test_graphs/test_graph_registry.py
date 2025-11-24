"""
Unit tests for graph registry system.

Tests graph discovery, registration, and retrieval.
"""

import pytest
from src.graphs import (
    register_graph,
    get_graph,
    list_graphs,
    get_default_graph,
    _GRAPH_REGISTRY
)
from src.graphs.base_graph import BaseGraphBuilder
from langgraph.graph import StateGraph


class TestGraphRegistry:
    """Test the graph registry system."""

    def test_list_graphs_returns_all_registered(self):
        """Test that list_graphs returns all registered graphs."""
        graphs = list_graphs()

        assert isinstance(graphs, dict)
        assert len(graphs) > 0

        # Check expected graphs are registered
        expected_graphs = [
            'deep_research',
            'quick_research',
            'fact_check',
            'comparative',
            'causal_inference',
            'code_investigation'
        ]

        for graph_name in expected_graphs:
            assert graph_name in graphs, f"Expected graph '{graph_name}' not found in registry"

    def test_list_graphs_includes_metadata(self):
        """Test that each graph includes metadata."""
        graphs = list_graphs()

        for name, metadata in graphs.items():
            assert isinstance(metadata, dict), f"Graph '{name}' metadata is not a dict"
            # Each graph should have at least a name field
            assert 'name' in metadata or 'description' in metadata, \
                f"Graph '{name}' missing metadata fields"

    def test_get_graph_returns_builder(self):
        """Test that get_graph returns a BaseGraphBuilder instance."""
        builder = get_graph('deep_research')

        assert isinstance(builder, BaseGraphBuilder)
        assert hasattr(builder, 'build')
        assert hasattr(builder, 'get_metadata')

    def test_get_graph_raises_on_unknown(self):
        """Test that get_graph raises KeyError for unknown graphs."""
        with pytest.raises(KeyError) as exc_info:
            get_graph('nonexistent_graph')

        assert 'not found' in str(exc_info.value).lower()
        assert 'available graphs' in str(exc_info.value).lower()

    def test_get_default_graph_returns_valid_name(self):
        """Test that get_default_graph returns a registered graph name."""
        default_name = get_default_graph()

        assert isinstance(default_name, str)
        assert default_name in list_graphs()
        assert default_name == 'deep_research'  # Current default

    def test_each_graph_can_be_compiled(self):
        """Test that each registered graph can be compiled."""
        graphs = list_graphs()

        for name in graphs.keys():
            builder = get_graph(name)
            compiled_graph = builder.build()

            assert compiled_graph is not None, f"Graph '{name}' compilation returned None"
            # Should be a compiled StateGraph
            assert hasattr(compiled_graph, 'invoke') or hasattr(compiled_graph, 'stream'), \
                f"Graph '{name}' missing invoke/stream methods"


@pytest.mark.unit
class TestGraphBuilders:
    """Test individual graph builders."""

    def test_deep_research_graph_structure(self):
        """Test deep_research graph has expected structure."""
        builder = get_graph('deep_research')
        metadata = builder.get_metadata()

        assert 'name' in metadata or 'description' in metadata
        # Should have complex, hierarchical workflow
        graph = builder.build()
        assert graph is not None

    def test_quick_research_graph_structure(self):
        """Test quick_research graph has expected structure."""
        builder = get_graph('quick_research')
        metadata = builder.get_metadata()

        assert 'name' in metadata or 'description' in metadata
        graph = builder.build()
        assert graph is not None

    def test_fact_check_graph_structure(self):
        """Test fact_check graph has expected structure."""
        builder = get_graph('fact_check')
        metadata = builder.get_metadata()

        assert 'name' in metadata or 'description' in metadata
        graph = builder.build()
        assert graph is not None

    def test_comparative_graph_structure(self):
        """Test comparative graph has expected structure."""
        builder = get_graph('comparative')
        metadata = builder.get_metadata()

        assert 'name' in metadata or 'description' in metadata
        graph = builder.build()
        assert graph is not None

    def test_causal_inference_graph_structure(self):
        """Test causal_inference graph has expected structure."""
        builder = get_graph('causal_inference')
        metadata = builder.get_metadata()

        assert 'name' in metadata or 'description' in metadata
        graph = builder.build()
        assert graph is not None

    def test_code_investigation_graph_structure(self):
        """Test code_investigation graph has expected structure."""
        builder = get_graph('code_investigation')
        metadata = builder.get_metadata()

        assert 'name' in metadata or 'description' in metadata
        graph = builder.build()
        assert graph is not None


@pytest.mark.unit
class TestGraphMetadata:
    """Test graph metadata consistency."""

    def test_all_graphs_have_consistent_metadata(self):
        """Test that all graphs provide consistent metadata structure."""
        graphs = list_graphs()

        for name, metadata in graphs.items():
            # Each graph should have metadata
            assert isinstance(metadata, dict), f"Graph '{name}' metadata not a dict"

            # Should have at least name or description
            assert any(key in metadata for key in ['name', 'description', 'use_cases']), \
                f"Graph '{name}' missing essential metadata fields"

    def test_metadata_contains_useful_information(self):
        """Test that metadata contains useful information."""
        graphs = list_graphs()

        for name, metadata in graphs.items():
            # Metadata should not be empty
            assert len(metadata) > 0, f"Graph '{name}' has empty metadata"

            # If description exists, should be non-empty string
            if 'description' in metadata:
                assert isinstance(metadata['description'], str)
                assert len(metadata['description']) > 10, \
                    f"Graph '{name}' description too short"


@pytest.mark.unit
class TestGraphStateClasses:
    """Test that graphs provide valid state classes."""

    def test_each_graph_has_state_class(self):
        """Test that each graph builder provides a state class."""
        graphs = list_graphs()

        for name in graphs.keys():
            builder = get_graph(name)

            # Should have get_state_class method
            assert hasattr(builder, 'get_state_class'), \
                f"Graph '{name}' builder missing get_state_class method"

            # Should return a class
            state_class = builder.get_state_class()
            assert state_class is not None, \
                f"Graph '{name}' get_state_class returned None"
