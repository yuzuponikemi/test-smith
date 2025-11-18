# System Overview

**Test-Smith v2.2** - LangGraph Multi-Agent Research System

---

## Architecture Summary

Test-Smith is a **hierarchical multi-agent research system** that orchestrates specialized agents to autonomously conduct research and generate comprehensive reports.

### Key Characteristics

- **Multi-Graph Architecture**: 5 specialized workflows for different research needs
- **Hierarchical Task Decomposition**: Complex queries broken into manageable subtasks
- **Dynamic Replanning**: Adapts research plan based on discoveries
- **Strategic Query Allocation**: Routes queries to optimal source (RAG vs Web)
- **Cumulative Learning**: Results accumulate across iterations

---

## Core Components

### 1. Workflow Orchestration (`src/graphs/`)

Multiple graph workflows, each tailored for specific use cases:

| Graph | Purpose | Nodes |
|-------|---------|-------|
| `deep_research` | Complex multi-faceted research | 12 nodes |
| `quick_research` | Fast single-pass lookup | 6 nodes |
| `fact_check` | Claim verification | 7 nodes |
| `comparative` | Side-by-side analysis | 8 nodes |
| `causal_inference` | Root cause analysis | 9 nodes |

### 2. Processing Nodes (`src/nodes/`)

Reusable node functions shared across graphs:

**Core Nodes:**
- `planner` - Strategic query allocation
- `searcher` - Web search (Tavily)
- `rag_retriever` - Knowledge base retrieval (ChromaDB)
- `analyzer` - Result synthesis
- `evaluator` - Sufficiency assessment
- `synthesizer` - Report generation

**Hierarchical Nodes:**
- `master_planner` - Task decomposition
- `depth_evaluator` - Depth quality assessment
- `drill_down_generator` - Recursive subtask creation
- `plan_revisor` - Dynamic plan adaptation

**Causal Inference Nodes:**
- `issue_analyzer`, `brainstormer`, `evidence_planner`
- `causal_checker`, `hypothesis_validator`, `causal_graph_builder`
- `root_cause_synthesizer`

### 3. LLM Configuration (`src/models.py`)

Centralized model management with provider abstraction:

```python
# Each task has a dedicated model function
get_planner_model()      # llama3 or gemini-pro
get_evaluation_model()   # command-r or gemini-pro
get_synthesizer_model()  # command-r or gemini-pro
```

### 4. Prompt Templates (`src/prompts/`)

LangChain PromptTemplates with variable injection for each node.

### 5. Knowledge Base (`src/preprocessor/`, `chroma_db/`)

RAG system with intelligent preprocessing and ChromaDB vector storage.

---

## State Management

### Agent State Schema

```python
class AgentState(TypedDict):
    # Core fields
    query: str
    report: str

    # Query allocation
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str

    # Results (cumulative)
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]

    # Evaluation
    evaluation: str
    reason: str
    loop_count: int

    # Hierarchical mode
    execution_mode: str  # "simple" or "hierarchical"
    master_plan: dict
    current_subtask_id: str
    current_subtask_index: int
    subtask_results: dict

    # Dynamic replanning
    revision_count: int
    plan_revisions: list
    max_revisions: int
    max_total_subtasks: int
```

### State Persistence

- **Technology**: SQLite checkpointing (`langgraph-checkpoint-sqlite`)
- **Purpose**: Conversation continuity, crash recovery, debugging

---

## Execution Modes

### Simple Mode

For straightforward queries - uses 6-node graph:

```
Planner → Searcher/RAG (parallel) → Analyzer → Evaluator → Synthesizer
                                              ↓ (if insufficient)
                                           Planner (max 2 loops)
```

### Hierarchical Mode

For complex queries - uses master planning and subtask execution:

