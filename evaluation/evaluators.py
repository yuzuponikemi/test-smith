"""
Custom Evaluators for Test-Smith Research Agent

This module provides a comprehensive set of evaluators for assessing
research agent performance across multiple dimensions:
- Accuracy and factual correctness
- Completeness and depth
- Source attribution and RAG usage
- Hallucination detection
- Performance metrics
- Graph-specific evaluation

Usage:
    from evaluation.evaluators import (
        evaluate_accuracy,
        evaluate_hallucination,
        evaluate_rag_usage
    )

    result = evaluate_accuracy(run, example)
"""

import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.models import get_evaluation_model

# ============================================================================
# HEURISTIC EVALUATORS (Rule-Based)
# ============================================================================

def evaluate_response_length(run: Any, example: Any) -> dict[str, Any]:
    """
    Evaluate if response length is appropriate for query complexity.

    Returns:
        score: 1.0 if appropriate, 0.5 if too short/long, 0.0 if empty
    """
    actual_output = run.outputs.get("report", "")
    complexity = example.inputs.get("metadata", {}).get("complexity", "medium")

    length = len(actual_output)

    if length == 0:
        return {
            "key": "response_length",
            "score": 0.0,
            "comment": "Empty response"
        }

    # Define expected length ranges
    length_ranges = {
        "simple": (50, 500),
        "medium": (200, 1500),
        "high": (500, 3000),
        "very_high": (1000, 5000)
    }

    min_length, max_length = length_ranges.get(complexity, (200, 2000))

    if min_length <= length <= max_length:
        score = 1.0
        comment = f"Appropriate length ({length} chars) for {complexity} query"
    elif length < min_length:
        score = 0.5
        comment = f"Too short ({length} chars) for {complexity} query (expected {min_length}+)"
    else:
        score = 0.5
        comment = f"Too long ({length} chars) for {complexity} query (expected <{max_length})"

    return {
        "key": "response_length",
        "score": score,
        "comment": comment
    }


def evaluate_execution_time(run: Any, example: Any) -> dict[str, Any]:
    """
    Evaluate if execution time meets expected performance thresholds.

    Returns:
        score: 1.0 if within threshold, proportional penalty if over
    """
    # Get execution time from run metadata
    if hasattr(run, 'execution_time'):
        execution_time = run.execution_time
    else:
        # Calculate from start/end times if available
        if hasattr(run, 'start_time') and hasattr(run, 'end_time'):
            execution_time = (run.end_time - run.start_time).total_seconds()
        else:
            return {
                "key": "execution_time",
                "score": None,
                "comment": "Execution time not available"
            }

    # Get expected time from example metadata
    expected_graph = example.inputs.get("metadata", {}).get("expected_graph", "quick_research")
    max_expected_time = example.inputs.get("metadata", {}).get("max_expected_time")

    # Default thresholds by graph type
    if not max_expected_time:
        thresholds = {
            "quick_research": 60,
            "fact_check": 45,
            "comparative": 90,
            "deep_research": 180
        }
        max_expected_time = thresholds.get(expected_graph, 120)

    if execution_time <= max_expected_time:
        score = 1.0
        comment = f"Completed in {execution_time:.1f}s (within {max_expected_time}s threshold)"
    else:
        # Penalty proportional to overage
        overage_ratio = execution_time / max_expected_time
        score = max(0.0, 1.0 - (overage_ratio - 1.0) * 0.5)
        comment = f"Slow: {execution_time:.1f}s (expected <{max_expected_time}s)"

    return {
        "key": "execution_time",
        "score": score,
        "comment": comment,
        "value": execution_time
    }


