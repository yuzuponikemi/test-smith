"""
Report Reviewer Node - Phase 2.3

Reviews the generated report against quality criteria.
Based on Anthropic's multi-layer quality control approach with LLM-as-Judge.
"""

import json
import re
from typing import Literal

from src.models import get_evaluation_model
from src.prompts.report_reviewer_prompt import REPORT_REVIEWER_PROMPT
from src.schemas import ReportOutline, ReportReviewResult
from src.utils.logging_utils import print_node_header
from src.utils.result_validator import check_meta_description, count_words, detect_language


def _create_outline_summary(outline: ReportOutline) -> str:
    """Create a summary of the outline for the reviewer."""
    parts = [
        f"**Title**: {outline.title}",
        f"**Target Language**: {outline.target_language}",
        f"**Target Word Count**: {outline.target_word_count}",
        "",
        "**Sections**:",
    ]

    for section in outline.sections:
        parts.append(
            f"- {section.section_id}: {section.heading} ({section.target_word_count} words)"
        )

    parts.extend(
        [
            "",
            "**Executive Summary Points**:",
        ]
    )
    for point in outline.executive_summary_points:
        parts.append(f"- {point}")

    parts.extend(
        [
            "",
            "**Conclusion Points**:",
        ]
    )
    for point in outline.conclusion_points:
        parts.append(f"- {point}")

    return "\n".join(parts)


def _heuristic_review(
    draft_report: str,
    outline: ReportOutline,
    original_query: str,  # noqa: ARG001 - Reserved for future LLM-based query relevance check
) -> ReportReviewResult:
    """
    Perform heuristic-based review (fast, no LLM).
    Returns preliminary review result.
    """
    issues = []
    revision_instructions = []
    sections_needing_expansion = []

    # Word count check
    actual_words = count_words(draft_report)
    target_words = outline.target_word_count
    word_count_met = actual_words >= target_words * 0.6  # 60% threshold

    if not word_count_met:
        issues.append(
            f"Word count too low: {actual_words}/{target_words} ({actual_words / target_words * 100:.0f}%)"
        )
        revision_instructions.append(
            f"Expand content to reach at least {int(target_words * 0.6)} words"
        )

    # Language check
    detected_lang = detect_language(draft_report)
    expected_lang = outline.target_language
    language_correct = detected_lang == expected_lang

    if not language_correct:
        issues.append(f"Language mismatch: expected {expected_lang}, detected {detected_lang}")
        revision_instructions.append(f"Rewrite content in {expected_lang}")

    # Meta-description check
    contains_meta, meta_patterns = check_meta_description(draft_report)
    if contains_meta:
        issues.append(f"Contains meta-descriptions: {meta_patterns[:3]}")
        revision_instructions.append(
            "Remove all descriptions of research methodology and system processes"
        )

    # Section coverage check
    for section in outline.sections:
        section_heading = section.heading
        # Simple check: is the heading present?
        if section_heading not in draft_report:
            issues.append(f"Missing section: {section_heading}")
            sections_needing_expansion.append(section.section_id)
        else:
            # Check if section has enough content
            # Find content between this heading and next
            pattern = rf"##\s*{re.escape(section_heading)}(.*?)(?=##|$)"
            match = re.search(pattern, draft_report, re.DOTALL | re.IGNORECASE)
            if match:
                section_content = match.group(1)
                section_words = count_words(section_content)
                if section_words < section.target_word_count * 0.4:  # 40% threshold
                    issues.append(
                        f"Section '{section_heading}' too short: {section_words}/{section.target_word_count} words"
                    )
                    sections_needing_expansion.append(section.section_id)

    # Structure quality
    has_intro = bool(
        re.search(r"#.*?(summary|introduction|概要|はじめに)", draft_report, re.IGNORECASE)
    )
    has_conclusion = bool(re.search(r"##.*?(conclusion|結論|まとめ)", draft_report, re.IGNORECASE))
    has_headings = len(re.findall(r"^##\s+", draft_report, re.MULTILINE)) >= 2

    structure_quality: Literal["excellent", "good", "adequate", "poor"]
    if has_intro and has_conclusion and has_headings and len(issues) == 0:
        structure_quality = "excellent"
    elif has_intro and has_conclusion and has_headings:
        structure_quality = "good"
    elif has_headings:
        structure_quality = "adequate"
    else:
        structure_quality = "poor"
        issues.append("Poor document structure")
        revision_instructions.append("Add clear section headings, introduction, and conclusion")

    # Coverage check (simplified)
    coverage_complete = len(sections_needing_expansion) <= len(outline.sections) // 3

    # Determine if criteria met
    meets_criteria = (
        word_count_met
        and language_correct
        and not contains_meta
        and coverage_complete
        and structure_quality in ("excellent", "good")
    )

    return ReportReviewResult(
        meets_criteria=meets_criteria,
        word_count_actual=actual_words,
        word_count_target=target_words,
        word_count_met=word_count_met,
        language_correct=language_correct,
        coverage_complete=coverage_complete,
        structure_quality=structure_quality,
        contains_meta_description=contains_meta,
        issues=issues,
        revision_instructions=revision_instructions,
        sections_needing_expansion=sections_needing_expansion,
    )


