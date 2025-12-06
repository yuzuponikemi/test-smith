# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリのコードを扱う際のガイダンスを提供します。

## プロジェクト概要

Test-Smithは、深い調査を自律的に実施し包括的なレポートを生成する**LangGraphベースのマルチエージェント研究アシスタント**です。**動的な再計画**機能を備えた高度な「階層的Plan-and-Execute」戦略を使用し、ステートベースのワークフローを通じて協調する専門化エージェントを特徴としています。

**バージョン:** v2.3 (6つの専門ワークフローを持つマルチグラフアーキテクチャ)

**主要技術:**
- LangGraph 0.6.11 (オーケストレーション)
- LangChain 0.3.27 (LLMフレームワーク)
- Ollama (ローカルLLM: llama3, command-r, nomic-embed-text)
- ChromaDB 1.3.4 (RAG用ベクトルデータベース)
- Tavily API (Web検索)
- LangSmith (可観測性/トレーシング)

## マルチグラフアーキテクチャ ⭐ NEW

Test-Smithは、調査ニーズに基づいて選択できる**複数のグラフワークフロー**をサポートするようになりました。すべてのグラフは同じノードとプロンプトを再利用するため、システムはモジュラーで拡張可能です。

### 利用可能なグラフ

1. **deep_research** (デフォルト) - 動的な再計画を伴う階層的マルチエージェント研究
   - 最適な用途: 複雑で多面的な質問、深い探索
   - 機能: タスク分解、再帰的ドリルダウン、適応型計画
   - 複雑度: 高 | 平均時間: 2-5分

2. **quick_research** - 高速シングルパス研究
   - 最適な用途: シンプルな質問、クイックファクト検索、時間に敏感なニーズ
   - 機能: シングルパス実行、最大2回の改善反復
   - 複雑度: 低 | 平均時間: 30-60秒

3. **fact_check** - 主張検証ワークフロー
   - 最適な用途: 事実確認、正確性チェック、相互参照
   - 機能: 証拠分類、信頼度スコアリング、引用追跡
   - 複雑度: 中 | 平均時間: 30-45秒

4. **comparative** - サイドバイサイド分析
   - 最適な用途: 技術/ツールの比較、トレードオフ分析、意思決定支援
   - 機能: 比較マトリックス、長所/短所、ユースケース推奨
   - 複雑度: 中 | 平均時間: 45-90秒

5. **causal_inference** - 根本原因分析と因果推論
   - 最適な用途: 問題のトラブルシューティング、インシデント調査、因果関係の理解
   - 機能: 仮説生成、証拠検証、因果グラフ、確率ランキング
   - 複雑度: 中 | 平均時間: 60-90秒

6. **code_investigation** ⭐ NEW - 深いコードベース分析と調査
   - 最適な用途: コード構造の理解、依存関係の発見、データフローのトレース
   - 機能: 依存関係追跡、フロー分析、変数使用状況、アーキテクチャパターン
   - 複雑度: 中 | 平均時間: 45-90秒

### グラフの選択

```bash
# 利用可能なすべてのグラフと説明を一覧表示
uv run python main.py graphs

# 詳細情報を含めて一覧表示
uv run python main.py graphs --detailed

# 特定のグラフで実行
uv run python main.py run "クエリ" --graph <graph_name>

# デフォルトでdeep_research（後方互換性あり）
uv run python main.py run "クエリ"
```

### カスタムグラフの作成

モジュラーアーキテクチャにより、新しいグラフワークフローを簡単に作成できます:

1. `src/graphs/`に新しいファイルを作成（例: `my_workflow_graph.py`）
2. `BaseGraphBuilder`を拡張し、以下を実装:
   - `get_state_class()` - ステートスキーマを定義
   - `build()` - ワークフローをビルドしコンパイル
   - `get_metadata()` - グラフを説明
3. `src/graphs/__init__.py`に登録
4. `src/nodes/`の既存ノードと`src/prompts/`のプロンプトを再利用

シンプルな例は`src/graphs/quick_research_graph.py`を参照してください。

## アーキテクチャ

### マルチエージェントワークフロー

システムは**2つの実行モード**をサポートします:

#### シンプルモード (v1.0 - シングルパス研究)
単純なクエリの場合、条件付きルーティングを持つ**6ノードグラフ**を使用:

1. **Strategic Planner（戦略プランナー）** → RAGとWeb検索の間でクエリを賢く割り当て
2. **Searcher（検索者）** (Tavily) + **RAG Retriever（RAG検索者）** (ChromaDB) → 異なるクエリセットで並列実行
3. **Analyzer（分析者）** → 結果をマージし要約
4. **Evaluator（評価者）** → 情報の十分性を評価
5. **Router（ルーター）** → 決定: 十分 → 統合、不十分 → 改善（最大2回の反復）
6. **Synthesizer（統合者）** → 最終的な包括的レポートを生成

#### 階層的モード (v2.1 - 動的再計画を伴う深い研究) ⭐ NEW
複雑なクエリの場合、**適応型階層的ワークフロー**を使用:

