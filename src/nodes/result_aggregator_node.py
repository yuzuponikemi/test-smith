"""
Result Aggregator Node - Phase 1.3

Aggregates and validates all subtask results into a structured format
that can be passed to the Writer Graph for report generation.
"""

from datetime import datetime

from src.schemas import AggregatedFindings, SubtaskFinding
from src.utils.logging_utils import print_node_header
from src.utils.result_validator import (
    detect_language,
    validate_subtask_result,
)


def _extract_findings_from_text(text: str) -> list[str]:
    """
    Extract individual findings from analysis text.

    Looks for bullet points, numbered lists, or paragraph breaks.
    """
    if not text:
        return []

    findings = []

    # Try to extract bullet points first
    bullet_matches = [
        line.strip() for line in text.split("\n") if line.strip().startswith(("-", "*", "•", "・"))
    ]

    if bullet_matches:
        for match in bullet_matches:
            # Remove bullet prefix
            finding = match.lstrip("-*•・ ").strip()
            if finding and len(finding) > 20:  # Filter out short fragments
                findings.append(finding)
        return findings[:10]  # Limit to 10 findings

    # Try numbered lists
    import re

    numbered_matches = re.findall(r"^\d+[\.\)]\s*(.+)", text, re.MULTILINE)
    if numbered_matches:
        for match in numbered_matches:
            if match and len(match) > 20:
                findings.append(match.strip())
        return findings[:10]

    # Fall back to paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for para in paragraphs[:5]:
        if len(para) > 50:
            # Take first 500 chars of each paragraph
            findings.append(para[:500])

    return findings


def _identify_themes(findings: list[SubtaskFinding]) -> list[str]:
    """
    Identify cross-cutting themes across subtask findings.

    Simple keyword-based approach - could be enhanced with LLM.
    """
    # Count keyword frequencies across all findings
    import re
    from collections import Counter

    all_text = " ".join(" ".join(f.findings) for f in findings)

    # Extract significant words (longer than 4 chars, not common)
    words = re.findall(r"\b[a-zA-Z\u3040-\u9fff]{4,}\b", all_text.lower())

    # Filter common words
    common_words = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "been",
        "were",
        "which",
        "their",
        "there",
        "about",
        "would",
        "could",
        "should",
        "these",
        "those",
        "also",
        "more",
        "some",
        "such",
        "other",
        "into",
    }
    words = [w for w in words if w not in common_words]

    # Get top themes
    word_counts = Counter(words)
    themes = [word for word, count in word_counts.most_common(5) if count >= 2]

    return themes


def _find_contradictions(_findings: list[SubtaskFinding]) -> list[dict]:
    """
    Find potential contradictions between subtask findings.

    Simple heuristic - looks for negation patterns.
    Could be enhanced with LLM-based comparison.

    Args:
        _findings: List of subtask findings (currently unused, placeholder for LLM)

    Returns:
        List of contradiction dictionaries
    """
    # This is a placeholder - real implementation would use LLM
    # to compare findings across subtasks
    return []


