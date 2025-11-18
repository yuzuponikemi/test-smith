"""
Tool Planner Node - Decides which tools to use based on research findings

This node analyzes the current research context and determines if computational
tools should be used to verify, calculate, or enhance the findings.
"""

import json
from src.models import get_evaluation_model
from src.tools import get_tool_registry


TOOL_PLANNER_PROMPT = """You are a Tool Planner for a research system. Your job is to analyze research findings and determine if any computational tools should be used to verify, calculate, or enhance the information.

## Available Tools

{tool_descriptions}

## Current Research Context

**Original Query:** {query}

**Current Findings:**
{analyzed_data}

## Your Task

Analyze the findings and determine:
1. Are there any numerical claims that need verification?
2. Are there calculations that should be performed?
3. Would any data analysis improve the research quality?
4. Are there conversions, statistics, or code execution needs?

## Response Format

Respond with a JSON object:
```json
{{
    "needs_tools": true/false,
    "reasoning": "Why tools are or aren't needed",
    "tool_calls": [
        {{
            "tool_name": "name of the tool",
            "arguments": {{"arg1": "value1"}},
            "purpose": "What this tool call will verify/compute"
        }}
    ]
}}
```

If no tools are needed, return:
```json
{{
    "needs_tools": false,
    "reasoning": "Explanation of why no tools are needed",
    "tool_calls": []
}}
```

Analyze the findings and plan tool usage:"""


def tool_planner(state):
    """
    Analyze research findings and plan tool usage.

    This node:
    1. Gets available tools from registry
    2. Analyzes current findings for computation needs
    3. Plans which tools to execute and with what arguments

    Args:
        state: Current agent state with analyzed_data

    Returns:
        dict: Updated state with tool_calls (list of planned tool invocations)
    """
    print("---TOOL PLANNER---")

    # Check if tools are enabled
    tools_enabled = state.get("tools_enabled", True)
    if not tools_enabled:
        print("  Tools disabled - skipping")
        return {"tool_calls": [], "tool_planning_result": "Tools disabled"}

    # Get tool registry and available tools
    registry = get_tool_registry()
    tools = registry.list_tools()

    if not tools:
        print("  No tools available - skipping")
        return {"tool_calls": [], "tool_planning_result": "No tools available"}

    # Format tool descriptions for prompt
    tool_descriptions = []
    for tool in tools:
        desc = f"- **{tool.name}**: {tool.description}"
        if tool.parameters:
            params = tool.parameters.get("properties", {})
            if params:
                param_list = ", ".join(params.keys())
                desc += f"\n  Parameters: {param_list}"
        tool_descriptions.append(desc)

    tool_desc_text = "\n".join(tool_descriptions)

    # Get current findings
    analyzed_data = state.get("analyzed_data", [])
    if not analyzed_data:
        print("  No analyzed data - skipping tool planning")
        return {"tool_calls": [], "tool_planning_result": "No data to analyze"}

    # Format analyzed data
    findings_text = "\n\n".join(analyzed_data[-3:])  # Last 3 analysis results

    # Build prompt
    prompt = TOOL_PLANNER_PROMPT.format(
        tool_descriptions=tool_desc_text,
        query=state.get("query", ""),
        analyzed_data=findings_text
    )

    # Get model and invoke
    model = get_evaluation_model()

    try:
        response = model.invoke(prompt)
        response_text = response.content

        # Parse JSON from response
        # Try to extract JSON from the response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            plan = json.loads(json_str)
        else:
            print("  Could not find JSON in response")
            return {"tool_calls": [], "tool_planning_result": "Failed to parse tool plan"}

        needs_tools = plan.get("needs_tools", False)
        tool_calls = plan.get("tool_calls", [])
        reasoning = plan.get("reasoning", "")

        print(f"  Needs tools: {needs_tools}")
        print(f"  Reasoning: {reasoning[:100]}...")

        if needs_tools and tool_calls:
            print(f"  Planned {len(tool_calls)} tool calls:")
            for tc in tool_calls:
                print(f"    - {tc.get('tool_name')}: {tc.get('purpose', 'N/A')}")

        return {
            "tool_calls": tool_calls if needs_tools else [],
            "tool_planning_result": reasoning
        }

    except json.JSONDecodeError as e:
        print(f"  Error parsing tool plan JSON: {e}")
        return {"tool_calls": [], "tool_planning_result": f"JSON parse error: {e}"}
    except Exception as e:
        print(f"  Error in tool planning: {e}")
        return {"tool_calls": [], "tool_planning_result": f"Error: {e}"}
