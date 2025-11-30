"""
Comparative Research Graph - Side-by-Side Analysis Workflow

This graph implements a specialized workflow for comparing multiple items:
- Identify items to compare from the query
- Research each item independently
- Analyze similarities and differences
- Provide structured comparison with pros/cons
- Generate decision support matrix

Use cases:
- Compare technologies, frameworks, or tools
- Evaluate multiple approaches to a problem
- Side-by-side feature comparison
- Trade-off analysis
- Decision support for choosing between options
"""

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

from src.nodes.analyzer_node import analyzer_node
from src.nodes.evaluator_node import evaluator_node

# Import reusable nodes
from src.nodes.planner_node import planner
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.searcher_node import searcher
from src.nodes.synthesizer_node import synthesizer_node

from .base_graph import BaseGraphBuilder


class ComparativeResearchState(TypedDict):
    """State for comparative research workflow"""

    # Core fields
    query: str  # The comparison query (e.g., "Compare React vs Vue vs Angular")
    report: str  # Final comparison report with decision matrix

    # Query allocation
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str

    # Results accumulation
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]

    # Comparison-specific fields
    items_to_compare: list[str]  # Extracted items (e.g., ["React", "Vue", "Angular"])
    comparison_criteria: list[str]  # Aspects to compare (e.g., ["performance", "learning curve"])
    item_data: dict  # item_name → research data

    # Evaluation and control
    evaluation: str
    reason: str
    loop_count: int


def comparative_router(state: ComparativeResearchState) -> Literal["synthesizer", "planner"]:
    """
    Router for comparative research: synthesize if sufficient or max loops reached

    Max 2 iterations to gather comprehensive comparison data.
    """
    loop_count = state.get("loop_count", 0)
    evaluation = state.get("evaluation", "")

    if "sufficient" in evaluation.lower() or loop_count >= 2:
        return "synthesizer"
    else:
        return "planner"


class ComparativeResearchGraphBuilder(BaseGraphBuilder):
    """Builder for the Comparative Research workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return ComparativeResearchState

    def build(self) -> StateGraph:
        """Build and compile the Comparative Research workflow"""
        workflow = StateGraph(ComparativeResearchState)

        # Register nodes (reusing existing nodes!)
        # Note: The planner will be responsible for:
        # 1. Extracting items to compare
        # 2. Identifying comparison criteria
        # 3. Generating targeted queries for each item
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up comparison flow
        # 1. Planner extracts items and creates comparison queries
        workflow.set_entry_point("planner")

        # 2. Parallel search for each item
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")

        # 3. Analyze and organize data by item
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # 4. Evaluate if we have enough data for each item
        workflow.add_edge("analyzer", "evaluator")

        # 5. Router: synthesize or gather more data
        workflow.add_conditional_edges(
            "evaluator",
            comparative_router,
            {
                "synthesizer": "synthesizer",
                "planner": "planner"
            }
        )

        # 6. Synthesizer creates comparison matrix and final report
        # The synthesizer will be configured (via prompts) to:
        # - Create side-by-side comparison table
        # - List pros/cons for each item
        # - Identify best use cases for each option
        # - Provide decision guidance
        workflow.add_edge("synthesizer", END)

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(ComparativeResearchState)

        # Register nodes
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")
        workflow.add_edge("analyzer", "evaluator")
        workflow.add_conditional_edges(
            "evaluator",
            comparative_router,
            {"synthesizer": "synthesizer", "planner": "planner"}
        )
        workflow.add_edge("synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Comparative Research",
            "description": "Side-by-side analysis and comparison workflow",
            "version": "1.0",
            "use_cases": [
                "Compare technologies, frameworks, or tools",
                "Evaluate multiple approaches to a problem",
                "Side-by-side feature comparison",
                "Trade-off analysis",
                "Decision support for choosing between options",
                "Product/service comparison",
                "A/B analysis"
            ],
            "complexity": "medium",
            "supports_streaming": True,
            "features": [
                "Automatic item extraction from query",
                "Comparison criteria identification",
                "Parallel research for each item",
                "Structured comparison matrix",
                "Pros/cons analysis",
                "Use case recommendations",
                "Decision guidance",
                "Up to 2 refinement iterations"
            ],
            "output_format": {
                "sections": [
                    "Executive summary",
                    "Items being compared",
                    "Comparison criteria",
                    "Side-by-side comparison table",
                    "Detailed analysis per item",
                    "Pros and cons",
                    "Best use cases for each option",
                    "Decision recommendations"
                ]
            },
            "performance": {
                "avg_execution_time": "45-90 seconds",
                "max_iterations": 2,
                "nodes": 6
            },
            "examples": [
                "Compare React vs Vue vs Angular for web development",
                "PostgreSQL vs MongoDB vs MySQL: which to choose?",
                "Python vs Go vs Rust for backend services",
                "AWS vs Azure vs GCP cloud platforms"
            ]
        }
