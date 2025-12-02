from typing import Literal, Optional

from pydantic import BaseModel, Field


class Plan(BaseModel):
    """A plan to answer the user's query."""

    queries: list[str] = Field(description="A list of search queries to answer the user's query.")


class StrategicPlan(BaseModel):
    """Strategic plan with intelligent query allocation between RAG and web sources."""

    rag_queries: list[str] = Field(
        description="Queries for knowledge base retrieval (domain-specific content, internal documentation, established concepts)"
    )
    web_queries: list[str] = Field(
        description="Queries for web search (recent events, current trends, general information, external sources)"
    )
    strategy: str = Field(
        description="Reasoning for this allocation: What information is likely in KB vs needs web? Why this distribution?"
    )


class Evaluation(BaseModel):
    """An evaluation of the sufficiency of the information."""

    is_sufficient: bool = Field(
        description="Whether the information is sufficient to create a comprehensive report."
    )
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
        description="ID of parent subtask (None for root-level tasks, e.g., 'task_1' for 'task_1.1')",
    )
    depth: int = Field(
        default=0,
        description="Hierarchical depth level: 0 = root, 1 = first drill-down, 2 = second drill-down, etc.",
        ge=0,
    )
    description: str = Field(description="Clear description of what this subtask should accomplish")
    focus_area: str = Field(description="Specific aspect or domain this subtask covers")
    priority: int = Field(
        description="Execution order, starting from 1 (1 = first to execute)", ge=1
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of subtask_ids that must complete before this subtask can start",
    )
    estimated_importance: float = Field(
        ge=0.0,
        le=1.0,
        description="Importance score (0.0-1.0) for resource allocation and prioritization",
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
    subtasks: list[SubTask] = Field(
        default_factory=list,
        description="List of subtasks for hierarchical execution (empty if simple mode)",
    )
    overall_strategy: str = Field(description="High-level strategy for addressing the user's query")


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
    drill_down_areas: list[str] = Field(
        default_factory=list,
        description="Specific areas or aspects that need deeper investigation (for child subtasks)",
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
    trigger_type: Literal[
        "new_topic", "scope_adjustment", "contradiction", "importance_shift", "none"
    ] = Field(
        description="Type of trigger for revision: "
        "'new_topic' = important related topic discovered not in original plan; "
        "'scope_adjustment' = current scope too narrow/broad; "
        "'contradiction' = conflicting information needs resolution; "
        "'importance_shift' = unexpected importance of certain aspects; "
        "'none' = no revision needed"
    )
    new_subtasks: list[SubTask] = Field(
        default_factory=list,
        description="New subtasks to add to the Master Plan (if revision needed)",
    )
    removed_subtasks: list[str] = Field(
        default_factory=list,
        description="Subtask IDs to skip/remove from execution (if revision needed)",
    )
    priority_changes: dict = Field(
        default_factory=dict,
        description="Priority changes for existing subtasks: subtask_id → new_priority (if revision needed)",
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
        "other",
    ] = Field(description="Category of the critique point")
    severity: Literal["critical", "moderate", "minor"] = Field(
        description="Severity level: 'critical' = must fix before synthesis, "
        "'moderate' = should address if possible, "
        "'minor' = note for improvement"
    )
    description: str = Field(description="Clear description of the issue identified")
    location: str = Field(
        description="Where in the analyzed data this issue appears (e.g., 'subtask_2', 'web results', 'overall')"
    )
    recommendation: str = Field(description="Specific recommendation for addressing this issue")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this critique (0.0-1.0)")


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
    critique_points: list[CritiquePoint] = Field(
        default_factory=list, description="Specific issues identified in the research findings"
    )
    missing_perspectives: list[str] = Field(
        default_factory=list,
        description="Important perspectives or viewpoints that are missing from the research",
    )
    contradictions: list[str] = Field(
        default_factory=list, description="Contradictions or conflicts found in the research data"
    )
    bias_indicators: list[str] = Field(
        default_factory=list, description="Potential biases detected in sources or analysis"
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
    synthesis_recommendations: list[str] = Field(
        default_factory=list,
        description="Specific recommendations for the synthesis phase to address identified issues",
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in the research findings (0.0-1.0)"
    )


# === Causal Inference Schemas ===


class IssueAnalysis(BaseModel):
    """
    Analysis of the problem statement extracting key symptoms and context.

    Used to decompose an issue into observable effects and background information
    before generating causal hypotheses.
    """

    issue_summary: str = Field(description="Concise summary of the problem/issue being analyzed")
    symptoms: list[str] = Field(
        description="Observable symptoms, effects, or manifestations of the issue"
    )
    context: str = Field(
        description="Relevant background context, constraints, and environment details"
    )
    scope: str = Field(
        description="Scope of the issue: system/component affected, timeframe, conditions"
    )


class RootCauseHypothesis(BaseModel):
    """
    A potential root cause hypothesis for the observed issue.

    Generated during brainstorming phase before evidence gathering.
    """

    hypothesis_id: str = Field(
        description="Unique identifier for this hypothesis (e.g., 'H1', 'H2', 'H3')"
    )
    description: str = Field(description="Clear description of the hypothesized root cause")
    mechanism: str = Field(
        description="How this cause could produce the observed symptoms (causal mechanism)"
    )
    category: Literal["technical", "process", "human", "environmental", "design", "external"] = (
        Field(description="Category of root cause for organization")
    )
    initial_plausibility: float = Field(
        ge=0.0, le=1.0, description="Initial plausibility score (0.0-1.0) before evidence gathering"
    )


class HypothesisList(BaseModel):
    """List of root cause hypotheses generated during brainstorming."""

    hypotheses: list[RootCauseHypothesis] = Field(description="All generated root cause hypotheses")
    brainstorming_approach: str = Field(
        description="Explanation of the brainstorming methodology used"
    )


class CausalRelationship(BaseModel):
    """
    A validated causal relationship between a hypothesis and observed symptoms.

    Created after evidence gathering to assess causal links.
    """

    hypothesis_id: str = Field(description="ID of the hypothesis being evaluated")
    relationship_type: Literal[
        "direct_cause", "contributing_factor", "correlated", "unlikely", "refuted"
    ] = Field(
        description="Type of causal relationship: "
        "'direct_cause' = strong evidence of causation; "
        "'contributing_factor' = partial causation; "
        "'correlated' = association without clear causation; "
        "'unlikely' = weak or contradictory evidence; "
        "'refuted' = evidence disproves this cause"
    )
    supporting_evidence: list[str] = Field(
        description="Evidence supporting this causal relationship"
    )
    contradicting_evidence: list[str] = Field(
        default_factory=list, description="Evidence contradicting this causal relationship"
    )
    causal_strength: float = Field(
        ge=0.0, le=1.0, description="Strength of causal link based on evidence (0.0-1.0)"
    )
    reasoning: str = Field(description="Detailed reasoning for this causal assessment")


class CausalAnalysis(BaseModel):
    """Complete causal analysis with all validated relationships."""

    relationships: list[CausalRelationship] = Field(
        description="All evaluated causal relationships"
    )
    analysis_approach: str = Field(description="Methodology used for causal validation")


class RankedHypothesis(BaseModel):
    """
    A root cause hypothesis with final probability ranking.

    Generated after all evidence is gathered and analyzed.
    """

    hypothesis_id: str = Field(description="ID of the hypothesis")
    description: str = Field(description="Description of the root cause")
    likelihood: float = Field(
        ge=0.0, le=1.0, description="Final likelihood/probability (0.0-1.0) based on all evidence"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in this assessment based on evidence quality"
    )
    supporting_factors: list[str] = Field(description="Key factors supporting this root cause")
    mitigating_factors: list[str] = Field(
        default_factory=list,
        description="Factors reducing likelihood or providing alternative explanations",
    )
    recommendation: str = Field(
        description="Recommended action or investigation steps for this hypothesis"
    )


class HypothesisRanking(BaseModel):
    """Ranked list of root cause hypotheses with probabilities."""

    ranked_hypotheses: list[RankedHypothesis] = Field(
        description="Hypotheses ranked by likelihood (highest first)"
    )
    ranking_methodology: str = Field(description="Explanation of ranking methodology and criteria")
    overall_assessment: str = Field(description="Overall assessment of root cause certainty")


# === Code Execution Schemas ===


class CodeExecutionRequest(BaseModel):
    """
    Request for code execution with context and requirements.

    Used to generate and execute Python code for data analysis,
    calculations, or information processing during research.
    """

    task_description: str = Field(
        description="Clear description of what the code should accomplish"
    )
    context: str = Field(description="Relevant context from previous research steps")
    input_data: Optional[str] = Field(
        default=None,
        description="Input data or parameters for the code (JSON format if structured)",
    )
    requirements: list[str] = Field(
        default_factory=list, description="Specific requirements or constraints for the code"
    )
    expected_output: str = Field(description="Description of expected output format")


class CodeExecutionResult(BaseModel):
    """
    Result of code execution including output and metadata.

    Captures both successful execution results and errors
    for proper handling in the workflow.
    """

    success: bool = Field(description="Whether code execution succeeded")
    output: str = Field(description="Output from code execution (stdout or return value)")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    execution_time: float = Field(description="Execution time in seconds")
    code: str = Field(description="The actual code that was executed")


# === Code Assistant Schemas ===


class CodeReference(BaseModel):
    """
    A reference to a specific location in the codebase.
    """

    file_path: str = Field(description="Relative path to the file in the repository")
    line_number: Optional[int] = Field(
        default=None, description="Specific line number (if applicable)"
    )
    symbol_name: Optional[str] = Field(
        default=None, description="Name of function, class, or variable referenced"
    )
    context: str = Field(description="Brief description of what this code does")


class CodeAnalysis(BaseModel):
    """
    Analysis result from the code assistant.
    """

    answer: str = Field(description="Direct answer to the user's code question")
    references: list[CodeReference] = Field(
        default_factory=list, description="Code references supporting the answer"
    )
    related_files: list[str] = Field(
        default_factory=list, description="Additional related files the user might want to check"
    )
    code_snippets: list[str] = Field(
        default_factory=list,
        description="Relevant code snippets (formatted with language identifier)",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in this answer based on retrieved code context"
    )


class CodeSearchQueries(BaseModel):
    """
    Search queries generated for code retrieval.
    """

    queries: list[str] = Field(description="List of search queries to find relevant code")
    reasoning: str = Field(description="Explanation of query generation strategy")
class SourceReference(BaseModel):
    """
    A reference to a single source of information.

    This is the atomic unit of provenance tracking, representing where
    a piece of information came from.
    """
    source_id: str = Field(
        description="Unique identifier for this source (e.g., 'web_1', 'rag_3', 'kb_doc_5')"
    )
    source_type: Literal["web", "rag", "internal"] = Field(
        description="Type of source: 'web' for internet, 'rag' for knowledge base, 'internal' for system-generated"
    )
    url: Optional[str] = Field(
        default=None,
        description="URL if web source"
    )
    title: str = Field(
        description="Title or name of the source"
    )
    content_snippet: str = Field(
        description="Relevant excerpt from the source (max 500 chars)"
    )
    query_used: str = Field(
        description="The query that retrieved this source"
    )
    timestamp: str = Field(
        description="ISO format timestamp when source was retrieved"
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        default=0.5,
        description="Relevance/similarity score from retrieval (0.0-1.0)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (chunk_id, page_number, section, etc.)"
    )

class EvidenceItem(BaseModel):
    """
    A piece of evidence extracted from sources that supports a claim.

    Links specific content from sources to claims made in the analysis.
    """
    evidence_id: str = Field(
        description="Unique identifier for this evidence (e.g., 'ev_1', 'ev_2')"
    )
    content: str = Field(
        description="The actual evidence text/statement"
    )
    source_ids: List[str] = Field(
        description="List of source_ids this evidence comes from"
    )
    extraction_method: Literal["direct_quote", "paraphrase", "synthesis", "inference"] = Field(
        description="How this evidence was derived from sources"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this evidence (0.0-1.0)"
    )

class Claim(BaseModel):
    """
    A claim or assertion made in the research report.

    Each claim is linked to its supporting evidence, enabling
    'Why do you say that?' queries.
    """
    claim_id: str = Field(
        description="Unique identifier for this claim (e.g., 'claim_1', 'claim_2')"
    )
    statement: str = Field(
        description="The claim/assertion being made"
    )
    evidence_ids: List[str] = Field(
        description="List of evidence_ids supporting this claim"
    )
    claim_type: Literal["fact", "analysis", "synthesis", "recommendation", "opinion"] = Field(
        description="Type of claim being made"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this claim based on evidence strength (0.0-1.0)"
    )
    location_in_report: str = Field(
        description="Where in the report this claim appears (e.g., 'section_2', 'conclusion')"
    )

class LineageNode(BaseModel):
    """
    A node in the provenance knowledge graph.

    Represents either a source, evidence, or claim for graph visualization.
    """
    node_id: str = Field(
        description="Unique identifier for this node"
    )
    node_type: Literal["source", "evidence", "claim"] = Field(
        description="Type of node in the lineage graph"
    )
    label: str = Field(
        description="Short label for display (max 50 chars)"
    )
    full_content: str = Field(
        description="Full content of the node"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata for this node"
    )

class LineageEdge(BaseModel):
    """
    An edge in the provenance knowledge graph.

    Represents a relationship between nodes (source→evidence, evidence→claim).
    """
    source_node_id: str = Field(
        description="ID of the source node"
    )
    target_node_id: str = Field(
        description="ID of the target node"
    )
    relationship: Literal["derived_from", "supports", "cites", "synthesizes"] = Field(
        description="Type of relationship between nodes"
    )
    strength: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Strength of the relationship (0.0-1.0)"
    )

class ProvenanceGraph(BaseModel):
    """
    Complete provenance knowledge graph for a research report.

    Contains all sources, evidence, and claims with their relationships,
    enabling lineage queries and visualization.
    """
    sources: List[SourceReference] = Field(
        description="All sources consulted during research"
    )
    evidence: List[EvidenceItem] = Field(
        description="All evidence extracted from sources"
    )
    claims: List[Claim] = Field(
        description="All claims made in the report"
    )
    nodes: List[LineageNode] = Field(
        description="All nodes in the lineage graph"
    )
    edges: List[LineageEdge] = Field(
        description="All edges (relationships) in the lineage graph"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Graph metadata (query, timestamp, stats)"
    )

class Citation(BaseModel):
    """
    A formatted citation for academic export.

    Can be exported to various formats (BibTeX, APA, MLA, etc.).
    """
    citation_id: str = Field(
        description="Unique identifier for this citation"
    )
    source_id: str = Field(
        description="Reference to the original source"
    )
    title: str = Field(
        description="Title of the source"
    )
    authors: List[str] = Field(
        default_factory=list,
        description="Authors if available"
    )
    publication_date: Optional[str] = Field(
        default=None,
        description="Publication date if available"
    )
    url: Optional[str] = Field(
        default=None,
        description="URL if web source"
    )
    access_date: str = Field(
        description="Date the source was accessed"
    )
    source_type: str = Field(
        description="Type of source (webpage, document, etc.)"
    )

class ProvenanceAnalysis(BaseModel):
    """
    LLM-generated analysis of sources with structured provenance tracking.

    Used by the analyzer to return both the analysis text and the
    provenance metadata.
    """
    analysis_text: str = Field(
        description="The main analysis/synthesis of the information"
    )
    claims: List[Claim] = Field(
        description="Claims made in this analysis with evidence links"
    )
    evidence_items: List[EvidenceItem] = Field(
        description="Evidence extracted from sources"
    )
    confidence_assessment: str = Field(
        description="Overall assessment of evidence quality and confidence"
    )

class ProvenanceQuery(BaseModel):
    """
    A query for provenance information ('Why do you say that?').

    Used to trace back from a claim to its supporting evidence and sources.
    """
    claim_id: Optional[str] = Field(
        default=None,
        description="Specific claim ID to query"
    )
    claim_text: Optional[str] = Field(
        default=None,
        description="Text of claim to find and explain"
    )
    query_type: Literal["explain", "sources", "evidence", "full_lineage"] = Field(
        default="full_lineage",
        description="Type of provenance query"
    )

class ProvenanceResponse(BaseModel):
    """
    Response to a provenance query.

    Provides the reasoning chain from claim back to original sources.
    """
    claim: Claim = Field(
        description="The claim being explained"
    )
    evidence_chain: List[EvidenceItem] = Field(
        description="Evidence supporting this claim"
    )
    source_chain: List[SourceReference] = Field(
        description="Original sources for the evidence"
    )
    explanation: str = Field(
        description="Natural language explanation of the reasoning chain"
    )
    confidence_breakdown: dict = Field(
        default_factory=dict,
        description="Breakdown of confidence at each level"
    )
