"""
Graph Selector - Automatic graph selection based on query analysis

MCP-aligned design philosophy:
- Analyzes query to determine optimal graph
- Only loads selected graph (0 tokens overhead for unused graphs)
- Implements intelligent routing without bloating context

This module enables:
- Automatic code_execution graph selection for computational queries
- Causal_inference for troubleshooting queries
- Comparative for comparison queries
- Default to deep_research for complex queries
"""

import re
from typing import Literal

GraphType = Literal[
    "code_execution",
    "causal_inference",
    "comparative",
    "fact_check",
    "quick_research",
    "deep_research"
]


def detect_code_execution_need(query: str) -> bool:
    """
    Detect if query requires code execution.

    Indicators:
    - Mathematical calculations
    - Data analysis keywords
    - Statistical operations
    - Visualization requests
    - Computational verbs
    """
    query_lower = query.lower()

    # Calculation indicators
    calculation_keywords = [
        "calculate", "compute", "sum", "average", "mean", "median",
        "percentage", "ratio", "rate", "growth", "trend",
        "statistical", "correlation", "regression",
        "analyze data", "process data", "parse",
        "how many", "how much", "total", "count"
    ]

    # Visualization indicators
    viz_keywords = [
        "chart", "graph", "plot", "visualize", "diagram",
        "show trend", "distribution", "histogram"
    ]

    # Check for mathematical expressions
    has_math_expression = bool(re.search(r'\d+\s*[\+\-\*\/\%]\s*\d+', query))

    # Check keywords
    has_calculation = any(kw in query_lower for kw in calculation_keywords)
    has_viz = any(kw in query_lower for kw in viz_keywords)

    return has_math_expression or has_calculation or has_viz


def detect_causal_inference_need(query: str) -> bool:
    """
    Detect if query requires causal inference analysis.

    Indicators:
    - Root cause questions
    - Troubleshooting
    - "Why" questions
    - Failure analysis
    """
    query_lower = query.lower()

    causal_keywords = [
        "why", "причина", "理由",  # multilingual "why"
        "root cause", "cause of", "reason for",
        "troubleshoot", "debug", "diagnose",
        "failure", "error", "bug", "issue",
        "not working", "broken", "problem with"
    ]

    return any(kw in query_lower for kw in causal_keywords)


def detect_comparative_need(query: str) -> bool:
    """
    Detect if query requires comparative analysis.

    Indicators:
    - Comparison keywords
    - "vs" or "versus"
    - Multiple options
    - Trade-off analysis
    """
    query_lower = query.lower()

    comparative_keywords = [
        " vs ", " versus ", "compare", "comparison",
        "difference between", "similarities between",
        "better than", "worse than",
        "which", "choose between", "decide between",
        "pros and cons", "trade-off", "tradeoff"
    ]

    # Check for "A vs B" pattern
    has_vs_pattern = bool(re.search(r'\w+\s+(vs|versus)\s+\w+', query_lower))

    has_comparative = any(kw in query_lower for kw in comparative_keywords)

    return has_vs_pattern or has_comparative


def detect_fact_check_need(query: str) -> bool:
    """
    Detect if query requires fact checking.

    Indicators:
    - Verification requests
    - True/false questions
    - Accuracy checking
    """
    query_lower = query.lower()

    fact_check_keywords = [
        "is it true", "is this true", "fact check",
        "verify", "accurate", "correct",
        "true or false", "真偽", "本当",
        "confirm", "validate"
    ]

    return any(kw in query_lower for kw in fact_check_keywords)


def detect_simple_query(query: str) -> bool:
    """
    Detect if query is simple enough for quick_research.

    Indicators:
    - Short queries (< 50 chars)
    - Single question word
    - No complex analysis required
    """
    # Very short queries are likely simple
    if len(query) < 50:
        return True

    # Single sentence questions
    sentences = query.split('.')
    if len(sentences) <= 1 and len(query) < 100:
        return True

    return False


def auto_select_graph(query: str, default: str = "deep_research") -> GraphType:
    """
    Automatically select the optimal graph based on query analysis.

    MCP benefit: Only the selected graph is loaded into context,
    avoiding the token overhead of loading all graphs.

    Priority order:
    1. Code execution (highest priority for computational tasks)
    2. Causal inference (for troubleshooting)
    3. Comparative (for comparisons)
    4. Fact check (for verification)
    5. Quick research (for simple queries)
    6. Deep research (default for complex queries)

    Args:
        query: User query
        default: Default graph if no pattern matches

    Returns:
        Selected graph name
    """
    # Priority 1: Code execution (computational queries)
    if detect_code_execution_need(query):
        return "code_execution"

    # Priority 2: Causal inference (troubleshooting)
    if detect_causal_inference_need(query):
        return "causal_inference"

    # Priority 3: Comparative analysis
    if detect_comparative_need(query):
        return "comparative"

    # Priority 4: Fact checking
    if detect_fact_check_need(query):
        return "fact_check"

    # Priority 5: Quick research for simple queries
    if detect_simple_query(query):
        return "quick_research"

    # Default: Deep research for complex queries
    return default


def explain_selection(query: str, selected_graph: str) -> str:
    """
    Explain why a particular graph was selected.

    Useful for debugging and user transparency.
    """
    reasons = []

    if detect_code_execution_need(query):
        reasons.append("Contains computational/analytical keywords")
    if detect_causal_inference_need(query):
        reasons.append("Requires causal reasoning or troubleshooting")
    if detect_comparative_need(query):
        reasons.append("Involves comparison or trade-off analysis")
    if detect_fact_check_need(query):
        reasons.append("Requires fact verification")
    if detect_simple_query(query):
        reasons.append("Query is simple and concise")

    if not reasons:
        reasons.append("Complex multi-faceted query")

    explanation = f"Selected '{selected_graph}' graph because:\n"
    for reason in reasons:
        explanation += f"  - {reason}\n"

    return explanation


# Example usage and testing
if __name__ == "__main__":
    test_queries = [
        "Calculate the compound annual growth rate from 2018 to 2023",
        "Why is my Python script using 100% CPU?",
        "Compare React vs Vue frameworks",
        "Is it true that Python is slower than C++?",
        "What is quantum computing?",
        "Analyze the correlation between variables A and B in this dataset"
    ]

    print("Graph Selection Examples:\n")
    for query in test_queries:
        selected = auto_select_graph(query)
        print(f"Query: {query}")
        print(f"→ {selected}\n")
