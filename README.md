# Test-Smith: Multi-Agent Research Assistant

A sophisticated LangGraph-based research assistant that combines multi-agent workflows with intelligent knowledge base management for deep research and comprehensive report generation.

## Overview

Test-Smith implements a "Plan-and-Execute" strategy with specialized AI agents collaborating through a state-based workflow. The system combines:

- **Multi-Agent Architecture**: Planner, Searcher, RAG Retriever, Analyzer, Evaluator, and Synthesizer
- **Intelligent Knowledge Base**: ChromaDB vector store with advanced preprocessing
- **Quality-First Approach**: Comprehensive document quality analysis and metrics
- **Local LLMs**: Powered by Ollama (llama3, command-r, nomic-embed-text)
- **Observability**: Full tracing via LangSmith

## Key Features

### Multi-Agent Workflow

1. **Planner** - Decomposes user queries into targeted search strategies
2. **Searcher** - Executes web searches via Tavily API
3. **RAG Retriever** - Retrieves relevant chunks from knowledge base
4. **Analyzer** - Merges and summarizes results from multiple sources
5. **Evaluator** - Assesses information sufficiency and quality
6. **Synthesizer** - Generates comprehensive final reports

The system executes iteratively (max 2 iterations) with conditional routing based on evaluation results.

### Intelligent Document Preprocessing

The knowledge base system includes a sophisticated preprocessing pipeline:

**Document Analyzer:**
- Quality scoring (0-1 scale)
- Language detection (English, Japanese, etc.)
- Structure analysis (Markdown, PDF, plain text)
- Automatic issue detection and recommendations

**Smart Chunking:**
- Strategy selection per document (Recursive, Markdown, Hybrid)
- Adaptive chunk sizing based on content type
- Language-aware adjustments (e.g., 1.2x for Japanese)
- Target: 500-1000 characters per chunk

**Content Cleaning:**
- Exact duplicate removal (MD5 hash-based)
- Near-duplicate detection (95% similarity threshold)
- Boilerplate pattern removal (repeated headers/footers)
- Size filtering (removes chunks < 100 chars)

**Quality Metrics:**
- Chunk size distribution analysis
- Uniqueness ratio tracking (target >95%)
- Vocabulary diversity measurement (target 25-50%)
- PCA variance analysis for embedding quality

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai/)
3. **Required Models:**
   ```bash
   ollama pull llama3
   ollama pull command-r
   ollama pull nomic-embed-text
   ```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd test-smith

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```bash
# LangSmith (for observability)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-api-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Tavily (for web search)
TAVILY_API_KEY="your-tavily-api-key"
```

## Usage

### Running Research Queries

```bash
# Basic research query
python main.py run "What are the latest advancements in AI-powered drug discovery?"

# Continue conversation with thread ID
python main.py run "Follow-up question" --thread-id abc-123

# Check version
python main.py --version
```

### Knowledge Base Management

#### Ingesting Documents

**Production Ingestion (Recommended):**
```bash
# Place documents in documents/ directory
# Run intelligent preprocessing pipeline
python ingest_with_preprocessor.py

# With quality filtering (skip files with score < 0.5)
python ingest_with_preprocessor.py --min-quality 0.5

# Disable specific cleaning steps if needed
python ingest_with_preprocessor.py --disable-deduplication
```

**Diagnostic Ingestion (For Debugging):**
```bash
# Use for investigating embedding issues
python ingest_diagnostic.py
```

**Automated Clean Re-ingest:**
```bash
# Backs up existing database and re-ingests
./clean_and_reingest.sh
```

#### Analyzing Your Knowledge Base

```bash
# Launch Jupyter notebook for interactive analysis
jupyter notebook chroma_explorer.ipynb
```

**Key Notebook Sections:**
- **Section 2.1**: Database content breakdown (sources, chunk counts)
- **Section 2.2**: Embedding quality diagnostics (duplicates, diversity)
- **Section 3.0**: PCA variance analysis (dimensionality check)
- **Section 3.1**: Interactive 2D visualization with hover tooltips
- **Section 3.2**: Interactive 4D pair plots

