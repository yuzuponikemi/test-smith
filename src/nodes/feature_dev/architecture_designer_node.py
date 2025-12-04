"""
Phase 4: Architecture Designer Node

Generates multiple architecture proposals and lets user choose.
This node runs multiple architects in parallel.
"""

import json
import logging

from src.models import get_planner_model
from src.prompts.feature_dev_prompts import ARCHITECTURE_DESIGNER_PROMPT
from src.feature_dev_schemas import ArchitectureProposal

logger = logging.getLogger(__name__)


def architecture_designer_node(state: dict) -> dict:
    """
    Design multiple architecture approaches in parallel.

    Args:
        state: Current workflow state

    Returns:
        Updated state with architecture proposals
    """
    logger.info("=== Phase 4: Architecture Design ===")

    # Three parallel architects with different approaches
    approach_types = ["minimal_changes", "clean_architecture", "pragmatic_balance"]

    proposals = []

    for approach_type in approach_types:
        logger.info(f"Designing approach: {approach_type}")

        # Get LLM
        llm = get_planner_model()

        # Create prompt
        prompt = ARCHITECTURE_DESIGNER_PROMPT.format(
            feature_request=state["feature_request"],
            clarified_requirements=state["clarified_requirements"],
            codebase_patterns=state.get("codebase_patterns", ""),
            user_answers=state.get("user_answers", "No additional answers provided"),
            approach_type=approach_type,
        )

        # Invoke LLM
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Try to parse JSON from response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            proposal_data = json.loads(json_str)

            # Convert to typed dict
            proposal: ArchitectureProposal = {
                "approach_name": proposal_data.get(
                    "approach_name", approach_type.replace("_", " ").title()
                ),
                "description": proposal_data.get("description", ""),
                "pros": proposal_data.get("pros", []),
                "cons": proposal_data.get("cons", []),
                "files_to_create": proposal_data.get("files_to_create", []),
                "files_to_modify": proposal_data.get("files_to_modify", []),
                "implementation_steps": proposal_data.get("implementation_steps", []),
                "complexity_score": proposal_data.get("complexity_score", 5),
            }

            proposals.append(proposal)
            logger.info(
                f"✓ {proposal['approach_name']}: Complexity {proposal['complexity_score']}/10"
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON for {approach_type}: {e}")
            # Create a fallback proposal
            proposal: ArchitectureProposal = {
                "approach_name": approach_type.replace("_", " ").title(),
                "description": "Failed to generate structured proposal",
                "pros": ["Approach analysis in progress"],
                "cons": ["Incomplete proposal"],
                "files_to_create": [],
                "files_to_modify": [],
                "implementation_steps": ["Review and refine approach"],
                "complexity_score": 5,
            }
            proposals.append(proposal)

    logger.info(f"Generated {len(proposals)} architecture proposals")

    return {
        "architecture_proposals": proposals,
        "awaiting_user_input": True,  # Wait for user to choose
        "current_phase": "architecture",
        "phase_history": ["architecture"],
    }
