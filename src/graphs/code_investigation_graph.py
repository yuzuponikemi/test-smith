"""
Code Investigation Graph - Specialized workflow for codebase research and analysis

This graph implements a comprehensive codebase investigation workflow:
- Query analysis to understand investigation scope
- Raw file search + RAG retrieval for code
- Dependency analysis between classes/functions
- Data flow and control flow tracking
- Variable and function usage analysis
- Comprehensive investigation report

Use cases:
- Understanding how a feature works
- Finding where a function/class is used
- Tracing dependencies between components
- Investigating variable/data flow
- Architecture and design pattern analysis
- Code refactoring impact analysis
"""

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

# Import existing nodes
from src.nodes.code_assistant_node import code_retriever
from src.nodes.code_flow_tracker_node import code_flow_tracker_node
from src.nodes.code_investigation_synthesizer_node import code_investigation_synthesizer_node

# Import new nodes (to be created)
from src.nodes.code_query_analyzer_node import code_query_analyzer_node
from src.nodes.dependency_analyzer_node import dependency_analyzer_node

from .base_graph import BaseGraphBuilder


class CodeInvestigationState(TypedDict):
    """State schema for code investigation workflow"""

    # Core fields
    query: str  # Original investigation question
    report: str  # Final investigation report

    # Query analysis
    investigation_type: str  # Type: 'dependency', 'flow', 'usage', 'architecture', 'general'
    target_elements: list[str]  # Functions, classes, variables to investigate
    search_patterns: list[str]  # Patterns to search for (regex, glob)
    code_queries: list[str]  # Queries for RAG search
    investigation_scope: str  # Narrow, medium, or broad scope

    # Code retrieval
    code_results: Annotated[list[str], operator.add]  # RAG retrieved code (cumulative)
    file_search_results: Annotated[list[str], operator.add]  # Direct file search results

    # Dependency analysis
    dependencies: list[dict]  # List of dependency relationships
    dependency_graph: dict  # Graph structure for visualization
    import_analysis: list[dict]  # Import statements analysis

    # Flow analysis
    data_flow: list[dict]  # Data flow paths
    control_flow: list[dict]  # Control flow paths
    variable_usage: list[dict]  # Variable definitions and usages
    function_calls: list[dict]  # Function call hierarchy

    # Aggregated analysis (use Annotated for concurrent updates from parallel nodes)
    key_findings: Annotated[list[str], operator.add]  # Important discoveries
    related_files: Annotated[list[str], operator.add]  # Files involved in the investigation
    architecture_patterns: Annotated[
        list[str], operator.add
    ]  # Detected patterns (MVC, Factory, etc.)

    # Control flow
    loop_count: int  # Iteration counter
    needs_deeper_analysis: bool  # Whether to do another pass


def investigation_router(
    state: CodeInvestigationState,
) -> Literal["code_investigation_synthesizer", "code_retriever"]:
    """
    Router to decide if deeper investigation is needed.

    Max 2 iterations to keep response time reasonable.
    """
    loop_count = state.get("loop_count", 0)

    # Force exit after 2 iterations
    if loop_count >= 2:
        return "code_investigation_synthesizer"

    # Check if we have enough information
    dependencies = state.get("dependencies", [])
    key_findings = state.get("key_findings", [])
    code_results = state.get("code_results", [])

    # If we have good coverage, proceed to synthesis
    if len(key_findings) >= 3 or (len(dependencies) >= 5 and len(code_results) >= 3):
        return "code_investigation_synthesizer"

    # If first iteration and need more data
    if loop_count < 2 and state.get("needs_deeper_analysis", False):
        return "code_retriever"

    return "code_investigation_synthesizer"


class CodeInvestigationGraphBuilder(BaseGraphBuilder):
    """Builder for the Code Investigation workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return CodeInvestigationState

    def build(self) -> StateGraph:
        """Build and compile the Code Investigation workflow"""
        workflow = StateGraph(CodeInvestigationState)

        # Register all nodes
        workflow.add_node("code_query_analyzer", code_query_analyzer_node)
        workflow.add_node("code_retriever", code_retriever)
        workflow.add_node("dependency_analyzer", dependency_analyzer_node)
        workflow.add_node("code_flow_tracker", code_flow_tracker_node)
        workflow.add_node("code_investigation_synthesizer", code_investigation_synthesizer_node)

        # Set up workflow
        workflow.set_entry_point("code_query_analyzer")

        # Query analysis → Code retrieval
        workflow.add_edge("code_query_analyzer", "code_retriever")

        # Code retrieval → Parallel analysis
        workflow.add_edge("code_retriever", "dependency_analyzer")
        workflow.add_edge("code_retriever", "code_flow_tracker")

        # Both analysis nodes → Router for possible refinement
        workflow.add_edge("dependency_analyzer", "code_investigation_synthesizer")
        workflow.add_edge("code_flow_tracker", "code_investigation_synthesizer")

        # Note: For simplicity, we go directly to synthesizer
        # A more complex version could use conditional routing for refinement

        # Synthesis → END
        workflow.add_edge("code_investigation_synthesizer", END)

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(CodeInvestigationState)

        # Register nodes
        workflow.add_node("code_query_analyzer", code_query_analyzer_node)
        workflow.add_node("code_retriever", code_retriever)
        workflow.add_node("dependency_analyzer", dependency_analyzer_node)
        workflow.add_node("code_flow_tracker", code_flow_tracker_node)
        workflow.add_node("code_investigation_synthesizer", code_investigation_synthesizer_node)

        # Set up edges
        workflow.set_entry_point("code_query_analyzer")
        workflow.add_edge("code_query_analyzer", "code_retriever")
        workflow.add_edge("code_retriever", "dependency_analyzer")
        workflow.add_edge("code_retriever", "code_flow_tracker")
        workflow.add_edge("dependency_analyzer", "code_investigation_synthesizer")
        workflow.add_edge("code_flow_tracker", "code_investigation_synthesizer")
        workflow.add_edge("code_investigation_synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Code Investigation",
            "description": "Deep codebase analysis with dependency tracking and flow analysis",
            "version": "1.0",
            "use_cases": [
                "Understanding how a feature is implemented",
                "Finding all usages of a function or class",
                "Tracing dependencies between components",
                "Analyzing data flow through the codebase",
                "Architecture and design pattern analysis",
                "Refactoring impact assessment",
                "Code review and understanding",
            ],
            "complexity": "medium",
            "supports_streaming": True,
            "features": [
                "Intelligent query analysis for investigation scope",
                "Combined RAG + pattern-based code search",
                "Dependency graph generation",
                "Data and control flow tracking",
                "Variable and function usage analysis",
                "Architecture pattern detection",
                "Comprehensive investigation reports with code references",
            ],
            "performance": {"avg_execution_time": "45-90 seconds", "max_iterations": 2, "nodes": 5},
            "workflow": [
                "1. Code Query Analyzer - Understand investigation scope and targets",
                "2. Code Retriever - Retrieve relevant code via RAG",
                "3. Dependency Analyzer - Track class/function dependencies (parallel)",
                "4. Code Flow Tracker - Analyze data/control flow (parallel)",
                "5. Code Investigation Synthesizer - Generate comprehensive report",
            ],
        }
