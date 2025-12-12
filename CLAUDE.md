# CLAUDE.md

Claude Code用の軽量ルーター。詳細は各サブモジュールを参照。

---

## 🎯 Core Behaviors

### Token Efficiency（最重要）
- **No Yapping**: 冗長な説明を避け、コード・箇条書き優先
- **Code-First**: 説明より動くコードを先に示す
- **Lazy Loading**: 必要になるまで詳細ドキュメントを読まない

### Communication
- **言語**: 日本語で返信（特に指示がない限り）
- **出力形式**: Markdown、箇条書き優先
- **認知的明瞭性**: *何*だけでなく*なぜ*を簡潔に説明

### Development Standards
- **Over-engineering禁止**: 要求された変更のみ実装
- **CI必須**: 実装完了前に `ruff check .` `ruff format --check .` `mypy src` `pytest` を実行
- **セキュリティ**: OWASP Top 10に注意、シークレット露出を避ける

---

## 📚 Context Routing Map

タスク種別に応じて、以下のドキュメントを**必要時に読む**こと:

### Pythonコード実装時
```
READ .claude/docs/coding_conventions.md
```
- 型ヒント、命名規則、import順序、エラー処理パターン

### アーキテクチャ設計・新機能追加時
```
READ docs/architecture/system-overview.md
READ docs/architecture/multi-graph-workflows.md
```
- システム全体設計、マルチグラフアーキテクチャ、ステート管理

### 新しいグラフワークフロー作成時
```
READ docs/development/creating-graphs.md
READ src/graphs/quick_research_graph.py (実例)
```
- BaseGraphBuilder拡張パターン、ノード・プロンプト再利用

### RAG・知識ベース関連作業時
```
READ docs/knowledge-base/rag-guide.md
READ docs/knowledge-base/preprocessor.md
```
- ChromaDB設定、取り込み、前処理、品質評価

### テスト・評価作業時
```
READ .claude/docs/testing_guidelines.md
READ docs/development/evaluation-guide.md
```
- pytest構造、テストデータ生成、LangSmith評価

### デバッグ・ロギング時
```
READ docs/development/logging-debugging.md
```
- ロギング設定、LangSmithトレース、診断ツール

### CI/CD・GitHub操作時
```
READ docs/development/ci-cd.md
READ docs/development/github-workflows.md
```
- GitHub Actions、PR作成、コミット規約

---

## 🚀 Quick Reference

### 頻用コマンド
```bash
# 研究クエリ実行
uv run python main.py run "クエリ"

# グラフ指定
uv run python main.py run "クエリ" --graph quick_research

# CI チェック（トークン効率版 - エラー時のみ詳細表示）
./scripts/ci/check.sh          # フル（pytest含む）
./scripts/ci/check.sh --quick  # 高速（lint + type のみ）
```

### 利用可能なグラフ
| グラフ名 | 用途 |
|---------|------|
| `deep_research` | 複雑な多面的質問（デフォルト） |
| `quick_research` | シンプルな質問、高速回答 |
| `fact_check` | 事実確認、検証 |
| `comparative` | 比較分析、トレードオフ |
| `causal_inference` | 根本原因分析、トラブルシューティング |
| `code_investigation` | コードベース分析、依存関係追跡 |

### プロジェクト構造（概要）
```
src/
├── graphs/       # ワークフローグラフ定義
├── nodes/        # 処理ノード（再利用可能）
├── prompts/      # LangChainプロンプト
├── models.py     # LLMファクトリー
└── schemas.py    # Pydanticスキーマ

scripts/
├── ingest/       # 知識ベース取り込み
├── experiments/  # 実験スクリプト
└── studio/       # LangGraph Studio
```

---

## ⚡ Custom Commands

### `/comp-pr [id1] [id2]`
2つのPRを比較分析。アーキテクチャ適合性、複雑性、エッジケースを評価。

### `/review`
`git diff --staged` のセキュリティ・品質監査。Critical/Warning/Suggestion形式で出力。

### `/commit`
Conventional Commits形式のコミットメッセージを生成。ユーザー承認後に実行。

### `/obsidian`
セッション要約をObsidianノート形式で出力（トピック、決定事項、今後の検討事項）。

---

## 🔧 Prototyping Mode

| タスク規模 | 出力形式 |
|-----------|---------|
| 小規模 | 単一スクリプト or Jupyterスニペット |
| 中規模 | 設計仕様（目標、アプローチ、変更ファイル、トレードオフ） |
| 大規模 | ロードマップ（フェーズ分け、技術スタック選択） |

---

## 📖 Full Documentation Index

詳細が必要な場合のみ参照:

- **[docs/README.md](docs/README.md)** - ドキュメント目次
- **[docs/architecture/](docs/architecture/)** - システム設計詳細
- **[docs/development/](docs/development/)** - 開発ガイド
- **[docs/knowledge-base/](docs/knowledge-base/)** - RAG設定詳細
