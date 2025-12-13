"""
Deep Research Graph - Unified Hierarchical Multi-Agent Research Workflow

v3.0: Unified architecture - all queries go through the hierarchical flow.
Even simple queries get at least 1 subtask and go through Writer Graph.

This graph implements:
- Hierarchical task decomposition (always at least 1 subtask)
- Dynamic replanning (Phase 4)
- Depth-aware exploration
- Strategic query allocation (RAG vs Web)
- Writer Graph for quality report generation
- Recursive drill-down capabilities

Use cases:
- All research questions (simple to complex)
- Topics requiring deep exploration
- Long-form report generation with quality checks
"""

import builtins
import operator
import sys
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

# Core research nodes
from src.nodes.analyzer_node import analyzer_node

# Hierarchical orchestration nodes
from src.nodes.depth_evaluator_node import depth_evaluator
from src.nodes.drill_down_generator import drill_down_generator
from src.nodes.master_planner_node import master_planner

# Result aggregation & Writer Graph nodes
from src.nodes.outline_generator_node import outline_generator_node
from src.nodes.plan_revisor_node import plan_revisor
from src.nodes.planner_node import planner
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.report_reviewer_node import report_reviewer_node
from src.nodes.report_revisor_node import report_revisor_node
from src.nodes.result_aggregator_node import result_aggregator_node
from src.nodes.searcher_node import searcher
from src.nodes.section_writer_node import section_writer_node
from src.nodes.subtask_executor import subtask_executor
from src.nodes.subtask_result_aggregator import save_subtask_result
from src.nodes.subtask_router import subtask_router
from src.nodes.synthesizer_node import synthesizer_node

# Term definition node (prevents topic drift)
from src.nodes.term_definer_node import term_definer_node

from .base_graph import BaseGraphBuilder


# Override print for Studio compatibility (prevents BrokenPipeError)
def _safe_print(*args, **kwargs):
    """Print function that doesn't raise BrokenPipeError in Studio environments"""
    try:
        builtins.__dict__.get("_original_print", print)(*args, **kwargs)
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        pass  # Silently ignore broken pipe errors


if "_original_print" not in builtins.__dict__:
    builtins.__dict__["_original_print"] = print
builtins.print = _safe_print


class DeepResearchState(TypedDict):
    """
    State for Deep Research workflow.

    v3.0: Unified architecture - always uses hierarchical flow with Writer Graph.
    v3.1: Added term_definitions for topic drift prevention.
    """

    # === Core Query Fields ===
    query: str  # Original user query
    research_depth: str  # "quick", "standard", "deep", "comprehensive"

    # === Term Definition Fields (v3.1 - topic drift prevention) ===
    extracted_terms: list[str]  # Technical terms extracted from query
    term_definitions: dict  # term → {category, definition, key_features, common_confusions}

    # === Hierarchical Orchestration Fields ===
    execution_mode: str  # Always "hierarchical" in v3.0
    master_plan: dict  # MasterPlan as dict (JSON-serializable)
    current_subtask_id: str  # ID of currently executing subtask
    current_subtask_index: int  # Index in subtask list
    subtask_results: dict  # subtask_id → analyzed_data

    # === Depth Evaluation Fields ===
    max_depth: int  # Maximum recursion depth (default: 2)
    depth_evaluation: dict  # Current subtask's DepthEvaluation
    subtask_evaluations: dict  # All depth evaluations: subtask_id → DepthEvaluation

    # === Dynamic Replanning Fields (Phase 4) ===
    revision_count: int  # Number of plan revisions made
    plan_revisions: list  # History of all plan revisions
    max_revisions: int  # Maximum allowed plan revisions (default: 3)
    max_total_subtasks: int  # Maximum total subtasks allowed
    revision_triggers: list  # List of triggers that caused revisions

    # === Recursion Budget Tracking ===
    node_execution_count: int  # Number of node executions
    recursion_limit: int  # Maximum recursion limit from config
    budget_warnings: list  # Warnings when budget is running low

    # === Per-Subtask Research Fields ===
    web_queries: list[str]  # Queries for web search
    rag_queries: list[str]  # Queries for RAG retrieval
    allocation_strategy: str  # Reasoning for query allocation
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]
    loop_count: int

    # === Result Aggregation Fields ===
    aggregated_findings: dict  # AggregatedFindings as dict
    findings_ready: bool  # Whether findings are ready for writing

    # === Writer Graph Fields ===
    report_outline: dict  # ReportOutline as dict
    draft_report: str  # Current draft of the report
    section_word_counts: dict  # Word counts per section
    total_word_count: int  # Total word count
    review_result: dict  # ReportReviewResult as dict
    needs_revision: bool  # Whether report needs revision

    # === Final Output Fields ===
    report: str  # Final synthesized report


