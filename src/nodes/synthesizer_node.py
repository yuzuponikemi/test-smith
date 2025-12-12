from datetime import datetime

from src.models import get_synthesizer_model
from src.prompts.synthesizer_prompt import (
    HIERARCHICAL_SYNTHESIZER_PROMPT,
    SYNTHESIZER_PROMPT,
    SYNTHESIZER_WITH_PROVENANCE_PROMPT,
)
from src.utils.logging_utils import print_node_header
from src.utils.result_validator import count_words, detect_language


def _format_source_summary(state: dict) -> str:
    """
    Format source information for the synthesizer prompt with citations.

    Creates a structured, easy-to-parse format that includes all metadata
    needed for proper citation in the final report.
    """
    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])

    if not web_sources and not rag_sources:
        return "No structured source data available."

    all_sources: list[dict] = []
    source_summary_lines = []

    # Add web sources
    for source in web_sources:
        source_num = len(all_sources) + 1
        source_id = source.get("source_id", f"web_{source_num}")
        title = source.get("title", "Unknown Title")
        url = source.get("url", "N/A")
        content = source.get("content_snippet", "")[:200]
        relevance = source.get("relevance_score", 0.5)

        # Store for summary
        all_sources.append(
            {"num": source_num, "title": title, "type": "Web", "url": url, "relevance": relevance}
        )

        # Format for LLM (verbose for clarity)
        source_entry = f"[{source_num}] {title}\n"
        source_entry += f"    Type: Web | ID: {source_id}\n"
        source_entry += f"    URL: {url}\n"
        source_entry += f"    Relevance: {relevance:.2f}\n"
        source_entry += f"    Content: {content}...\n"

        source_summary_lines.append(source_entry)

    # Add RAG sources
    for source in rag_sources:
        source_num = len(all_sources) + 1
        source_id = source.get("source_id", f"rag_{source_num}")
        title = source.get("title", "Unknown Document")
        content = source.get("content_snippet", "")[:200]
        relevance = source.get("relevance_score", 0.5)
        source_file = source.get("metadata", {}).get("source_file", "Unknown")

        # Store for summary
        all_sources.append(
            {
                "num": source_num,
                "title": title,
                "type": "Knowledge Base",
                "file": source_file,
                "relevance": relevance,
            }
        )

        # Format for LLM (verbose for clarity)
        source_entry = f"[{source_num}] {title}\n"
        source_entry += f"    Type: Knowledge Base | ID: {source_id}\n"
        source_entry += f"    File: {source_file}\n"
        source_entry += f"    Relevance: {relevance:.2f}\n"
        source_entry += f"    Content: {content}...\n"

        source_summary_lines.append(source_entry)

    # Create reference template that LLM can directly copy
    reference_template = "\n\nREFERENCE LIST FORMAT (copy this structure to References section):\n"
    reference_template += "=" * 80 + "\n"

    for src in all_sources:
        if src["type"] == "Web":
            reference_template += f'{src["num"]}. "{src["title"]}" - Type: Web\n'
            reference_template += f"   URL: {src['url']}\n"
            reference_template += f"   Relevance: {src['relevance']:.2f}\n\n"
        else:
            reference_template += f'{src["num"]}. "{src["title"]}" - Type: Knowledge Base\n'
            reference_template += f"   File: {src['file']}\n"
            reference_template += f"   Relevance: {src['relevance']:.2f}\n\n"

    reference_template += "=" * 80 + "\n"

    return "\n".join(source_summary_lines) + reference_template


def _get_report_length_guidance(depth_config) -> str:
    """Generate report length guidance based on research depth config."""
    detail_guidance = {
        "brief": "Write a concise summary. Focus on key points only.",
        "moderate": "Provide balanced coverage with relevant details.",
        "detailed": "Include comprehensive analysis with multiple perspectives and supporting evidence.",
        "exhaustive": "Provide exhaustive coverage with in-depth analysis, multiple viewpoints, extensive evidence, and thorough exploration of all aspects.",
    }

    return (
        f"\n## Report Length Requirements\n"
        f"- Target word count: {depth_config.target_word_count} words\n"
        f"- Minimum word count: {depth_config.min_word_count} words\n"
        f"- Detail level: {depth_config.detail_level.upper()}\n"
        f"- Guidance: {detail_guidance.get(depth_config.detail_level, detail_guidance['moderate'])}\n"
    )


