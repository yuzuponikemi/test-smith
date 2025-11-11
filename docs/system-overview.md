
# Test-Smith: LangGraph Agent System Overview

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Software Structure](#software-structure)
3. [Knowledge Base & Preprocessing](#knowledge-base--preprocessing)
4. [Configuration Concepts](#configuration-concepts)
5. [User Interface](#user-interface)
6. [Data Flow](#data-flow)
7. [Development Setup](#development-setup)
8. [Customization Guide](#customization-guide)

## System Architecture

Test-Smith is a LangGraph-based AI agent system designed for research and information synthesis. The system implements a multi-step workflow that combines planning, searching, analysis, evaluation, and synthesis to answer complex queries.

### Core Concepts

- **Agent Graph**: A state-based workflow engine using LangGraph
- **Node-based Processing**: Each step is implemented as a discrete node
- **State Management**: Persistent state across execution steps
- **Model Abstraction**: Configurable AI models for different tasks
- **Memory Management**: SQLite-based checkpointing for conversation continuity

## Software Structure

### Directory Organization

```
test-smith/
├── main.py                      # Entry point and CLI interface
├── requirements.in              # High-level dependencies
├── requirements.txt             # Compiled dependencies (auto-generated)
├── README.md                    # Project overview
├── ingest_with_preprocessor.py  # Production ingestion with preprocessing
├── ingest_diagnostic.py         # Diagnostic ingestion for debugging
├── clean_and_reingest.sh        # Automated clean re-ingest script
├── chroma_explorer.ipynb        # Interactive database analysis notebook
├── PREPROCESSOR_QUICKSTART.md   # Quick start guide for preprocessing
├── docs/                        # Documentation
│   ├── agent_graph.md           # Agent workflow documentation
│   ├── system-overview.md       # This file
│   ├── RAG_DATA_PREPARATION_GUIDE.md              # Comprehensive RAG guide
│   ├── WRITING_RAG_FRIENDLY_DOCUMENTATION.md      # Writing best practices
│   └── DOCUMENT_DESIGN_EVALUATION.md              # Evaluation metrics
├── src/                         # Source code
│   ├── __init__.py
│   ├── graph.py                 # Main workflow graph definition
│   ├── models.py                # AI model configurations
│   ├── schemas.py               # Pydantic data schemas
│   ├── nodes/                   # Individual processing nodes
│   │   ├── __init__.py
│   │   ├── planner_node.py
│   │   ├── searcher_node.py
│   │   ├── rag_retriever_node.py
│   │   ├── analyzer_node.py
│   │   ├── evaluator_node.py
│   │   └── synthesizer_node.py
│   ├── prompts/                 # AI prompts for each node
│   │   ├── __init__.py
│   │   ├── planner_prompt.py
│   │   ├── analyzer_prompt.py
│   │   ├── evaluator_prompt.py
│   │   └── synthesizer_prompt.py
│   └── preprocessor/            # Document preprocessing system
│       ├── __init__.py
│       ├── document_analyzer.py
│       ├── chunking_strategy.py
│       ├── content_cleaner.py
│       └── quality_metrics.py
├── documents/                   # Source documents for RAG (gitignored)
└── chroma_db/                   # ChromaDB vector store (gitignored)
```

### Core Components

#### 1. Graph Definition (`src/graph.py`)
- **AgentState**: TypedDict defining the workflow state structure
- **Workflow Nodes**: Planner, Searcher, Analyzer, Evaluator, Synthesizer
- **Router Logic**: Conditional routing based on evaluation results
- **Loop Control**: Maximum iteration limits to prevent infinite loops

#### 2. Processing Nodes (`src/nodes/`)

**Planner Node** (`planner_node.py`)
- Generates search queries based on user input
- Uses structured output with Pydantic validation
- Handles feedback from previous iterations
- Increments loop counter for iteration control

**Searcher Node** (`searcher_node.py`)
- Executes web searches using DuckDuckGo
- Processes multiple queries in sequence
- Aggregates search results for analysis

**Analyzer Node** (`analyzer_node.py`)
- Processes and summarizes search results
- Extracts relevant information from web content
- Prepares data for evaluation

**Evaluator Node** (`evaluator_node.py`)
- Assesses information sufficiency
- Determines if additional research is needed
- Controls workflow continuation or termination

**Synthesizer Node** (`synthesizer_node.py`)
- Creates final comprehensive reports
- Combines all analyzed information
- Produces user-ready output

#### 3. AI Model Management (`src/models.py`)
- **Model Factory Functions**: Centralized model configuration
- **Provider Abstraction**: Easy switching between AI providers
- **Role-specific Models**: Different models for different tasks
- **Default Configuration**: Ollama-based local models

#### 4. Data Schemas (`src/schemas.py`)
- **Plan Schema**: Validates search query lists
- **Evaluation Schema**: Ensures structured evaluation output
- **Type Safety**: Pydantic-based validation
- **Documentation**: Field descriptions for clarity

## Knowledge Base & Preprocessing

### RAG (Retrieval-Augmented Generation) System

Test-Smith uses a sophisticated RAG system to augment agent responses with domain-specific knowledge:

**Components:**
- **Document Storage**: `documents/` directory for source materials
- **Vector Database**: ChromaDB for semantic search
- **Embedding Model**: nomic-embed-text (768 dimensions)
- **Retriever Node**: `rag_retriever_node.py` fetches relevant chunks

### Intelligent Document Preprocessing

The system includes a comprehensive preprocessing pipeline (`src/preprocessor/`) that ensures high-quality embeddings:

#### Document Analyzer (`document_analyzer.py`)

**Purpose**: Evaluates document quality before ingestion

**Capabilities:**
- File size and format detection
- Language identification (English, Japanese, etc.)
- Structure analysis (markdown, PDF, plain text)
- Quality scoring (0-1 scale)
- Issue detection and recommendations

**Quality Factors:**
- File size appropriateness
- Content length
- Language consistency
- Structure complexity

#### Chunking Strategy Selector (`chunking_strategy.py`)

**Purpose**: Selects optimal chunking method per document

**Available Strategies:**
- **Recursive**: General-purpose text splitting
- **Markdown Headers**: Structure-aware splitting for markdown
- **Hybrid**: Combines multiple strategies

**Selection Logic:**
- **Document structure**: Markdown vs plain text
- **File size**: Larger chunks for big files
- **Language**: Adjusted sizes for Japanese (1.2x)
- **Complexity**: Special handling for tables/code

**Configuration:**
```python
@dataclass
class ChunkingConfig:
    method: ChunkingMethod
    chunk_size: int           # Target: 500-1000 chars
    chunk_overlap: int        # Overlap for context
    min_chunk_size: int       # Filter tiny chunks
```

#### Content Cleaner (`content_cleaner.py`)

**Purpose**: Removes duplicates and cleans content

**Cleaning Operations:**
1. **Exact Duplicate Removal**: MD5 hash-based deduplication
2. **Near-Duplicate Detection**: SequenceMatcher similarity (95% threshold)
3. **Boilerplate Removal**: Detects repeated patterns (headers, footers)
4. **Size Filtering**: Removes chunks < minimum length
5. **Content Normalization**: Whitespace and formatting cleanup

**Statistics Tracked:**
- Exact duplicates removed
- Near duplicates removed
- Boilerplate patterns detected
- Chunks filtered by size
- Overall removal rate

#### Quality Metrics (`quality_metrics.py`)

**Purpose**: Validates preprocessing results

**Calculated Metrics:**
- **Chunk Size Distribution**: very_small, small, medium, large, very_large
- **Median/Mean Chunk Size**: Target 500-800 characters
- **Uniqueness Ratio**: Percentage of unique chunks (target >95%)
- **Vocabulary Diversity**: Unique words / total words (target 25-50%)
- **Quality Score**: Composite score 0-1 (target >0.7)

**Quality Grades:**
- Excellent (0.9+)
- Good (0.75-0.89)
- Fair (0.6-0.74)
- Poor (0.4-0.59)
- Very Poor (<0.4)

### Ingestion Workflows

#### Production Ingestion: `ingest_with_preprocessor.py`

**Recommended for all document ingestion**

**6-Phase Pipeline:**

1. **Document Analysis Phase**
   - Analyzes all files in `documents/`
   - Generates quality reports
   - Filters low-quality files (optional threshold)

2. **Embedding Model Setup**
   - Initializes Ollama embeddings
   - Tests model connectivity
   - Configures vector store

3. **Document Processing & Chunking**
   - Loads documents with UnstructuredLoader
   - Selects chunking strategy per document
   - Creates chunks with metadata

4. **Content Cleaning & Deduplication**
   - Removes exact and near-duplicates
   - Filters boilerplate content
   - Validates chunk sizes

5. **Quality Metrics Calculation**
   - Calculates comprehensive quality metrics
   - Generates quality reports
   - Provides actionable recommendations

6. **Vector Store Ingestion**
   - Batch processing (100 chunks/batch)
   - Error handling and retry logic
   - Ingestion statistics

**Usage:**
```bash
# Standard ingestion
python ingest_with_preprocessor.py

# With quality filtering
python ingest_with_preprocessor.py --min-quality 0.5

# Skip analysis for speed
python ingest_with_preprocessor.py --skip-analysis

# Disable specific cleaning steps
python ingest_with_preprocessor.py --disable-deduplication
python ingest_with_preprocessor.py --disable-boilerplate
```

#### Diagnostic Ingestion: `ingest_diagnostic.py`

**Use for debugging embedding issues**

**Features:**
- Real-time duplicate detection
- Sample embedding generation
- Similarity analysis
- Detailed logging per file
- Embedding quality validation

**When to use:**
- Investigating poor retrieval quality
- Debugging "all embeddings similar" issues
- Validating preprocessing changes
- Understanding chunk distribution

#### Automated Clean Re-ingest: `clean_and_reingest.sh`

**Complete database refresh workflow**

**Steps:**
1. Backs up existing `chroma_db/` with timestamp
2. Checks Ollama service status
3. Verifies embedding model availability
4. Activates virtual environment
5. Runs diagnostic ingestion
6. Generates detailed logs

**Usage:**
```bash
./clean_and_reingest.sh
```

### Database Analysis Tools

#### ChromaDB Explorer Notebook (`chroma_explorer.ipynb`)

**Interactive analysis and visualization**

**Key Sections:**

**Section 1: Basic Exploration**
- Collection statistics
- Document count and sources
- Metadata inspection

**Section 2: Data Quality Analysis**
- Section 2.1: Database content breakdown
- Section 2.2: Embedding quality diagnostics
  - Duplicate detection
  - Diversity analysis
  - Pairwise similarity
  - Visual diagnostics

**Section 3: PCA Variance Analysis**
- Section 3.0: Variance explained by components
- Section 3.1: Interactive 2D visualization
- Section 3.2: Interactive 4D pair plots

**Healthy Embedding Indicators:**
- Median chunk size: 500-800 characters
- Duplication rate: <5%
- Quality score: >0.7
- PCA components for 95% variance: 20-40
- Mean cosine similarity: 0.3-0.8

**Problematic Indicators:**
- Median chunk size: <200 characters (chunks too small)
- Duplication rate: >15% (too much repetition)
- Quality score: <0.5 (poor quality)
- PCA components for 99% variance: <10 (lack of diversity)
- Mean similarity: >0.95 (everything looks the same)

### Documentation Quality Best Practices

The system includes comprehensive guides for creating RAG-friendly documentation:

#### RAG Data Preparation Guide (`RAG_DATA_PREPARATION_GUIDE.md`)

**Comprehensive 400+ line guide covering:**
- Why data quality matters
- Complete RAG pipeline explanation
- Document preprocessing fundamentals
- Chunking strategies (Fixed-size, Semantic, Hybrid)
- Embedding quality assessment
- Common pitfalls and solutions
- Best practices checklist

#### Writing RAG-Friendly Documentation (`WRITING_RAG_FRIENDLY_DOCUMENTATION.md`)

**Best practices for document authors:**
- Self-contained information blocks
- Optimal section lengths (500-1500 chars)
- Header naming conventions
- Handling aliases and synonyms
- Cross-referencing strategies
- Terminology consistency
- Anti-patterns to avoid

**Key Principles:**
- Each section should be understandable independently
- Include main topic in every header
- Use consistent terminology
- Define acronyms on first use
- Provide context in cross-references

#### Document Design Evaluation (`DOCUMENT_DESIGN_EVALUATION.md`)

**Reproducible metrics for documentation quality:**

**Automated Metrics:**
- Chunk size distribution
- Median chunk size
- Duplication rate
- Quality score
- Vocabulary diversity
- Uniqueness ratio
- PCA variance components

**Manual Evaluation Checklists:**
- Section independence
- Term consistency
- Header descriptiveness
- Acronym definition
- Cross-reference quality

**Scoring System:**
- Overall document design score (0-100)
- Grade scale (A+ to F)
- Action items per grade level

**Continuous Improvement:**
- Monthly evaluation cycle
- Progress tracking
- 90-day improvement plans
- Troubleshooting guides

### Best Practices for Knowledge Base Management

1. **Document Preparation**
   - Read `WRITING_RAG_FRIENDLY_DOCUMENTATION.md` before creating docs
   - Target 500-1500 characters per section
   - Use descriptive headers with topic names
   - Define all acronyms on first use

2. **Quality Evaluation**
   - Run `python ingest_with_preprocessor.py` for all ingestion
   - Review quality metrics in logs
   - Check PCA analysis in `chroma_explorer.ipynb`
   - Follow evaluation workflow monthly

3. **Continuous Monitoring**
   - Track quality scores over time
   - Identify problematic documents
   - Improve based on metrics
   - Re-evaluate after changes

4. **Troubleshooting**
   - Median chunk size too small → Expand sections
   - High duplication → Remove boilerplate
   - Low vocabulary diversity → Add varied examples
   - Poor PCA components → Fix chunk sizes and duplication

## Configuration Concepts

### Environment Configuration

The system uses environment variables for configuration:

```bash
# AI Model Configuration
OLLAMA_BASE_URL=http://localhost:11434
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_TRACING=true

# Search Configuration
DUCKDUCKGO_REGION=en-us
```

### Model Configuration

Models are configured in `src/models.py`:

```python
def get_planner_model():
    return ChatOllama(model="llama3")

def get_evaluation_model():
    return ChatOllama(model="command-r")
```

**Configuration Options:**
- **Model Provider**: Ollama (local), OpenAI, Anthropic, etc.
- **Model Selection**: Different models for different tasks
- **Parameters**: Temperature, max tokens, etc.
- **Fallback Models**: Error handling and alternatives

### Prompt Configuration

Each node has configurable prompts in `src/prompts/`:

- **Template-based**: Using LangChain PromptTemplate
- **Variable Injection**: Dynamic content insertion
- **Format Instructions**: Pydantic schema integration
- **Feedback Integration**: Iterative improvement support

### Workflow Configuration

**Loop Control:**
- Maximum iterations: 2 (configurable in router)
- Early termination: Based on evaluation results
- State persistence: SQLite checkpointing

**Node Routing:**
- Conditional edges based on evaluation
- Deterministic flow control
- Error handling and recovery

## User Interface

### Command Line Interface

The system provides a CLI through `main.py`:

```bash
# Basic usage
python main.py run "Your research question here"

# With thread continuity
python main.py run "Follow-up question" --thread-id abc-123

# Version information
python main.py --version
```

**CLI Features:**
- **Streaming Output**: Real-time node execution results
- **Thread Management**: Conversation continuity
- **Error Handling**: Graceful failure management
- **Progress Indicators**: Node execution tracking

### Output Format

The system provides structured output:

```
Running the LangGraph agent...
Output from node 'planner':
---
{'plan': ['query1', 'query2'], 'loop_count': 1}

Output from node 'searcher':
---
{'search_results': ['result1', 'result2']}

---
```

### State Visibility

Users can observe:
- **Current Node**: Which processing step is active
- **State Changes**: How data flows between nodes
- **Loop Progress**: Iteration count and continuation logic
- **Final Output**: Comprehensive research report

## Data Flow

### 1. Input Processing
```
User Query → Planner → Search Queries
```

### 2. Information Gathering
```
Search Queries → Searcher → Raw Search Results
```

### 3. Analysis Phase
```
Raw Results → Analyzer → Structured Analysis
```

### 4. Evaluation Loop
```
Analysis → Evaluator → Sufficiency Decision
├─ Sufficient → Synthesizer → Final Report
└─ Insufficient → Planner (with feedback)
```

### 5. State Management
```
SQLite Checkpointer ↔ Agent State ↔ Thread Continuity
```

### State Structure

```python
class AgentState(TypedDict):
    query: str                      # Original user query
    plan: list[str]                 # Current search plan
    search_results: list[str]       # Accumulated search results
    analyzed_data: list[str]        # Processed information
    report: str                     # Final synthesis
    evaluation: str                 # Sufficiency assessment
    loop_count: int                 # Iteration counter
```

## Development Setup

### Dependencies

**Core Framework:**
- `langgraph`: Workflow engine
- `langchain-core`: LLM abstractions
- `langchain-community`: Community tools
- `langchain-ollama`: Local model support

**Search & Data:**
- `duckduckgo-search`: Web search capability
- `SQLAlchemy`: Database management
- `langgraph-checkpoint-sqlite`: State persistence

**Development:**
- `pytest`: Testing framework
- `python-dotenv`: Environment management
- `pydantic`: Data validation

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv
uv pip install -r requirements.in
```

### Local Model Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3
ollama pull command-r
```

## Customization Guide

### Adding New Nodes

1. **Create Node File**: `src/nodes/my_node.py`
2. **Implement Function**: `def my_node(state): ...`
3. **Update Graph**: Add node to `src/graph.py`
4. **Add Prompt**: Create `src/prompts/my_prompt.py`
5. **Configure Model**: Add model function to `src/models.py`

### Modifying Workflow

**Add Conditional Logic:**
```python
def custom_router(state):
    if condition:
        return "node_a"
    else:
        return "node_b"

workflow.add_conditional_edges(
    "source_node",
    custom_router,
    {"node_a": "node_a", "node_b": "node_b"}
)
```

**Parallel Processing:**
```python
workflow.add_edge("source", "parallel_1")
workflow.add_edge("source", "parallel_2")
workflow.add_edge("parallel_1", "merger")
workflow.add_edge("parallel_2", "merger")
```

### Custom Models

**External Provider:**
```python
from langchain_openai import ChatOpenAI

def get_custom_model():
    return ChatOpenAI(
        model="gpt-4",
        temperature=0.1,
        max_tokens=1000
    )
```

**Model Parameters:**
```python
def get_specialized_model():
    return ChatOllama(
        model="llama3",
        temperature=0.7,
        num_predict=500,
        top_p=0.9
    )
```

### Advanced Configuration

**Custom State Schema:**
```python
class ExtendedState(AgentState):
    custom_field: str
    metadata: dict
    confidence_score: float
```

**Error Handling:**
```python
def robust_node(state):
    try:
        return process_state(state)
    except Exception as e:
        return {"error": str(e), "fallback": True}
```

**Monitoring Integration:**
```python
from langsmith import traceable

@traceable
def monitored_node(state):
    # Node implementation with automatic tracing
    return result
```

This system architecture provides a flexible, extensible framework for building complex AI workflows while maintaining clear separation of concerns and easy customization options.