**Healthy Knowledge Base Indicators:**
- Median chunk size: 500-800 characters
- Duplication rate: <5%
- Quality score: >0.7
- PCA components for 95% variance: 20-40

## Creating RAG-Friendly Documentation

To maximize retrieval quality, follow these best practices when creating knowledge base documents:

### Key Principles

1. **Self-Contained Sections** - Each section should make sense independently
2. **Optimal Length** - Target 500-1500 characters per section
3. **Descriptive Headers** - Include main topic in every header
4. **Consistent Terminology** - Use same terms for same concepts
5. **Define Acronyms** - Use "Full Term (Acronym)" pattern on first use

### Example: Poor vs Good

❌ **Poor - RAG-Unfriendly:**
```markdown
## Configuration

Edit the config file. Set the parameters.
```
- Too short (no context)
- Generic header
- Vague references

✅ **Good - RAG-Friendly:**
```markdown
## PostgreSQL Connection Configuration

Configure PostgreSQL database connection settings in the
postgresql.conf file located at /etc/postgresql/14/main/postgresql.conf.

Key settings to configure:
- listen_addresses: Set to '0.0.0.0' for remote connections
- port: Default PostgreSQL port is 5432
- max_connections: Maximum concurrent connections (default: 100)

Restart PostgreSQL after changes: sudo systemctl restart postgresql
```
- Adequate length (self-explanatory)
- Topic-specific header
- Complete, standalone information

### Documentation Guides

- **[Writing RAG-Friendly Documentation](docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md)** - Comprehensive writing best practices
- **[Document Design Evaluation](docs/DOCUMENT_DESIGN_EVALUATION.md)** - Reproducible quality metrics
- **[RAG Data Preparation Guide](docs/RAG_DATA_PREPARATION_GUIDE.md)** - Deep dive into RAG concepts

## Project Structure

```
test-smith/
├── main.py                          # Entry point and CLI
├── ingest_with_preprocessor.py      # Production ingestion
├── ingest_diagnostic.py             # Diagnostic ingestion
├── clean_and_reingest.sh            # Automated re-ingest
├── chroma_explorer.ipynb            # Analysis notebook
├── PREPROCESSOR_QUICKSTART.md       # Quick start guide
├── docs/                            # Documentation
│   ├── system-overview.md           # Architecture deep dive
│   ├── RAG_DATA_PREPARATION_GUIDE.md
│   ├── WRITING_RAG_FRIENDLY_DOCUMENTATION.md
│   └── DOCUMENT_DESIGN_EVALUATION.md
├── src/                             # Source code
│   ├── graph.py                     # Workflow definition
│   ├── models.py                    # LLM configurations
│   ├── schemas.py                   # Data schemas
│   ├── nodes/                       # Agent nodes
│   │   ├── planner_node.py
│   │   ├── searcher_node.py
│   │   ├── rag_retriever_node.py
│   │   ├── analyzer_node.py
│   │   ├── evaluator_node.py
│   │   └── synthesizer_node.py
│   ├── prompts/                     # Prompt templates
│   │   ├── planner_prompt.py
│   │   ├── analyzer_prompt.py
│   │   ├── evaluator_prompt.py
│   │   └── synthesizer_prompt.py
│   └── preprocessor/                # Preprocessing pipeline
│       ├── document_analyzer.py     # Quality analysis
│       ├── chunking_strategy.py     # Smart chunking
│       ├── content_cleaner.py       # Deduplication
│       └── quality_metrics.py       # Validation
├── documents/                       # Source documents (gitignored)
└── chroma_db/                       # Vector database (gitignored)
```

## Monitoring & Observability

### LangSmith Tracing

1. Navigate to your LangSmith dashboard
2. Select project "deep-research-v1-proto"
3. View detailed execution traces:
   - Node-by-node execution flow
   - Input/output for each agent
   - Token usage and latency
   - Error tracking

### Knowledge Base Quality Monitoring

