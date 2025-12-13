#!/bin/bash
# CI チェック - トークン効率重視版
# 成功時: 1行サマリー
# 失敗時: エラー箇所のみ表示

set -o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

ERRORS=0
SUMMARY=""

# Ruff Linter
echo -n "Ruff lint... "
RUFF_OUT=$(uv run ruff check . 2>&1)
RUFF_EXIT=$?
if [ $RUFF_EXIT -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    # エラー行のみ抽出（ファイル:行:列: エラーコード 形式）
    echo "$RUFF_OUT" | grep -E "^[^:]+:\d+:\d+:" | head -20
    ERRORS=$((ERRORS + 1))
    SUMMARY="${SUMMARY}ruff "
fi

# Ruff Format
echo -n "Ruff format... "
FORMAT_OUT=$(uv run ruff format --check . 2>&1)
FORMAT_EXIT=$?
if [ $FORMAT_EXIT -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    # 修正が必要なファイル名のみ
    echo "$FORMAT_OUT" | grep -E "^Would reformat:" | head -10
    ERRORS=$((ERRORS + 1))
    SUMMARY="${SUMMARY}format "
fi

# Mypy
echo -n "Mypy... "
MYPY_OUT=$(uv run mypy src --no-error-summary 2>&1)
MYPY_EXIT=$?
if [ $MYPY_EXIT -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    # エラー行のみ（note: は除外）
    echo "$MYPY_OUT" | grep -E "^src/.*: error:" | head -20
    ERRORS=$((ERRORS + 1))
    SUMMARY="${SUMMARY}mypy "
fi

# Pytest (オプション: --quick フラグで省略可能)
if [[ "$1" != "--quick" ]]; then
    echo -n "Pytest... "
    PYTEST_OUT=$(uv run pytest -q --tb=no 2>&1)
    PYTEST_EXIT=$?
    if [ $PYTEST_EXIT -eq 0 ]; then
        # 成功時はパス数のみ
        PASSED=$(echo "$PYTEST_OUT" | grep -oE "[0-9]+ passed" | head -1)
        echo -e "${GREEN}OK${NC} ($PASSED)"
    else
        echo -e "${RED}FAIL${NC}"
        # 失敗テスト名のみ
        echo "$PYTEST_OUT" | grep -E "^FAILED" | head -10
        ERRORS=$((ERRORS + 1))
        SUMMARY="${SUMMARY}pytest "
    fi
fi

# 最終サマリー
echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed${NC}"
    exit 0
else
    echo -e "${RED}✗ Failed: ${SUMMARY}${NC}"
    exit 1
fi
