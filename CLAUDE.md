# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Test-Smith is a **LangGraph-based multi-agent research assistant** that autonomously conducts deep research and generates comprehensive reports. It uses an advanced "Hierarchical Plan-and-Execute" strategy with **dynamic replanning** capabilities, featuring specialized agents that collaborate through a state-based workflow.

**Version:** v2.2 (Multi-Graph Architecture with 5 Specialized Workflows)

**Key Technologies:**
- LangGraph 0.6.11 (orchestration)
- LangChain 0.3.27 (LLM framework)
- Ollama (local LLMs: llama3, command-r, nomic-embed-text)
- ChromaDB 1.3.4 (vector database for RAG)
- Tavily API (web search)
- LangSmith (observability/tracing)

## Multi-Graph Architecture ⭐ NEW

Test-Smith now supports **multiple graph workflows** that can be selected based on your research needs. All graphs reuse the same nodes and prompts, making the system modular and extensible.

### Available Graphs

1. **deep_research** (default) - Hierarchical multi-agent research with dynamic replanning
   - Best for: Complex multi-faceted questions, deep exploration
   - Features: Task decomposition, recursive drill-down, adaptive planning
   - Complexity: High | Avg time: 2-5 minutes

2. **quick_research** - Fast single-pass research
   - Best for: Simple questions, quick fact lookups, time-sensitive needs
   - Features: Single-pass execution, max 2 refinement iterations
   - Complexity: Low | Avg time: 30-60 seconds

3. **fact_check** - Claim verification workflow
   - Best for: Verifying factual claims, checking accuracy, cross-referencing
   - Features: Evidence categorization, confidence scoring, citation tracking
   - Complexity: Medium | Avg time: 30-45 seconds

4. **comparative** - Side-by-side analysis
   - Best for: Comparing technologies/tools, trade-off analysis, decision support
   - Features: Comparison matrix, pros/cons, use case recommendations
   - Complexity: Medium | Avg time: 45-90 seconds

5. **causal_inference** ⭐ NEW - Root cause analysis and causal reasoning
   - Best for: Troubleshooting issues, incident investigation, understanding causality
   - Features: Hypothesis generation, evidence validation, causal graph, probability ranking
   - Complexity: Medium | Avg time: 60-90 seconds

### Graph Selection

```bash
# List all available graphs with descriptions
python main.py graphs

# List with detailed information
python main.py graphs --detailed

# Run with specific graph
python main.py run "Your query" --graph <graph_name>

# Default to deep_research (backward compatible)
python main.py run "Your query"
```

### Creating Custom Graphs

The modular architecture makes it easy to create new graph workflows:

1. Create a new file in `src/graphs/` (e.g., `my_workflow_graph.py`)
2. Extend `BaseGraphBuilder` and implement:
   - `get_state_class()` - Define your state schema
   - `build()` - Build and compile your workflow
   - `get_metadata()` - Describe your graph
3. Register in `src/graphs/__init__.py`
4. Reuse existing nodes from `src/nodes/` and prompts from `src/prompts/`

See `src/graphs/quick_research_graph.py` for a simple example.

## Architecture

### Multi-Agent Workflow

The system supports **two execution modes**:

#### Simple Mode (v1.0 - Single-Pass Research)
For straightforward queries, uses a **6-node graph** with conditional routing:

1. **Strategic Planner** → Intelligently allocates queries between RAG and web search
2. **Searcher** (Tavily) + **RAG Retriever** (ChromaDB) → Execute in parallel with DIFFERENT query sets
3. **Analyzer** → Merges and summarizes results
4. **Evaluator** → Assesses information sufficiency
5. **Router** → Decides: sufficient → synthesize, insufficient → refine (max 2 iterations)
6. **Synthesizer** → Generates final comprehensive report

#### Hierarchical Mode (v2.1 - Deep Research with Dynamic Replanning) ⭐ NEW
For complex queries, uses an **adaptive hierarchical workflow**:

