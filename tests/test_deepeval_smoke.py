"""
DeepEval smoke test — verify metrics work with Ollama judge.

No agent execution. Uses hardcoded input/output to test DeepEval + Ollama integration only.
Takes ~30-60 seconds (just LLM judge calls).

Usage:
    uv run pytest tests/test_deepeval_smoke.py -v -s
"""

import pytest
from deepeval import assert_test  # type: ignore[attr-defined]
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase

ollama_judge = OllamaModel(
    model="command-r",
    base_url="http://localhost:11434",
    generation_kwargs={"num_ctx": 8192},
)


@pytest.mark.slow
def test_answer_relevancy_smoke():
    """Verify AnswerRelevancyMetric works with Ollama judge."""
    metric = AnswerRelevancyMetric(model=ollama_judge, threshold=0.5, async_mode=False)
    test_case = LLMTestCase(
        input="What is Python?",
        actual_output=(
            "Python is a high-level, general-purpose programming language. "
            "It emphasizes code readability with significant whitespace."
        ),
    )
    assert_test(test_case, [metric])


@pytest.mark.slow
def test_faithfulness_smoke():
    """Verify FaithfulnessMetric works with Ollama judge."""
    metric = FaithfulnessMetric(model=ollama_judge, threshold=0.5, async_mode=False)
    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output="The capital of France is Paris.",
        retrieval_context=["Paris is the capital and largest city of France."],
    )
    assert_test(test_case, [metric])
