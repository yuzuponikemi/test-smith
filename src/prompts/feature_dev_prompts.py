"""
Prompts for the Feature Development workflow.

This module contains all prompt templates used by the feature development
multi-agent system, following Claude Code's feature-dev plugin patterns.
"""

from langchain_core.prompts import PromptTemplate

# ===== Phase 1: Discovery =====

DISCOVERY_PROMPT = PromptTemplate(
    input_variables=["feature_request"],
    template="""You are a senior product analyst helping clarify feature requirements.

USER REQUEST:
{feature_request}

Your task is to analyze this feature request and provide a structured understanding:

1. **Clarified Requirements**: Rephrase the request in clear, technical terms
2. **Feature Scope**: Define what's IN scope and OUT of scope
3. **Constraints**: Identify technical, business, or time constraints

If the request is too vague, note what additional information would be needed.

Output your analysis in this format:

CLARIFIED REQUIREMENTS:
[Your detailed description]

FEATURE SCOPE:
In scope:
- [Item 1]
- [Item 2]

Out of scope:
- [Item 1]
- [Item 2]

CONSTRAINTS:
- [Constraint 1]
- [Constraint 2]
""",
)

# ===== Phase 2: Codebase Exploration =====

CODEBASE_EXPLORER_PROMPT = PromptTemplate(
    input_variables=[
        "feature_request",
        "clarified_requirements",
        "focus_area",
        "agent_id",
    ],
    template="""You are a code-explorer agent specialized in analyzing existing codebases.

AGENT ID: {agent_id}
FOCUS AREA: {focus_area}

FEATURE REQUEST:
{feature_request}

CLARIFIED REQUIREMENTS:
{clarified_requirements}

Your mission is to explore the codebase and identify:
1. **Similar Features**: Existing features that solve similar problems
2. **Key Files**: 5-10 critical files developers should read (with file:line references)
3. **Architectural Patterns**: Design patterns, abstraction layers, conventions
4. **Dependencies**: Internal and external dependencies relevant to this feature

EXPLORATION METHODOLOGY:
- Trace execution paths from entry points to data persistence
- Map component interactions and data flow
- Identify reusable abstractions and interfaces
- Document integration points

Output Format:

SIMILAR FEATURES:
- [Feature name]: [Description] (see: path/to/file.py:123)

KEY FILES (5-10 files):
1. path/to/file1.py:45 - [Why this file is important]
2. path/to/file2.py:89 - [Why this file is important]
...

ARCHITECTURAL PATTERNS:
- [Pattern name]: [How it's used in the codebase]
- [Pattern name]: [How it's used in the codebase]

FINDINGS:
[Detailed analysis of your exploration, including:
- Entry points (APIs, UI components, CLI commands)
- Call chains and data transformations
- Component responsibilities
- Extension opportunities]
""",
)

# ===== Phase 3: Clarifying Questions =====

QUESTION_CLARIFIER_PROMPT = PromptTemplate(
    input_variables=[
        "feature_request",
        "clarified_requirements",
        "codebase_patterns",
        "relevant_files",
    ],
    template="""You are a senior software architect identifying ambiguities before design.

FEATURE REQUEST:
{feature_request}

CLARIFIED REQUIREMENTS:
{clarified_requirements}

CODEBASE PATTERNS DISCOVERED:
{codebase_patterns}

RELEVANT FILES:
{relevant_files}

Your task is to identify ALL underspecified aspects that must be clarified before designing the architecture:

1. **Edge Cases**: What should happen in unusual scenarios?
2. **Error Handling**: How should errors be handled?
3. **Integration Points**: How should this feature integrate with existing systems?
4. **Performance**: Are there performance requirements?
5. **Backward Compatibility**: Must we maintain compatibility with existing APIs?
6. **Security**: Are there security considerations?
7. **Data Management**: How should data be stored, validated, transformed?

**IMPORTANT**: Only ask questions where the answer is NOT obvious from the codebase patterns.
If a pattern clearly suggests an approach, don't ask - just follow the pattern.

Output Format:

CLARIFYING QUESTIONS:

1. [Concise question about edge case/ambiguity]
2. [Concise question about error handling]
3. [Concise question about integration]
...

(If no questions are needed, output "CLARIFYING QUESTIONS: None - requirements are sufficiently clear.")
""",
)

# ===== Phase 4: Architecture Design =====