1. **Master Planner** → Detects complexity and decomposes into subtasks (Phase 1)
2. **For each subtask:**
   - Strategic Planner → Allocates queries for this specific subtask
   - Searcher + RAG Retriever → Execute in parallel
   - Analyzer → Processes results
   - **Depth Evaluator** → Assesses depth quality (Phase 2)
   - **Drill-Down Generator** → Creates child subtasks if needed (Phase 3)
   - **Plan Revisor** → Adapts master plan based on discoveries ⭐ (Phase 4)
3. **Hierarchical Synthesizer** → Synthesizes all subtask results into comprehensive report

**Key Innovations:**
- **Dynamic Replanning (Phase 4):** System adapts master plan mid-execution based on important discoveries
- **Hierarchical Decomposition:** Complex queries broken into manageable subtasks with recursive drill-down
- **Strategic Query Allocation:** Targets queries to right information source (RAG vs web)
- **Depth-Aware Exploration:** Automatically adjusts research depth based on importance
- **Safety Controls:** Budget limits prevent runaway expansion (max 3 revisions, 20 subtasks)

**Key Pattern:** Uses `Annotated[list[str], operator.add]` for cumulative result accumulation across iterations.

#### Causal Inference Mode (v2.2 - Root Cause Analysis) ⭐ NEW
For troubleshooting and investigation queries, uses a **9-node specialized workflow**:

1. **Issue Analyzer** → Extracts symptoms, context, and scope from problem statement
2. **Brainstormer** → Generates diverse root cause hypotheses (5-8 hypotheses)
3. **Evidence Planner** → Plans strategic queries for evidence gathering (RAG + Web)
4. **Searcher + RAG Retriever** → Gather evidence in parallel
5. **Causal Checker** → Validates causal relationships using rigorous criteria
6. **Hypothesis Validator** → Ranks hypotheses by likelihood with confidence levels
7. **Router** → Decides if more evidence needed (max 2 iterations)
8. **Causal Graph Builder** → Creates visualization-ready graph structure
9. **Root Cause Synthesizer** → Generates comprehensive RCA report

**Key Features:**
- **Systematic Hypothesis Generation:** Uses divergent thinking (5 Whys, Fishbone, Analogical)
- **Rigorous Causal Validation:** Temporal precedence, covariation, mechanism plausibility
- **Evidence-Based Ranking:** Probability scores (0.0-1.0) with confidence levels (high/medium/low)
- **Causal Graph Visualization:** Structured data for nodes (hypotheses/symptoms) and edges (relationships)
- **Comprehensive RCA Reports:** Executive summary, ranked hypotheses, recommendations, confidence assessment

**Use Cases:**
- Technical troubleshooting and debugging
- Incident investigation and post-mortems
- System failure analysis
- Understanding why something happened
- Hypothesis-driven investigation

**Causal Graph Visualization:**
The workflow generates a structured graph representation (nodes + edges) that can be visualized:
```bash
# Extract graph data from workflow output and save to JSON
# Then visualize using the included script
python visualize_causal_graph.py causal_graph.json

# Opens an interactive HTML visualization showing:
# - Hypothesis nodes (color-coded by likelihood)
# - Symptom nodes
# - Causal relationships (edges with strength indicators)
```

### State Management

```python
class AgentState(TypedDict):
    query: str                      # Original user query
    web_queries: list[str]          # Queries allocated for web search
    rag_queries: list[str]          # Queries allocated for KB retrieval
    allocation_strategy: str        # Reasoning for query allocation
    search_results: Annotated[list[str], operator.add]  # Accumulated results
    rag_results: Annotated[list[str], operator.add]     # KB results
    analyzed_data: Annotated[list[str], operator.add]   # Processed information
    report: str                     # Final synthesis
    evaluation: str                 # Sufficiency assessment
    loop_count: int                 # Iteration counter
```

**Strategic Allocation:** The planner checks `chroma_db/` contents and populates `web_queries` and `rag_queries` separately based on information needs.

State persists via **SQLite checkpointing** (`langgraph-checkpoint-sqlite`) for conversation continuity.

## Running the System

### Prerequisites

