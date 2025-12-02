"""
Provenance機能のクイックデモ

既存のレポートデータを使用して、Provenance機能を素早く実演します。
"""

import json
from pathlib import Path
from datetime import datetime


def load_latest_report_data():
    """最新のテストレポートからソースデータを読み込む"""

    # Ultimate testの結果を使用 (script is in examples/provenance/)
    report_file = Path("../../reports/report_20251202_230148_simple_Ultimate_test_complete_citation_system_verificati.md")

    if not report_file.exists():
        print(f"❌ レポートファイルが見つかりません: {report_file}")
        return None

    # レポートを読み込み
    with open(report_file) as f:
        report_content = f.read()

    # Simulate state (実際の実行からソースデータを再構築)
    # Note: 実際のアプリケーションではgraph.invoke()から取得
    mock_state = {
        "query": "Ultimate test: complete citation system verification",
        "report": report_content,
        "web_sources": generate_mock_web_sources(35),
        "rag_sources": generate_mock_rag_sources(35)
    }

    return mock_state


def generate_mock_web_sources(count: int):
    """モックWebソースを生成（テストデータ）"""
    sources = []
    for i in range(1, count + 1):
        sources.append({
            "source_id": f"web_{i}",
            "source_type": "web",
            "title": f"Citation Verification Best Practices {i}",
            "url": f"https://example.com/citation-research-{i}",
            "content_snippet": f"This article discusses citation verification methods and their importance in academic research. Key findings include...",
            "relevance_score": 0.85 - (i * 0.01),
            "query_used": "citation verification best practices",
            "timestamp": datetime.now().isoformat()
        })
    return sources


def generate_mock_rag_sources(count: int):
    """モックKBソースを生成（テストデータ）"""
    sources = []
    kb_files = [
        "Causal Inference with Large Language Model A Survey.md",
        "Enhancing Ontologies with Large Language Models.pdf",
        "rough-alignment-algorithms-full-workflow.md"
    ]

    for i in range(1, count + 1):
        sources.append({
            "source_id": f"rag_{i}",
            "source_type": "rag",
            "title": f"Internal Documentation: Citation Systems Part {i}",
            "content_snippet": f"Our internal documentation on citation management systems highlights the importance of accuracy and consistency...",
            "relevance_score": 0.80 - (i * 0.015),
            "query_used": "citation system documentation",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "source_file": f"documents/{kb_files[i % len(kb_files)]}",
                "chunk_index": i,
                "full_content_length": 1500
            }
        })
    return sources


def export_citations_simple(state: dict, format: str = "bibtex"):
    """引用を指定されたフォーマットでエクスポート（簡易版）"""

    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])
    all_sources = web_sources + rag_sources

    if format == "bibtex":
        entries = []
        year = datetime.now().year

        for i, source in enumerate(all_sources[:5], 1):  # 最初の5つ
            source_type = source.get("source_type", "misc")
            title = source.get("title", "Unknown")
            url = source.get("url")

            key = f"source{year}_{i}"

            if source_type == "web" and url:
                entry = f"""@online{{{key},
  title = {{{title}}},
  url = {{{url}}},
  year = {{{year}}},
  note = {{Accessed: {datetime.now().strftime('%Y-%m-%d')}}}
}}"""
            else:
                file_path = source.get("metadata", {}).get("source_file", "Unknown")
                entry = f"""@techreport{{{key},
  title = {{{title}}},
  institution = {{Internal Knowledge Base}},
  year = {{{year}}},
  note = {{Source: {file_path}}}
}}"""

            entries.append(entry)

        return "\n\n".join(entries)

    elif format == "apa":
        citations = []
        year = datetime.now().year

        for i, source in enumerate(all_sources[:5], 1):
            title = source.get("title", "Unknown")
            source_type = source.get("source_type", "misc")
            url = source.get("url")

            if source_type == "web" and url:
                citation = f"{i}. {title}. ({year}). Retrieved from {url}"
            else:
                file_path = source.get("metadata", {}).get("source_file", "Unknown")
                citation = f"{i}. {title}. ({year}). Internal Knowledge Base. Source: {file_path}"

            citations.append(citation)

        return "\n\n".join(citations)

    elif format == "mla":
        citations = []
        access_date = datetime.now().strftime("%d %b. %Y")

        for i, source in enumerate(all_sources[:5], 1):
            title = source.get("title", "Unknown")
            source_type = source.get("source_type", "misc")
            url = source.get("url")

            if source_type == "web" and url:
                citation = f'{i}. "{title}." Web. {access_date}. <{url}>.'
            else:
                file_path = source.get("metadata", {}).get("source_file", "Unknown")
                citation = f'{i}. "{title}." Internal Knowledge Base. {access_date}. Source: {file_path}.'

            citations.append(citation)

        return "\n\n".join(citations)


def query_claim_provenance_simple(state: dict, claim: str):
    """特定の主張のソースを検索（簡易版）"""

    report = state.get("report", "")
    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])
    all_sources = web_sources + rag_sources

    # レポート内で主張を検索
    claim_lower = claim.lower()
    report_lower = report.lower()

    if claim_lower not in report_lower:
        return {
            "claim": claim,
            "found": False,
            "message": "主張がレポート内に見つかりませんでした"
        }

    # 主張の周辺テキストを取得
    pos = report_lower.index(claim_lower)
    start = max(0, pos - 150)
    end = min(len(report), pos + len(claim) + 150)
    context = report[start:end]

    # 引用番号を検索 [1], [2], etc.
    import re
    citation_pattern = r'\[(\d+)\]'
    citations = []

    for match in re.finditer(citation_pattern, context):
        cite_num = int(match.group(1))
        if 1 <= cite_num <= len(all_sources):
            source = all_sources[cite_num - 1]
            citations.append({
                "number": cite_num,
                "title": source.get("title", "Unknown"),
                "type": source.get("source_type", "unknown"),
                "relevance": source.get("relevance_score", 0.5)
            })

    return {
        "claim": claim,
        "found": True,
        "context": context,
        "citations": citations,
        "source_count": len(citations)
    }


