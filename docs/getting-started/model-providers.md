# モデルプロバイダーガイド

Test-Smithは2つのモデルプロバイダーをサポートします: **Ollama**（ローカル）と**Gemini**（クラウド）。

---

## クイック切り替え

```bash
# Geminiに切り替え（高速、クラウド）
python scripts/utils/switch_model_provider.py gemini

# Ollamaに切り替え（無料、ローカル）
python scripts/utils/switch_model_provider.py ollama

# 現在のプロバイダーを確認
python scripts/utils/switch_model_provider.py status
```

---

## プロバイダー比較

| 機能 | Ollama | Gemini |
|---------|--------|--------|
| **コスト** | 無料 | 従量課金（約$0.01-0.05/クエリ） |
| **速度** | レスポンスあたり10-30秒 | レスポンスあたり1-3秒 |
| **プライバシー** | すべてのデータがローカル | データがGoogleに送信 |
| **オフライン** | はい | いいえ |
| **セットアップ** | インストール + モデルプル | APIキーのみ |
| **一貫性** | 中 | 高 |

---

## Ollamaセットアップ

### インストール

```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Mac
brew install ollama

# Windows
# https://ollama.ai/downloadからダウンロード
```

### 必要なモデルをプル

```bash
ollama pull llama3           # 一般的な推論
ollama pull command-r        # 評価と統合
ollama pull nomic-embed-text # RAG用埋め込み

# 確認
ollama list
```

### 設定

`.env`内:
```bash
MODEL_PROVIDER="ollama"
OLLAMA_BASE_URL="http://localhost:11434"  # オプション、デフォルト
```

### ハードウェア要件

| レベル | RAM | CPU | GPU |
|-------|-----|-----|-----|
| 最小 | 16GB | 4コア | オプション |
| 推奨 | 32GB | 8コア | 8GB VRAM |
| 最適 | 64GB | 16コア | 16GB VRAM |

### トラブルシューティング

**Ollamaに接続できない:**
```bash
# Ollamaサービスを起動
ollama serve

# 実行中か確認
ollama list
```

**モデルが見つからない:**
```bash
ollama pull llama3
```

**パフォーマンスが遅い:**
- ハードウェアをアップグレード（より多くのRAM、より良いGPU）
- より小さいモデルを使用（ただし品質が低下）
- 他のアプリケーションを閉じる

---

## Geminiセットアップ

### APIキーを取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでサインイン
3. 「APIキーを作成」をクリック
4. キーをコピー（`AIza...`で始まる）

### APIキーをテスト

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{"contents":[{"parts":[{"text":"Say hello"}]}]}'
```

### 設定

`.env`内:
```bash
GOOGLE_API_KEY="AIza..."
MODEL_PROVIDER="gemini"
```

### モデルオプション

| モデル | 速度 | 品質 | コスト | 用途 |
|-------|-------|---------|------|---------|
| `gemini-pro` | 高速 | 良い | 低 | ほとんどのタスク |
| `gemini-1.5-flash` | 非常に高速 | 良い | 非常に低い | 速度重視 |
| `gemini-1.5-pro` | 中 | 最高 | 高い | 重要な分析 |

モデルを変更するには、`src/models.py`を編集:
```python
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"  # デフォルト: "gemini-pro"
```

### コスト見積もり

**無料ティア（Google AI Studio）:**
- 1分あたり60リクエスト
- 開発には十分

**課金あり:**
- gemini-pro: 1K文字あたり約$0.0005
- 完全な研究クエリ: 約$0.01-0.05
- 100クエリ/日: 約$1-5/日

### トラブルシューティング

**404 models/gemini-pro not found:**
- https://makersuite.google.com/app/apikeyでAPIキーを確認
- Google Cloud ConsoleではなくGoogle AI Studioのキーを使用

**403 Permission denied:**
- https://makersuite.google.com/でクォータを確認
- より高いクォータのために課金を有効にする必要がある場合があります

**APIタイムアウト:**
- インターネット接続を確認
- 数分後に再試行
- 一時的にOllamaに切り替え

---

## いつどちらを使用するか

### Ollamaを使用する場合:

- **開発と反復** - 無料で無制限のテスト
- **プライバシーが必要** - 機密データはローカルに保持
- **オフライン作業** - インターネット不要
- **学習** - コストを気にせず実験

```bash
python scripts/utils/switch_model_provider.py ollama
python main.py run "テストクエリ" --graph quick_research
```

### Geminiを使用する場合:

- **本番実行** - 高速で一貫した結果
- **大規模評価** - 5-10倍高速
- **時間に敏感** - 迅速なターンアラウンドが必要
- **比較テスト** - 一貫したベンチマーク

```bash
python scripts/utils/switch_model_provider.py gemini
python main.py run "本番クエリ" --graph deep_research
```

### ハイブリッドアプローチ（推奨）

```bash
# 開発: Ollama（無料）
python scripts/utils/switch_model_provider.py ollama
python main.py run "テストクエリ" --graph quick_research

# 本番: Gemini（高速）
python scripts/utils/switch_model_provider.py gemini
python main.py run "最終分析" --graph deep_research
```

---

## モデル設定の詳細

### 現在のモデル割り当て

| タスク | Ollamaモデル | Geminiモデル |
|------|--------------|--------------|
| 計画 | llama3 | gemini-pro |
| 分析 | command-r | gemini-pro |
| 評価 | command-r | gemini-pro |
| 統合 | command-r | gemini-pro |
| 埋め込み | nomic-embed-text | N/A（Ollamaを使用） |

### モデルのカスタマイズ

`src/models.py`を編集:

```python
def get_planner_model():
    return _get_model(
        gemini_model="gemini-1.5-flash",  # 計画には高速
        ollama_model="llama3",
        temperature=0.7
    )

def get_evaluation_model():
    return _get_model(
        gemini_model="gemini-pro",       # 評価にはより良い品質
        ollama_model="command-r",
        temperature=0.5                   # より一貫性
    )
```

---

## パフォーマンスベンチマーク

### 20例の評価

| プロバイダー | 合計時間 | クエリあたり平均 | コスト |
|----------|------------|---------------|------|
| Gemini | 5-10分 | 15-30秒 | $0.01-0.05 |
| Ollama | 30-60分 | 90-180秒 | $0 |

### 複雑な階層的クエリ

| プロバイダー | 時間 | サブタスク | 備考 |
|----------|------|----------|-------|
| Gemini | 2-5分 | 5-7 | 一貫性あり |
| Ollama | 10-20分 | 5-7 | ハードウェア依存 |

---

## まとめ

- **開発**: Ollamaを使用（無料、無制限、プライベート）
- **本番**: Geminiを使用（高速、一貫性）
- **簡単に切り替え**: `python scripts/utils/switch_model_provider.py <provider>`
- **ステータス確認**: `python scripts/utils/switch_model_provider.py status`

---

## 次のステップ

- **[クイックスタート](quick-start.md)** - 最初のクエリを実行
- **[評価ガイド](../development/evaluation-guide.md)** - LangSmithでベンチマーク
- **[システム概要](../architecture/system-overview.md)** - アーキテクチャでのモデル使用を理解
