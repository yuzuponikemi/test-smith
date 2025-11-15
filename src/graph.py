from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Existing nodes
from src.nodes.planner_node import planner
from src.nodes.searcher_node import searcher
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.analyzer_node import analyzer_node
from src.nodes.synthesizer_node import synthesizer_node
from src.nodes.evaluator_node import evaluator_node

# New hierarchical nodes (Phase 1)
from src.nodes.master_planner_node import master_planner
from src.nodes.subtask_router import subtask_router
from src.nodes.subtask_executor import subtask_executor
from src.nodes.subtask_result_aggregator import save_subtask_result

# New hierarchical nodes (Phase 2)
from src.nodes.depth_evaluator_node import depth_evaluator

# New hierarchical nodes (Phase 3)
from src.nodes.drill_down_generator import drill_down_generator

# New hierarchical nodes (Phase 4 - Dynamic Replanning)
from src.nodes.plan_revisor_node import plan_revisor

# Define the state
class AgentState(TypedDict):
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

# Define the graph
workflow = StateGraph(AgentState)

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

# After analyzer: Route to appropriate evaluator based on mode (Phase 2 enhancement)
def analyzer_router(state):
    """Route to depth_evaluator for hierarchical mode, regular evaluator for simple mode"""
    execution_mode = state.get("execution_mode", "simple")
    if execution_mode == "hierarchical":
        print("---ANALYZER ROUTER: Using depth_evaluator for hierarchical mode---")
        return "depth_evaluator"
    else:
        print("---ANALYZER ROUTER: Using regular evaluator for simple mode---")
        return "evaluator"

workflow.add_conditional_edges(
    "analyzer",
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
def post_save_router(state):
    """Router after saving subtask result"""
    print("---POST-SAVE ROUTER---")
    return subtask_router(state)

workflow.add_conditional_edges(
    "save_result",
    post_save_router,
    {
        "execute_subtask": "subtask_executor",  # More subtasks to execute
        "synthesize": "synthesizer"  # All done, synthesize
    }
)

workflow.add_edge("synthesizer", END)

# Compile the workflow for LangGraph Studio
# Note: LangGraph Studio will provide its own checkpointer (PostgreSQL)
# so we don't include one here
workflow = workflow.compile()
