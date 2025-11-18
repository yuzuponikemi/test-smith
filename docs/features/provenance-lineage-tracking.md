# Research Provenance & Lineage Tracking

## Overview

Test-Smith now includes comprehensive provenance tracking that builds a knowledge graph showing the complete lineage of research findings: **claim → evidence → source**. This feature enables:

- **"Why do you say that?"** queries to trace any claim back to its sources
- **Inline citations** in reports (similar to Perplexity AI)
- **Visualization** of reasoning chains
- **Academic export** of citations (BibTeX, APA, MLA)

## Architecture

```
Sources (Web/RAG)
       ↓
    Evidence
       ↓
     Claims
       ↓
     Report
```

### Data Model

The provenance system uses three levels of tracking:

1. **Sources** - Raw information retrieved from web search or knowledge base
   - URL, title, content snippet, query used, timestamp
   - Relevance scores for ranking

2. **Evidence** - Facts extracted from sources
   - Links to source IDs
   - Extraction method (quote, paraphrase, synthesis)
   - Confidence scores

3. **Claims** - Assertions made in the final report
   - Links to evidence IDs
   - Claim type (fact, analysis, recommendation)
   - Location in report

## Usage

### Basic Usage

Provenance tracking is automatically enabled in all research graphs. After running a query:

```python
from src.provenance import (
    query_claim_provenance,
    list_claims,
    export_citations,
    visualize_lineage
)

# Run a research query
result = graph.invoke({"query": "What are best practices for Python testing?"})
state = result  # Contains provenance data

# List all claims extracted
claims = list_claims(state)
for claim in claims:
    print(f"[{claim['id']}] {claim['statement'][:60]}...")

# Query "Why do you say that?" for any claim
explanation = query_claim_provenance(state, "pytest is the standard")
print(explanation["explanation"])
print(f"Sources: {len(explanation['source_chain'])}")

# Export citations
bibtex = export_citations(state, format="bibtex")
print(bibtex)

# Generate visualization
html_path = visualize_lineage(state, "my_research_lineage.html")
```

### Inline Citations in Reports

Reports now include inline citations like academic papers:

```markdown
## Python Testing Best Practices

Python testing has evolved significantly over the past decade [1].
The pytest framework has become the de facto standard [2, 3],
replacing earlier tools like nose and unittest [1].

Key features include:
- Fixture-based setup [2]
- Parametrized testing [3, 4]
- Plugin ecosystem [5]

### References

1. Python Testing History - Web - https://example.com/history
2. pytest Documentation - KB - pytest-docs.md
3. Real Python Tutorial - Web - https://realpython.com/pytest
...
```

### "Why Do You Say That?" Queries

Trace any claim back to its original sources:

```python
from src.provenance import why  # Alias for query_claim_provenance

# Find the claim and explain it
result = why(state, "pytest is widely adopted")

print("Claim:", result["claim"]["statement"])
print("\nEvidence:")
for ev in result["evidence_chain"]:
    print(f"  - {ev['content'][:100]}...")

print("\nSources:")
for src in result["source_chain"]:
    print(f"  - [{src['source_id']}] {src['title']}")
    if src['url']:
        print(f"    URL: {src['url']}")

print("\nExplanation:")
print(result["explanation"])
```

### Visualization

Generate interactive HTML visualizations showing the reasoning chain:

```bash
# From saved provenance data
python scripts/visualization/visualize_provenance_graph.py provenance.json

# Or programmatically
from src.provenance import visualize_lineage
path = visualize_lineage(state, "lineage.html")
```

The visualization shows:
- **Source nodes** (blue) at the bottom
- **Evidence nodes** (green) in the middle
- **Claim nodes** (purple) at the top
- **Edges** showing relationships with strength indicators
- Color intensity indicates confidence/relevance

### Academic Export

Export citations for papers, reports, or documentation:

```python
from src.provenance import export_citations

# BibTeX format (for LaTeX)
bibtex = export_citations(state, format="bibtex")

# APA format
apa = export_citations(state, format="apa")

# MLA format
mla = export_citations(state, format="mla")

# Markdown with links
markdown = export_citations(state, format="markdown")

# Full JSON export
json_data = export_citations(state, format="json")
```

Or use the command-line tool:

```bash
# Export to specific format
python scripts/utils/export_citations.py provenance.json --format bibtex -o refs.bib

# Export all formats
python scripts/utils/export_citations.py provenance.json --format all --output exports/
```

### Saving and Loading

Save provenance data for later analysis:

```python
from src.provenance import save_provenance, load_provenance

# Save after research
path = save_provenance(state, "my_research.json")

# Load later
data = load_provenance("my_research.json")
claims = data["provenance_graph"]["claims"]
```

## State Schema

Provenance tracking adds these fields to the graph state:

```python
# Source tracking (accumulated across iterations)
web_sources: Annotated[list[dict], operator.add]
rag_sources: Annotated[list[dict], operator.add]

# Complete lineage graph
provenance_graph: dict  # Built by provenance_graph_builder_node
```

## Nodes

### Searcher Node (`src/nodes/searcher_node.py`)

Now captures structured metadata from web searches:
- Source ID, URL, title
- Content snippet
- Query used, timestamp
- Relevance score

### RAG Retriever Node (`src/nodes/rag_retriever_node.py`)

Now captures knowledge base metadata:
- Source ID, document title
- Content snippet
- Query used, similarity score
- Source file path

### Provenance Graph Builder (`src/nodes/provenance_graph_builder_node.py`)

Builds the complete lineage graph:
- Extracts claims and evidence from analyzed data
- Links evidence to sources
- Creates graph structure for visualization

## Schemas

New Pydantic schemas in `src/schemas.py`:

- `SourceReference` - Individual source metadata
- `EvidenceItem` - Evidence with source links
- `Claim` - Claims with evidence links
- `LineageNode` / `LineageEdge` - Graph structure
- `ProvenanceGraph` - Complete graph
- `Citation` - Academic citation format
- `ProvenanceQuery` / `ProvenanceResponse` - Query interface

## Configuration

Provenance tracking is enabled by default. The synthesizer automatically uses citations when provenance data is available.

To disable inline citations, use the original prompts by not providing source data.

## Performance Notes

- Source metadata collection adds minimal overhead (~10ms per query)
- Graph building uses LLM call for claim extraction
- Visualization is client-side (vis.js), no server needed
- Full lineage graph is only built on demand

## Example Workflow

```python
import asyncio
from langgraph.checkpoint.sqlite import SqliteSaver
from src.graphs import get_graph

# Setup
memory = SqliteSaver.from_conn_string(":memory:")
graph_builder = get_graph("quick_research")
graph = graph_builder.get_uncompiled_graph().compile(checkpointer=memory)

# Run research
config = {"configurable": {"thread_id": "research-1"}}
result = graph.invoke(
    {"query": "What are the best practices for API rate limiting?"},
    config
)

# The report now includes inline citations
print(result["report"])

# Query provenance
from src.provenance import why, list_claims, visualize_lineage

# See all claims
claims = list_claims(result)
print(f"Found {len(claims)} claims")

# Explain a specific claim
explanation = why(result, "token bucket")
print(explanation["explanation"])

# Visualize
visualize_lineage(result, "rate_limiting_lineage.html")
```

## Troubleshooting

### No provenance data available

Ensure you're using a graph that includes the updated nodes (searcher, rag_retriever). Check that `web_sources` or `rag_sources` are in the state.

### Claims not extracted

The graph builder uses an LLM to extract claims. If the model fails or returns invalid JSON, claims may be empty. Check logs for parsing errors.

### Visualization not loading

Ensure vis.js CDN is accessible. The visualization requires JavaScript enabled in the browser.

## Related Documentation

- [System Architecture](../architecture/system-overview.md)
- [Multi-Graph Workflows](../architecture/multi-graph-workflows.md)
- [Creating Custom Graphs](../development/creating-graphs.md)
