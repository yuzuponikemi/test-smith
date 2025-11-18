from langchain.prompts import PromptTemplate

BRAINSTORMER_TEMPLATE = """You are an expert brainstormer specializing in root cause analysis and causal reasoning.

Your task is to generate diverse root cause hypotheses for the issue based on the following analysis:

ORIGINAL QUERY:
{query}

ISSUE ANALYSIS:
Summary: {issue_summary}
Symptoms: {symptoms}
Context: {context}
Scope: {scope}

Generate 5-8 distinct root cause hypotheses that could explain the observed symptoms. For each hypothesis:
1. **Description**: Clear explanation of what the root cause is
2. **Mechanism**: How this cause produces the observed symptoms (causal chain)
3. **Category**: Classify as technical/process/human/environmental/design/external
4. **Initial Plausibility**: Your initial assessment (0.0-1.0) before evidence gathering

Use diverse thinking approaches:
- **First Principles**: What fundamental factors could cause this?
- **5 Whys**: Drill down to underlying causes
- **Fishbone/Ishikawa**: Consider categories (people, process, tools, environment, design)
- **Analogical Thinking**: Similar issues in related domains
- **Counterfactual Thinking**: What would prevent this issue?

Ensure hypotheses span:
- Immediate vs. underlying causes
- Internal vs. external factors
- Technical vs. non-technical factors
- Common vs. rare causes

Provide hypotheses that are:
- **Testable**: Can be validated with evidence
- **Specific**: Concrete mechanisms, not vague
- **Diverse**: Cover different categories and levels
"""

BRAINSTORMER_PROMPT = PromptTemplate(
    template=BRAINSTORMER_TEMPLATE,
    input_variables=["query", "issue_summary", "symptoms", "context", "scope"]
)