1. **Master Planner（マスタープランナー）** → 複雑さを検出しサブタスクに分解（フェーズ1）
2. **各サブタスクについて:**
   - Strategic Planner → この特定のサブタスクのクエリを割り当て
   - Searcher + RAG Retriever → 並列実行
   - Analyzer → 結果を処理
   - **Depth Evaluator（深度評価者）** → 深度品質を評価（フェーズ2）
   - **Drill-Down Generator（ドリルダウンジェネレーター）** → 必要に応じて子サブタスクを作成（フェーズ3）
   - **Plan Revisor（計画改訂者）** → 発見に基づいてマスタープランを適応 ⭐（フェーズ4）
3. **Hierarchical Synthesizer（階層的統合者）** → すべてのサブタスク結果を包括的レポートに統合

**主要なイノベーション:**
- **動的再計画（フェーズ4）:** 重要な発見に基づいてシステムが実行中にマスタープランを適応
- **階層的分解:** 複雑なクエリを管理可能なサブタスクに分解し、再帰的ドリルダウン
- **戦略的クエリ割り当て:** 適切な情報ソース（RAG vs Web）にクエリをターゲット
- **深度認識探索:** 重要性に基づいて調査深度を自動調整
- **安全制御:** 予算制限により暴走拡大を防止（最大3回の改訂、20サブタスク）

**キーパターン:** 反復にわたる累積結果蓄積のため`Annotated[list[str], operator.add]`を使用。

#### 因果推論モード (v2.2 - 根本原因分析) ⭐ NEW
トラブルシューティングと調査クエリの場合、**9ノードの専門ワークフロー**を使用:

1. **Issue Analyzer（問題分析者）** → 問題文から症状、コンテキスト、範囲を抽出
2. **Brainstormer（ブレインストーマー）** → 多様な根本原因仮説を生成（5-8仮説）
3. **Evidence Planner（証拠プランナー）** → 証拠収集のための戦略的クエリを計画（RAG + Web）
4. **Searcher + RAG Retriever** → 並列で証拠を収集
5. **Causal Checker（因果チェッカー）** → 厳密な基準を使用して因果関係を検証
6. **Hypothesis Validator（仮説検証者）** → 信頼レベルで仮説を可能性順にランク付け
7. **Router（ルーター）** → さらなる証拠が必要かどうかを決定（最大2回の反復）
8. **Causal Graph Builder（因果グラフビルダー）** → 可視化準備完了のグラフ構造を作成
9. **Root Cause Synthesizer（根本原因統合者）** → 包括的なRCAレポートを生成

**主要機能:**
- **体系的仮説生成:** 発散的思考を使用（5つのなぜ、フィッシュボーン、類推的）
- **厳密な因果検証:** 時間的優先順位、共変動、メカニズムの妥当性
- **証拠ベースのランキング:** 信頼レベル（高/中/低）付き確率スコア（0.0-1.0）
- **因果グラフ可視化:** ノード（仮説/症状）とエッジ（関係）の構造化データ
- **包括的なRCAレポート:** エグゼクティブサマリー、ランク付けされた仮説、推奨事項、信頼度評価

**ユースケース:**
- 技術的トラブルシューティングとデバッグ
- インシデント調査とポストモーテム
- システム障害分析
- なぜ何かが起こったのかを理解
- 仮説駆動調査

**因果グラフ可視化:**
ワークフローは可視化可能な構造化グラフ表現（ノード + エッジ）を生成:
```bash
# ワークフロー出力からグラフデータを抽出しJSONに保存
# その後、含まれているスクリプトを使用して可視化
python scripts/visualization/visualize_causal_graph.py causal_graph.json

# 以下を示すインタラクティブHTML可視化を開く:
# - 仮説ノード（可能性で色分け）
# - 症状ノード
# - 因果関係（強度インジケーター付きエッジ）
```

#### コード調査モード (v2.3 - コードベース分析) ⭐ NEW
コードベース研究と理解のため、**5ノードの専門ワークフロー**を使用:

1. **Code Query Analyzer（コードクエリ分析者）** → 調査範囲とターゲット要素を理解
2. **Code Retriever（コード検索者）** → RAG検索経由で関連コードを取得
3. **Dependency Analyzer（依存関係分析者）** → クラス/関数の依存関係を追跡（並列）
4. **Code Flow Tracker（コードフロートラッカー）** → データ/制御フローを分析（並列）
5. **Code Investigation Synthesizer（コード調査統合者）** → 包括的レポートを生成

**主要機能:**
- **インテリジェントクエリ分析:** 調査タイプを決定（依存関係、フロー、使用状況、アーキテクチャ）
- **依存関係追跡:** インポート分析、クラス継承、コンポジション、関数呼び出し
- **フロー分析:** データフローパス、制御フロー、変数使用状況
- **マルチ言語サポート:** Python、C#、JavaScript、TypeScript、Java、Go、Rust
- **C# & Windows Formsサポート:** .cs、.csproj、.sln、.resx、.xamlファイルの完全サポート

