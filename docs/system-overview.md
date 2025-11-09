
# Test-Smith: LangGraph Agent System Overview

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Software Structure](#software-structure)
3. [Configuration Concepts](#configuration-concepts)
4. [User Interface](#user-interface)
5. [Data Flow](#data-flow)
6. [Development Setup](#development-setup)
7. [Customization Guide](#customization-guide)

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
├── main.py                 # Entry point and CLI interface
├── requirements.in         # High-level dependencies
├── requirements.txt        # Compiled dependencies (auto-generated)
├── README.md              # Project overview
├── docs/                  # Documentation
│   ├── agent_graph.md     # Agent workflow documentation
│   └── system-overview.md # This file
└── src/                   # Source code
    ├── __init__.py
    ├── graph.py           # Main workflow graph definition
    ├── models.py          # AI model configurations
    ├── schemas.py         # Pydantic data schemas
    ├── nodes/             # Individual processing nodes
    │   ├── __init__.py
    │   ├── planner_node.py
    │   ├── searcher_node.py
    │   ├── analyzer_node.py
    │   ├── evaluator_node.py
    │   └── synthesizer_node.py
    └── prompts/           # AI prompts for each node
        ├── __init__.py
        ├── planner_prompt.py
        ├── analyzer_prompt.py
        ├── evaluator_prompt.py
        └── synthesizer_prompt.py
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