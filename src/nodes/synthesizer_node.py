from src.models import get_synthesizer_model
from src.utils.logging_utils import print_node_header
from src.prompts.synthesizer_prompt import SYNTHESIZER_PROMPT, HIERARCHICAL_SYNTHESIZER_PROMPT
import json

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
        # Simple mode: Use existing synthesis (unchanged)
        print(f"  Mode: SIMPLE")

        allocation_strategy = state.get("allocation_strategy", "")
        web_queries = state.get("web_queries", [])
        rag_queries = state.get("rag_queries", [])
        analyzed_data = state.get("analyzed_data", [])
        loop_count = state.get("loop_count", 0)

        # Get code execution results if available
        code_results = state.get("code_execution_results", [])

        print(f"  Iterations: {loop_count}")
        print(f"  Total analyzed data entries: {len(analyzed_data)}")
        print(f"  Code execution results: {len(code_results)}")

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
                if result.get('code'):
                    code_results_str += f"- Code:\n```python\n{result['code']}\n```\n"
                code_results_str += "\n"
            code_results_str += "**IMPORTANT:** Use the actual output values from the code execution results above in your final answer. Do not use placeholders like '[insert value]'.\n"

        prompt = SYNTHESIZER_PROMPT.format(
            original_query=original_query,
            allocation_strategy=allocation_strategy,
            web_queries=web_queries,
            rag_queries=rag_queries,
            analyzed_data=analyzed_data,
            loop_count=loop_count
        ) + code_results_str

    message = model.invoke(prompt)
    print("  ✓ Report generated successfully\n")

    return {"report": message.content}
