"""
Schemas for the Feature Development workflow.

This module defines the state and data structures used in the
feature development multi-agent workflow.
"""

import operator
from typing import Annotated, Literal, TypedDict


class ExplorationResult(TypedDict):
    """Result from a single code exploration agent."""

    agent_id: str  # e.g., "explorer-1", "explorer-2"
    focus_area: str  # What this agent was exploring
    key_files: list[str]  # Important files discovered
    patterns: str  # Architectural patterns found
    findings: str  # Detailed findings


class ArchitectureProposal(TypedDict):
    """A single architecture design proposal."""

    approach_name: str  # e.g., "Minimal Changes", "Clean Architecture"
    description: str  # What this approach entails
    pros: list[str]  # Advantages
    cons: list[str]  # Disadvantages
    files_to_create: list[str]  # New files needed
    files_to_modify: list[str]  # Existing files to modify
    implementation_steps: list[str]  # High-level steps
    complexity_score: int  # 1-10 scale


class ReviewFinding(TypedDict):
    """A single code review finding."""

    severity: Literal["critical", "important", "minor"]  # Issue severity
    confidence: int  # 0-100 confidence score
    category: str  # e.g., "bug", "security", "quality", "convention"
    file_path: str  # File with the issue
    line_number: int  # Line number (0 if unknown)
    description: str  # What the issue is
    recommendation: str  # How to fix it


class FeatureDevState(TypedDict):
    """State for the feature development workflow."""

    # ===== Input =====
    feature_request: str  # Original user request

    # ===== Phase 1: Discovery =====
    clarified_requirements: str  # Clarified feature description
    feature_scope: str  # Scope and boundaries
    constraints: str  # Known constraints

    # ===== Phase 2: Codebase Exploration =====
    exploration_results: Annotated[list[ExplorationResult], operator.add]
    similar_features: list[str]  # References to similar existing features
    relevant_files: list[str]  # All files identified as relevant
    codebase_patterns: str  # Summary of patterns found

    # ===== Phase 3: Clarifying Questions =====
    questions: list[str]  # Questions for the user
    user_answers: str  # User's answers (blocks until provided)
    awaiting_user_input: bool  # Flag for blocking

    # ===== Phase 4: Architecture Design =====
    architecture_proposals: list[ArchitectureProposal]
    chosen_architecture: ArchitectureProposal | None  # User's choice
    architecture_decision: str  # Why this architecture was chosen

    # ===== Phase 5: Implementation =====
    implementation_approved: bool  # User approval to proceed
    implementation_plan: str  # Detailed implementation plan
    files_created: list[str]  # Files created during implementation
    files_modified: list[str]  # Files modified during implementation
    implementation_log: Annotated[list[str], operator.add]  # Progress log

    # ===== Phase 6: Quality Review =====
    review_findings: Annotated[list[ReviewFinding], operator.add]
    critical_issues: list[ReviewFinding]  # Filtered critical issues
    review_approved: bool  # Whether to fix issues or proceed

    # ===== Phase 7: Summary =====
    summary: str  # Final summary document
    next_steps: list[str]  # Suggested next steps

    # ===== Workflow Control =====
    current_phase: Literal[
        "discovery",
        "exploration",
        "clarification",
        "architecture",
        "implementation",
        "review",
        "summary",
        "complete",
    ]
    phase_history: Annotated[list[str], operator.add]  # Track phase transitions
