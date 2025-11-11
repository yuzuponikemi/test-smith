# Agent Graph

This document explains the structure of the multi-agent research system defined in `src/graph.py`.

## Overview

The agent is a LangGraph-based workflow with 6 specialized nodes collaborating through a state-based system. The workflow combines **web search** (Tavily) and **knowledge base retrieval** (ChromaDB) in parallel for comprehensive research.

## Agent Nodes

### 1. Planner (Strategic Query Allocator)
**File:** `src/nodes/planner_node.py`

**Purpose:** Intelligently allocates queries between RAG and web search based on information availability

**Input:** User query, feedback from previous iterations, KB metadata
**Output:** Strategic plan with separate query sets for RAG and web search

**Behavior:**
1. **Checks knowledge base contents** using `check_kb_contents()`:
   - Verifies if `chroma_db/` exists
   - Counts total chunks available
   - Samples documents to understand what's in the KB
   - Generates summary for strategic decision-making

2. **Strategic allocation** via LLM:
   - Analyzes which information is likely in KB vs needs web
   - Allocates queries to RAG for domain-specific/internal content
   - Allocates queries to web for current events/general knowledge
   - Provides reasoning for the allocation strategy

3. **Refines based on feedback:**
   - Adjusts allocation if evaluator indicates missing information
   - Increments loop counter for iteration control

**Model:** `llama3` (via `get_planner_model()`)

**Output Validation:** Uses `StrategicPlan` Pydantic schema
```python
class StrategicPlan(BaseModel):
    rag_queries: List[str] = Field(
        description="Queries for knowledge base retrieval"
    )
    web_queries: List[str] = Field(
        description="Queries for web search"
    )
    strategy: str = Field(
        description="Reasoning for this allocation"
    )
```

**Allocation Examples:**
- **KB-heavy:** Internal API docs query → 4 RAG queries, 1 web query
- **Web-heavy:** Current AI trends → 1 RAG query, 4 web queries
- **Balanced:** Implementation with best practices → 2 RAG, 3 web queries
- **Web-only:** No KB available or query needs current events → 0 RAG, 5 web queries

### 2. Searcher
**File:** `src/nodes/searcher_node.py`

**Purpose:** Executes web searches via Tavily API

**Input:** `web_queries` from strategic planner (0-5 queries)
**Output:** Web search results

**Behavior:**
- Receives strategically allocated queries for web search
- Skips execution if `web_queries` is empty (saves API calls)
- Executes each query against Tavily search API (max 5 results per query)
- Aggregates results from multiple queries
- Handles errors gracefully

**Strategic Allocation:**
- Receives queries that need **current information** (news, trends, recent events)
- Receives queries for **general knowledge** not in the knowledge base
- Receives queries for **external references** and comparisons

**API:** Tavily (configured via `TAVILY_API_KEY` environment variable)

### 3. RAG Retriever
**File:** `src/nodes/rag_retriever_node.py`

**Purpose:** Retrieves relevant chunks from ChromaDB knowledge base

**Input:** `rag_queries` from strategic planner (0-5 queries)
**Output:** Retrieved document chunks

**Behavior:**
- Receives strategically allocated queries for knowledge base search
- Skips execution if `rag_queries` is empty (KB not available or not needed)
- Embeds each query using `nomic-embed-text` model
- Performs semantic similarity search in ChromaDB
- Returns top 5 most relevant chunks per query
- Includes source metadata for provenance

**Strategic Allocation:**
- Receives queries for **domain-specific content** (internal documentation, APIs)
- Receives queries for **established concepts** and procedures
- Receives queries for **technical details** that should be in uploaded docs
- Skipped entirely if KB is empty or query needs only current/external info

