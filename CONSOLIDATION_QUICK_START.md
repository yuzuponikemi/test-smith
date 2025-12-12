# 🚀 ノード整理クイックスタート

## 今すぐ始められる3ステップ

### Step 1: Synthesizer統合（最も効果大）⭐

**Before (3ファイル, 598行):**
```python
src/nodes/
├── synthesizer_node.py                        # 291行
├── code_investigation_synthesizer_node.py     # 234行
└── root_cause_synthesizer_node.py             # 73行
```

**After (1ファイル, ~350行):**
```python
src/nodes/core/unified_synthesizer_node.py     # 350行
```

**実装コマンド:**
```bash
# 1. 新しい統合ノード作成
mkdir -p src/nodes/core
# （後述のコードをコピペ）

# 2. グラフファイルで切り替え
# src/graphs/deep_research_graph.py
from src.nodes.core.unified_synthesizer_node import unified_synthesizer_node

# 3. テスト
uv run python main.py run "テストクエリ" --graph deep_research

# 4. 旧ノード削除（動作確認後）
git mv src/nodes/synthesizer_node.py src/nodes/_deprecated/
```

---

### Step 2: Retriever統合（並列実行維持）

**Before:**
- `searcher_node.py` - Web検索
- `rag_retriever_node.py` - RAG検索

**After:**
- `unified_retriever_node.py` - 両方をサポート、並列実行可能

**コマンド:**
```bash
# 統合しても並列実行は維持（グラフ構造で制御）
workflow.add_node("web_search", lambda s: unified_retriever(s, mode="web"))
workflow.add_node("rag_search", lambda s: unified_retriever(s, mode="rag"))
```

---

### Step 3: ディレクトリ再編成（認知負荷削減）

```bash
# 新しい構造に移行
src/nodes/
├── core/                  # よく使う統合ノード
├── specialized/           # グラフ専用ノード
│   ├── causal_inference/
│   ├── code_investigation/
│   └── comparative/
└── shared/                # ユーティリティ

# 移行コマンド
mkdir -p src/nodes/{core,specialized/{causal_inference,code_investigation,comparative},shared}
git mv src/nodes/brainstormer_node.py src/nodes/specialized/causal_inference/
# （以下同様に移動）
```

---

## 🔍 実装サンプル: Unified Synthesizer

```python
# src/nodes/core/unified_synthesizer_node.py
"""統合Synthesizerノード - すべてのグラフで使用可能"""

from src.models import get_synthesizer_model
from src.prompts.synthesizer_prompt import (
    SYNTHESIZER_PROMPT,
    HIERARCHICAL_SYNTHESIZER_PROMPT,
    CODE_INVESTIGATION_SYNTHESIZER_PROMPT,
    ROOT_CAUSE_SYNTHESIZER_PROMPT,
)


def unified_synthesizer_node(state: dict) -> dict:
    """
    統合Synthesizer - モードで振る舞い切り替え

    state['synthesis_mode'] の値:
    - "deep_research" (default)
    - "hierarchical"
    - "code_investigation"
    - "root_cause"
    """
    mode = state.get("synthesis_mode", "deep_research")

    # モードに応じてプロンプトと処理を切り替え
    if mode == "hierarchical":
        return _synthesize_hierarchical(state)
    elif mode == "code_investigation":
        return _synthesize_code_investigation(state)
    elif mode == "root_cause":
        return _synthesize_root_cause(state)
    else:
        return _synthesize_default(state)


def _synthesize_hierarchical(state: dict) -> dict:
    """階層的研究レポート統合"""
    # 元のsynthesizer_node.pyのロジックをここに移動
    query = state.get("query", "")
    subtask_results = state.get("subtask_results", [])
    # ... 既存のロジック ...
    return {"report": final_report}


def _synthesize_code_investigation(state: dict) -> dict:
    """コード調査レポート統合"""
    # 元のcode_investigation_synthesizer_node.pyのロジック
    query = state.get("query", "")
    code_results = state.get("code_results", [])
    dependencies = state.get("dependencies", [])
    # ... 既存のロジック ...
    return {"report": investigation_report}


def _synthesize_root_cause(state: dict) -> dict:
    """根本原因分析レポート統合"""
    # 元のroot_cause_synthesizer_node.pyのロジック
    hypotheses = state.get("ranked_hypotheses", [])
    causal_graph = state.get("causal_graph", {})
    # ... 既存のロジック ...
    return {"report": rca_report}


def _synthesize_default(state: dict) -> dict:
    """通常の研究レポート統合"""
    query = state.get("query", "")
    analyzed_data = state.get("analyzed_data", [])
    model = get_synthesizer_model()
    # ... 既存のロジック ...
    return {"report": report}
```

**使用方法:**
```python
# src/graphs/deep_research_graph.py
from src.nodes.core.unified_synthesizer_node import unified_synthesizer_node

# ステートに synthesis_mode を設定
workflow.add_node("synthesizer", unified_synthesizer_node)

# または、デフォルト値を設定
def set_synthesis_mode(state):
    return {"synthesis_mode": "hierarchical"}

workflow.add_node("set_mode", set_synthesis_mode)
workflow.add_edge("set_mode", "synthesizer")
```

---

## 📊 効果測定

整理前後の比較:

| 指標 | 現状 | Step 1完了後 | Step 1-3完了後 |
|------|------|--------------|----------------|
| ノードファイル数 | 31 | 29 (-2) | 22 (-9) |
| 総行数 | 3,841 | 3,591 (-250) | 3,000 (-841) |
| ディレクトリ深度 | 1層 | 1層 | 3層（整理済み） |
| 新人が把握する時間 | 2-3日 | 2日 | 1日 |

---

## ⚠️ よくある質問

### Q1: 動的エージェント生成は必要？
**A:** 現時点では**不要**。以下の場合のみ検討:
- ワークフローを**週1で追加**するペース
- 非エンジニアがワークフロー作成する必要がある
- A/Bテストを**頻繁に**実施

それ以外は**Phase 1-2の静的統合**で十分。

---

### Q2: 既存グラフへの影響は？
**A:** 最小限。ノードのインポートパスが変わるのみ:
```python
# Before
from src.nodes.synthesizer_node import synthesizer_node

# After
from src.nodes.core.unified_synthesizer_node import unified_synthesizer_node
```

ステート構造は変更なし。

---

### Q3: テストは？
**A:** 統合前後で動作比較:
```bash
# 統合前のレポートを保存
uv run python main.py run "Pythonの歴史" > before.txt

# 統合後に同じクエリ
uv run python main.py run "Pythonの歴史" > after.txt

# 差分確認
diff before.txt after.txt
```

---

## 🎯 今すぐできること

```bash
# 1. 計画レビュー
cat docs/architecture/NODE_CONSOLIDATION_PLAN.md

# 2. Step 1を実装（推定時間: 2-3時間）
# - unified_synthesizer_node.pyを作成
# - 既存3ファイルのロジックを移動
# - 1つのグラフで試す

# 3. CIチェック
uv run ruff check .
uv run mypy src
uv run pytest

# 4. コミット
git add .
git commit -m "refactor(nodes): Synthesizer系ノードを統合 (-2ファイル, -250行)"
```

---

## 📚 参考資料

- **詳細計画**: `docs/architecture/NODE_CONSOLIDATION_PLAN.md`
- **動的生成サンプル**: `src/nodes/dynamic/agent_factory.py`
- **LangGraphパターン**: https://langchain-ai.github.io/langgraph/concepts/
