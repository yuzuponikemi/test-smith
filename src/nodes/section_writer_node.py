"""
Section Writer Node - Phase 2.2

Writes individual sections of the report based on the outline and relevant findings.
Based on GPT Researcher's approach of separating research from writing.
"""

from src.models import get_synthesizer_model
from src.prompts.section_writer_prompt import (
    CONCLUSION_WRITER_PROMPT,
    INTRODUCTION_WRITER_PROMPT,
    SECTION_WRITER_PROMPT,
)
from src.schemas import AggregatedFindings, ReportOutline, SubtaskFinding
from src.utils.logging_utils import print_node_header
from src.utils.result_validator import count_words


def _get_relevant_findings(
    finding_ids: list[str], all_findings: list[SubtaskFinding]
) -> list[SubtaskFinding]:
    """Get findings that match the given IDs."""
    findings_by_id = {f.subtask_id: f for f in all_findings}
    return [findings_by_id[fid] for fid in finding_ids if fid in findings_by_id]


def _format_findings_for_section(findings: list[SubtaskFinding]) -> str:
    """Format findings for the section writer prompt."""
    if not findings:
        return "No specific findings provided for this section."

    parts = []
    for finding in findings:
        part = f"""
### Source: {finding.subtask_id} - {finding.focus_area}
**Relevance Score**: {finding.relevance_score:.2f}

**Findings**:
"""
        for i, f in enumerate(finding.findings, 1):
            part += f"{i}. {f}\n"

        if finding.key_insights:
            part += "\n**Key Insights**:\n"
            for insight in finding.key_insights:
                part += f"- {insight}\n"

        parts.append(part)

    return "\n".join(parts)


