# ノード整理・スリム化計画

## 📊 現状
- **ノード数**: 31個
- **総行数**: 3,841行
- **課題**: 管理負担増、重複コード、認知負荷

---

## 🎯 整理戦略（優先度順）

### **Phase 1: クイックウィン（1-2週間）** ⭐ 即実施推奨

#### 1.1 Synthesizer系の統合 (-2ファイル, -250行)
**統合対象:**
- `synthesizer_node.py` (291行)
- `code_investigation_synthesizer_node.py` (234行)
- `root_cause_synthesizer_node.py` (73行)

**→ `unified_synthesizer_node.py` (~350行)**

```python
def unified_synthesizer_node(state: dict) -> dict:
    """統合synthesizerノード - モードで振る舞い切り替え"""
    mode = state.get("synthesis_mode", "deep_research")

    if mode == "deep_research":
        return _synthesize_hierarchical(state)
    elif mode == "code_investigation":
        return _synthesize_code_investigation(state)
    elif mode == "root_cause":
        return _synthesize_root_cause(state)
    else:
        return _synthesize_default(state)
```

**効果:**
- ファイル数: 31 → 29 (-2)
- 行数: 3,841 → 3,591 (-250)
- プロンプト選択ロジックを一元管理

---

#### 1.2 Retriever系の統合 (-1ファイル, -100行)
**統合対象:**
- `searcher_node.py` (108行) - Web検索
- `rag_retriever_node.py` (115行) - RAG検索

**→ `unified_retriever_node.py` (~150行)**

並列実行は維持しつつ、共通ロジック（エラーハンドリング、ロギング）を統合

```python
def unified_retriever_node(state: dict) -> dict:
    """Web/RAG検索を統合 - 並列実行可能"""
    retrieval_type = state.get("retrieval_type", "hybrid")

    if retrieval_type == "web_only":
        return _search_web(state)
    elif retrieval_type == "rag_only":
        return _search_rag(state)
    else:  # hybrid
        return _search_both_parallel(state)
```

---

#### 1.3 Evaluator系の統合 (-1ファイル, -50行)
**統合対象:**
- `evaluator_node.py` (評価)
- `depth_evaluator_node.py` (115行) - 深度評価
- `reflection_node.py` (109行) - リフレクション

**→ `unified_evaluator_node.py` (~200行)**

---

### **Phase 2: モジュラー再構築（3-4週間）**

#### 2.1 ディレクトリ構造の再編成

```
src/nodes/
├── core/                           # 汎用コアノード（8-10個）
│   ├── unified_synthesizer.py     # 統合synthesizer
│   ├── unified_retriever.py       # 統合retriever
│   ├── unified_evaluator.py       # 統合evaluator
│   ├── unified_planner.py         # strategic + master planner
│   └── base_analyzer.py           # 汎用analyzer
│
├── specialized/                    # グラフ専用ノード（15-20個）
│   ├── causal_inference/          # 因果推論専用
│   │   ├── brainstormer.py
│   │   ├── causal_checker.py
│   │   └── hypothesis_validator.py
│   │
│   ├── code_investigation/        # コード調査専用
│   │   ├── code_query_analyzer.py
│   │   ├── dependency_analyzer.py
│   │   └── flow_tracker.py
│   │
│   └── provenance/                # 来歴追跡専用
│       └── provenance_graph_builder.py
│
├── shared/                         # 共有ユーティリティ
│   ├── source_formatting.py      # ソースフォーマット共通化
│   ├── citation_handler.py       # 引用処理共通化
│   └── graph_builder_utils.py    # グラフ構築ヘルパー
│
└── dynamic/                        # 動的生成（オプション）
    └── agent_factory.py           # 設定ベースノード生成
```

**効果:**
- 認知負荷削減（グラフごとに関連ノードが整理）
- インポート整理（`from src.nodes.specialized.causal_inference import brainstormer`）
- テストしやすい（モジュールごとに分離）

---

#### 2.2 共通ロジックの抽出

**抽出候補:**
- ソースフォーマット処理（synthesizer系で重複）
- 引用処理（複数ノードで使用）
- グラフ構造構築（`causal_graph_builder`, `provenance_graph_builder`）

```python
# Before: synthesizer_node.py, code_investigation_synthesizer_node.pyで重複
def _format_source_summary(state: dict) -> str:
    # 200行の重複コード...

# After: src/nodes/shared/source_formatting.py
from src.nodes.shared.source_formatting import format_sources_with_citations

def synthesizer_node(state: dict) -> dict:
    sources = format_sources_with_citations(state)  # 再利用
```

---

### **Phase 3: 動的エージェント生成（4-8週間）** 🚀 長期戦略

#### 3.1 YAML設定ベースワークフロー

```yaml
# configs/workflows/quick_research.yaml
graph: quick_research
nodes:
  - id: planner
    type: planner
    model: llama3
    prompt: prompts/strategic_planner.txt
    output_schema: StrategicPlan

  - id: retriever
    type: retriever
    mode: hybrid
    web_queries_from: planner.web_queries
    rag_queries_from: planner.rag_queries

  - id: analyzer
    type: analyzer
    model: command-r
    prompt: prompts/analyzer.txt
    inputs: [retriever.search_results, retriever.rag_results]
    output: analyzed_data

edges:
  - from: planner
    to: [retriever]
  - from: retriever
    to: analyzer
```

