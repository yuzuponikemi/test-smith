# LangGraph Studio ガイド

## Code Execution Graph の可視化

LangGraph Studioでcode_execution graphを確認する方法を説明します。

## LangGraph Studioとは

LangGraph Studioは、LangGraphワークフローを視覚的に確認・デバッグできるツールです：

- **インタラクティブなグラフ可視化**: ノードとエッジをビジュアル表示
- **ステップ実行**: 各ノードの入力/出力を確認
- **タイムトラベルデバッグ**: 過去の状態に戻って再実行
- **状態変更**: 実行中に状態を変更してテスト

## セットアップ方法

### オプション1: LangGraph Studio Desktop アプリ（推奨）

1. **ダウンロード**
   ```
   https://studio.langchain.com/
   ```

2. **プロジェクトを開く**
   - アプリを起動
   - "Open Folder"をクリック
   - このプロジェクト: `/Users/ikmx/source/personal/test-smith` を選択

3. **グラフを選択**
   - 左サイドバーから `code_execution` を選択
   - または他のグラフ: `deep_research`, `quick_research`, etc.

4. **クエリを実行**
   - 入力欄に: `"Calculate the average of 15, 25, 35, and 45"`
   - "Run" をクリック

### オプション2: langgraph dev（要 Python 3.11+）

```bash
# Python 3.11+環境で
pip install -U "langgraph-cli[inmem]"
langgraph dev --port 8123

# ブラウザで開く
open http://localhost:8123
```

**注意**: 現在の環境はPython 3.9のため、Desktop アプリを使用してください。

## Code Execution Graph の構造

```
┌─────────────┐
│  __start__  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   planner   │ Strategic query allocation (RAG vs Web)
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
       ▼             ▼             │
┌────────────┐ ┌─────────────┐   │
│  searcher  │ │rag_retriever│   │ Parallel execution
└─────┬──────┘ └──────┬──────┘   │
      │                │          │
      └────────┬───────┘          │
               │                   │
               ▼                   │
        ┌─────────────┐           │
        │   analyzer  │           │ Merge & analyze
        └──────┬──────┘           │
               │                   │
         [条件分岐]                │
               │                   │
        ┌──────┴──────┐           │
        │             │           │
        ▼             ▼           │
┌──────────────┐ ┌──────────┐   │
│code_executor │ │evaluator │   │ Code execution (Docker)
└──────┬───────┘ └────┬─────┘   │
       │              │          │
       └──────┬───────┘          │
              │                   │
              ▼                   │
       ┌─────────────┐           │
       │  evaluator  │           │ Assess sufficiency
       └──────┬──────┘           │
              │                   │
        [条件分岐]                │
              │                   │
       ┌──────┴──────┐           │
       │             │           │
       ▼             ▼           │
┌─────────────┐ ┌────────┐     │
│ synthesizer │ │planner │◄────┘ Refine (max 2 loops)
└──────┬──────┘ └────────┘
       │
       ▼
  ┌──────────┐
  │ __end__  │
  └──────────┘
```

## 各ノードの役割

### 1. planner
- **役割**: クエリをRAG検索とWeb検索に振り分け
- **入力**: `query`, `loop_count`
- **出力**: `rag_queries`, `web_queries`, `allocation_strategy`
- **LLM**: llama3 + command-r

### 2. searcher & rag_retriever（並行実行）
- **searcher**: Tavily APIでWeb検索
- **rag_retriever**: ChromaDB知識ベース検索
- **出力**: `search_results`, `rag_results`

### 3. analyzer
- **役割**: Web/RAG結果をマージして分析
- **出力**: `analyzed_data`

### 4. code_executor ⭐ MCP準拠
- **役割**: Pythonコードを生成・実行
- **Docker実行**:
  - ネットワーク隔離 (`--network=none`)
  - メモリ制限 (512MB)
  - CPU制限 (1コア)
  - 60秒タイムアウト
- **入力**: `code_task` (または自動的に `query` を使用)
- **出力**: `code_execution_results`
  ```json
  {
    "success": true,
    "output": "30.0",
    "execution_mode": "docker_sandbox",
    "execution_time": 7.64,
    "code": "..."
  }
  ```

### 5. evaluator
- **役割**: 情報充足性を評価
- **出力**: `evaluation`, `reason`
- **ルーティング**:
  - "sufficient" → synthesizer
  - "insufficient" → planner（最大2ループ）

