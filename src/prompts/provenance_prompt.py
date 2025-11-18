"""
Prompts for Research Provenance & Lineage Tracking.

These prompts help extract claims, evidence, and their relationships
from analyzed data, enabling "Why do you say that?" queries and
visualization of reasoning chains.
"""

PROVENANCE_ANALYSIS_PROMPT = """You are an expert at analyzing research findings and extracting structured provenance information.

Your task is to analyze the research content and extract:
1. **Claims** - Key assertions, findings, or conclusions made
2. **Evidence** - Supporting information for each claim
3. **Source Attribution** - Which sources support which evidence

## Research Query
{query}

## Sources Available
{sources_summary}

## Analyzed Content
{analyzed_content}

## Instructions

Carefully extract all significant claims from the analyzed content and trace them back to their supporting evidence and sources.

For each claim:
- Identify the specific statement or assertion being made
- Classify the claim type (fact, analysis, synthesis, recommendation, opinion)
- Find the evidence that supports it
- Link evidence to specific source IDs
- Assess confidence based on evidence strength

Return a JSON object with this structure:
{{
    "claims": [
        {{
            "claim_id": "claim_1",
            "statement": "The specific claim being made",
            "claim_type": "fact|analysis|synthesis|recommendation|opinion",
            "evidence_ids": ["ev_1", "ev_2"],
            "confidence": 0.0-1.0,
            "location_in_report": "section or context where this appears"
        }}
    ],
    "evidence_items": [
        {{
            "evidence_id": "ev_1",
            "content": "The actual evidence text",
            "source_ids": ["web_1", "rag_3"],
            "extraction_method": "direct_quote|paraphrase|synthesis|inference",
            "confidence": 0.0-1.0
        }}
    ],
    "confidence_assessment": "Overall assessment of evidence quality and provenance clarity"
}}

Be thorough but precise. Only include claims that have clear evidence support.
Ensure every claim can be traced back to at least one source through evidence."""

PROVENANCE_QUERY_PROMPT = """You are explaining the reasoning chain behind a specific claim from a research report.

## The Claim
{claim_statement}

## Supporting Evidence
{evidence_items}

## Original Sources
{source_details}

## Task

Explain in clear, concise language:
1. What evidence supports this claim
2. Where that evidence came from (which sources)
3. How confident we can be in this claim
4. Any caveats or limitations

Write your explanation as if answering the question "Why do you say that?" from a curious reader.
Keep it informative but not overly technical. Reference specific sources when explaining."""

CITATION_EXTRACTION_PROMPT = """Extract citation metadata from these sources for academic export.

## Sources
{sources}

For each source, extract:
- Title (or generate descriptive title if missing)
- Authors (if available, otherwise "Unknown")
- Publication date (if available)
- URL (for web sources)
- Access date
- Source type (webpage, document, database, etc.)

Return as a JSON array of citation objects:
[
    {{
        "citation_id": "cite_1",
        "source_id": "web_1",
        "title": "Source title",
        "authors": ["Author Name"],
        "publication_date": "2024-01-15",
        "url": "https://...",
        "access_date": "2024-03-20",
        "source_type": "webpage"
    }}
]

Generate reasonable titles for sources without clear titles based on their content."""
