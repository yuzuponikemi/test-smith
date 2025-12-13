"""
Report Revisor Node - Phase 2.4

Revises the report based on reviewer feedback.
Based on GPT Researcher's Revisor agent that iteratively improves content.
"""

from src.models import get_synthesizer_model
from src.prompts.report_revisor_prompt import REPORT_REVISOR_PROMPT
from src.schemas import AggregatedFindings, ReportOutline, ReportReviewResult
from src.utils.logging_utils import print_node_header
from src.utils.result_validator import count_words


def _format_additional_findings(
    aggregated: AggregatedFindings, sections_to_expand: list[str], outline: ReportOutline
) -> str:
    """
    Format additional findings for sections that need expansion.
    """
    parts = []

    # Map section IDs to their relevant finding IDs
    section_findings_map = {s.section_id: s.relevant_finding_ids for s in outline.sections}

    # Get findings for sections that need expansion
    relevant_finding_ids = set()
    for section_id in sections_to_expand:
        if section_id in section_findings_map:
            relevant_finding_ids.update(section_findings_map[section_id])

    # If no specific sections, include all findings
    if not relevant_finding_ids:
        relevant_finding_ids = {f.subtask_id for f in aggregated.findings}

    # Format relevant findings
    for finding in aggregated.findings:
        if finding.subtask_id in relevant_finding_ids:
            part = f"""
### {finding.subtask_id}: {finding.focus_area}

**Findings**:
"""
            for f in finding.findings:
                part += f"- {f}\n"

            if finding.key_insights:
                part += "\n**Insights**:\n"
                for insight in finding.key_insights:
                    part += f"- {insight}\n"

            parts.append(part)

    return "\n".join(parts) if parts else "No additional findings available."


def report_revisor_node(state: dict) -> dict:
    """
    Revise the report based on reviewer feedback.

    This node:
    1. Takes the draft report and review feedback
    2. Uses LLM to revise and improve the report
    3. Focuses on expanding thin sections and fixing issues
    4. Ensures language consistency throughout

    Args:
        state: Current workflow state with draft_report, review_result, etc.

    Returns:
        Updated state with revised draft_report and incremented revision_count
    """
    print_node_header("REPORT REVISOR")

    # Get inputs
    draft_report = state.get("draft_report", "")
    review_dict = state.get("review_result", {})
    outline_dict = state.get("report_outline", {})
    aggregated_dict = state.get("aggregated_findings", {})
    revision_count = state.get("revision_count", 0)

    if not draft_report or not review_dict:
        print("  ⚠️ Missing draft report or review result")
        return {
            "draft_report": draft_report,
            "revision_count": revision_count,
        }

    # Reconstruct objects
    try:
        review = ReportReviewResult.model_validate(review_dict)
        outline = ReportOutline.model_validate(outline_dict)
        aggregated = AggregatedFindings.model_validate(aggregated_dict)
    except Exception as e:
        print(f"  ⚠️ Failed to parse input data: {e}")
        return {
            "draft_report": draft_report,
            "revision_count": revision_count,
        }

    print(f"  Current word count: {review.word_count_actual}")
    print(f"  Target word count: {review.word_count_target}")
    print(f"  Revision attempt: {revision_count + 1}")
    print(f"  Issues to fix: {len(review.issues)}")
    print(f"  Sections to expand: {len(review.sections_needing_expansion)}")

    # Format inputs for prompt
    issues_str = "\n".join(f"- {issue}" for issue in review.issues) if review.issues else "None"
    instructions_str = (
        "\n".join(f"- {inst}" for inst in review.revision_instructions)
        if review.revision_instructions
        else "None"
    )
    sections_str = (
        ", ".join(review.sections_needing_expansion)
        if review.sections_needing_expansion
        else "None"
    )

    # Get additional findings for expansion
    additional_findings = _format_additional_findings(
        aggregated, review.sections_needing_expansion, outline
    )

    # Calculate how much expansion is needed
    words_needed = max(0, int(review.word_count_target * 0.7) - review.word_count_actual)
    print(f"  Words to add: ~{words_needed}")

    # Build prompt
    prompt = REPORT_REVISOR_PROMPT.format(
        original_query=aggregated.original_query,
        target_language=outline.target_language,
        current_word_count=review.word_count_actual,
        target_word_count=review.word_count_target,
        issues=issues_str,
        revision_instructions=instructions_str,
        sections_needing_expansion=sections_str,
        draft_report=draft_report,
        additional_findings=additional_findings,
    )

    # Get LLM response
    print("\n  ✏️  Revising report...")
    llm = get_synthesizer_model()

    try:
        response = llm.invoke(prompt)
        revised_report = response.content if hasattr(response, "content") else str(response)

        # Validate revision
        new_word_count = count_words(revised_report)

        # Sanity check: revision should be at least as long as original
        if new_word_count < review.word_count_actual * 0.8:
            print("  ⚠️ Revision is shorter than original, keeping original")
            revised_report = draft_report
            new_word_count = review.word_count_actual
        else:
            improvement = new_word_count - review.word_count_actual
            print(f"  ✓ Revision complete: {new_word_count} words (+{improvement})")

    except Exception as e:
        print(f"  ⚠️ Revision failed: {e}")
        revised_report = draft_report
        new_word_count = review.word_count_actual

    # Update word counts per section (simplified)
    section_word_counts = state.get("section_word_counts", {})

    # Print summary
    print("\n  📊 Revision Summary:")
    print(f"     Before: {review.word_count_actual} words")
    print(f"     After: {new_word_count} words")
    print(f"     Target: {review.word_count_target} words")
    achievement = (
        (new_word_count / review.word_count_target * 100) if review.word_count_target > 0 else 0
    )
    print(f"     Achievement: {achievement:.1f}%")
    print()

    return {
        "draft_report": revised_report,
        "revision_count": revision_count + 1,
        "total_word_count": new_word_count,
        "section_word_counts": section_word_counts,
    }
