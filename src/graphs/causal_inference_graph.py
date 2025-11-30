"""
Causal Inference Graph - Root Cause Analysis and Causal Reasoning Workflow

This graph implements a specialized workflow for root cause analysis:
- Issue analysis and symptom extraction
- Hypothesis generation through brainstorming
- Evidence gathering from RAG and web sources
- Causal relationship validation
- Hypothesis ranking by likelihood
- Causal graph visualization
- Comprehensive root cause analysis report

Use cases:
- Troubleshooting technical issues
- Root cause analysis for incidents
- Understanding causal relationships
- Problem diagnosis and investigation
- System failure analysis
"""

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from src.nodes.brainstormer_node import brainstormer_node
from src.nodes.causal_checker_node import causal_checker_node
from src.nodes.causal_graph_builder_node import causal_graph_builder_node
from src.nodes.evidence_planner_node import evidence_planner_node
from src.nodes.hypothesis_validator_node import hypothesis_validator_node

# Import nodes
from src.nodes.issue_analyzer_node import issue_analyzer_node
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.root_cause_synthesizer_node import root_cause_synthesizer_node
from src.nodes.searcher_node import searcher

from .base_graph import BaseGraphBuilder


class CausalInferenceState(TypedDict):
    """State schema for causal inference workflow"""

    # Core fields
    query: str  # Original problem/issue statement
    report: str  # Final root cause analysis report

    # Issue analysis
    issue_summary: str  # Summary of the issue
    symptoms: list[str]  # Observable symptoms/effects
    context: str  # Background and context
    scope: str  # Scope of the issue

    # Hypothesis generation
    hypotheses: list[dict]  # Root cause hypotheses (list of RootCauseHypothesis dicts)
    brainstorming_approach: str  # Methodology used for brainstorming

    # Evidence gathering (strategic allocation)
    web_queries: list[str]  # Queries for web search
    rag_queries: list[str]  # Queries for knowledge base
    allocation_strategy: str  # Strategy reasoning
    search_results: Annotated[list[str], operator.add]  # Web search results (cumulative)
    rag_results: Annotated[list[str], operator.add]  # RAG results (cumulative)

    # Causal analysis
    causal_relationships: list[
        dict
    ]  # Validated causal relationships (list of CausalRelationship dicts)
    causal_analysis_approach: str  # Analysis methodology

    # Hypothesis ranking
    ranked_hypotheses: list[
        dict
    ]  # Hypotheses ranked by likelihood (list of RankedHypothesis dicts)
    ranking_methodology: str  # Ranking methodology
    overall_assessment: str  # Overall confidence assessment

    # Causal graph
    causal_graph_data: dict  # Graph structure for visualization

    # Control flow
    loop_count: int  # Iteration counter for refinement
    needs_more_evidence: bool  # Whether more evidence gathering is needed


def evidence_router(
    state: CausalInferenceState,
) -> Literal["causal_graph_builder", "evidence_planner"]:
    """
    Router to decide if more evidence is needed or proceed to graph building.

    Max 2 evidence gathering iterations to keep response time reasonable.
    """
    loop_count = state.get("loop_count", 0)

    # Force exit after 2 iterations
    if loop_count >= 2:
        return "causal_graph_builder"

    # Check if we have enough evidence for all hypotheses
    causal_relationships = state.get("causal_relationships", [])
    hypotheses = state.get("hypotheses", [])

    # Count hypotheses with strong or weak evidence
    strong_evidence_count = sum(
        1
        for rel in causal_relationships
        if rel["relationship_type"] in ["direct_cause", "contributing_factor"]
    )

    # If we have strong evidence for at least half the hypotheses, proceed
    if len(hypotheses) > 0 and strong_evidence_count >= len(hypotheses) * 0.5:
        return "causal_graph_builder"

    # Otherwise, gather more evidence (if not at max iterations)
    if loop_count < 2:
        return "evidence_planner"

    # Default: proceed to graph building
    return "causal_graph_builder"


