"""Configuration module for Test-Smith research system."""

from src.config.research_depth import (
    DEPTH_CONFIGS,
    ResearchDepth,
    ResearchDepthConfig,
    get_depth_config,
)

__all__ = ["ResearchDepth", "ResearchDepthConfig", "DEPTH_CONFIGS", "get_depth_config"]
