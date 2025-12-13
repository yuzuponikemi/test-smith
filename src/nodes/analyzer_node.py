from src.models import get_analyzer_model
from src.prompts.analyzer_prompt import ANALYZER_PROMPT
from src.utils.logging_utils import print_node_header
from src.utils.structured_logging import log_analysis_summary, log_node_execution, log_performance


def analyzer_node(state):
    print_node_header("ANALYZER")

    with log_node_execution("analyzer", state) as logger:
        model = get_analyzer_model()

        # Get strategic context
        original_query = state.get("query", "")
        allocation_strategy = (
            state.get("allocation_strategy", "No strategy provided") or "No strategy provided"
        )
        web_queries = state.get("web_queries", []) or []
        rag_queries = state.get("rag_queries", []) or []

        # Get results separately to maintain source context
        web_results = state.get("search_results", []) or []
        rag_results = state.get("rag_results", []) or []

        # Get code execution results if available
        code_results = state.get("code_execution_results", []) or []

        # Get term definitions for consistency checking
        term_definitions = state.get("term_definitions", {})

        # Log analysis summary
        log_analysis_summary(logger, len(web_results), len(rag_results), len(code_results))

        print(
            f"  Analyzing {len(web_results)} web results, {len(rag_results)} RAG results, {len(code_results)} code results"
        )
        if term_definitions:
            print(f"  Term definitions available: {list(term_definitions.keys())}")
        print(f"  Strategy: {allocation_strategy[:100]}...")

        # Format code results for inclusion in prompt
        code_results_str = ""
        if code_results:
            code_results_str = "\n\n**CODE EXECUTION RESULTS:**\n"
            for i, result in enumerate(code_results, 1):
                code_results_str += f"\nResult {i}:\n"
                code_results_str += f"- Success: {result.get('success', False)}\n"
                code_results_str += f"- Output: {result.get('output', 'N/A')}\n"
                code_results_str += f"- Execution Mode: {result.get('execution_mode', 'N/A')}\n"
                if result.get("code"):
                    code_results_str += f"- Code:\n```python\n{result['code']}\n```\n"

        # Format term definitions for prompt
        term_definitions_section = _format_term_definitions(term_definitions)

        prompt = (
            ANALYZER_PROMPT.format(
                original_query=original_query,
                allocation_strategy=allocation_strategy,
                web_queries=web_queries,
                rag_queries=rag_queries,
                web_results=web_results,
                rag_results=rag_results,
                term_definitions_section=term_definitions_section,
            )
            + code_results_str
        )

        logger.info(
            "analysis_llm_invoke_start",
            strategy_length=len(allocation_strategy),
            has_code_results=len(code_results) > 0,
        )

        with log_performance(logger, "analysis_llm_call"):
            message = model.invoke(prompt)

        logger.info("analysis_complete", analysis_length=len(message.content))

        return {"analyzed_data": [message.content]}


def _format_term_definitions(term_definitions: dict) -> str:
    """Format term definitions for inclusion in the analyzer prompt."""
    if not term_definitions:
        return "No technical terms were pre-verified for this query."

    lines = ["The following terms have been verified BEFORE research began:\n"]

    for term, info in term_definitions.items():
        confidence = info.get("confidence", "unknown")
        confidence_marker = {"high": "✓", "medium": "?", "low": "⚠"}.get(confidence, "?")

        lines.append(f"**{term}** {confidence_marker}")
        lines.append(f"- Category: {info.get('category', 'unknown')}")
        lines.append(f"- Definition: {info.get('definition', 'Unknown')}")

        features = info.get("key_features", [])
        if features:
            lines.append(f"- Key features: {', '.join(features[:3])}")

        confusions = info.get("common_confusions", [])
        if confusions:
            lines.append(f"- NOT to be confused with: {', '.join(confusions[:2])}")

        lines.append("")

    return "\n".join(lines)
