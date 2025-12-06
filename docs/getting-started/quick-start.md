# クイックスタートガイド

5分でTest-Smithを実行できます。

---

## 前提条件

[インストール](installation.md)手順が完了していることを確認してください:
- 必要なモデルでOllamaが実行中
- Tavily APIキーで`.env`ファイルが設定済み
- 仮想環境が起動中

---

## 最初のクエリ

### 基本的な研究クエリ

```bash
python main.py run "TransformerとRNNの主な違いは何ですか？"
```

これはデフォルトの`deep_research`ワークフローを使用し、以下を実行します:
1. クエリの複雑さを分析
2. 複雑な場合はサブタスクに分解
3. Webおよび/または知識ベースを検索
4. 包括的なレポートを統合

### クイック検索

シンプルな質問には、より高速な`quick_research`ワークフローを使用:

```bash
python main.py run "フランスの首都は？" --graph quick_research
```

---

## 利用可能なワークフロー

すべての利用可能なワークフローを一覧表示:

```bash
python main.py graphs
```

### 適切なワークフローの選択

| ワークフロー | 使用タイミング | 例 |
|----------|----------|---------|
| `deep_research` | 複雑で多面的な質問 | "本番用AIフレームワークを比較" |
| `quick_research` | シンプルな検索、時間に敏感 | "BERTとは？" |
| `fact_check` | 主張の検証 | "Pythonは1991年に作成されたというのは本当か？" |
| `comparative` | オプションの比較 | "新しいプロジェクトにReact vs Vue" |
| `causal_inference` | トラブルシューティング、根本原因 | "なぜアプリが遅く動作しているのか？" |

### コマンド例

```bash
# 深い研究（デフォルト）
python main.py run "マルチエージェントAIシステムを分析"

# クイック研究
python main.py run "ChromaDBとは？" --graph quick_research

# ファクトチェック
python main.py run "検証: GPT-4は2023年3月にリリースされた" --graph fact_check

# 比較
python main.py run "WebアプリケーションにPostgreSQL vs MySQL" --graph comparative

# 根本原因分析
python main.py run "なぜAPIが断続的に500エラーを返すのか？" --graph causal_inference
```

---

## 出力の理解

### コンソール出力

実行中、以下が表示されます:
- ノード実行の進捗
- クエリ割り当て（web vs RAG）
- サブタスク分解（階層モード用）
- 最終レポート

### 生成されたファイル

各実行で以下が作成されます:

1. **実行ログ** (`logs/execution_*.log`)
   - 完全な実行トレース
   - デバッグに便利

2. **研究レポート** (`reports/report_*.md`)
   - 最終統合レポート
   - メタデータ付きMarkdown形式

```bash
# 最近のレポートを一覧表示
python main.py list reports --limit 5

# 最近のログを一覧表示
python main.py list logs --limit 5
```

---

## 会話の継続

フォローアップ質問にスレッドIDを使用:

```bash
# 最初のクエリ
python main.py run "LangGraphとは？" --thread-id my-session

# 同じコンテキストでフォローアップ
python main.py run "AutoGenと比較してどうですか？" --thread-id my-session
```

---

## 一般的なオプション

```bash
# ロギングを無効化（コンソールのみ）
python main.py run "クイックテスト" --no-log --no-report

# グラフを指定
python main.py run "あなたのクエリ" --graph quick_research

# スレッドIDを使用
python main.py run "フォローアップ" --thread-id abc123
```

---

## より良い結果のためのヒント

### 1. 具体的に

```bash
# 曖昧 - 一般的な結果を生成する可能性
python main.py run "AIについて教えて"

# 具体的 - より良い結果
python main.py run "Transformerのアテンションメカニズムとそのアドバンテージを説明してください"
```

### 2. 適切なワークフローを使用

シンプルな事実に`deep_research`を使用しないでください - より遅く、過剰です。

### 3. コンテキストを追加

```bash
# 良い: コンテキストを含む
python main.py run "サーバーサイドレンダリングが必要な大規模eコマースアプリケーション用にReactとVueを比較"

# コンテキストが少ない
python main.py run "React vs Vue"
```

### 4. 知識ベースを確認

ドメイン固有のドキュメントがある場合:
```bash
# 最初に知識ベースにドキュメントを追加
python scripts/ingest/ingest_with_preprocessor.py

# その後クエリ
python main.py run "当社の認証システムはどのように機能しますか？"
```

---

## 次のステップ

- **[モデルプロバイダー](model-providers.md)** - 異なるパフォーマンスのためOllamaまたはGeminiを設定
- **[マルチグラフワークフロー](../architecture/multi-graph-workflows.md)** - ワークフローオプションの詳細
- **[RAGガイド](../knowledge-base/rag-guide.md)** - 独自のドキュメントを知識ベースに追加
