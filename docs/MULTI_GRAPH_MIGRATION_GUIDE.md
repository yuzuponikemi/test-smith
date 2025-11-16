# Multi-Graph Architecture Migration Guide

## Overview

Test-Smith v2.1 introduces a **multi-graph architecture** that allows you to choose from multiple specialized workflows based on your research needs. This guide explains what changed, how to migrate existing code, and how to create new graph workflows.

## What Changed

### Before (v2.0 and earlier)
- Single hardcoded graph in `src/graph.py`
- All research used the same workflow (hierarchical deep research)
- Difficult to create alternative workflows

### After (v2.1)
- **Multiple graph workflows** in `src/graphs/` directory
- **Graph registry system** for discovering and selecting workflows
- **Reusable nodes and prompts** shared across all graphs
- **Easy to create custom workflows** by extending base classes

## For End Users

### Command Line Changes

**Old (still works for backward compatibility):**
```bash
python main.py run "Your query"
```

**New (with graph selection):**
```bash
# List available graphs
python main.py graphs

# Run with specific graph
python main.py run "Your query" --graph quick_research
python main.py run "Your query" --graph fact_check
python main.py run "Your query" --graph comparative
python main.py run "Your query" --graph deep_research  # same as old default
```

**Default behavior unchanged:** If you don't specify `--graph`, it defaults to `deep_research` (the hierarchical workflow you're already using).

## For Developers

### Import Changes

**Old Code (deprecated but still works):**
```python
from src.graph import graph, workflow, AgentState

# Get uncompiled graph
app = graph.compile(checkpointer=memory)
```

**New Code (recommended):**
```python
from src.graphs import get_graph, list_graphs

# Get a specific graph
builder = get_graph("deep_research")
graph = builder.get_uncompiled_graph()
app = graph.compile(checkpointer=memory)

# Or get compiled workflow directly
workflow = builder.build()

# List all available graphs
graphs = list_graphs()
```

### Deprecation Warnings

The old `src/graph.py` module will show a deprecation warning:
```
DeprecationWarning: Importing from src.graph is deprecated.
Please use 'from src.graphs import get_graph' instead.
```

This is just a warning - your code will still work. Update at your convenience.

## Creating a New Graph Workflow

### Step 1: Create Graph File

Create `src/graphs/my_workflow_graph.py`:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from .base_graph import BaseGraphBuilder

# Import reusable nodes
from src.nodes.planner_node import planner
from src.nodes.searcher_node import searcher
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.analyzer_node import analyzer_node
from src.nodes.synthesizer_node import synthesizer_node

# Define state schema
class MyWorkflowState(TypedDict):
    query: str
    report: str
    # Add any custom fields you need
    custom_field: str

# Create builder class
class MyWorkflowGraphBuilder(BaseGraphBuilder):
    def get_state_class(self) -> type:
        return MyWorkflowState

    def build(self) -> StateGraph:
        workflow = StateGraph(MyWorkflowState)

        # Register nodes (reuse existing ones!)
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Define workflow
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("analyzer", "synthesizer")
        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        # Same as build() but return uncompiled
        workflow = StateGraph(MyWorkflowState)
        # ... add nodes and edges ...
        return workflow  # Don't compile

    def get_metadata(self) -> dict:
        return {
            "name": "My Workflow",
            "description": "A custom workflow for X",
            "version": "1.0",
            "use_cases": [
                "Use case 1",
                "Use case 2"
            ],
            "complexity": "low",
            "supports_streaming": True,
        }
```

### Step 2: Register in Graph Registry

Edit `src/graphs/__init__.py` and add to `_auto_register_graphs()`:

```python
def _auto_register_graphs():
    # ... existing registrations ...

    try:
        from .my_workflow_graph import MyWorkflowGraphBuilder
        register_graph("my_workflow", MyWorkflowGraphBuilder())
    except ImportError as e:
        print(f"[GraphRegistry] Warning: Could not load my_workflow graph: {e}")
```

### Step 3: Use Your Graph

```bash
# List it
python main.py graphs