def evaluate_rag_usage(run: Any, example: Any) -> dict[str, Any]:
    """
    Evaluate if RAG/knowledge base was used appropriately.

    Checks if internal documentation queries used RAG and external
    queries used web search as expected.

    Returns:
        score: 1.0 if correct source, 0.0 if wrong source
    """
    # Check if this example requires RAG
    metadata = example.inputs.get("metadata", {})
    should_use_rag = metadata.get("should_use_rag", None)
    requires_kb = metadata.get("requires_kb", False)
    requires_web = metadata.get("requires_web", False)

    # Get actual sources used from run outputs
    outputs = run.outputs
    rag_queries = outputs.get("rag_queries", [])
    web_queries = outputs.get("web_queries", [])
    rag_results = outputs.get("rag_results", [])

    used_rag = len(rag_queries) > 0 or len(rag_results) > 0
    used_web = len(web_queries) > 0

    # Evaluate based on requirements
    if requires_kb and not used_rag:
        return {
            "key": "rag_usage",
            "score": 0.0,
            "comment": "Failed to use knowledge base for internal documentation query"
        }

    if requires_web and not used_web:
        return {
            "key": "rag_usage",
            "score": 0.0,
            "comment": "Failed to use web search for current events/external query"
        }

    if should_use_rag is True and not used_rag:
        return {
            "key": "rag_usage",
            "score": 0.0,
            "comment": "Should have used RAG but didn't"
        }

    if should_use_rag is False and used_rag and not used_web:
        return {
            "key": "rag_usage",
            "score": 0.5,
            "comment": "Used only RAG when web search would be more appropriate"
        }

    # If no specific requirement, check for reasonable allocation
    if used_rag and used_web:
        comment = "Good: Used both RAG and web search (strategic allocation)"
        score = 1.0
    elif used_rag:
        comment = "Used RAG only"
        score = 0.8
    elif used_web:
        comment = "Used web search only"
        score = 0.8
    else:
        comment = "Warning: No sources used"
        score = 0.0

    return {
        "key": "rag_usage",
        "score": score,
        "comment": comment
    }


def evaluate_no_errors(run: Any, example: Any) -> dict[str, Any]:
    """
    Check if execution completed without errors.

    Returns:
        score: 1.0 if no errors, 0.0 if errors occurred
    """
    # Check for error in run
    if hasattr(run, 'error') and run.error:
        return {
            "key": "no_errors",
            "score": 0.0,
            "comment": f"Execution error: {str(run.error)}"
        }

    # Check for empty output (possible silent failure)
    actual_output = run.outputs.get("report", "")
    if not actual_output or len(actual_output.strip()) == 0:
        return {
            "key": "no_errors",
            "score": 0.0,
            "comment": "Empty output (possible silent failure)"
        }

    return {
        "key": "no_errors",
        "score": 1.0,
        "comment": "Completed without errors"
    }


# ============================================================================
# LLM-AS-JUDGE EVALUATORS
# ============================================================================

def create_llm_evaluator(
    criteria: str,
    metric_name: str,
    scoring_guide: str = None
) -> callable:
    """
    Factory function to create LLM-as-judge evaluators.

    Args:
        criteria: What to evaluate (e.g., "factual accuracy")
        metric_name: Name for the metric
        scoring_guide: Optional detailed scoring rubric

    Returns:
        Evaluator function
    """
    llm = get_evaluation_model()

    default_scoring = """
    Rate from 0.0 to 1.0 where:
    0.0 = Completely fails criteria
    0.25 = Poor, major issues
    0.5 = Acceptable, some issues
    0.75 = Good, minor issues
    1.0 = Excellent, fully meets criteria
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert evaluator for a research AI agent.
Your task is to evaluate the agent's output based on specific criteria.

Be objective and consistent. Provide a numerical score and brief reasoning."""),
        ("human", """Evaluate the following:

QUERY: {query}

AGENT OUTPUT:
{output}

REFERENCE/EXPECTED OUTPUT:
{reference}

EVALUATION CRITERIA: {criteria}

SCORING GUIDE:
{scoring_guide}

Provide your evaluation in this exact format:
Score: <number between 0.0 and 1.0>
Reasoning: <brief explanation>""")
    ])

    chain = prompt | llm

    def evaluator(run: Any, example: Any) -> dict[str, Any]:
        """LLM-as-judge evaluator"""
        actual_output = run.outputs.get("report", "")
        reference_output = example.outputs.get("reference_output", "")
        query = example.inputs.get("input", "")

        try:
            result = chain.invoke({
                "query": query,
                "output": actual_output,
                "reference": reference_output,
                "criteria": criteria,
                "scoring_guide": scoring_guide or default_scoring
            })

            # Parse score from LLM response
            response_text = result.content
            score_match = re.search(r"Score:\s*([\d.]+)", response_text)
            reasoning_match = re.search(r"Reasoning:\s*(.+)", response_text, re.DOTALL)

            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            else:
                score = None

            reasoning = reasoning_match.group(1).strip() if reasoning_match else response_text

            return {
                "key": metric_name,
                "score": score,
                "comment": reasoning[:500]  # Limit comment length
            }

        except Exception as e:
            return {
                "key": metric_name,
                "score": None,
                "comment": f"Evaluation error: {str(e)}"
            }

    return evaluator


