"""
Section Writer Prompt - Phase 2.2

Writes individual sections of the report based on the outline and relevant findings.
Each section is written independently to ensure focused, high-quality content.
"""

from langchain_core.prompts import PromptTemplate

SECTION_WRITER_PROMPT = PromptTemplate.from_template(
    """You are an expert research writer. Your task is to write a single section
of a comprehensive research report.

## Report Context
**Report Title**: {report_title}
**Original Query**: {original_query}
**Target Language**: {target_language}

CRITICAL: Write the ENTIRE section in {target_language}. This is non-negotiable.

## Section to Write
**Section Heading**: {section_heading}
**Subheadings**: {subheadings}
**Target Word Count**: {target_word_count} words
**Key Points to Cover**: {key_points}

## Relevant Research Findings
{relevant_findings}

---

## Writing Instructions

Write a comprehensive section that:

1. **Opens with context**: Start with a brief introduction connecting to the report's theme
2. **Covers all key points**: Address each key point using the provided findings
3. **Uses subheadings**: Organize content under the provided subheadings
4. **Cites findings**: Reference specific facts and data from the research
5. **Maintains flow**: Ensure smooth transitions between paragraphs
6. **Hits word target**: Aim for approximately {target_word_count} words

## Format Requirements

- Use Markdown formatting
- Start with the section heading as ## {section_heading}
- Use ### for subheadings
- Use bullet points for lists where appropriate
- Include specific data, examples, and evidence from findings
- End with a brief transition to the next topic (if applicable)

## DO NOT

- Include meta-descriptions about the research process
- Say "According to the research" or "The findings show" - just state the facts
- Include information not supported by the findings
- Write in a language other than {target_language}
- Write significantly less than {target_word_count} words

## Output

Write ONLY the section content in Markdown format. Start with:

## {section_heading}
"""
)


INTRODUCTION_WRITER_PROMPT = PromptTemplate.from_template(
    """You are an expert research writer. Write the introduction/executive summary
for a comprehensive research report.

## Report Title
{report_title}

## Original Research Query
{original_query}

## Target Language
{target_language}

CRITICAL: Write the ENTIRE introduction in {target_language}.

## Executive Summary Points to Include
{executive_summary_points}

## Report Structure Overview
{sections_overview}

## Key Themes from Research
{themes}

## Target Word Count
{target_word_count} words

---

## Writing Instructions

Write an engaging introduction that:

1. **Hook**: Opens with a compelling statement about the topic
2. **Context**: Provides necessary background
3. **Scope**: Clearly states what the report covers
4. **Key Findings Preview**: Highlights the most important discoveries
5. **Structure Guide**: Briefly mentions what each section covers

## Format

Write in Markdown starting with:

# {report_title}

## Executive Summary

[Your introduction here]

Do NOT include meta-descriptions about research methodology.
Write in {target_language} only.
"""
)


CONCLUSION_WRITER_PROMPT = PromptTemplate.from_template(
    """You are an expert research writer. Write the conclusion for a comprehensive
research report.

## Report Title
{report_title}

## Original Research Query
{original_query}

## Target Language
{target_language}

CRITICAL: Write the ENTIRE conclusion in {target_language}.

## Conclusion Points to Include
{conclusion_points}

## Summary of Key Findings from All Sections
{findings_summary}

## Target Word Count
{target_word_count} words

---

## Writing Instructions

Write a powerful conclusion that:

1. **Synthesizes**: Brings together key findings from all sections
2. **Answers the Query**: Directly addresses the original research question
3. **Key Takeaways**: Lists the most important learnings
4. **Implications**: Discusses what the findings mean
5. **Recommendations**: Provides actionable recommendations (if applicable)
6. **Future Outlook**: Optional - mentions future considerations

## Format

Write in Markdown starting with:

## Conclusion

[Your conclusion here]

### Key Takeaways

[Bullet points]

### Recommendations

[If applicable]

Do NOT include meta-descriptions about research methodology.
Write in {target_language} only.
"""
)