def _write_introduction(
    outline: ReportOutline, aggregated: AggregatedFindings, llm
) -> tuple[str, int]:
    """Write the introduction/executive summary."""
    # Format sections overview
    sections_overview = "\n".join(
        f"- {s.heading}: {s.target_word_count} words" for s in outline.sections
    )

    prompt = INTRODUCTION_WRITER_PROMPT.format(
        report_title=outline.title,
        original_query=aggregated.original_query,
        target_language=outline.target_language,
        executive_summary_points="\n".join(f"- {p}" for p in outline.executive_summary_points),
        sections_overview=sections_overview,
        themes=", ".join(aggregated.themes) if aggregated.themes else "Various aspects",
        target_word_count=min(500, outline.target_word_count // 10),
    )

    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    word_count = count_words(content)

    return content, word_count


def _write_section(
    section_idx: int,
    outline: ReportOutline,
    aggregated: AggregatedFindings,
    llm,
) -> tuple[str, int]:
    """Write a single section of the report."""
    section = outline.sections[section_idx]

    # Get relevant findings for this section
    relevant_findings = _get_relevant_findings(section.relevant_finding_ids, aggregated.findings)
    findings_text = _format_findings_for_section(relevant_findings)

    prompt = SECTION_WRITER_PROMPT.format(
        report_title=outline.title,
        original_query=aggregated.original_query,
        target_language=outline.target_language,
        section_heading=section.heading,
        subheadings=", ".join(section.subheadings) if section.subheadings else "None",
        target_word_count=section.target_word_count,
        key_points="\n".join(f"- {p}" for p in section.key_points)
        if section.key_points
        else "Cover the topic comprehensively",
        relevant_findings=findings_text,
    )

    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    word_count = count_words(content)

    return content, word_count


def _write_conclusion(
    outline: ReportOutline, aggregated: AggregatedFindings, llm
) -> tuple[str, int]:
    """Write the conclusion section."""
    # Summarize all findings
    findings_summary = []
    for finding in aggregated.findings[:10]:  # Limit to top 10
        summary = f"- {finding.focus_area}: " + "; ".join(finding.findings[:2])
        findings_summary.append(summary)

    prompt = CONCLUSION_WRITER_PROMPT.format(
        report_title=outline.title,
        original_query=aggregated.original_query,
        target_language=outline.target_language,
        conclusion_points="\n".join(f"- {p}" for p in outline.conclusion_points),
        findings_summary="\n".join(findings_summary),
        target_word_count=min(800, outline.target_word_count // 8),
    )

    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    word_count = count_words(content)

    return content, word_count


def section_writer_node(state: dict) -> dict:
    """
    Write all sections of the report based on the outline.

    This node:
    1. Writes the introduction/executive summary
    2. Writes each main section using relevant findings
    3. Writes the conclusion
    4. Assembles the complete report

    Args:
        state: Current workflow state with report_outline and aggregated_findings

    Returns:
        Updated state with draft_report and section_word_counts
    """
    print_node_header("SECTION WRITER")

    # Get outline
    outline_dict = state.get("report_outline", {})
    if not outline_dict:
        print("  ⚠️ No report outline available")
        return {"draft_report": "", "section_word_counts": {}}

    # Get aggregated findings
    aggregated_dict = state.get("aggregated_findings", {})
    if not aggregated_dict:
        print("  ⚠️ No aggregated findings available")
        return {"draft_report": "", "section_word_counts": {}}

    # Reconstruct objects
    try:
        outline = ReportOutline.model_validate(outline_dict)
        aggregated = AggregatedFindings.model_validate(aggregated_dict)
    except Exception as e:
        print(f"  ⚠️ Failed to parse input data: {e}")
        return {"draft_report": "", "section_word_counts": {}}

    print(f"  Report title: {outline.title}")
    print(f"  Target language: {outline.target_language}")
    print(f"  Sections to write: {len(outline.sections)}")
    print(f"  Target word count: {outline.target_word_count}")

    # Initialize LLM
    llm = get_synthesizer_model()

    # Track word counts
    section_word_counts = {}
    report_parts = []
    total_words = 0

    # 1. Write introduction
    print("\n  📝 Writing introduction...")
    try:
        intro_content, intro_words = _write_introduction(outline, aggregated, llm)
        report_parts.append(intro_content)
        section_word_counts["introduction"] = intro_words
        total_words += intro_words
        print(f"     ✓ Introduction: {intro_words} words")
    except Exception as e:
        print(f"     ⚠️ Introduction failed: {e}")
        report_parts.append(f"# {outline.title}\n\n## Executive Summary\n\n[Introduction pending]")

    # 2. Write each main section
    print("\n  📝 Writing main sections...")
    for i, section in enumerate(outline.sections):
        try:
            section_content, section_words = _write_section(i, outline, aggregated, llm)
            report_parts.append(section_content)
            section_word_counts[section.section_id] = section_words
            total_words += section_words
            print(
                f"     ✓ {section.heading}: {section_words} words (target: {section.target_word_count})"
            )
        except Exception as e:
            print(f"     ⚠️ Section '{section.heading}' failed: {e}")
            report_parts.append(f"\n## {section.heading}\n\n[Section pending]")

    # 3. Write conclusion
    print("\n  📝 Writing conclusion...")
    try:
        conclusion_content, conclusion_words = _write_conclusion(outline, aggregated, llm)
        report_parts.append(conclusion_content)
        section_word_counts["conclusion"] = conclusion_words
        total_words += conclusion_words
        print(f"     ✓ Conclusion: {conclusion_words} words")
    except Exception as e:
        print(f"     ⚠️ Conclusion failed: {e}")
        report_parts.append("\n## Conclusion\n\n[Conclusion pending]")

    # Assemble report
    draft_report = "\n\n".join(report_parts)

    # Print summary
    print("\n  📊 Writing Summary:")
    print(f"     Total sections: {len(outline.sections) + 2}")  # +intro +conclusion
    print(f"     Total words: {total_words}")
    print(f"     Target words: {outline.target_word_count}")
    achievement = (
        (total_words / outline.target_word_count * 100) if outline.target_word_count > 0 else 0
    )
    print(f"     Achievement: {achievement:.1f}%")
    print()

    return {
        "draft_report": draft_report,
        "section_word_counts": section_word_counts,
        "total_word_count": total_words,
    }
