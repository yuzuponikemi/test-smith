"""
Outline Generator Prompt - Phase 2.1

Generates a structured outline from aggregated research findings.
Based on Stanford STORM's pre-writing approach.
"""

from langchain_core.prompts import PromptTemplate

OUTLINE_GENERATOR_PROMPT = PromptTemplate.from_template(
    """You are an expert report architect. Your task is to create a comprehensive outline
for a research report based on the provided findings.

## Original Research Query
{original_query}

## Research Depth Level
{research_depth}

## Target Language
{target_language}
IMPORTANT: Generate ALL outline content (title, headings, points) in {target_language}.

## Aggregated Research Findings
{findings_summary}

## Cross-cutting Themes Identified
{themes}

## Coverage Gaps (areas that may need attention)
{coverage_gaps}

## Target Word Count
{target_word_count} words

---

## Your Task

Create a detailed outline for the final report that:

1. **Title**: Create a compelling, informative title in {target_language}
2. **Executive Summary Points**: List 3-5 key takeaways (these will become the summary)
3. **Main Sections**: Design 4-8 logical sections that:
   - Cover all major aspects of the query
   - Group related findings together
   - Follow a logical flow (introduction → analysis → conclusions)
   - Allocate word count proportionally to importance
4. **Conclusion Points**: List 3-5 key conclusions/recommendations

For each section, specify:
- Section heading (in {target_language})
- 2-4 subheadings
- Which findings are relevant (by subtask ID)
- Key points to cover
- Target word count

## Output Format

Respond with a JSON object:

```json
{{
    "title": "Report title in {target_language}",
    "executive_summary_points": [
        "Key point 1",
        "Key point 2",
        "Key point 3"
    ],
    "sections": [
        {{
            "section_id": "section_1",
            "heading": "Section heading in {target_language}",
            "subheadings": ["Sub 1", "Sub 2"],
            "relevant_finding_ids": ["subtask_1", "subtask_2"],
            "key_points": ["Point to cover 1", "Point to cover 2"],
            "target_word_count": 800
        }}
    ],
    "conclusion_points": [
        "Conclusion 1",
        "Conclusion 2"
    ],
    "target_word_count": {target_word_count},
    "target_language": "{target_language}"
}}
```

IMPORTANT GUIDELINES:
- Write everything in {target_language}
- Ensure logical flow between sections
- Allocate word counts to sum to approximately {target_word_count}
- Reference specific finding IDs to ensure coverage
- Do NOT include meta-descriptions about the research process
"""
)


OUTLINE_FORMAT_INSTRUCTIONS = """
The outline must be:
1. Comprehensive - covering all aspects of the original query
2. Logical - with clear flow from introduction to conclusion
3. Balanced - with appropriate depth for each topic
4. Actionable - providing clear guidance for the writer
"""
