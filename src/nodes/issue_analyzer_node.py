"""
Issue Analyzer Node - Extracts symptoms and context from problem statement.

Part of the Causal Inference Graph workflow for root cause analysis.
"""

from src.models import get_issue_analyzer_model
from src.utils.logging_utils import print_node_header
from src.prompts.issue_analyzer_prompt import ISSUE_ANALYZER_PROMPT
from src.schemas import IssueAnalysis


def issue_analyzer_node(state: dict) -> dict:
    """
    Analyzes the problem statement and extracts key information for causal analysis.

    Args:
        state: Current graph state with 'query' field

    Returns:
        Updated state with issue analysis fields
    """
    print_node_header("ISSUE ANALYZER")

    query = state.get("query", "")
    print(f"  Analyzing issue: {query[:100]}...")

    # Get model with structured output
    model = get_issue_analyzer_model()
    structured_model = model.with_structured_output(IssueAnalysis)

    # Format prompt and invoke
    prompt = ISSUE_ANALYZER_PROMPT.format(query=query)
    analysis: IssueAnalysis = structured_model.invoke(prompt)

    print(f"  Extracted {len(analysis.symptoms)} symptoms")
    print(f"  Issue summary: {analysis.issue_summary[:80]}...")

    return {
        "issue_summary": analysis.issue_summary,
        "symptoms": analysis.symptoms,
        "context": analysis.context,
        "scope": analysis.scope,
    }