```bash
# 1. Ensure Ollama is running
ollama list  # Should show llama3, command-r, nomic-embed-text

# 2. Pull models if missing
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text

# 3. Activate virtual environment
source .venv/bin/activate
```

### Main Commands

```bash
# Basic research query
python main.py run "YOUR_QUERY_HERE"

# Continue conversation with thread ID
python main.py run "Follow-up question" --thread-id abc-123

# Use causal inference graph for troubleshooting
python main.py run "Why is my application experiencing high latency?" --graph causal_inference

# Check version
python main.py --version
```

### Knowledge Base Ingestion

```bash
# RECOMMENDED: Production ingestion with intelligent preprocessing
python ingest_with_preprocessor.py

# With quality filtering (skip files with score < 0.5)
python ingest_with_preprocessor.py --min-quality 0.5

# Diagnostic ingestion (use for debugging embedding issues)
python ingest_diagnostic.py

# Automated clean re-ingest with validation
./clean_and_reingest.sh
```

**Ingestion Configuration:**
- **Source:** `documents/` directory
- **Destination:** `chroma_db/` (ChromaDB vector store)
- **Preprocessing:** 6-phase pipeline with quality analysis
- **Chunking:** Smart strategy selection per document (target: 500-1000 chars)
- **Cleaning:** Exact + near-duplicate removal, boilerplate filtering
- **Embedding:** nomic-embed-text via Ollama (768 dimensions)
- **Collection:** "research_agent_collection"

**Preprocessor Features:**
- Document quality analysis before ingestion
- Intelligent chunking strategy selection (Recursive, Markdown, Hybrid)
- Duplicate detection and removal (exact + 95% similarity threshold)
- Boilerplate pattern removal
- Quality metrics and recommendations

### Diagnostic Tools

```bash
# Interactive notebook for ChromaDB exploration
jupyter notebook chroma_explorer.ipynb

# View ingestion logs
cat ingestion_diagnostic_*.log

# Monitor via LangSmith
# Navigate to project "deep-research-v1-proto" in LangSmith UI
```

## Development

### Project Structure

```
src/
├── graphs/                      # ⭐ Multiple graph workflows
│   ├── __init__.py             # Graph registry system
│   ├── base_graph.py           # Base classes for building graphs
│   ├── deep_research_graph.py  # Hierarchical research workflow
│   ├── quick_research_graph.py # Fast single-pass workflow
│   ├── fact_check_graph.py     # Claim verification workflow
│   ├── comparative_graph.py    # Side-by-side comparison workflow
│   └── causal_inference_graph.py # ⭐ NEW: Root cause analysis workflow
├── graph.py                     # Legacy compatibility (deprecated)
├── models.py                    # Model factory functions (reusable)
├── schemas.py                   # Pydantic data schemas (reusable)
├── nodes/                       # Processing nodes (reusable across graphs)
│   ├── planner_node.py
│   ├── searcher_node.py
│   ├── rag_retriever_node.py
│   ├── analyzer_node.py
│   ├── evaluator_node.py
│   ├── synthesizer_node.py
│   ├── master_planner_node.py
│   ├── depth_evaluator_node.py
│   ├── drill_down_generator.py
│   ├── plan_revisor_node.py
│   ├── issue_analyzer_node.py          # ⭐ NEW: Causal inference nodes
│   ├── brainstormer_node.py            # ⭐ NEW
│   ├── evidence_planner_node.py        # ⭐ NEW
│   ├── causal_checker_node.py          # ⭐ NEW
│   ├── hypothesis_validator_node.py    # ⭐ NEW
│   ├── causal_graph_builder_node.py    # ⭐ NEW
│   └── root_cause_synthesizer_node.py  # ⭐ NEW
├── prompts/                     # LangChain prompt templates (reusable)
│   ├── planner_prompt.py
│   ├── analyzer_prompt.py
│   ├── evaluator_prompt.py
│   ├── synthesizer_prompt.py
│   ├── master_planner_prompt.py
│   ├── issue_analyzer_prompt.py         # ⭐ NEW: Causal inference prompts
│   ├── brainstormer_prompt.py           # ⭐ NEW
│   ├── evidence_planner_prompt.py       # ⭐ NEW
│   ├── causal_checker_prompt.py         # ⭐ NEW
│   ├── hypothesis_validator_prompt.py   # ⭐ NEW
│   └── root_cause_synthesizer_prompt.py # ⭐ NEW
└── preprocessor/                # Document preprocessing system
    ├── __init__.py
    ├── document_analyzer.py    # Quality analysis & scoring
    ├── chunking_strategy.py    # Smart chunking selection
    ├── content_cleaner.py      # Deduplication & cleaning
    └── quality_metrics.py      # Validation & metrics
```

