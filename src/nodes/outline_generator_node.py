"""
Outline Generator Node - Phase 2.1

Generates a structured outline from aggregated research findings.
Based on Stanford STORM's pre-writing approach where outline generation
significantly improves final report quality.
"""

import json
import re

from src.models import get_synthesizer_model
from src.prompts.outline_generator_prompt import OUTLINE_GENERATOR_PROMPT
from src.schemas import AggregatedFindings, OutlineSection, ReportOutline
from src.utils.logging_utils import print_node_header

# Word count targets by research depth
WORD_COUNT_TARGETS = {
    "quick": 1500,
    "standard": 3000,
    "deep": 6000,
    "comprehensive": 10000,
}


def _format_findings_summary(aggregated: AggregatedFindings) -> str:
    """
    Format aggregated findings into a summary for the outline generator.
    """
    summary_parts = []

    for finding in aggregated.findings:
        part = f"""
### {finding.subtask_id}: {finding.focus_area}
**Query**: {finding.query}
**Quality**: {finding.quality_score:.2f} | **Words**: {finding.word_count}

**Key Findings**:
"""
        for i, f in enumerate(finding.findings[:5], 1):
            # Truncate long findings
            truncated = f[:300] + "..." if len(f) > 300 else f
            part += f"  {i}. {truncated}\n"

        summary_parts.append(part)

    return "\n".join(summary_parts)


def _parse_outline_response(response_text: str, target_language: str) -> ReportOutline | None:
    """
    Parse LLM response into ReportOutline structure.
    """
    # Try to extract JSON from response
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            return None

    try:
        data = json.loads(json_str)

        # Build sections
        sections: list[OutlineSection] = []
        for s in data.get("sections", []):
            section = OutlineSection(
                section_id=s.get("section_id", f"section_{len(sections) + 1}"),
                heading=s.get("heading", "Untitled Section"),
                subheadings=s.get("subheadings", []),
                relevant_finding_ids=s.get("relevant_finding_ids", []),
                key_points=s.get("key_points", []),
                target_word_count=s.get("target_word_count", 500),
            )
            sections.append(section)

        outline = ReportOutline(
            title=data.get("title", "Research Report"),
            executive_summary_points=data.get("executive_summary_points", []),
            sections=sections,
            conclusion_points=data.get("conclusion_points", []),
            target_word_count=data.get("target_word_count", 3000),
            target_language=data.get("target_language", target_language),
        )

        return outline

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"  ⚠️ Failed to parse outline JSON: {e}")
        return None


def _create_default_outline(
    aggregated: AggregatedFindings, target_word_count: int
) -> ReportOutline:
    """
    Create a default outline when LLM parsing fails.
    """
    # Group findings by focus area
    focus_areas: dict[str, list[str]] = {}
    for finding in aggregated.findings:
        area = finding.focus_area or "General"
        if area not in focus_areas:
            focus_areas[area] = []
        focus_areas[area].append(finding.subtask_id)

    # Create sections from focus areas
    sections = []
    section_count = len(focus_areas)
    words_per_section = target_word_count // max(section_count + 2, 1)  # +2 for intro/conclusion

    for i, (area, finding_ids) in enumerate(focus_areas.items(), 1):
        section = OutlineSection(
            section_id=f"section_{i}",
            heading=area,
            subheadings=[],
            relevant_finding_ids=finding_ids,
            key_points=[],
            target_word_count=words_per_section,
        )
        sections.append(section)

    return ReportOutline(
        title=f"Research Report: {aggregated.original_query[:50]}",
        executive_summary_points=["Key findings from research"],
        sections=sections,
        conclusion_points=["Summary and recommendations"],
        target_word_count=target_word_count,
        target_language=aggregated.target_language,
    )


def outline_generator_node(state: dict) -> dict:
    """
    Generate a structured outline from aggregated research findings.

    This node:
    1. Takes AggregatedFindings from Phase 1
    2. Uses LLM to create a logical outline structure
    3. Allocates word counts to sections
    4. Maps findings to sections for coverage

    Args:
        state: Current workflow state with aggregated_findings

    Returns:
        Updated state with report_outline
    """
    print_node_header("OUTLINE GENERATOR")

    # Get aggregated findings
    aggregated_dict = state.get("aggregated_findings", {})
    if not aggregated_dict:
        print("  ⚠️ No aggregated findings available")
        return {"report_outline": None}

    # Reconstruct AggregatedFindings from dict
    try:
        aggregated = AggregatedFindings.model_validate(aggregated_dict)
    except Exception as e:
        print(f"  ⚠️ Failed to parse aggregated findings: {e}")
        return {"report_outline": None}

    research_depth = aggregated.research_depth
    target_language = aggregated.target_language
    target_word_count = WORD_COUNT_TARGETS.get(research_depth, 3000)

    print(f"  Query: {aggregated.original_query[:60]}...")
    print(f"  Research depth: {research_depth}")
    print(f"  Target language: {target_language}")
    print(f"  Target word count: {target_word_count}")
    print(f"  Total findings: {len(aggregated.findings)}")
    print(f"  Themes: {aggregated.themes}")

    # Format findings for prompt
    findings_summary = _format_findings_summary(aggregated)
    themes_str = ", ".join(aggregated.themes) if aggregated.themes else "None identified"
    coverage_gaps_str = (
        ", ".join(aggregated.coverage_gaps) if aggregated.coverage_gaps else "None identified"
    )

    # Build prompt
    prompt = OUTLINE_GENERATOR_PROMPT.format(
        original_query=aggregated.original_query,
        research_depth=research_depth,
        target_language=target_language,
        findings_summary=findings_summary,
        themes=themes_str,
        coverage_gaps=coverage_gaps_str,
        target_word_count=target_word_count,
    )

    # Get LLM response
    print("\n  Generating outline...")
    llm = get_synthesizer_model()

    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Parse response
        outline = _parse_outline_response(response_text, target_language)

        if outline is None:
            print("  ⚠️ Failed to parse LLM response, using default outline")
            outline = _create_default_outline(aggregated, target_word_count)

    except Exception as e:
        print(f"  ⚠️ LLM error: {e}")
        outline = _create_default_outline(aggregated, target_word_count)

    # Print outline summary
    print("\n  📋 Generated Outline:")
    print(f"     Title: {outline.title}")
    print(f"     Sections: {len(outline.sections)}")
    for section in outline.sections:
        print(f"       - {section.heading} ({section.target_word_count} words)")
    print(f"     Executive points: {len(outline.executive_summary_points)}")
    print(f"     Conclusion points: {len(outline.conclusion_points)}")
    print(f"     Total target: {outline.target_word_count} words")
    print()

    return {
        "report_outline": outline.model_dump(),
    }