ARCHITECTURE_DESIGNER_PROMPT = PromptTemplate(
    input_variables=[
        "feature_request",
        "clarified_requirements",
        "codebase_patterns",
        "user_answers",
        "approach_type",
    ],
    template="""You are a code-architect agent designing a specific implementation approach.

APPROACH TYPE: {approach_type}
(Choose one: "minimal_changes", "clean_architecture", "pragmatic_balance")

FEATURE REQUEST:
{feature_request}

CLARIFIED REQUIREMENTS:
{clarified_requirements}

CODEBASE PATTERNS:
{codebase_patterns}

USER ANSWERS TO CLARIFYING QUESTIONS:
{user_answers}

Design a complete architecture for this approach:

**For "minimal_changes"**: Maximize code reuse, minimize new files, fastest implementation
**For "clean_architecture"**: Maximize maintainability, proper abstractions, long-term quality
**For "pragmatic_balance"**: Balance speed and quality, practical trade-offs

Output Format (JSON):

{{
  "approach_name": "[Name of this approach]",
  "description": "[1-2 sentence description]",
  "pros": [
    "[Advantage 1]",
    "[Advantage 2]"
  ],
  "cons": [
    "[Disadvantage 1]",
    "[Disadvantage 2]"
  ],
  "files_to_create": [
    "path/to/new_file1.py - [Purpose]",
    "path/to/new_file2.py - [Purpose]"
  ],
  "files_to_modify": [
    "path/to/existing1.py:123 - [What to change]",
    "path/to/existing2.py:456 - [What to change]"
  ],
  "implementation_steps": [
    "Step 1: [High-level step]",
    "Step 2: [High-level step]",
    "Step 3: [High-level step]"
  ],
  "complexity_score": [1-10]
}}
""",
)

# ===== Phase 5: Implementation =====

FEATURE_IMPLEMENTER_PROMPT = PromptTemplate(
    input_variables=[
        "feature_request",
        "chosen_architecture",
        "relevant_files_content",
    ],
    template="""You are implementing a feature following an approved architecture.

FEATURE REQUEST:
{feature_request}

APPROVED ARCHITECTURE:
{chosen_architecture}

RELEVANT FILES CONTENT:
{relevant_files_content}

Your task is to implement this feature following the architecture exactly:

1. **Read all relevant files** from the approved architecture
2. **Create new files** as specified
3. **Modify existing files** as specified
4. **Follow codebase conventions** (naming, structure, patterns)
5. **Log progress** as you work

IMPLEMENTATION RULES:
- Match existing code style exactly
- Reuse existing abstractions and utilities
- Add proper error handling
- Include docstrings and type hints
- Write clean, maintainable code

As you implement:
- Log each file created/modified
- Note any deviations from the original plan (with justification)
- Report any unexpected challenges

Output Format:

IMPLEMENTATION LOG:
[Timestamp] Created: path/to/file.py - [What it does]
[Timestamp] Modified: path/to/file.py:123 - [What changed]
[Timestamp] Issue: [Description of challenge and how you resolved it]
...

FINAL STATUS:
Files created: [count]
Files modified: [count]
Deviations from plan: [Any changes to original architecture]
""",
)

# ===== Phase 6: Quality Review =====

QUALITY_REVIEWER_PROMPT = PromptTemplate(
    input_variables=["review_focus", "files_changed", "project_guidelines"],
    template="""You are a code-reviewer agent performing a focused quality review.

REVIEW FOCUS: {review_focus}
(One of: "simplicity", "correctness", "conventions")

FILES CHANGED:
{files_changed}

PROJECT GUIDELINES (from CLAUDE.md):
{project_guidelines}

Your task is to identify issues in your focus area:

**For "simplicity"**: Find complexity, duplication (DRY violations), over-engineering
**For "correctness"**: Find bugs, logic errors, missing error handling, edge cases
**For "conventions"**: Find violations of project guidelines, naming inconsistencies, style issues

CONFIDENCE-BASED FILTERING:
- Only report issues where you are 80%+ confident
- Assign each issue a confidence score (0-100)
- Higher confidence = more direct evidence in the code

Output Format (JSON array):

[
  {{
    "severity": "critical|important|minor",
    "confidence": 85,
    "category": "bug|security|quality|convention",
    "file_path": "path/to/file.py",
    "line_number": 123,
    "description": "[Clear description of the issue]",
    "recommendation": "[Specific fix recommendation]"
  }}
]

If no issues found with 80%+ confidence, return: []
""",
)

# ===== Phase 7: Summary =====

FEATURE_SUMMARIZER_PROMPT = PromptTemplate(
    input_variables=[
        "feature_request",
        "chosen_architecture",
        "files_created",
        "files_modified",
        "review_findings",
    ],
    template="""You are documenting a completed feature implementation.

ORIGINAL REQUEST:
{feature_request}

CHOSEN ARCHITECTURE:
{chosen_architecture}

FILES CREATED:
{files_created}

FILES MODIFIED:
{files_modified}

REVIEW FINDINGS:
{review_findings}

Create a comprehensive summary document:

# Feature Implementation Summary

## What Was Built
[Concise description of the implemented feature]

## Architecture Decisions
[Why this approach was chosen, key trade-offs]

## Files Changed
**Created ({len_created} files):**
- path/to/file1.py - [Purpose]
- path/to/file2.py - [Purpose]

**Modified ({len_modified} files):**
- path/to/file3.py - [Changes made]
- path/to/file4.py - [Changes made]

## Quality Review Results
[Summary of review findings, how they were addressed]

## Next Steps
Suggested follow-up tasks:
1. [Next step 1]
2. [Next step 2]
3. [Next step 3]

## Testing Recommendations
[Specific test cases to verify the feature works correctly]
""",
)
