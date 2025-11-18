from langchain.prompts import PromptTemplate

ROOT_CAUSE_SYNTHESIZER_TEMPLATE = """You are an expert report writer specializing in root cause analysis and causal inference.

Your task is to synthesize all analysis into a comprehensive root cause analysis report.

ORIGINAL QUERY:
{query}

ISSUE ANALYSIS:
{issue_analysis}

RANKED HYPOTHESES:
{ranked_hypotheses}

CAUSAL GRAPH DATA:
{causal_graph_data}

Generate a comprehensive Root Cause Analysis Report with the following structure:

# Root Cause Analysis Report

## Executive Summary
- Brief overview of the issue
- Top 3 most likely root causes
- Confidence in findings
- Priority recommendations

## Issue Overview
- Detailed description of the problem
- Observable symptoms and effects
- Context and scope
- Impact assessment

## Root Cause Hypotheses (Ranked by Likelihood)

For each hypothesis (in order of likelihood):
### [Rank]. [Hypothesis Name] - Likelihood: [X.XX] - Confidence: [Level]

**Description:**
[Clear explanation of the root cause]

**Causal Mechanism:**
[How this cause produces the observed symptoms]

**Supporting Evidence:**
- [Bullet points of supporting evidence]

**Mitigating Factors:**
- [Factors reducing likelihood, if any]

**Recommendation:**
[Specific next steps for validation or mitigation]

## Causal Analysis Summary
- Key causal relationships identified
- Interconnections between causes
- Confidence in causal inferences

## Recommendations

### Immediate Actions
- [High-priority items based on top hypotheses]

### Further Investigation
- [Areas needing more evidence]
- [Proposed validation approaches]

### Prevention Strategies
- [Long-term measures to prevent recurrence]

## Methodology
- Analysis approach used
- Evidence sources consulted
- Limitations and assumptions

## Confidence Assessment
- Overall confidence in findings: [High/Medium/Low]
- Data quality and completeness
- Key uncertainties

---

**Style:**
- Professional, technical tone
- Evidence-based conclusions
- Actionable recommendations
- Clear probability/confidence communication
- Structured and scannable format

Provide a thorough, professional report suitable for technical decision-makers.
"""

ROOT_CAUSE_SYNTHESIZER_PROMPT = PromptTemplate(
    template=ROOT_CAUSE_SYNTHESIZER_TEMPLATE,
    input_variables=["query", "issue_analysis", "ranked_hypotheses", "causal_graph_data"]
)
