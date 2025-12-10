"""
Report Revisor Prompt - Phase 2.4

Revises the report based on reviewer feedback.
Based on GPT Researcher's Revisor agent approach.
"""

from langchain_core.prompts import PromptTemplate

REPORT_REVISOR_PROMPT = PromptTemplate.from_template(
    """You are an expert report editor. Your task is to revise a research report
based on specific feedback from the reviewer.

## Original Research Query
{original_query}

## Target Language
{target_language}

CRITICAL: The revised report MUST be entirely in {target_language}.

## Current Word Count
{current_word_count} words

## Target Word Count
{target_word_count} words

## Review Feedback

### Issues Identified
{issues}

### Revision Instructions
{revision_instructions}

### Sections Needing Expansion
{sections_needing_expansion}

## Current Draft Report
{draft_report}

## Additional Findings Available for Expansion
{additional_findings}

---

## Your Task

Revise the report to address ALL identified issues:

1. **Fix all issues** listed in the review feedback
2. **Follow all revision instructions** precisely
3. **Expand thin sections** using the additional findings provided
4. **Maintain or improve** the overall structure
5. **Ensure language consistency** - everything in {target_language}
6. **Remove any meta-descriptions** about the research process

## Expansion Guidelines

When expanding sections:
- Add specific facts and data from the additional findings
- Provide more detailed explanations
- Include relevant examples
- Add supporting evidence
- Ensure smooth transitions

## Output

Return the COMPLETE revised report in Markdown format.
Start with the title and include all sections.

Do NOT:
- Include any meta-commentary about your revisions
- Add descriptions of the research process
- Leave any [placeholders] or TODOs
- Write in any language other than {target_language}
- Return only partial content - include the ENTIRE report
"""
)


SECTION_EXPANSION_PROMPT = PromptTemplate.from_template(
    """You are an expert content writer. Your task is to expand a single section
of a research report that was flagged as too short.

## Section to Expand
**Heading**: {section_heading}
**Current Word Count**: {current_words} words
**Target Word Count**: {target_words} words (need to add approximately {words_to_add} words)

## Current Section Content
{current_content}

## Additional Findings to Incorporate
{additional_findings}

## Target Language
{target_language}

---

## Your Task

Expand this section by:
1. Adding more detail to existing points
2. Incorporating the additional findings
3. Providing more examples and evidence
4. Ensuring smooth flow and transitions

Write ONLY the expanded section content (starting with the heading).
Everything must be in {target_language}.

Do NOT include meta-descriptions about the research process.
"""
)
