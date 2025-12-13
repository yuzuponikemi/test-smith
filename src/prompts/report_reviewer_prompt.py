"""
Report Reviewer Prompt - Phase 2.3

Reviews the generated report against quality criteria.
Based on Anthropic's multi-layer quality control approach.
"""

from langchain_core.prompts import PromptTemplate

REPORT_REVIEWER_PROMPT = PromptTemplate.from_template(
    """You are an expert report reviewer. Your task is to evaluate the quality
of a research report and identify any issues that need to be fixed.

## Original Research Query
{original_query}

## Expected Target Language
{target_language}

## Target Word Count
{target_word_count} words

## Actual Word Count
{actual_word_count} words

## Report Outline
{outline_summary}

## Draft Report to Review
{draft_report}

---

## Review Criteria

Evaluate the report on these criteria:

### 1. Word Count (Critical)
- Does the report meet at least 60% of the target word count?
- Are sections appropriately balanced in length?

### 2. Language Consistency (Critical)
- Is the entire report written in {target_language}?
- Are there any sections in the wrong language?

### 3. Content Coverage (Important)
- Does the report address all aspects of the original query?
- Are all outline sections present and substantive?
- Are there significant gaps in coverage?

### 4. Structure Quality (Important)
- Does the report have clear headings and organization?
- Are transitions between sections smooth?
- Is there an introduction and conclusion?

### 5. Meta-Description Check (Critical)
- Does the report contain unwanted descriptions of the research process?
- (e.g., "The RAG system retrieved...", "Web search was used...")
- The report should contain ONLY the research findings, not methodology.

### 6. Content Quality
- Are claims supported by evidence?
- Is the writing clear and professional?
- Is there unnecessary repetition?

---

## Output Format

Respond with a JSON object:

```json
{{
    "meets_criteria": true/false,
    "word_count_actual": {actual_word_count},
    "word_count_target": {target_word_count},
    "word_count_met": true/false,
    "language_correct": true/false,
    "coverage_complete": true/false,
    "structure_quality": "excellent/good/adequate/poor",
    "contains_meta_description": true/false,
    "issues": [
        "Issue 1 description",
        "Issue 2 description"
    ],
    "revision_instructions": [
        "Specific instruction for fixing issue 1",
        "Specific instruction for fixing issue 2"
    ],
    "sections_needing_expansion": [
        "section_1",
        "section_3"
    ]
}}
```

## Important Notes

- `meets_criteria` should be true only if ALL critical criteria pass
- Be specific in `revision_instructions` - they will be used to improve the report
- List sections by section_id that need more content in `sections_needing_expansion`
- Focus on actionable feedback that can improve the report
"""
)


REVIEW_SUMMARY_PROMPT = """
Based on your review, summarize the overall quality and main issues in 2-3 sentences.
"""
