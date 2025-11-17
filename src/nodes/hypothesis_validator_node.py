"""
Hypothesis Validator Node - Ranks hypotheses by likelihood.

Part of the Causal Inference Graph workflow for root cause analysis.
"""

from src.models import get_hypothesis_validator_model
from src.prompts.hypothesis_validator_prompt import HYPOTHESIS_VALIDATOR_PROMPT
from src.schemas import HypothesisRanking


def hypothesis_validator_node(state: dict) -> dict:
    """
    Ranks all hypotheses by likelihood based on causal analysis.

    Args:
        state: Current graph state with hypotheses and causal analysis

    Returns:
        Updated state with ranked_hypotheses
    """
    print("---HYPOTHESIS VALIDATOR---")

    query = state.get("query", "")
    issue_summary = state.get("issue_summary", "")
    hypotheses = state.get("hypotheses", [])
    causal_relationships = state.get("causal_relationships", [])

    print(f"  Ranking {len(hypotheses)} hypotheses based on causal analysis...")

    # Get model with structured output
    model = get_hypothesis_validator_model()
    structured_model = model.with_structured_output(HypothesisRanking)

    # Format causal analysis for prompt
    causal_analysis_str = "\n".join([
        f"- {rel['hypothesis_id']}: {rel['relationship_type']} (strength: {rel['causal_strength']:.2f})\n"
        f"  Supporting: {', '.join(rel['supporting_evidence'][:2])}\n"
        f"  Reasoning: {rel['reasoning'][:100]}..."
        for rel in causal_relationships
    ])

    # Format hypotheses for prompt
    hypotheses_str = "\n".join([
        f"- {h['hypothesis_id']}: {h['description']}"
        for h in hypotheses
    ])

    # Format prompt and invoke
    prompt = HYPOTHESIS_VALIDATOR_PROMPT.format(
        query=query,
        issue_summary=issue_summary,
        causal_analysis=causal_analysis_str,
        hypotheses=hypotheses_str
    )

    ranking: HypothesisRanking = structured_model.invoke(prompt)

    print(f"  Ranked {len(ranking.ranked_hypotheses)} hypotheses")
    print(f"  Top 3 most likely:")
    for i, h in enumerate(ranking.ranked_hypotheses[:3], 1):
        print(f"    {i}. {h.hypothesis_id}: {h.description[:50]}... (likelihood: {h.likelihood:.2f})")

    # Convert to dict format for state storage
    ranked_hypotheses_dict = [h.dict() for h in ranking.ranked_hypotheses]

    return {
        "ranked_hypotheses": ranked_hypotheses_dict,
        "ranking_methodology": ranking.ranking_methodology,
        "overall_assessment": ranking.overall_assessment,
    }