def _count_words(text: str) -> int:
    """Count words in text, handling both English and Japanese."""
    import re

    # Remove markdown formatting
    text = re.sub(r"```[\s\S]*?```", "", text)  # Remove code blocks
    text = re.sub(r"`[^`]+`", "", text)  # Remove inline code
    text = re.sub(r"[#*_\[\]()>]", " ", text)  # Remove markdown chars

    # Count English words
    english_words = len(re.findall(r"[a-zA-Z]+", text))

    # Count Japanese characters (each counts as ~1 word equivalent)
    # This is an approximation: Japanese characters are counted individually
    japanese_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", text))

    # For Japanese, roughly 2-3 characters = 1 word equivalent
    japanese_word_equiv = japanese_chars // 2

    return english_words + japanese_word_equiv


def _validate_report_length(report: str, depth_config, research_depth: str) -> dict:
    """Validate report meets length requirements and return status."""
    word_count = _count_words(report)
    min_words = depth_config.min_word_count
    target_words = depth_config.target_word_count

    status = {
        "word_count": word_count,
        "min_required": min_words,
        "target": target_words,
        "meets_minimum": word_count >= min_words,
        "meets_target": word_count >= target_words,
        "percentage_of_target": round((word_count / target_words) * 100, 1)
        if target_words > 0
        else 0,
    }

    if word_count < min_words:
        status["warning"] = (
            f"⚠️ Report is {word_count} words, below minimum of {min_words} "
            f"for {research_depth} depth ({status['percentage_of_target']}% of target)"
        )
    elif word_count < target_words:
        status["info"] = (
            f"ℹ️ Report is {word_count} words, {status['percentage_of_target']}% of "
            f"target {target_words} for {research_depth} depth"
        )
    else:
        status["success"] = f"✓ Report meets target: {word_count} words (target: {target_words})"

    return status


def _get_synthesizer_depth_guidance(research_depth: str) -> str:
    """Generate depth-specific guidance for report synthesis."""
    guidance_map = {
        "quick": """**Quick Research Mode**
- Target: ~1,000 words (2-3 pages)
- Focus: Concise, direct answers
- Sections: Summary + 1-2 main sections + Key Takeaways
- Style: Brief but informative""",
        "standard": """**Standard Research Mode**
- Target: ~3,000 words (6-8 pages)
- Focus: Balanced coverage with moderate depth
- Sections: Executive Summary + 3-5 main sections + Conclusion
- Style: Professional report with clear structure""",
        "deep": """**Deep Research Mode**
- Target: ~6,000 words (12-15 pages)
- Focus: In-depth analysis with multiple perspectives
- Sections: Comprehensive coverage of all subtasks with detailed analysis
- Style: Academic-quality with thorough examination of each aspect""",
        "comprehensive": """**Comprehensive Research Mode**
- Target: ~10,000 words (20-25 pages, A4 10枚以上)
- Focus: Exhaustive, multi-dimensional coverage
- Sections: Detailed analysis of EVERY subtask + cross-cutting insights + thorough conclusion
- Style: Authoritative reference document
- IMPORTANT: This is the MOST THOROUGH mode - include ALL relevant details, examples, and analysis
- Each major subtask should have its own substantial section (500-1000 words per subtask)""",
    }
    return guidance_map.get(research_depth, guidance_map["standard"])


