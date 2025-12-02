# Provenance機能 完全ガイド

Test-SmithのProvenance機能を使用すると、研究レポートの主張を元のソースまで追跡し、引用を様々なフォーマットでエクスポートできます。

## 📋 目次

1. [クイックスタート](#クイックスタート)
2. [主な機能](#主な機能)
3. [実際の使用例](#実際の使用例)
4. [生成される成果物](#生成される成果物)
5. [API リファレンス](#apiリファレンス)

---

## クイックスタート

### 基本的な使い方

```python
from src.graphs import get_graph
from src.provenance import (
    query_claim_provenance,
    export_citations,
    get_sources_summary
)

# 1. 研究を実行
graph = get_graph("quick_research")
result = graph.invoke({"query": "What are the benefits of RAG systems?"})

# 2. ソース統計を確認
summary = get_sources_summary(result)
print(f"Total sources: {summary['total']}")
print(f"Web: {summary['web_count']}, KB: {summary['rag_count']}")

# 3. 特定の主張の根拠を確認
provenance = query_claim_provenance(result, "RAG improves accuracy")
print(f"Supporting sources: {provenance['source_count']}")

# 4. 引用をエクスポート
bibtex = export_citations(result, format="bibtex")
apa = export_citations(result, format="apa")
mla = export_citations(result, format="mla")
```

### デモを実行

クイックデモを実行して機能を試します：

```bash
python demo_provenance_quick.py
```

**生成されるファイル:**
- `demo_citations_quick_bibtex.bib` - BibTeX形式の引用
- `demo_citations_quick_apa.txt` - APA形式の引用
- `demo_citations_quick_mla.txt` - MLA形式の引用

---

## 主な機能

### 1. ソース追跡 (Source Tracking)

すべてのソース（WebとKnowledge Base）が自動的に追跡されます：

```python
summary = get_sources_summary(result)

# Web sources
for source in summary['web_sources']:
    print(f"{source['title']}: {source['url']}")

# Knowledge Base sources
for source in summary['rag_sources']:
    print(f"{source['title']}: {source['file']}")
```

### 2. 主張の根拠確認 (Claim Provenance)

レポート内の特定の主張がどのソースから来たか確認：

```python
provenance = query_claim_provenance(
    result,
    claim="RAG systems improve retrieval accuracy"
)

print(f"Claim: {provenance['claim']}")
print(f"Confidence: {provenance['confidence']}")
print(f"Supporting sources: {provenance['source_count']}")

for source in provenance['sources']:
    print(f"  [{source['citation_number']}] {source['title']}")
    print(f"      Relevance: {source['relevance']:.2f}")
```

### 3. 引用エクスポート (Citation Export)

複数の学術フォーマットをサポート：

#### BibTeX (LaTeX用)

```python
bibtex = export_citations(result, format="bibtex")
# LaTeX論文で使用可能
```

**出力例:**
```bibtex
@online{source2025_1,
  title = {Citation Verification Best Practices},
  url = {https://example.com/citation-research-1},
  year = {2025},
  note = {Accessed: 2025-12-02}
}
```

#### APA Style (社会科学用)

```python
apa = export_citations(result, format="apa")
```

**出力例:**
```
1. Citation Verification Best Practices. (2025). Retrieved from https://example.com/citation-research-1
```

#### MLA Style (人文科学用)

```python
mla = export_citations(result, format="mla")
```

**出力例:**
```
1. "Citation Verification Best Practices." Web. 02 Dec. 2025. <https://example.com/citation-research-1>.
```

---

## 実際の使用例

### ケース1: 論文執筆での使用

```python
# 研究を実行
result = graph.invoke({"query": "Evolution of neural networks"})

# BibTeX をエクスポートして LaTeX で使用
with open("references.bib", "w") as f:
    f.write(export_citations(result, format="bibtex"))

# LaTeX論文で使用:
# \cite{source2025_1}
```

### ケース2: レポート検証

```python
# レポート内の主張を検証
claims_to_verify = [
    "Neural networks were inspired by biological neurons",
    "Deep learning requires large datasets",
    "Transformers revolutionized NLP"
]

for claim in claims_to_verify:
    prov = query_claim_provenance(result, claim)
    print(f"\nClaim: {claim}")
    print(f"Evidence strength: {prov['source_count']} sources")
    print(f"Confidence: {prov['confidence']:.2f}")
```

### ケース3: ソース品質分析

```python
summary = get_sources_summary(result)

# 高品質ソースをフィルタ (relevance > 0.7)
high_quality_web = [
    s for s in summary['web_sources']
    if s['relevance'] > 0.7
]

high_quality_kb = [
    s for s in summary['rag_sources']
    if s['relevance'] > 0.7
]

print(f"High-quality sources: {len(high_quality_web + high_quality_kb)}")
```

---

## 生成される成果物

### 1. 研究レポート (Markdown)

**場所:** `reports/report_YYYYMMDD_HHMMSS_*.md`

**内容:**
- レポート本文（引用番号付き [1], [2], etc.）
- 完全なReferencesセクション（すべてのソース）
- メタデータ（クエリ、タイムスタンプ、etc.）

**例:**
```markdown
**Citation Verification in Academic Research**

Inaccurate citations can lead to errors [1]. Verification
methods include lateral reading [2] and automated tools [3].

**References**

1. "Citation Verification with AI" - Type: Web
   URL: https://arxiv.org/...
   Relevance: 0.85

2. "Internal Documentation: Citations" - Type: Knowledge Base
   File: documents/citation-guide.md
   Relevance: 0.92
```

### 2. BibTeX引用ファイル (.bib)

**使用方法:**
```latex
\documentclass{article}
\usepackage{natbib}

\begin{document}
Neural networks were inspired by biological neurons \cite{source2025_1}.

\bibliographystyle{plain}
\bibliography{references}
\end{document}
```

### 3. プロベナンスデータ (JSON)

```python
from src.provenance import save_provenance

path = save_provenance(result, output_path="provenance_data.json")
```

**JSON構造:**
```json
{
  "query": "Your research query",
  "provenance_graph": {
    "sources": [...],
    "evidence": [...],
    "claims": [...]
  },
  "metadata": {
    "exported_at": "2025-12-02T23:01:48",
    "web_source_count": 35,
    "rag_source_count": 35
  }
}
```

---

## API リファレンス

### `query_claim_provenance(state, claim)`

特定の主張の根拠を確認します。

**パラメータ:**
- `state` (dict): グラフ実行結果
- `claim` (str): 確認したい主張のテキスト

**戻り値:**
```python
{
    "claim": "検索された主張",
    "found": True,
    "sources": [
        {
            "citation_number": 1,
            "title": "ソースタイトル",
            "type": "web" or "rag",
            "relevance": 0.85
        }
    ],
    "source_count": 3,
    "confidence": 0.92
}
```

### `export_citations(state, format)`

引用を指定フォーマットでエクスポートします。

**パラメータ:**
- `state` (dict): グラフ実行結果
- `format` (str): "bibtex", "apa", "mla", "chicago" のいずれか

**戻り値:** フォーマットされた引用文字列

### `get_sources_summary(state)`

ソース統計を取得します。

**戻り値:**
```python
{
    "total": 70,
    "web_count": 35,
    "rag_count": 35,
    "web_sources": [...],
    "rag_sources": [...]
}
```

### `save_provenance(state, output_path)`

プロベナンスデータをJSONで保存します。

**パラメータ:**
- `state` (dict): グラフ実行結果
- `output_path` (str): 保存先パス（省略可）

**戻り値:** 保存されたファイルパス

---

## 実装の詳細

### ソース追跡の仕組み

1. **Searcher Node** (`src/nodes/searcher_node.py`)
   - Webソースをキャプチャ
   - `web_sources` リストに追加
   - タイトル、URL、関連度スコアを記録

2. **RAG Retriever Node** (`src/nodes/rag_retriever_node.py`)
   - Knowledge Baseソースをキャプチャ
   - `rag_sources` リストに追加
   - タイトル、ファイルパス、関連度スコアを記録

3. **Synthesizer Node** (`src/nodes/synthesizer_node.py`)
   - すべてのソースをReferencesセクションに追加
   - プログラムで完全なメタデータを含むリストを生成
   - レポート本文に引用番号を含める

### 引用番号の対応

レポート内の `[1]`, `[2]` などの引用番号は、Referencesセクションの番号と対応：

```markdown
... this is supported by research [1, 3] ...

**References**
1. "First Source" - Type: Web
2. "Second Source" - Type: KB
3. "Third Source" - Type: Web
```

---

## トラブルシューティング

### 引用が表示されない

**原因:** プロベナンス機能が有効になっていない

**解決:** `quick_research` または `deep_research` グラフを使用してください：
```python
graph = get_graph("quick_research")  # ✅ 正しい
```

### ソース数が0

**原因:** RAG embedding dimensionのミスマッチ

**解決:** ChromaDB collectionのメタデータを確認：
```python
import chromadb
client = chromadb.PersistentClient(path='chroma_db')
collection = client.get_collection('research_agent_collection')
print(collection.metadata)  # embedding_modelを確認
```

### 引用フォーマットが不完全

**問題:** これは既に修正されています（Synthesizerのポストプロセッシング）

**確認:** `src/nodes/synthesizer_node.py:224-289` を参照

---

## まとめ

Provenance機能を使用すると：

✅ **すべてのソースを追跡** - WebとKnowledge Base両方
✅ **主張の根拠を確認** - "Why do you say that?"
✅ **複数の学術フォーマットをサポート** - BibTeX, APA, MLA, Chicago
✅ **論文執筆をサポート** - LaTeX、Wordなどで直接使用可能
✅ **研究の透明性を向上** - 完全なソース追跡

**今すぐ試す:**
```bash
python demo_provenance_quick.py
```