**ユースケース:**
- 機能の実装方法の理解
- 関数やクラスのすべての使用箇所を見つける
- コンポーネント間の依存関係をトレース
- コードベースを通じたデータフローの分析
- アーキテクチャとデザインパターン分析
- リファクタリング影響評価

**使用方法:**
```bash
# コード依存関係を調査
uv run python main.py run "AuthServiceに依存しているクラスは？" --graph code_investigation

# データフローをトレース
uv run python main.py run "ユーザー入力が検証システムをどのように流れるか？" --graph code_investigation

# 関数の使用状況を検索
uv run python main.py run "calculate_total関数はどこで使用されているか？" --graph code_investigation
```

**コード調査グラフのテスト:**
```bash
# フルテスト: test-smithリポジトリを取り込み + テストクエリを実行
uv run python scripts/experiments/test_code_investigation.py

# 取り込みをスキップ（既存のcodebase_collectionを使用）
uv run python scripts/experiments/test_code_investigation.py --skip-ingest

# 特定のテストを実行
uv run python scripts/experiments/test_code_investigation.py --test dependency
uv run python scripts/experiments/test_code_investigation.py --test flow
uv run python scripts/experiments/test_code_investigation.py --test usage
uv run python scripts/experiments/test_code_investigation.py --test architecture
uv run python scripts/experiments/test_code_investigation.py --test implementation
```

**独自のコードベースを取り込む:**
```bash
# 任意のリポジトリを取り込み
uv run python scripts/ingest/ingest_codebase.py /path/to/your/repo

# カスタムコレクション名で
uv run python scripts/ingest/ingest_codebase.py . --collection my_project_code

# その後クエリ
uv run python main.py run "認証はどのように機能しますか？" --graph code_investigation
```

### ステート管理

```python
class AgentState(TypedDict):
    query: str                      # 元のユーザークエリ
    web_queries: list[str]          # Web検索用に割り当てられたクエリ
    rag_queries: list[str]          # KB検索用に割り当てられたクエリ
    allocation_strategy: str        # クエリ割り当ての理由
    search_results: Annotated[list[str], operator.add]  # 累積結果
    rag_results: Annotated[list[str], operator.add]     # KB結果
    analyzed_data: Annotated[list[str], operator.add]   # 処理された情報
    report: str                     # 最終統合
    evaluation: str                 # 十分性評価
    loop_count: int                 # 反復カウンター
```

**戦略的割り当て:** プランナーは`chroma_db/`の内容をチェックし、情報ニーズに基づいて`web_queries`と`rag_queries`を個別に設定します。

ステートは**SQLiteチェックポイント**（`langgraph-checkpoint-sqlite`）経由で会話継続のために永続化されます。

## システムの実行

### 前提条件

**uvを使用（推奨）:**

```bash
# 1. uvをインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 依存関係をインストール
uv sync

# 3. （オプション）ローカルモデルを使用する場合、Ollamaが実行されていることを確認
ollama list  # llama3、command-r、nomic-embed-textが表示されるはず
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text
```

**従来のセットアップ:**

```bash
# 1. 仮想環境を作成し起動
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 依存関係をインストール
pip install -e ".[dev]"

# 3. （オプション）必要に応じてOllamaモデルをプル
```

### 主なコマンド

**uvを使用（推奨）:**

```bash
# 基本的な研究クエリ
uv run python main.py run "クエリをここに"

# スレッドIDで会話を継続
uv run python main.py run "フォローアップ質問" --thread-id abc-123

# トラブルシューティングに因果推論グラフを使用
uv run python main.py run "なぜアプリケーションが高レイテンシを経験しているのか？" --graph causal_inference

# バージョン確認
uv run python main.py --version
```

**従来のPython:**

```bash
# 最初にvenvを起動
source .venv/bin/activate

# その後コマンドを実行
python main.py run "クエリをここに"
python main.py run "フォローアップ質問" --thread-id abc-123
python main.py --version
```

### LangGraph Studio（ビジュアルデバッグ）

LangGraph Studioを使用すると、グラフをビジュアルに確認・デバッグできます。

```bash
# ワンクリックで起動
./scripts/studio/start_studio.sh

# 停止
./scripts/studio/stop_studio.sh
# または Ctrl+C
```

**起動後のアクセス:**
- Studio UI: ブラウザが自動的に開きます
- API: `http://127.0.0.1:8123`
- Docs: `http://127.0.0.1:8123/docs`

**詳細ガイド:**
- **[scripts/studio/README.md](scripts/studio/README.md)** - スクリプト使用方法
- **[docs/STUDIO_GUIDE.md](docs/STUDIO_GUIDE.md)** - Studio機能の詳細

### 知識ベースの取り込み

```bash
# 推奨: インテリジェント前処理を伴う本番取り込み
uv run python scripts/ingest/ingest_with_preprocessor.py

# 品質フィルタリング付き（スコア < 0.5のファイルをスキップ）
uv run python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.5

# 診断取り込み（埋め込みの問題のデバッグに使用）
uv run python scripts/ingest/ingest_diagnostic.py

# 検証付き自動クリーン再取り込み
./scripts/ingest/clean_and_reingest.sh
```

