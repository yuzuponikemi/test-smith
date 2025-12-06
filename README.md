# Test-Smith: マルチエージェント研究アシスタント

高度な知識ベース管理とマルチエージェントワークフローを組み合わせた、LangGraphベースの研究アシスタントです。深い調査と包括的なレポート生成を実現します。

## 概要

Test-Smithは、専門化されたAIエージェントがステートベースのワークフローを通じて協調する「Plan-and-Execute」戦略を実装しています。システムは以下を組み合わせています:

- **マルチエージェントアーキテクチャ**: Planner、Searcher、RAG Retriever、Analyzer、Evaluator、Synthesizer
- **インテリジェント知識ベース**: 高度な前処理を備えたChromaDBベクトルストア
- **品質優先アプローチ**: 包括的なドキュメント品質分析とメトリクス
- **柔軟なLLMサポート**: Google Gemini API（デフォルト）またはローカルOllamaモデル
- **可観測性**: LangSmithによる完全なトレーシング

## 主な機能

### マルチエージェントワークフロー

1. **Strategic Planner（戦略プランナー）** - RAGとWeb検索の間でクエリを賢く割り当て
   - 知識ベースの内容と利用可能性を確認
   - ドメイン固有のクエリをRAG検索に割り当て
   - 現在の/外部のクエリをWeb検索に割り当て
   - Evaluatorからのフィードバックに基づいて戦略を適応

2. **Searcher（検索者）** - Tavily API経由で戦略的に割り当てられたWeb検索を実行
3. **RAG Retriever（RAG検索者）** - 戦略的に割り当てられたクエリを使用して関連チャンクを取得
4. **Analyzer（分析者）** - 複数のソースからの結果をマージし要約
5. **Evaluator（評価者）** - 情報の十分性と品質を評価
6. **Synthesizer（統合者）** - 包括的な最終レポートを生成

**主要なイノベーション:** プランナーは両方のソースに同じクエリを送る代わりに、**戦略的なクエリ割り当て**を実行します。これによりAPIコールを節約し、関連性を向上させ、知識ベースの内容に基づいて動的に適応します。システムは評価結果に基づく条件付きルーティングで反復的に実行されます（最大2回の反復）。

### インテリジェントドキュメント前処理

知識ベースシステムには高度な前処理パイプラインが含まれています:

**ドキュメントアナライザー:**
- 品質スコアリング（0-1スケール）
- 言語検出（英語、日本語など）
- 構造分析（Markdown、PDF、プレーンテキスト）
- 自動問題検出と推奨

**スマートチャンキング:**
- ドキュメントごとの戦略選択（Recursive、Markdown、Hybrid）
- コンテンツタイプに基づく適応的なチャンクサイジング
- 言語対応調整（例：日本語は1.2倍）
- ターゲット：チャンクあたり500-1000文字

**コンテンツクリーニング:**
- 完全重複除去（MD5ハッシュベース）
- 近似重複検出（95%類似度閾値）
- 定型文パターン除去（繰り返しヘッダー/フッター）
- サイズフィルタリング（100文字未満のチャンクを除去）

**品質メトリクス:**
- チャンクサイズ分布分析
- 一意性比率追跡（目標 >95%）
- 語彙多様性測定（目標 25-50%）
- 埋め込み品質のためのPCA分散分析

## クイックスタート

### 前提条件

