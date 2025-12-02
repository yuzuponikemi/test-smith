"""
Provenance機能のデモンストレーション

このスクリプトは、Test-SmithのProvenance機能の使い方を実演します：
1. 研究クエリを実行
2. 特定の主張の根拠を確認
3. 引用を様々なフォーマットでエクスポート
4. ソース統計を表示
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.graphs import get_graph
from src.provenance import (
    query_claim_provenance,
    export_citations,
    get_sources_summary,
    list_claims,
    save_provenance
)


def demo_provenance_features():
    """Provenance機能の完全なデモを実行"""

    print("=" * 80)
    print("🔬 Test-Smith Provenance機能デモ")
    print("=" * 80)
    print()

    # Step 1: 研究クエリを実行
    print("📊 Step 1: 研究クエリを実行中...")
    print("Query: 'What are the key benefits of RAG systems?'")
    print()

    graph = get_graph("quick_research")

    initial_state = {
        "query": "What are the key benefits of RAG systems?"
    }

    print("⏳ グラフを実行中... (1-2分かかります)")
    result = graph.invoke(initial_state)
    print("✅ 研究完了！\n")

    # Step 2: ソース統計を表示
    print("=" * 80)
    print("📈 Step 2: ソース統計")
    print("=" * 80)

    summary = get_sources_summary(result)

    print(f"\n総ソース数: {summary['total']}")
    print(f"  - Web sources: {summary['web_count']}")
    print(f"  - Knowledge Base sources: {summary['rag_count']}\n")

    # Top 5 Web sources
    if summary['web_sources']:
        print("🌐 Top 5 Web Sources:")
        for source in summary['web_sources'][:5]:
            print(f"  • {source['title']}")
            print(f"    URL: {source['url']}")
            print(f"    Relevance: {source['relevance']:.2f}\n")

    # Top 5 KB sources
    if summary['rag_sources']:
        print("📚 Top 5 Knowledge Base Sources:")
        for source in summary['rag_sources'][:5]:
            print(f"  • {source['title']}")
            print(f"    File: {source['file']}")
            print(f"    Relevance: {source['relevance']:.2f}\n")

    # Step 3: 特定の主張の根拠を確認
    print("=" * 80)
    print("🔍 Step 3: 特定の主張の根拠を確認")
    print("=" * 80)
    print()

    # レポートから興味深い主張を抽出
    report = result.get("report", "")

    # 最初の実質的な文を取得
    sentences = [s.strip() for s in report.split('.') if len(s.strip()) > 50]
    if sentences:
        claim_to_check = sentences[0] + '.'
        print(f"主張を確認: \"{claim_to_check[:100]}...\"")
        print()

        # Provenance を確認
        provenance_result = query_claim_provenance(result, claim_to_check)

        print(f"📋 主張: {provenance_result.get('claim', 'N/A')[:100]}...")
        print(f"📊 信頼度: {provenance_result.get('confidence', 0):.2f}")
        print(f"📚 支持ソース数: {provenance_result.get('source_count', 0)}")
        print()

        sources = provenance_result.get('sources', [])
        if sources:
            print("💡 この主張を支持するソース:")
            for source in sources[:3]:  # Top 3
                print(f"\n  [{source['citation_number']}] {source['title']}")
                print(f"      Type: {source['type']}")
                if source.get('url'):
                    print(f"      URL: {source['url']}")
                if source.get('file'):
                    print(f"      File: {source['file']}")
                print(f"      Relevance: {source['relevance']:.2f}")

    # Step 4: 引用を複数のフォーマットでエクスポート
    print("\n" + "=" * 80)
    print("📄 Step 4: 引用をエクスポート")
    print("=" * 80)
    print()

    # BibTeX形式
    print("📖 BibTeX形式:")
    print("-" * 80)
    bibtex = export_citations(result, format="bibtex")
    # 最初の2エントリだけ表示
    bibtex_entries = bibtex.split('\n\n')
    for entry in bibtex_entries[:2]:
        print(entry)
        print()
    if len(bibtex_entries) > 2:
        print(f"... (他 {len(bibtex_entries) - 2} エントリ)\n")

    # APA形式
    print("📘 APA形式:")
    print("-" * 80)
    apa = export_citations(result, format="apa")
    apa_entries = apa.split('\n\n')
    for entry in apa_entries[:3]:
        print(entry)
    if len(apa_entries) > 3:
        print(f"\n... (他 {len(apa_entries) - 3} エントリ)\n")

    # MLA形式
    print("\n📗 MLA形式:")
    print("-" * 80)
    mla = export_citations(result, format="mla")
    mla_entries = mla.split('\n\n')
    for entry in mla_entries[:3]:
        print(entry)
    if len(mla_entries) > 3:
        print(f"\n... (他 {len(mla_entries) - 3} エントリ)\n")

    # Step 5: プロベナンスデータを保存
    print("\n" + "=" * 80)
    print("💾 Step 5: プロベナンスデータを保存")
    print("=" * 80)
    print()

    saved_path = save_provenance(result, output_path="demo_provenance_output.json")
    print(f"✅ プロベナンスデータを保存: {saved_path}")
    print()

    # 完全な引用リストをファイルにエクスポート
    with open("demo_citations_bibtex.bib", "w") as f:
        f.write(export_citations(result, format="bibtex"))
    print("✅ BibTeX引用を保存: demo_citations_bibtex.bib")

    with open("demo_citations_apa.txt", "w") as f:
        f.write(export_citations(result, format="apa"))
    print("✅ APA引用を保存: demo_citations_apa.txt")

    with open("demo_citations_mla.txt", "w") as f:
        f.write(export_citations(result, format="mla"))
    print("✅ MLA引用を保存: demo_citations_mla.txt")

    # Step 6: 生成されたレポートを保存
    print("\n" + "=" * 80)
    print("📝 Step 6: 完全なレポートを保存")
    print("=" * 80)
    print()

    report_path = "demo_research_report.md"
    with open(report_path, "w") as f:
        f.write(result.get("report", ""))
    print(f"✅ 研究レポートを保存: {report_path}")

    # サマリー
    print("\n" + "=" * 80)
    print("🎉 デモ完了！")
    print("=" * 80)
    print()
    print("生成されたファイル:")
    print(f"  1. {report_path} - 完全な研究レポート（引用付き）")
    print(f"  2. demo_provenance_output.json - プロベナンスデータ")
    print(f"  3. demo_citations_bibtex.bib - BibTeX形式の引用")
    print(f"  4. demo_citations_apa.txt - APA形式の引用")
    print(f"  5. demo_citations_mla.txt - MLA形式の引用")
    print()
    print("💡 これらのファイルを使って:")
    print("   - レポートを論文に含める")
    print("   - BibTeXをLaTeXで使用")
    print("   - プロベナンスデータで主張を検証")
    print()


if __name__ == "__main__":
    try:
        demo_provenance_features()
    except KeyboardInterrupt:
        print("\n\n⚠️  デモが中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