**取り込み設定:**
- **ソース:** `documents/`ディレクトリ
- **宛先:** `chroma_db/`（ChromaDBベクトルストア）
- **前処理:** 品質分析を伴う6フェーズパイプライン
- **チャンキング:** ドキュメントごとのスマート戦略選択（目標: 500-1000文字）
- **クリーニング:** 完全 + 近似重複除去、定型文フィルタリング
- **埋め込み:** Ollama経由でnomic-embed-text（768次元）
- **コレクション:** "research_agent_collection"

**前処理機能:**
- 取り込み前のドキュメント品質分析
- インテリジェントチャンキング戦略選択（Recursive、Markdown、Hybrid）
- 重複検出と除去（完全 + 95%類似度閾値）
- 定型文パターン除去
- 品質メトリクスと推奨事項

### 診断ツール

```bash
# ChromaDB探索のためのインタラクティブノートブック
jupyter notebook chroma_explorer.ipynb

# 取り込みログを表示
cat ingestion_diagnostic_*.log

# LangSmith経由で監視
# LangSmith UIでプロジェクト"deep-research-v1-proto"に移動
```

## 開発

### 開発ワークフロー

**重要: 実装完了と見なす前に、常にローカルでCIチェックを実行してください**

機能や修正の実装を終えたら、以下のCIチェックを**自動的に**ローカルで実行してください:

**uvを使用（推奨）:**

```bash
# すべてのCIチェックを実行（GitHub Actionsと同じ）
# uvではvenv起動不要！

# 1. Ruffリンター
echo "=== Ruff Linter ==="
uv run ruff check .

# 2. Ruffフォーマッター
echo "=== Ruff Formatter ==="
uv run ruff format --check .

# 3. Mypyタイプチェッカー
echo "=== Mypy Type Checker ==="
uv run mypy src --no-error-summary

# 4. Pytest
echo "=== Pytest ==="
uv run pytest -v --tb=short
```

**一般的な問題を自動修正:**
```bash
# リンティングエラーを自動修正
uv run ruff check --fix .

# コードを自動フォーマット
uv run ruff format .
```

**従来のPython:**

```bash
# 最初にvenvを起動
source .venv/bin/activate

# チェックを実行
ruff check .
ruff format --check .
mypy src --no-error-summary
pytest -v --tb=short
```

**これが重要な理由:**
- プルリクエストでのCI失敗を防ぐ
- プッシュ前に早期に問題をキャッチ
- コード品質標準を維持
- CIフィードバックループを回避して時間を節約

**実行するタイミング:**
- ✅ 機能実装完了後
- ✅ バグ修正後
- ✅ コミット作成前
- ✅ テストやリンティングが変更の影響を受ける可能性がある場合

### プロジェクト構造

