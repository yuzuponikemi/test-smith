from src.models import get_synthesizer_model
from src.prompts.synthesizer_prompt import (
    HIERARCHICAL_SYNTHESIZER_PROMPT,
    SYNTHESIZER_PROMPT,
    SYNTHESIZER_WITH_PROVENANCE_PROMPT,
)
from src.utils.logging_utils import print_node_header


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


def synthesizer_node(state):
    print_node_header("SYNTHESIZER")
    model = get_synthesizer_model()

    # Get execution mode
    execution_mode = state.get("execution_mode", "simple")
    original_query = state.get("query", "")

    if execution_mode == "hierarchical":
        # Hierarchical mode: Synthesize multiple subtask results
        master_plan = state.get("master_plan", {})
        subtask_results = state.get("subtask_results", {})

        print("  Mode: HIERARCHICAL")
        print(f"  Subtasks completed: {len(subtask_results)}")

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
        for subtask_id, result in subtask_results.items():
            # Find the subtask details
            subtask_details = next(
                (s for s in master_plan.get("subtasks", []) if s["subtask_id"] == subtask_id), None
            )
            if subtask_details:
                subtask_results_formatted.append(
                    f"### Subtask: {subtask_id}\n"
                    f"**Description:** {subtask_details['description']}\n"
                    f"**Focus Area:** {subtask_details['focus_area']}\n\n"
                    f"**Research Results:**\n{result}\n"
                )

        subtask_results_str = "\n\n---\n\n".join(subtask_results_formatted)

        # Use hierarchical synthesis prompt
        prompt = HIERARCHICAL_SYNTHESIZER_PROMPT.format(
            original_query=original_query,
            subtask_count=subtask_count,
            subtask_list=subtask_list_str,
            complexity_reasoning=complexity_reasoning,
            subtask_results_formatted=subtask_results_str,
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
            for i, result in enumerate(code_results, 1):
                code_results_str += f"Result {i}:\n"
                code_results_str += f"- Success: {result.get('success', False)}\n"
                code_results_str += f"- Output: {result.get('output', 'N/A')}\n"
                code_results_str += f"- Execution Mode: {result.get('execution_mode', 'N/A')}\n"
                if result.get("code"):
                    code_results_str += f"- Code:\n```python\n{result['code']}\n```\n"
                code_results_str += "\n"
            code_results_str += "**IMPORTANT:** Use the actual output values from the code execution results above in your final answer. Do not use placeholders like '[insert value]'.\n"

        if has_provenance:
            # Use citation-aware prompt
            source_summary = _format_source_summary(state)
            print(f"  Total sources for citations: {len(web_sources) + len(rag_sources)}")

            prompt = (
                SYNTHESIZER_WITH_PROVENANCE_PROMPT.format(
                    original_query=original_query,
                    allocation_strategy=allocation_strategy,
                    source_summary=source_summary,
                    analyzed_data=analyzed_data,
                )
                + code_results_str
            )
        else:
            # Fallback to original prompt
            prompt = (
                SYNTHESIZER_PROMPT.format(
                    original_query=original_query,
                    allocation_strategy=allocation_strategy,
                    web_queries=web_queries,
                    rag_queries=rag_queries,
                    analyzed_data=analyzed_data,
                    loop_count=loop_count,
                )
                + code_results_str
            )

    message = model.invoke(prompt)
    print("  ✓ Report generated successfully\n")

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

    return {"report": report_content}