def post_save_router(state):
    """Router after saving subtask result"""
    print("---POST-SAVE ROUTER---")
    return subtask_router(state)


def writer_review_router(state):
    """
    Router after report reviewer - decides whether to revise or finalize.

    Routes to revisor if needs_revision is True and revision_count < 3.
    Otherwise routes to synthesizer for final output.
    """
    print("---WRITER REVIEW ROUTER---")
    needs_revision = state.get("needs_revision", False)
    revision_count = state.get("revision_count", 0)

    if needs_revision and revision_count < 3:
        print(f"  Report needs revision (attempt {revision_count + 1}/3)")
        return "report_revisor"
    else:
        if needs_revision:
            print("  Max revisions reached, proceeding to synthesizer")
        else:
            print("  Report passed review, proceeding to synthesizer")
        return "synthesizer"


class DeepResearchGraphBuilder(BaseGraphBuilder):
    """Builder for the Deep Research hierarchical workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return DeepResearchState

    def build(self) -> Any:
        """
        Build and compile the Deep Research workflow.

        v3.0: Unified architecture - always uses hierarchical flow with Writer Graph.
        Even simple queries get at least 1 subtask and go through the full pipeline.

        Flow:
        master_planner → subtask_executor → planner → search → analyze
        → depth_evaluator → drill_down → plan_revisor → save_result
        → (loop for more subtasks or) result_aggregator → Writer Graph → synthesizer → END
        """
        workflow = StateGraph(DeepResearchState)

        # === Term Definition Node (v3.1 - prevents topic drift) ===
        workflow.add_node("term_definer", term_definer_node)  # type: ignore[type-var]

        # === Core Research Nodes ===
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # === Hierarchical Orchestration Nodes ===
        workflow.add_node("master_planner", master_planner)
        workflow.add_node("subtask_executor", subtask_executor)
        workflow.add_node("save_result", save_subtask_result)
        workflow.add_node("depth_evaluator", depth_evaluator)
        workflow.add_node("drill_down_generator", drill_down_generator)
        workflow.add_node("plan_revisor", plan_revisor)

        # === Result Aggregation & Writer Graph Nodes ===
        workflow.add_node("result_aggregator", result_aggregator_node)  # type: ignore[type-var]
        workflow.add_node("outline_generator", outline_generator_node)  # type: ignore[type-var]
        workflow.add_node("section_writer", section_writer_node)  # type: ignore[type-var]
        workflow.add_node("report_reviewer", report_reviewer_node)  # type: ignore[type-var]
        workflow.add_node("report_revisor", report_revisor_node)  # type: ignore[type-var]

        # === Entry Point: Start with Term Definer (v3.1) ===
        workflow.set_entry_point("term_definer")

        # === Term Definer → Master Planner ===
        workflow.add_edge("term_definer", "master_planner")

        # === Master Planner → Subtask Execution ===
        # Always routes to execute_subtask (unified architecture)
        workflow.add_conditional_edges(
            "master_planner",
            subtask_router,
            {
                "execute_subtask": "subtask_executor",
                "synthesize": "result_aggregator",  # Edge case: skip to aggregation
            },
        )

        # === Subtask Execution Flow ===
        workflow.add_edge("subtask_executor", "planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # === After Analyzer: Always use depth_evaluator ===
        workflow.add_edge("analyzer", "depth_evaluator")

        # === Depth Evaluation → Drill-Down → Plan Revision → Save ===
        workflow.add_edge("depth_evaluator", "drill_down_generator")
        workflow.add_edge("drill_down_generator", "plan_revisor")
        workflow.add_edge("plan_revisor", "save_result")

        # === After Save: More subtasks or aggregate results ===
        workflow.add_conditional_edges(
            "save_result",
            post_save_router,
            {
                "execute_subtask": "subtask_executor",
                "synthesize": "result_aggregator",
            },
        )

        # === Writer Graph Flow ===
        workflow.add_edge("result_aggregator", "outline_generator")
        workflow.add_edge("outline_generator", "section_writer")
        workflow.add_edge("section_writer", "report_reviewer")

        workflow.add_conditional_edges(
            "report_reviewer",
            writer_review_router,
            {
                "report_revisor": "report_revisor",
                "synthesizer": "synthesizer",
            },
        )
        workflow.add_edge("report_revisor", "report_reviewer")

        # === Final Output ===
        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup (same as build())"""
        workflow = StateGraph(DeepResearchState)

        # === Term Definition Node (v3.1 - prevents topic drift) ===
        workflow.add_node("term_definer", term_definer_node)  # type: ignore[type-var]

        # === Core Research Nodes ===
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # === Hierarchical Orchestration Nodes ===
        workflow.add_node("master_planner", master_planner)
        workflow.add_node("subtask_executor", subtask_executor)
        workflow.add_node("save_result", save_subtask_result)
        workflow.add_node("depth_evaluator", depth_evaluator)
        workflow.add_node("drill_down_generator", drill_down_generator)
        workflow.add_node("plan_revisor", plan_revisor)

        # === Result Aggregation & Writer Graph Nodes ===
        workflow.add_node("result_aggregator", result_aggregator_node)  # type: ignore[type-var]
        workflow.add_node("outline_generator", outline_generator_node)  # type: ignore[type-var]
        workflow.add_node("section_writer", section_writer_node)  # type: ignore[type-var]
        workflow.add_node("report_reviewer", report_reviewer_node)  # type: ignore[type-var]
        workflow.add_node("report_revisor", report_revisor_node)  # type: ignore[type-var]

        # === Entry Point & Edges ===
        workflow.set_entry_point("term_definer")
        workflow.add_edge("term_definer", "master_planner")
        workflow.add_conditional_edges(
            "master_planner",
            subtask_router,
            {
                "execute_subtask": "subtask_executor",
                "synthesize": "result_aggregator",
            },
        )
        workflow.add_edge("subtask_executor", "planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")
        workflow.add_edge("analyzer", "depth_evaluator")
        workflow.add_edge("depth_evaluator", "drill_down_generator")
        workflow.add_edge("drill_down_generator", "plan_revisor")
        workflow.add_edge("plan_revisor", "save_result")
        workflow.add_conditional_edges(
            "save_result",
            post_save_router,
            {"execute_subtask": "subtask_executor", "synthesize": "result_aggregator"},
        )
        workflow.add_edge("result_aggregator", "outline_generator")
        workflow.add_edge("outline_generator", "section_writer")
        workflow.add_edge("section_writer", "report_reviewer")
        workflow.add_conditional_edges(
            "report_reviewer",
            writer_review_router,
            {"report_revisor": "report_revisor", "synthesizer": "synthesizer"},
        )
        workflow.add_edge("report_revisor", "report_reviewer")
        workflow.add_edge("synthesizer", END)

        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Deep Research",
            "description": "Unified hierarchical research with Writer Graph - all queries go through the same quality pipeline",
            "version": "3.1",
            "use_cases": [
                "All research questions (simple to complex)",
                "Topics requiring deep exploration",
                "Long-form report generation with quality checks",
                "Adaptive research that discovers new angles mid-execution",
            ],
            "complexity": "medium-high",
            "supports_streaming": True,
            "features": [
                "Term definition verification (v3.1 - prevents topic drift)",
                "Multi-layer consistency checking (Analyzer + Evaluator)",
                "Unified architecture (no simple/hierarchical split)",
                "Always at least 1 subtask (even for simple queries)",
                "Writer Graph for all reports (quality guaranteed)",
                "Hierarchical task decomposition",
                "Dynamic replanning",
                "Depth-aware exploration",
                "Strategic query allocation (RAG vs Web)",
                "Recursive drill-down up to 2 levels",
                "Budget-aware execution control",
                "Result aggregation with quality validation",
                "Outline-driven report generation",
                "Multi-section report writing with review-revise loop",
                "Language consistency enforcement",
            ],
            "flow": (
                "term_definer → master_planner → subtask_executor → planner → search → analyze → "
                "depth_eval → drill_down → plan_revisor → save_result → "
                "(loop or) result_aggregator → Writer Graph → synthesizer → END"
            ),
        }
