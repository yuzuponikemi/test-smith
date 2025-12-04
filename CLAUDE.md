# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Test-Smith is a **LangGraph-based multi-agent research assistant** that autonomously conducts deep research and generates comprehensive reports. It uses an advanced "Hierarchical Plan-and-Execute" strategy with **dynamic replanning** capabilities, featuring specialized agents that collaborate through a state-based workflow.

**Version:** v2.4 (Multi-Graph Architecture with 7 Specialized Workflows)

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

5. **causal_inference** - Root cause analysis and causal reasoning
   - Best for: Troubleshooting issues, incident investigation, understanding causality
   - Features: Hypothesis generation, evidence validation, causal graph, probability ranking
   - Complexity: Medium | Avg time: 60-90 seconds

6. **code_investigation** - Deep codebase analysis and investigation
   - Best for: Understanding code structure, finding dependencies, tracing data flow
   - Features: Dependency tracking, flow analysis, variable usage, architecture patterns
   - Complexity: Medium | Avg time: 45-90 seconds

7. **feature_dev** ⭐ NEW - Systematic feature development workflow
   - Best for: Building new features, complex implementations requiring planning
   - Features: 7-phase workflow (Discovery → Exploration → Clarification → Architecture → Implementation → Review → Summary)
   - Complexity: High | Avg time: 10-20 minutes
   - User interaction: High - multiple approval gates (questions, architecture choice, implementation approval, review)
   - Parallel agents: Yes (2 explorers, 3 architects, 3 reviewers)

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
python scripts/visualization/visualize_causal_graph.py causal_graph.json

# Opens an interactive HTML visualization showing:
# - Hypothesis nodes (color-coded by likelihood)
# - Symptom nodes
# - Causal relationships (edges with strength indicators)
```

#### Code Investigation Mode (v2.3 - Codebase Analysis) ⭐ NEW
For codebase research and understanding, uses a **5-node specialized workflow**:

1. **Code Query Analyzer** → Understands investigation scope and target elements
2. **Code Retriever** → Retrieves relevant code via RAG search
3. **Dependency Analyzer** → Tracks class/function dependencies (parallel)
4. **Code Flow Tracker** → Analyzes data/control flow (parallel)
5. **Code Investigation Synthesizer** → Generates comprehensive report

**Key Features:**
- **Intelligent Query Analysis:** Determines investigation type (dependency, flow, usage, architecture)
- **Dependency Tracking:** Import analysis, class inheritance, composition, function calls
- **Flow Analysis:** Data flow paths, control flow, variable usage
- **Multi-Language Support:** Python, C#, JavaScript, TypeScript, Java, Go, Rust
- **C# & Windows Forms Support:** Full support for .cs, .csproj, .sln, .resx, .xaml files

**Use Cases:**
- Understanding how a feature is implemented
- Finding all usages of a function or class
- Tracing dependencies between components
- Analyzing data flow through the codebase
- Architecture and design pattern analysis
- Refactoring impact assessment

**Usage:**
```bash
# Investigate code dependencies
python main.py run "What classes depend on AuthService?" --graph code_investigation

# Trace data flow
python main.py run "How does user input flow through the validation system?" --graph code_investigation

# Find function usages
python main.py run "Where is the calculate_total function used?" --graph code_investigation
```

**Testing the Code Investigation Graph:**
```bash
# Full test: ingest test-smith repo + run test queries
python scripts/testing/test_code_investigation.py

# Skip ingestion (use existing codebase_collection)
python scripts/testing/test_code_investigation.py --skip-ingest

# Run specific test
python scripts/testing/test_code_investigation.py --test dependency
python scripts/testing/test_code_investigation.py --test flow
python scripts/testing/test_code_investigation.py --test usage
python scripts/testing/test_code_investigation.py --test architecture
python scripts/testing/test_code_investigation.py --test implementation
```

**Ingest Your Own Codebase:**
```bash
# Ingest any repository
python scripts/ingest/ingest_codebase.py /path/to/your/repo

# With custom collection name
python scripts/ingest/ingest_codebase.py . --collection my_project_code

# Then query it
python main.py run "How does auth work?" --graph code_investigation
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

### LangGraph Studio (Visual Debugging)

LangGraph Studioを使用すると、グラフをビジュアルに確認・デバッグできます。

```bash
# ワンクリックで起動
./scripts/studio/start_studio.sh

# 停止
./scripts/studio/stop_studio.sh
# または Ctrl+C
```

**起動後のアクセス:**
- Studio UI: ブラウザが自動的に開きます
- API: `http://127.0.0.1:8123`
- Docs: `http://127.0.0.1:8123/docs`

