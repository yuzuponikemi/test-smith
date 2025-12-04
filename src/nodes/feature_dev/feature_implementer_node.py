"""
Phase 5: Feature Implementer Node

Implements the feature following the chosen architecture.
"""

import logging
from datetime import datetime

from src.models import get_planner_model
from src.prompts.feature_dev_prompts import FEATURE_IMPLEMENTER_PROMPT

logger = logging.getLogger(__name__)


def feature_implementer_node(state: dict) -> dict:
    """
    Implement the feature following the chosen architecture.

    Args:
        state: Current workflow state

    Returns:
        Updated state with implementation log
    """
    logger.info("=== Phase 5: Implementation ===")

    chosen_arch = state.get("chosen_architecture")
    if not chosen_arch:
        logger.error("No architecture chosen!")
        return {
            "implementation_log": ["ERROR: No architecture was chosen"],
            "current_phase": "review",
            "phase_history": ["implementation"],
        }

    logger.info(f"Implementing: {chosen_arch['approach_name']}")

    # Get LLM
    llm = get_planner_model()

    # For now, we'll simulate implementation by generating a plan
    # In a real system, this would actually create/modify files
    prompt = FEATURE_IMPLEMENTER_PROMPT.format(
        feature_request=state["feature_request"],
        chosen_architecture=json.dumps(chosen_arch, indent=2),
        relevant_files_content="[Files would be read here in real implementation]",
    )

    # Invoke LLM
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    # Parse implementation log
    log_entries = []
    files_created = []
    files_modified = []

    if "IMPLEMENTATION LOG:" in content:
        log_section = content.split("IMPLEMENTATION LOG:")[1].split("FINAL STATUS:")[0]

        for line in log_section.split("\n"):
            line = line.strip()
            if line:
                log_entries.append(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")

                # Extract file operations
                if "Created:" in line:
                    file_path = line.split("Created:")[1].split("-")[0].strip()
                    files_created.append(file_path)
                elif "Modified:" in line:
                    file_path = line.split("Modified:")[1].split("-")[0].strip()
                    files_modified.append(file_path)

    # If no specific files found, use the ones from architecture
    if not files_created:
        files_created = [
            f.split("-")[0].strip() for f in chosen_arch.get("files_to_create", [])
        ]
    if not files_modified:
        files_modified = [
            f.split("-")[0].strip() for f in chosen_arch.get("files_to_modify", [])
        ]

    logger.info(f"Implementation complete: {len(files_created)} created, {len(files_modified)} modified")

    return {
        "implementation_log": log_entries,
        "files_created": files_created,
        "files_modified": files_modified,
        "current_phase": "review",
        "phase_history": ["implementation"],
    }


# Import json for the implementer
import json
