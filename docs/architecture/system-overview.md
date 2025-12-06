# システム概要

**Test-Smith v2.2** - LangGraphマルチエージェント研究システム

---

## アーキテクチャ概要

Test-Smithは、専門化されたエージェントを統合して自律的に研究を実施し、包括的なレポートを生成する**階層的マルチエージェント研究システム**です。

### 主な特徴

- **マルチグラフアーキテクチャ**: 異なる研究ニーズに対応する5つの専門ワークフロー
- **階層的タスク分解**: 複雑なクエリを管理可能なサブタスクに分解
- **動的再計画**: 発見に基づいて研究計画を適応
- **戦略的クエリ割り当て**: 最適なソース（RAG vs Web）にクエリをルーティング
- **累積学習**: 反復にわたって結果を蓄積

---

## コアコンポーネント

### 1. ワークフローオーケストレーション (`src/graphs/`)

特定のユースケースに合わせた複数のグラフワークフロー:

| グラフ | 目的 | ノード数 |
|-------|---------|-------|
| `deep_research` | 複雑で多面的な研究 | 12ノード |
| `quick_research` | 高速シングルパス検索 | 6ノード |
| `fact_check` | 主張検証 | 7ノード |
| `comparative` | サイドバイサイド分析 | 8ノード |
| `causal_inference` | 根本原因分析 | 9ノード |

### 2. 処理ノード (`src/nodes/`)

グラフ間で共有される再利用可能なノード関数:

**コアノード:**
- `planner` - 戦略的クエリ割り当て
- `searcher` - Web検索（Tavily）
- `rag_retriever` - 知識ベース検索（ChromaDB）
- `analyzer` - 結果統合
- `evaluator` - 十分性評価
- `synthesizer` - レポート生成

**階層ノード:**
- `master_planner` - タスク分解
- `depth_evaluator` - 深度品質評価
- `drill_down_generator` - 再帰的サブタスク作成
- `plan_revisor` - 動的計画適応

**因果推論ノード:**
- `issue_analyzer`、`brainstormer`、`evidence_planner`
- `causal_checker`、`hypothesis_validator`、`causal_graph_builder`
- `root_cause_synthesizer`

### 3. LLM設定 (`src/models.py`)

プロバイダー抽象化を伴う中央集中型モデル管理:

```python
# 各タスクに専用のモデル関数
get_planner_model()      # llama3またはgemini-pro
get_evaluation_model()   # command-rまたはgemini-pro
get_synthesizer_model()  # command-rまたはgemini-pro
```

### 4. プロンプトテンプレート (`src/prompts/`)

各ノード用の変数注入を伴うLangChain PromptTemplate。

### 5. 知識ベース (`src/preprocessor/`, `chroma_db/`)

インテリジェント前処理とChromaDBベクトルストレージを備えたRAGシステム。

---

## ステート管理

### エージェントステートスキーマ

```python
class AgentState(TypedDict):
    # コアフィールド
    query: str
    report: str

    # クエリ割り当て
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str

    # 結果（累積）
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]

    # 評価
    evaluation: str
    reason: str
    loop_count: int

    # 階層モード
    execution_mode: str  # "simple"または"hierarchical"
    master_plan: dict
    current_subtask_id: str
    current_subtask_index: int
    subtask_results: dict

    # 動的再計画
    revision_count: int
    plan_revisions: list
    max_revisions: int
    max_total_subtasks: int
```

### ステート永続化

- **技術**: SQLiteチェックポイント（`langgraph-checkpoint-sqlite`）
- **目的**: 会話継続、クラッシュ回復、デバッグ

---

## 実行モード

### シンプルモード

単純なクエリ用 - 6ノードグラフを使用:

```
Planner → Searcher/RAG（並列） → Analyzer → Evaluator → Synthesizer
                                              ↓（不十分な場合）
                                           Planner（最大2ループ）
```

### 階層モード

複雑なクエリ用 - マスタープランニングとサブタスク実行を使用:

