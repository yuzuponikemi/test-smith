# Feature Development Workflow

Test-SmithにClaude Codeの`feature-dev` pluginにインスパイアされた機能開発ワークフローを実装しました。

## 概要

**feature_dev**グラフは、新機能を体系的に開発するための7フェーズワークフローです。コードを書く前に要件を明確化し、コードベースを理解し、アーキテクチャを設計し、品質をレビューする構造化されたアプローチを提供します。

## アーキテクチャ

### 7つのフェーズ

```
Discovery → Exploration → Clarification → Architecture → Implementation → Review → Summary
```

#### Phase 1: Discovery（要件明確化）
- 機能リクエストを分析
- 要件を明確化
- スコープと制約を定義

**出力**:
- 明確化された要件
- スコープ定義
- 制約のリスト

#### Phase 2: Exploration（コードベース探索）
- **2つの並列エージェント**がコードベースを分析
  - Agent 1: 類似機能と既存実装
  - Agent 2: アーキテクチャパターンと統合ポイント
- 実行パスをトレース
- 重要なファイルを特定（5-10ファイル）
- 設計パターンをマッピング

**出力**:
- 探索結果（各エージェントから）
- 関連ファイルのリスト
- コードベースパターンのサマリー

#### Phase 3: Clarification（質問の明確化）
- 曖昧な点を特定
- ユーザーへの質問を生成
  - エッジケース
  - エラーハンドリング
  - 統合ポイント
  - パフォーマンス要件
  - 後方互換性

**ブロッキング**: 質問がある場合、ユーザーの回答を待つ

**出力**:
- 質問リスト
- ユーザーの回答（提供された場合）

#### Phase 4: Architecture（アーキテクチャ設計）
- **3つの並列アーキテクトエージェント**が異なるアプローチを設計
  1. **Minimal Changes**: 最速実装、最大限のコード再利用
  2. **Clean Architecture**: 最高の保守性、適切な抽象化
  3. **Pragmatic Balance**: スピードと品質のバランス

各提案には以下が含まれます：
- 説明
- 長所/短所
- 作成するファイル
- 変更するファイル
- 実装ステップ
- 複雑度スコア（1-10）

**ブロッキング**: ユーザーがアーキテクチャを選択するまで待つ

**出力**:
- 3つのアーキテクチャ提案
- 選択されたアーキテクチャ
- 選択理由

#### Phase 5: Implementation（実装）
- 選択されたアーキテクチャに従って実装
- 新しいファイルを作成
- 既存のファイルを変更
- コードベースの規約に従う
- 進捗をログに記録

**ブロッキング**: 実装開始前にユーザーの承認を要求

**出力**:
- 実装ログ
- 作成されたファイルのリスト
- 変更されたファイルのリスト

#### Phase 6: Quality Review（品質レビュー）
- **3つの並列レビュアーエージェント**が異なる観点でレビュー
  1. **Simplicity**: 複雑さ、重複（DRY違反）、過度なエンジニアリング
  2. **Correctness**: バグ、ロジックエラー、エラーハンドリングの欠如
  3. **Conventions**: プロジェクトガイドライン違反、命名の不一致

**Confidence-Based Filtering**: 80%以上の信頼度の問題のみ報告

**ブロッキング**: 重大な問題がある場合、ユーザーの判断を待つ

**出力**:
- レビュー結果リスト
- 重大な問題（クリティカル）
- レビュー承認ステータス

#### Phase 7: Summary（サマリー）
- 包括的なドキュメントを生成
- 構築内容
- アーキテクチャの決定
- 変更されたファイル
- 品質レビューの結果
- 次のステップ

**出力**:
- 完全なサマリードキュメント
- 推奨される次のステップ

### ステート管理

```python
class FeatureDevState(TypedDict):
    # Input
    feature_request: str

    # Phase 1: Discovery
    clarified_requirements: str
    feature_scope: str
    constraints: str

    # Phase 2: Exploration
    exploration_results: list[ExplorationResult]
    relevant_files: list[str]
    codebase_patterns: str

    # Phase 3: Clarification
    questions: list[str]
    user_answers: str
    awaiting_user_input: bool

    # Phase 4: Architecture
    architecture_proposals: list[ArchitectureProposal]
    chosen_architecture: ArchitectureProposal | None

    # Phase 5: Implementation
    implementation_log: list[str]
    files_created: list[str]
    files_modified: list[str]

    # Phase 6: Review
    review_findings: list[ReviewFinding]
    critical_issues: list[ReviewFinding]

    # Phase 7: Summary
    summary: str
    next_steps: list[str]

    # Control
    current_phase: str
    phase_history: list[str]
```

### ユーザー承認ゲート

ワークフローには4つの承認ゲートがあります：

1. **Phase 3完了時**: 質問がある場合、ユーザーの回答を待つ
2. **Phase 4完了時**: ユーザーがアーキテクチャを選択するまで待つ
3. **Phase 5開始前**: 実装開始の承認を待つ
4. **Phase 6完了時**: 重大な問題への対応判断を待つ

