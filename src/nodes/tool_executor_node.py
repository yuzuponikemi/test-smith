"""
Tool Executor Node - Executes planned tool calls

This node takes the tool calls planned by the Tool Planner and executes them,
returning results that can be used to enhance the research findings.
"""

import json
from src.tools import get_tool_registry


def tool_executor(state):
    """
    Execute planned tool calls and return results.

    This node:
    1. Gets planned tool calls from state
    2. Executes each tool via the registry
    3. Collects and formats results

    Args:
        state: Current agent state with tool_calls

    Returns:
        dict: Updated state with tool_results
    """
    print("---TOOL EXECUTOR---")

    tool_calls = state.get("tool_calls", [])

    if not tool_calls:
        print("  No tool calls to execute")
        return {"tool_results": []}

    registry = get_tool_registry()
    results = []

    for i, call in enumerate(tool_calls):
        tool_name = call.get("tool_name", "")
        arguments = call.get("arguments", {})
        purpose = call.get("purpose", "N/A")

        print(f"  Executing [{i+1}/{len(tool_calls)}]: {tool_name}")
        print(f"    Purpose: {purpose}")

        if not registry.has_tool(tool_name):
            error_result = {
                "tool_name": tool_name,
                "purpose": purpose,
                "success": False,
                "result": f"Error: Tool '{tool_name}' not found"
            }
            results.append(error_result)
            print(f"    Error: Tool not found")
            continue

        try:
            # Execute tool (synchronously for node compatibility)
            result = registry.execute_tool_sync(tool_name, arguments)

            tool_result = {
                "tool_name": tool_name,
                "purpose": purpose,
                "arguments": arguments,
                "success": True,
                "result": str(result)
            }
            results.append(tool_result)

            # Truncate result for logging
            result_preview = str(result)[:200]
            print(f"    Result: {result_preview}{'...' if len(str(result)) > 200 else ''}")

        except Exception as e:
            error_result = {
                "tool_name": tool_name,
                "purpose": purpose,
                "arguments": arguments,
                "success": False,
                "result": f"Error: {str(e)}"
            }
            results.append(error_result)
            print(f"    Error: {str(e)}")

    # Format results as text for inclusion in analyzed_data
    formatted_results = format_tool_results(results)

    print(f"  Completed {len(results)} tool executions")
    print(f"  Successful: {sum(1 for r in results if r['success'])}")

    return {
        "tool_results": results,
        "tool_results_text": formatted_results
    }


def format_tool_results(results: list) -> str:
    """
    Format tool results as readable text for inclusion in analysis.

    Args:
        results: List of tool result dictionaries

    Returns:
        Formatted string with all tool results
    """
    if not results:
        return ""

    lines = ["## Tool Execution Results\n"]

    for result in results:
        tool_name = result.get("tool_name", "Unknown")
        purpose = result.get("purpose", "N/A")
        success = result.get("success", False)
        output = result.get("result", "No result")

        status = "SUCCESS" if success else "FAILED"
        lines.append(f"### {tool_name} [{status}]")
        lines.append(f"**Purpose:** {purpose}")
        lines.append(f"**Result:**\n```\n{output}\n```\n")

    return "\n".join(lines)


def tool_results_aggregator(state):
    """
    Aggregate tool results into analyzed_data for the synthesizer.

    This is an optional node that merges tool results with existing analysis.
    """
    print("---TOOL RESULTS AGGREGATOR---")

    tool_results_text = state.get("tool_results_text", "")

    if not tool_results_text:
        print("  No tool results to aggregate")
        return {}

    # Add tool results to analyzed_data
    current_data = state.get("analyzed_data", [])

    # Create enhanced analysis that includes tool results
    enhanced = f"""
## Computational Verification and Analysis

The following computational tools were used to verify and enhance the research findings:

{tool_results_text}

These tool results should be considered alongside the web and RAG research findings for comprehensive analysis.
"""

    print(f"  Aggregated tool results into analysis")

    return {"analyzed_data": [enhanced]}
