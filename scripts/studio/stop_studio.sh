#!/bin/bash

# LangGraph Studio停止スクリプト
# 使い方: ./scripts/studio/stop_studio.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 LangGraph Studio を停止中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# langgraph dev プロセスを探す
if pgrep -f "langgraph dev" > /dev/null; then
    pkill -f "langgraph dev"
    sleep 2

    # 停止確認
    if pgrep -f "langgraph dev" > /dev/null; then
        echo "⚠️  通常の停止に失敗しました。強制停止を試みます..."
        pkill -9 -f "langgraph dev"
        sleep 1
    fi

    if pgrep -f "langgraph dev" > /dev/null; then
        echo "❌ エラー: LangGraph Studio の停止に失敗しました"
        echo "   手動で停止してください: pkill -9 -f 'langgraph dev'"
        exit 1
    else
        echo "✅ LangGraph Studio を停止しました"
    fi
else
    echo "ℹ️  LangGraph Studio は起動していません"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