```
scripts/                         # 整理されたユーティリティスクリプト
├── ingest/                      # 知識ベース取り込み
│   ├── ingest.py               # 基本ドキュメント取り込み
│   ├── ingest_diagnostic.py    # 診断付き拡張取り込み
│   ├── ingest_with_preprocessor.py # 本番取り込み（推奨）
│   └── clean_and_reingest.sh   # 自動クリーン再取り込み
├── experiments/                 # 手動実験/検証スクリプト
│   ├── test_gemini_models.py   # Google Geminiモデルテスト
│   ├── test_langsmith_monitoring.py # LangSmith監視テスト
│   ├── test_phase4_dynamic_replanning.py # 動的再計画テスト
│   └── test_code_investigation.py # コード調査グラフテスト
├── utils/                       # ユーティリティスクリプト
│   ├── switch_model_provider.py # Ollama/Geminiプロバイダー切り替え
│   ├── verify_model_provider.py # 現在のプロバイダーを確認
│   ├── update_node_logging.py  # ロギング設定を更新
│   ├── update_causal_nodes_logging.py # 因果ノードロギングを更新
│   └── test_imports.py         # インポート検証
├── visualization/               # 可視化スクリプト
│   ├── visualize_graphs.py     # グラフダイアグラムを生成
│   ├── visualize_causal_graph.py # インタラクティブ因果グラフ可視化
│   └── visualize_studio_trace.py # Studioトレース可視化
└── studio/                      # LangGraph Studio起動スクリプト
    ├── start_studio.sh         # Studioサーバー起動
    └── stop_studio.sh          # Studioサーバー停止

evaluation/                      # 評価フレームワーク
├── evaluate_agent.py           # LangSmith評価ランナー
├── evaluators.py               # ヒューリスティック + LLM評価者
├── datasets/                    # テストデータセット
└── results/                     # 評価結果

src/
├── graphs/                      # ⭐ 複数のグラフワークフロー
│   ├── __init__.py             # グラフレジストリシステム
│   ├── base_graph.py           # グラフ構築用基底クラス
│   ├── deep_research_graph.py  # 階層的研究ワークフロー
│   ├── quick_research_graph.py # 高速シングルパスワークフロー
│   ├── fact_check_graph.py     # 主張検証ワークフロー
│   ├── comparative_graph.py    # サイドバイサイド比較ワークフロー
│   ├── causal_inference_graph.py # 根本原因分析ワークフロー
│   └── code_investigation_graph.py # ⭐ NEW: コードベース分析ワークフロー
├── models.py                    # モデルファクトリー関数（再利用可能）
├── schemas.py                   # Pydanticデータスキーマ（再利用可能）
├── nodes/                       # 処理ノード（グラフ間で再利用可能）
│   ├── planner_node.py
│   ├── searcher_node.py
│   ├── rag_retriever_node.py
│   ├── analyzer_node.py
│   ├── evaluator_node.py
│   ├── synthesizer_node.py
│   ├── master_planner_node.py
│   ├── depth_evaluator_node.py
│   ├── drill_down_generator.py
│   ├── plan_revisor_node.py
│   ├── issue_analyzer_node.py          # 因果推論ノード
│   ├── brainstormer_node.py
│   ├── evidence_planner_node.py
│   ├── causal_checker_node.py
│   ├── hypothesis_validator_node.py
│   ├── causal_graph_builder_node.py
│   ├── root_cause_synthesizer_node.py
│   ├── code_assistant_node.py          # コード検索と分析
│   ├── code_query_analyzer_node.py     # ⭐ NEW: コード調査ノード
│   ├── dependency_analyzer_node.py     # ⭐ NEW
│   ├── code_flow_tracker_node.py       # ⭐ NEW
│   └── code_investigation_synthesizer_node.py # ⭐ NEW
├── prompts/                     # LangChainプロンプトテンプレート（再利用可能）
│   ├── planner_prompt.py
│   ├── analyzer_prompt.py
│   ├── evaluator_prompt.py
│   ├── synthesizer_prompt.py
│   ├── master_planner_prompt.py
│   ├── issue_analyzer_prompt.py         # 因果推論プロンプト
│   ├── brainstormer_prompt.py
│   ├── evidence_planner_prompt.py
│   ├── causal_checker_prompt.py
│   ├── hypothesis_validator_prompt.py
│   ├── root_cause_synthesizer_prompt.py
│   ├── code_assistant_prompt.py         # コードアシスタントプロンプト
│   └── code_investigation_prompts.py    # ⭐ NEW: コード調査プロンプト
└── preprocessor/                # ドキュメント前処理システム
    ├── __init__.py
    ├── document_analyzer.py    # 品質分析 & スコアリング
    ├── chunking_strategy.py    # スマートチャンキング選択
    ├── content_cleaner.py      # 重複除去 & クリーニング
    └── quality_metrics.py      # 検証 & メトリクス
```

**主要な設計原則:**
- **モジュラー:** ノードとプロンプトはすべてのグラフ間で再利用可能
- **拡張可能:** 新しいグラフワークフローを簡単に追加
- **後方互換性:** `src.graph`からインポートする古いコードは引き続き動作
- **レジストリベース:** グラフは自動登録され、`list_graphs()`経由で発見可能

### カスタマイズポイント

**LLMの変更:**
`src/models.py`を編集 - 各エージェントには専用のモデル関数があります:
```python
def get_planner_model():
    return ChatOllama(model="llama3")

def get_evaluation_model():
    return ChatOllama(model="command-r")
```

**プロンプトの変更:**
`src/prompts/`のテンプレートを編集 - 変数注入を伴うLangChain PromptTemplateを使用。変更はそのノードを使用するすべてのグラフに適用されます。

**新しいグラフワークフローの作成:**
1. `src/graphs/my_workflow_graph.py`を作成
2. `BaseGraphBuilder`クラスを拡張:
   ```python
   from src.graphs.base_graph import BaseGraphBuilder

   class MyWorkflowGraphBuilder(BaseGraphBuilder):
       def get_state_class(self) -> type:
           return MyWorkflowState  # ステートスキーマを定義

       def build(self) -> StateGraph:
           workflow = StateGraph(MyWorkflowState)
           # ノード、エッジ、条件付きルーティングを追加...
           return workflow.compile()

       def get_metadata(self) -> dict:
           return {"name": "My Workflow", "description": "..."}
   ```
3. `src/graphs/__init__.py`に登録（`_auto_register_graphs()`に追加）
4. `src/nodes/`の既存ノードを再利用するか、新しいノードを作成

**既存グラフの変更:**
特定のグラフファイルを編集（例: `src/graphs/quick_research_graph.py`）:
- ノードの追加/削除
- ルーティングロジックの変更
- ループ制限の変更
- ステートスキーマの調整

**新しいノードの追加:**
1. `src/nodes/my_node.py`を関数シグネチャで作成: `def my_node(state: dict) -> dict`
2. 必要に応じて`src/prompts/my_prompt.py`を作成
3. 必要に応じて`src/models.py`にモデル関数を追加
4. ノードをインポートして登録することで任意のグラフで使用