**Critical Configuration:**
```python
# MUST use nomic-embed-text (same model used during ingestion)
embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

**Database:**
- Collection: `research_agent_collection`
- Location: `chroma_db/`
- Embedding dimension: 768

**Note:** RAG Retriever runs in **parallel** with Searcher for performance.

### 4. Analyzer (Context-Aware Combiner)
**File:** `src/nodes/analyzer_node.py`

**Purpose:** Intelligently merges results from both sources with understanding of strategic intent

**Input:**
- Original user `query`
- `allocation_strategy` (reasoning from planner)
- `web_queries` and `rag_queries` (what was asked of each source)
- `search_results` from Tavily
- `rag_results` from ChromaDB

**Output:** Strategic analysis combining both sources

**Behavior:**
1. **Understands strategic context** - Receives the planner's reasoning for query allocation
2. **Respects source priorities** - Gives appropriate weight based on strategic intent
3. **Prevents RAG dismissal** - Understands that internal docs may be concise but authoritative
4. **Combines complementary info** - Uses web to enhance RAG and vice versa
5. **Maintains source attribution** - Tracks which information came from which source
6. **Addresses original query** - Synthesizes information to answer the user's question

**Key Improvement:** The analyzer now receives strategic context, preventing it from misunderstanding or ignoring RAG results when they're the primary source of relevant information.

**Model:** `llama3` (via `get_analyzer_model()`)

### 5. Evaluator
**File:** `src/nodes/evaluator_node.py`

**Purpose:** Assesses information sufficiency and quality

**Input:** Analyzed data from analyzer
**Output:** Sufficiency decision ("sufficient" or "insufficient")

**Behavior:**
- Evaluates if gathered information answers the query
- Checks for completeness and relevance
- Determines if more research is needed
- Provides feedback for planner refinement

**Model:** `command-r` (via `get_evaluator_model()`)

**Output Validation:** Uses `Evaluation` Pydantic schema
```python
class Evaluation(BaseModel):
    is_sufficient: bool = Field(description="Information sufficiency")
```

### 6. Synthesizer
**File:** `src/nodes/synthesizer_node.py`

**Purpose:** Generates comprehensive final reports

**Input:** All analyzed data from iterations
**Output:** Final research report

**Behavior:**
- Synthesizes information from all iterations
- Creates well-structured, comprehensive report
- Cites sources (both web and knowledge base)
- Produces user-ready output

**Model:** `llama3` (via `get_synthesizer_model()`)

## Workflow

### State Structure

```python
class AgentState(TypedDict):
    query: str                                      # Original user query
    web_queries: list[str]                          # Queries allocated for web search
    rag_queries: list[str]                          # Queries allocated for KB retrieval
    allocation_strategy: str                        # Reasoning for query allocation
    search_results: Annotated[list[str], operator.add]  # Web results (accumulated)
    rag_results: Annotated[list[str], operator.add]     # KB results (accumulated)
    analyzed_data: Annotated[list[str], operator.add]   # Processed info (accumulated)
    report: str                                     # Final report
    evaluation: str                                 # Sufficiency assessment
    loop_count: int                                 # Iteration counter
```

**Key Patterns:**
- `Annotated[list[str], operator.add]` enables cumulative accumulation across iterations
- `web_queries` and `rag_queries` are separate lists allocated strategically by the planner
- `allocation_strategy` provides transparency into planner's decision-making

### Execution Flow

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Strategic Planner               │
│                                         │
│  1. Check KB contents (chroma_db/)      │
│  2. Analyze information needs           │
│  3. Allocate queries strategically:     │
│     - rag_queries (domain-specific)     │
│     - web_queries (current/external)    │
└──────┬──────────────────────────────────┘
       │
       ├─────────────────────────┐
       │ web_queries             │ rag_queries
       ▼                         ▼
┌─────────────┐          ┌─────────────┐
│  Searcher   │          │    RAG      │  ← Execute in PARALLEL
│  (Tavily)   │          │  Retriever  │    with DIFFERENT queries
│             │          │  (ChromaDB) │
│ 0-5 queries │          │ 0-5 queries │
└──────┬──────┘          └──────┬──────┘
       │                        │
       └──────────┬─────────────┘
                  │
                  ▼
           ┌─────────────┐
           │  Analyzer   │  ← Merges web + KB results
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │  Evaluator  │  ← Assesses sufficiency
           └──────┬──────┘
                  │
         ┌────────┴────────┐
         │                 │
    Sufficient        Insufficient
         │                 │
         ▼                 ▼
  ┌─────────────┐    ┌─────────────┐
  │ Synthesizer │    │  Planner    │ ← Refine allocation
  │             │    │  (Loop)     │    with feedback
  └──────┬──────┘    └─────────────┘    (max 2 iterations)
         │
         ▼
     Final Report
```