def main():
    """メインデモ実行"""

    print("=" * 80)
    print("🔬 Test-Smith Provenance機能 - クイックデモ")
    print("=" * 80)
    print()

    # Step 1: レポートデータを読み込み
    print("📂 既存のレポートデータを読み込み中...")
    state = load_latest_report_data()

    if not state:
        print("❌ レポートデータの読み込みに失敗しました")
        return

    print("✅ データ読み込み完了\n")

    # Step 2: ソース統計を表示
    print("=" * 80)
    print("📈 ソース統計")
    print("=" * 80)
    print()

    web_sources = state.get("web_sources", [])
    rag_sources = state.get("rag_sources", [])

    print(f"総ソース数: {len(web_sources) + len(rag_sources)}")
    print(f"  - Web sources: {len(web_sources)}")
    print(f"  - Knowledge Base sources: {len(rag_sources)}")
    print()

    # Top 3 Web sources
    print("🌐 Top 3 Web Sources:")
    for source in web_sources[:3]:
        print(f"  • {source['title']}")
        print(f"    URL: {source['url']}")
        print(f"    Relevance: {source['relevance_score']:.2f}\n")

    # Top 3 KB sources
    print("📚 Top 3 Knowledge Base Sources:")
    for source in rag_sources[:3]:
        print(f"  • {source['title']}")
        print(f"    File: {source['metadata']['source_file']}")
        print(f"    Relevance: {source['relevance_score']:.2f}\n")

    # Step 3: 特定の主張の根拠を確認
    print("=" * 80)
    print("🔍 特定の主張の根拠を確認")
    print("=" * 80)
    print()

    claim_to_check = "Inaccurate citations can lead to errors"
    print(f"確認する主張: \"{claim_to_check}\"")
    print()

    provenance = query_claim_provenance_simple(state, claim_to_check)

    if provenance.get("found"):
        print(f"✅ 主張を発見")
        print(f"📚 支持ソース数: {provenance['source_count']}")
        print()

        if provenance.get("citations"):
            print("💡 この主張を支持するソース:")
            for citation in provenance["citations"][:3]:
                print(f"  [{citation['number']}] {citation['title']}")
                print(f"      Type: {citation['type']}")
                print(f"      Relevance: {citation['relevance']:.2f}\n")
    else:
        print(f"❌ {provenance.get('message')}")

    # Step 4: 引用を複数のフォーマットでエクスポート
    print("=" * 80)
    print("📄 引用をエクスポート (最初の5エントリのみ)")
    print("=" * 80)
    print()

    # BibTeX
    print("📖 BibTeX形式:")
    print("-" * 80)
    bibtex = export_citations_simple(state, format="bibtex")
    print(bibtex)
    print()

    # APA
    print("📘 APA形式:")
    print("-" * 80)
    apa = export_citations_simple(state, format="apa")
    print(apa)
    print()

    # MLA
    print("📗 MLA形式:")
    print("-" * 80)
    mla = export_citations_simple(state, format="mla")
    print(mla)
    print()

    # Step 5: 引用をファイルにエクスポート
    print("=" * 80)
    print("💾 引用をファイルにエクスポート")
    print("=" * 80)
    print()

    with open("../../citations/demo_citations_quick_bibtex.bib", "w") as f:
        f.write(export_citations_simple(state, format="bibtex"))
    print("✅ BibTeX引用を保存: citations/demo_citations_quick_bibtex.bib")

    with open("../../citations/demo_citations_quick_apa.txt", "w") as f:
        f.write(export_citations_simple(state, format="apa"))
    print("✅ APA引用を保存: citations/demo_citations_quick_apa.txt")

    with open("../../citations/demo_citations_quick_mla.txt", "w") as f:
        f.write(export_citations_simple(state, format="mla"))
    print("✅ MLA引用を保存: citations/demo_citations_quick_mla.txt")

    # サマリー
    print("\n" + "=" * 80)
    print("🎉 デモ完了！")
    print("=" * 80)
    print()
    print("生成されたファイル:")
    print("  1. citations/demo_citations_quick_bibtex.bib - BibTeX形式の引用")
    print("  2. citations/demo_citations_quick_apa.txt - APA形式の引用")
    print("  3. citations/demo_citations_quick_mla.txt - MLA形式の引用")
    print()
    print("💡 Provenance機能の使い方:")
    print()
    print("  # Pythonコード例:")
    print("  from src.provenance import query_claim_provenance, export_citations")
    print()
    print("  # 研究実行後")
    print('  result = graph.invoke({"query": "Your query"})')
    print()
    print("  # 主張の根拠を確認")
    print('  explanation = query_claim_provenance(result, "specific claim")')
    print()
    print("  # 引用をエクスポート")
    print('  bibtex = export_citations(result, format="bibtex")')
    print('  apa = export_citations(result, format="apa")')
    print('  mla = export_citations(result, format="mla")')
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  デモが中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
