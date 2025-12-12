"""
Report Quality Checker Node

Checks if the generated report meets minimum quality criteria.
If not, triggers re-research with enhanced queries.

This implements a quality feedback loop to ensure reports meet
the target word count and depth requirements.
"""

from src.config.research_depth import get_depth_config
from src.utils.logging_utils import print_node_header
from src.utils.result_validator import count_words


def report_quality_checker_node(state: dict) -> dict:
    """
    Check report quality and determine if re-research is needed.

    Quality criteria:
    1. Word count >= 60% of target (minimum threshold)
    2. Maximum retry count not exceeded (prevent infinite loops)

    Returns:
        Updated state with:
        - quality_check_passed: bool
        - quality_feedback: str (feedback for planner if retry needed)
        - quality_retry_count: int
    """
    print_node_header("REPORT QUALITY CHECKER")

    report = state.get("report", "")
    research_depth = state.get("research_depth", "standard")
    retry_count = state.get("quality_retry_count", 0)
    execution_mode = state.get("execution_mode", "simple")

    # Get depth config for target word count
    depth_config = get_depth_config(research_depth)
    target_word_count = depth_config.target_word_count
    min_word_count = int(target_word_count * 0.6)  # 60% threshold

    # Count actual words
    actual_word_count = count_words(report)
    word_ratio = actual_word_count / target_word_count if target_word_count > 0 else 0

    print(f"  Research depth: {research_depth}")
    print(f"  Execution mode: {execution_mode}")
    print(f"  Target word count: {target_word_count}")
    print(f"  Minimum required: {min_word_count} (60%)")
    print(f"  Actual word count: {actual_word_count}")
    print(f"  Achievement: {word_ratio * 100:.1f}%")
    print(f"  Retry count: {retry_count}/2")

    # Maximum 2 retries to prevent infinite loops
    max_retries = 2

    # Check if quality criteria met
    quality_passed = actual_word_count >= min_word_count

    if quality_passed:
        print("\n  ✓ Quality check PASSED")
        return {
            "quality_check_passed": True,
            "quality_feedback": "",
            "quality_retry_count": retry_count,
        }

    # Quality not met - check if we can retry
    if retry_count >= max_retries:
        print(f"\n  ⚠ Quality check FAILED but max retries ({max_retries}) reached")
        print("    Proceeding with current report")
        return {
            "quality_check_passed": True,  # Force pass to prevent infinite loop
            "quality_feedback": "",
            "quality_retry_count": retry_count,
        }

    # Generate feedback for planner to improve research
    shortfall = min_word_count - actual_word_count
    feedback = _generate_quality_feedback(
        actual_word_count=actual_word_count,
        target_word_count=target_word_count,
        shortfall=shortfall,
        research_depth=research_depth,
        retry_count=retry_count,
    )

    print("\n  ✗ Quality check FAILED")
    print(f"    Shortfall: {shortfall} words needed")
    print(f"    Triggering re-research (attempt {retry_count + 1}/{max_retries})")

    return {
        "quality_check_passed": False,
        "quality_feedback": feedback,
        "quality_retry_count": retry_count + 1,
        # Reset loop_count to allow more iterations
        "loop_count": 0,
        # Clear previous evaluation to force re-evaluation
        "evaluation": "",
    }


def _generate_quality_feedback(
    actual_word_count: int,
    target_word_count: int,
    shortfall: int,
    research_depth: str,
    retry_count: int,
) -> str:
    """Generate actionable feedback for the planner."""
    feedback_parts = [
        f"QUALITY FEEDBACK (Retry {retry_count + 1}):",
        f"The previous report was {actual_word_count} words, "
        f"but needs at least {int(target_word_count * 0.6)} words ({research_depth} depth).",
        f"Need approximately {shortfall} more words of content.",
        "",
        "INSTRUCTIONS FOR IMPROVED RESEARCH:",
    ]

    if retry_count == 0:
        # First retry - expand search scope
        feedback_parts.extend(
            [
                "1. Generate MORE search queries (at least 3-4 queries)",
                "2. Search for RELATED topics and broader context",
                "3. Include practical examples and use cases",
                "4. Look for recent developments and trends",
            ]
        )
    else:
        # Second retry - different approach
        feedback_parts.extend(
            [
                "1. Try DIFFERENT search terms and angles",
                "2. Search for case studies and real-world applications",
                "3. Include comparisons with alternatives",
                "4. Look for expert opinions and analysis",
                "5. Search for historical context and evolution",
            ]
        )

    return "\n".join(feedback_parts)
