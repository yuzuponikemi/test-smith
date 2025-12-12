"""
Deep Research Graph - Hierarchical Multi-Agent Research Workflow

This graph implements the v2.1 Deep Research system with:
- Hierarchical task decomposition
- Dynamic replanning (Phase 4)
- Depth-aware exploration
- Strategic query allocation (RAG vs Web)
- Recursive drill-down capabilities

Use cases:
- Complex multi-faceted research questions
- Topics requiring deep exploration
- Queries benefiting from subtask decomposition
"""

import builtins
import operator
import sys
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from src.nodes.analyzer_node import analyzer_node

# Hierarchical nodes (Phase 2)
from src.nodes.depth_evaluator_node import depth_evaluator

# Hierarchical nodes (Phase 3)
from src.nodes.drill_down_generator import drill_down_generator
from src.nodes.evaluator_node import evaluator_node

# Hierarchical nodes (Phase 1)
from src.nodes.master_planner_node import master_planner

# Phase 2: Long Report Generation - Writer Graph Nodes
from src.nodes.outline_generator_node import outline_generator_node

# Hierarchical nodes (Phase 4 - Dynamic Replanning)
from src.nodes.plan_revisor_node import plan_revisor

# Import existing nodes
from src.nodes.planner_node import planner
from src.nodes.rag_retriever_node import rag_retriever

# Reflection node (Meta-reasoning & Self-Critique)
from src.nodes.reflection_node import reflection_node

# Quality feedback loop
from src.nodes.report_quality_checker_node import report_quality_checker_node
from src.nodes.report_reviewer_node import report_reviewer_node
from src.nodes.report_revisor_node import report_revisor_node

# Phase 1: Long Report Generation - Result Aggregator
from src.nodes.result_aggregator_node import result_aggregator_node
from src.nodes.searcher_node import searcher
from src.nodes.section_writer_node import section_writer_node
from src.nodes.subtask_executor import subtask_executor
from src.nodes.subtask_result_aggregator import save_subtask_result
from src.nodes.subtask_router import subtask_router
from src.nodes.synthesizer_node import synthesizer_node

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
    """State for Deep Research workflow with hierarchical capabilities"""

    # Original query
    query: str

    # Research depth control
    research_depth: str  # "quick", "standard", "deep", "comprehensive"

    # === Hierarchical Mode Fields (Phase 1) ===
    execution_mode: str  # "simple" or "hierarchical"
    master_plan: dict  # MasterPlan as dict (JSON-serializable)
    current_subtask_id: str  # ID of currently executing subtask
    current_subtask_index: int  # Index in subtask list
    subtask_results: dict  # subtask_id → analyzed_data

    # === Hierarchical Mode Fields (Phase 2) ===
    max_depth: int  # Maximum recursion depth (default: 2 for Phase 2-beta)
    depth_evaluation: dict  # Current subtask's DepthEvaluation (as dict)
    subtask_evaluations: dict  # All depth evaluations: subtask_id → DepthEvaluation dict

    # === Hierarchical Mode Fields (Phase 4 - Dynamic Replanning) ===
    revision_count: int  # Number of plan revisions made during this execution
    plan_revisions: list  # History of all plan revisions (list of PlanRevision dicts)
    max_revisions: int  # Maximum allowed plan revisions (default: 3)
    max_total_subtasks: int  # Maximum total subtasks allowed (default: 20)
    revision_triggers: list  # List of triggers that caused revisions (for logging)

    # === Recursion Budget Tracking (Phase 4.1 - Budget-Aware Control) ===
    node_execution_count: int  # Number of node executions (tracks recursion usage)
    recursion_limit: int  # Maximum recursion limit from config (default: 150)
    budget_warnings: list  # Warnings when budget is running low

    # === Existing Fields (used per-subtask in hierarchical mode) ===
    web_queries: list[str]  # Queries for web search
    rag_queries: list[str]  # Queries for RAG retrieval
    allocation_strategy: str  # Reasoning for query allocation
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]
    report: str
    evaluation: str
    reason: str  # Evaluator's reasoning (used as feedback for planner refinement)
    loop_count: int

    # === Reflection & Self-Critique Fields ===
    reflection_critique: dict  # ReflectionCritique as dict (JSON-serializable)
    reflection_quality: (
        str  # Overall quality assessment: "excellent" | "good" | "adequate" | "poor"
    )
    should_continue_research: (
        bool  # Whether reflection identified critical gaps requiring more research
    )
    reflection_confidence: float  # Confidence score from reflection (0.0-1.0)

    # === Phase 1: Long Report Generation Fields ===
    aggregated_findings: dict  # AggregatedFindings as dict (JSON-serializable)
    findings_ready: bool  # Whether findings are ready for writing

    # === Phase 2: Writer Graph Integration Fields ===
    report_outline: dict  # ReportOutline as dict (JSON-serializable)
    draft_report: str  # Current draft of the report
    section_word_counts: dict  # Word counts per section
    total_word_count: int  # Total word count
    review_result: dict  # ReportReviewResult as dict
    needs_revision: bool  # Whether report needs revision

    # === Quality Feedback Loop Fields ===
    quality_check_passed: bool  # Whether report meets quality criteria
    quality_feedback: str  # Feedback for planner if retry needed
    quality_retry_count: int  # Number of quality-based retries


