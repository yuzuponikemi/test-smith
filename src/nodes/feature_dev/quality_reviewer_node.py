"""
Phase 6: Quality Reviewer Node

Performs parallel code reviews from multiple perspectives.
"""

import json
import logging

from src.models import get_evaluation_model
from src.prompts.feature_dev_prompts import QUALITY_REVIEWER_PROMPT
from src.feature_dev_schemas import ReviewFinding

logger = logging.getLogger(__name__)


def quality_reviewer_node(state: dict) -> dict:
    """
    Perform parallel quality reviews from three perspectives.

    Args:
        state: Current workflow state

    Returns:
        Updated state with review findings
    """
    logger.info("=== Phase 6: Quality Review ===")

    # Three parallel reviewers with different focuses
    review_focuses = ["simplicity", "correctness", "conventions"]

    all_findings = []

    # Prepare files changed for review
    files_changed = []
    for f in state.get("files_created", []):
        files_changed.append(f"Created: {f}")
    for f in state.get("files_modified", []):
        files_changed.append(f"Modified: {f}")

    files_changed_str = "\n".join(files_changed) if files_changed else "No files changed"

    # Load project guidelines (from CLAUDE.md if available)
    project_guidelines = """
    - Follow existing code style and conventions
    - Use type hints and docstrings
    - Write clean, maintainable code
    - Reuse existing abstractions
    - Handle errors appropriately
    """

    for focus in review_focuses:
        logger.info(f"Reviewing: {focus}")

        # Get LLM
        llm = get_evaluation_model()

        # Create prompt
        prompt = QUALITY_REVIEWER_PROMPT.format(
            review_focus=focus,
            files_changed=files_changed_str,
            project_guidelines=project_guidelines,
        )

        # Invoke LLM
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Try to parse JSON
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            findings_data = json.loads(json_str)

            # Convert to typed dicts and filter by confidence >= 80
            for finding_data in findings_data:
                confidence = finding_data.get("confidence", 0)
                if confidence >= 80:
                    finding: ReviewFinding = {
                        "severity": finding_data.get("severity", "minor"),
                        "confidence": confidence,
                        "category": finding_data.get("category", "quality"),
                        "file_path": finding_data.get("file_path", "unknown"),
                        "line_number": finding_data.get("line_number", 0),
                        "description": finding_data.get("description", ""),
                        "recommendation": finding_data.get("recommendation", ""),
                    }
                    all_findings.append(finding)

            logger.info(f"✓ {focus}: Found {len(findings_data)} issues, {len([f for f in findings_data if f.get('confidence', 0) >= 80])} >= 80% confidence")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON for {focus}: {e}")

    # Filter critical issues
    critical_issues = [f for f in all_findings if f["severity"] == "critical"]

    logger.info(f"Review complete: {len(all_findings)} total findings, {len(critical_issues)} critical")

    return {
        "review_findings": all_findings,
        "critical_issues": critical_issues,
        "awaiting_user_input": len(all_findings) > 0,  # Wait if issues found
        "current_phase": "review",
        "phase_history": ["review"],
    }
