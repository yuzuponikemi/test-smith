#!/bin/bash

# LangGraph Studio起動スクリプト
# 使い方: ./scripts/studio/start_studio.sh

set -e

# スクリプトの場所を取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 LangGraph Studio 起動中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 仮想環境の存在確認
if [ ! -d ".venv" ]; then
    echo "❌ エラー: 仮想環境が見つかりません (.venv)"
    echo "   以下のコマンドで環境をセットアップしてください:"
    echo "   uv sync --all-extras"
    exit 1
fi

# 仮想環境をアクティベート
echo "📦 仮想環境をアクティベート中..."
source .venv/bin/activate

# langgraph CLIのインストール確認
if ! command -v langgraph &> /dev/null; then
    echo "📥 langgraph-cli をインストール中..."
    pip install -U "langgraph-cli[inmem]" > /dev/null 2>&1
    echo "✅ langgraph-cli インストール完了"
fi

# Ollamaの起動確認（警告のみ）
if ! command -v ollama &> /dev/null; then
    echo "⚠️  警告: Ollamaがインストールされていません"
    echo "   一部の機能が動作しない可能性があります"
else
    if ! ollama list &> /dev/null; then
        echo "⚠️  警告: Ollamaが起動していません"
        echo "   ターミナルで 'ollama serve' を実行してください"
    else
        echo "✅ Ollama 起動確認"
    fi
fi

# 既存のStudioプロセスをチェック
if pgrep -f "langgraph dev" > /dev/null; then
    echo "⚠️  警告: LangGraph Studio は既に起動しています"
    echo "   停止する場合: ./scripts/studio/stop_studio.sh"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ LangGraph Studio を起動します"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 利用可能なグラフ:"
echo "   - deep_research (階層的リサーチ)"
echo "   - code_execution (コード実行) ⭐"
echo "   - quick_research (高速リサーチ)"
echo "   - comparative (比較分析)"
echo "   - fact_check (事実確認)"
echo "   - causal_inference (根本原因分析)"
echo ""
echo "🌐 アクセス方法:"
echo "   Studio UI: ブラウザが自動的に開きます"
echo "   API: http://127.0.0.1:8123"
echo "   Docs: http://127.0.0.1:8123/docs"
echo ""
echo "🛑 停止方法: Ctrl+C または ./scripts/studio/stop_studio.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# LangGraph Studio を起動
langgraph dev --port 8123
