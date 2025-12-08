"""
Research Depth Configuration

Defines configurable depth levels that control the breadth and depth of research:
- quick: Fast, surface-level research (1-2 pages equivalent)
- standard: Balanced research (3-5 pages equivalent) [default]
- deep: Thorough investigation (6-10 pages equivalent)
- comprehensive: Exhaustive research (10+ pages equivalent)

Each level affects:
- Number of search queries generated
- Maximum research iterations
- Subtask limits for hierarchical mode
- Report length expectations
- Evaluator strictness
"""

from dataclasses import dataclass
from typing import Literal

ResearchDepth = Literal["quick", "standard", "deep", "comprehensive"]


@dataclass(frozen=True)
class ResearchDepthConfig:
    """Configuration settings for a specific research depth level."""

    # Identity
    name: str
    description: str
    estimated_pages: str  # Human-readable estimate

    # Query Generation (Planner)
    min_queries: int  # Minimum total queries (RAG + Web)
    max_queries: int  # Maximum total queries (RAG + Web)
    rag_query_weight: float  # Fraction of queries for RAG (0.0-1.0)

    # Iteration Control (Router)
    max_iterations: int  # Maximum research loops
    max_subtasks: int  # Maximum subtasks in hierarchical mode

    # Report Generation (Synthesizer)
    target_word_count: int  # Target word count for report
    min_word_count: int  # Minimum acceptable word count
    detail_level: Literal["brief", "moderate", "detailed", "exhaustive"]

    # Evaluator Strictness
    evaluator_strictness: Literal["lenient", "standard", "strict", "very_strict"]
    min_sources_required: int  # Minimum sources before marking sufficient


# Depth level configurations
DEPTH_CONFIGS: dict[ResearchDepth, ResearchDepthConfig] = {
    "quick": ResearchDepthConfig(
        name="quick",
        description="Fast, surface-level research for simple questions",
        estimated_pages="1-2",
        # Planner
        min_queries=3,
        max_queries=4,
        rag_query_weight=0.3,
        # Router
        max_iterations=1,
        max_subtasks=0,  # Force simple mode
        # Synthesizer
        target_word_count=500,
        min_word_count=300,
        detail_level="brief",
        # Evaluator
        evaluator_strictness="lenient",
        min_sources_required=2,
    ),
    "standard": ResearchDepthConfig(
        name="standard",
        description="Balanced research with good coverage",
        estimated_pages="3-5",
        # Planner
        min_queries=5,
        max_queries=7,
        rag_query_weight=0.4,
        # Router
        max_iterations=2,
        max_subtasks=5,
        # Synthesizer
        target_word_count=1500,
        min_word_count=800,
        detail_level="moderate",
        # Evaluator
        evaluator_strictness="standard",
        min_sources_required=4,
    ),
    "deep": ResearchDepthConfig(
        name="deep",
        description="Thorough investigation with multiple perspectives",
        estimated_pages="6-10",
        # Planner
        min_queries=8,
        max_queries=12,
        rag_query_weight=0.4,
        # Router
        max_iterations=3,
        max_subtasks=10,
        # Synthesizer
        target_word_count=4000,
        min_word_count=2500,
        detail_level="detailed",
        # Evaluator
        evaluator_strictness="strict",
        min_sources_required=8,
    ),
    "comprehensive": ResearchDepthConfig(
        name="comprehensive",
        description="Exhaustive research covering all aspects",
        estimated_pages="10+",
        # Planner
        min_queries=15,
        max_queries=20,
        rag_query_weight=0.5,
        # Router
        max_iterations=5,
        max_subtasks=20,
        # Synthesizer
        target_word_count=10000,
        min_word_count=6000,
        detail_level="exhaustive",
        # Evaluator
        evaluator_strictness="very_strict",
        min_sources_required=15,
    ),
}


def get_depth_config(depth: ResearchDepth) -> ResearchDepthConfig:
    """Get configuration for the specified research depth level."""
    if depth not in DEPTH_CONFIGS:
        raise ValueError(
            f"Unknown depth level: {depth}. "
            f"Valid options: {', '.join(DEPTH_CONFIGS.keys())}"
        )
    return DEPTH_CONFIGS[depth]


def get_depth_description(depth: ResearchDepth) -> str:
    """Get human-readable description for a depth level."""
    config = get_depth_config(depth)
    return (
        f"{config.name}: {config.description} "
        f"(~{config.estimated_pages} pages, {config.target_word_count} words)"
    )


def list_depth_levels() -> dict[str, str]:
    """List all available depth levels with descriptions."""
    return {name: get_depth_description(name) for name in DEPTH_CONFIGS}
