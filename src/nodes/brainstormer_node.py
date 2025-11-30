"""
Brainstormer Node - Generates diverse root cause hypotheses.

Part of the Causal Inference Graph workflow for root cause analysis.
"""

from src.models import get_brainstormer_model
from src.prompts.brainstormer_prompt import BRAINSTORMER_PROMPT
from src.schemas import HypothesisList
from src.utils.logging_utils import print_node_header


def brainstormer_node(state: dict) -> dict:
    """
    Generates multiple diverse root cause hypotheses for the issue.

    Args:
        state: Current graph state with issue analysis fields

    Returns:
        Updated state with hypotheses list
    """
    print_node_header("BRAINSTORMER")

    query = state.get("query", "")
    issue_summary = state.get("issue_summary", "")
    symptoms = state.get("symptoms", [])
    context = state.get("context", "")
    scope = state.get("scope", "")

    print(f"  Generating hypotheses for: {issue_summary[:60]}...")

    # Get model with structured output
    model = get_brainstormer_model()
    structured_model = model.with_structured_output(HypothesisList)

    # Format prompt and invoke
    prompt = BRAINSTORMER_PROMPT.format(
        query=query,
        issue_summary=issue_summary,
        symptoms=symptoms,
        context=context,
        scope=scope
    )

    result: HypothesisList = structured_model.invoke(prompt)

    print(f"  Generated {len(result.hypotheses)} root cause hypotheses")
    for h in result.hypotheses[:3]:  # Show first 3
        print(f"    - {h.hypothesis_id}: {h.description[:60]}...")

    # Convert to dict format for state storage
    hypotheses_dict = [h.dict() for h in result.hypotheses]

    return {
        "hypotheses": hypotheses_dict,
        "brainstorming_approach": result.brainstorming_approach,
    }
