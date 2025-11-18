# Test-Smith Documentation

**Version:** 2.2 | **Last Updated:** November 2025

Welcome to the Test-Smith documentation. This is your single entry point to all project documentation.

---

## Quick Navigation

| I want to... | Go to |
|-------------|-------|
| Set up and run Test-Smith | [Getting Started](getting-started/) |
| Understand the architecture | [Architecture](architecture/) |
| Configure the knowledge base | [Knowledge Base](knowledge-base/) |
| Develop or extend the system | [Development](development/) |
| View historical design docs | [Archive](archive/) |

---

## Documentation Structure

### Getting Started
Essential guides for installation, setup, and first use.

- **[Installation & Setup](getting-started/installation.md)** - Prerequisites, dependencies, and environment setup
- **[Quick Start](getting-started/quick-start.md)** - Run your first research query in 5 minutes
- **[Model Providers](getting-started/model-providers.md)** - Configure Ollama (local) or Gemini (cloud) models

### Architecture
System design and architecture documentation.

- **[System Overview](architecture/system-overview.md)** - Complete architecture deep dive, components, and data flow
- **[Multi-Graph Workflows](architecture/multi-graph-workflows.md)** - Available graph workflows and when to use each
- **[Diagrams](architecture/diagrams/)** - Visual architecture diagrams

### Knowledge Base
RAG system configuration and knowledge base management.

- **[RAG Guide](knowledge-base/rag-guide.md)** - Complete guide to data preparation, chunking, and embedding
- **[Writing Documentation](knowledge-base/writing-docs.md)** - Best practices for writing RAG-friendly documentation
- **[Quality Evaluation](knowledge-base/quality-evaluation.md)** - Metrics and evaluation for documentation quality
- **[Preprocessor](knowledge-base/preprocessor.md)** - Using the intelligent document preprocessor

### Development
Guides for developers and contributors.

- **[Evaluation Guide](development/evaluation-guide.md)** - Testing the system with LangSmith evaluation framework
- **[Logging & Debugging](development/logging-debugging.md)** - Debug execution, analyze logs, manage reports
- **[Creating Graphs](development/creating-graphs.md)** - Create custom workflow graphs
- **[CI/CD](development/ci-cd.md)** - GitHub Actions and automated testing

### Archive
Historical design documents and implementation notes.

- **[Phase 1-4 Implementation](archive/hierarchical-decomposition.md)** - Original design and implementation history
- **[Migration Notes](archive/migration-notes.md)** - Notes from major version migrations

---

## Key Concepts

### What is Test-Smith?

Test-Smith is a **LangGraph-based multi-agent research assistant** that autonomously conducts deep research and generates comprehensive reports. It uses a "Hierarchical Plan-and-Execute" strategy with dynamic replanning.

### Core Technologies

| Technology | Purpose |
|------------|---------|
| LangGraph 0.6.11 | Multi-agent workflow orchestration |
| LangChain 0.3.27 | LLM framework and abstractions |
| Ollama | Local LLMs (llama3, command-r, nomic-embed-text) |
| ChromaDB 1.3.4 | Vector database for RAG |
| Tavily API | Web search capabilities |
| LangSmith | Observability and tracing |

### Available Workflows

| Graph | Best For | Complexity |
|-------|----------|------------|
| **deep_research** (default) | Complex multi-faceted questions | High |
| **quick_research** | Simple questions, fast lookups | Low |
| **fact_check** | Verifying claims, checking accuracy | Medium |
| **comparative** | Comparing technologies, trade-off analysis | Medium |
| **causal_inference** | Root cause analysis, troubleshooting | Medium |

---

## Quick Commands

```bash
# List available graphs
python main.py graphs

# Run default (deep_research) workflow
python main.py run "Your research question"

# Run specific workflow
python main.py run "Your question" --graph quick_research

# Check version
python main.py --version
```

---

## Documentation Conventions

- **Code blocks** show exact commands to run
- **Tables** summarize options and configurations
- **Mermaid diagrams** visualize workflows
- Each document is **self-contained** and can be read independently

---

## Related Resources

- **[CLAUDE.md](../CLAUDE.md)** - Quick reference for Claude Code
- **[README.md](../README.md)** - Project overview and basic usage
- **[chroma_explorer.ipynb](../chroma_explorer.ipynb)** - Interactive knowledge base analysis

---

## Need Help?

1. Check the relevant documentation section above
2. Search for specific topics in the docs
3. Review [Logging & Debugging](development/logging-debugging.md) for troubleshooting
4. Open an issue on the project repository