**Key Design Principles:**
- **Modular:** Nodes and prompts are reusable across all graphs
- **Extensible:** Easy to add new graph workflows
- **Backward Compatible:** Old code importing from `src.graph` still works
- **Registry-Based:** Graphs auto-register and are discoverable via `list_graphs()`

### Customization Points

**Change LLMs:**
Edit `src/models.py` - each agent has a dedicated model function:
```python
def get_planner_model():
    return ChatOllama(model="llama3")

def get_evaluation_model():
    return ChatOllama(model="command-r")
```

**Modify Prompts:**
Edit templates in `src/prompts/` - uses LangChain PromptTemplate with variable injection. Changes apply to all graphs using that node.

**Create New Graph Workflow:**
1. Create `src/graphs/my_workflow_graph.py`
2. Extend `BaseGraphBuilder` class:
   ```python
   from src.graphs.base_graph import BaseGraphBuilder

   class MyWorkflowGraphBuilder(BaseGraphBuilder):
       def get_state_class(self) -> type:
           return MyWorkflowState  # Define your state schema

       def build(self) -> StateGraph:
           workflow = StateGraph(MyWorkflowState)
           # Add nodes, edges, conditional routing...
           return workflow.compile()

       def get_metadata(self) -> dict:
           return {"name": "My Workflow", "description": "..."}
   ```
3. Register in `src/graphs/__init__.py` (add to `_auto_register_graphs()`)
4. Reuse existing nodes from `src/nodes/` or create new ones

**Modify Existing Graph:**
Edit the specific graph file (e.g., `src/graphs/quick_research_graph.py`):
- Add/remove nodes
- Change routing logic
- Modify loop limits
- Adjust state schema

**Add New Node:**
1. Create `src/nodes/my_node.py` with function signature: `def my_node(state: dict) -> dict`
2. Create `src/prompts/my_prompt.py` if needed
3. Add model function to `src/models.py` if needed
4. Use in any graph by importing and registering the node

**Tune Preprocessing:**
Edit parameters in `ingest_with_preprocessor.py`:
```python
min_quality_score=0.5        # Minimum quality threshold
similarity_threshold=0.95    # Near-duplicate threshold
min_content_length=100       # Minimum chunk size
```

**Create RAG-Friendly Documentation:**
Follow guidelines in `docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md`:
- Target 500-1500 characters per section
- Include topic in every header
- Use consistent terminology
- Define acronyms on first use
- Make sections self-contained

### Dependencies

Install with pinned versions:
```bash
pip install -r requirements.txt
```

Edit high-level deps in `requirements.in`, then recompile:
```bash
pip-compile requirements.in
```

## Important Implementation Details

### Parallel Execution & Strategic Allocation

Searcher (Tavily) and RAG Retriever (ChromaDB) run **simultaneously** but with **different query sets**:
```python
workflow.add_edge("planner", "searcher")
workflow.add_edge("planner", "rag_retriever")
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("rag_retriever", "analyzer")
```

**Strategic Allocation Process:**
1. Planner checks KB contents using `check_kb_contents()`:
   - Verifies `chroma_db/` exists
   - Counts total chunks
   - Samples documents to understand content
2. LLM allocates queries strategically:
   - **RAG queries:** Domain-specific, internal docs, established concepts
   - **Web queries:** Current events, general knowledge, external references
3. Nodes skip execution if their query list is empty (saves API calls)