def router(state):
    """
    Router after reflection - handles both simple and hierarchical modes

    Incorporates reflection critique to make more informed routing decisions.
    Checks both evaluation and reflection to determine next step.
    Uses research_depth to determine max iterations.

    Simple mode: Loop back to planner if reflection identifies critical gaps
    Hierarchical mode: Save result and move to next subtask or synthesize
    """
    print("---ROUTER (POST-REFLECTION)---")

    execution_mode = state.get("execution_mode", "simple")

    if execution_mode == "simple":
        # Get max iterations from research depth config
        from src.config.research_depth import get_depth_config

        research_depth = state.get("research_depth", "standard")
        depth_config = get_depth_config(research_depth)
        max_iterations = depth_config.max_iterations

        # Check both evaluation and reflection
        loop_count = state.get("loop_count", 0)
        evaluation = state.get("evaluation", "")
        should_continue_research = state.get("should_continue_research", False)
        reflection_quality = state.get("reflection_quality", "adequate")

        # Force exit after max loops (depth-aware)
        if loop_count >= max_iterations:
            print(
                f"  Simple mode: Max loops reached ({max_iterations}, depth={research_depth}) → synthesize"
            )
            return "synthesizer"

        # Check reflection feedback first (higher priority)
        if should_continue_research:
            print(
                f"  Simple mode: Reflection identified critical gaps (quality: {reflection_quality}) → refine with planner"
            )
            return "planner"

        # Check evaluation
        if "sufficient" in evaluation.lower():
            print(
                f"  Simple mode: Evaluation sufficient, reflection quality: {reflection_quality} → synthesize"
            )
            return "synthesizer"
        else:
            print("  Simple mode: Evaluation insufficient → refine with planner")
            return "planner"

    else:
        # Hierarchical mode: Always save result and check if more subtasks
        print("  Hierarchical mode: Saving subtask result")
        return "save_result"


def analyzer_router(state):
    """Route to depth_evaluator for hierarchical mode, regular evaluator for simple mode"""
    execution_mode = state.get("execution_mode", "simple")
    if execution_mode == "hierarchical":
        print("---ANALYZER ROUTER: Using depth_evaluator for hierarchical mode---")
        return "depth_evaluator"
    else:
        print("---ANALYZER ROUTER: Using regular evaluator for simple mode---")
        return "evaluator"


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


def quality_check_router(state):
    """
    Router after quality checker - decides whether to retry research or finish.

    For SIMPLE mode: If quality check failed and retries available, go back to planner.
    For HIERARCHICAL mode: Quality check is not used (uses Writer Graph instead).
    """
    print("---QUALITY CHECK ROUTER---")
    execution_mode = state.get("execution_mode", "simple")
    quality_check_passed = state.get("quality_check_passed", True)

    if execution_mode != "simple":
        # Hierarchical mode doesn't use this quality check loop
        print("  Hierarchical mode: Skipping quality check loop → END")
        return "end"

    if quality_check_passed:
        print("  Quality check passed → END")
        return "end"
    else:
        quality_retry_count = state.get("quality_retry_count", 0)
        print(f"  Quality check failed, retry {quality_retry_count}/2 → planner")
        return "planner"


