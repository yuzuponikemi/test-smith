# Quick Start Guide

Get Test-Smith running in 5 minutes.

---

## Prerequisites

Ensure you've completed the [Installation](installation.md) steps:
- Ollama running with required models
- `.env` file configured with Tavily API key
- Virtual environment activated

---

## Your First Query

### Basic Research Query

```bash
python main.py run "What are the key differences between transformers and RNNs?"
```

This uses the default `deep_research` workflow, which:
1. Analyzes query complexity
2. Decomposes into subtasks if complex
3. Searches web and/or knowledge base
4. Synthesizes a comprehensive report

### Quick Lookup

For simple questions, use the faster `quick_research` workflow:

```bash
python main.py run "What is the capital of France?" --graph quick_research
```

---

## Available Workflows

List all available workflows:

```bash
python main.py graphs
```

### Choose the Right Workflow

| Workflow | Use When | Example |
|----------|----------|---------|
| `deep_research` | Complex, multi-faceted questions | "Compare AI frameworks for production use" |
| `quick_research` | Simple lookups, time-sensitive | "What is BERT?" |
| `fact_check` | Verifying claims | "Is it true that Python was created in 1991?" |
| `comparative` | Comparing options | "React vs Vue for a new project" |
| `causal_inference` | Troubleshooting, root cause | "Why is my app running slowly?" |

### Example Commands

```bash
# Deep research (default)
python main.py run "Analyze multi-agent AI systems"

# Quick research
python main.py run "What is ChromaDB?" --graph quick_research

# Fact checking
python main.py run "Verify: GPT-4 was released in March 2023" --graph fact_check

# Comparison
python main.py run "PostgreSQL vs MySQL for web applications" --graph comparative

# Root cause analysis
python main.py run "Why does my API return 500 errors intermittently?" --graph causal_inference
```

---

## Understanding Output

### Console Output

During execution, you'll see:
- Node execution progress
- Query allocation (web vs RAG)
- Subtask decomposition (for hierarchical mode)
- Final report

### Generated Files

Each run creates:

1. **Execution Log** (`logs/execution_*.log`)
   - Complete execution trace
   - Useful for debugging

2. **Research Report** (`reports/report_*.md`)
   - Final synthesized report
   - Markdown format with metadata

```bash
# List recent reports
python main.py list reports --limit 5

# List recent logs
python main.py list logs --limit 5
```

---

## Conversation Continuity

Use thread IDs for follow-up questions:

```bash
# First query
python main.py run "What is LangGraph?" --thread-id my-session

# Follow-up in same context
python main.py run "How does it compare to AutoGen?" --thread-id my-session
```

---

## Common Options

```bash
# Disable logging (console only)
python main.py run "Quick test" --no-log --no-report

# Specify graph
python main.py run "Your query" --graph quick_research

# Use thread ID
python main.py run "Follow-up" --thread-id abc123
```

---

## Tips for Better Results

### 1. Be Specific

```bash
# Vague - may produce generic results
python main.py run "Tell me about AI"

# Specific - better results
python main.py run "Explain transformer attention mechanisms and their advantages over RNN architectures"
```

### 2. Use Appropriate Workflow

Don't use `deep_research` for simple facts - it's slower and overkill.

### 3. Add Context

```bash
# Good: includes context
python main.py run "Compare React and Vue for building a large e-commerce application with server-side rendering needs"

# Less context
python main.py run "React vs Vue"
```

### 4. Check the Knowledge Base

If you have domain-specific documents:
```bash
# Add documents to knowledge base first
python scripts/ingest/ingest_with_preprocessor.py

# Then query
python main.py run "How does our authentication system work?"
```

---

## Next Steps

- **[Model Providers](model-providers.md)** - Configure Ollama or Gemini for different performance
- **[Multi-Graph Workflows](../architecture/multi-graph-workflows.md)** - Deep dive into workflow options
- **[RAG Guide](../knowledge-base/rag-guide.md)** - Add your own documents to the knowledge base
