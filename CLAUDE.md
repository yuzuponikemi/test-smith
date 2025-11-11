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

1. **Strategic Planner** → Intelligently allocates queries between RAG and web search
   - Checks knowledge base contents and availability
   - Allocates domain-specific queries to RAG (0-5 queries)
   - Allocates current/external queries to web search (0-5 queries)
   - Provides reasoning for allocation strategy
2. **Searcher** (Tavily) + **RAG Retriever** (ChromaDB) → Execute in parallel with DIFFERENT query sets
3. **Analyzer** → Merges and summarizes results
4. **Evaluator** → Assesses information sufficiency
5. **Router** → Decides: sufficient → synthesize, insufficient → refine (max 2 iterations)
6. **Synthesizer** → Generates final comprehensive report

**Key Innovation:** Strategic query allocation saves API calls and improves relevance by targeting queries to the right information source.

**Key Pattern:** Uses `Annotated[list[str], operator.add]` for cumulative result accumulation across iterations.

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
├── prompts/              # LangChain prompt templates
│   ├── planner_prompt.py
│   ├── analyzer_prompt.py
│   ├── evaluator_prompt.py
│   └── synthesizer_prompt.py
└── preprocessor/         # Document preprocessing system
    ├── __init__.py
    ├── document_analyzer.py    # Quality analysis & scoring
    ├── chunking_strategy.py    # Smart chunking selection
    ├── content_cleaner.py      # Deduplication & cleaning
    └── quality_metrics.py      # Validation & metrics
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
