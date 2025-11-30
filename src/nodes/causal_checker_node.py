"""
Causal Checker Node - Validates causal relationships using evidence.

Part of the Causal Inference Graph workflow for root cause analysis.
"""

from src.models import get_causal_checker_model
from src.prompts.causal_checker_prompt import CAUSAL_CHECKER_PROMPT
from src.schemas import CausalAnalysis
from src.utils.logging_utils import print_node_header


def causal_checker_node(state: dict) -> dict:
    """
    Evaluates causal relationships between hypotheses and symptoms using gathered evidence.

    Args:
        state: Current graph state with hypotheses and evidence

    Returns:
        Updated state with causal_relationships
    """
    print_node_header("CAUSAL CHECKER")

    query = state.get("query", "")
    issue_summary = state.get("issue_summary", "")
    symptoms = state.get("symptoms", [])
    hypotheses = state.get("hypotheses", [])

    # Get evidence
    web_results = state.get("search_results", [])
    rag_results = state.get("rag_results", [])

    print(f"  Analyzing causal relationships for {len(hypotheses)} hypotheses")
    print(f"  Using {len(web_results)} web results and {len(rag_results)} RAG results")

    # Get model with structured output
    model = get_causal_checker_model()
    structured_model = model.with_structured_output(CausalAnalysis)

    # Format hypotheses for prompt
    hypotheses_str = "\n".join(
        [
            f"- {h['hypothesis_id']}: {h['description']}\n  Mechanism: {h['mechanism']}"
            for h in hypotheses
        ]
    )

    # Format prompt and invoke
    prompt = CAUSAL_CHECKER_PROMPT.format(
        query=query,
        issue_summary=issue_summary,
        symptoms=symptoms,
        hypotheses=hypotheses_str,
        web_results=web_results,
        rag_results=rag_results,
    )

    analysis: CausalAnalysis = structured_model.invoke(prompt)

    print(f"  Evaluated {len(analysis.relationships)} causal relationships")

    # Show summary of relationship types
    relationship_types: dict[str, int] = {}
    for rel in analysis.relationships:
        rel_type = str(rel.relationship_type)
        relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

    for rel_type, count in relationship_types.items():
        print(f"    - {rel_type}: {count}")

    # Convert to dict format for state storage
    relationships_dict = [r.dict() for r in analysis.relationships]

    return {
        "causal_relationships": relationships_dict,
        "causal_analysis_approach": analysis.analysis_approach,
    }