**前処理のチューニング:**
`scripts/ingest/ingest_with_preprocessor.py`のパラメータを編集:
```python
min_quality_score=0.5        # 最小品質閾値
similarity_threshold=0.95    # 近似重複閾値
min_content_length=100       # 最小チャンクサイズ
```

**RAGフレンドリーなドキュメントの作成:**
`docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md`のガイドラインに従う:
- セクションあたり500-1500文字を目標
- すべてのヘッダーにトピックを含める
- 一貫した用語を使用
- 最初の使用時に頭字語を定義
- セクションを自己完結型にする

### 依存関係

**uvを使用（推奨）:**

```bash
# すべての依存関係をインストール
uv sync

# dev依存関係を含めてインストール
uv sync --all-extras

# 新しい依存関係を追加
uv add langchain-openai

# dev依存関係を追加
uv add --dev pytest-asyncio

# 依存関係を更新
uv lock --upgrade
```

**従来のpip:**

```bash
# pyproject.tomlからインストール
pip install -e ".[dev]"

# またはrequirements.txtからインストール（レガシー）
pip install -r requirements.txt
```

**注意:** 依存関係は現在`pyproject.toml`で管理されています。古い`requirements.in`と`requirements.txt`ファイルは後方互換性のために保持されていますが、新しい開発には推奨されません。

## 重要な実装詳細

### 並列実行と戦略的割り当て

Searcher（Tavily）とRAG Retriever（ChromaDB）は**同時に**実行されますが、**異なるクエリセット**を使用します:
```python
workflow.add_edge("planner", "searcher")
workflow.add_edge("planner", "rag_retriever")
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("rag_retriever", "analyzer")
```

**戦略的割り当てプロセス:**
1. Plannerは`check_kb_contents()`を使用してKBの内容を確認:
   - `chroma_db/`の存在を確認
   - 総チャンク数をカウント
   - ドキュメントをサンプリングして内容を理解
2. LLMがクエリを戦略的に割り当て:
   - **RAGクエリ:** ドメイン固有、内部ドキュメント、確立された概念
   - **Webクエリ:** 現在の出来事、一般知識、外部参照
3. クエリリストが空の場合、ノードは実行をスキップ（APIコールを節約）

**割り当て例:**
- クエリ: "当社の認証システムはOAuth2ベストプラクティスと比較してどのように機能しますか？"
- KBステータス: 内部認証ドキュメントを含む
- 結果: 3つのRAGクエリ（内部実装） + 2つのWebクエリ（OAuth2ベストプラクティス）

### 反復的改善

Evaluatorがループ継続を制御:
```python
def router(state: AgentState) -> Literal["synthesizer", "planner"]:
    if state["loop_count"] >= 2:
        return "synthesizer"  # 2回の反復後に強制終了
    if "sufficient" in state.get("evaluation", "").lower():
        return "synthesizer"
    return "planner"  # フィードバックで改善
```

### ステート蓄積

累積集約のためのアノテーションパターンを使用:
```python
from typing import Annotated
import operator

search_results: Annotated[list[str], operator.add]
# 各ノードがリストに追加; ステートは自動的にマージ
```

### 構造化出力

ノードは`.with_structured_output()`でPydanticスキーマを使用:
```python
from src.schemas import StrategicPlan

planner_llm = get_planner_model().with_structured_output(StrategicPlan)
# StrategicPlanスキーマは以下を保証:
#   - rag_queries: List[str]
#   - web_queries: List[str]
#   - strategy: str (割り当ての理由)
# 型安全で検証された出力を保証
```

## 監視と可観測性

### LangSmith統合

**環境変数:**
```bash
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="<your-key>"
LANGCHAIN_PROJECT="deep-research-v1-proto"
```

**トレースの表示:**
1. LangSmithにログイン
2. プロジェクト"deep-research-v1-proto"に移動
3. トレースをクリックしてノードごとの入出力を含む完全な実行グラフを表示

### 埋め込み品質診断

**`chroma_explorer.ipynb`のSection 2.2**は包括的なチェックを提供:
- 重複検出
- 多様性分析（次元にわたる分散）
- ペアワイズ類似度分布
- ビジュアル診断（ヒストグラム、分散プロット）

**健全な埋め込み:**
- チャンクサイズの中央値: 500-800文字
- 重複率: <5%
- 品質スコア: >0.7
- 95%分散にPCAが20-40成分必要
- 平均コサイン類似度: 0.3-0.8

**問題のある埋め込み:**
- チャンクサイズの中央値: <200文字（チャンクが小さすぎる）
- 重複率: >15%（繰り返しが多すぎる）
- 品質スコア: <0.5（品質が悪い）
- 99%分散にPCAが1-10成分のみ必要（致命的 - 多様性の欠如）
- 平均類似度 > 0.95（ドキュメントが似すぎている）

**一般的な根本原因:**
- UnstructuredLoaderの過剰分割 → 前処理を使用
- 繰り返しヘッダー/フッター → 定型文除去を有効化
- ソースドキュメントの小さなセクション → `docs/knowledge-base/writing-docs.md`に従う