def _llm_review(
    draft_report: str,
    outline: ReportOutline,
    original_query: str,
    actual_word_count: int,
) -> ReportReviewResult | None:
    """
    Perform LLM-based review for deeper quality assessment.
    Returns enhanced review result or None if LLM fails.
    """
    llm = get_evaluation_model()

    prompt = REPORT_REVIEWER_PROMPT.format(
        original_query=original_query,
        target_language=outline.target_language,
        target_word_count=outline.target_word_count,
        actual_word_count=actual_word_count,
        outline_summary=_create_outline_summary(outline),
        draft_report=draft_report[:15000],  # Limit to prevent context overflow
    )

    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Parse JSON from response
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None

        data = json.loads(json_str)

        return ReportReviewResult(
            meets_criteria=data.get("meets_criteria", False),
            word_count_actual=data.get("word_count_actual", actual_word_count),
            word_count_target=data.get("word_count_target", outline.target_word_count),
            word_count_met=data.get("word_count_met", False),
            language_correct=data.get("language_correct", True),
            coverage_complete=data.get("coverage_complete", False),
            structure_quality=data.get("structure_quality", "adequate"),
            contains_meta_description=data.get("contains_meta_description", False),
            issues=data.get("issues", []),
            revision_instructions=data.get("revision_instructions", []),
            sections_needing_expansion=data.get("sections_needing_expansion", []),
        )

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"  ⚠️ LLM review parsing failed: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️ LLM review error: {e}")
        return None


def report_reviewer_node(state: dict) -> dict:
    """
    Review the draft report against quality criteria.

    This node:
    1. Performs heuristic checks (word count, language, structure)
    2. Optionally uses LLM for deeper quality assessment
    3. Generates specific revision instructions if needed

    Args:
        state: Current workflow state with draft_report and report_outline

    Returns:
        Updated state with review_result and needs_revision flag
    """
    print_node_header("REPORT REVIEWER")

    # Get inputs
    draft_report = state.get("draft_report", "")
    outline_dict = state.get("report_outline", {})
    aggregated_dict = state.get("aggregated_findings", {})
    revision_count = state.get("revision_count", 0)

    if not draft_report:
        print("  ⚠️ No draft report to review")
        return {
            "review_result": None,
            "needs_revision": False,
        }

    if not outline_dict:
        print("  ⚠️ No outline available")
        return {
            "review_result": None,
            "needs_revision": False,
        }

    # Reconstruct outline
    try:
        outline = ReportOutline.model_validate(outline_dict)
    except Exception as e:
        print(f"  ⚠️ Failed to parse outline: {e}")
        return {
            "review_result": None,
            "needs_revision": False,
        }

    original_query = aggregated_dict.get("original_query", "")

    print(f"  Report length: {len(draft_report)} chars")
    print(f"  Target word count: {outline.target_word_count}")
    print(f"  Current revision: {revision_count}")

    # 1. Heuristic review (always)
    print("\n  🔍 Running heuristic review...")
    heuristic_result = _heuristic_review(draft_report, outline, original_query)

    print(
        f"     Word count: {heuristic_result.word_count_actual}/{heuristic_result.word_count_target}"
    )
    print(f"     Language correct: {'✓' if heuristic_result.language_correct else '✗'}")
    print(
        f"     Meta-description: {'✗ Found' if heuristic_result.contains_meta_description else '✓ Clean'}"
    )
    print(f"     Structure: {heuristic_result.structure_quality}")
    print(
        f"     Initial assessment: {'✓ PASS' if heuristic_result.meets_criteria else '✗ NEEDS REVISION'}"
    )

    # 2. LLM review (only if heuristic passes or first revision)
    final_result = heuristic_result

    if heuristic_result.meets_criteria or revision_count == 0:
        print("\n  🤖 Running LLM review for deeper assessment...")
        llm_result = _llm_review(
            draft_report, outline, original_query, heuristic_result.word_count_actual
        )

        if llm_result:
            # Merge results (LLM may catch issues heuristic missed)
            final_result = ReportReviewResult(
                meets_criteria=heuristic_result.meets_criteria and llm_result.meets_criteria,
                word_count_actual=heuristic_result.word_count_actual,
                word_count_target=heuristic_result.word_count_target,
                word_count_met=heuristic_result.word_count_met,
                language_correct=heuristic_result.language_correct and llm_result.language_correct,
                coverage_complete=llm_result.coverage_complete,  # Trust LLM for this
                structure_quality=llm_result.structure_quality,
                contains_meta_description=(
                    heuristic_result.contains_meta_description
                    or llm_result.contains_meta_description
                ),
                issues=list(set(heuristic_result.issues + llm_result.issues)),
                revision_instructions=list(
                    set(heuristic_result.revision_instructions + llm_result.revision_instructions)
                ),
                sections_needing_expansion=list(
                    set(
                        heuristic_result.sections_needing_expansion
                        + llm_result.sections_needing_expansion
                    )
                ),
            )
            print(
                f"     LLM assessment: {'✓ PASS' if llm_result.meets_criteria else '✗ NEEDS REVISION'}"
            )
        else:
            print("     ⚠️ LLM review failed, using heuristic result only")

    # Determine if revision needed
    # Max 3 revisions to prevent infinite loops
    needs_revision = not final_result.meets_criteria and revision_count < 3

    # Print summary
    print("\n  📊 Review Summary:")
    print(f"     Meets criteria: {'✓ Yes' if final_result.meets_criteria else '✗ No'}")
    print(f"     Needs revision: {'Yes' if needs_revision else 'No'}")

    if final_result.issues:
        print(f"     Issues found: {len(final_result.issues)}")
        for issue in final_result.issues[:5]:
            print(f"       - {issue}")

    if needs_revision and final_result.revision_instructions:
        print(f"     Revision instructions: {len(final_result.revision_instructions)}")

    print()

    return {
        "review_result": final_result.model_dump(),
        "needs_revision": needs_revision,
    }
