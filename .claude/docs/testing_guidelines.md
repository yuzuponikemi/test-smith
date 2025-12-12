# Testing Guidelines

Test-Smith プロジェクトのテスト・評価ガイドライン。

---

## テスト構造

### ディレクトリ配置
```
tests/
├── unit/                    # 単体テスト
│   ├── test_nodes.py       # ノード関数テスト
│   ├── test_schemas.py     # Pydanticスキーマテスト
│   └── test_models.py      # モデルファクトリーテスト
├── integration/             # 統合テスト
│   ├── test_graphs.py      # グラフ実行テスト
│   └── test_rag.py         # RAGパイプラインテスト
└── conftest.py              # 共通フィクスチャ
```

---

## 単体テストパターン

### ノード関数テスト
```python
import pytest
from src.nodes.planner_node import planner_node

def test_planner_node_with_valid_input():
    """正常入力でのプランナーノード実行"""
    state = {
        "query": "What is LangGraph?",
        "loop_count": 0
    }

    result = planner_node(state)

    assert "web_queries" in result
    assert "rag_queries" in result
    assert isinstance(result["web_queries"], list)

def test_planner_node_empty_query():
    """空クエリでの振る舞い"""
    state = {"query": "", "loop_count": 0}

    result = planner_node(state)

    # 空でも例外を投げない
    assert "web_queries" in result
```

### Pydanticスキーマテスト
```python
from src.schemas import StrategicPlan

def test_strategic_plan_validation():
    """スキーマバリデーション"""
    plan = StrategicPlan(
        rag_queries=["query1"],
        web_queries=["query2"],
        strategy="Test strategy"
    )

    assert len(plan.rag_queries) == 1
    assert plan.strategy == "Test strategy"

def test_strategic_plan_empty_queries():
    """空リストの許容"""
    plan = StrategicPlan(
        rag_queries=[],
        web_queries=[],
        strategy="No queries needed"
    )

    assert plan.rag_queries == []
```

---

## 統合テストパターン

### グラフ実行テスト
```python
import pytest
from src.graphs import get_graph

@pytest.fixture
def quick_research_graph():
    """QuickResearchグラフのフィクスチャ"""
    return get_graph("quick_research")

def test_quick_research_end_to_end(quick_research_graph):
    """QuickResearchグラフの完全実行"""
    result = quick_research_graph.invoke({
        "query": "What is Python?"
    })

    assert "report" in result
    assert len(result["report"]) > 0
```

### モック使用パターン
```python
from unittest.mock import patch, MagicMock

def test_searcher_node_with_mock():
    """外部API呼び出しのモック"""
    mock_results = [{"title": "Test", "content": "Mock content"}]

    with patch("src.nodes.searcher_node.TavilySearchResults") as mock_tavily:
        mock_tavily.return_value.invoke.return_value = mock_results

        result = searcher_node({"web_queries": ["test query"]})

        assert "search_results" in result
        mock_tavily.return_value.invoke.assert_called_once()
```

---

## フィクスチャ設計

### conftest.py
```python
import pytest
from langchain_community.chat_models import ChatOllama

@pytest.fixture(scope="session")
def test_llm():
    """テスト用LLMインスタンス（セッションスコープ）"""
    return ChatOllama(model="llama3", temperature=0)

@pytest.fixture
def sample_state():
    """基本的なAgentStateサンプル"""
    return {
        "query": "Test query",
        "web_queries": [],
        "rag_queries": [],
        "search_results": [],
        "rag_results": [],
        "analyzed_data": [],
        "report": "",
        "evaluation": "",
        "loop_count": 0
    }

@pytest.fixture
def mock_chroma_client():
    """ChromaDBクライアントモック"""
    with patch("chromadb.PersistentClient") as mock:
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock.return_value.get_collection.return_value = mock_collection
        yield mock
```

---

## テストデータ生成

### 研究クエリサンプル
```python
SAMPLE_QUERIES = {
    "simple": [
        "What is Python?",
        "How does LangGraph work?"
    ],
    "complex": [
        "Compare LangChain and LlamaIndex for RAG applications",
        "What are the trade-offs between different vector databases?"
    ],
    "causal": [
        "Why is my application experiencing high latency?",
        "What causes memory leaks in Python?"
    ]
}
```

### テストドキュメント
```python
SAMPLE_DOCUMENTS = [
    {
        "content": "LangGraph is a framework for building stateful agents.",
        "metadata": {"source": "test_doc_1.md"}
    },
    {
        "content": "ChromaDB is a vector database for embeddings.",
        "metadata": {"source": "test_doc_2.md"}
    }
]
```

---

## LangSmith評価

### 評価スクリプト実行
```bash
# 評価実行
uv run python evaluation/evaluate_agent.py

# 特定データセットで実行
uv run python evaluation/evaluate_agent.py --dataset research_queries
```

### 評価者タイプ
| 評価者 | 用途 |
|-------|------|
| `relevance_evaluator` | 回答の関連性 |
| `completeness_evaluator` | 情報の完全性 |
| `citation_evaluator` | 引用の正確性 |

### カスタム評価者
```python
from langsmith.evaluation import LangChainStringEvaluator

def custom_evaluator(run, example):
    """カスタム評価ロジック"""
    prediction = run.outputs.get("report", "")
    reference = example.outputs.get("expected", "")

    # スコアリングロジック
    score = calculate_similarity(prediction, reference)

    return {"score": score, "reasoning": "..."}
```

---

## CI統合

### pytest実行
```bash
# 全テスト
uv run pytest

# 詳細出力
uv run pytest -v --tb=short

# 特定ファイル
uv run pytest tests/unit/test_nodes.py

# カバレッジ付き
uv run pytest --cov=src --cov-report=html
```

### GitHub Actions設定
```yaml
# .github/workflows/ci.yml に設定済み
- name: Run tests
  run: uv run pytest -v --tb=short
```

---

## テスト作成チェックリスト

- [ ] 正常系テスト（happy path）
- [ ] 空入力・境界値テスト
- [ ] エラーハンドリングテスト
- [ ] 外部依存のモック化
- [ ] 適切なアサーション
- [ ] テスト名は振る舞いを説明
