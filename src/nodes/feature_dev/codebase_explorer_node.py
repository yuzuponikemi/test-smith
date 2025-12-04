"""
Phase 2: Codebase Explorer Node

Explores the codebase to find similar features and architectural patterns.
This node can be run in parallel with multiple focus areas.
"""

import logging

from src.models import get_planner_model
from src.prompts.feature_dev_prompts import CODEBASE_EXPLORER_PROMPT
from src.feature_dev_schemas import ExplorationResult

logger = logging.getLogger(__name__)


def codebase_explorer_node(state: dict) -> dict:
    """
    Explore codebase for similar features and patterns.

    This node is designed to be called multiple times in parallel,
    each with a different focus area.

    Args:
        state: Current workflow state

    Returns:
        Updated state with exploration results
    """
    # Determine focus areas based on feature type
    # For simplicity, we'll create 2 explorers with different focuses
    focus_areas = [
        "similar features and existing implementations",
        "architectural patterns and integration points",
    ]

    exploration_results = []

    for i, focus_area in enumerate(focus_areas):
        agent_id = f"explorer-{i+1}"
        logger.info(f"=== Phase 2: Codebase Exploration ({agent_id}) ===")
        logger.info(f"Focus: {focus_area}")

        # Get LLM
        llm = get_planner_model()

        # Create prompt
        prompt = CODEBASE_EXPLORER_PROMPT.format(
            feature_request=state["feature_request"],
            clarified_requirements=state["clarified_requirements"],
            focus_area=focus_area,
            agent_id=agent_id,
        )

        # Invoke LLM
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse response to extract key information
        key_files = []
        patterns = ""
        findings = content

        # Extract KEY FILES section
        if "KEY FILES" in content:
            files_section = content.split("KEY FILES")[1].split("ARCHITECTURAL PATTERNS")[
                0
            ]
            # Parse file references (simple extraction)
            for line in files_section.split("\n"):
                if line.strip() and (
                    line.strip().startswith("-") or line.strip()[0].isdigit()
                ):
                    # Extract file path (before first '-' or space after path)
                    parts = line.split("-")
                    if len(parts) > 0:
                        file_ref = parts[0].strip().lstrip("0123456789. -")
                        if ":" in file_ref:
                            file_path = file_ref.split(":")[0].strip()
                            if file_path and file_path.endswith(".py"):
                                key_files.append(file_path)

        # Extract ARCHITECTURAL PATTERNS section
        if "ARCHITECTURAL PATTERNS" in content:
            patterns_section = content.split("ARCHITECTURAL PATTERNS")[1].split(
                "FINDINGS"
            )[0]
            patterns = patterns_section.strip()

        result: ExplorationResult = {
            "agent_id": agent_id,
            "focus_area": focus_area,
            "key_files": key_files[:10],  # Limit to 10 files
            "patterns": patterns,
            "findings": findings,
        }

        exploration_results.append(result)
        logger.info(f"{agent_id} found {len(key_files)} key files")

    # Aggregate all files
    all_files = []
    all_patterns = []

    for result in exploration_results:
        all_files.extend(result["key_files"])
        if result["patterns"]:
            all_patterns.append(f"[{result['agent_id']}] {result['patterns']}")

    # Deduplicate files
    unique_files = list(set(all_files))

    return {
        "exploration_results": exploration_results,
        "relevant_files": unique_files,
        "codebase_patterns": "\n\n".join(all_patterns),
        "current_phase": "clarification",
        "phase_history": ["exploration"],
    }