**詳細ガイド:**
- **[scripts/studio/README.md](scripts/studio/README.md)** - スクリプト使用方法
- **[docs/STUDIO_GUIDE.md](docs/STUDIO_GUIDE.md)** - Studio機能の詳細

### Knowledge Base Ingestion

```bash
# RECOMMENDED: Production ingestion with intelligent preprocessing
python scripts/ingest/ingest_with_preprocessor.py

# With quality filtering (skip files with score < 0.5)
python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.5

# Diagnostic ingestion (use for debugging embedding issues)
python scripts/ingest/ingest_diagnostic.py

# Automated clean re-ingest with validation
./scripts/ingest/clean_and_reingest.sh
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

### Development Workflow

**IMPORTANT: Always run CI checks locally before considering implementation complete**

When you finish implementing a feature or fix, **automatically** run the following CI checks locally:

```bash
# Run all CI checks (same as GitHub Actions)
source .venv/bin/activate

# 1. Ruff linter
echo "=== Ruff Linter ==="
ruff check .

# 2. Ruff formatter
echo "=== Ruff Formatter ==="
ruff format --check .

# 3. Mypy type checker
echo "=== Mypy Type Checker ==="
mypy src --no-error-summary

# 4. Pytest
echo "=== Pytest ==="
python -m pytest -v --tb=short
```

**Auto-fix common issues:**
```bash
# Auto-fix linting errors
ruff check --fix .

# Auto-format code
ruff format .
```

**Why this matters:**
- Prevents CI failures in pull requests
- Catches issues early before pushing
- Maintains code quality standards
- Saves time by avoiding CI feedback loops

**When to run:**
- ✅ After completing any feature implementation
- ✅ After fixing bugs
- ✅ Before creating a commit
- ✅ When tests or linting might be affected by changes

### Project Structure

```
scripts/                         # Organized utility scripts
├── ingest/                      # Knowledge base ingestion
│   ├── ingest.py               # Basic document ingestion
│   ├── ingest_diagnostic.py    # Enhanced ingestion with diagnostics
│   ├── ingest_with_preprocessor.py # Production ingestion (recommended)
│   └── clean_and_reingest.sh   # Automated clean re-ingest
├── testing/                     # Test scripts
│   ├── test_gemini_models.py   # Google Gemini model tests
│   ├── test_langsmith_monitoring.py # LangSmith monitoring tests
│   ├── test_phase4_dynamic_replanning.py # Dynamic replanning tests
│   └── test_code_investigation.py # ⭐ NEW: Code investigation graph tests
├── utils/                       # Utility scripts
│   ├── switch_model_provider.py # Toggle Ollama/Gemini providers
│   ├── verify_model_provider.py # Verify current provider
│   ├── update_node_logging.py  # Update logging config
│   └── update_causal_nodes_logging.py # Update causal node logging
└── visualization/               # Visualization scripts
    ├── visualize_graphs.py     # Generate graph diagrams
    └── visualize_causal_graph.py # Interactive causal graph viz

evaluation/                      # Evaluation framework
├── evaluate_agent.py           # LangSmith evaluation runner
├── evaluators.py               # Heuristic + LLM evaluators
├── datasets/                    # Test datasets
└── results/                     # Evaluation results

src/
├── graphs/                      # ⭐ Multiple graph workflows
│   ├── __init__.py             # Graph registry system
│   ├── base_graph.py           # Base classes for building graphs
│   ├── deep_research_graph.py  # Hierarchical research workflow
│   ├── quick_research_graph.py # Fast single-pass workflow
│   ├── fact_check_graph.py     # Claim verification workflow
│   ├── comparative_graph.py    # Side-by-side comparison workflow
│   ├── causal_inference_graph.py # Root cause analysis workflow
│   └── code_investigation_graph.py # ⭐ NEW: Codebase analysis workflow
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
│   ├── issue_analyzer_node.py          # Causal inference nodes
│   ├── brainstormer_node.py
│   ├── evidence_planner_node.py
│   ├── causal_checker_node.py
│   ├── hypothesis_validator_node.py
│   ├── causal_graph_builder_node.py
│   ├── root_cause_synthesizer_node.py
│   ├── code_assistant_node.py          # Code retrieval and analysis
│   ├── code_query_analyzer_node.py     # ⭐ NEW: Code investigation nodes
│   ├── dependency_analyzer_node.py     # ⭐ NEW
│   ├── code_flow_tracker_node.py       # ⭐ NEW
│   └── code_investigation_synthesizer_node.py # ⭐ NEW
├── prompts/                     # LangChain prompt templates (reusable)
│   ├── planner_prompt.py
│   ├── analyzer_prompt.py
│   ├── evaluator_prompt.py
│   ├── synthesizer_prompt.py
│   ├── master_planner_prompt.py
│   ├── issue_analyzer_prompt.py         # Causal inference prompts
│   ├── brainstormer_prompt.py
│   ├── evidence_planner_prompt.py
│   ├── causal_checker_prompt.py
│   ├── hypothesis_validator_prompt.py
│   ├── root_cause_synthesizer_prompt.py
│   ├── code_assistant_prompt.py         # Code assistant prompts
│   └── code_investigation_prompts.py    # ⭐ NEW: Code investigation prompts
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
Edit parameters in `scripts/ingest/ingest_with_preprocessor.py`:
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
- Small sections in source docs → Follow `docs/knowledge-base/writing-docs.md`