**解決策:** 常に本番取り込みには`scripts/ingest/ingest_with_preprocessor.py`を使用。

## 設定ファイル

**.env** (LangSmith + Web検索に必要):
```bash
# LangSmith（監視/トレーシング）
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="<langsmith-key>"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Web検索プロバイダー（自動フォールバック付き複数プロバイダー）
SEARCH_PROVIDER_PRIORITY="tavily,duckduckgo"  # 優先順位
TAVILY_API_KEY="<tavily-key>"  # オプション: 高品質検索（月1,000回無料）
# BRAVE_API_KEY="<brave-key>"  # オプション: 代替プロバイダー（月2,000回無料）

# モデルプロバイダー
MODEL_PROVIDER="ollama"  # またはGeminiには"google"
# GOOGLE_API_KEY="<google-key>"  # MODEL_PROVIDER="google"の場合必須
```

**Web検索プロバイダー:**
- **Tavily**（推奨）: LLM向けに最適化された高品質検索。無料ティア: 月1,000回検索。APIキー必要。
- **DuckDuckGo**（無料）: APIキー不要の無料検索。組み込みフォールバック。
- **Brave Search**（オプション）: プライバシー重視の検索。無料ティア: 月2,000回検索。（近日公開）

**自動フォールバック**: Tavilyが失敗した場合（API制限到達、無効なキーなど）、システムは自動的にDuckDuckGoにフォールバック。

**ヘルスチェック:**
```bash
python scripts/utils/check_search_providers.py
```

**詳細ガイド**: [docs/WEB_SEARCH_PROVIDERS.md](docs/WEB_SEARCH_PROVIDERS.md)

**注意:** `.env`は実際のキーでgitにチェックインされています（本番環境ではベストプラクティスではありません）。

## 既知の問題と制限

- **最大2回の反復:** 無限ループを防ぐためルーターにハードコード
- **テストカバレッジなし:** pytestはインストール済みだがテストは未作成
- **プリントベースのロギング:** 本番環境では構造化ロギングを使用

## 追加リソース

**ドキュメントエントリーポイント:**
- **[docs/README.md](docs/README.md)** - すべてのドキュメントはここから開始

**はじめに:**
- **docs/getting-started/installation.md** - セットアップと依存関係
- **docs/getting-started/quick-start.md** - 5分で最初のクエリ
- **docs/getting-started/model-providers.md** - OllamaとGemini設定

**アーキテクチャ:**
- **docs/architecture/system-overview.md** - 完全なシステムアーキテクチャ
- **docs/architecture/multi-graph-workflows.md** - 利用可能なワークフローグラフ

**知識ベース:**
- **docs/knowledge-base/rag-guide.md** - 完全なRAG設定ガイド
- **docs/knowledge-base/writing-docs.md** - ドキュメント作成のベストプラクティス
- **docs/knowledge-base/quality-evaluation.md** - 品質メトリクスと評価
- **docs/knowledge-base/preprocessor.md** - ドキュメント前処理の使用方法

**開発:**
- **docs/development/evaluation-guide.md** - LangSmith評価フレームワーク
- **docs/development/logging-debugging.md** - ロギングとデバッグガイド
- **docs/development/creating-graphs.md** - カスタムワークフローの構築
- **docs/development/ci-cd.md** - CI/CD統合

**ツールと分析:**
- **chroma_explorer.ipynb** - データベース分析用インタラクティブノートブック
- **scripts/ingest/ingest_with_preprocessor.py** - 本番取り込み
- **scripts/visualization/visualize_graphs.py** - グラフダイアグラム生成
- **evaluation/evaluate_agent.py** - LangSmith評価ランナー

---

# 🧠 認知拡張プロトコル（パーソナルアシスタント設定）

## コアアイデンティティとミッション
Claude Codeはこのコードベースを扱う際、**ユーザーの認知の拡張**として機能します。
**シニアソフトウェアアーキテクト**として優先:

1. **認知的明瞭性**: 認知負荷を減らす - *何*だけでなく*なぜ*を説明
2. **スケーラビリティ**: クイックハックよりも堅牢でスケーラブルなソリューションを優先（プロトタイピング時を除く）
3. **コンテキスト認識**: コード変更からより広い目標を常に推測

## ガイドライン
- **言語**: 任意の言語で読むが、特に指示がない限り**日本語で返信**
- **出力形式**: Markdownを使用。要約時は可読性のため箇条書きを使用
- **ツール使用**: `gh`（GitHub CLI）と標準Unixツールへの完全アクセス

## ⚡ カスタムコマンド

### `/comp-pr [id1] [id2]` - プルリクエストの比較
**目標**: 2つの実装を比較する中立的な審判として機能

