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

from typing import Literal, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.models import get_graph_selector_model

GraphType = Literal[
    "code_execution",
    "causal_inference",
    "comparative",
    "fact_check",
    "quick_research",
    "deep_research",
]


class GraphSelection(BaseModel):
    """Selection of the most appropriate graph workflow."""

    selected_graph: GraphType = Field(
        ..., description="The most appropriate graph workflow for the query"
    )
    reasoning: str = Field(..., description="Brief explanation for the selection")


def select_graph_with_llm(query: str) -> dict:
    """
    Select the optimal graph using an LLM.

    Args:
        query: User query

    Returns:
        Dictionary with 'selected_graph' and 'reasoning'
    """
    model = get_graph_selector_model()
    
    # Use structured output for reliable parsing
    structured_llm = model.with_structured_output(GraphSelection)
    
    system_prompt = """You are an intelligent router for a multi-agent research system. 
Your goal is to select the most appropriate workflow graph for a given user query.

Available Graphs:
1. code_execution: 
   - For queries requiring calculation, data analysis, visualization, or code generation.
   - Keywords: calculate, plot, graph, analyze data, python script, correlation, statistical, dataset.
   - Note: Do NOT use for general "what is" or "how to" questions unless they explicitly ask for code/math.

2. causal_inference:
   - For troubleshooting, root cause analysis, or "why" questions about failures.
   - Keywords: why, root cause, debug, fix, error, issue.

3. comparative:
   - For comparing 2 or more options, technologies, or concepts.
   - Keywords: vs, compare, difference between, trade-offs.

4. fact_check:
   - For verifying specific claims, true/false questions, or debunking.
   - Keywords: is it true, verify, fact check, confirm.
   - Note: Do NOT use for data analysis or correlation tasks (use code_execution).

5. quick_research:
   - For simple, straightforward questions that need a quick answer.
   - Criteria: Short query, single fact, specific lookup.

6. deep_research:
   - The DEFAULT for complex, open-ended, or multi-faceted research topics.
   - Use this if the query implementation involves broad exploration or doesn't fit others perfectly.

Analyze the user's intent and select the best graph.
"""
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{query}"),
        ]
    )
    
    chain = prompt | structured_llm
    
    try:
        result = chain.invoke({"query": query})
        return {
            "selected_graph": result.selected_graph,
            "reasoning": result.reasoning
        }
    except Exception as e:
        # Fallback if LLM fails
        print(f"Graph selection LLM failed: {e}")
        return {
            "selected_graph": "deep_research",  # Safe default
            "reasoning": "LLM selection failed, defaulting to deep_research"
        }


def auto_select_graph(query: str, default: GraphType = "deep_research") -> GraphType:
    """
    Automatically select the optimal graph based on query analysis.
    Uses LLM-based routing for intelligent decision making.

    Args:
        query: User query
        default: Default graph if selection fails

    Returns:
        Selected graph name
    """
    try:
        selection = select_graph_with_llm(query)
        return selection["selected_graph"]
    except Exception:
        return default


def explain_selection(query: str, selected_graph: str) -> str:
    """
    Explain why a particular graph was selected.
    Now uses the LLM to generate the explanation if possible, re-running logic if needed,
    or just returns a generic explanation if we don't want to re-run.
    
    For efficiency, main.py should ideally pass the reasoning if it has it, 
    but since the signature is fixed for now, we'll do a quick re-eval or logic check.
    
    Actually, to avoid double cost, we can just say "Selected by LLM based on intent analysis".
    But for better UX, let's call the LLM one more time or rely on a cache if we were caching.
    
    Since we don't have caching implemented yet, we will re-run the selection to get the reasoning
    or just provide a static message.
    """
    # Simply re-run to get the reasoning (it's a cheap call)
    try:
        selection = select_graph_with_llm(query)
        if selection["selected_graph"] == selected_graph:
            return f"Selected '{selected_graph}' because: {selection['reasoning']}"
    except:
        pass
        
    return f"Selected '{selected_graph}' based on intelligent intent analysis."


# Example usage and testing
if __name__ == "__main__":
    test_queries = [
        "Calculate the compound annual growth rate from 2018 to 2023",
        "Why is my Python script using 100% CPU?",
        "Compare React vs Vue frameworks",
        "Is it true that Python is slower than C++?",
        "What is quantum computing?",
        "Analyze the correlation between variables A and B in this dataset",
    ]

    print("Graph Selection Examples (LLM-based):\n")
    for query in test_queries:
        print(f"Query: {query}")
        selection = select_graph_with_llm(query)
        print(f"→ {selection['selected_graph']}")
        print(f"  Reason: {selection['reasoning']}\n")
