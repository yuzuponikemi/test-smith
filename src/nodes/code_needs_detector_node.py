"""
Code needs detector node for determining when code execution is beneficial.

This node analyzes the query and collected data to determine if
programmatic computation would improve the research output.
"""

from src.models import get_code_needs_detector_model
from src.utils.logging_utils import print_node_header
from src.prompts.code_executor_prompt import CODE_NEEDS_DETECTOR_PROMPT
from src.schemas import CodeNeedsAnalysis


def code_needs_detector_node(state: dict) -> dict:
    """
    Determine if code execution would benefit the research.

    Analyzes the query and collected data to decide if computational
    analysis (calculations, data processing, visualizations) would
    provide value.

    Args:
        state: Current graph state containing:
            - query: Original user query
            - analyzed_data: Collected and analyzed research data

    Returns:
        State update with:
            - needs_code_execution: Whether to run code executor
            - code_task_description: What computation to perform
            - code_data_context: Data to use for computation
    """
    print_node_header("CODE NEEDS DETECTOR")

    # Extract state
    query = state.get("query", "")
    analyzed_data = state.get("analyzed_data", [])

    # Format analyzed data for the prompt
    if isinstance(analyzed_data, list):
        data_text = "\n\n".join(analyzed_data)
    else:
        data_text = str(analyzed_data)

    print(f"  Analyzing query: {query[:60]}...")
    print(f"  Data available: {len(data_text)} characters")

    # Get model with structured output
    model = get_code_needs_detector_model()

    try:
        structured_model = model.with_structured_output(CodeNeedsAnalysis)

        prompt = CODE_NEEDS_DETECTOR_PROMPT.format(
            query=query,
            analyzed_data=data_text[:10000]  # Limit context size
        )

        analysis: CodeNeedsAnalysis = structured_model.invoke(prompt)

        needs_execution = analysis.needs_code_execution
        task_type = analysis.task_type

        if needs_execution:
            print(f"  Decision: Code execution NEEDED")
            print(f"  Task type: {task_type}")
            print(f"  Task: {analysis.task_description[:60]}...")

            # Prepare data context for code execution
            # Extract relevant data points mentioned in the analysis
            data_context = _prepare_data_context(
                data_text,
                analysis.data_to_extract
            )

            return {
                "needs_code_execution": True,
                "code_task_description": analysis.task_description,
                "code_data_context": data_context,
                "code_expected_output": analysis.expected_output,
                "code_task_type": task_type
            }
        else:
            print(f"  Decision: Code execution NOT needed")
            print(f"  Reason: {analysis.reasoning[:80]}...")

            return {
                "needs_code_execution": False,
                "code_task_description": "",
                "code_data_context": "",
                "code_expected_output": "",
                "code_task_type": "none"
            }

    except Exception as e:
        print(f"  Warning: Structured detection failed, using fallback: {e}")

        # Fallback: simple heuristic detection
        needs_code = _heuristic_code_detection(query, data_text)

        if needs_code:
            print("  Decision: Code execution NEEDED (heuristic)")
            return {
                "needs_code_execution": True,
                "code_task_description": f"Analyze data related to: {query}",
                "code_data_context": data_text[:5000],
                "code_expected_output": "Quantitative analysis",
                "code_task_type": "data_analysis"
            }
        else:
            print("  Decision: Code execution NOT needed (heuristic)")
            return {
                "needs_code_execution": False,
                "code_task_description": "",
                "code_data_context": "",
                "code_expected_output": "",
                "code_task_type": "none"
            }


def _prepare_data_context(data_text: str, data_to_extract: list) -> str:
    """
    Prepare data context for code execution.

    Extracts relevant portions of the analyzed data based on
    the identified data points to extract.

    Args:
        data_text: Full analyzed data text
        data_to_extract: Specific data points to extract

    Returns:
        Formatted data context for code generation
    """
    if not data_to_extract:
        # If no specific extraction, return a summarized version
        return data_text[:5000]

    context_parts = [
        "## Data Context for Analysis",
        "",
        "### Raw Data:",
        data_text[:3000],
        "",
        "### Specific Data Points to Extract:",
    ]

    for point in data_to_extract:
        context_parts.append(f"- {point}")

    return "\n".join(context_parts)


def _heuristic_code_detection(query: str, data_text: str) -> bool:
    """
    Simple heuristic to detect if code execution might be useful.

    Args:
        query: User query
        data_text: Analyzed data

    Returns:
        Whether code execution is likely beneficial
    """
    # Keywords that suggest quantitative analysis
    quantitative_keywords = [
        "calculate", "compute", "percentage", "growth", "rate",
        "compare", "benchmark", "performance", "statistics",
        "average", "median", "correlation", "trend", "chart",
        "graph", "plot", "visualize", "analyze data", "csv",
        "json", "numbers", "metrics", "ratio", "distribution"
    ]

    query_lower = query.lower()

    # Check if query contains quantitative keywords
    for keyword in quantitative_keywords:
        if keyword in query_lower:
            return True

    # Check if data contains numerical patterns
    import re
    numbers = re.findall(r'\d+\.?\d*', data_text[:2000])
    if len(numbers) > 10:  # Many numbers suggest data analysis potential
        return True

    return False
