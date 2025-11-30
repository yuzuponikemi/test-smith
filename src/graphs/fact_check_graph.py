"""
Fact Check Graph - Claim Verification Workflow

This graph implements a specialized workflow for verifying claims and statements:
- Extract specific claims from the query
- Search both KB and web for supporting/contradicting evidence
- Cross-reference multiple sources
- Provide confidence assessment with citations

Use cases:
- Verify factual claims
- Check statement accuracy
- Cross-reference information across sources
- Detect contradictions or inconsistencies
- Provide evidence-based assessments
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from src.nodes.analyzer_node import analyzer_node

# Import reusable nodes
from src.nodes.planner_node import planner
from src.nodes.rag_retriever_node import rag_retriever
from src.nodes.searcher_node import searcher
from src.nodes.synthesizer_node import synthesizer_node

from .base_graph import BaseGraphBuilder


class FactCheckState(TypedDict):
    """State for fact checking workflow"""

    # Core fields
    query: str  # The claim or statement to verify
    report: str  # Final verification report with confidence assessment

    # Query allocation
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str

    # Results accumulation
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]

    # Fact-checking specific fields
    claims_extracted: list[str]  # Individual claims to verify
    evidence_for: Annotated[list[str], operator.add]  # Supporting evidence
    evidence_against: Annotated[list[str], operator.add]  # Contradicting evidence
    confidence_score: float  # 0.0-1.0 confidence in the claim


class FactCheckGraphBuilder(BaseGraphBuilder):
    """Builder for the Fact Check verification workflow"""

    def get_state_class(self) -> type:
        """Return the state class for this graph"""
        return FactCheckState

    def build(self) -> StateGraph:
        """Build and compile the Fact Check workflow"""
        workflow = StateGraph(FactCheckState)

        # Register nodes (reusing existing nodes!)
        # Note: In a real implementation, you might want specialized nodes
        # for claim extraction and evidence analysis, but we reuse existing ones
        # to demonstrate the architecture
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up fact-checking flow
        # 1. Planner extracts claims and plans verification queries
        workflow.set_entry_point("planner")

        # 2. Parallel search for evidence
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")

        # 3. Analyze evidence (categorize as supporting/contradicting)
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")

        # 4. Synthesize final verification report
        # The synthesizer will be configured (via prompts) to:
        # - Assess confidence based on evidence quality
        # - Identify contradictions
        # - Provide citations
        workflow.add_edge("analyzer", "synthesizer")

        # 5. End
        workflow.add_edge("synthesizer", END)

        # Compile and return
        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """Return uncompiled graph for custom checkpointer setup"""
        workflow = StateGraph(FactCheckState)

        # Register nodes
        workflow.add_node("planner", planner)
        workflow.add_node("searcher", searcher)
        workflow.add_node("rag_retriever", rag_retriever)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Set up edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("planner", "rag_retriever")
        workflow.add_edge("searcher", "analyzer")
        workflow.add_edge("rag_retriever", "analyzer")
        workflow.add_edge("analyzer", "synthesizer")
        workflow.add_edge("synthesizer", END)

        # Return uncompiled
        return workflow

    def get_metadata(self) -> dict:
        """Return metadata about this graph"""
        return {
            "name": "Fact Check",
            "description": "Claim verification workflow with evidence analysis",
            "version": "1.0",
            "use_cases": [
                "Verify factual claims",
                "Check statement accuracy",
                "Cross-reference information across sources",
                "Detect contradictions or inconsistencies",
                "Provide evidence-based assessments with citations",
            ],
            "complexity": "medium",
            "supports_streaming": True,
            "features": [
                "Claim extraction and decomposition",
                "Multi-source evidence gathering (KB + Web)",
                "Evidence categorization (supporting/contradicting)",
                "Confidence scoring (0.0-1.0)",
                "Citation tracking",
                "Contradiction detection",
                "Single-pass execution for speed",
            ],
            "output_format": {
                "sections": [
                    "Claim summary",
                    "Supporting evidence with citations",
                    "Contradicting evidence with citations",
                    "Confidence assessment",
                    "Limitations and caveats",
                ]
            },
            "performance": {"avg_execution_time": "30-45 seconds", "max_iterations": 1, "nodes": 5},
        }
