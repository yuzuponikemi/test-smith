# Provenance機能 デモスクリプト

このディレクトリには、Test-SmithのProvenance機能（ソース追跡・引用エクスポート）を実演するデモスクリプトが含まれています。

## スクリプト一覧

### 1. `demo_provenance_quick.py` - クイックデモ（モックデータ使用）

既存のレポートデータを使用して、Provenance機能を素早く実演します。

**特徴:**
- モックデータ使用（実際のグラフ実行不要）
- 5つのソースでデモ
- 3つのフォーマット（BibTeX, APA, MLA）で引用をエクスポート

**実行方法:**
```bash
cd examples/provenance
python demo_provenance_quick.py
```

**生成ファイル:**
- `citations/demo_citations_quick_bibtex.bib`
- `citations/demo_citations_quick_apa.txt`
- `citations/demo_citations_quick_mla.txt`

---

### 2. `test_real_provenance.py` - 実データテスト

最新の研究レポートからProvenance機能を実際に使用します。

**特徴:**
- 実際のレポートファイルを解析
- 全ソースの統計表示
- 特定の主張の根拠を確認
- 3つのフォーマットで引用をエクスポート

**実行方法:**
```bash
# まず、研究を実行してレポートを生成
cd ../..  # プロジェクトルートに戻る
python main.py run "Your research query" --graph quick_research

# 次に、デモスクリプトを実行
cd examples/provenance
python test_real_provenance.py
```

**生成ファイル:**
- `citations/real_citations_bibtex.bib`
- `citations/real_citations_apa.txt`
- `citations/real_citations_mla.txt`

---

### 3. `demo_provenance.py` - フル機能デモ

グラフ実行から引用エクスポートまで、完全なフローをデモします。

**特徴:**
- 実際にグラフを実行
- Provenance機能をフルに使用
- ソース追跡、主張の根拠確認、引用エクスポートをすべて実演

**実行方法:**
```bash
cd examples/provenance
python demo_provenance.py
```

---

## 実際の使用方法

Provenance機能を実際のプロジェクトで使用する場合：

```python
from src.graphs import get_graph
from src.provenance import (
    query_claim_provenance,
    export_citations,
    get_sources_summary
)

# 1. 研究を実行
graph = get_graph("quick_research")
result = graph.invoke({"query": "Your research query"})

# 2. ソース統計を確認
summary = get_sources_summary(result)
print(f"Total sources: {summary['total']}")

# 3. 特定の主張の根拠を確認
provenance = query_claim_provenance(result, "specific claim")
print(f"Supporting sources: {provenance['source_count']}")

# 4. 引用をエクスポート
bibtex = export_citations(result, format="bibtex")
apa = export_citations(result, format="apa")
mla = export_citations(result, format="mla")

# ファイルに保存
with open("citations/my_citations.bib", "w") as f:
    f.write(bibtex)
```

---

## ドキュメント

完全なドキュメントは以下を参照：
- **[docs/PROVENANCE_GUIDE.md](../../docs/PROVENANCE_GUIDE.md)** - 完全ガイド

---

## 注意事項

- すべてのスクリプトは `examples/provenance/` ディレクトリから実行してください
- 生成された引用ファイルは `citations/` ディレクトリに保存されます
- 引用ファイルは `.gitignore` で除外されています（自動生成されるため）