**Check After Each Ingestion:**

```bash
# Review ingestion log
cat ingestion_preprocessed_*.log

# Look for these sections:
# - DOCUMENT ANALYSIS REPORT (quality scores)
# - CHUNKING STATISTICS (chunk distribution)
# - CONTENT CLEANING STATISTICS (duplication rates)
# - QUALITY METRICS REPORT (overall quality score)
```

**Monthly Evaluation:**

1. Run ingestion: `python ingest_with_preprocessor.py`
2. Extract metrics from log file
3. Run PCA analysis in notebook (Section 3.0)
4. Record scores and track progress
5. Identify and fix weak areas

## Customization

### Changing LLMs

Edit `src/models.py`:

```python
def get_planner_model():
    return ChatOllama(model="llama3")  # Change model here

def get_evaluation_model():
    return ChatOllama(model="command-r")
```

### Modifying Agents

Edit prompts in `src/prompts/`:

```python
# src/prompts/planner_prompt.py
PLANNER_PROMPT = PromptTemplate(
    template="Your custom prompt here...",
    input_variables=["query", "feedback"]
)
```

### Tuning Preprocessing

Edit `ingest_with_preprocessor.py`:

```python
ingestion = PreprocessedIngestion(
    min_quality_score=0.5,              # Quality threshold
    enable_near_duplicate_detection=True,
    enable_boilerplate_removal=True
)

cleaner = ContentCleaner(
    similarity_threshold=0.95,          # Near-duplicate threshold
    min_content_length=100              # Minimum chunk size
)
```

## Troubleshooting

### Poor Retrieval Quality

**Symptoms:**
- RAG retriever returns irrelevant chunks
- Answers lack domain-specific knowledge
- Same chunks retrieved for different queries

**Diagnosis:**
```bash
# Run diagnostic ingestion
python ingest_diagnostic.py

# Check logs for:
# - High duplication rate (>15%)
# - Small median chunk size (<300 chars)
# - Low quality score (<0.5)
```

**Solutions:**
1. Review source documents (follow `WRITING_RAG_FRIENDLY_DOCUMENTATION.md`)
2. Re-ingest with preprocessor: `./clean_and_reingest.sh`
3. Check PCA analysis in notebook - should need 20-40 components for 95% variance

### "All Embeddings Look Similar" Issue

**Symptoms:**
- PCA shows 1-10 components for 99% variance
- Visualizations show all points clustered together
- Mean cosine similarity >0.95

**Root Causes:**
- Chunks too small (UnstructuredLoader over-splitting)
- High duplication (repeated headers/footers)
- Low content diversity

**Solution:**
Use `ingest_with_preprocessor.py` which addresses all these issues automatically.

### Ollama Connection Errors

```bash
# Check Ollama is running
ollama list

# Verify models are pulled
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text

# Test embedding
ollama run nomic-embed-text
```

## Documentation

- **[System Overview](docs/system-overview.md)** - Comprehensive architecture guide
- **[Agent Graph](docs/agent_graph.md)** - Workflow documentation
- **[RAG Data Preparation](docs/RAG_DATA_PREPARATION_GUIDE.md)** - Complete RAG guide
- **[Writing Documentation](docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md)** - Best practices
- **[Design Evaluation](docs/DOCUMENT_DESIGN_EVALUATION.md)** - Quality metrics
- **[CLAUDE.md](CLAUDE.md)** - Quick reference for Claude Code
- **[Preprocessor Quickstart](PREPROCESSOR_QUICKSTART.md)** - Getting started

## Contributing

When adding to the knowledge base:

1. Follow guidelines in `docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md`
2. Run `python ingest_with_preprocessor.py` to ingest
3. Check quality metrics in log file
4. Run notebook Section 2.2 for validation
5. Track quality score over time

## License

[Your License Here]

## Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [Ollama](https://ollama.ai/) - Local LLM serving
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Tavily](https://tavily.com/) - Web search API
- [LangSmith](https://smith.langchain.com/) - Observability platform
