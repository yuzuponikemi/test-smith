"""
Code Flow Tracker Node - Analyzes data flow and control flow in code

This node analyzes retrieved code to trace:
- Data flow (how data moves through the code)
- Control flow (execution paths)
- Variable usage (definitions, modifications, reads)
- Function call hierarchy
"""

import json
import re

from langchain_core.prompts import PromptTemplate

from src.models import get_analyzer_model
from src.prompts.code_investigation_prompts import CODE_FLOW_TRACKER_PROMPT
from src.utils.logging_utils import print_node_header


def code_flow_tracker_node(state):
    """
    Code Flow Tracker Node - Traces data and control flow through code

    Takes retrieved code and analyzes how data and execution flows.
    """
    print_node_header("CODE FLOW TRACKER")

    query = state.get("query", "")
    target_elements = state.get("target_elements", [])
    code_results = state.get("code_results", [])

    if not code_results:
        print("  No code results to analyze")
        return {
            "data_flow": [],
            "control_flow": [],
            "variable_usage": [],
            "function_calls": [],
            "related_files": [],
        }

    # Combine code results
    code_context = "\n\n".join(code_results)

    print(f"  Analyzing flow in {len(code_context)} chars of code")
    print(f"  Target elements: {target_elements}")

    # Create prompt
    prompt = PromptTemplate(
        template=CODE_FLOW_TRACKER_PROMPT,
        input_variables=["query", "target_elements", "code_context"],
    )

    # Get model
    model = get_analyzer_model()
    chain = prompt | model

    try:
        response = chain.invoke(
            {
                "query": query,
                "target_elements": ", ".join(target_elements)
                if target_elements
                else "Not specified",
                "code_context": code_context[:15000],  # Limit context size
            }
        )

        # Extract content
        result = response.content if hasattr(response, "content") else str(response)

        # Parse JSON from response
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback: do basic analysis
            analysis = _analyze_flow_basic(code_context, target_elements)

        data_flow = analysis.get("data_flow", [])
        control_flow = analysis.get("control_flow", [])
        variable_usage = analysis.get("variable_usage", [])
        function_calls = analysis.get("function_calls", [])
        key_findings = analysis.get("key_findings", [])

        # Extract related files from code results
        related_files = _extract_file_paths(code_context)

        print(f"  Data flow paths: {len(data_flow)}")
        print(f"  Control flow entries: {len(control_flow)}")
        print(f"  Variable usages: {len(variable_usage)}")
        print(f"  Function calls: {len(function_calls)}")
        print(f"  Related files: {len(related_files)}")

        # Merge key findings with existing
        existing_findings = state.get("key_findings", [])
        all_findings = existing_findings + key_findings

        return {
            "data_flow": data_flow,
            "control_flow": control_flow,
            "variable_usage": variable_usage,
            "function_calls": function_calls,
            "related_files": related_files,
            "key_findings": all_findings,
        }

    except Exception as e:
        print(f"  Error analyzing flow: {e}")
        # Return basic analysis
        basic = _analyze_flow_basic(code_context, target_elements)
        return {
            "data_flow": basic.get("data_flow", []),
            "control_flow": basic.get("control_flow", []),
            "variable_usage": basic.get("variable_usage", []),
            "function_calls": basic.get("function_calls", []),
            "related_files": _extract_file_paths(code_context),
            "key_findings": [f"Basic analysis only due to error: {str(e)}"],
        }


def _analyze_flow_basic(code_context: str, _target_elements: list) -> dict:
    """Basic flow analysis using regex patterns"""

    data_flow = []
    control_flow = []
    variable_usage = []
    function_calls = []

    # Find function definitions (Python)
    py_functions = re.findall(r"def\s+(\w+)\s*\(([^)]*)\)", code_context)
    for func_name, params in py_functions:
        if params.strip():
            for param in params.split(","):
                param = param.split(":")[0].split("=")[0].strip()
                if param:
                    data_flow.append(
                        {
                            "variable": param,
                            "source": "parameter",
                            "transformations": [],
                            "destination": f"used in {func_name}",
                        }
                    )
        control_flow.append({"entry_point": func_name, "branches": [], "exit_points": ["return"]})

    # Find C# method definitions
    cs_methods = re.findall(
        r"(?:public|private|protected|internal|static|\s)+[\w\<\>\[\],]+\s+(\w+)\s*\(([^)]*)\)",
        code_context,
    )
    for method_name, params in cs_methods:
        if params.strip():
            for param in params.split(","):
                parts = param.strip().split()
                if len(parts) >= 2:
                    param_name = parts[-1]
                    data_flow.append(
                        {
                            "variable": param_name,
                            "source": "parameter",
                            "transformations": [],
                            "destination": f"used in {method_name}",
                        }
                    )
        control_flow.append({"entry_point": method_name, "branches": [], "exit_points": ["return"]})

    # Find function calls (Python)
    py_calls = re.findall(r"(\w+)\s*\([^)]*\)", code_context)
    seen_calls = set()
    for call in py_calls:
        if call not in seen_calls and call not in ("def", "class", "if", "for", "while", "with"):
            seen_calls.add(call)
            function_calls.append({"caller": "unknown", "callee": call, "purpose": "function call"})

    # Find variable assignments
    py_assignments = re.findall(r"^(\s*)(\w+)\s*=\s*(.+)$", code_context, re.MULTILINE)
    for _indent, var_name, _value in py_assignments[:20]:  # Limit to 20
        variable_usage.append(
            {"name": var_name, "defined_in": "unknown", "modified_in": [], "read_in": []}
        )

    return {
        "data_flow": data_flow[:15],
        "control_flow": control_flow[:10],
        "variable_usage": variable_usage[:15],
        "function_calls": list({c["callee"]: c for c in function_calls}.values())[:15],
        "key_findings": [
            f"Found {len(control_flow)} function/method definitions",
            f"Found {len(function_calls)} function calls",
        ],
    }


def _extract_file_paths(code_context: str) -> list:
    """Extract file paths mentioned in code results"""

    # Look for file path patterns in the code context
    file_patterns = [
        r"File:\s*([^\n]+)",
        r"path/to/([^\s]+)",
        r"src/([^\s:]+)",
        r"([a-zA-Z_][a-zA-Z0-9_/]*\.(?:py|cs|js|ts|java|go|rs))",
    ]

    files = set()
    for pattern in file_patterns:
        matches = re.findall(pattern, code_context)
        for match in matches:
            if match and not match.startswith("http"):
                files.add(match)

    return list(files)[:20]  # Limit to 20 files
