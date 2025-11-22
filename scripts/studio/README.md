# LangGraph Studio 起動スクリプト

LangGraph Studioをワンクリックで起動・停止するためのシェルスクリプトです。

## 📁 ファイル

- **`start_studio.sh`** - Studioを起動
- **`stop_studio.sh`** - Studioを停止

## 🚀 起動方法

### オプション1: プロジェクトルートから実行

```bash
./scripts/studio/start_studio.sh
```

### オプション2: スクリプトディレクトリから実行

```bash
cd scripts/studio
./start_studio.sh
```

### 起動確認

スクリプトが以下の処理を自動的に実行します：

1. ✅ 仮想環境の存在確認
2. ✅ 仮想環境のアクティベート
3. ✅ langgraph-cli のインストール確認（必要に応じて自動インストール）
4. ✅ Ollama起動確認（警告のみ）
5. ✅ 既存プロセスのチェック
6. ✅ LangGraph Studio サーバーの起動

### 起動後

ブラウザが自動的に開き、以下のURLでアクセスできます：

- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123`
- **API**: `http://127.0.0.1:8123`
- **API Docs**: `http://127.0.0.1:8123/docs`

## 🛑 停止方法

### オプション1: Ctrl+C

起動中のターミナルで `Ctrl+C` を押す

### オプション2: 停止スクリプト

別のターミナルで以下を実行：

```bash
./scripts/studio/stop_studio.sh
```

## 📊 利用可能なグラフ

Studio UIで以下のグラフを選択できます：

| グラフ名 | 説明 |
|---------|------|
| `deep_research` | 階層的マルチエージェントリサーチ |
| `code_execution` ⭐ | コード実行機能付きリサーチ |
| `quick_research` | 高速シングルパスリサーチ |
| `comparative` | サイドバイサイド比較分析 |
| `fact_check` | クレーム検証ワークフロー |
| `causal_inference` | 根本原因分析 |

## 🧪 テストクエリ例（code_execution グラフ用）

Studio UIで `code_execution` グラフを選択後、以下のクエリを試してください：

### 数学計算
```
Calculate the standard deviation of these numbers: 10, 15, 20, 25, 30
```

### データ分析
```
What is the correlation between variables A and B in a dataset with values [1,2,3,4,5] and [2,4,5,4,5]?
```

### 統計処理
```
Calculate the compound annual growth rate from 2018 to 2023 with initial value 100 and final value 150
```

### 簡単な計算
```
What is 15% of 200?
```

## 🔧 トラブルシューティング

### エラー: 仮想環境が見つかりません

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### エラー: Ollamaが起動していません

```bash
# Ollamaを起動
ollama serve

# 別のターミナルでモデルを確認
ollama list
```

必要なモデル：
- `llama3`
- `command-r`
- `nomic-embed-text`

### エラー: 既にStudioが起動しています

```bash
# 既存のプロセスを停止
./scripts/studio/stop_studio.sh

# 再度起動
./scripts/studio/start_studio.sh
```

### ポート8123が使用中

別のポートを使用する場合は、`start_studio.sh` の最終行を編集：

```bash
langgraph dev --port 8124  # 任意のポート番号
```

## 📖 関連ドキュメント

- **[docs/STUDIO_GUIDE.md](../../docs/STUDIO_GUIDE.md)** - LangGraph Studioの詳細ガイド
- **[docs/architecture/multi-graph-workflows.md](../../docs/architecture/multi-graph-workflows.md)** - マルチグラフアーキテクチャ
- **[langgraph.json](../../langgraph.json)** - Studio設定ファイル
- **[src/studio_graphs.py](../../src/studio_graphs.py)** - グラフエントリーポイント

## 💡 Tips

### バックグラウンド起動（非推奨）

通常はフォアグラウンドで起動することを推奨しますが、バックグラウンドで起動したい場合：

```bash
nohup ./scripts/studio/start_studio.sh > studio.log 2>&1 &
```

停止時は必ず `stop_studio.sh` を使用してください。

### ログ確認

起動ログを確認したい場合：

```bash
./scripts/studio/start_studio.sh 2>&1 | tee studio_startup.log
```

### 複数グラフの同時実行

LangGraph Studioは1つのサーバーで全グラフにアクセスできるため、複数のプロセスを起動する必要はありません。Studio UIで左サイドバーからグラフを切り替えてください。