### 6. synthesizer
- **役割**: 最終レポート生成
- **出力**: `report`

## Studio で確認できる内容

### グラフビュー
- ノード間の接続関係
- 条件分岐（点線で表示）
- 並行実行ブロック
- ループ構造

### 実行トレース
各ステップで以下を確認可能：
```
[1] planner
  Input:
    query: "Calculate the average of 15, 25, 35, and 45"
    loop_count: 0
  Output:
    rag_queries: ["average calculation methods"]
    web_queries: ["current trends in numerical calculations 2025"]
    allocation_strategy: "..."

[2] searcher (parallel)
  Input: web_queries
  Output: search_results (Tavily APIの結果)

[3] rag_retriever (parallel)
  Input: rag_queries
  Output: rag_results (ChromaDBの結果)

[4] analyzer
  Input: search_results, rag_results
  Output: analyzed_data

[5] code_executor
  Input: query (auto-populated as code_task)
  Output:
    success: true
    output: "30.0"
    execution_mode: "docker_sandbox"
    execution_time: 7.64
    code: "def calculate_average(): ..."

[6] evaluator
  Input: analyzed_data, code_execution_results
  Output: evaluation: "sufficient"

[7] synthesizer
  Input: all accumulated data
  Output: report (final comprehensive report)
```

### 状態インスペクタ
各ノード後の完全な状態を確認：
```json
{
  "query": "Calculate the average of 15, 25, 35, and 45",
  "loop_count": 1,
  "rag_queries": [...],
  "web_queries": [...],
  "search_results": [...],
  "rag_results": [...],
  "analyzed_data": [...],
  "code_execution_results": [{
    "success": true,
    "output": "30.0",
    "execution_mode": "docker_sandbox",
    ...
  }],
  "evaluation": "...",
  "report": "..."
}
```

## デバッグ機能

### 1. ブレークポイント
特定のノードで実行を一時停止して状態を確認

### 2. 状態変更
ノード実行前に状態を手動で変更してテスト
```
例: code_executor 前に code_task を変更
    → 異なる計算タスクをテスト
```

### 3. ステップ実行
ノードを1つずつ実行して動作を確認

### 4. タイムトラベル
過去の状態に戻って別のパスを試す

## MCP設計の確認

Studioでは以下のMCP設計思想が確認できます：

### トークン効率
- code_execution graphは **明示的に選択された時のみロード**
- 他のグラフ実行時はこのコードが一切コンテキストに入らない
- **不要時は0 tokens**

### 独立性
- code_execution graphは他のグラフと完全に独立
- 状態スキーマも独自 (CodeExecutionState)
- ノードは再利用可能（planner, analyzer等）

### セキュリティ
- Docker実行モードがトレースで確認可能
- `execution_mode: "docker_sandbox"` フィールド
- 実行時間とエラーハンドリング

## テストクエリ例

### 計算タスク
```
Calculate the compound annual growth rate from 2018 to 2023
```

### データ分析
```
What is the correlation between variables A and B?
```

### 統計処理
```
Calculate the standard deviation of these numbers: 10, 15, 20, 25, 30
```

### 簡単な計算
```
What is 15% of 200?
```

## トラブルシューティング

### グラフが表示されない
- `langgraph.json` を確認
- `src/studio_graphs.py` が正しくインポートできるか確認
- 環境変数（.env）が設定されているか確認

### ノードが実行されない
- Ollamaが起動しているか確認: `ollama list`
- 必要なモデルがあるか: `llama3`, `command-r`, `nomic-embed-text`
- ChromaDBが初期化されているか確認

### Docker実行が失敗する
- Dockerが起動しているか: `docker info`
- フォールバックモードで動作: `execution_mode: "restricted_fallback"`

## 関連ファイル

- **langgraph.json**: Studio設定ファイル
- **src/studio_graphs.py**: グラフエントリーポイント
- **src/graphs/code_execution_graph.py**: グラフ定義
- **src/nodes/code_executor_node.py**: コード実行ノード
- **visualizations/code_execution_graph.mmd**: Mermaid図

## 参考リソース

- LangGraph Studio: https://studio.langchain.com/
- LangGraph Docs: https://python.langchain.com/docs/langgraph
- MCP Philosophy: `docs/MCP_PHILOSOPHY.md`
