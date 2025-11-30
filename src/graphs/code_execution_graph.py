"""
Code Execution Graph - Research with Code Execution Capabilities

This graph implements a research workflow with integrated code execution:
- Strategic query allocation (RAG vs Web)
- Data gathering and analysis
- Code generation and execution for complex tasks
- Result synthesis

Use cases:
- Research requiring calculations or data processing
- Questions needing verification through code
- Tasks requiring data transformation or analysis
- Complex problem-solving with computational steps
"""

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

from src.nodes.analyzer_node import analyzer_node
from src.nodes.code_executor_node import code_executor
from src.nodes.evaluator_node import evaluator_node

# Import reusable nodes
from src.nodes.planner_node import planner
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.searcher_node import searcher
from src.nodes.synthesizer_node import synthesizer_node

from .base_graph import BaseGraphBuilder


class CodeExecutionState(TypedDict):
    """State for code execution workflow"""

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

    # Code execution fields
    code_task: str  # Description of code task
    context_for_code: str  # Context from research for code generation
    code_input_data: str  # Input data for code
    code_requirements: list[str]  # Requirements for code
    expected_code_output: str  # Expected output format
    code_execution_results: Annotated[list[dict], operator.add]  # Code execution results

    # Evaluation and control
    evaluation: str
    reason: str
    loop_count: int
    needs_code_execution: bool  # Whether code execution is needed


def code_router(state: CodeExecutionState) -> Literal["code_executor", "evaluator"]:
    """
    Router for code execution decision.

    For code_execution graph, we always execute code since this graph
    was specifically selected for computational tasks.
    """
    print("  Code execution graph → always execute code")
    return "code_executor"


def continuation_router(state: CodeExecutionState) -> Literal["synthesizer", "planner"]:
    """
    Router for continuing research or synthesizing.

    Checks evaluation and loop count to determine next step.
    Max 2 iterations to prevent long execution.
    """
    loop_count = state.get("loop_count", 0)
    evaluation = state.get("evaluation", "")

    # Force exit after max loops
    if loop_count >= 2:
        print("  Max loops reached → synthesize")
        return "synthesizer"

    # Check evaluation
    if "sufficient" in evaluation.lower():
        print("  Evaluation sufficient → synthesize")
        return "synthesizer"
    else:
        print("  Evaluation insufficient → refine")
        return "planner"


class CodeExecutionGraphBuilder(BaseGraphBuilder):
    """Builder for the Code Execution research workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return CodeExecutionState

    def build(self) -> StateGraph:
        """Build and compile the Code Execution workflow"""
        workflow = StateGraph(CodeExecutionState)

        # Register nodes
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("code_executor", code_executor)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up flow
        workflow.set_entry_point("planner")

        # Planner → Parallel execution
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")

        # Parallel execution → Analyzer
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # Analyzer → Code Router (decides if code execution is needed)
        workflow.add_conditional_edges(
            "analyzer",
            code_router,
            {
                "code_executor": "code_executor",
                "evaluator": "evaluator"
            }
        )

        # Code Executor → Evaluator
        workflow.add_edge("code_executor", "evaluator")

        # Evaluator → Continuation Router
        workflow.add_conditional_edges(
            "evaluator",
            continuation_router,
            {
                "synthesizer": "synthesizer",
                "planner": "planner"
            }
        )

        # Synthesizer → END
        workflow.add_edge("synthesizer", END)

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(CodeExecutionState)

        # Register nodes
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("code_executor", code_executor)
        workflow.add_node("evaluator", evaluator_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")
        workflow.add_conditional_edges(
            "analyzer",
            code_router,
            {"code_executor": "code_executor", "evaluator": "evaluator"}
        )
        workflow.add_edge("code_executor", "evaluator")
        workflow.add_conditional_edges(
            "evaluator",
            continuation_router,
            {"synthesizer": "synthesizer", "planner": "planner"}
        )
        workflow.add_edge("synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Code Execution Research",
            "description": "Research workflow with integrated code execution capabilities",
            "version": "1.0",
            "use_cases": [
                "Research requiring calculations or data processing",
                "Questions needing verification through code",
                "Tasks requiring data transformation or analysis",
                "Complex problem-solving with computational steps",
                "Mathematical or statistical analysis",
                "Data validation and verification"
            ],
            "complexity": "medium",
            "supports_streaming": True,
            "features": [
                "Strategic query allocation (RAG vs Web)",
                "Parallel data gathering",
                "Automated code generation",
                "Safe code execution environment",
                "Iterative refinement (max 2 iterations)",
                "Result synthesis with code outputs"
            ],
            "performance": {
                "avg_execution_time": "60-120 seconds",
                "max_iterations": 2,
                "nodes": 7
            }
        }
