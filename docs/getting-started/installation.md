# インストールとセットアップ

このガイドでは、**UV**（モダンなPythonパッケージマネージャー）を使用したTest-Smithの完全なセットアッププロセスをカバーします。

---

## 前提条件

### 必要なソフトウェア

- **Python 3.9.2+** - コアランタイム（UVがインストール可能）
- **UV** - モダンなパッケージマネージャー（[インストールガイド](#1-uvのインストール)）
- **Git** - バージョン管理

### オプション: LLMプロバイダー

以下から1つまたは両方を選択:

- **Google Gemini API**（推奨） - クラウドベースのLLM（[無料キーを取得](https://makersuite.google.com/app/apikey)）
- **Ollama**（オプション） - ローカルLLM推論（[ダウンロード](https://ollama.ai/)）

### 必要なAPIキー

- **Tavily APIキー** - Web検索（[無料キーを取得](https://tavily.com/)）
- **LangSmith APIキー**（オプション） - 可観測性（[無料キーを取得](https://smith.langchain.com/)）

---

## インストール手順

### 1. UVのインストール

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**インストールの確認:**
```bash
uv --version
```

### 2. リポジトリのクローン

```bash
git clone https://github.com/your-repo/test-smith.git
cd test-smith
```

### 3. 依存関係のインストール

UVは自動的に仮想環境を作成し、すべての依存関係をインストールします:

```bash
# すべての依存関係をインストール（devツールを含む）
uv sync --all-extras
```

**何が起こるか:**
- ✅ `.venv/`を自動的に作成
- ✅ `pyproject.toml`からすべての依存関係をインストール
- ✅ 再現性のため`uv.lock`を生成
- ✅ 約5秒で完了（pipの約2分と比較！）

### 4. LLMプロバイダーの設定

#### オプションA: Google Gemini（推奨、デフォルト）

**利点:**
- ✅ ローカルインストール不要
- ✅ 高速な推論
- ✅ 低いリソース使用量
- ✅ 無料ティアが利用可能

**セットアップ:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey)からAPIキーを取得
2. `.env`に追加（ステップ5を参照）
3. 追加のセットアップは不要！

#### オプションB: Ollama（ローカルモデル）

**利点:**
- ✅ 完全にオフライン
- ✅ APIコスト不要
- ✅ データプライバシー

**セットアップ:**
```bash
# Ollamaをインストール
curl -fsSL https://ollama.ai/install.sh | sh

# 必要なモデルをプル
ollama pull llama3           # メイン推論モデル（4.7GB）
ollama pull command-r        # 高度な推論（20GB）
ollama pull nomic-embed-text # 埋め込み（274MB）

# モデルを確認
ollama list
```

期待される出力:
```
NAME              ID          SIZE   MODIFIED
llama3:latest     ...         4.7GB  ...
command-r:latest  ...         20GB   ...
nomic-embed-text  ...         274MB  ...
```

### 5. 環境の設定

プロジェクトルートに`.env`ファイルを作成:

**Google Gemini用（デフォルト）:**
```bash
# モデルプロバイダー
MODEL_PROVIDER="gemini"

# Google Gemini APIキー（必須）
GOOGLE_API_KEY="your-google-api-key-here"

# Web検索（必須）
TAVILY_API_KEY="tvly-your-key-here"

# LangSmith（オプション - 可観測性用）
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# ロギング（オプション）
STRUCTURED_LOGS_JSON="false"
LOG_LEVEL="INFO"
```

**Ollama用（ローカル）:**
```bash
# モデルプロバイダー
MODEL_PROVIDER="ollama"

# Web検索（必須）
TAVILY_API_KEY="tvly-your-key-here"

# LangSmith（オプション - 可観測性用）
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# ロギング（オプション）
STRUCTURED_LOGS_JSON="false"
LOG_LEVEL="INFO"
```

### 6. インストールの確認

```bash
# バージョンを確認
uv run python main.py --version

# 利用可能なグラフを一覧表示
uv run python main.py graphs

# テストクエリを実行
uv run python main.py run "LangGraphとは何ですか？"
```

**期待される出力:**
- 利用可能なワークフローを表示するグラフリスト
- planner → searcher → analyzer → synthesizerの研究プロセス
- 最終的な包括的レポート

---

## ディレクトリ構造

インストール後、プロジェクトは以下のようになります:

```
test-smith/
├── .env                    # 環境設定
├── .venv/                  # 仮想環境（UVが自動作成）
├── uv.lock                 # 依存関係ロックファイル
├── pyproject.toml          # プロジェクト設定と依存関係
├── main.py                 # CLIエントリーポイント
├── src/                    # ソースコード
│   ├── graphs/             # ワークフロー定義
│   ├── nodes/              # 処理ノード
│   ├── prompts/            # LLMプロンプト
│   └── preprocessor/       # ドキュメント前処理
├── documents/              # RAGソースドキュメント
├── chroma_db/              # ベクトルデータベース（初回実行時に作成）
├── logs/                   # 実行ログ
└── reports/                # 生成されたレポート
```

---

## トラブルシューティング

### UVコマンドが見つからない

**解決策:** UVをPATHに追加:

```bash
# ~/.bashrcまたは~/.zshrcに追加
export PATH="$HOME/.local/bin:$PATH"

# シェルをリロード
source ~/.bashrc  # またはsource ~/.zshrc
```

### Ollamaが起動しない（Ollamaを使用する場合）

```bash
# Ollamaが実行されているか確認
ollama list

# Ollamaサービスを起動
ollama serve

# またはOllamaアプリを再起動
```

### モデルが見つからない（Ollamaを使用する場合）

```bash
# 不足しているモデルをプル
ollama pull llama3

# インストールされているか確認
ollama list
```

### APIキーエラー

```bash
# .envファイルが存在するか確認
cat .env

# 環境変数がロードされているか確認
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TAVILY_API_KEY'))"
```

### インポートエラー

```bash
# ロックファイルを再生成
uv lock

# 依存関係を再インストール
uv sync --all-extras
```

### 「解決策が見つかりません」依存関係エラー

**これは修正したエラーです！**

解決策: `pyproject.toml`に`requires-python = ">=3.9.2"`が設定され、依存関係の競合が解決されます。

```bash
# まだこれが表示される場合は、以下を試してください:
uv lock --upgrade
uv sync --all-extras
```

---

## レガシーインストール（非推奨）

<details>
<summary>⚠️ pipを使用（非推奨）</summary>

**注意:** この方法は非推奨です。より良いパフォーマンスと再現性のためUVを使用してください。

```bash
# リポジトリをクローン
git clone https://github.com/your-repo/test-smith.git
cd test-smith

# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate     # Windows

# 依存関係をインストール
pip install -e ".[dev]"
```

**なぜpipではないのか？**
- 🐌 UVより10-100倍遅い
- ⚠️ 再現可能なビルドなし
- 🔧 手動venv管理が必要
- ❌ より弱い依存関係解決

</details>

---

## 次のステップ

- **[クイックスタート](quick-start.md)** - 最初の研究クエリを実行
- **[モデルプロバイダー](model-providers.md)** - OllamaまたはGeminiを設定
- **[UV使用ガイド](../../.github/UV_GUIDE.md)** - 完全なUVドキュメント
- **[RAGガイド](../knowledge-base/rag-guide.md)** - 知識ベースにドキュメントを追加

---

## 追加リソース

- **[UVドキュメント](https://docs.astral.sh/uv/)** - 公式UVドキュメント
- **[UVトラブルシューティング](../../.github/UV_GUIDE.md#-troubleshooting)** - 一般的な問題と解決策
- **[pipからの移行](../../.github/UV_GUIDE.md#-migration-from-pip)** - pipに慣れている場合
