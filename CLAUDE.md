# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Test-Smith is a **LangGraph-based multi-agent research assistant** that autonomously conducts deep research and generates comprehensive reports. It uses a "Plan-and-Execute" strategy with specialized agents collaborating through a state-based workflow.

**Key Technologies:**
- LangGraph 0.6.11 (orchestration)
- LangChain 0.3.27 (LLM framework)
- Ollama (local LLMs: llama3, command-r, nomic-embed-text)
- ChromaDB 1.3.4 (vector database for RAG)
- Tavily API (web search)
- LangSmith (observability/tracing)

## Architecture

### Multi-Agent Workflow

The system executes a **6-node graph** with conditional routing and iterative loops:

1. **Planner** → Decomposes query into 3-5 search queries
2. **Searcher** (Tavily) + **RAG Retriever** (ChromaDB) → Execute in parallel
3. **Analyzer** → Merges and summarizes results
4. **Evaluator** → Assesses information sufficiency
5. **Router** → Decides: sufficient → synthesize, insufficient → refine (max 2 iterations)
6. **Synthesizer** → Generates final comprehensive report

**Key Pattern:** Uses `Annotated[list[str], operator.add]` for cumulative result accumulation across iterations.

### State Management

```python
class AgentState(TypedDict):
    query: str                      # Original user query
    plan: list[str]                 # Current search plan
    search_results: Annotated[list[str], operator.add]  # Accumulated results
    analyzed_data: Annotated[list[str], operator.add]   # Processed information
    report: str                     # Final synthesis
    evaluation: str                 # Sufficiency assessment
    loop_count: int                 # Iteration counter
```

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

# Check version
python main.py --version
```

### Knowledge Base Ingestion

```bash
# Standard ingestion (use for production)
python ingest.py

# Diagnostic ingestion (use for debugging embedding issues)
python ingest_diagnostic.py

# Automated clean re-ingest with validation
./clean_and_reingest.sh
```

**Ingestion Configuration:**
- **Source:** `documents/` directory
- **Destination:** `chroma_db/` (ChromaDB vector store)
- **Chunking:** 1000 chars, 200 char overlap (RecursiveCharacterTextSplitter)
- **Embedding:** nomic-embed-text via Ollama
- **Collection:** "research_agent_collection"

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
├── graph.py              # Core workflow definition (START HERE)
├── models.py             # Model factory functions
├── schemas.py            # Pydantic data schemas
├── nodes/                # Processing nodes (6 agents)
│   ├── planner_node.py
│   ├── searcher_node.py
│   ├── rag_retriever_node.py
│   ├── analyzer_node.py
│   ├── evaluator_node.py
│   └── synthesizer_node.py
└── prompts/              # LangChain prompt templates
    ├── planner_prompt.py
    ├── analyzer_prompt.py
    ├── evaluator_prompt.py
    └── synthesizer_prompt.py
```

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
Edit templates in `src/prompts/` - uses LangChain PromptTemplate with variable injection.

**Adjust Workflow:**
Edit `src/graph.py`:
- Add/remove nodes
- Change routing logic (see `router()` function)
- Modify loop limits (currently max 2 iterations)

**Add New Node:**
1. Create `src/nodes/my_node.py` with function signature: `def my_node(state: AgentState) -> dict`
2. Create `src/prompts/my_prompt.py`
3. Add model function to `src/models.py`
4. Register in `src/graph.py` workflow

**Tune Ingestion:**
Edit parameters in `ingest.py`:
```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

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

### Parallel Execution

Searcher (Tavily) and RAG Retriever (ChromaDB) run **simultaneously** for performance:
```python
workflow.add_edge("planner", "searcher")
workflow.add_edge("planner", "rag_retriever")
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("rag_retriever", "analyzer")
```

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
from src.schemas import Plan

planner_llm = get_planner_model().with_structured_output(Plan)
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
- Mean cosine similarity: 0.3 - 0.8
- Std deviation: > 0.01
- PCA needs 20+ components for 95% variance

**Problematic Embeddings:**
- Mean similarity > 0.95 (documents too similar)
- Std < 0.01 (low variance - model may not be working)
- PCA needs only 1 component for 99% variance (critical issue)

See `EMBEDDING_DIAGNOSTICS.md` for troubleshooting guide.

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
- **README outdated:** References DuckDuckGo but system uses Tavily
- **Embedding diagnostics:** If PCA shows 1 component for 99% variance, re-run `ingest_diagnostic.py`

## Additional Resources

- **docs/system-overview.md** - 400+ line architecture deep dive
- **EMBEDDING_DIAGNOSTICS.md** - Troubleshooting guide for vector DB issues
- **chroma_explorer.ipynb** - Interactive notebook for database analysis
- **ingest_diagnostic.py** - Enhanced ingestion with real-time quality checks