# Run it
python main.py run "Your query" --graph my_workflow
```

## Node Reusability

All nodes in `src/nodes/` are designed to be reusable across graphs. You can mix and match them:

**Available Nodes:**
- `planner` - Strategic query allocation (RAG vs Web)
- `searcher` - Web search via Tavily
- `rag_retriever` - Knowledge base retrieval via ChromaDB
- `analyzer_node` - Results analysis and summarization
- `evaluator_node` - Information sufficiency evaluation
- `synthesizer_node` - Final report generation
- `master_planner` - Hierarchical task decomposition
- `depth_evaluator` - Depth quality assessment
- `drill_down_generator` - Recursive subtask generation
- `plan_revisor` - Dynamic plan adaptation

**Example: Minimal Graph**
```python
# Just planner → searcher → synthesizer
workflow.add_node("planner", planner)
workflow.add_node("searcher", searcher)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "searcher")
workflow.add_edge("searcher", "synthesizer")
workflow.add_edge("synthesizer", END)
```

## State Management

Each graph defines its own state schema, but there are helpful base classes:

**BaseAgentState** - Minimal required fields:
```python
from src.graphs.base_graph import BaseAgentState

class MyState(BaseAgentState):
    # Inherits: query, report
    custom_field: str  # Add your own
```

**ExtendedAgentState** - Common fields included:
```python
from src.graphs.base_graph import ExtendedAgentState

class MyState(ExtendedAgentState):
    # Inherits: query, report, web_queries, rag_queries,
    # search_results, rag_results, analyzed_data, evaluation, etc.
    custom_field: str  # Add your own
```

## Examples to Learn From

1. **quick_research_graph.py** - Simple linear workflow (best starting point)
2. **fact_check_graph.py** - Shows custom state fields
3. **comparative_graph.py** - Shows evaluation loops
4. **deep_research_graph.py** - Complex hierarchical workflow with routing

## Testing Your Graph

### Manual Testing
```bash
# Test graph registration
python main.py graphs --detailed

# Test execution
python main.py run "test query" --graph your_graph_name
```

### Programmatic Testing
```python
from src.graphs import get_graph

# Verify registration
builder = get_graph("your_graph_name")
assert builder is not None

# Check metadata
metadata = builder.get_metadata()
assert "name" in metadata

# Build and verify
workflow = builder.build()
assert workflow is not None
```

## Best Practices

### 1. Reuse Nodes
Don't create new nodes if existing ones work. The power of this architecture is reusability.

### 2. Keep States Minimal
Only add fields to state that you actually use. Inherit from `BaseAgentState` for minimal graphs.

### 3. Document Your Graph
Provide rich metadata in `get_metadata()` so users understand when to use your graph.

### 4. Test End-to-End
Test your graph with real queries, not just unit tests. Research workflows have emergent behaviors.

### 5. Handle Edge Cases
Consider what happens with:
- Empty results from searcher/RAG
- Very short/long queries
- Malformed state data

## Troubleshooting

### "Graph 'xyz' not found"
- Check that your graph is registered in `_auto_register_graphs()`
- Verify no import errors (check console output when importing `src.graphs`)
- Make sure you're using the exact registered name

### "AttributeError: X has no attribute Y"
- Check your state schema matches what nodes expect
- Ensure you inherit from correct base state class
- Verify nodes you're using are compatible with your state

### "Graph doesn't compile"
- Check all edges are properly connected
- Ensure you have an entry point set
- Verify all paths lead to END
- Check for typos in node names

## Migration Checklist

- [ ] Update imports from `src.graph` to `src.graphs`
- [ ] Test existing workflows still work (they should!)
- [ ] Explore new graphs: `python main.py graphs --detailed`
- [ ] Try different graphs for different use cases
- [ ] Consider creating custom graphs for your specific needs
- [ ] Update any scripts/automation to use `--graph` flag
- [ ] Review new documentation in CLAUDE.md

## Questions?

- Check `src/graphs/quick_research_graph.py` for a simple example
- Review `src/graphs/base_graph.py` for base class documentation
- See CLAUDE.md for architecture overview
- Look at existing graphs for patterns and best practices

## Backward Compatibility

**The old way still works!**

All existing code will continue to function. The deprecation warning is just a heads-up to migrate when convenient. There's no rush, and no breaking changes.

```python
# This still works (with deprecation warning)
from src.graph import graph, workflow

# But this is better going forward
from src.graphs import get_graph
builder = get_graph("deep_research")
graph = builder.get_uncompiled_graph()
```
