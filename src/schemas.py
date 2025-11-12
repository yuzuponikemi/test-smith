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
    """
    subtask_id: str = Field(
        description="Unique identifier for this subtask (e.g., 'task_1', 'task_2')"
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