def synthesizer_node(state):
    print_node_header("SYNTHESIZER")
    model = get_synthesizer_model()

    # Get execution mode and research depth
    execution_mode = state.get("execution_mode", "simple")
    original_query = state.get("query", "")
    research_depth = state.get("research_depth", "standard")

    # Get depth-aware report settings
    from src.config.research_depth import get_depth_config

    depth_config = get_depth_config(research_depth)
    report_guidance = _get_report_length_guidance(depth_config)

    print(f"  Research depth: {research_depth}")
    print(f"  Target word count: {depth_config.target_word_count}")

    if execution_mode == "hierarchical":
        # Hierarchical mode: Synthesize multiple subtask results
        master_plan = state.get("master_plan", {})
        subtask_results = state.get("subtask_results", {})
        aggregated_findings = state.get("aggregated_findings", {})
        findings_ready = state.get("findings_ready", False)

        # Check if Writer Graph has produced a draft report
        draft_report = state.get("draft_report", "")
        total_word_count = state.get("total_word_count", 0)

        print("  Mode: HIERARCHICAL")
        print(f"  Subtasks completed: {len(subtask_results)}")

        # If Writer Graph has produced a draft report, use it directly
        if draft_report and total_word_count > 500:
            print(f"  Writer Graph report: ✓ available ({total_word_count} words)")
            print("  Using Writer Graph output as final report")
            return {"report": draft_report}

        # Log aggregation status if available
        if aggregated_findings:
            print("  Aggregated findings: ✓ available")
            print(f"    - Target language: {aggregated_findings.get('target_language', 'unknown')}")
            print(f"    - Avg quality: {aggregated_findings.get('average_quality_score', 0):.2f}")
            print(f"    - Themes found: {len(aggregated_findings.get('themes', []))}")
            print(f"    - Ready for writing: {'✓' if findings_ready else '✗'}")
            if aggregated_findings.get("coverage_gaps"):
                print(f"    - Coverage gaps: {aggregated_findings['coverage_gaps']}")
        else:
            print("  Aggregated findings: Not available (using raw subtask results)")

        # Format subtask information for prompt
        subtask_count = len(master_plan.get("subtasks", []))
        complexity_reasoning = master_plan.get("complexity_reasoning", "No reasoning provided")

        # Create subtask list
        subtask_list = []
        for i, subtask in enumerate(master_plan.get("subtasks", []), 1):
            subtask_list.append(
                f"{i}. [{subtask['subtask_id']}] {subtask['description']}\n"
                f"   Focus: {subtask['focus_area']}\n"
                f"   Priority: {subtask['priority']}, Importance: {subtask['estimated_importance']}"
            )
        subtask_list_str = "\n\n".join(subtask_list)

        # Format subtask results
        subtask_results_formatted = []
        for subtask_id, subtask_result in subtask_results.items():
            # Find the subtask details
            subtask_details = next(
                (s for s in master_plan.get("subtasks", []) if s["subtask_id"] == subtask_id), None
            )
            if subtask_details:
                subtask_results_formatted.append(
                    f"### Subtask: {subtask_id}\n"
                    f"**Description:** {subtask_details['description']}\n"
                    f"**Focus Area:** {subtask_details['focus_area']}\n\n"
                    f"**Research Results:**\n{subtask_result}\n"
                )

        subtask_results_str = "\n\n---\n\n".join(subtask_results_formatted)

        # Get depth-specific guidance for synthesizer
        depth_guidance = _get_synthesizer_depth_guidance(research_depth)

        # Build aggregation summary if available
        aggregation_summary = ""
        if aggregated_findings:
            target_lang = aggregated_findings.get("target_language", "en")
            themes = aggregated_findings.get("themes", [])
            avg_quality = aggregated_findings.get("average_quality_score", 0)
            total_words = aggregated_findings.get("total_word_count", 0)
            coverage_gaps = aggregated_findings.get("coverage_gaps", [])

            aggregation_summary = f"""
## Quality Analysis Summary
- **Target Language**: {target_lang} (IMPORTANT: Write the entire report in this language)
- **Average Quality Score**: {avg_quality:.2f}/1.0
- **Total Research Words**: {total_words}
- **Cross-cutting Themes**: {", ".join(themes) if themes else "None identified"}
"""
            if coverage_gaps:
                aggregation_summary += f"- **Coverage Gaps**: {'; '.join(coverage_gaps)}\n"
            aggregation_summary += "\n"

        # Use hierarchical synthesis prompt with depth guidance
        prompt = (
            HIERARCHICAL_SYNTHESIZER_PROMPT.format(
                original_query=original_query,
                subtask_count=subtask_count,
                subtask_list=subtask_list_str,
                complexity_reasoning=complexity_reasoning,
                subtask_results_formatted=subtask_results_str,
                research_depth=research_depth,
                depth_guidance=depth_guidance,
            )
            + aggregation_summary
            + report_guidance
        )

    else:
        # Simple mode: Use synthesis with citations if provenance data available
        print("  Mode: SIMPLE")

        allocation_strategy = state.get("allocation_strategy", "")
        web_queries = state.get("web_queries", [])
        rag_queries = state.get("rag_queries", [])
        analyzed_data = state.get("analyzed_data", [])
        loop_count = state.get("loop_count", 0)

        # Check if provenance data is available
        web_sources = state.get("web_sources", [])
        rag_sources = state.get("rag_sources", [])
        has_provenance = bool(web_sources or rag_sources)

        # Get code execution results if available
        code_results = state.get("code_execution_results", [])

        print(f"  Iterations: {loop_count}")
        print(f"  Total analyzed data entries: {len(analyzed_data)}")
        print(f"  Code execution results: {len(code_results)}")
        print(f"  Provenance tracking: {'enabled' if has_provenance else 'disabled'}")

        # Format code results for inclusion in prompt
        code_results_str = ""
        if code_results:
            code_results_str = "\n\n**CODE EXECUTION RESULTS:**\n"
            code_results_str += "The following code was executed to answer the query:\n\n"
            for i, code_result in enumerate(code_results, 1):
                code_results_str += f"Result {i}:\n"
                code_results_str += f"- Success: {code_result.get('success', False)}\n"
                code_results_str += f"- Output: {code_result.get('output', 'N/A')}\n"
                code_results_str += f"- Execution Mode: {code_result.get('execution_mode', 'N/A')}\n"
                if code_result.get("code"):
                    code_results_str += f"- Code:\n```python\n{code_result['code']}\n```\n"
                code_results_str += "\n"
            code_results_str += "**IMPORTANT:** Use the actual output values from the code execution results above in your final answer. Do not use placeholders like '[insert value]'.\n"

        if has_provenance:
            # Use citation-aware prompt with depth guidance
            source_summary = _format_source_summary(state)
            print(f"  Total sources for citations: {len(web_sources) + len(rag_sources)}")

            prompt = (
                SYNTHESIZER_WITH_PROVENANCE_PROMPT.format(
                    original_query=original_query,
                    allocation_strategy=allocation_strategy,
                    source_summary=source_summary,
                    analyzed_data=analyzed_data,
                )
                + report_guidance
                + code_results_str
            )
        else:
            # Fallback to original prompt with depth guidance
            prompt = (
                SYNTHESIZER_PROMPT.format(
                    original_query=original_query,
                    allocation_strategy=allocation_strategy,
                    web_queries=web_queries,
                    rag_queries=rag_queries,
                    analyzed_data=analyzed_data,
                    loop_count=loop_count,
                )
                + report_guidance
                + code_results_str
            )

    message = model.invoke(prompt)
    print("  ✓ Report generated successfully")

    # Validate report length
    length_status = _validate_report_length(message.content, depth_config, research_depth)
    if "warning" in length_status:
        print(f"  {length_status['warning']}")
    elif "info" in length_status:
        print(f"  {length_status['info']}")
    else:
        print(f"  {length_status.get('success', '')}")
    print()

    # Post-process: Ensure proper references section if provenance data available
    report_content = message.content

    if execution_mode == "simple" and has_provenance:
        # Generate clean reference list programmatically
        reference_lines = ["\n\n**References**\n"]

        all_sources_list: list[dict] = []

        # Add web sources
        for source in web_sources:
            source_num = len(all_sources_list) + 1
            title = source.get("title", "Unknown Title")
            url = source.get("url", "N/A")
            relevance = source.get("relevance_score", 0.5)

            all_sources_list.append(
                {
                    "num": source_num,
                    "title": title,
                    "type": "Web",
                    "url": url,
                    "relevance": relevance,
                }
            )

        # Add RAG sources
        for source in rag_sources:
            source_num = len(all_sources_list) + 1
            title = source.get("title", "Unknown Document")
            relevance = source.get("relevance_score", 0.5)
            source_file = source.get("metadata", {}).get("source_file", "Unknown")

            all_sources_list.append(
                {
                    "num": source_num,
                    "title": title,
                    "type": "Knowledge Base",
                    "file": source_file,
                    "relevance": relevance,
                }
            )

        # Format all sources
        for src in all_sources_list:
            if src["type"] == "Web":
                reference_lines.append(f'{src["num"]}. "{src["title"]}" - Type: Web\n')
                reference_lines.append(f"   URL: {src['url']}\n")
                reference_lines.append(f"   Relevance: {src['relevance']:.2f}\n\n")
            else:
                reference_lines.append(f'{src["num"]}. "{src["title"]}" - Type: Knowledge Base\n')
                reference_lines.append(f"   File: {src['file']}\n")
                reference_lines.append(f"   Relevance: {src['relevance']:.2f}\n\n")

        # Check if report already has a References section
        if "**References**" in report_content or "## References" in report_content:
            # Remove existing incomplete references section
            parts = report_content.split("**References**")
            if len(parts) > 1:
                report_content = parts[0].rstrip()
            else:
                parts = report_content.split("## References")
                if len(parts) > 1:
                    report_content = parts[0].rstrip()

        # Append complete references
        report_content += "".join(reference_lines)
        print(f"  ✓ Added {len(all_sources_list)} references programmatically\n")

    # Build aggregated_findings for SIMPLE mode to enable research data saving
    result: dict = {"report": report_content}

    if execution_mode == "simple":
        # Calculate report metrics
        report_word_count = count_words(report_content)
        detected_lang = detect_language(report_content)

        # Build simple mode findings from analyzed_data
        simple_findings = {
            "original_query": original_query,
            "research_depth": research_depth,
            "target_language": detected_lang,
            "execution_mode": "simple",
            "total_subtasks": 1,
            "successful_subtasks": 1,
            "findings": [
                {
                    "subtask_id": "simple_research",
                    "query": original_query,
                    "focus_area": "General Research",
                    "language": detected_lang,
                    "findings": analyzed_data if analyzed_data else [],
                    "key_insights": [],
                    "sources": [],
                    "quality_score": min(1.0, report_word_count / depth_config.target_word_count),
                    "relevance_score": 1.0,
                    "word_count": report_word_count,
                    "contains_meta_description": False,
                    "metadata": {
                        "web_queries": web_queries,
                        "rag_queries": rag_queries,
                        "allocation_strategy": allocation_strategy,
                        "loop_count": loop_count,
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            ],
            "themes": [],
            "contradictions": [],
            "coverage_gaps": [],
            "total_word_count": report_word_count,
            "average_quality_score": min(1.0, report_word_count / depth_config.target_word_count),
            "ready_for_writing": True,
            "validation_notes": [],
            "report_word_count": report_word_count,
            "target_word_count": depth_config.target_word_count,
        }

        # Add source information if available
        if has_provenance:
            simple_findings["findings"][0]["sources"] = [
                {"type": "web", "url": s.get("url", ""), "title": s.get("title", "")}
                for s in web_sources
            ] + [
                {
                    "type": "rag",
                    "file": s.get("metadata", {}).get("source_file", ""),
                    "title": s.get("title", ""),
                }
                for s in rag_sources
            ]

        result["aggregated_findings"] = simple_findings
        print(f"  ✓ Built research data for SIMPLE mode ({report_word_count} words)")

    return result
