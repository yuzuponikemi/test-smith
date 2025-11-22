"""
LangGraph Studio Entry Points

This module provides compiled graph instances for LangGraph Studio.
Each graph is instantiated and compiled for Studio visualization.

Uses the existing graph registry to ensure consistency.
"""

from src.graphs import get_graph

# Get all graphs from registry and compile them
# This ensures we use the same graphs that main.py uses

def _compile_graph(graph_name: str):
    """Helper to compile a graph by name"""
    try:
        builder = get_graph(graph_name)
        return builder.build()
    except Exception as e:
        print(f"Warning: Could not compile {graph_name}: {e}")
        return None

# Compile each registered graph
deep_research = _compile_graph("deep_research")
code_execution = _compile_graph("code_execution")
quick_research = _compile_graph("quick_research")
comparative = _compile_graph("comparative")
fact_check = _compile_graph("fact_check")
causal_inference = _compile_graph("causal_inference")

# For Code Investigation (if exists)
try:
    code_investigation = _compile_graph("code_investigation")
except:
    code_investigation = None