**Example Allocation:**
- Query: "How does our auth system work compared to OAuth2 best practices?"
- KB Status: Contains internal auth documentation
- Result: 3 RAG queries (internal implementation) + 2 web queries (OAuth2 best practices)

### Iterative Refinement

Evaluator controls loop continuation:
```python
def router(state: AgentState) -> Literal["synthesizer", "planner"]:
    if state["loop_count"] >= 2:
        return "synthesizer"  # Force exit after 2 iterations
    if "sufficient" in state.get("evaluation", "").lower():
        return "synthesizer"
    return "planner"  # Refine with feedback
```

### State Accumulation

Uses annotation pattern for cumulative aggregation:
```python
from typing import Annotated
import operator

search_results: Annotated[list[str], operator.add]
# Each node appends to list; state merges automatically
```

### Structured Outputs

Nodes use Pydantic schemas with `.with_structured_output()`:
```python
from src.schemas import StrategicPlan

planner_llm = get_planner_model().with_structured_output(StrategicPlan)
# StrategicPlan schema ensures:
#   - rag_queries: List[str]
#   - web_queries: List[str]
#   - strategy: str (reasoning for allocation)
# Ensures type-safe, validated outputs
```

## Monitoring & Observability

### LangSmith Integration

**Environment Variables:**
```bash
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="<your-key>"
LANGCHAIN_PROJECT="deep-research-v1-proto"
```

**View Traces:**
1. Log in to LangSmith
2. Navigate to project "deep-research-v1-proto"
3. Click on trace to see full execution graph with inputs/outputs per node

### Embedding Quality Diagnostics

**Section 2.2 in `chroma_explorer.ipynb`** provides comprehensive checks:
- Duplicate detection
- Diversity analysis (variance across dimensions)
- Pairwise similarity distributions
- Visual diagnostics (histograms, variance plots)

**Healthy Embeddings:**
- Median chunk size: 500-800 characters
- Duplication rate: <5%
- Quality score: >0.7
- PCA needs 20-40 components for 95% variance
- Mean cosine similarity: 0.3-0.8

**Problematic Embeddings:**
- Median chunk size: <200 characters (chunks too small)
- Duplication rate: >15% (too much repetition)
- Quality score: <0.5 (poor quality)
- PCA needs only 1-10 components for 99% variance (critical - lack of diversity)
- Mean similarity > 0.95 (documents too similar)

**Common Root Causes:**
- UnstructuredLoader over-splitting → Use preprocessor
- Repeated headers/footers → Enable boilerplate removal
- Small sections in source docs → Follow `WRITING_RAG_FRIENDLY_DOCUMENTATION.md`

**Solution:** Always use `ingest_with_preprocessor.py` for production ingestion.

## Configuration Files

**.env** (required for LangSmith + Tavily):
```bash
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="<langsmith-key>"
LANGCHAIN_PROJECT="deep-research-v1-proto"
TAVILY_API_KEY="<tavily-key>"
```

**Note:** `.env` is checked into git with actual keys (not best practice for production).

## Known Issues & Limitations

- **Max 2 iterations:** Hardcoded in router to prevent infinite loops
- **No test coverage:** pytest installed but no tests written yet
- **Print-based logging:** Use structured logging for production

## Additional Resources

**Architecture & System Design:**
- **docs/system-overview.md** - Comprehensive architecture deep dive with preprocessing details
- **CLAUDE.md** - This file - Quick reference for Claude Code

**RAG & Knowledge Base:**
- **docs/RAG_DATA_PREPARATION_GUIDE.md** - 400+ line comprehensive guide
- **docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md** - Best practices for document authors
- **docs/DOCUMENT_DESIGN_EVALUATION.md** - Reproducible quality metrics
- **PREPROCESSOR_QUICKSTART.md** - Quick start guide for preprocessing

**Tools & Analysis:**
- **chroma_explorer.ipynb** - Interactive notebook for database analysis with PCA
- **ingest_with_preprocessor.py** - Production ingestion with quality pipeline
- **ingest_diagnostic.py** - Enhanced ingestion with real-time quality checks
- **clean_and_reingest.sh** - Automated clean re-ingest workflow
