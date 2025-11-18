# Creating Custom Graph Workflows

Build your own specialized workflows for Test-Smith.

---

## Overview

Test-Smith's multi-graph architecture lets you create custom workflows by:
- Extending base classes
- Reusing existing nodes
- Defining custom state schemas
- Registering with the graph registry

---

## Quick Start

### 1. Create Graph File

Create `src/graphs/my_workflow_graph.py`:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
from .base_graph import BaseGraphBuilder

# Import reusable nodes
from src.nodes.planner_node import planner
from src.nodes.searcher_node import searcher
from src.nodes.synthesizer_node import synthesizer_node

# Define state
class MyWorkflowState(TypedDict):
    query: str
    report: str

# Create builder
class MyWorkflowGraphBuilder(BaseGraphBuilder):
    def get_state_class(self) -> type:
        return MyWorkflowState

    def build(self) -> StateGraph:
        workflow = StateGraph(MyWorkflowState)

        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("synthesizer", synthesizer_node)

        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("searcher", "synthesizer")
        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    def get_metadata(self) -> dict:
        return {
            "name": "My Workflow",
            "description": "Custom workflow for X",
            "version": "1.0"
        }
```

### 2. Register Graph

Edit `src/graphs/__init__.py`:

```python
def _auto_register_graphs():
    # ... existing registrations ...

    try:
        from .my_workflow_graph import MyWorkflowGraphBuilder
        register_graph("my_workflow", MyWorkflowGraphBuilder())
    except ImportError as e:
        print(f"Warning: Could not load my_workflow: {e}")
```

### 3. Use It

```bash
python main.py graphs
python main.py run "Query" --graph my_workflow
```

---

## Available Nodes

All nodes in `src/nodes/` are reusable:

### Core Nodes

- `planner` - Strategic query allocation
- `searcher` - Web search (Tavily)
- `rag_retriever` - KB retrieval (ChromaDB)
- `analyzer_node` - Result analysis
- `evaluator_node` - Sufficiency check
- `synthesizer_node` - Report generation

### Hierarchical Nodes

- `master_planner` - Task decomposition
- `depth_evaluator` - Depth assessment
- `drill_down_generator` - Recursive subtasks
- `plan_revisor` - Dynamic replanning

### Causal Inference Nodes

- `issue_analyzer`
- `brainstormer`
- `evidence_planner`
- `causal_checker`
- `hypothesis_validator`
- `causal_graph_builder`
- `root_cause_synthesizer`

---

## State Schemas

### Base States

```python
from src.graphs.base_graph import BaseAgentState, ExtendedAgentState

# Minimal
class MyState(BaseAgentState):
    # Inherits: query, report
    custom: str

# Extended
class MyState(ExtendedAgentState):
    # Inherits: query, report, web_queries, rag_queries,
    # search_results, rag_results, analyzed_data, etc.
    custom: str
```

### Cumulative Lists

Use `Annotated` for automatic list merging:

```python
from typing import Annotated
import operator

class MyState(TypedDict):
    results: Annotated[list[str], operator.add]
```

---

## Examples

### Minimal Graph

```python
workflow.add_node("planner", planner)
workflow.add_node("searcher", searcher)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "searcher")
workflow.add_edge("searcher", "synthesizer")
workflow.add_edge("synthesizer", END)
```

### With Conditional Routing

```python
def router(state):
    if state.get("evaluation") == "sufficient":
        return "synthesizer"
    return "planner"

workflow.add_conditional_edges(
    "evaluator",
    router,
    {"synthesizer": "synthesizer", "planner": "planner"}
)
```

### Parallel Execution

```python
# Both run after planner
workflow.add_edge("planner", "searcher")
workflow.add_edge("planner", "rag_retriever")

# Both feed analyzer
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("rag_retriever", "analyzer")
```

---

## Testing

### Manual

```bash
python main.py graphs --detailed
python main.py run "Test query" --graph my_workflow
```

### Programmatic

```python
from src.graphs import get_graph

builder = get_graph("my_workflow")
assert builder is not None

metadata = builder.get_metadata()
assert "name" in metadata

workflow = builder.build()
assert workflow is not None
```

---

## Best Practices

### 1. Reuse Nodes

Don't create new nodes if existing ones work.

### 2. Keep State Minimal

Only add fields you actually use.

### 3. Document Your Graph

Provide rich metadata:

```python
def get_metadata(self):
    return {
        "name": "My Workflow",
        "description": "Purpose and use cases",
        "version": "1.0",
        "use_cases": ["Use case 1", "Use case 2"],
        "complexity": "medium"
    }
```

### 4. Handle Edge Cases

Consider:
- Empty results from searcher/RAG
- Very short/long queries
- Malformed state data

### 5. Test End-to-End

Test with real queries, not just unit tests.

---

## Troubleshooting

### "Graph not found"

- Check registration in `_auto_register_graphs()`
- Verify no import errors
- Use exact registered name

### "AttributeError: no attribute"

- Check state schema matches node expectations
- Verify base class inheritance
- Check node compatibility

### "Graph doesn't compile"

- All edges properly connected?
- Entry point set?
- All paths lead to END?
- Typos in node names?

---

## Learning Resources

Study existing graphs:

1. **quick_research_graph.py** - Simple linear (start here)
2. **fact_check_graph.py** - Custom state fields
3. **comparative_graph.py** - Evaluation loops
4. **deep_research_graph.py** - Complex routing

---

## Migration from Old Code

### Old Way (deprecated)

```python
from src.graph import graph, workflow
```

### New Way

```python
from src.graphs import get_graph

builder = get_graph("deep_research")
graph = builder.get_uncompiled_graph()
workflow = builder.build()
```

Old code still works but shows deprecation warning.

---

## Related Documentation

- **[System Overview](../architecture/system-overview.md)** - Architecture
- **[Multi-Graph Workflows](../architecture/multi-graph-workflows.md)** - Available graphs