**ステップ**:
1. `gh pr view [id1]`と`gh pr view [id2]`を実行して説明を取得
2. `gh pr diff [id1]`と`gh pr diff [id2]`を実行してコード変更を取得
3. 以下に基づいて分析:
   - **アーキテクチャ適合性**: どちらが現在のシステム設計により適合するか？
   - **複雑性**: どちらが保守が簡単か？
   - **エッジケース**: エラー処理を誰かが見逃していないか？
4. **出力**: 比較表と最終推奨を生成（「PR Aを採用するがPR BからXを借用」）

**例**:
```
ユーザー: /comp-pr 5 7
Claude: [両方のPRを取得、差分を分析、比較表を生成]
```

### `/review` - 深いコードレビュー
**目標**: 現在の変更にセキュリティと品質監査を実行

**ステップ**:
1. `git diff --staged`（または現在変更されたファイル）を実行
2. 以下をチェック:
   - セキュリティ脆弱性（シークレット、インジェクションリスク）
   - パフォーマンスボトルネック（N+1クエリ、重いループ）
   - 命名の一貫性
3. **出力**: 優先順位付けされた問題リスト（Critical / Warning / Suggestion）

**例**:
```
ユーザー: /review
Claude:
Critical:
  - line 45: 設定でAPIキーが露出
Warning:
  - line 120: ループ内のN+1クエリ
Suggestion:
  - line 67: より説明的な変数名の使用を検討
```

### `/commit` - スマートコミットメッセージ
**目標**: 変更に基づいて従来型コミットメッセージを生成

**ステップ**:
1. `git diff --staged`を分析
2. **Conventional Commits**形式に従ったコミットメッセージを生成:
   - `feat: ...` 新機能用
   - `fix: ...` バグ修正用
   - `refactor: ...` コードリストラクチャリング用
   - `docs: ...` ドキュメンテーション用
3. `git commit`実行前にユーザー承認を待つ

**例**:
```
ユーザー: /commit
Claude:
提案されたコミットメッセージ:
feat(code-investigation): 複数リポジトリ比較サポートを追加

- コード調査グラフに比較モードを追加
- 比較専用プロンプトを使用するようsynthesizerを更新
- マルチリポジトリクエリ用に--collectionsフラグをサポート

このコミットで進めますか？ (yes/no)
```

### `/obsidian` - 知識同期
**目標**: ユーザーのObsidianノート用に現在のセッションを要約

**ステップ**:
1. 会話とコード変更を確認
2. 以下を含むMarkdownブロックを出力:
   - **トピック**: 1行の要約
   - **主要な決定**: 何が決定され、なぜか
   - **後で考えること**: このセッションから生まれた哲学的または技術的な質問

**出力例**:
```markdown
## セッション: 複数リポジトリコード比較実装

**トピック**: コード調査ワークフローに複数リポジトリ比較を追加

**主要な決定**:
- 分離のためリポジトリごとに個別のChromaDBコレクションを使用
- `--collections`フラグ経由で比較モードを実装
- synthesizer用に専用の比較プロンプトを作成
- レジストリがすべての取り込みリポジトリを追跡

**後で考えること**:
- 3つ以上のリポジトリの比較をサポートすべきか？
- コレクション間で異なる埋め込みモデルをどう扱うか？
- 依存関係に基づいて関連コードベースを自動検出できるか？

**変更されたファイル**:
- src/graphs/code_investigation_graph.py
- src/nodes/code_investigation_synthesizer_node.py
- main.py
- docs/CODEBASE_MANAGEMENT.md
```

## 🚀 プロトタイピングモード（ユーザー設定）

### 小規模タスク
単一のPythonスクリプトまたはJupyterノートブックスニペットを提供

### 中規模タスク
コーディング前に「実装設計仕様」を提供:
```markdown
## 設計仕様: [機能名]

**目標**: [1文の目的]

**アプローチ**:
1. [高レベルステップ1]
2. [高レベルステップ2]

**変更するファイル**:
- file1.py: [どんな変更]
- file2.py: [どんな変更]

**トレードオフ**:
- オプションA: [長所/短所]
- オプションB: [長所/短所]

**推奨**: オプションB [理由]のため
```

### 大規模タスク
最初に技術スタック選択を含むロードマップを提供:
```markdown
## ロードマップ: [プロジェクト名]

**フェーズ1**: 基盤
- [ ] データベーススキーマ設計
- [ ] API構造
- [ ] 認証レイヤー

**フェーズ2**: コア機能
- [ ] 機能X
- [ ] 機能Y

**技術スタック選択**:
- DB: PostgreSQL vs MongoDB
  - 推奨: PostgreSQL（理由...）
- API: REST vs GraphQL
  - 推奨: REST（理由...）
```

---

## GitHub PR比較例

このリポジトリで`/comp-pr`コマンドを試すには:

```bash
# 最近のPRをリスト
gh pr list

# 2つのPRを比較
# 使用方法: /comp-pr [pr-番号-1] [pr-番号-2]
```

比較は以下を分析します:
- コード変更とアーキテクチャへの影響
- 複雑性と保守性
- テストカバレッジとエッジケース
- どのアプローチがTest-Smithのマルチグラフアーキテクチャにより適合するか
