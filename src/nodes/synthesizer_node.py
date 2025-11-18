from src.models import get_synthesizer_model
from src.utils.logging_utils import print_node_header
from src.prompts.synthesizer_prompt import (
    SYNTHESIZER_PROMPT,
    HIERARCHICAL_SYNTHESIZER_PROMPT,
    SYNTHESIZER_WITH_PROVENANCE_PROMPT
)
import json


def _format_source_summary(state: dict) -> str:
    """Format source information for the synthesizer prompt with citations."""
    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])

    if not web_sources and not rag_sources:
        return "No structured source data available."

    all_sources = []

    # Add web sources
    for source in web_sources:
        source_num = len(all_sources) + 1
        source_id = source.get("source_id", f"web_{source_num}")
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        content = source.get("content_snippet", "")[:200]
        relevance = source.get("relevance_score", 0.5)

        source_entry = f"[{source_num}] {title}\n"
        source_entry += f"    Type: Web | ID: {source_id}\n"
        if url:
            source_entry += f"    URL: {url}\n"
        source_entry += f"    Relevance: {relevance:.2f}\n"
        source_entry += f"    Content: {content}...\n"

        all_sources.append(source_entry)

    # Add RAG sources
    for source in rag_sources:
        source_num = len(all_sources) + 1
        source_id = source.get("source_id", f"rag_{source_num}")
        title = source.get("title", "Unknown Document")
        content = source.get("content_snippet", "")[:200]
        relevance = source.get("relevance_score", 0.5)
        source_file = source.get("metadata", {}).get("source_file", "")

        source_entry = f"[{source_num}] {title}\n"
        source_entry += f"    Type: Knowledge Base | ID: {source_id}\n"
        if source_file:
            source_entry += f"    File: {source_file}\n"
        source_entry += f"    Relevance: {relevance:.2f}\n"
        source_entry += f"    Content: {content}...\n"

        all_sources.append(source_entry)

    return "\n".join(all_sources)

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

        print(f"  Mode: HIERARCHICAL")
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
                (s for s in master_plan.get("subtasks", []) if s["subtask_id"] == subtask_id),
                None
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
            subtask_results_formatted=subtask_results_str
        )

    else:
        # Simple mode: Use synthesis with citations if provenance data available
        print(f"  Mode: SIMPLE")

        allocation_strategy = state.get("allocation_strategy", "")
        web_queries = state.get("web_queries", [])
        rag_queries = state.get("rag_queries", [])
        analyzed_data = state.get("analyzed_data", [])
        loop_count = state.get("loop_count", 0)

        # Check if provenance data is available
        web_sources = state.get("web_sources", [])
        rag_sources = state.get("rag_sources", [])
        has_provenance = bool(web_sources or rag_sources)

        print(f"  Iterations: {loop_count}")
        print(f"  Total analyzed data entries: {len(analyzed_data)}")
        print(f"  Provenance tracking: {'enabled' if has_provenance else 'disabled'}")

        if has_provenance:
            # Use citation-aware prompt
            source_summary = _format_source_summary(state)
            print(f"  Total sources for citations: {len(web_sources) + len(rag_sources)}")

            prompt = SYNTHESIZER_WITH_PROVENANCE_PROMPT.format(
                original_query=original_query,
                allocation_strategy=allocation_strategy,
                source_summary=source_summary,
                analyzed_data=analyzed_data
            )
        else:
            # Fallback to original prompt
            prompt = SYNTHESIZER_PROMPT.format(
                original_query=original_query,
                allocation_strategy=allocation_strategy,
                web_queries=web_queries,
                rag_queries=rag_queries,
                analyzed_data=analyzed_data,
                loop_count=loop_count
            )

    message = model.invoke(prompt)
    print("  ✓ Report generated successfully\n")

    return {"report": message.content}
