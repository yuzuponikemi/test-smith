"""
Phase 1: Discovery Node

Clarifies feature requirements and establishes scope.
"""

import logging

from src.models import get_planner_model
from src.prompts.feature_dev_prompts import DISCOVERY_PROMPT

logger = logging.getLogger(__name__)


def discovery_node(state: dict) -> dict:
    """
    Analyze and clarify the feature request.

    Args:
        state: Current workflow state

    Returns:
        Updated state with clarified requirements
    """
    logger.info("=== Phase 1: Discovery ===")
    logger.info(f"Feature Request: {state['feature_request']}")

    # Get LLM
    llm = get_planner_model()

    # Create prompt
    prompt = DISCOVERY_PROMPT.format(feature_request=state["feature_request"])

    # Invoke LLM
    response = llm.invoke(prompt)

    # Parse response
    content = response.content if hasattr(response, "content") else str(response)

    # Extract sections
    clarified = ""
    scope = ""
    constraints = ""

    if "CLARIFIED REQUIREMENTS:" in content:
        parts = content.split("FEATURE SCOPE:")
        clarified = parts[0].replace("CLARIFIED REQUIREMENTS:", "").strip()
        if len(parts) > 1:
            scope_parts = parts[1].split("CONSTRAINTS:")
            scope = scope_parts[0].strip()
            if len(scope_parts) > 1:
                constraints = scope_parts[1].strip()

    logger.info(f"Clarified Requirements: {clarified[:200]}...")
    logger.info(f"Scope: {scope[:200]}...")

    return {
        "clarified_requirements": clarified,
        "feature_scope": scope,
        "constraints": constraints,
        "current_phase": "exploration",
        "phase_history": ["discovery"],
    }
