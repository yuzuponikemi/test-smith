"""
Phase 3: Question Clarifier Node

Identifies ambiguities and generates clarifying questions for the user.
"""

import logging

from src.models import get_planner_model
from src.prompts.feature_dev_prompts import QUESTION_CLARIFIER_PROMPT

logger = logging.getLogger(__name__)


def question_clarifier_node(state: dict) -> dict:
    """
    Generate clarifying questions based on codebase exploration.

    Args:
        state: Current workflow state

    Returns:
        Updated state with questions (blocks if questions exist)
    """
    logger.info("=== Phase 3: Clarifying Questions ===")

    # Get LLM
    llm = get_planner_model()

    # Create prompt
    prompt = QUESTION_CLARIFIER_PROMPT.format(
        feature_request=state["feature_request"],
        clarified_requirements=state["clarified_requirements"],
        codebase_patterns=state.get("codebase_patterns", ""),
        relevant_files="\n".join(state.get("relevant_files", [])),
    )

    # Invoke LLM
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    # Extract questions
    questions = []
    if "CLARIFYING QUESTIONS:" in content:
        questions_section = content.split("CLARIFYING QUESTIONS:")[1].strip()

        # Check if "None" or no questions
        if "None -" in questions_section or "No questions" in questions_section:
            logger.info("No clarifying questions needed - requirements are clear")
            return {
                "questions": [],
                "awaiting_user_input": False,
                "current_phase": "architecture",
                "phase_history": ["clarification"],
            }

        # Parse questions
        for line in questions_section.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering and clean up
                question = line.lstrip("0123456789. -").strip()
                if question and len(question) > 10:  # Valid question
                    questions.append(question)

    logger.info(f"Generated {len(questions)} clarifying questions")
    for i, q in enumerate(questions, 1):
        logger.info(f"Q{i}: {q}")

    if questions:
        return {
            "questions": questions,
            "awaiting_user_input": True,
            "current_phase": "clarification",
            "phase_history": ["clarification"],
        }
    else:
        return {
            "questions": [],
            "awaiting_user_input": False,
            "current_phase": "architecture",
            "phase_history": ["clarification"],
        }