```
Master Planner → [Subtask Loop] → Hierarchical Synthesizer
                      ↓
          Subtask Executor → Planner → Searcher/RAG → Analyzer
                                                        ↓
                                              Depth Evaluator
                                                        ↓
                                            Drill-Down Generator
                                                        ↓
                                               Plan Revisor
                                                        ↓
                                              Save Result
```

---

## Data Flow

### 1. Input Processing

```
User Query → Master Planner → Complexity Assessment → Mode Selection
```

### 2. Query Allocation

```
Strategic Planner → Check KB Contents → Allocate RAG/Web Queries
```

### 3. Parallel Retrieval

```
RAG Queries → ChromaDB → RAG Results
Web Queries → Tavily   → Search Results
```

### 4. Analysis & Synthesis

```
Results → Analyzer → Evaluation → Synthesis → Report
```

---

## Key Design Patterns

### 1. Cumulative State Accumulation

Uses `Annotated[list[str], operator.add]` for automatic list merging:

```python
# Each node appends to list
# LangGraph merges automatically
search_results: Annotated[list[str], operator.add]
```

### 2. Strategic Query Allocation

Planner checks KB contents and routes queries optimally:

```python
# KB has auth docs → RAG queries for auth
# Need current events → Web queries
allocation = {
    "rag_queries": ["internal auth flow"],
    "web_queries": ["OAuth2 best practices 2025"]
}
```

### 3. Structured Outputs

Pydantic schemas with `.with_structured_output()`:

```python
from src.schemas import StrategicPlan

planner_llm = get_planner_model().with_structured_output(StrategicPlan)
output = planner_llm.invoke(prompt)  # Validated Pydantic object
```

### 4. Dynamic Replanning

Plan Revisor analyzes findings and adapts master plan:

```python
# After finding important topic not in original plan
revision = {
    "should_revise": True,
    "new_subtasks": [...],
    "trigger_type": "new_topic"
}
```

---

## Directory Structure

```
test-smith/
├── main.py                      # CLI entry point
├── src/
│   ├── graphs/                  # Workflow definitions
│   │   ├── __init__.py          # Graph registry
│   │   ├── base_graph.py        # Base classes
│   │   ├── deep_research_graph.py
│   │   ├── quick_research_graph.py
│   │   ├── fact_check_graph.py
│   │   ├── comparative_graph.py
│   │   └── causal_inference_graph.py
│   ├── nodes/                   # Processing nodes
│   ├── prompts/                 # LLM prompts
│   ├── models.py                # Model configuration
│   ├── schemas.py               # Pydantic schemas
│   └── preprocessor/            # Document preprocessing
├── scripts/
│   ├── ingest/                  # KB ingestion
│   ├── utils/                   # Utilities
│   └── visualization/           # Graph visualization
├── evaluation/                  # LangSmith evaluation
├── documents/                   # RAG source documents
├── chroma_db/                   # Vector database
├── logs/                        # Execution logs
└── reports/                     # Generated reports
```

---

## Configuration

### Environment Variables

```bash
# Required
TAVILY_API_KEY="your-key"

# LangSmith (optional)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Gemini (optional)
GOOGLE_API_KEY="your-key"
MODEL_PROVIDER="ollama"  # or "gemini"
```

### Key Parameters

| Parameter | Location | Default | Purpose |
|-----------|----------|---------|---------|
| `recursion_limit` | main.py | 100 | Max LangGraph steps |
| `max_depth` | master_planner | 2 | Max drill-down depth |
| `max_revisions` | plan_revisor | 3 | Max plan revisions |
| `max_total_subtasks` | plan_revisor | 20 | Subtask budget |
| `loop_count` | evaluator | 2 | Max refinement loops |

---

## Related Documentation

- **[Multi-Graph Workflows](multi-graph-workflows.md)** - Workflow details and selection
- **[Creating Graphs](../development/creating-graphs.md)** - Build custom workflows
- **[RAG Guide](../knowledge-base/rag-guide.md)** - Knowledge base configuration