**Solution:** Always use `scripts/ingest/ingest_with_preprocessor.py` for production ingestion.

## Configuration Files

**.env** (required for LangSmith + Web Search):
```bash
# LangSmith (monitoring/tracing)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="<langsmith-key>"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Web Search Providers (multiple providers with auto-fallback)
SEARCH_PROVIDER_PRIORITY="tavily,duckduckgo"  # Priority order
TAVILY_API_KEY="<tavily-key>"  # Optional: High-quality search (1,000/month free)
# BRAVE_API_KEY="<brave-key>"  # Optional: Alternative provider (2,000/month free)

# Model Provider
MODEL_PROVIDER="ollama"  # or "google" for Gemini
# GOOGLE_API_KEY="<google-key>"  # Required if MODEL_PROVIDER="google"
```

**Web Search Providers:**
- **Tavily** (推奨): High-quality search optimized for LLMs. Free tier: 1,000 searches/month. Requires API key.
- **DuckDuckGo** (無料): Free search with no API key required. Built-in fallback.
- **Brave Search** (オプション): Privacy-focused search. Free tier: 2,000 searches/month. (Coming soon)

**Auto-Fallback**: If Tavily fails (API limit reached, invalid key, etc.), system automatically falls back to DuckDuckGo.

**Health Check:**
```bash
python scripts/utils/check_search_providers.py
```

**詳細ガイド**: [docs/WEB_SEARCH_PROVIDERS.md](docs/WEB_SEARCH_PROVIDERS.md)

**Note:** `.env` is checked into git with actual keys (not best practice for production).

## Known Issues & Limitations

- **Max 2 iterations:** Hardcoded in router to prevent infinite loops
- **No test coverage:** pytest installed but no tests written yet
- **Print-based logging:** Use structured logging for production

## Additional Resources

**Documentation Entry Point:**
- **[docs/README.md](docs/README.md)** - Start here for all documentation

**Getting Started:**
- **docs/getting-started/installation.md** - Setup and dependencies
- **docs/getting-started/quick-start.md** - First query in 5 minutes
- **docs/getting-started/model-providers.md** - Ollama vs Gemini configuration

**Architecture:**
- **docs/architecture/system-overview.md** - Complete system architecture
- **docs/architecture/multi-graph-workflows.md** - Available workflow graphs

**Knowledge Base:**
- **docs/knowledge-base/rag-guide.md** - Complete RAG configuration guide
- **docs/knowledge-base/writing-docs.md** - Best practices for documentation
- **docs/knowledge-base/quality-evaluation.md** - Quality metrics and evaluation
- **docs/knowledge-base/preprocessor.md** - Document preprocessor usage

**Development:**
- **docs/development/evaluation-guide.md** - LangSmith evaluation framework
- **docs/development/logging-debugging.md** - Logging and debugging guide
- **docs/development/creating-graphs.md** - Building custom workflows
- **docs/development/ci-cd.md** - CI/CD integration

**Tools & Analysis:**
- **chroma_explorer.ipynb** - Interactive notebook for database analysis
- **scripts/ingest/ingest_with_preprocessor.py** - Production ingestion
- **scripts/visualization/visualize_graphs.py** - Graph diagram generation
- **evaluation/evaluate_agent.py** - LangSmith evaluation runner

---

# 🧠 Cognitive Extension Protocol (Personal Assistant Settings)

## Core Identity & Mission
Claude Code acts as an **extension of the user's cognition** when working with this codebase.
Prioritize as a **Senior Software Architect**:

1. **Cognitive Clarity**: Reduce cognitive load - explain *why*, not just *what*
2. **Scalability**: Prefer robust, scalable solutions over quick hacks (unless prototyping)
3. **Context Awareness**: Always infer the broader goal from code changes

## Guidelines
- **Language**: Read in any language, but **reply in Japanese** unless asked otherwise
- **Output Format**: Use Markdown. When summarizing, use bullet points for readability
- **Tool Usage**: Full access to `gh` (GitHub CLI) and standard Unix tools

