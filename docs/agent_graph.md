# Agent Graph

This document explains the structure of the multi-agent research system defined in `src/graph.py`.

## Overview

The agent is a LangGraph-based workflow with 6 specialized nodes collaborating through a state-based system. The workflow combines **web search** (Tavily) and **knowledge base retrieval** (ChromaDB) in parallel for comprehensive research.

## Agent Nodes

### 1. Planner
**File:** `src/nodes/planner_node.py`

**Purpose:** Decomposes user queries into targeted research strategies

**Input:** User query, feedback from previous iterations
**Output:** List of 3-5 search queries

**Behavior:**
- Analyzes the user's question
- Generates specific, actionable search queries
- Considers feedback from evaluator if information was insufficient
- Increments loop counter for iteration control

**Model:** `llama3` (via `get_planner_model()`)

**Output Validation:** Uses `Plan` Pydantic schema
```python
class Plan(BaseModel):
    queries: List[str] = Field(description="List of search queries")
```

### 2. Searcher
**File:** `src/nodes/searcher_node.py`

**Purpose:** Executes web searches via Tavily API

**Input:** Search queries from planner
**Output:** Web search results

**Behavior:**
- Executes each query against Tavily search API
- Aggregates results from multiple queries
- Handles errors gracefully

**API:** Tavily (configured via `TAVILY_API_KEY` environment variable)

### 3. RAG Retriever
**File:** `src/nodes/rag_retriever_node.py`

**Purpose:** Retrieves relevant chunks from ChromaDB knowledge base

**Input:** Search queries from planner
**Output:** Retrieved document chunks

**Behavior:**
- Embeds each query using `nomic-embed-text` model
- Performs semantic similarity search in ChromaDB
- Returns top 5 most relevant chunks per query
- Includes source metadata for provenance

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

### 4. Analyzer
**File:** `src/nodes/analyzer_node.py`

**Purpose:** Merges and summarizes results from both Searcher and RAG Retriever

**Input:**
- `search_results` from Tavily
- `rag_results` from ChromaDB

**Output:** Structured analysis combining both sources

**Behavior:**
- Combines web results and knowledge base chunks
- Extracts key insights and relevant information
- Summarizes findings for evaluation
- Prepares context for synthesizer

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
    plan: list[str]                                 # Current search queries
    search_results: Annotated[list[str], operator.add]  # Web results (accumulated)
    rag_results: Annotated[list[str], operator.add]     # KB results (accumulated)
    analyzed_data: Annotated[list[str], operator.add]   # Processed info (accumulated)
    report: str                                     # Final report
    evaluation: str                                 # Sufficiency assessment
    loop_count: int                                 # Iteration counter
```

**Key Pattern:** `Annotated[list[str], operator.add]` enables cumulative accumulation across iterations.

### Execution Flow

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Planner    │  ← Generates 3-5 search queries
└──────┬──────┘
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌─────────────┐        ┌─────────────┐
│  Searcher   │        │    RAG      │  ← Execute in PARALLEL
│  (Tavily)   │        │  Retriever  │
│             │        │  (ChromaDB) │
└──────┬──────┘        └──────┬──────┘
       │                      │
       └──────────┬───────────┘
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
  │ Synthesizer │    │  Planner    │ ← Refine with feedback
  │             │    │  (Loop)     │    (max 2 iterations)
  └──────┬──────┘    └─────────────┘
         │
         ▼
     Final Report
```

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

- `planner_prompt.py` - Query decomposition and planning
- `analyzer_prompt.py` - Result summarization
- `evaluator_prompt.py` - Sufficiency assessment
- `synthesizer_prompt.py` - Final report generation

**To customize:** Edit the `PromptTemplate` in each file.

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

**Key Takeaway:** The system combines real-time web search (Tavily) with local knowledge base retrieval (ChromaDB) in parallel, using iterative refinement to ensure comprehensive, high-quality research outputs.
