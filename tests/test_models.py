"""Tests for model factory functions."""

import os

import pytest

# Skip all tests if API keys are not available
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY") and not os.getenv("OLLAMA_HOST"),
    reason="No model provider available (GOOGLE_API_KEY or OLLAMA_HOST required)",
)


def test_import_models() -> None:
    """Test that model functions can be imported."""
    from src.models import get_analyzer_model, get_planner_model, get_synthesizer_model

    assert get_planner_model is not None
    assert get_analyzer_model is not None
    assert get_synthesizer_model is not None
