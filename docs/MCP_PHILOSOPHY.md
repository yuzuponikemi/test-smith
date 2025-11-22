# MCP Philosophy in Test-Smith

## 背景：トークン爆発問題

従来のマルチエージェントシステムでは、全ツール定義を事前にコンテキストへ詰め込むアプローチが一般的でした。

```
従来型アーキテクチャ:
  LLM Context (質問する前に)
  ├─ Tool A定義: 5,000 tokens
  ├─ Tool B定義: 8,000 tokens
  ├─ Tool C定義: 12,000 tokens
  └─ ユーザーの質問: 100 tokens
  → 合計: 25,100 tokens

マルチエージェント環境では最大15倍のトークン増加が報告されています。
```

## MCP（Model Context Protocol）パラダイムシフト

AnthropicがMCPで提示した新しい設計思想：

> **"ツールを直接叩く時代は終わる。エージェントはコードを書いて実行し、その中でツールを扱う時代になる"**

### MCPの3層アーキテクチャ

```
LLM層: プロンプトエンジニアリング、推論
  ↓
MCP層: 外部リソース接続（標準化されたインターフェース）
  ↓
Code実行層: データ加工、計算、ツール呼び出し
```

### トークン削減効果

```
MCP型アーキテクチャ:
  LLM → "Pythonコードを生成"
         ↓
       実行環境（必要な時だけロード）
         ↓
       結果のみをLLMに返す
  → 数百 tokens（98.7%削減可能）
```

## Test-SmithにおけるMCP実装

### Design Decision: 独立グラフアーキテクチャ

Test-Smithは「Code Execution」機能をPR #14の**独立グラフアプローチ**で実装しました。

#### ❌ 従来アプローチ（PR #10）の課題

```python
# deep_research_graph.py に統合
class DeepResearchState(TypedDict):
    # ... 既存フィールド ...
    needs_code_execution: bool         # +4,000 tokens
    code_task_description: str         # （毎リクエスト）
    code_data_context: str
    # ... 9個の専用フィールド ...
```

**問題点**:
- コード実行が不要なクエリでも常に4,000 tokensがコンテキストに載る
- グラフ数が増えると線形にトークン使用量が増加
- 将来的なMCPサーバー化が困難

#### ✅ MCP型アプローチ（PR #14ベース + 改善）

```python
# code_execution_graph.py（完全に独立）
class CodeExecutionGraphBuilder(BaseGraphBuilder):
    """
    MCP-aligned design:
    - このグラフは必要な時だけロード
    - 不要時は0 tokens
    - 将来的にMCPサーバーとして外部化可能
    """
```

**利点**:
- 不要時は完全に0 tokens（98.7%削減に近づく）
- グラフ数増加に対してスケーラブル
- MCPサーバーとして切り出し容易

### ハイブリッド実装：ベストオブボスワールド

Test-Smithは両アプローチの利点を統合：

1. **PR #14のアーキテクチャ**（MCPパラダイム）
   - 独立したcode_execution_graph
   - 必要時のみロード
   - MCP準拠の疎結合設計

2. **PR #10のセキュリティ**（本番環境対応）
   - Dockerサンドボックス
   - ネットワーク隔離、リソース制限
   - 多層防御

3. **自動グラフ選択**（UX改善）
   - ユーザーは`--graph`指定不要
   - クエリから自動判断
   - 透明性のある選択理由表示

## 実装詳細

### 自動グラフ選択（graph_selector.py）

```python
def auto_select_graph(query: str) -> str:
    """
    MCP benefit: 選択されたグラフのみロード

    優先順位:
    1. Code execution（計算クエリ）
    2. Causal inference（トラブルシューティング）
    3. Comparative（比較分析）
    4. Fact check（検証）
    5. Quick research（シンプルなクエリ）
    6. Deep research（複雑なクエリ）
    """
```

### Dockerセキュリティ層（code_executor_node.py）

```python
def execute_code_in_docker(code: str) -> tuple:
    """
    PR #10のDockerサンドボックスを統合

    セキュリティ機能:
    - --network=none（ネットワーク遮断）
    - --memory=512m（メモリ制限）
    - --cpus=1（CPU制限）
    - --read-only（読み取り専用FS）
    - 60秒タイムアウト
    """
```

## 使用例

### Before（従来型）

```bash
# ユーザーはグラフを意識する必要がある
python main.py run "Calculate growth rate from 2018 to 2023" --graph code_execution

# グラフ指定忘れると、コード実行が使われない
python main.py run "Calculate growth rate..."
# → deep_research graphで処理（計算はLLMに頼る = 精度低下）
```

### After（MCP型 + 自動選択）

```bash
# シンプルに質問するだけ
python main.py run "Calculate growth rate from 2018 to 2023"

# 出力:
# [System] Using graph workflow: code_execution (auto)
# [Auto-Selection Reasoning]
#   - Contains computational/analytical keywords
#
# CODE EXECUTOR
#   ✓ Docker available - using sandboxed execution
#   Generated code (150 chars)
#   ✓ Execution successful (0.8s) [docker_sandbox]
```

## トークン効率の比較

### シナリオ: 20個のグラフを持つ将来のTest-Smith

| アプローチ | 不要時のコスト | 必要時のコスト |
|-----------|--------------|--------------|
| **統合型（PR #10）** | 4,000 tokens × 20 = 80,000 tokens | 80,000 tokens |
| **MCP型（PR #14改）** | 0 tokens | 3,000 tokens |
| **削減率** | **100%** | **96.25%** |

## 将来的なMCPサーバー化

このアーキテクチャにより、将来的な拡張が容易：

```python
# Phase 3: MCP標準化
mcp_servers/
  └── code_execution/
      ├── server.py          # MCP protocol実装
      └── executor.py        # code_executorロジック再利用

# Claude Desktop等から直接利用可能
# Test-Smith以外のLLMアプリケーションからも利用可能
```

### MCP Server構成例

```json
{
  "mcpServers": {
    "test-smith-code-execution": {
      "command": "python",
      "args": ["mcp_servers/code_execution/server.py"],
      "env": {
        "DOCKER_ENABLED": "true"
      }
    }
  }
}
```

## 参考資料

- **Zenn記事**: [Code Execution × MCPの設計思想](https://zenn.dev/hatyibei/articles/6b26d6bd27a9c2)
  - トークン削減98.7%の実例
  - マルチエージェント環境での課題
  - Anthropicの提示する未来像

- **Anthropic MCP Documentation**: https://modelcontextprotocol.io/

## まとめ

Test-Smithの code_execution 実装は：

1. ✅ **MCP哲学に準拠**（独立グラフ、必要時のみロード）
2. ✅ **本番環境対応**（Dockerセキュリティ）
3. ✅ **優れたUX**（自動選択、グラフ意識不要）
4. ✅ **将来拡張性**（MCPサーバー化の基盤）

この設計により、トークン効率、セキュリティ、使いやすさのすべてを実現しています。