#### 3.2 動的ロード

```python
# src/graphs/dynamic_graph_builder.py
from src.nodes.dynamic.agent_factory import AgentFactory

class DynamicGraphBuilder:
    def build_from_config(self, yaml_path: str):
        config = load_yaml(yaml_path)
        factory = AgentFactory()

        workflow = StateGraph(...)
        for node_config in config["nodes"]:
            node_func = factory.create_node(
                node_config["type"],
                node_config
            )
            workflow.add_node(node_config["id"], node_func)

        # エッジも設定から追加...
        return workflow.compile()
```

**メリット:**
- ノードファイル: 31 → 10-15個（コア + 専用のみ）
- 新ワークフロー追加: YAMLファイル作成のみ
- A/Bテスト容易（プロンプトやモデル変更が設定のみ）

**デメリット:**
- デバッグが難しい（スタックトレースが動的生成コードを指す）
- 型安全性低下（Pydanticスキーマを文字列で指定）
- LangSmith/Studioでノード名が動的

---

## 🎯 推奨実施順序

### **今すぐ実施（Phase 1）:**
1. **Synthesizer統合** - 最も効果が高い
2. **Retriever統合** - 並列実行維持しつつ共通化
3. **Evaluator統合** - 評価ロジック一元化

**期待効果:**
- ファイル数: 31 → 27 (-4)
- 行数: 3,841 → 3,400 (-441, 約11%削減)
- **実装時間: 1-2週間**

---

### **次のステップ（Phase 2）:**
4. **ディレクトリ再編成** - 認知負荷削減
5. **共通ロジック抽出** - DRY原則適用

**期待効果:**
- コード重複: -20%
- テスト容易性: +30%
- **実装時間: 3-4週間**

---

### **長期戦略（Phase 3）:**
6. **動的エージェント生成** - 最大の柔軟性

**期待効果:**
- ノードファイル: 27 → 10-15
- 新ワークフロー追加時間: 数時間 → 30分
- **実装時間: 4-8週間**

**注意:** Phase 3は**実験的**。既存システムが安定している場合、Phase 1-2で十分。

---

## 🔍 他のLangGraphプロジェクトの事例

### **事例1: LangChain公式テンプレート**
- **ノード数**: 平均 8-12個
- **戦略**: シンプルな専用ノード + 条件付きルーティング
- **教訓**: 複雑性は**グラフ構造**で表現、ノードはシンプルに保つ

### **事例2: AutoGPT/BabyAGI系**
- **ノード数**: 5-7個（非常に少ない）
- **戦略**: 動的タスク生成 + シンプルなコアループ
- **教訓**: 動的性は**ステート**で管理、ノードは汎用化

### **事例3: CrewAI**
- **ノード数**: エージェントごとに1つ（可変）
- **戦略**: エージェント = 設定 + ツール（動的ロード）
- **教訓**: 設定駆動アーキテクチャで拡張性確保

---

## 💡 Test-Smithに最適な戦略

### **推奨アプローチ: ハイブリッド型**

```
コアノード（統合済み）
    ↓
専門ノード（グラフ固有）
    ↓
動的生成（実験的新機能のみ）
```

**理由:**
1. **既存の安定性維持**: Phase 1-2は既存コードを整理するのみ
2. **デバッグ容易性**: 専用ノードは静的に保持
3. **拡張性**: 新ワークフローはPhase 3の動的生成で実験

---

## 📊 効果予測

| 指標 | 現状 | Phase 1 | Phase 2 | Phase 3 |
|------|------|---------|---------|---------|
| ノードファイル数 | 31 | 27 | 22 | 10-15 |
| 総行数 | 3,841 | 3,400 | 3,000 | 2,500 |
| 新ワークフロー追加時間 | 8時間 | 6時間 | 4時間 | 30分 |
| デバッグ難易度 | 中 | 中 | 低 | 高 |
| 認知負荷 | 高 | 中 | 低 | 中 |

---

## 🚀 アクションプラン

### Week 1-2:
- [ ] Synthesizer統合実装
- [ ] 既存グラフでテスト
- [ ] ドキュメント更新

### Week 3-4:
- [ ] Retriever統合実装
- [ ] Evaluator統合実装
- [ ] CI/CDテスト通過確認

### Week 5-8:
- [ ] ディレクトリ再編成
- [ ] 共通ロジック抽出
- [ ] リファクタリング完了

### Week 9-16（オプション）:
- [ ] 動的生成システム実装
- [ ] YAML設定実験
- [ ] 既存ワークフローを段階的移行

---

## 参考リソース

- **LangGraph Best Practices**: https://langchain-ai.github.io/langgraph/concepts/
- **Agent Architecture Patterns**: https://www.patterns.dev/posts/agent-architecture
- **CrewAI Config-Driven Design**: https://docs.crewai.com/concepts/agents