def result_aggregator_node(state):
    """
    Aggregate and validate all subtask results.

    This node:
    1. Validates each subtask's results for quality
    2. Extracts structured findings from raw text
    3. Identifies themes and contradictions
    4. Produces AggregatedFindings for the Writer Graph

    Args:
        state: Current workflow state with subtask_results

    Returns:
        Updated state with aggregated_findings
    """
    print_node_header("RESULT AGGREGATOR")

    original_query = state.get("query", "")
    research_depth = state.get("research_depth", "standard")
    subtask_results = state.get("subtask_results", {})
    master_plan = state.get("master_plan", {})

    # Get subtask metadata from master plan
    subtasks = master_plan.get("subtasks", [])
    subtask_metadata = {
        s["subtask_id"]: {
            "query": s.get("description", ""),
            "focus_area": s.get("focus_area", ""),
        }
        for s in subtasks
    }

    print(f"  Query: {original_query[:80]}...")
    print(f"  Research depth: {research_depth}")
    print(f"  Subtasks to aggregate: {len(subtask_results)}")

    # Determine target language from query
    target_language = detect_language(original_query)
    print(f"  Target language: {target_language}")

    # Validate all subtask results
    print("\n  📋 Validating subtask results...")

    validated_findings: list[SubtaskFinding] = []
    total_word_count = 0
    quality_scores = []

    for subtask_id, result_text in subtask_results.items():
        metadata = subtask_metadata.get(subtask_id, {})

        # Validate the result
        validation = validate_subtask_result(
            text=result_text,
            original_query=original_query,
            subtask_query=metadata.get("query", ""),
            focus_area=metadata.get("focus_area", ""),
            expected_language=target_language,
            min_word_count=50,  # Lower threshold for subtasks
        )

        # Extract structured findings
        findings_list = _extract_findings_from_text(result_text)

        # Create SubtaskFinding
        finding = SubtaskFinding(
            subtask_id=subtask_id,
            query=metadata.get("query", subtask_id),
            focus_area=metadata.get("focus_area", ""),
            language=validation.detected_language,
            findings=findings_list,
            key_insights=[],  # Could be populated by LLM
            sources=[],  # Would come from provenance tracking
            quality_score=validation.quality_score,
            relevance_score=validation.relevance_score,
            word_count=validation.word_count,
            contains_meta_description=validation.contains_meta_description,
            metadata={
                "validated_at": datetime.now().isoformat(),
                "issues": validation.issues,
                "warnings": validation.warnings,
            },
        )

        validated_findings.append(finding)
        total_word_count += validation.word_count
        quality_scores.append(validation.quality_score)

        # Log validation status
        status = "✓" if validation.is_valid else "⚠"
        print(
            f"     {status} {subtask_id}: q={validation.quality_score:.2f}, "
            f"words={validation.word_count}, findings={len(findings_list)}"
        )

    # Calculate aggregate metrics
    successful_subtasks = sum(1 for f in validated_findings if f.quality_score >= 0.4)
    average_quality = sum(quality_scores) / max(len(quality_scores), 1)

    # Identify themes and contradictions
    themes = _identify_themes(validated_findings)
    contradictions = _find_contradictions(validated_findings)

    # Check for coverage gaps
    coverage_gaps = []
    if len(validated_findings) < len(subtasks):
        missing = set(subtask_metadata.keys()) - set(subtask_results.keys())
        if missing:
            coverage_gaps.append(f"Missing subtasks: {missing}")

    low_quality_areas = [f.focus_area for f in validated_findings if f.quality_score < 0.4]
    if low_quality_areas:
        coverage_gaps.append(f"Low quality coverage: {low_quality_areas}")

    # Determine if ready for writing
    ready_for_writing = (
        successful_subtasks >= len(subtasks) * 0.5  # At least 50% successful
        and average_quality >= 0.4
        and total_word_count >= 200  # Minimum content threshold
    )

    # Build validation notes
    validation_notes = []
    if not ready_for_writing:
        if successful_subtasks < len(subtasks) * 0.5:
            validation_notes.append(
                f"Too few successful subtasks: {successful_subtasks}/{len(subtasks)}"
            )
        if average_quality < 0.4:
            validation_notes.append(f"Average quality too low: {average_quality:.2f}")
        if total_word_count < 200:
            validation_notes.append(f"Total content too short: {total_word_count} words")

    # Create aggregated findings
    aggregated = AggregatedFindings(
        original_query=original_query,
        research_depth=research_depth,
        target_language=target_language,
        total_subtasks=len(subtasks),
        successful_subtasks=successful_subtasks,
        findings=validated_findings,
        themes=themes,
        contradictions=contradictions,
        coverage_gaps=coverage_gaps,
        total_word_count=total_word_count,
        average_quality_score=round(average_quality, 2),
        ready_for_writing=ready_for_writing,
        validation_notes=validation_notes,
    )

    # Print summary
    print("\n  📊 Aggregation Summary:")
    print(f"     Total subtasks: {len(subtasks)}")
    print(
        f"     Successful: {successful_subtasks} ({successful_subtasks / max(len(subtasks), 1) * 100:.0f}%)"
    )
    print(f"     Average quality: {average_quality:.2f}")
    print(f"     Total words: {total_word_count}")
    print(f"     Themes found: {len(themes)}")
    print(f"     Ready for writing: {'✓ Yes' if ready_for_writing else '✗ No'}")

    if not ready_for_writing:
        print("\n  ⚠️  Not ready for writing:")
        for note in validation_notes:
            print(f"     - {note}")

    print()

    return {
        "aggregated_findings": aggregated.model_dump(),
        "findings_ready": ready_for_writing,
    }