class DeepResearchGraphBuilder(BaseGraphBuilder):
    """Builder for the Deep Research hierarchical workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return DeepResearchState

    def build(self) -> Any:
        """Build and compile the Deep Research workflow"""
        workflow = StateGraph(DeepResearchState)

        # Register existing nodes
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Register new hierarchical nodes (Phase 1)
        workflow.add_node("master_planner", master_planner)
        workflow.add_node("subtask_executor", subtask_executor)
        workflow.add_node("save_result", save_subtask_result)

        # Register new hierarchical nodes (Phase 2)
        workflow.add_node("depth_evaluator", depth_evaluator)

        # Register new hierarchical nodes (Phase 3)
        workflow.add_node("drill_down_generator", drill_down_generator)

        # Register new hierarchical nodes (Phase 4)
        workflow.add_node("plan_revisor", plan_revisor)

        # Register reflection node (Meta-reasoning & Self-Critique)
        workflow.add_node("reflection", reflection_node)

        # Register Phase 1 Long Report Generation nodes
        workflow.add_node("result_aggregator", result_aggregator_node)  # type: ignore[type-var]

        # Register Phase 2 Long Report Generation nodes (Writer Graph)
        workflow.add_node("outline_generator", outline_generator_node)  # type: ignore[type-var]
        workflow.add_node("section_writer", section_writer_node)  # type: ignore[type-var]
        workflow.add_node("report_reviewer", report_reviewer_node)  # type: ignore[type-var]
        workflow.add_node("report_revisor", report_revisor_node)  # type: ignore[type-var]

        # Register Quality Feedback Loop node
        workflow.add_node("quality_checker", report_quality_checker_node)  # type: ignore[type-var]

        # Entry point: Master Planner (Phase 1 change)
        workflow.set_entry_point("master_planner")

        # After master planner: Route based on complexity
        workflow.add_conditional_edges(
            "master_planner",
            subtask_router,
            {
                "simple": "planner",  # Simple mode: Use existing flow
                "execute_subtask": "subtask_executor",  # Hierarchical: Start first subtask
                "synthesize": "synthesizer",  # Edge case: no subtasks to execute
            },
        )

        # Subtask executor → Strategic Planner (for this specific subtask)
        workflow.add_edge("subtask_executor", "planner")

        # Existing edges
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # After analyzer: Route to appropriate evaluator based on mode (Phase 2 enhancement)
        workflow.add_conditional_edges(
            "analyzer",
            analyzer_router,
            {"evaluator": "evaluator", "depth_evaluator": "depth_evaluator"},
        )

        # After depth_evaluator: Check for drill-down, then revise plan, then save result (Phase 3 + Phase 4)
        workflow.add_edge("depth_evaluator", "drill_down_generator")
        workflow.add_edge(
            "drill_down_generator", "plan_revisor"
        )  # Phase 4: Plan revision after drill-down
        workflow.add_edge("plan_revisor", "save_result")

        # After evaluator: Go to reflection for meta-reasoning critique
        workflow.add_edge("evaluator", "reflection")

        # After reflection: Route based on mode and reflection feedback
        workflow.add_conditional_edges(
            "reflection",
            router,
            {
                "synthesizer": "synthesizer",  # Simple mode: sufficient
                "planner": "planner",  # Simple mode: loop back
                "save_result": "save_result",  # Hierarchical: save and continue
            },
        )

        # After saving result: Check if more subtasks
        workflow.add_conditional_edges(
            "save_result",
            post_save_router,
            {
                "execute_subtask": "subtask_executor",  # More subtasks to execute
                "synthesize": "result_aggregator",  # All done → aggregate first
            },
        )

        # Phase 1 Long Report: result_aggregator → outline_generator
        workflow.add_edge("result_aggregator", "outline_generator")

        # Phase 2 Long Report: Writer Graph flow
        workflow.add_edge("outline_generator", "section_writer")
        workflow.add_edge("section_writer", "report_reviewer")

        # After reviewer: revise or proceed to synthesizer
        workflow.add_conditional_edges(
            "report_reviewer",
            writer_review_router,
            {
                "report_revisor": "report_revisor",
                "synthesizer": "synthesizer",
            },
        )

        # Revisor loops back to reviewer
        workflow.add_edge("report_revisor", "report_reviewer")

        # Synthesizer → Quality Checker (for SIMPLE mode quality feedback loop)
        workflow.add_edge("synthesizer", "quality_checker")

        # Quality Checker routes: retry research or finish
        workflow.add_conditional_edges(
            "quality_checker",
            quality_check_router,
            {
                "planner": "planner",  # Retry research with feedback
                "end": END,  # Quality passed or max retries
            },
        )

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(DeepResearchState)

        # Register all nodes (same as build())
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("synthesizer", synthesizer_node)
        workflow.add_node("master_planner", master_planner)
        workflow.add_node("subtask_executor", subtask_executor)
        workflow.add_node("save_result", save_subtask_result)
        workflow.add_node("depth_evaluator", depth_evaluator)
        workflow.add_node("drill_down_generator", drill_down_generator)
        workflow.add_node("plan_revisor", plan_revisor)
        workflow.add_node("reflection", reflection_node)
        workflow.add_node("result_aggregator", result_aggregator_node)  # type: ignore[type-var]
        workflow.add_node("outline_generator", outline_generator_node)  # type: ignore[type-var]
        workflow.add_node("section_writer", section_writer_node)  # type: ignore[type-var]
        workflow.add_node("report_reviewer", report_reviewer_node)  # type: ignore[type-var]
        workflow.add_node("report_revisor", report_revisor_node)  # type: ignore[type-var]
        workflow.add_node("quality_checker", report_quality_checker_node)  # type: ignore[type-var]

        # Set up all edges (same as build())
        workflow.set_entry_point("master_planner")
        workflow.add_conditional_edges(
            "master_planner",
            subtask_router,
            {
                "simple": "planner",
                "execute_subtask": "subtask_executor",
                "synthesize": "synthesizer",
            },
        )
        workflow.add_edge("subtask_executor", "planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")
        workflow.add_conditional_edges(
            "analyzer",
            analyzer_router,
            {"evaluator": "evaluator", "depth_evaluator": "depth_evaluator"},
        )
        workflow.add_edge("depth_evaluator", "drill_down_generator")
        workflow.add_edge("drill_down_generator", "plan_revisor")
        workflow.add_edge("plan_revisor", "save_result")
        workflow.add_edge("evaluator", "reflection")
        workflow.add_conditional_edges(
            "reflection",
            router,
            {"synthesizer": "synthesizer", "planner": "planner", "save_result": "save_result"},
        )
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
        workflow.add_edge("synthesizer", "quality_checker")
        workflow.add_conditional_edges(
            "quality_checker",
            quality_check_router,
            {"planner": "planner", "end": END},
        )

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Deep Research",
            "description": "Hierarchical multi-agent research with dynamic replanning and long-form report generation",
            "version": "2.2",
            "use_cases": [
                "Complex multi-faceted research questions",
                "Topics requiring deep exploration",
                "Queries benefiting from subtask decomposition",
                "Adaptive research that discovers new angles mid-execution",
                "Long-form report generation (6,000+ words)",
            ],
            "complexity": "high",
            "supports_streaming": True,
            "features": [
                "Hierarchical task decomposition",
                "Dynamic replanning (Phase 4)",
                "Depth-aware exploration",
                "Strategic query allocation (RAG vs Web)",
                "Recursive drill-down up to 2 levels",
                "Budget-aware execution control",
                "Meta-reasoning reflection & self-critique",
                "Result aggregation with quality validation (Long Report Phase 1)",
                "Outline-driven report generation (Long Report Phase 2)",
                "Multi-section report writing with review-revise loop",
                "Language consistency enforcement",
            ],
            "phases": {
                "1": "Basic hierarchical decomposition",
                "2": "Depth evaluation and quality assessment",
                "3": "Recursive drill-down for important subtasks",
                "4": "Dynamic plan revision based on discoveries",
                "4.1": "Budget-aware control and monitoring",
                "5": "Result aggregation and quality validation",
                "6": "Outline-driven long-form report generation",
            },
        }
