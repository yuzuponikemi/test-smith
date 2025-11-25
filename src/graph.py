"""
LEGACY COMPATIBILITY MODULE

This module maintains backward compatibility with code that imports from src.graph.
New code should use the src.graphs module and graph registry system instead.

Example migration:
    OLD: from src.graph import graph, workflow
    NEW: from src.graphs import get_graph
         builder = get_graph("deep_research")
         graph = builder.get_uncompiled_graph()
         workflow = builder.build()
"""

import warnings

# Import from new graph system
from src.graphs import get_graph
from src.graphs.deep_research_graph import DeepResearchState

# Show deprecation warning
warnings.warn(
    "Importing from src.graph is deprecated. "
    "Please use 'from src.graphs import get_graph' instead. "
    "See src/graphs/__init__.py for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility: Export the deep_research graph as default
_builder = get_graph("deep_research")

# Export state class for compatibility
AgentState = DeepResearchState

# Export uncompiled graph (for main.py compatibility)
graph = _builder.get_uncompiled_graph()

# Export compiled workflow (for LangGraph Studio compatibility)
# Note: LangGraph Studio will provide its own checkpointer (PostgreSQL)
workflow = _builder.build()

# Save graph visualization
try:
    from pathlib import Path

    # Create visualizations directory if it doesn't exist
    viz_dir = Path(__file__).parent.parent / "visualizations"
    viz_dir.mkdir(exist_ok=True)

    # Save Mermaid diagram (text format that can be rendered)
    mermaid_path = viz_dir / "graph_structure.mmd"
    mermaid_diagram = workflow.get_graph().draw_mermaid()
    with open(mermaid_path, "w") as f:
        f.write(mermaid_diagram)
    print(f"Graph visualization saved to: {mermaid_path}")

    # Try to save PNG if dependencies are available
    try:
        png_data = workflow.get_graph().draw_mermaid_png()
        png_path = viz_dir / "graph_structure.png"
        with open(png_path, "wb") as f:
            f.write(png_data)
        print(f"Graph PNG saved to: {png_path}")
    except Exception as e:
        print(f"Note: PNG generation skipped (install pygraphviz for PNG support): {e}")

except Exception as e:
    print(f"Warning: Could not save graph visualization: {e}")