1. **Python 3.8+**
2. **LLMプロバイダー** - 以下から1つ選択:
   - **Google Gemini API**（推奨、デフォルト） - [Google AI Studio](https://makersuite.google.com/app/apikey)で無料ティアが利用可能
   - **Ollama**（ローカルモデル） - [ollama.ai](https://ollama.ai/)からインストール

**Ollamaを使用する場合（ローカルモデル）:**
```bash
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text
```

**Geminiを使用する場合（クラウドAPI）:**
```bash
# Google AI Studioから APIキーを取得するだけです
# ローカルモデルのインストールは不要！
```

### インストール

**uvを使用（推奨）**

```bash
# リポジトリをクローン
git clone <repository-url>
cd test-smith

# uvをインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境を作成し依存関係をインストール
uv sync --all-extras
```

**uvを使う理由は？**
- ⚡ **pipより10-100倍高速**
- 🔒 **uv.lockによる再現可能なビルド**
- 🎯 **より良い依存関係解決**
- 💾 **グローバルキャッシュ**で高速インストール
- ✨ **`uv run`で手動venv起動不要**

**完全なuvの使い方ガイドは[.github/UV_GUIDE.md](.github/UV_GUIDE.md)をご覧ください。**

<details>
<summary>レガシー: pipを使用（非推奨）</summary>

**⚠️ 注意:** pipサポートは非推奨です。より良いパフォーマンスと再現性のためuvを使用してください。

```bash
# リポジトリをクローン
git clone <repository-url>
cd test-smith

# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係をインストール
pip install -e ".[dev]"
```
</details>

### 設定

ルートディレクトリに`.env`ファイルを作成:

```bash
# モデルプロバイダー（"gemini"または"ollama"を選択）
MODEL_PROVIDER="gemini"  # デフォルト: Google Gemini APIを使用

# Google Gemini APIキー（MODEL_PROVIDER=geminiの場合必須）
# APIキーの取得先: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY="your-google-api-key"

# Tavily（Web検索用 - 必須）
TAVILY_API_KEY="your-tavily-api-key"

# LangSmith（オプション - 可観測性用）
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-api-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# 構造化ロギング（オプション）
STRUCTURED_LOGS_JSON="false"  # 開発用はfalse、本番用はtrue
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

**Google Geminiを使用（デフォルト）:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey)から無料APIキーを取得
2. `.env`ファイルで`MODEL_PROVIDER=gemini`を設定
3. `GOOGLE_API_KEY`を追加
4. 依存関係は`uv sync`で既にインストール済み

**ローカルOllamaモデルを使用:**
1. [Ollama](https://ollama.ai/)をインストール
2. モデルをプル: `ollama pull llama3 && ollama pull command-r`
3. `.env`ファイルで`MODEL_PROVIDER=ollama`を設定

### GitHub Actionsのセットアップ

このリポジトリにはGitHub Actionsによる自動テストが含まれています。CI/CD用のAPIキーを設定するには:

#### ステップ1: リポジトリ設定に移動

1. GitHubリポジトリに移動
2. **Settings**タブをクリック
3. 左サイドバーで、**Secrets and variables** → **Actions**をクリック

#### ステップ2: リポジトリシークレットを追加

**New repository secret**をクリックし、以下のシークレットを追加:

**必須シークレット:**

| シークレット名 | 説明 | 取得先 |
|------------|-------------|--------------|
| `GOOGLE_API_KEY` | Google Gemini APIキー | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `TAVILY_API_KEY` | Tavily Web検索APIキー | [Tavilyダッシュボード](https://tavily.com/) |

**オプションのシークレット:**

| シークレット名 | 説明 | 取得先 |
|------------|-------------|--------------|
| `LANGCHAIN_API_KEY` | LangSmith可観測性キー | [LangSmith](https://smith.langchain.com/) |

#### ステップ3: 各シークレットを追加

各シークレットについて:
1. **New repository secret**をクリック
2. **Name**を入力（例: `GOOGLE_API_KEY`）
3. **Value**に実際のAPIキーを貼り付け
4. **Add secret**をクリック

#### ステップ4: ワークフローを確認

1. コードをプッシュまたはプルリクエストを作成
2. リポジトリの**Actions**タブに移動
3. "Test Graphs with Gemini"ワークフローが実行されているのが確認できます
4. ワークフローをクリックして詳細ログを表示

#### 手動ワークフロートリガー

カスタムパラメータでワークフローを手動トリガーできます:

1. GitHubリポジトリに移動
2. **Actions**タブをクリック
3. 左サイドバーから**"Test Graphs with Gemini"**を選択
4. **"Run workflow"**ボタン（右上）をクリック
5. テストパラメータを設定:

| パラメータ | 説明 | デフォルト | オプション |
|-----------|-------------|---------|---------|
| **graph_type** | テストするグラフワークフロー | `quick_research` | quick_research, deep_research, fact_check, comparative |
| **test_query** | カスタムテストクエリ | "What is Python programming language?" | 任意の文字列 |
| **run_full_suite** | すべてのグラフコンパイルテストを実行 | `true` | true, false |
| **python_version** | テストするPythonバージョン | `3.11` | 3.10, 3.11, 3.12 |

6. **"Run workflow"**をクリックしてテスト開始

**使用例:**
- **クイックテスト**: `run_full_suite=false`、`graph_type=quick_research`、カスタムクエリ
- **特定グラフのテスト**: `graph_type=comparative`を選択、比較クエリを提供
- **Python互換性テスト**: `python_version`を変更して異なるPythonバージョンをテスト
- **完全検証**: デフォルトのまま`run_full_suite=true`

**ワークフロー機能:**
- ✅ すべてのワークフロータイプのグラフコンパイルをテスト
- ✅ Geminiモデル初期化を検証
- ✅ 任意のグラフワークフローでカスタマイズ可能なテストクエリを実行
- ✅ 環境設定を検証
- ✅ テスト出力をアーティファクトとしてアップロード
- ⚡ 軽量な`requirements-ci.txt`を使用して高速CIビルド（重いMLパッケージを除外）
- 🎮 カスタマイズ可能なパラメータ（グラフタイプ、クエリ、Pythonバージョン）での手動トリガー

**GitHub Actionsのトラブルシューティング:**
- "GOOGLE_API_KEY not set"でワークフローが失敗する場合、シークレットが正しく追加されているか確認
- シークレット名は大文字小文字を区別し、正確に一致する必要があります
- シークレットは暗号化され、作成後は表示できません
- シークレットを更新するには、同じ名前で新しいものを作成します

## 使用方法

### 研究クエリの実行

**uvを使用（推奨）:**

```bash
# 基本的な研究クエリ
uv run python main.py run "AI創薬の最新の進歩は？"

# スレッドIDを使用して会話を継続
uv run python main.py run "フォローアップ質問" --thread-id abc-123

# バージョン確認
uv run python main.py --version
```

<details>
<summary>レガシー: 従来のPythonを使用（非推奨）</summary>

**⚠️ 注意:** 手動のvenv起動は非推奨です。よりクリーンなワークフローのため`uv run`を使用してください。

```bash
# 最初に仮想環境を起動
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# その後コマンドを実行
python main.py run "AI創薬の最新の進歩は？"
python main.py run "フォローアップ質問" --thread-id abc-123
python main.py --version
```
</details>

### テストの実行

Test-Smithにはノード、グラフ、統合テストを含む包括的なテストスイートが含まれています。

**uvを使用（推奨）:**

```bash
# すべてのテストを実行
uv run pytest

# ユニットテストのみ実行
uv run pytest tests/unit -v

# 特定のテストファイルを実行
uv run pytest tests/unit/test_nodes/test_planner_node.py -v

# カバレッジレポート付きでテスト実行
uv run pytest --cov=src --cov-report=html

# 遅い/API依存テストを除外してテスト実行
uv run pytest -m "not slow and not requires_api"
```

<details>
<summary>レガシー: 従来のPythonを使用（非推奨）</summary>

**⚠️ 注意:** 手動のvenv起動は非推奨です。代わりに`uv run`を使用してください。

```bash
# 最初に仮想環境を起動
source .venv/bin/activate

# その後テストを実行
pytest
pytest tests/unit -v
pytest --cov=src --cov-report=html
```
</details>

**テスト構造:**
- `tests/unit/test_nodes/` - 個別ノードのユニットテスト
- `tests/unit/test_graphs/` - グラフコンパイルと構造のテスト
- `tests/integration/` - エンドツーエンドワークフローテスト（近日公開）
- `tests/conftest.py` - 共有フィクスチャとモックLLM実装

**GitHub Actions:**
プルリクエストで自動的にテストが実行されます。Actionsタブでテスト結果を確認できます。

### 知識ベース管理

#### ドキュメントの取り込み

**本番取り込み（推奨）:**
```bash
# documents/ディレクトリにドキュメントを配置
# インテリジェント前処理パイプラインを実行
uv run python scripts/ingest/ingest_with_preprocessor.py

# 品質フィルタリング付き（スコア < 0.5のファイルをスキップ）
uv run python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.5

# 必要に応じて特定のクリーニングステップを無効化
uv run python scripts/ingest/ingest_with_preprocessor.py --disable-deduplication
```

**診断取り込み（デバッグ用）:**
```bash
# 埋め込みの問題を調査するために使用
uv run python scripts/ingest/ingest_diagnostic.py
```

**自動クリーン再取り込み:**
```bash
# 既存のデータベースをバックアップし再取り込み
./scripts/ingest/clean_and_reingest.sh
```

#### 知識ベースの分析

```bash
# 対話型分析用Jupyterノートブックを起動
uv run jupyter notebook chroma_explorer.ipynb
```

**主要なノートブックセクション:**
- **Section 2.1**: データベースコンテンツの内訳（ソース、チャンク数）
- **Section 2.2**: 埋め込み品質診断（重複、多様性）
- **Section 3.0**: PCA分散分析（次元性チェック）
- **Section 3.1**: ホバーツールチップ付き対話型2D可視化
- **Section 3.2**: 対話型4Dペアプロット

**健全な知識ベースの指標:**
- チャンクサイズの中央値: 500-800文字
- 重複率: <5%
- 品質スコア: >0.7
- 95%分散のためのPCA成分: 20-40

## RAGフレンドリーなドキュメントの作成

検索品質を最大化するために、知識ベースドキュメントを作成する際は以下のベストプラクティスに従ってください:

### 主要原則

1. **自己完結型セクション** - 各セクションは独立して意味をなすべき
2. **最適な長さ** - セクションあたり500-1500文字を目標
3. **説明的なヘッダー** - すべてのヘッダーにメイントピックを含める
4. **一貫した用語** - 同じ概念には同じ用語を使用
5. **頭字語を定義** - 最初の使用時に「完全な用語（頭字語）」パターンを使用

### 例: 悪い vs 良い

❌ **悪い - RAG非対応:**
```markdown
## 設定

設定ファイルを編集。パラメータを設定。
```
- 短すぎる（コンテキストなし）
- 一般的なヘッダー
- 曖昧な参照

✅ **良い - RAG対応:**
```markdown
## PostgreSQL接続設定

/etc/postgresql/14/main/postgresql.confにあるpostgresql.confファイルで
PostgreSQLデータベース接続設定を構成します。

設定する主要な設定:
- listen_addresses: リモート接続の場合は'0.0.0.0'に設定
- port: デフォルトのPostgreSQLポートは5432
- max_connections: 最大同時接続数（デフォルト: 100）

変更後はPostgreSQLを再起動: sudo systemctl restart postgresql
```
- 適切な長さ（自己説明的）
- トピック固有のヘッダー
- 完全で独立した情報

### ドキュメントガイド

- **[RAGフレンドリーなドキュメントの作成](docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md)** - 包括的な執筆ベストプラクティス
- **[ドキュメント設計評価](docs/DOCUMENT_DESIGN_EVALUATION.md)** - 再現可能な品質メトリクス
- **[RAGデータ準備ガイド](docs/RAG_DATA_PREPARATION_GUIDE.md)** - RAG概念の深堀り

## プロジェクト構造

```
test-smith/
├── main.py                          # エントリーポイントとCLI
├── pytest.ini                       # Pytest設定
├── chroma_explorer.ipynb            # 分析ノートブック
├── PREPROCESSOR_QUICKSTART.md       # クイックスタートガイド
├── tests/                           # テストスイート
│   ├── conftest.py                 # 共有フィクスチャとモック
│   ├── unit/                        # ユニットテスト
│   │   ├── test_nodes/             # ノードユニットテスト
│   │   ├── test_graphs/            # グラフテスト
│   │   └── test_preprocessor/      # 前処理テスト
│   └── integration/                 # 統合テスト
├── scripts/                         # 整理されたユーティリティスクリプト
│   ├── ingest/                      # 知識ベース取り込み
│   │   ├── ingest.py               # 基本ドキュメント取り込み
│   │   ├── ingest_diagnostic.py    # 診断取り込み
│   │   ├── ingest_with_preprocessor.py # 本番取り込み
│   │   └── clean_and_reingest.sh   # 自動クリーン再取り込み
│   ├── testing/                     # テストスクリプト
│   │   ├── test_gemini_models.py
│   │   ├── test_langsmith_monitoring.py
│   │   └── test_phase4_dynamic_replanning.py
│   ├── utils/                       # ユーティリティスクリプト
│   │   ├── switch_model_provider.py
│   │   ├── verify_model_provider.py
│   │   └── update_node_logging.py
│   └── visualization/               # 可視化スクリプト
│       ├── visualize_graphs.py     # グラフダイアグラム生成
│       └── visualize_causal_graph.py
├── evaluation/                      # 評価フレームワーク
│   ├── evaluate_agent.py           # LangSmith評価ランナー
│   ├── evaluators.py               # ヒューリスティック + LLM評価者
│   ├── datasets/                    # テストデータセット
│   └── results/                     # 評価結果
├── docs/                            # ドキュメント
│   ├── system-overview.md           # アーキテクチャの詳細
│   ├── GEMINI.md                    # Gemini API統合
│   ├── RAG_DATA_PREPARATION_GUIDE.md
│   ├── WRITING_RAG_FRIENDLY_DOCUMENTATION.md
│   └── DOCUMENT_DESIGN_EVALUATION.md
├── src/                             # ソースコード
│   ├── graph.py                     # ワークフロー定義
│   ├── models.py                    # LLM設定
│   ├── schemas.py                   # データスキーマ
│   ├── graphs/                      # 複数のグラフワークフロー
│   │   ├── deep_research_graph.py
│   │   ├── quick_research_graph.py
│   │   ├── fact_check_graph.py
│   │   ├── comparative_graph.py
│   │   └── causal_inference_graph.py
│   ├── nodes/                       # エージェントノード
│   │   ├── planner_node.py
│   │   ├── searcher_node.py
│   │   ├── rag_retriever_node.py
│   │   ├── analyzer_node.py
│   │   ├── evaluator_node.py
│   │   └── synthesizer_node.py
│   ├── prompts/                     # プロンプトテンプレート
│   └── preprocessor/                # 前処理パイプライン
│       ├── document_analyzer.py     # 品質分析
│       ├── chunking_strategy.py     # スマートチャンキング
│       ├── content_cleaner.py       # 重複除去
│       └── quality_metrics.py       # 検証
├── documents/                       # ソースドキュメント（gitignore）
└── chroma_db/                       # ベクトルデータベース（gitignore）
```

## 監視と可観測性

### 構造化ロギング

Test-Smithは機械可読でクエリ可能なロギングのため`structlog`を使用します。

**機能:**
- **コンテキストロギング**: query、node、thread_idの自動バインディング
- **パフォーマンスメトリクス**: 操作の自動タイミング
- **開発フレンドリー**: 人間可読なコンソール出力
- **本番対応**: ログ集約のためのJSON出力

**設定**（`.env`内）:
```bash
STRUCTURED_LOGS_JSON="false"  # 開発用はfalse、本番用はtrue
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

**ログ出力例**（開発）:
```
2025-01-24T10:30:45.123Z [info] node_start node=planner query="What is TDD?" model=gemini/gemini-2.5-flash
2025-01-24T10:30:45.456Z [info] operation_complete operation=kb_contents_check duration_ms=123.45
2025-01-24T10:30:47.891Z [info] query_allocation rag_query_count=2 web_query_count=1 strategy="Use RAG for basics"
2025-01-24T10:30:47.892Z [info] node_end node=planner execution_time_ms=2769.12 status=success
```

**メリット:**
- パフォーマンスボトルネックの追跡
- 豊富なコンテキストでのデバッグ
- クエリパターンの分析
- エラー率の監視

📖 **完全ガイド**: [docs/STRUCTURED_LOGGING.md](docs/STRUCTURED_LOGGING.md)

### LangSmithトレーシング

1. LangSmithダッシュボードにログイン
2. プロジェクト"deep-research-v1-proto"を選択
3. 詳細な実行トレースを表示:
   - ノードごとの実行フロー
   - 各エージェントの入出力
   - トークン使用量とレイテンシ
   - エラー追跡

### 知識ベース品質監視

**各取り込み後にチェック:**

```bash
# 取り込みログを確認
cat ingestion_preprocessed_*.log

# 以下のセクションを確認:
# - DOCUMENT ANALYSIS REPORT（品質スコア）
# - CHUNKING STATISTICS（チャンク分布）
# - CONTENT CLEANING STATISTICS（重複率）
# - QUALITY METRICS REPORT（全体品質スコア）
```

**月次評価:**

1. 取り込みを実行: `python scripts/ingest/ingest_with_preprocessor.py`
2. ログファイルからメトリクスを抽出
3. ノートブックでPCA分析を実行（Section 3.0）
4. スコアを記録し進捗を追跡
5. 弱い領域を特定し修正

## カスタマイゼーション

### LLMの変更

**GeminiとOllamaの切り替え:**

`.env`ファイルの`MODEL_PROVIDER`を変更するだけです:

```bash
# Google Geminiを使用（デフォルト）
MODEL_PROVIDER=gemini

# またはローカルOllamaモデルを使用
MODEL_PROVIDER=ollama
```

**Geminiモデルのカスタマイズ:**

`src/models.py`を編集してどのGeminiモデルを使用するか変更:

```python
# デフォルトのGeminiモデル
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"  # 高速で効率的
ADVANCED_GEMINI_MODEL = "gemini-1.5-pro"   # 複雑なタスク用

# または最新の実験的機能にgemini-2.0-flash-expを使用
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash-exp"
```

**エージェントごとの温度カスタマイズ:**

```python
def get_planner_model():
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.7  # この値を調整（0.0-1.0）
    )
```

### エージェントの変更

`src/prompts/`のプロンプトを編集:

```python
# src/prompts/planner_prompt.py
PLANNER_PROMPT = PromptTemplate(
    template="ここにカスタムプロンプト...",
    input_variables=["query", "feedback"]
)
```

### 前処理のチューニング

`scripts/ingest/ingest_with_preprocessor.py`を編集:

```python
ingestion = PreprocessedIngestion(
    min_quality_score=0.5,              # 品質閾値
    enable_near_duplicate_detection=True,
    enable_boilerplate_removal=True
)

cleaner = ContentCleaner(
    similarity_threshold=0.95,          # 近似重複閾値
    min_content_length=100              # 最小チャンクサイズ
)
```

## トラブルシューティング

### 検索品質が悪い

**症状:**
- RAG検索者が無関係なチャンクを返す
- 回答にドメイン固有の知識が欠けている
- 異なるクエリに対して同じチャンクが検索される

**診断:**
```bash
# 診断取り込みを実行
python scripts/ingest/ingest_diagnostic.py

# ログで以下を確認:
# - 高い重複率（>15%）
# - 小さいチャンクサイズの中央値（<300文字）
# - 低い品質スコア（<0.5）
```

**解決策:**
1. ソースドキュメントを確認（`WRITING_RAG_FRIENDLY_DOCUMENTATION.md`に従う）
2. 前処理で再取り込み: `./scripts/ingest/clean_and_reingest.sh`
3. ノートブックでPCA分析を確認 - 95%分散に20-40成分が必要なはず

### 「すべての埋め込みが似ている」問題

**症状:**
- PCAが99%分散に1-10成分を示す
- 可視化ですべての点が一緒にクラスター化されている
- 平均コサイン類似度 >0.95

**根本原因:**
- チャンクが小さすぎる（UnstructuredLoaderの過剰分割）
- 高い重複（繰り返しヘッダー/フッター）
- 低いコンテンツ多様性

**解決策:**
これらの問題をすべて自動的に解決する`scripts/ingest/ingest_with_preprocessor.py`を使用。

### Ollama接続エラー

```bash
# Ollamaが実行されているか確認
ollama list

# モデルがプルされているか確認
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text

# 埋め込みをテスト
ollama run nomic-embed-text
```

## ドキュメント

- **[システム概要](docs/system-overview.md)** - 包括的なアーキテクチャガイド
- **[エージェントグラフ](docs/agent_graph.md)** - ワークフロードキュメント
- **[RAGデータ準備](docs/RAG_DATA_PREPARATION_GUIDE.md)** - 完全なRAGガイド
- **[ドキュメントの作成](docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md)** - ベストプラクティス
- **[設計評価](docs/DOCUMENT_DESIGN_EVALUATION.md)** - 品質メトリクス
- **[CLAUDE.md](CLAUDE.md)** - Claude Codeのクイックリファレンス
- **[Preprocessor Quickstart](PREPROCESSOR_QUICKSTART.md)** - 始め方

## コントリビューション

知識ベースに追加する際:

1. `docs/WRITING_RAG_FRIENDLY_DOCUMENTATION.md`のガイドラインに従う
2. `python scripts/ingest/ingest_with_preprocessor.py`を実行して取り込む
3. ログファイルで品質メトリクスを確認
4. 検証のためノートブックSection 2.2を実行
5. 品質スコアを経時的に追跡

## ライセンス

[Your License Here]

## 謝辞

以下を使用して構築:
- [LangGraph](https://github.com/langchain-ai/langgraph) - ワークフローオーケストレーション
- [LangChain](https://github.com/langchain-ai/langchain) - LLMフレームワーク
- [Ollama](https://ollama.ai/) - ローカルLLMサービング
- [ChromaDB](https://www.trychroma.com/) - ベクトルデータベース
- [Tavily](https://tavily.com/) - Web検索API
- [LangSmith](https://smith.langchain.com/) - 可観測性プラットフォーム
