"""
Feature Development Graph

A 7-phase workflow for systematic feature development, inspired by
Claude Code's feature-dev plugin.

Phases:
1. Discovery: Clarify requirements
2. Exploration: Parallel codebase analysis (2 agents)
3. Clarification: Generate questions (blocks if needed)
4. Architecture: Design proposals (3 parallel approaches)
5. Implementation: Build feature (blocks for approval)
6. Review: Quality checks (3 parallel reviewers)
7. Summary: Documentation generation
"""

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from src.graphs.base_graph import BaseGraphBuilder
from src.nodes.feature_dev import (
    architecture_designer_node,
    codebase_explorer_node,
    discovery_node,
    feature_implementer_node,
    feature_summarizer_node,
    quality_reviewer_node,
    question_clarifier_node,
)
from src.feature_dev_schemas import FeatureDevState

logger = logging.getLogger(__name__)


class FeatureDevGraphBuilder(BaseGraphBuilder):
    """Builder for the Feature Development workflow graph."""

    def get_state_class(self) -> type:
        """Return the state class for this graph."""
        return FeatureDevState

    def build(self) -> StateGraph:
        """Build and compile the feature development workflow graph."""
        logger.info("Building Feature Development graph...")

        # Create workflow
        workflow = StateGraph(FeatureDevState)

        # ===== Add Nodes =====
        workflow.add_node("discovery", discovery_node)
        workflow.add_node("exploration", codebase_explorer_node)
        workflow.add_node("clarification", question_clarifier_node)
        workflow.add_node("architecture", architecture_designer_node)
        workflow.add_node("implementation", feature_implementer_node)
        workflow.add_node("review", quality_reviewer_node)
        workflow.add_node("summary", feature_summarizer_node)

        # ===== Add Edges =====

        # Phase 1 → Phase 2
        workflow.add_edge("discovery", "exploration")

        # Phase 2 → Phase 3
        workflow.add_edge("exploration", "clarification")

        # Phase 3 → Router (check if questions need answers)
        workflow.add_conditional_edges(
            "clarification",
            self._clarification_router,
            {
                "wait_for_user": END,  # Block and wait for user input
                "architecture": "architecture",  # No questions, proceed
            },
        )

        # Phase 4 → Router (check if user chose architecture)
        workflow.add_conditional_edges(
            "architecture",
            self._architecture_router,
            {
                "wait_for_choice": END,  # Block and wait for user to choose
                "implementation": "implementation",  # Choice made, proceed
            },
        )

        # Phase 5 → Phase 6 (always proceed to review)
        workflow.add_edge("implementation", "review")

        # Phase 6 → Router (check if user approved or wants fixes)
        workflow.add_conditional_edges(
            "review",
            self._review_router,
            {
                "wait_for_approval": END,  # Block and wait for user decision
                "summary": "summary",  # Approved, generate summary
            },
        )

        # Phase 7 → END
        workflow.add_edge("summary", END)

        # Set entry point
        workflow.set_entry_point("discovery")

        logger.info("Feature Development graph built successfully")

        return workflow.compile()

    def get_metadata(self) -> dict:
        """Return metadata about this graph."""
        return {
            "name": "feature_dev",
            "display_name": "Feature Development",
            "description": "Systematic 7-phase workflow for building new features",
            "complexity": "High",
            "avg_time": "10-20 minutes",
            "best_for": [
                "Building new features",
                "Adding significant functionality",
                "Complex implementations requiring planning",
            ],
            "phases": [
                "Discovery",
                "Exploration",
                "Clarification",
                "Architecture",
                "Implementation",
                "Review",
                "Summary",
            ],
            "user_interaction": "High - multiple approval gates",
            "parallel_agents": True,
        }

    # ===== Router Functions =====

    def _clarification_router(
        self, state: dict
    ) -> Literal["wait_for_user", "architecture"]:
        """
        Route after clarification phase.

        If questions exist and not answered, wait for user.
        Otherwise, proceed to architecture.
        """
        questions = state.get("questions", [])
        user_answers = state.get("user_answers", "")

        if questions and not user_answers:
            logger.info("⏸️  Waiting for user to answer clarifying questions")
            return "wait_for_user"

        logger.info("✓ Proceeding to architecture design")
        return "architecture"

    def _architecture_router(
        self, state: dict
    ) -> Literal["wait_for_choice", "implementation"]:
        """
        Route after architecture phase.

        If no architecture chosen, wait for user.
        Otherwise, proceed to implementation.
        """
        chosen_arch = state.get("chosen_architecture")

        if not chosen_arch:
            logger.info("⏸️  Waiting for user to choose architecture")
            return "wait_for_choice"

        logger.info("✓ Architecture chosen, proceeding to implementation")
        return "implementation"

    def _review_router(
        self, state: dict
    ) -> Literal["wait_for_approval", "summary"]:
        """
        Route after review phase.

        If critical issues found and not approved, wait for user.
        Otherwise, proceed to summary.
        """
        review_approved = state.get("review_approved", False)
        critical_issues = state.get("critical_issues", [])

        if critical_issues and not review_approved:
            logger.info("⏸️  Waiting for user decision on critical issues")
            return "wait_for_approval"

        logger.info("✓ Review complete, generating summary")
        return "summary"
