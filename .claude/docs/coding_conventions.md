# Coding Conventions

Test-Smith プロジェクトのPythonコーディング規約。

---

## 型ヒント

### 必須ルール
```python
# ✅ 関数シグネチャには必ず型ヒント
def process_query(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    ...

# ✅ クラス属性にも型ヒント
class AgentState(TypedDict):
    query: str
    search_results: Annotated[list[str], operator.add]

# ✅ Pydanticモデルでの構造化出力
class StrategicPlan(BaseModel):
    rag_queries: list[str]
    web_queries: list[str]
    strategy: str
```

### 累積ステート用アノテーション
```python
from typing import Annotated
import operator

# 複数ノードから結果を累積する場合
search_results: Annotated[list[str], operator.add]
```

---

## 命名規則

| 対象 | 規則 | 例 |
|-----|------|-----|
| ファイル | snake_case | `planner_node.py` |
| クラス | PascalCase | `DeepResearchGraphBuilder` |
| 関数 | snake_case | `process_subtask()` |
| 定数 | UPPER_SNAKE | `MAX_ITERATIONS = 2` |
| 型変数 | PascalCase | `AgentState` |

### ノード関数命名
```python
# パターン: {role}_node または {action}_{target}
def planner_node(state: AgentState) -> dict:
    ...

def depth_evaluator_node(state: HierarchicalAgentState) -> dict:
    ...
```

### グラフビルダー命名
```python
# パターン: {ワークフロー名}GraphBuilder
class QuickResearchGraphBuilder(BaseGraphBuilder):
    ...
```

---

## Import順序

```python
# 1. 標準ライブラリ
import operator
from typing import Annotated, Any, Literal

# 2. サードパーティ
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph
from pydantic import BaseModel

# 3. ローカルモジュール
from src.models import get_planner_model
from src.schemas import StrategicPlan
from src.prompts.planner_prompt import PLANNER_PROMPT
```

---

## エラー処理パターン

### ノード内での安全な処理
```python
def searcher_node(state: AgentState) -> dict:
    queries = state.get("web_queries", [])

    # 空リストの場合は早期リターン（APIコール節約）
    if not queries:
        logger.info("No web queries assigned, skipping search")
        return {"search_results": []}

    try:
        results = perform_search(queries)
        return {"search_results": results}
    except SearchAPIError as e:
        logger.error(f"Search failed: {e}")
        return {"search_results": [f"Search error: {e}"]}
```

### ルーター関数のガード
```python
def router(state: AgentState) -> Literal["synthesizer", "planner"]:
    # ループ制限によるガード
    if state.get("loop_count", 0) >= MAX_ITERATIONS:
        return "synthesizer"

    evaluation = state.get("evaluation", "")
    if "sufficient" in evaluation.lower():
        return "synthesizer"

    return "planner"
```

---

## ロギング

### 標準パターン
```python
import logging

logger = logging.getLogger(__name__)

def my_node(state: dict) -> dict:
    logger.info(f"Processing query: {state.get('query', 'N/A')[:50]}...")
    # 処理
    logger.debug(f"Results count: {len(results)}")
    return {"results": results}
```

### 本番環境での構造化ロギング
```python
logger.info(
    "Node execution complete",
    extra={
        "node": "planner",
        "query_count": len(queries),
        "duration_ms": elapsed_ms
    }
)
```

---

## グラフ構築パターン

### BaseGraphBuilder継承
```python
from src.graphs.base_graph import BaseGraphBuilder

class MyWorkflowGraphBuilder(BaseGraphBuilder):
    def get_state_class(self) -> type:
        return MyWorkflowState

    def build(self) -> CompiledGraph:
        workflow = StateGraph(self.get_state_class())

        # ノード追加
        workflow.add_node("planner", planner_node)
        workflow.add_node("executor", executor_node)

        # エッジ定義
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", END)

        return workflow.compile()

    def get_metadata(self) -> dict:
        return {
            "name": "my_workflow",
            "description": "Brief description",
            "complexity": "low",
            "avg_time": "30-60 seconds"
        }
```

### 並列実行パターン
```python
# 並列ノードへのエッジ
workflow.add_edge("planner", "searcher")
workflow.add_edge("planner", "rag_retriever")

# 並列ノードからの合流
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("rag_retriever", "analyzer")
```

---

## Pydanticスキーマ定義

### 構造化出力用
```python
from pydantic import BaseModel, Field

class StrategicPlan(BaseModel):
    """プランナーの出力スキーマ"""
    rag_queries: list[str] = Field(
        description="Knowledge base queries"
    )
    web_queries: list[str] = Field(
        description="Web search queries"
    )
    strategy: str = Field(
        description="Allocation reasoning"
    )
```

### LLMとの連携
```python
from src.models import get_planner_model
from src.schemas import StrategicPlan

llm = get_planner_model().with_structured_output(StrategicPlan)
result: StrategicPlan = llm.invoke(prompt)
```

---

## コードフォーマット

### ツール
- **Ruff**: リンティング + フォーマット
- **Mypy**: 型チェック

### 実行コマンド
```bash
# リンティング
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# フォーマット
uv run ruff format .

# 型チェック
uv run mypy src
```

### 設定ファイル
`pyproject.toml` で設定済み。
