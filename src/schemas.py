from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Plan(BaseModel):
    """A plan to answer the user's query."""
    queries: List[str] = Field(description="A list of search queries to answer the user's query.")

class StrategicPlan(BaseModel):
    """Strategic plan with intelligent query allocation between RAG and web sources."""

    rag_queries: List[str] = Field(
        description="Queries for knowledge base retrieval (domain-specific content, internal documentation, established concepts)"
    )
    web_queries: List[str] = Field(
        description="Queries for web search (recent events, current trends, general information, external sources)"
    )
    strategy: str = Field(
        description="Reasoning for this allocation: What information is likely in KB vs needs web? Why this distribution?"
    )

class Evaluation(BaseModel):
    """An evaluation of the sufficiency of the information."""
    is_sufficient: bool = Field(description="Whether the information is sufficient to create a comprehensive report.")
    reason: str = Field(description="The reason for the evaluation.")

# === Hierarchical Task Decomposition Schemas (Phase 1) ===

class SubTask(BaseModel):
    """
    Represents a single subtask in hierarchical decomposition.

    Used in Phase 1 (v2.0-alpha) for basic task decomposition.
    Enhanced in Phase 2 (v2.0-beta) with depth tracking for recursive drill-down.
    """
    subtask_id: str = Field(
        description="Unique identifier for this subtask (e.g., 'task_1', 'task_1.1', 'task_2.3.1')"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="ID of parent subtask (None for root-level tasks, e.g., 'task_1' for 'task_1.1')"
    )
    depth: int = Field(
        default=0,
        description="Hierarchical depth level: 0 = root, 1 = first drill-down, 2 = second drill-down, etc.",
        ge=0
    )
    description: str = Field(
        description="Clear description of what this subtask should accomplish"
    )
    focus_area: str = Field(
        description="Specific aspect or domain this subtask covers"
    )
    priority: int = Field(
        description="Execution order, starting from 1 (1 = first to execute)",
        ge=1
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of subtask_ids that must complete before this subtask can start"
    )
    estimated_importance: float = Field(
        ge=0.0,
        le=1.0,
        description="Importance score (0.0-1.0) for resource allocation and prioritization"
    )

class MasterPlan(BaseModel):
    """
    Master plan with complexity detection and task decomposition.

    Determines whether a query is simple (single-pass research) or complex
    (requires hierarchical decomposition into subtasks).
    """
    is_complex: bool = Field(
        description="Whether the query requires hierarchical decomposition into subtasks"
    )
    complexity_reasoning: str = Field(
        description="Explanation of why the query is classified as simple or complex"
    )
    execution_mode: Literal["simple", "hierarchical"] = Field(
        description="Execution mode: 'simple' uses existing single-pass flow, "
                    "'hierarchical' decomposes into subtasks"
    )
    subtasks: List[SubTask] = Field(
        default_factory=list,
        description="List of subtasks for hierarchical execution (empty if simple mode)"
    )
    overall_strategy: str = Field(
        description="High-level strategy for addressing the user's query"
    )

# === Hierarchical Task Decomposition Schemas (Phase 2) ===

class DepthEvaluation(BaseModel):
    """
    Evaluation of subtask result depth and quality.

    Used in Phase 2 (v2.0-beta) to determine if a subtask needs deeper exploration
    through drill-down into child subtasks.
    """
    is_sufficient: bool = Field(
        description="Whether the subtask has been explored sufficiently for its importance level"
    )
    depth_quality: Literal["superficial", "adequate", "deep"] = Field(
        description="Assessment of information depth: "
                    "'superficial' = general statements only, lacks detail; "
                    "'adequate' = specific facts with context; "
                    "'deep' = rich detail, multiple perspectives, well-sourced"
    )
    drill_down_needed: bool = Field(
        description="Whether this subtask should spawn child subtasks for deeper exploration"
    )
    drill_down_areas: List[str] = Field(
        default_factory=list,
        description="Specific areas or aspects that need deeper investigation (for child subtasks)"
    )
    reasoning: str = Field(
        description="Detailed explanation of the depth assessment and drill-down decision"
    )