class CausalInferenceGraphBuilder(BaseGraphBuilder):
    """Builder for the Causal Inference workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return CausalInferenceState

    def build(self) -> Any:
        """Build and compile the Causal Inference workflow"""
        workflow = StateGraph(CausalInferenceState)

        # Register all nodes
        workflow.add_node("issue_analyzer", issue_analyzer_node)  # type: ignore[type-var]
        workflow.add_node("brainstormer", brainstormer_node)  # type: ignore[type-var]
        workflow.add_node("evidence_planner", evidence_planner_node)  # type: ignore[type-var]
        workflow.add_node("searcher", searcher)  # type: ignore[type-var]
        workflow.add_node("rag_retriever", rag_retriever)  # type: ignore[type-var]
        workflow.add_node("causal_checker", causal_checker_node)  # type: ignore[type-var]
        workflow.add_node("hypothesis_validator", hypothesis_validator_node)  # type: ignore[type-var]
        workflow.add_node("causal_graph_builder", causal_graph_builder_node)  # type: ignore[type-var]
        workflow.add_node("root_cause_synthesizer", root_cause_synthesizer_node)  # type: ignore[type-var]

        # Set up workflow
        workflow.set_entry_point("issue_analyzer")

        # Linear flow: issue analysis → brainstorming → evidence planning
        workflow.add_edge("issue_analyzer", "brainstormer")
        workflow.add_edge("brainstormer", "evidence_planner")

        # Evidence gathering (parallel)
        workflow.add_edge("evidence_planner", "searcher")
        workflow.add_edge("evidence_planner", "rag_retriever")

        # Both evidence nodes → causal checker
        workflow.add_edge("searcher", "causal_checker")
        workflow.add_edge("rag_retriever", "causal_checker")

        # Causal analysis → hypothesis validation
        workflow.add_edge("causal_checker", "hypothesis_validator")

        # Router: more evidence needed or proceed to graph building?
        workflow.add_conditional_edges(
            "hypothesis_validator",
            evidence_router,
            {
                "evidence_planner": "evidence_planner",  # Gather more evidence
                "causal_graph_builder": "causal_graph_builder",  # Proceed to visualization
            },
        )

        # Graph building → synthesis
        workflow.add_edge("causal_graph_builder", "root_cause_synthesizer")

        # Synthesis → END
        workflow.add_edge("root_cause_synthesizer", END)

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> Any:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(CausalInferenceState)

        # Register nodes
        workflow.add_node("issue_analyzer", issue_analyzer_node)  # type: ignore[type-var]
        workflow.add_node("brainstormer", brainstormer_node)  # type: ignore[type-var]
        workflow.add_node("evidence_planner", evidence_planner_node)  # type: ignore[type-var]
        workflow.add_node("searcher", searcher)  # type: ignore[type-var]
        workflow.add_node("rag_retriever", rag_retriever)  # type: ignore[type-var]
        workflow.add_node("causal_checker", causal_checker_node)  # type: ignore[type-var]
        workflow.add_node("hypothesis_validator", hypothesis_validator_node)  # type: ignore[type-var]
        workflow.add_node("causal_graph_builder", causal_graph_builder_node)  # type: ignore[type-var]
        workflow.add_node("root_cause_synthesizer", root_cause_synthesizer_node)  # type: ignore[type-var]

        # Set up edges
        workflow.set_entry_point("issue_analyzer")
        workflow.add_edge("issue_analyzer", "brainstormer")
        workflow.add_edge("brainstormer", "evidence_planner")
        workflow.add_edge("evidence_planner", "searcher")
        workflow.add_edge("evidence_planner", "rag_retriever")
        workflow.add_edge("searcher", "causal_checker")
        workflow.add_edge("rag_retriever", "causal_checker")
        workflow.add_edge("causal_checker", "hypothesis_validator")
        workflow.add_conditional_edges(
            "hypothesis_validator",
            evidence_router,
            {
                "evidence_planner": "evidence_planner",
                "causal_graph_builder": "causal_graph_builder",
            },
        )
        workflow.add_edge("causal_graph_builder", "root_cause_synthesizer")
        workflow.add_edge("root_cause_synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Causal Inference",
            "description": "Root cause analysis with causal reasoning and hypothesis ranking",
            "version": "1.0",
            "use_cases": [
                "Root cause analysis for technical issues",
                "System failure diagnosis",
                "Incident investigation and troubleshooting",
                "Understanding causal relationships",
                "Problem diagnosis with evidence validation",
                "Hypothesis-driven investigation",
            ],
            "complexity": "medium",
            "supports_streaming": True,
            "features": [
                "Systematic issue analysis and symptom extraction",
                "Diverse hypothesis generation (brainstorming)",
                "Strategic evidence gathering (RAG + Web)",
                "Rigorous causal relationship validation",
                "Probability-based hypothesis ranking",
                "Causal graph visualization data",
                "Comprehensive root cause analysis reports",
                "Iterative evidence refinement (max 2 iterations)",
            ],
            "performance": {"avg_execution_time": "60-90 seconds", "max_iterations": 2, "nodes": 9},
            "workflow": [
                "1. Issue Analyzer - Extract symptoms and context",
                "2. Brainstormer - Generate root cause hypotheses",
                "3. Evidence Planner - Plan strategic queries (RAG + Web)",
                "4. Searcher + RAG Retriever - Gather evidence (parallel)",
                "5. Causal Checker - Validate causal relationships",
                "6. Hypothesis Validator - Rank by likelihood",
                "7. Router - More evidence needed? (max 2 iterations)",
                "8. Causal Graph Builder - Create visualization data",
                "9. Root Cause Synthesizer - Generate comprehensive report",
            ],
        }
