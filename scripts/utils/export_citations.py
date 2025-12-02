#!/usr/bin/env python3
"""
Export Research Citations

Exports research provenance data to various academic citation formats:
- BibTeX (for LaTeX)
- APA (American Psychological Association)
- MLA (Modern Language Association)
- JSON (structured data)
- Markdown (with links)

Usage:
    python scripts/utils/export_citations.py provenance_graph.json --format bibtex
    python scripts/utils/export_citations.py provenance_graph.json --format apa --output refs.txt
    python scripts/utils/export_citations.py provenance_graph.json --format all
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def sanitize_bibtex_key(title: str, index: int) -> str:
    """Generate a valid BibTeX key from title."""
    # Extract first word and clean it
    words = re.sub(r"[^a-zA-Z0-9\s]", "", title).split()
    first_word = words[0].lower() if words else "source"
    year = datetime.now().year
    return f"{first_word}{year}_{index}"


def format_bibtex(sources: list) -> str:
    """Format sources as BibTeX entries."""
    entries = []

    for i, source in enumerate(sources, 1):
        source_id = source.get("source_id", f"source_{i}")
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        timestamp = source.get("timestamp", "")
        source_type = source.get("source_type", "web")

        # Parse access date
        try:
            access_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            access_str = access_date.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            access_str = datetime.now().strftime("%Y-%m-%d")

        key = sanitize_bibtex_key(title, i)

        if source_type == "web" and url:
            entry = f"""@misc{{{key},
    title = {{{title}}},
    howpublished = {{\\url{{{url}}}}},
    note = {{Accessed: {access_str}}},
    year = {{{datetime.now().year}}}
}}"""
        else:
            # For KB documents
            entry = f"""@techreport{{{key},
    title = {{{title}}},
    institution = {{Internal Knowledge Base}},
    note = {{Document ID: {source_id}}},
    year = {{{datetime.now().year}}}
}}"""

        entries.append(entry)

    return "\n\n".join(entries)


def format_apa(sources: list) -> str:
    """Format sources as APA citations."""
    citations = []

    for source in sources:
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        timestamp = source.get("timestamp", "")
        source_type = source.get("source_type", "web")

        # Parse dates
        try:
            access_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            access_str = access_date.strftime("%B %d, %Y")
            year = access_date.year
        except (ValueError, AttributeError):
            access_str = datetime.now().strftime("%B %d, %Y")
            year = datetime.now().year

        if source_type == "web" and url:
            citation = f"{title}. ({year}). Retrieved {access_str}, from {url}"
        else:
            citation = f"{title}. ({year}). Internal Knowledge Base."

        citations.append(citation)

    return "\n\n".join(citations)


def format_mla(sources: list) -> str:
    """Format sources as MLA citations."""
    citations = []

    for source in sources:
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        timestamp = source.get("timestamp", "")
        source_type = source.get("source_type", "web")

        # Parse access date
        try:
            access_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            access_str = access_date.strftime("%d %b. %Y")
        except (ValueError, AttributeError):
            access_str = datetime.now().strftime("%d %b. %Y")

        if source_type == "web" and url:
            citation = f'"{title}." Web. {access_str}. <{url}>.'
        else:
            citation = f'"{title}." Internal Knowledge Base. {access_str}.'

        citations.append(citation)

    return "\n\n".join(citations)


def format_markdown(sources: list) -> str:
    """Format sources as Markdown with links."""
    lines = ["# Research Sources\n"]

    # Group by source type
    web_sources = [s for s in sources if s.get("source_type") == "web"]
    rag_sources = [s for s in sources if s.get("source_type") == "rag"]

    if web_sources:
        lines.append("## Web Sources\n")
        for i, source in enumerate(web_sources, 1):
            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            query = source.get("query_used", "")
            relevance = source.get("relevance_score", 0)

            if url:
                lines.append(f"{i}. [{title}]({url})")
            else:
                lines.append(f"{i}. {title}")

            if query:
                lines.append(f"   - Query: *{query}*")
            lines.append(f"   - Relevance: {relevance:.2f}\n")

    if rag_sources:
        lines.append("## Knowledge Base Sources\n")
        for i, source in enumerate(rag_sources, 1):
            title = source.get("title", "Unknown Title")
            query = source.get("query_used", "")
            relevance = source.get("relevance_score", 0)
            source_file = source.get("metadata", {}).get("source_file", "")

            lines.append(f"{i}. **{title}**")
            if source_file:
                lines.append(f"   - File: `{source_file}`")
            if query:
                lines.append(f"   - Query: *{query}*")
            lines.append(f"   - Relevance: {relevance:.2f}\n")

    return "\n".join(lines)


def format_json_export(graph_data: dict) -> str:
    """Export full structured data as formatted JSON."""
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "metadata": graph_data.get("metadata", {}),
        "sources": graph_data.get("sources", []),
        "evidence": graph_data.get("evidence", []),
        "claims": graph_data.get("claims", []),
        "lineage": {
            "nodes": len(graph_data.get("nodes", [])),
            "edges": len(graph_data.get("edges", [])),
        },
    }
    return json.dumps(export_data, indent=2)


def export_citations(graph_data: dict, format_type: str) -> str:
    """Export citations in the specified format."""
    sources = graph_data.get("sources", [])

    if not sources:
        return "No sources available for export."

    formatters = {
        "bibtex": format_bibtex,
        "apa": format_apa,
        "mla": format_mla,
        "markdown": format_markdown,
    }

    if format_type == "json":
        return format_json_export(graph_data)
    elif format_type in formatters:
        return formatters[format_type](sources)
    else:
        return f"Unknown format: {format_type}"


def main():
    parser = argparse.ArgumentParser(description="Export Research Citations to various formats")
    parser.add_argument("input_file", help="Path to JSON file containing provenance graph data")
    parser.add_argument(
        "--format",
        "-f",
        choices=["bibtex", "apa", "mla", "markdown", "json", "all"],
        default="bibtex",
        help="Citation format (default: bibtex)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")

    args = parser.parse_args()

    # Load graph data
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    with open(input_path) as f:
        graph_data = json.load(f)

    # Export in requested format(s)
    if args.format == "all":
        formats = ["bibtex", "apa", "mla", "markdown", "json"]
        output_dir = Path(args.output) if args.output else Path(".")

        if args.output:
            output_dir.mkdir(parents=True, exist_ok=True)

        for fmt in formats:
            content = export_citations(graph_data, fmt)

            ext = {
                "bibtex": ".bib",
                "apa": ".txt",
                "mla": ".txt",
                "markdown": ".md",
                "json": ".json",
            }[fmt]

            output_file = output_dir / f"citations_{fmt}{ext}"
            with open(output_file, "w") as f:
                f.write(content)
            print(f"Exported {fmt} to: {output_file}")
    else:
        content = export_citations(graph_data, args.format)

        if args.output:
            with open(args.output, "w") as f:
                f.write(content)
            print(f"Exported to: {args.output}")
        else:
            print(content)


if __name__ == "__main__":
    main()
