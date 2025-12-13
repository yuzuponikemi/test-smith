"""
Writer Graph - Phase 2.5

Dedicated graph for long-form report writing.
Takes aggregated findings from Phase 1 and produces quality-validated final report.

Based on:
- GPT Researcher's multi-agent pipeline (Researcher → Editor → Reviewer → Revisor → Writer)
- Stanford STORM's outline-driven generation
- Anthropic's multi-layer quality control
"""

from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from src.graphs.base_graph import BaseGraphBuilder
from src.nodes.outline_generator_node import outline_generator_node
from src.nodes.report_reviewer_node import report_reviewer_node
from src.nodes.report_revisor_node import report_revisor_node
from src.nodes.section_writer_node import section_writer_node


class WriterGraphState(TypedDict):
    """
    State for the Writer Graph workflow.

    This graph takes aggregated research findings and produces a quality-validated report.
    """

    # Input from Phase 1 (Research Collection)
    query: str  # Original user query
    aggregated_findings: dict  # AggregatedFindings as dict
    findings_ready: bool  # Whether findings are ready for writing

    # Writing Phase state
    report_outline: dict  # ReportOutline as dict
    draft_report: str  # Current draft of the report
    section_word_counts: dict[str, int]  # Word counts per section
    total_word_count: int  # Total word count

    # Review/Revision state
    review_result: dict  # ReportReviewResult as dict
    needs_revision: bool  # Whether report needs revision
    revision_count: int  # Number of revisions performed

    # Final output
    report: str  # Final approved report


def _review_router(state: WriterGraphState) -> Literal["revisor", "finalize"]:
    """
    Route based on review result.

    If needs_revision is True and we haven't hit max revisions, go to revisor.
    Otherwise, finalize the report.
    """
    needs_revision = state.get("needs_revision", False)
    revision_count = state.get("revision_count", 0)

    # Max 3 revisions to prevent infinite loops
    if needs_revision and revision_count < 3:
        return "revisor"
    return "finalize"


def _finalize_node(state: WriterGraphState) -> dict:
    """
    Finalize the report by copying draft to final report field.
    """
    draft = state.get("draft_report", "")
    total_words = state.get("total_word_count", 0)

    print("\n" + "=" * 60)
    print("  FINALIZING REPORT")
    print("=" * 60)
    print(f"  Final word count: {total_words}")
    print(f"  Revisions performed: {state.get('revision_count', 0)}")
    print("=" * 60 + "\n")

    return {"report": draft}


class WriterGraphBuilder(BaseGraphBuilder):
    """
    Builder for the Writer Graph workflow.

    This graph implements Phase 2 of the Long Report Generation system:
    1. Outline Generator - Creates structured outline from findings
    2. Section Writer - Writes each section based on outline
    3. Reviewer - Evaluates report quality
    4. Revisor - Improves report based on feedback (up to 3 iterations)
    5. Finalize - Produces final report

    The workflow supports iterative improvement through the review-revise loop.
    """

    def get_state_class(self) -> type:
        """Return the state class for this graph."""
        return WriterGraphState

    def build(self) -> Any:  # type: ignore[override]
        """
        Build and compile the Writer Graph workflow.

        Returns:
            Compiled StateGraph ready for execution
        """
        workflow = StateGraph(WriterGraphState)

        # Register nodes
        workflow.add_node("outline_generator", outline_generator_node)  # type: ignore[type-var]
        workflow.add_node("section_writer", section_writer_node)  # type: ignore[type-var]
        workflow.add_node("reviewer", report_reviewer_node)  # type: ignore[type-var]
        workflow.add_node("revisor", report_revisor_node)  # type: ignore[type-var]
        workflow.add_node("finalize", _finalize_node)

        # Set entry point
        workflow.set_entry_point("outline_generator")

        # Define edges
        # Linear flow: outline → write → review
        workflow.add_edge("outline_generator", "section_writer")
        workflow.add_edge("section_writer", "reviewer")

        # Conditional: review → revise or finalize
        workflow.add_conditional_edges(
            "reviewer",
            _review_router,
            {
                "revisor": "revisor",
                "finalize": "finalize",
            },
        )

        # Revise → review again
        workflow.add_edge("revisor", "reviewer")

        # Finalize → END
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def get_uncompiled_graph(self) -> StateGraph:
        """
        Return the uncompiled StateGraph for external compilation.

        Useful for applying custom checkpointers or configuration.

        Returns:
            Uncompiled StateGraph instance
        """
        workflow = StateGraph(WriterGraphState)

        # Register nodes
        workflow.add_node("outline_generator", outline_generator_node)  # type: ignore[type-var]
        workflow.add_node("section_writer", section_writer_node)  # type: ignore[type-var]
        workflow.add_node("reviewer", report_reviewer_node)  # type: ignore[type-var]
        workflow.add_node("revisor", report_revisor_node)  # type: ignore[type-var]
        workflow.add_node("finalize", _finalize_node)

        # Set entry point
        workflow.set_entry_point("outline_generator")

        # Define edges
        workflow.add_edge("outline_generator", "section_writer")
        workflow.add_edge("section_writer", "reviewer")

        workflow.add_conditional_edges(
            "reviewer",
            _review_router,
            {
                "revisor": "revisor",
                "finalize": "finalize",
            },
        )

        workflow.add_edge("revisor", "reviewer")
        workflow.add_edge("finalize", END)

        return workflow

    def get_metadata(self) -> dict:
        """
        Return metadata about this graph workflow.

        Returns:
            Dictionary with graph metadata
        """
        return {
            "name": "Writer Graph",
            "description": "Dedicated graph for long-form report writing with quality validation",
            "use_cases": [
                "Long-form report generation from research findings",
                "Multi-section document creation",
                "Quality-controlled content generation",
                "Iterative report improvement",
            ],
            "complexity": "medium",
            "average_time": "60-180 seconds",
            "supports_streaming": True,
            "features": [
                "Outline-driven generation (Stanford STORM approach)",
                "Section-by-section writing for focused content",
                "Multi-layer quality control (Anthropic approach)",
                "Automatic revision loop (up to 3 iterations)",
                "Language consistency enforcement",
                "Word count targeting",
            ],
            "phases": {
                "1": "Outline Generation - Create structured outline from findings",
                "2": "Section Writing - Write each section independently",
                "3": "Review - Evaluate against quality criteria",
                "4": "Revision - Improve based on feedback (iterative)",
                "5": "Finalization - Produce final report",
            },
            "input_requirements": {
                "aggregated_findings": "Required - Output from Phase 1 Result Aggregator",
                "findings_ready": "Required - Boolean indicating findings quality",
            },
            "output": {
                "report": "Final quality-validated report in Markdown format",
                "report_outline": "Structured outline used for generation",
                "review_result": "Final review assessment",
                "total_word_count": "Actual word count achieved",
            },
        }