各ゲートで`awaiting_user_input = True`となり、ワークフローは`END`に到達して一時停止します。

## 使用方法

### 基本的な使用方法

```bash
# Ollamaが実行されていることを確認
ollama list

# feature_devグラフで機能開発を開始
python main.py run "Add user authentication with OAuth2" --graph feature_dev
```

### グラフ情報の確認

```bash
# 利用可能なグラフをリスト
python main.py graphs

# feature_devの詳細情報
python main.py graphs --detailed | grep -A 20 "feature_dev"
```

### テスト実行

```bash
# テストスクリプトを実行（Ollamaが必要）
python scripts/testing/test_feature_dev.py
```

## 実装の詳細

### ファイル構成

```
src/
├── feature_dev_schemas.py              # ステートとデータ構造
├── prompts/
│   └── feature_dev_prompts.py          # 7つのフェーズのプロンプト
├── nodes/
│   └── feature_dev/
│       ├── __init__.py
│       ├── discovery_node.py           # Phase 1
│       ├── codebase_explorer_node.py   # Phase 2（並列実行）
│       ├── question_clarifier_node.py  # Phase 3
│       ├── architecture_designer_node.py # Phase 4（並列実行）
│       ├── feature_implementer_node.py # Phase 5
│       ├── quality_reviewer_node.py    # Phase 6（並列実行）
│       └── feature_summarizer_node.py  # Phase 7
└── graphs/
    └── feature_dev_graph.py            # グラフ定義とルーター
```

### 並列エージェント実行

以下のフェーズで並列実行を使用：

- **Phase 2**: 2エージェント（異なる探索フォーカス）
- **Phase 4**: 3エージェント（3つの異なるアーキテクチャアプローチ）
- **Phase 6**: 3エージェント（3つの異なるレビュー観点）

### ルーターロジック

```python
def _clarification_router(state):
    """Phase 3後: 質問があり未回答なら待機"""
    if questions and not user_answers:
        return "wait_for_user"
    return "architecture"

def _architecture_router(state):
    """Phase 4後: アーキテクチャ未選択なら待機"""
    if not chosen_architecture:
        return "wait_for_choice"
    return "implementation"

def _review_router(state):
    """Phase 6後: 重大な問題があり未承認なら待機"""
    if critical_issues and not review_approved:
        return "wait_for_approval"
    return "summary"
```

## Claude Code feature-devとの比較

### 類似点

✅ **7フェーズワークフロー**: Discovery → Exploration → Clarification → Architecture → Implementation → Review → Summary

✅ **並列エージェント実行**: Phase 2（探索）、Phase 4（アーキテクチャ）、Phase 6（レビュー）

✅ **ユーザー承認ゲート**: 重要な決定ポイントでワークフローをブロック

✅ **Confidence-Based Filtering**: レビューで80%以上の信頼度の問題のみ報告

✅ **3つのアーキテクチャアプローチ**: Minimal Changes、Clean Architecture、Pragmatic Balance

### 相違点

🔄 **Test-Smith固有の実装**:
- LangGraphベースのステートマシン
- ChromaDB RAG統合（将来的に）
- Ollama/Geminiローカルモデル
- 既存のTest-Smithグラフシステムへの統合

🔄 **Claude Code固有の機能**:
- VSCode統合
- ファイルシステムへの直接書き込み
- Git操作の統合
- インタラクティブなUI

## ユースケース

### 適している場合

✅ 新機能の追加
✅ 重要な機能の実装
✅ 計画が必要な複雑な実装
✅ 既存コードベースへの統合
✅ アーキテクチャ的な決定が必要な場合

### 適していない場合

❌ 小さなバグ修正
❌ タイポの修正
❌ ドキュメントのみの変更
❌ 設定ファイルの調整

これらには`quick_research`または直接的な実装が適しています。

## 次のステップ

### 今後の改善

1. **RAG統合**: ChromaDBでコードベース検索を実装
2. **実際のファイル操作**: Phase 5で実際にファイルを作成/変更
3. **Git統合**: 自動コミットとブランチ作成
4. **テストカバレッジ**: 各フェーズのユニットテスト
5. **インタラクティブモード**: ユーザー入力をリアルタイムで収集

### 使用開始方法

1. Ollamaが実行中であることを確認
2. 機能リクエストを準備
3. `python main.py run "YOUR_REQUEST" --graph feature_dev`を実行
4. 各承認ゲートで質問に回答/選択を行う
5. 最終的なサマリーとファイル変更を確認

## トラブルシューティング

### グラフが見つからない

```bash
# グラフが登録されているか確認
python -c "from src.graphs import list_graphs; print(list(list_graphs().keys()))"
```

### Ollama接続エラー

```bash
# Ollamaが実行中か確認
ollama list

# 必要に応じて起動
ollama serve
```

### インポートエラー

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

## 参考資料

- [Claude Code feature-dev plugin](https://github.com/anthropics/claude-code/tree/main/plugins/feature-dev)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Test-Smith Architecture](docs/architecture/system-overview.md)