## ⚡ Custom Commands

### `/comp-pr [id1] [id2]` - Compare Pull Requests
**Goal**: Act as a neutral referee to compare two implementations

**Steps**:
1. Run `gh pr view [id1]` and `gh pr view [id2]` to get descriptions
2. Run `gh pr diff [id1]` and `gh pr diff [id2]` to get code changes
3. Analyze based on:
   - **Architectural Fit**: Which fits the current system design better?
   - **Complexity**: Which is simpler to maintain?
   - **Edge Cases**: Did anyone miss error handling?
4. **Output**: Generate a comparison table and a final recommendation ("Adopt PR A but borrow X from PR B")

**Example**:
```
User: /comp-pr 5 7
Claude: [Fetches both PRs, analyzes diffs, generates comparison table]
```

### `/review` - Deep Code Review
**Goal**: Perform a security and quality audit on current changes

**Steps**:
1. Run `git diff --staged` (or currently modified files)
2. Check for:
   - Security vulnerabilities (secrets, injection risks)
   - Performance bottlenecks (N+1 queries, heavy loops)
   - Naming consistency
3. **Output**: A prioritized list of issues (Critical / Warning / Suggestion)

**Example**:
```
User: /review
Claude:
Critical:
  - line 45: API key exposed in config
Warning:
  - line 120: N+1 query in loop
Suggestion:
  - line 67: Consider using more descriptive variable name
```

### `/commit` - Smart Commit Message
**Goal**: Generate a conventional commit message based on changes

**Steps**:
1. Analyze `git diff --staged`
2. Generate a commit message following **Conventional Commits** format:
   - `feat: ...` for new features
   - `fix: ...` for bug fixes
   - `refactor: ...` for code restructuring
   - `docs: ...` for documentation
3. Wait for user approval before running `git commit`

**Example**:
```
User: /commit
Claude:
Proposed commit message:
feat(code-investigation): Add multi-repository comparison support

- Add comparison mode to code investigation graph
- Update synthesizer to use comparison-specific prompts
- Support --collections flag for multi-repo queries

Proceed with this commit? (yes/no)
```

### `/obsidian` - Knowledge Sync
**Goal**: Summarize the current session for the user's Obsidian notes

**Steps**:
1. Review the conversation and code changes
2. Output a Markdown block containing:
   - **Topic**: 1-line summary
   - **Key Decisions**: What was decided and why
   - **Questions for Later**: Philosophical or technical questions sparked by this session

**Example Output**:
```markdown
## Session: Multi-Repository Code Comparison Implementation

**Topic**: Added multi-repo comparison to code investigation workflow

**Key Decisions**:
- Use separate ChromaDB collections per repository for isolation
- Implement comparison mode via `--collections` flag
- Create specialized comparison prompt for synthesizer
- Registry tracks all ingested repositories

**Questions for Later**:
- Should we support comparison of 3+ repositories?
- How to handle different embedding models across collections?
- Could we auto-detect related codebases based on dependencies?

**Files Modified**:
- src/graphs/code_investigation_graph.py
- src/nodes/code_investigation_synthesizer_node.py
- main.py
- docs/CODEBASE_MANAGEMENT.md
```

## 🚀 Prototyping Modes (User Preference)

### Small Task
Provide a single Python script or Jupyter Notebook snippet

### Medium Task
Provide an "Implementation Design Spec" before coding:
```markdown
## Design Spec: [Feature Name]

**Goal**: [1-sentence objective]

**Approach**:
1. [High-level step 1]
2. [High-level step 2]

**Files to Modify**:
- file1.py: [what changes]
- file2.py: [what changes]

**Trade-offs**:
- Option A: [pros/cons]
- Option B: [pros/cons]

**Recommendation**: Option B because [reasoning]
```

### Large Task
Provide a Roadmap with Tech Stack choices first:
```markdown
## Roadmap: [Project Name]

**Phase 1**: Foundation
- [ ] Database schema design
- [ ] API structure
- [ ] Authentication layer

**Phase 2**: Core Features
- [ ] Feature X
- [ ] Feature Y

**Tech Stack Choices**:
- DB: PostgreSQL vs MongoDB
  - Recommendation: PostgreSQL (reasoning...)
- API: REST vs GraphQL
  - Recommendation: REST (reasoning...)
```

---

## GitHub PR Comparison Example

To try the `/comp-pr` command with this repository:

```bash
# List recent PRs
gh pr list

# Compare two PRs
# Usage: /comp-pr [pr-number-1] [pr-number-2]
```

The comparison will analyze:
- Code changes and architectural impact
- Complexity and maintainability
- Test coverage and edge cases
- Which approach better fits Test-Smith's multi-graph architecture
