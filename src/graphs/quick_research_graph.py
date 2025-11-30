"""
Quick Research Graph - Fast Single-Pass Research Workflow

This graph implements a streamlined research workflow for simple queries:
- Single-pass execution (no hierarchical decomposition)
- Strategic query allocation (RAG vs Web)
- Fast results with minimal overhead
- Maximum 2 refinement iterations

Use cases:
- Simple, straightforward questions
- Quick fact lookups
- Queries that don't require deep exploration
- Time-sensitive research needs
"""

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from src.nodes.analyzer_node import analyzer_node
from src.nodes.evaluator_node import evaluator_node

# Import reusable nodes
from src.nodes.planner_node import planner
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.reflection_node import reflection_node
from src.nodes.searcher_node import searcher
from src.nodes.synthesizer_node import synthesizer_node

from .base_graph import BaseGraphBuilder


class QuickResearchState(TypedDict):
    """Minimal state for quick research workflow"""

    # Core fields
    query: str
    report: str

    # Query allocation
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str

    # Results accumulation
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]

    # Evaluation and control
    evaluation: str
    reason: str
    loop_count: int

    # Reflection & Self-Critique
    reflection_critique: dict  # ReflectionCritique as dict (JSON-serializable)
    reflection_quality: str  # Overall quality assessment
    should_continue_research: bool  # Whether reflection identified critical gaps
    reflection_confidence: float  # Confidence score from reflection (0.0-1.0)


def quick_router(state: QuickResearchState) -> Literal["synthesizer", "planner"]:
    """
    Router with reflection-aware decision making.

    Checks both evaluation and reflection critique to determine next step.
    Max 2 iterations to keep response time fast.
    """
    loop_count = state.get("loop_count", 0)
    evaluation = state.get("evaluation", "")
    should_continue_research = state.get("should_continue_research", False)
    reflection_quality = state.get("reflection_quality", "adequate")

    # Force exit after max loops
    if loop_count >= 2:
        print(f"  Quick mode: Max loops reached (quality: {reflection_quality}) → synthesize")
        return "synthesizer"

    # Check reflection feedback first (higher priority for quality)
    if should_continue_research:
        print(
            f"  Quick mode: Reflection identified critical gaps (quality: {reflection_quality}) → refine"
        )
        return "planner"

    # Check evaluation
    if "sufficient" in evaluation.lower():
        print(f"  Quick mode: Evaluation sufficient (quality: {reflection_quality}) → synthesize")
        return "synthesizer"
    else:
        print("  Quick mode: Evaluation insufficient → refine")
        return "planner"


class QuickResearchGraphBuilder(BaseGraphBuilder):
    """Builder for the Quick Research single-pass workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return QuickResearchState

    def build(self) -> Any:
        """Build and compile the Quick Research workflow"""
        workflow = StateGraph(QuickResearchState)

        # Register nodes (reusing existing nodes!)
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("reflection", reflection_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up linear flow with evaluation loop
        workflow.set_entry_point("planner")

        # Planner → Parallel execution
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")

        # Parallel execution → Analyzer
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # Analyzer → Evaluator
        workflow.add_edge("analyzer", "evaluator")

        # Evaluator → Reflection (meta-reasoning critique)
        workflow.add_edge("evaluator", "reflection")

        # Reflection → Router (synthesize or refine based on reflection + evaluation)
        workflow.add_conditional_edges(
            "reflection", quick_router, {"synthesizer": "synthesizer", "planner": "planner"}
        )

        # Synthesizer → END
        workflow.add_edge("synthesizer", END)

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(QuickResearchState)

        # Register nodes
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("reflection", reflection_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")
        workflow.add_edge("analyzer", "evaluator")
        workflow.add_edge("evaluator", "reflection")
        workflow.add_conditional_edges(
            "reflection", quick_router, {"synthesizer": "synthesizer", "planner": "planner"}
        )
        workflow.add_edge("synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Quick Research",
            "description": "Fast single-pass research for simple queries",
            "version": "1.0",
            "use_cases": [
                "Simple, straightforward questions",
                "Quick fact lookups",
                "Queries that don't require deep exploration",
                "Time-sensitive research needs",
                "General knowledge questions",
            ],
            "complexity": "low",
            "supports_streaming": True,
            "features": [
                "Single-pass execution",
                "Strategic query allocation (RAG vs Web)",
                "Fast results with minimal overhead",
                "Maximum 2 refinement iterations",
                "Meta-reasoning reflection & self-critique",
                "Parallel RAG and web search",
            ],
            "performance": {"avg_execution_time": "30-60 seconds", "max_iterations": 2, "nodes": 6},
        }
