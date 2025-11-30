from src.models import get_analyzer_model
from src.prompts.analyzer_prompt import ANALYZER_PROMPT
from src.utils.logging_utils import print_node_header


def analyzer_node(state):
    print_node_header("ANALYZER")
    model = get_analyzer_model()

    # Get strategic context
    original_query = state.get("query", "")
    allocation_strategy = state.get("allocation_strategy", "No strategy provided")
    web_queries = state.get("web_queries", [])
    rag_queries = state.get("rag_queries", [])

    # Get results separately to maintain source context
    web_results = state.get("search_results", [])
    rag_results = state.get("rag_results", [])

    # Get code execution results if available
    code_results = state.get("code_execution_results", [])

    print(
        f"  Analyzing {len(web_results)} web results, {len(rag_results)} RAG results, {len(code_results)} code results"
    )
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

    prompt = (
        ANALYZER_PROMPT.format(
            original_query=original_query,
            allocation_strategy=allocation_strategy,
            web_queries=web_queries,
            rag_queries=rag_queries,
            web_results=web_results,
            rag_results=rag_results,
        )
        + code_results_str
    )

    message = model.invoke(prompt)
    return {"analyzed_data": [message.content]}