**Key Improvements:**
1. **Strategic Allocation** - The planner performs intelligent query distribution instead of sending the same queries to both sources:
   - **Saves API calls** - Only queries web when needed
   - **Improves relevance** - KB queries target internal docs, web queries target current info
   - **Adapts dynamically** - Allocation changes based on KB contents and query type

2. **Context-Aware Analysis** - The analyzer receives strategic context to properly understand and combine results:
   - **Understands intent** - Knows why each source was chosen
   - **Respects priorities** - Gives appropriate weight to each source based on strategy
   - **Prevents dismissal** - Won't ignore RAG results even if web results seem more detailed

### Iteration Logic

**Router Function** (`src/graph.py`):
```python
def router(state):
    loop_count = state.get("loop_count", 0)

    # Force exit after 2 iterations
    if loop_count >= 2:
        return "synthesizer"

    # Check evaluation result
    if "sufficient" in state["evaluation"].lower():
        return "synthesizer"
    else:
        return "planner"  # Refine and try again
```

**Maximum Iterations:** 2 (hardcoded to prevent infinite loops)

## Configuration

### Models

Models are configured in `src/models.py`:

```python
def get_planner_model():
    return ChatOllama(model="llama3")

def get_analyzer_model():
    return ChatOllama(model="llama3")

def get_evaluator_model():
    return ChatOllama(model="command-r")

def get_synthesizer_model():
    return ChatOllama(model="llama3")
```

**To change models:** Edit the return values in each function.

### Prompts

Prompts are defined in `src/prompts/`:

- `planner_prompt.py` - Strategic query allocation between RAG and web search
  - `STRATEGIC_PLANNER_PROMPT` - Main prompt for intelligent allocation with examples
  - `PLANNER_PROMPT` - Legacy simple planning (not currently used)
- `analyzer_prompt.py` - Result summarization
- `evaluator_prompt.py` - Sufficiency assessment
- `synthesizer_prompt.py` - Final report generation

**To customize:** Edit the prompt strings in each file.

**Strategic Planner Prompt** includes:
- Framework for deciding RAG vs web allocation
- KB-heavy, web-heavy, balanced, and web-only examples
- Guidelines for query diversity and specificity
- Instructions for handling feedback and refinement

### Web Search

**Provider:** Tavily API
**Configuration:**
```bash
# .env file
TAVILY_API_KEY="your-api-key-here"
```

**Node:** `src/nodes/searcher_node.py`

### Knowledge Base Retrieval

**Database:** ChromaDB
**Configuration:**
- Collection: `research_agent_collection`
- Persist directory: `chroma_db/`
- Embedding model: `nomic-embed-text`
- Top-k: 5 chunks per query

**Node:** `src/nodes/rag_retriever_node.py`

**Important:** The RAG retriever MUST use the same embedding model (`nomic-embed-text`) that was used during document ingestion. Using a different model will result in poor retrieval quality because the embeddings will be in different vector spaces.

## Parallel Execution

The workflow uses **parallel execution** for performance:

```python
# Both searcher and rag_retriever execute simultaneously
workflow.add_edge("planner", "searcher")
workflow.add_edge("planner", "rag_retriever")

# Both feed into analyzer
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("rag_retriever", "analyzer")
```

**Benefits:**
- Faster execution (web search + DB retrieval happen concurrently)
- Better information coverage (web + internal knowledge)
- No blocking dependencies

## State Accumulation

