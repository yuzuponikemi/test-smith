"""
DeepEval agent evaluation tests.

Tests agent response quality using LLM-as-Judge pattern with DeepEval metrics.
Requires running Ollama (command-r) and Tavily API key.

Usage:
    uv run deepeval test run tests/test_agent_eval.py
    uv run pytest tests/test_agent_eval.py -v -s
"""

import pytest
from deepeval import assert_test  # type: ignore[attr-defined]
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase
from langgraph.checkpoint.sqlite import SqliteSaver

from src.graphs import get_graph

# ==================== Judge Model ====================

ollama_judge = OllamaModel(
    model="command-r",
    base_url="http://localhost:11434",
    generation_kwargs={"num_ctx": 8192},
)

# ==================== Metrics ====================

answer_relevancy_metric = AnswerRelevancyMetric(
    model=ollama_judge,
    threshold=0.7,
    async_mode=False,
)

faithfulness_metric = FaithfulnessMetric(
    model=ollama_judge,
    threshold=0.7,
    async_mode=False,
)

# ==================== Golden Dataset ====================

GOLDEN_DATASET = [
    {
        "input": "フローサイトメーターとは何か？",
        "expected_output": (
            "フローサイトメーターは、液体中の細胞や粒子をレーザー光で一つずつ分析する装置です。"
            "細胞のサイズ、形態、蛍光特性などを高速に測定でき、"
            "免疫学、がん研究、血液学などの分野で広く使用されています。"
        ),
    },
    {
        "input": "PCR法の原理を説明してください",
        "expected_output": (
            "PCR（ポリメラーゼ連鎖反応）は、特定のDNA配列を指数関数的に増幅する技術です。"
            "変性（二本鎖DNAの分離）、アニーリング（プライマーの結合）、"
            "伸長（DNAポリメラーゼによる合成）の3ステップを繰り返すことで、"
            "少量のDNAから大量のコピーを生成します。"
        ),
    },
]


# ==================== Agent Runner ====================

# Cache agent results to avoid running the agent multiple times per query
_agent_cache: dict[str, dict] = {}


def run_agent(query: str) -> dict:
    """Run quick_research graph and return final state. Results are cached per query."""
    if query in _agent_cache:
        return _agent_cache[query]

    builder = get_graph("quick_research")
    with SqliteSaver.from_conn_string(":memory:") as memory:
        app = builder.get_uncompiled_graph().compile(checkpointer=memory)
        config = {
            "configurable": {"thread_id": "eval-test"},
            "recursion_limit": 150,
        }
        inputs = {"query": query, "loop_count": 0}

        final_state: dict = {}
        for output in app.stream(inputs, config=config):
            for _key, value in output.items():
                if value:
                    final_state.update(value)

    _agent_cache[query] = final_state
    return final_state


# ==================== Tests ====================


@pytest.mark.slow
def test_answer_relevancy_flow_cytometer():
    """Test answer relevancy for flow cytometer query."""
    data = GOLDEN_DATASET[0]
    state = run_agent(data["input"])
    actual_output = state.get("report", "")

    test_case = LLMTestCase(
        input=data["input"],
        actual_output=actual_output,
        expected_output=data["expected_output"],
    )
    assert_test(test_case, [answer_relevancy_metric])


@pytest.mark.slow
def test_faithfulness_flow_cytometer():
    """Test faithfulness for flow cytometer query."""
    data = GOLDEN_DATASET[0]
    state = run_agent(data["input"])
    actual_output = state.get("report", "")
    retrieval_context = state.get("search_results", []) + state.get("rag_results", [])

    test_case = LLMTestCase(
        input=data["input"],
        actual_output=actual_output,
        retrieval_context=retrieval_context if retrieval_context else ["No context retrieved"],
    )
    assert_test(test_case, [faithfulness_metric])


@pytest.mark.slow
def test_answer_relevancy_pcr():
    """Test answer relevancy for PCR query."""
    data = GOLDEN_DATASET[1]
    state = run_agent(data["input"])
    actual_output = state.get("report", "")

    test_case = LLMTestCase(
        input=data["input"],
        actual_output=actual_output,
        expected_output=data["expected_output"],
    )
    assert_test(test_case, [answer_relevancy_metric])


@pytest.mark.slow
def test_faithfulness_pcr():
    """Test faithfulness for PCR query."""
    data = GOLDEN_DATASET[1]
    state = run_agent(data["input"])
    actual_output = state.get("report", "")
    retrieval_context = state.get("search_results", []) + state.get("rag_results", [])

    test_case = LLMTestCase(
        input=data["input"],
        actual_output=actual_output,
        retrieval_context=retrieval_context if retrieval_context else ["No context retrieved"],
    )
    assert_test(test_case, [faithfulness_metric])
