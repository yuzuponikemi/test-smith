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

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Literal
import operator
import sys
import builtins

from .base_graph import BaseGraphBuilder

# Import existing nodes
from src.nodes.planner_node import planner
from src.nodes.searcher_node import searcher
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.analyzer_node import analyzer_node
from src.nodes.synthesizer_node import synthesizer_node
from src.nodes.evaluator_node import evaluator_node

# Hierarchical nodes (Phase 1)
from src.nodes.master_planner_node import master_planner
from src.nodes.subtask_router import subtask_router
from src.nodes.subtask_executor import subtask_executor
from src.nodes.subtask_result_aggregator import save_subtask_result

# Hierarchical nodes (Phase 2)
from src.nodes.depth_evaluator_node import depth_evaluator

# Hierarchical nodes (Phase 3)
from src.nodes.drill_down_generator import drill_down_generator

# Hierarchical nodes (Phase 4 - Dynamic Replanning)
from src.nodes.plan_revisor_node import plan_revisor

# Tool use nodes (Phase 5 - Computational Enhancement)
from src.nodes.tool_planner_node import tool_planner
from src.nodes.tool_executor_node import tool_executor, tool_results_aggregator


# Override print for Studio compatibility (prevents BrokenPipeError)
def _safe_print(*args, **kwargs):
    """Print function that doesn't raise BrokenPipeError in Studio environments"""
    try:
        builtins.__dict__.get('_original_print', print)(*args, **kwargs)
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        pass  # Silently ignore broken pipe errors

if '_original_print' not in builtins.__dict__:
    builtins.__dict__['_original_print'] = print
builtins.print = _safe_print


class DeepResearchState(TypedDict):
    """State for Deep Research workflow with hierarchical capabilities"""

    # Original query
    query: str

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

    # === Tool Use Fields (Phase 5 - Computational Enhancement) ===
    tools_enabled: bool  # Whether tool use is enabled (default: True)
    tool_calls: list  # Planned tool invocations from tool_planner
    tool_results: list  # Results from tool_executor
    tool_results_text: str  # Formatted tool results for synthesis
    tool_planning_result: str  # Reasoning from tool planner

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


def router(state):
    """
    Router after evaluator - handles both simple and hierarchical modes

    Simple mode: Loop back to planner if insufficient
    Hierarchical mode: Save result and move to next subtask or synthesize
    """
    print("---ROUTER (POST-EVALUATOR)---")

    execution_mode = state.get("execution_mode", "simple")

    if execution_mode == "simple":
        # Existing simple mode logic
        loop_count = state.get("loop_count", 0)
        evaluation = state.get("evaluation", "")

        if "sufficient" in evaluation.lower() or loop_count >= 2:
            print("  Simple mode: Evaluation sufficient or max loops reached → synthesize")
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


class DeepResearchGraphBuilder(BaseGraphBuilder):
    """Builder for the Deep Research hierarchical workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return DeepResearchState

    def build(self) -> StateGraph:
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

        # Register tool use nodes (Phase 5)
        workflow.add_node("tool_planner", tool_planner)
        workflow.add_node("tool_executor", tool_executor)
        workflow.add_node("tool_aggregator", tool_results_aggregator)

        # Entry point: Master Planner (Phase 1 change)
        workflow.set_entry_point("master_planner")

        # After master planner: Route based on complexity
        workflow.add_conditional_edges(
            "master_planner",
            subtask_router,
            {
                "simple": "planner",  # Simple mode: Use existing flow
                "execute_subtask": "subtask_executor",  # Hierarchical: Start first subtask
                "synthesize": "synthesizer"  # Edge case: no subtasks to execute
            }
        )

        # Subtask executor → Strategic Planner (for this specific subtask)
        workflow.add_edge("subtask_executor", "planner")

        # Existing edges
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # After analyzer: Go to tool planner for computational enhancement (Phase 5)
        workflow.add_edge("analyzer", "tool_planner")

        # Tool execution chain
        workflow.add_edge("tool_planner", "tool_executor")
        workflow.add_edge("tool_executor", "tool_aggregator")

        # After tool aggregation: Route to appropriate evaluator based on mode (Phase 2 enhancement)
        workflow.add_conditional_edges(
            "tool_aggregator",
            analyzer_router,
            {
                "evaluator": "evaluator",
                "depth_evaluator": "depth_evaluator"
            }
        )

        # After depth_evaluator: Check for drill-down, then revise plan, then save result (Phase 3 + Phase 4)
        workflow.add_edge("depth_evaluator", "drill_down_generator")
        workflow.add_edge("drill_down_generator", "plan_revisor")  # Phase 4: Plan revision after drill-down
        workflow.add_edge("plan_revisor", "save_result")

        # After evaluator: Route based on mode
        workflow.add_conditional_edges(
            "evaluator",
            router,
            {
                "synthesizer": "synthesizer",  # Simple mode: sufficient
                "planner": "planner",  # Simple mode: loop back
                "save_result": "save_result"  # Hierarchical: save and continue
            }
        )

        # After saving result: Check if more subtasks
        workflow.add_conditional_edges(
            "save_result",
            post_save_router,
            {
                "execute_subtask": "subtask_executor",  # More subtasks to execute
                "synthesize": "synthesizer"  # All done, synthesize
            }
        )

        workflow.add_edge("synthesizer", END)

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

        # Register tool use nodes (Phase 5)
        workflow.add_node("tool_planner", tool_planner)
        workflow.add_node("tool_executor", tool_executor)
        workflow.add_node("tool_aggregator", tool_results_aggregator)

        # Set up all edges (same as build())
        workflow.set_entry_point("master_planner")
        workflow.add_conditional_edges(
            "master_planner",
            subtask_router,
            {"simple": "planner", "execute_subtask": "subtask_executor", "synthesize": "synthesizer"}
        )
        workflow.add_edge("subtask_executor", "planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # Tool use chain (Phase 5)
        workflow.add_edge("analyzer", "tool_planner")
        workflow.add_edge("tool_planner", "tool_executor")
        workflow.add_edge("tool_executor", "tool_aggregator")

        workflow.add_conditional_edges(
            "tool_aggregator",
            analyzer_router,
            {"evaluator": "evaluator", "depth_evaluator": "depth_evaluator"}
        )
        workflow.add_edge("depth_evaluator", "drill_down_generator")
        workflow.add_edge("drill_down_generator", "plan_revisor")
        workflow.add_edge("plan_revisor", "save_result")
        workflow.add_conditional_edges(
            "evaluator",
            router,
            {"synthesizer": "synthesizer", "planner": "planner", "save_result": "save_result"}
        )
        workflow.add_conditional_edges(
            "save_result",
            post_save_router,
            {"execute_subtask": "subtask_executor", "synthesize": "synthesizer"}
        )
        workflow.add_edge("synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Deep Research",
            "description": "Hierarchical multi-agent research with dynamic replanning",
            "version": "2.1",
            "use_cases": [
                "Complex multi-faceted research questions",
                "Topics requiring deep exploration",
                "Queries benefiting from subtask decomposition",
                "Adaptive research that discovers new angles mid-execution"
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
                "Tool use for computation and verification (Phase 5)",
                "MCP tool integration for external services"
            ],
            "phases": {
                "1": "Basic hierarchical decomposition",
                "2": "Depth evaluation and quality assessment",
                "3": "Recursive drill-down for important subtasks",
                "4": "Dynamic plan revision based on discoveries",
                "4.1": "Budget-aware control and monitoring",
                "5": "Tool use for computational enhancement and verification"
            }
        }
