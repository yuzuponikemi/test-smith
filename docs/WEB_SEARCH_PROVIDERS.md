# Web検索プロバイダー設定ガイド

Test-Smithは複数のWeb検索プロバイダーをサポートしており、自動フォールバック機能を備えています。

## 📋 サポートされているプロバイダー

### 1. Tavily (推奨)
- **特徴**: LLMアプリケーション向けに最適化された高品質な検索API
- **料金**: 無料プラン 1,000検索/月
- **APIキー**: 必要
- **登録**: https://tavily.com/

**設定:**
```bash
TAVILY_API_KEY="your-tavily-api-key"
```

### 2. DuckDuckGo (無料・API不要)
- **特徴**: APIキー不要の無料検索
- **料金**: 完全無料
- **APIキー**: 不要
- **制限**: レート制限あり（通常の使用では問題なし）

**設定:**
```bash
# 設定不要（自動的に利用可能）
```

### 3. Brave Search (オプション)
- **特徴**: プライバシー重視の独立検索エンジン
- **料金**: 無料プラン 2,000検索/月
- **APIキー**: 必要
- **登録**: https://brave.com/search/api/

**設定:**
```bash
BRAVE_API_KEY="your-brave-api-key"
```
*(現在実装中)*

## ⚙️ 設定方法

### 環境変数の設定

`.env`ファイルに以下を追加：

```bash
# Search Provider Configuration
# Priority order for web search providers (comma-separated)
# Available: tavily, duckduckgo, brave
SEARCH_PROVIDER_PRIORITY="tavily,duckduckgo"

# Tavily API Key (optional, but recommended)
TAVILY_API_KEY="your-tavily-api-key"

# Optional: Brave Search API Key
# BRAVE_API_KEY="your-brave-api-key"
```

### プロバイダー優先順位

`SEARCH_PROVIDER_PRIORITY`で検索プロバイダーの優先順位を設定できます：

```bash
# Tavilyを最優先、失敗したらDuckDuckGo
SEARCH_PROVIDER_PRIORITY="tavily,duckduckgo"

# DuckDuckGoのみ使用（完全無料）
SEARCH_PROVIDER_PRIORITY="duckduckgo"

# Brave → Tavily → DuckDuckGo の順
SEARCH_PROVIDER_PRIORITY="brave,tavily,duckduckgo"
```

## 🔄 自動フォールバック機能

システムは以下のように自動的にフォールバックします：

1. **優先度の高いプロバイダーから試行**
   ```
   例: tavily → duckduckgo
   ```

2. **失敗時の自動切り替え**
   - Tavilyが432エラー（APIキー無効/クレジット切れ）→ DuckDuckGoに自動切り替え
   - DuckDuckGoがレート制限 → 次のプロバイダーに切り替え

3. **エラーハンドリング**
   - 全プロバイダーが失敗してもグラフは停止せず、エラーメッセージを含めて続行
   - ユーザーにわかりやすいエラーメッセージを表示

## 🔍 ヘルスチェック

検索プロバイダーの状態を確認するスクリプト：

```bash
python scripts/utils/check_search_providers.py
```

**出力例:**
```
================================================================================
SEARCH PROVIDER HEALTH CHECK
================================================================================

=== Search Provider Status ===

✅ tavily: Configured and ready
✅ duckduckgo: Configured and ready

Priority order: tavily → duckduckgo

================================================================================
RUNNING HEALTH CHECKS
================================================================================

  [tavily] ✅
  [duckduckgo] ✅

================================================================================
SUMMARY
================================================================================

Healthy providers: 2/2
Priority order: tavily → duckduckgo

✅ All configured providers are healthy!
```

## 🚨 トラブルシューティング

### Tavily 432 エラー
```
⚠️ Tavily API Error: API key may be invalid, expired, or out of credits.
```

**原因**:
- APIキーが無効
- 月間クレジット上限（1,000検索）に達した

**解決策**:
1. https://tavily.com/ でアカウントを確認
2. 新しいAPIキーを取得
3. または`SEARCH_PROVIDER_PRIORITY="duckduckgo"`に変更

### DuckDuckGo レート制限エラー
```
⚠️ DuckDuckGo rate limit exceeded
```

**解決策**:
1. 少し待ってから再試行
2. Tavilyプロバイダーを追加して負荷分散

### 全プロバイダー失敗
```
⚠️ All search providers failed
```

**解決策**:
1. ネットワーク接続を確認
2. `python scripts/utils/check_search_providers.py`でヘルスチェック実行
3. `.env`の設定を確認

## 💡 推奨設定

### 開発環境（完全無料）
```bash
SEARCH_PROVIDER_PRIORITY="duckduckgo"
```

### 本番環境（高品質）
```bash
SEARCH_PROVIDER_PRIORITY="tavily,duckduckgo"
TAVILY_API_KEY="your-tavily-api-key"
```

### 高負荷環境（複数API）
```bash
SEARCH_PROVIDER_PRIORITY="tavily,brave,duckduckgo"
TAVILY_API_KEY="your-tavily-api-key"
BRAVE_API_KEY="your-brave-api-key"
```

## 📊 プロバイダー比較

| プロバイダー | 品質 | 速度 | 料金 | APIキー | レート制限 |
|------------|------|------|------|---------|----------|
| Tavily     | ★★★★★ | ★★★★☆ | 無料 1,000/月 | 必要 | 緩い |
| DuckDuckGo | ★★★☆☆ | ★★★★★ | 完全無料 | 不要 | やや厳しい |
| Brave      | ★★★★☆ | ★★★★☆ | 無料 2,000/月 | 必要 | 緩い |

## 🔗 関連ドキュメント

- **[CLAUDE.md](../CLAUDE.md)** - プロジェクト全体のドキュメント
- **[src/utils/search_providers/](../src/utils/search_providers/)** - プロバイダー実装
- **[scripts/utils/check_search_providers.py](../scripts/utils/check_search_providers.py)** - ヘルスチェックスクリプト