The system uses `Annotated[list[str], operator.add]` for cumulative state:

```python
search_results: Annotated[list[str], operator.add]
rag_results: Annotated[list[str], operator.add]
analyzed_data: Annotated[list[str], operator.add]
```

**How it works:**
- Iteration 1: `search_results = ["result1", "result2"]`
- Iteration 2: New results are **appended**: `search_results = ["result1", "result2", "result3", "result4"]`
- Synthesizer sees **all results** from all iterations

## Monitoring

### LangSmith Integration

**Configuration:**
```bash
# .env file
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"
```

**View Traces:**
1. Log in to LangSmith
2. Navigate to your project
3. View detailed execution traces with:
   - Node-by-node execution flow
   - Inputs/outputs for each node
   - Token usage and latency
   - Error tracking

### Console Output

Each node prints execution status:
```
---PLANNER---
---SEARCHER---
---RAG RETRIEVER---
Retrieving from RAG for: query1
  Retrieved 5 documents
---ANALYZER---
---EVALUATOR---
---ROUTER---
---SYNTHESIZER---
```

## Extending the Graph

### Adding a New Node

1. **Create node file:** `src/nodes/my_node.py`
   ```python
   def my_node(state):
       # Process state
       return {"my_output": result}
   ```

2. **Add to state:** `src/graph.py`
   ```python
   class AgentState(TypedDict):
       # ... existing fields
       my_output: str  # or Annotated[list[str], operator.add]
   ```

3. **Register in graph:** `src/graph.py`
   ```python
   from src.nodes.my_node import my_node

   workflow.add_node("my_node", my_node)
   workflow.add_edge("source_node", "my_node")
   ```

4. **Create prompt:** `src/prompts/my_prompt.py`

5. **Add model function:** `src/models.py`
   ```python
   def get_my_model():
       return ChatOllama(model="llama3")
   ```

### Modifying Routing Logic

Edit the `router()` function in `src/graph.py`:

```python
def router(state):
    # Custom routing logic
    if custom_condition:
        return "node_a"
    else:
        return "node_b"
```

### Adding Parallel Nodes

```python
# Both execute simultaneously
workflow.add_edge("source", "parallel_1")
workflow.add_edge("source", "parallel_2")

# Both feed into merger
workflow.add_edge("parallel_1", "merger")
workflow.add_edge("parallel_2", "merger")
```

## Troubleshooting

### Poor RAG Retrieval

**Symptoms:** RAG retriever returns irrelevant chunks

**Causes:**
- Wrong embedding model in `rag_retriever_node.py`
- Poor quality chunks in database
- No documents ingested

**Solutions:**
1. Verify embedding model is `nomic-embed-text`
2. Run `python ingest_with_preprocessor.py` to re-ingest
3. Check `chroma_db/` directory exists and has data

### Infinite Loops

**Prevention:** Router automatically exits after 2 iterations

**To change limit:** Edit router function:
```python
if loop_count >= 3:  # Increase to 3 iterations
    return "synthesizer"
```

### No Web Results

**Cause:** Missing or invalid Tavily API key

**Solution:** Check `.env` file has valid `TAVILY_API_KEY`

### Ollama Connection Errors

**Symptoms:** Model loading fails

**Solutions:**
```bash
# Check Ollama is running
ollama list

# Pull missing models
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text
```

## See Also

- **[System Overview](system-overview.md)** - Complete architecture documentation
- **[CLAUDE.md](../CLAUDE.md)** - Quick reference guide
- **[RAG Data Preparation Guide](RAG_DATA_PREPARATION_GUIDE.md)** - Knowledge base setup

---

**Key Takeaway:** The system uses **strategic query allocation** to intelligently distribute queries between real-time web search (Tavily) and local knowledge base retrieval (ChromaDB). The planner checks KB contents and allocates queries based on information type—internal/domain-specific content goes to RAG, current/external info goes to web search. Both sources execute in parallel with their optimized query sets, then iterative refinement ensures comprehensive, high-quality research outputs.
