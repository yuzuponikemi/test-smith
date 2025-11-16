"""
Model factory functions for Test-Smith multi-agent system.

Supports two model providers:
1. Ollama (local LLMs) - Default, no API key required
2. Claude/Anthropic - Cloud-based, requires ANTHROPIC_API_KEY in .env

To use Claude models, set USE_CLAUDE=true in .env file.
"""

import os
from typing import Literal
from langchain_ollama.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic

# Model provider configuration
USE_CLAUDE = os.getenv("USE_CLAUDE", "false").lower() == "true"

# Claude model versions (with enhanced detectability metadata)
CLAUDE_SONNET = "claude-sonnet-4-5-20250929"  # Latest Sonnet 4.5
CLAUDE_SONNET_35 = "claude-3-5-sonnet-20241022"  # Sonnet 3.5
CLAUDE_HAIKU = "claude-3-5-haiku-20241022"  # Haiku 3.5 (fast, cost-effective)

def _get_claude_model(
    model: str = CLAUDE_SONNET,
    temperature: float = 0.0,
    max_tokens: int = 4096
) -> ChatAnthropic:
    """
    Create a Claude model instance with enhanced detectability.

    Args:
        model: Claude model version (default: claude-sonnet-4-5-20250929)
        temperature: Sampling temperature (0.0 = deterministic)
        max_tokens: Maximum tokens in response

    Returns:
        ChatAnthropic instance configured with metadata for tracing
    """
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        # Enhanced detectability: Add metadata for LangSmith/LangGraph tracing
        model_kwargs={
            "extra_headers": {
                "anthropic-source": "test-smith-research-agent",
                "anthropic-version": "2025-01-15"
            }
        }
    )

def get_planner_model():
    """Strategic Planner - allocates queries between RAG and web search"""
    if USE_CLAUDE:
        # Use Haiku for fast query planning
        return _get_claude_model(
            model=CLAUDE_HAIKU,
            temperature=0.0,
            max_tokens=2048
        )
    return ChatOllama(model="llama3")

def get_master_planner_model():
    """
    Master Planner - hierarchical task decomposition
    Uses more powerful model for complex planning
    """
    if USE_CLAUDE:
        # Use Sonnet 4.5 for hierarchical decomposition
        return _get_claude_model(
            model=CLAUDE_SONNET,
            temperature=0.0,
            max_tokens=4096
        )
    return ChatOllama(model="command-r")

def get_reflection_model():
    """Reflection model for self-evaluation and critique"""
    if USE_CLAUDE:
        return _get_claude_model(
            model=CLAUDE_HAIKU,
            temperature=0.1,
            max_tokens=2048
        )
    return ChatOllama(model="llama3")

def get_evaluation_model():
    """Evaluator - assesses information sufficiency and depth quality"""
    if USE_CLAUDE:
        # Use Sonnet 3.5 for balanced evaluation
        return _get_claude_model(
            model=CLAUDE_SONNET_35,
            temperature=0.0,
            max_tokens=2048
        )
    return ChatOllama(model="command-r")

def get_analyzer_model():
    """Analyzer - processes and merges search/RAG results"""
    if USE_CLAUDE:
        # Use Sonnet 4.5 for comprehensive analysis
        return _get_claude_model(
            model=CLAUDE_SONNET,
            temperature=0.0,
            max_tokens=4096
        )
    return ChatOllama(model="llama3")

def get_synthesizer_model():
    """Synthesizer - generates final comprehensive reports"""
    if USE_CLAUDE:
        # Use Sonnet 4.5 for highest quality synthesis
        return _get_claude_model(
            model=CLAUDE_SONNET,
            temperature=0.1,  # Slight creativity for natural writing
            max_tokens=8192  # Allow longer reports
        )
    return ChatOllama(model="llama3")

# Model info utility
def get_active_models() -> dict:
    """
    Returns information about currently active models.
    Useful for debugging and tracing.
    """
    if USE_CLAUDE:
        return {
            "provider": "Claude/Anthropic",
            "planner": CLAUDE_HAIKU,
            "master_planner": CLAUDE_SONNET,
            "reflection": CLAUDE_HAIKU,
            "evaluation": CLAUDE_SONNET_35,
            "analyzer": CLAUDE_SONNET,
            "synthesizer": CLAUDE_SONNET
        }
    else:
        return {
            "provider": "Ollama (Local)",
            "planner": "llama3",
            "master_planner": "command-r",
            "reflection": "llama3",
            "evaluation": "command-r",
            "analyzer": "llama3",
            "synthesizer": "llama3"
        }
