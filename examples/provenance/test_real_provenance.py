"""
実際のグラフ実行結果でProvenance機能をテスト

このスクリプトは、先ほど実行した研究のレポートを読み込み、
Provenance機能を実際に使用して、ソース追跡と引用エクスポートを実演します。
"""

import json
from pathlib import Path
from datetime import datetime


def load_latest_report():
    """最新のレポートファイルを読み込む"""
    # Script is in examples/provenance/, reports are in ../../reports/
    reports_dir = Path("../../reports")

    # 最新のレポートを探す
    report_files = sorted(reports_dir.glob("report_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not report_files:
        print("❌ レポートファイルが見つかりません")
        return None

    latest = report_files[0]
    print(f"📄 最新レポート: {latest.name}")

    with open(latest) as f:
        content = f.read()

    return content


def extract_references(report_content: str) -> list:
    """レポートからReferencesセクションを抽出"""
    if "**References**" not in report_content:
        return []

    references_section = report_content.split("**References**")[1]

    # 各ソースを解析
    sources = []
    lines = references_section.strip().split("\n")

    current_source = {}
    for line in lines:
        line = line.strip()

        # ソース番号（例: 1. "Title"）
        if line and line[0].isdigit() and ". " in line:
            if current_source:
                sources.append(current_source)

            # タイトルとタイプを抽出
            parts = line.split(" - Type: ")
            title = parts[0].split(". ", 1)[1].strip('"')
            source_type = parts[1] if len(parts) > 1 else "Unknown"

            current_source = {
                "number": int(line.split(".")[0]),
                "title": title,
                "type": source_type
            }

        # URL行
        elif line.startswith("URL:"):
            current_source["url"] = line.replace("URL:", "").strip()

        # File行
        elif line.startswith("File:"):
            current_source["file"] = line.replace("File:", "").strip()

        # Relevance行
        elif line.startswith("Relevance:"):
            relevance_str = line.replace("Relevance:", "").strip()
            current_source["relevance"] = float(relevance_str)

    if current_source:
        sources.append(current_source)

    return sources


def export_citations_real(sources: list, format: str = "bibtex") -> str:
    """実際のソースから引用をエクスポート"""

    if format == "bibtex":
        entries = []
        year = datetime.now().year

        for source in sources:
            source_num = source["number"]
            title = source.get("title", "Unknown")
            source_type = source.get("type", "Unknown")
            key = f"source{year}_{source_num}"

            if source_type == "Web" and "url" in source:
                url = source["url"]
                entry = f"""@online{{{key},
  title = {{{title}}},
  url = {{{url}}},
  year = {{{year}}},
  note = {{Accessed: {datetime.now().strftime('%Y-%m-%d')}}}
}}"""
            else:
                file_path = source.get("file", "Unknown")
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

        for source in sources:
            source_num = source["number"]
            title = source.get("title", "Unknown")
            source_type = source.get("type", "Unknown")

            if source_type == "Web" and "url" in source:
                url = source["url"]
                citation = f"{source_num}. {title}. ({year}). Retrieved from {url}"
            else:
                file_path = source.get("file", "Unknown")
                citation = f"{source_num}. {title}. ({year}). Internal Knowledge Base. Source: {file_path}"

            citations.append(citation)

        return "\n\n".join(citations)

    elif format == "mla":
        citations = []
        access_date = datetime.now().strftime("%d %b. %Y")

        for source in sources:
            source_num = source["number"]
            title = source.get("title", "Unknown")
            source_type = source.get("type", "Unknown")

            if source_type == "Web" and "url" in source:
                url = source["url"]
                citation = f'{source_num}. "{title}." Web. {access_date}. <{url}>.'
            else:
                file_path = source.get("file", "Unknown")
                citation = f'{source_num}. "{title}." Internal Knowledge Base. {access_date}. Source: {file_path}.'

            citations.append(citation)

        return "\n\n".join(citations)


def query_claim_in_report(report: str, sources: list, claim: str):
    """レポート内の特定の主張を検索してソースを見つける"""

    # レポート内で主張を検索
    report_lower = report.lower()
    claim_lower = claim.lower()

    if claim_lower not in report_lower:
        return {
            "claim": claim,
            "found": False,
            "message": "主張がレポート内に見つかりませんでした"
        }

    # 主張の周辺テキストを取得
    pos = report_lower.index(claim_lower)
    start = max(0, pos - 200)
    end = min(len(report), pos + len(claim) + 200)
    context = report[start:end]

    # 引用番号を検索 [1], [2], etc.
    import re
    citation_pattern = r'\[(\d+)\]'
    cited_sources = []

    for match in re.finditer(citation_pattern, context):
        cite_num = int(match.group(1))

        # ソースを探す
        for source in sources:
            if source["number"] == cite_num:
                cited_sources.append(source)
                break

    return {
        "claim": claim,
        "found": True,
        "context": context.strip(),
        "sources": cited_sources,
        "source_count": len(cited_sources)
    }


def main():
    """メイン実行"""

    print("=" * 80)
    print("🔬 Test-Smith Provenance機能 - 実際のデータでテスト")
    print("=" * 80)
    print()

    # Step 1: 最新のレポートを読み込み
    print("📂 最新のレポートを読み込み中...")
    report_content = load_latest_report()

    if not report_content:
        return

    print("✅ レポート読み込み完了\n")

    # Step 2: Referencesセクションを解析
    print("=" * 80)
    print("📖 References セクションを解析")
    print("=" * 80)
    print()

    sources = extract_references(report_content)

    if not sources:
        print("❌ ソースが見つかりませんでした")
        return

    # ソース統計
    web_sources = [s for s in sources if s.get("type") == "Web"]
    kb_sources = [s for s in sources if s.get("type") == "Knowledge Base"]

    print(f"総ソース数: {len(sources)}")
    print(f"  - Web sources: {len(web_sources)}")
    print(f"  - Knowledge Base sources: {len(kb_sources)}")
    print()

    # Top 3 sources
    print("🏆 Top 3 Sources:")
    for source in sources[:3]:
        print(f"  [{source['number']}] {source['title']}")
        print(f"      Type: {source['type']}")
        if "url" in source:
            print(f"      URL: {source['url']}")
        if "file" in source:
            print(f"      File: {source['file']}")
        if "relevance" in source:
            print(f"      Relevance: {source['relevance']:.2f}")
        print()

    # Step 3: 特定の主張の根拠を確認
    print("=" * 80)
    print("🔍 特定の主張の根拠を確認")
    print("=" * 80)
    print()

    # レポート内のキーワードを使って主張を探す
    test_claims = [
        "RAG",
        "retrieval",
        "accuracy"
    ]

    for claim_word in test_claims:
        if claim_word.lower() in report_content.lower():
            # このキーワードを含む文を抽出
            sentences = report_content.split(".")
            for sentence in sentences:
                if claim_word.lower() in sentence.lower() and len(sentence.strip()) > 20:
                    claim = sentence.strip()[:100]  # 最初の100文字
                    break
            else:
                continue

            print(f"主張: \"{claim}...\"")
            print()

            provenance = query_claim_in_report(report_content, sources, claim)

            if provenance.get("found") and provenance.get("source_count") > 0:
                print(f"✅ この主張を支持するソース数: {provenance['source_count']}")
                print()
                print("💡 支持ソース:")
                for source in provenance["sources"][:3]:
                    print(f"  [{source['number']}] {source['title']}")
                    print(f"      Type: {source['type']}")
                    if "relevance" in source:
                        print(f"      Relevance: {source['relevance']:.2f}")
                print()

            break  # 1つだけテスト

    # Step 4: 引用を複数のフォーマットでエクスポート
    print("=" * 80)
    print("📄 引用を複数フォーマットでエクスポート")
    print("=" * 80)
    print()

    # 最初の5ソースのみ
    sources_subset = sources[:5]

    # BibTeX
    print("📖 BibTeX形式 (最初の5エントリ):")
    print("-" * 80)
    bibtex = export_citations_real(sources_subset, format="bibtex")
    print(bibtex)
    print()

    # APA
    print("📘 APA形式 (最初の5エントリ):")
    print("-" * 80)
    apa = export_citations_real(sources_subset, format="apa")
    print(apa)
    print()

    # MLA
    print("📗 MLA形式 (最初の5エントリ):")
    print("-" * 80)
    mla = export_citations_real(sources_subset, format="mla")
    print(mla)
    print()

    # Step 5: ファイルにエクスポート
    print("=" * 80)
    print("💾 引用をファイルにエクスポート")
    print("=" * 80)
    print()

    with open("../../citations/real_citations_bibtex.bib", "w") as f:
        f.write(export_citations_real(sources, format="bibtex"))
    print("✅ BibTeX引用を保存: citations/real_citations_bibtex.bib")

    with open("../../citations/real_citations_apa.txt", "w") as f:
        f.write(export_citations_real(sources, format="apa"))
    print("✅ APA引用を保存: citations/real_citations_apa.txt")

    with open("../../citations/real_citations_mla.txt", "w") as f:
        f.write(export_citations_real(sources, format="mla"))
    print("✅ MLA引用を保存: citations/real_citations_mla.txt")

    # サマリー
    print("\n" + "=" * 80)
    print("🎉 実際のデータでのProvenance機能テスト完了！")
    print("=" * 80)
    print()
    print(f"総ソース数: {len(sources)}")
    print(f"  - Web: {len(web_sources)}")
    print(f"  - Knowledge Base: {len(kb_sources)}")
    print()
    print("生成されたファイル:")
    print("  1. citations/real_citations_bibtex.bib - BibTeX形式の引用")
    print("  2. citations/real_citations_apa.txt - APA形式の引用")
    print("  3. citations/real_citations_mla.txt - MLA形式の引用")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
