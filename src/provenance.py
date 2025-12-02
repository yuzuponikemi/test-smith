"""
Research Provenance & Lineage Tracking Utilities

This module provides easy access to provenance features:
- Query provenance ("Why do you say that?")
- Build lineage graphs
- Export citations
- Save/load provenance data

Usage:
    from src.provenance import (
        query_claim_provenance,
        build_provenance_graph,
        export_citations,
        save_provenance,
        load_provenance
    )

    # After running a research query, query the provenance
    result = query_claim_provenance(state, "Python is widely used")

    # Build the full lineage graph
    graph = build_provenance_graph(state)

    # Export citations
    bibtex = export_citations(state, format="bibtex")
"""

import json
from datetime import datetime
from pathlib import Path

from src.nodes.provenance_graph_builder_node import provenance_graph_builder_node, query_provenance


def query_claim_provenance(state: dict, claim_text: str = None, claim_id: str = None) -> dict:
    """
    Query provenance for a specific claim ("Why do you say that?").

    Args:
        state: Graph state containing provenance data
        claim_text: Text of the claim to look up (fuzzy match)
        claim_id: Specific claim ID to look up (exact match)

    Returns:
        dict with claim, evidence_chain, source_chain, and explanation

    Example:
        result = query_claim_provenance(state, "Python is popular")
        print(result["explanation"])
    """
    # Build graph if not already built
    if not state.get("provenance_graph"):
        state = {**state, **build_provenance_graph(state)}

    return query_provenance(state, claim_text=claim_text, claim_id=claim_id)


def build_provenance_graph(state: dict) -> dict:
    """
    Build the complete provenance lineage graph from state.

    Args:
        state: Graph state with web_sources, rag_sources, and analyzed_data

    Returns:
        dict with provenance_graph key containing the built graph

    Example:
        result = build_provenance_graph(state)
        graph = result["provenance_graph"]
        print(f"Found {len(graph['claims'])} claims")
    """
    return provenance_graph_builder_node(state)


def export_citations(state: dict, format: str = "markdown") -> str:
    """
    Export citations from provenance data.

    Args:
        state: Graph state with provenance data
        format: One of "bibtex", "apa", "mla", "markdown", "json"

    Returns:
        Formatted citation string

    Example:
        bibtex = export_citations(state, format="bibtex")
        print(bibtex)
    """
    # Import here to avoid circular imports
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "utils"))
    from export_citations import export_citations as _export  # type: ignore[import-not-found]

    # Build graph if needed
    if not state.get("provenance_graph"):
        graph_result = build_provenance_graph(state)
        graph_data = graph_result.get("provenance_graph", {})
    else:
        graph_data = state.get("provenance_graph", {})

    # If no graph data, use sources directly
    if not graph_data:
        graph_data = {
            "sources": state.get("web_sources", []) + state.get("rag_sources", []),
            "evidence": [],
            "claims": [],
        }

    return _export(graph_data, format)


def save_provenance(state: dict, output_path: str = None, include_full_state: bool = False) -> str:
    """
    Save provenance data to a JSON file.

    Args:
        state: Graph state with provenance data
        output_path: Path to save file (default: provenance_TIMESTAMP.json)
        include_full_state: Whether to include full analyzed data

    Returns:
        Path to saved file

    Example:
        path = save_provenance(state)
        print(f"Saved to {path}")
    """
    # Build graph if needed
    if not state.get("provenance_graph"):
        graph_result = build_provenance_graph(state)
        provenance_graph = graph_result.get("provenance_graph", {})
    else:
        provenance_graph = state.get("provenance_graph", {})

    # Prepare export data
    export_data = {
        "query": state.get("query", ""),
        "provenance_graph": provenance_graph,
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "web_source_count": len(state.get("web_sources", [])),
            "rag_source_count": len(state.get("rag_sources", [])),
        },
    }

    if include_full_state:
        export_data["analyzed_data"] = state.get("analyzed_data", [])
        export_data["report"] = state.get("report", "")

    # Generate output path
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"provenance_{timestamp}.json"

    # Save to file
    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    return output_path


def load_provenance(file_path: str) -> dict:
    """
    Load provenance data from a JSON file.

    Args:
        file_path: Path to provenance JSON file

    Returns:
        dict with loaded provenance data

    Example:
        data = load_provenance("provenance_20240320.json")
        claims = data["provenance_graph"]["claims"]
    """
    with open(file_path) as f:
        return json.load(f)


def get_sources_summary(state: dict) -> dict:
    """
    Get a summary of all sources used in research.

    Args:
        state: Graph state with web_sources and rag_sources

    Returns:
        dict with source statistics and summaries

    Example:
        summary = get_sources_summary(state)
        print(f"Total sources: {summary['total']}")
    """
    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])

    return {
        "total": len(web_sources) + len(rag_sources),
        "web_count": len(web_sources),
        "rag_count": len(rag_sources),
        "web_sources": [
            {
                "id": s.get("source_id"),
                "title": s.get("title"),
                "url": s.get("url"),
                "relevance": s.get("relevance_score", 0.5),
            }
            for s in web_sources
        ],
        "rag_sources": [
            {
                "id": s.get("source_id"),
                "title": s.get("title"),
                "file": s.get("metadata", {}).get("source_file", ""),
                "relevance": s.get("relevance_score", 0.5),
            }
            for s in rag_sources
        ],
    }


def list_claims(state: dict) -> list:
    """
    List all claims extracted from the research.

    Args:
        state: Graph state with provenance_graph

    Returns:
        List of claim summaries

    Example:
        claims = list_claims(state)
        for claim in claims:
            print(f"{claim['id']}: {claim['statement'][:50]}...")
    """
    # Build graph if needed
    if not state.get("provenance_graph"):
        graph_result = build_provenance_graph(state)
        provenance_graph = graph_result.get("provenance_graph", {})
    else:
        provenance_graph = state.get("provenance_graph", {})

    claims = provenance_graph.get("claims", [])

    return [
        {
            "id": c.get("claim_id"),
            "statement": c.get("statement"),
            "type": c.get("claim_type"),
            "confidence": c.get("confidence", 0.5),
            "evidence_count": len(c.get("evidence_ids", [])),
        }
        for c in claims
    ]


def visualize_lineage(state: dict, output_path: str = "lineage_graph.html") -> str:
    """
    Generate an interactive HTML visualization of the lineage graph.

    Args:
        state: Graph state with provenance data
        output_path: Path for output HTML file

    Returns:
        Path to generated visualization

    Example:
        path = visualize_lineage(state)
        # Open path in browser to view
    """
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "visualization"))
    from visualize_provenance_graph import (  # type: ignore[import-not-found]
        generate_html_visualization,
    )

    # Build graph if needed
    if not state.get("provenance_graph"):
        graph_result = build_provenance_graph(state)
        graph_data = graph_result.get("provenance_graph", {})
    else:
        graph_data = state.get("provenance_graph", {})

    return generate_html_visualization(graph_data, output_path)


# Convenience aliases
why = query_claim_provenance  # "why" do you say that?
trace = query_claim_provenance  # trace the lineage