# Pre-configured LLM evaluators
evaluate_accuracy = create_llm_evaluator(
    criteria="Factual accuracy and correctness of information",
    metric_name="accuracy",
    scoring_guide="""
    1.0 = All facts correct, no errors
    0.75 = Mostly correct, 1-2 minor errors
    0.5 = Several errors or missing important facts
    0.25 = Major factual errors
    0.0 = Completely incorrect or fabricated
    """
)

evaluate_completeness = create_llm_evaluator(
    criteria="Completeness - does it cover all important aspects of the query?",
    metric_name="completeness",
    scoring_guide="""
    1.0 = Comprehensive, covers all expected aspects
    0.75 = Covers most aspects, minor gaps
    0.5 = Covers some aspects, significant gaps
    0.25 = Superficial, misses most aspects
    0.0 = Does not address the query
    """
)

evaluate_hallucination = create_llm_evaluator(
    criteria="Hallucination detection - does the output contain fabricated or unverifiable claims?",
    metric_name="hallucination",
    scoring_guide="""
    1.0 = No hallucinations, all claims grounded in sources or common knowledge
    0.75 = Minor speculation clearly marked as such
    0.5 = Some unverified claims presented as facts
    0.25 = Significant fabrication or invention of details
    0.0 = Entirely fabricated response

    Note: Score 1.0 means NO hallucination (higher is better)
    """
)

evaluate_relevance = create_llm_evaluator(
    criteria="Relevance - how well does the output address the specific query?",
    metric_name="relevance",
    scoring_guide="""
    1.0 = Directly and fully addresses the query
    0.75 = Mostly relevant, minor tangents
    0.5 = Partially relevant, some off-topic content
    0.25 = Largely irrelevant
    0.0 = Completely off-topic
    """
)

evaluate_structure = create_llm_evaluator(
    criteria="Organization and structure - is the output well-organized and easy to follow?",
    metric_name="structure",
    scoring_guide="""
    1.0 = Excellent organization, clear sections, logical flow
    0.75 = Good structure, minor organization issues
    0.5 = Acceptable but could be better organized
    0.25 = Poor organization, hard to follow
    0.0 = Chaotic, no clear structure
    """
)


# ============================================================================
# SPECIALIZED EVALUATORS
# ============================================================================

def evaluate_graph_selection(run: Any, example: Any) -> dict[str, Any]:
    """
    Evaluate if the correct graph type was selected for the query.

    Returns:
        score: 1.0 if correct graph, 0.5 if suboptimal, 0.0 if wrong
    """
    expected_graph = example.inputs.get("metadata", {}).get("expected_graph")

    if not expected_graph or expected_graph == "any":
        return {
            "key": "graph_selection",
            "score": None,
            "comment": "No specific graph requirement"
        }

    # Get actual graph used from run metadata
    actual_graph = run.outputs.get("graph_type") or getattr(run, 'graph_type', None)

    if not actual_graph:
        return {
            "key": "graph_selection",
            "score": None,
            "comment": "Graph type not recorded in run"
        }

    if actual_graph == expected_graph:
        score = 1.0
        comment = f"Correct: Used {actual_graph} as expected"
    else:
        # Check if it's a reasonable alternative
        alternatives = {
            "quick_research": ["fact_check", "comparative"],
            "deep_research": ["quick_research"],  # overkill but works
            "fact_check": ["quick_research"],
            "comparative": ["quick_research", "deep_research"]
        }

        if actual_graph in alternatives.get(expected_graph, []):
            score = 0.5
            comment = f"Suboptimal: Used {actual_graph}, expected {expected_graph}"
        else:
            score = 0.0
            comment = f"Wrong: Used {actual_graph}, expected {expected_graph}"

    return {
        "key": "graph_selection",
        "score": score,
        "comment": comment
    }