# === Hierarchical Task Decomposition Schemas (Phase 4) ===

class PlanRevision(BaseModel):
    """
    Revision decision for Master Plan based on subtask execution findings.

    Used in Phase 4 (v2.1) to enable adaptive research that responds to discoveries
    during execution. Analyzes subtask results and determines if the Master Plan
    should be updated to add new subtasks, adjust priorities, or change scope.
    """
    should_revise: bool = Field(
        description="Whether the Master Plan should be revised based on current findings"
    )
    revision_reasoning: str = Field(
        description="Detailed explanation of why revision is or isn't needed"
    )
    trigger_type: Literal["new_topic", "scope_adjustment", "contradiction", "importance_shift", "none"] = Field(
        description="Type of trigger for revision: "
                    "'new_topic' = important related topic discovered not in original plan; "
                    "'scope_adjustment' = current scope too narrow/broad; "
                    "'contradiction' = conflicting information needs resolution; "
                    "'importance_shift' = unexpected importance of certain aspects; "
                    "'none' = no revision needed"
    )
    new_subtasks: List[SubTask] = Field(
        default_factory=list,
        description="New subtasks to add to the Master Plan (if revision needed)"
    )
    removed_subtasks: List[str] = Field(
        default_factory=list,
        description="Subtask IDs to skip/remove from execution (if revision needed)"
    )
    priority_changes: dict = Field(
        default_factory=dict,
        description="Priority changes for existing subtasks: subtask_id → new_priority (if revision needed)"
    )
    estimated_impact: str = Field(
        description="How this revision will improve the final report quality"
    )

# === Reflection & Self-Critique Schemas ===

class CritiquePoint(BaseModel):
    """
    A single critique point identified during reflection.

    Used to identify specific issues in research findings that need attention
    before synthesis.
    """
    category: Literal[
        "logical_fallacy",
        "contradiction",
        "missing_evidence",
        "bias_detected",
        "source_credibility",
        "alternative_perspective",
        "incomplete_coverage",
        "other"
    ] = Field(
        description="Category of the critique point"
    )
    severity: Literal["critical", "moderate", "minor"] = Field(
        description="Severity level: 'critical' = must fix before synthesis, "
                    "'moderate' = should address if possible, "
                    "'minor' = note for improvement"
    )
    description: str = Field(
        description="Clear description of the issue identified"
    )
    location: str = Field(
        description="Where in the analyzed data this issue appears (e.g., 'subtask_2', 'web results', 'overall')"
    )
    recommendation: str = Field(
        description="Specific recommendation for addressing this issue"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this critique (0.0-1.0)"
    )

class ReflectionCritique(BaseModel):
    """
    Meta-reasoning analysis of research findings before synthesis.

    Provides critical review of information quality, identifies gaps,
    contradictions, biases, and suggests improvements to ensure
    high-quality, trustworthy research output.
    """
    overall_quality: Literal["excellent", "good", "adequate", "poor"] = Field(
        description="Overall assessment of research findings quality"
    )
    quality_reasoning: str = Field(
        description="Detailed explanation of the overall quality assessment"
    )
    critique_points: List[CritiquePoint] = Field(
        default_factory=list,
        description="Specific issues identified in the research findings"
    )
    missing_perspectives: List[str] = Field(
        default_factory=list,
        description="Important perspectives or viewpoints that are missing from the research"
    )
    contradictions: List[str] = Field(
        default_factory=list,
        description="Contradictions or conflicts found in the research data"
    )
    bias_indicators: List[str] = Field(
        default_factory=list,
        description="Potential biases detected in sources or analysis"
    )
    evidence_strength: Literal["strong", "moderate", "weak"] = Field(
        description="Overall strength of evidence supporting conclusions"
    )
    should_continue_research: bool = Field(
        description="Whether additional research iteration is needed to address critical gaps"
    )
    continuation_reasoning: str = Field(
        description="Explanation for whether to continue research or proceed to synthesis"
    )
    synthesis_recommendations: List[str] = Field(
        default_factory=list,
        description="Specific recommendations for the synthesis phase to address identified issues"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence in the research findings (0.0-1.0)"
    )
