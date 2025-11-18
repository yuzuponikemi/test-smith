"""
Provenance Graph Builder Node - Builds knowledge graph for research lineage.

This node constructs a complete provenance graph showing:
- claim → evidence → source relationships
- Enables "Why do you say that?" queries
- Provides data for lineage visualization
"""

import json
from datetime import datetime
from src.models import get_analyzer_model
from src.prompts.provenance_prompt import PROVENANCE_ANALYSIS_PROMPT
from src.utils.logging_utils import print_node_header


def provenance_graph_builder_node(state: dict) -> dict:
    """
    Builds a provenance knowledge graph from research results.

    Takes accumulated sources and analyzed data, extracts claims and evidence,
    and constructs a graph showing the complete lineage from claims back to sources.

    Returns:
        dict with provenance_graph containing nodes, edges, and metadata
    """
    print_node_header("PROVENANCE GRAPH BUILDER")

    # Gather all sources
    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])
    all_sources = web_sources + rag_sources

    if not all_sources:
        print("  No sources available for provenance tracking")
        return {"provenance_graph": _create_empty_graph()}

    # Get analyzed content
    analyzed_data = state.get("analyzed_data", [])
    query = state.get("query", "")

    print(f"  Processing {len(all_sources)} sources")
    print(f"  Analyzing {len(analyzed_data)} data segments")

    # Create sources summary for the prompt
    sources_summary = _create_sources_summary(all_sources)
    analyzed_content = "\n\n---\n\n".join(analyzed_data) if analyzed_data else "No analyzed content available."

    # Use LLM to extract claims and evidence
    model = get_analyzer_model()
    prompt = PROVENANCE_ANALYSIS_PROMPT.format(
        query=query,
        sources_summary=sources_summary,
        analyzed_content=analyzed_content
    )

    try:
        response = model.invoke(prompt)
        provenance_data = _parse_provenance_response(response.content)
    except Exception as e:
        print(f"  Error extracting provenance: {e}")
        provenance_data = {"claims": [], "evidence_items": [], "confidence_assessment": "Error during extraction"}

    # Build the graph structure
    graph = _build_lineage_graph(all_sources, provenance_data)

    print(f"  Built provenance graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
    print(f"  Extracted {len(provenance_data.get('claims', []))} claims")

    return {"provenance_graph": graph}


def _create_sources_summary(sources: list) -> str:
    """Create a formatted summary of sources for the prompt."""
    summary_parts = []
    for source in sources:
        source_id = source.get("source_id", "unknown")
        source_type = source.get("source_type", "unknown")
        title = source.get("title", "Unknown")
        snippet = source.get("content_snippet", "")[:200]

        summary_parts.append(
            f"[{source_id}] ({source_type}) {title}\n"
            f"  Content: {snippet}..."
        )

    return "\n\n".join(summary_parts)


def _parse_provenance_response(response: str) -> dict:
    """Parse the LLM response to extract provenance data."""
    try:
        # Try to extract JSON from the response
        # Handle cases where LLM wraps JSON in markdown code blocks
        content = response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)
    except json.JSONDecodeError:
        # If JSON parsing fails, return empty structure
        return {
            "claims": [],
            "evidence_items": [],
            "confidence_assessment": "Failed to parse provenance data"
        }


def _build_lineage_graph(sources: list, provenance_data: dict) -> dict:
    """Build the complete lineage graph structure."""
    nodes = []
    edges = []

    # Add source nodes
    for source in sources:
        source_id = source.get("source_id", "unknown")
        nodes.append({
            "node_id": source_id,
            "node_type": "source",
            "label": source.get("title", "Unknown Source")[:50],
            "full_content": source.get("content_snippet", ""),
            "metadata": {
                "source_type": source.get("source_type", "unknown"),
                "url": source.get("url"),
                "relevance_score": source.get("relevance_score", 0.5),
                "query_used": source.get("query_used", ""),
                "timestamp": source.get("timestamp", "")
            }
        })

    # Add evidence nodes and edges from sources
    evidence_items = provenance_data.get("evidence_items", [])
    for evidence in evidence_items:
        evidence_id = evidence.get("evidence_id", "unknown")

        nodes.append({
            "node_id": evidence_id,
            "node_type": "evidence",
            "label": evidence.get("content", "")[:50],
            "full_content": evidence.get("content", ""),
            "metadata": {
                "extraction_method": evidence.get("extraction_method", "unknown"),
                "confidence": evidence.get("confidence", 0.5)
            }
        })

        # Create edges from sources to evidence
        for source_id in evidence.get("source_ids", []):
            edges.append({
                "source_node_id": source_id,
                "target_node_id": evidence_id,
                "relationship": "derived_from",
                "strength": evidence.get("confidence", 0.5)
            })

    # Add claim nodes and edges from evidence
    claims = provenance_data.get("claims", [])
    for claim in claims:
        claim_id = claim.get("claim_id", "unknown")

        nodes.append({
            "node_id": claim_id,
            "node_type": "claim",
            "label": claim.get("statement", "")[:50],
            "full_content": claim.get("statement", ""),
            "metadata": {
                "claim_type": claim.get("claim_type", "unknown"),
                "confidence": claim.get("confidence", 0.5),
                "location": claim.get("location_in_report", "")
            }
        })

        # Create edges from evidence to claims
        for evidence_id in claim.get("evidence_ids", []):
            edges.append({
                "source_node_id": evidence_id,
                "target_node_id": claim_id,
                "relationship": "supports",
                "strength": claim.get("confidence", 0.5)
            })

    # Build complete graph structure
    graph = {
        "sources": sources,
        "evidence": evidence_items,
        "claims": claims,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_sources": len(sources),
            "total_evidence": len(evidence_items),
            "total_claims": len(claims),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "graph_type": "provenance_lineage",
            "created_at": datetime.now().isoformat(),
            "confidence_assessment": provenance_data.get("confidence_assessment", "")
        }
    }

    return graph