def evaluate_citation_quality(run: Any, example: Any) -> dict[str, Any]:
    """
    Evaluate quality of source citations and attribution.

    Looks for indicators like "according to", "research shows", URLs, etc.

    Returns:
        score: Based on citation presence and quality
    """
    actual_output = run.outputs.get("report", "")

    # Citation indicators
    citation_patterns = [
        r"according to",
        r"research shows",
        r"studies indicate",
        r"https?://",
        r"\[.*?\]",  # Markdown links
        r"source:",
        r"references",
    ]

    citation_count = sum(
        len(re.findall(pattern, actual_output, re.IGNORECASE))
        for pattern in citation_patterns
    )

    complexity = example.inputs.get("metadata", {}).get("complexity", "medium")

    # Expected citations by complexity
    expected_citations = {
        "simple": 0,
        "medium": 1,
        "high": 3,
        "very_high": 5
    }

    expected = expected_citations.get(complexity, 1)

    if citation_count >= expected:
        score = 1.0
        comment = f"Good citation quality ({citation_count} indicators found)"
    elif citation_count >= expected // 2:
        score = 0.5
        comment = f"Some citations ({citation_count} indicators), could improve"
    else:
        score = 0.0
        comment = f"Poor citation quality ({citation_count} indicators, expected {expected}+)"

    return {
        "key": "citation_quality",
        "score": score,
        "comment": comment,
        "value": citation_count
    }


# ============================================================================
# EVALUATOR REGISTRY
# ============================================================================

# All available evaluators grouped by type
HEURISTIC_EVALUATORS = {
    "response_length": evaluate_response_length,
    "execution_time": evaluate_execution_time,
    "rag_usage": evaluate_rag_usage,
    "no_errors": evaluate_no_errors,
    "graph_selection": evaluate_graph_selection,
    "citation_quality": evaluate_citation_quality,
}

LLM_EVALUATORS = {
    "accuracy": evaluate_accuracy,
    "completeness": evaluate_completeness,
    "hallucination": evaluate_hallucination,
    "relevance": evaluate_relevance,
    "structure": evaluate_structure,
}

ALL_EVALUATORS = {**HEURISTIC_EVALUATORS, **LLM_EVALUATORS}


def get_evaluators_for_example(example: Any) -> list:
    """
    Get recommended evaluators for a specific example based on its metadata.

    Args:
        example: Test example with metadata

    Returns:
        List of evaluator functions to use
    """
    category = example.inputs.get("category", "")
    complexity = example.inputs.get("metadata", {}).get("complexity", "")

    # Always run these
    evaluators = [
        evaluate_no_errors,
        evaluate_response_length,
        evaluate_accuracy,
        evaluate_relevance,
    ]

    # Add based on category
    if "internal_documentation" in category:
        evaluators.append(evaluate_rag_usage)

    if complexity in ["high", "very_high"]:
        evaluators.extend([
            evaluate_completeness,
            evaluate_structure,
            evaluate_citation_quality,
        ])

    if "hallucination" in category:
        evaluators.append(evaluate_hallucination)

    if example.inputs.get("metadata", {}).get("expected_graph"):
        evaluators.append(evaluate_graph_selection)

    if category in ["speed_test", "simple"]:
        evaluators.append(evaluate_execution_time)

    return evaluators