```
Master Planner → [Subtask Loop] → Hierarchical Synthesizer
                      ↓
          Subtask Executor → Planner → Searcher/RAG → Analyzer
                                                        ↓
                                              Depth Evaluator
                                                        ↓
                                            Drill-Down Generator
                                                        ↓
                                               Plan Revisor
                                                        ↓
                                              Save Result
```

---

## データフロー

### 1. 入力処理

```
ユーザークエリ → Master Planner → 複雑性評価 → モード選択
```

### 2. クエリ割り当て

```
Strategic Planner → KB内容確認 → RAG/Webクエリ割り当て
```

### 3. 並列検索

```
RAGクエリ → ChromaDB → RAG結果
Webクエリ → Tavily   → 検索結果
```

### 4. 分析と統合

```
結果 → Analyzer → 評価 → 統合 → レポート
```

---

## 主要な設計パターン

### 1. 累積ステート蓄積

自動リストマージのため`Annotated[list[str], operator.add]`を使用:

```python
# 各ノードがリストに追加
# LangGraphが自動的にマージ
search_results: Annotated[list[str], operator.add]
```

### 2. 戦略的クエリ割り当て

PlannerがKB内容を確認し、クエリを最適にルーティング:

```python
# KBに認証ドキュメントがある → 認証用RAGクエリ
# 現在の出来事が必要 → Webクエリ
allocation = {
    "rag_queries": ["内部認証フロー"],
    "web_queries": ["OAuth2ベストプラクティス2025"]
}
```

### 3. 構造化出力

`.with_structured_output()`を伴うPydanticスキーマ:

```python
from src.schemas import StrategicPlan

planner_llm = get_planner_model().with_structured_output(StrategicPlan)
output = planner_llm.invoke(prompt)  # 検証済みPydanticオブジェクト
```

### 4. 動的再計画

Plan Revisorが発見を分析しマスタープランを適応:

```python
# 元の計画にない重要なトピックを発見後
revision = {
    "should_revise": True,
    "new_subtasks": [...],
    "trigger_type": "new_topic"
}
```

---

## ディレクトリ構造

```
test-smith/
├── main.py                      # CLIエントリーポイント
├── src/
│   ├── graphs/                  # ワークフロー定義
│   │   ├── __init__.py          # グラフレジストリ
│   │   ├── base_graph.py        # 基底クラス
│   │   ├── deep_research_graph.py
│   │   ├── quick_research_graph.py
│   │   ├── fact_check_graph.py
│   │   ├── comparative_graph.py
│   │   └── causal_inference_graph.py
│   ├── nodes/                   # 処理ノード
│   ├── prompts/                 # LLMプロンプト
│   ├── models.py                # モデル設定
│   ├── schemas.py               # Pydanticスキーマ
│   └── preprocessor/            # ドキュメント前処理
├── scripts/
│   ├── ingest/                  # KB取り込み
│   ├── utils/                   # ユーティリティ
│   └── visualization/           # グラフ可視化
├── evaluation/                  # LangSmith評価
├── documents/                   # RAGソースドキュメント
├── chroma_db/                   # ベクトルデータベース
├── logs/                        # 実行ログ
└── reports/                     # 生成されたレポート
```

---

## 設定

### 環境変数

```bash
# 必須
TAVILY_API_KEY="your-key"

# LangSmith（オプション）
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Gemini（オプション）
GOOGLE_API_KEY="your-key"
MODEL_PROVIDER="ollama"  # または"gemini"
```

### 主要パラメータ

| パラメータ | 場所 | デフォルト | 目的 |
|-----------|----------|---------|---------|
| `recursion_limit` | main.py | 100 | 最大LangGraphステップ |
| `max_depth` | master_planner | 2 | 最大ドリルダウン深度 |
| `max_revisions` | plan_revisor | 3 | 最大計画改訂回数 |
| `max_total_subtasks` | plan_revisor | 20 | サブタスク予算 |
| `loop_count` | evaluator | 2 | 最大改善ループ |

---

## 関連ドキュメント

- **[マルチグラフワークフロー](multi-graph-workflows.md)** - ワークフローの詳細と選択
- **[グラフの作成](../development/creating-graphs.md)** - カスタムワークフローの構築
- **[RAGガイド](../knowledge-base/rag-guide.md)** - 知識ベース設定