def _create_empty_graph() -> dict:
    """Create an empty provenance graph structure."""
    return {
        "sources": [],
        "evidence": [],
        "claims": [],
        "nodes": [],
        "edges": [],
        "metadata": {
            "total_sources": 0,
            "total_evidence": 0,
            "total_claims": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "graph_type": "provenance_lineage",
            "created_at": datetime.now().isoformat(),
            "confidence_assessment": "No sources available"
        }
    }


def query_provenance(state: dict, claim_text: str = None, claim_id: str = None) -> dict:
    """
    Query provenance information for a specific claim.

    Enables "Why do you say that?" functionality by tracing
    a claim back through its evidence to the original sources.

    Args:
        state: Current graph state containing provenance_graph
        claim_text: Text of the claim to look up (fuzzy match)
        claim_id: Specific claim ID to look up (exact match)

    Returns:
        dict with claim, evidence_chain, source_chain, and explanation
    """
    provenance_graph = state.get("provenance_graph", {})

    if not provenance_graph:
        return {
            "error": "No provenance graph available",
            "explanation": "Research has not been completed or provenance tracking was not enabled."
        }

    claims = provenance_graph.get("claims", [])
    evidence_items = provenance_graph.get("evidence", [])
    sources = provenance_graph.get("sources", [])

    # Find the claim
    target_claim = None
    if claim_id:
        for claim in claims:
            if claim.get("claim_id") == claim_id:
                target_claim = claim
                break
    elif claim_text:
        # Fuzzy match on claim text
        claim_text_lower = claim_text.lower()
        for claim in claims:
            if claim_text_lower in claim.get("statement", "").lower():
                target_claim = claim
                break

    if not target_claim:
        return {
            "error": "Claim not found",
            "explanation": f"Could not find a claim matching: {claim_text or claim_id}",
            "available_claims": [c.get("statement", "")[:100] for c in claims[:5]]
        }

    # Build evidence chain
    evidence_chain = []
    evidence_ids = target_claim.get("evidence_ids", [])
    for ev_id in evidence_ids:
        for evidence in evidence_items:
            if evidence.get("evidence_id") == ev_id:
                evidence_chain.append(evidence)
                break

    # Build source chain
    source_chain = []
    source_ids_seen = set()
    for evidence in evidence_chain:
        for source_id in evidence.get("source_ids", []):
            if source_id not in source_ids_seen:
                for source in sources:
                    if source.get("source_id") == source_id:
                        source_chain.append(source)
                        source_ids_seen.add(source_id)
                        break

    # Generate explanation using LLM
    from src.prompts.provenance_prompt import PROVENANCE_QUERY_PROMPT

    evidence_text = "\n".join([
        f"- [{e.get('evidence_id')}] {e.get('content')}"
        for e in evidence_chain
    ])

    source_text = "\n".join([
        f"- [{s.get('source_id')}] {s.get('title')} ({s.get('source_type')})"
        + (f"\n  URL: {s.get('url')}" if s.get('url') else "")
        for s in source_chain
    ])

    model = get_analyzer_model()
    prompt = PROVENANCE_QUERY_PROMPT.format(
        claim_statement=target_claim.get("statement", ""),
        evidence_items=evidence_text,
        source_details=source_text
    )

    try:
        response = model.invoke(prompt)
        explanation = response.content
    except Exception as e:
        explanation = f"Error generating explanation: {e}"

    return {
        "claim": target_claim,
        "evidence_chain": evidence_chain,
        "source_chain": source_chain,
        "explanation": explanation,
        "confidence_breakdown": {
            "claim_confidence": target_claim.get("confidence", 0.5),
            "avg_evidence_confidence": sum(e.get("confidence", 0.5) for e in evidence_chain) / len(evidence_chain) if evidence_chain else 0,
            "avg_source_relevance": sum(s.get("relevance_score", 0.5) for s in source_chain) / len(source_chain) if source_chain else 0
        }
    }
