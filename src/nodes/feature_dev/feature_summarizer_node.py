"""
Phase 7: Feature Summarizer Node

Generates comprehensive summary documentation.
"""

import json
import logging

from src.models import get_planner_model
from src.prompts.feature_dev_prompts import FEATURE_SUMMARIZER_PROMPT

logger = logging.getLogger(__name__)


def feature_summarizer_node(state: dict) -> dict:
    """
    Generate comprehensive feature implementation summary.

    Args:
        state: Current workflow state

    Returns:
        Updated state with summary and next steps
    """
    logger.info("=== Phase 7: Summary ===")

    # Get LLM
    llm = get_planner_model()

    # Prepare data for summary
    chosen_arch = state.get("chosen_architecture", {})
    files_created = state.get("files_created", [])
    files_modified = state.get("files_modified", [])
    review_findings = state.get("review_findings", [])

    # Create prompt
    prompt = FEATURE_SUMMARIZER_PROMPT.format(
        feature_request=state["feature_request"],
        chosen_architecture=json.dumps(chosen_arch, indent=2)
        if chosen_arch
        else "No architecture selected",
        files_created="\n".join(files_created) if files_created else "None",
        files_modified="\n".join(files_modified) if files_modified else "None",
        review_findings=json.dumps(review_findings, indent=2)
        if review_findings
        else "No issues found",
    )

    # Invoke LLM
    response = llm.invoke(prompt)
    summary = response.content if hasattr(response, "content") else str(response)

    # Extract next steps if present
    next_steps = []
    if "## Next Steps" in summary:
        steps_section = summary.split("## Next Steps")[1].split("##")[0]
        for line in steps_section.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                step = line.lstrip("0123456789. -").strip()
                if step:
                    next_steps.append(step)

    logger.info("Summary generated successfully")
    logger.info(f"Next steps: {len(next_steps)} recommendations")

    return {
        "summary": summary,
        "next_steps": next_steps,
        "current_phase": "complete",
        "phase_history": ["summary"],
    }
