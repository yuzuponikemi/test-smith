"""
Causal Graph Builder Node - Creates graph structure for visualization.

Part of the Causal Inference Graph workflow for root cause analysis.
Generates structured data representing causal relationships as a graph.
"""


def causal_graph_builder_node(state: dict) -> dict:
    """
    Builds a causal graph structure from validated relationships.

    The graph represents:
    - Nodes: Hypotheses (root causes) and Symptoms (effects)
    - Edges: Causal relationships with strength

    Args:
        state: Current graph state with hypotheses and causal relationships

    Returns:
        Updated state with causal_graph_data
    """
    print("---CAUSAL GRAPH BUILDER---")

    hypotheses = state.get("hypotheses", [])
    symptoms = state.get("symptoms", [])
    causal_relationships = state.get("causal_relationships", [])
    ranked_hypotheses = state.get("ranked_hypotheses", [])

    print(f"  Building causal graph with {len(hypotheses)} hypotheses and {len(symptoms)} symptoms...")

    # Create lookup for ranked likelihood
    likelihood_map = {
        h['hypothesis_id']: h['likelihood']
        for h in ranked_hypotheses
    }

    # Build nodes
    nodes = []

    # Add symptom nodes
    for i, symptom in enumerate(symptoms):
        nodes.append({
            "id": f"symptom_{i}",
            "label": symptom[:50] + ("..." if len(symptom) > 50 else ""),
            "type": "symptom",
            "full_text": symptom
        })

    # Add hypothesis nodes
    for h in hypotheses:
        nodes.append({
            "id": h['hypothesis_id'],
            "label": h['description'][:50] + ("..." if len(h['description']) > 50 else ""),
            "type": "hypothesis",
            "category": h['category'],
            "likelihood": likelihood_map.get(h['hypothesis_id'], 0.5),
            "full_text": h['description']
        })

    # Build edges from causal relationships
    edges = []
    for rel in causal_relationships:
        # Create edges from hypothesis to symptoms
        # (In a full implementation, we'd need to map which symptoms each hypothesis explains)
        for i in range(len(symptoms)):
            edges.append({
                "source": rel['hypothesis_id'],
                "target": f"symptom_{i}",
                "relationship_type": rel['relationship_type'],
                "strength": rel['causal_strength'],
                "supporting_evidence_count": len(rel['supporting_evidence']),
                "contradicting_evidence_count": len(rel.get('contradicting_evidence', []))
            })

    # Create graph structure
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_hypotheses": len(hypotheses),
            "total_symptoms": len(symptoms),
            "total_relationships": len(causal_relationships),
            "graph_type": "causal_inference"
        }
    }

    print(f"  Graph created: {len(nodes)} nodes, {len(edges)} edges")

    # Statistics
    strong_relationships = sum(1 for e in edges if e['strength'] > 0.7)
    print(f"  Strong causal relationships (>0.7): {strong_relationships}")

    return {
        "causal_graph_data": graph_data
    }
