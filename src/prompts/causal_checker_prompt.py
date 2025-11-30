from langchain_core.prompts import PromptTemplate

CAUSAL_CHECKER_TEMPLATE = """You are an expert causal analyst specializing in validating cause-effect relationships using evidence.

Your task is to evaluate each root cause hypothesis against gathered evidence to establish causal relationships.

ORIGINAL QUERY:
{query}

ISSUE SUMMARY:
{issue_summary}

SYMPTOMS:
{symptoms}

HYPOTHESES:
{hypotheses}

GATHERED EVIDENCE:
Web Search Results:
{web_results}

Knowledge Base Results:
{rag_results}

For each hypothesis, evaluate the causal relationship using rigorous criteria:

**Causal Validation Framework:**

1. **Temporal Precedence**: Does the cause precede the effect?
2. **Covariation**: Does the effect vary with the cause?
3. **Mechanism Plausibility**: Is there a credible causal mechanism?
4. **Alternative Explanations**: Have other explanations been ruled out?
5. **Evidence Strength**: How strong is the supporting evidence?

**Classification:**
- **direct_cause**: Strong evidence of direct causation (multiple criteria met)
- **contributing_factor**: Partial causation (some criteria met)
- **correlated**: Association present but causation unclear
- **unlikely**: Weak or contradictory evidence
- **refuted**: Evidence clearly disproves this cause

For each hypothesis, identify:
- **Supporting Evidence**: Specific facts supporting causation
- **Contradicting Evidence**: Facts refuting or weakening causation
- **Causal Strength**: Overall strength (0.0-1.0) based on evidence quality
- **Reasoning**: Detailed analysis of the causal relationship

Apply critical thinking:
- Distinguish correlation from causation
- Consider confounding factors
- Evaluate evidence quality and reliability
- Look for counter-evidence
- Assess mechanism plausibility

Provide a thorough causal analysis for all hypotheses.
"""

CAUSAL_CHECKER_PROMPT = PromptTemplate(
    template=CAUSAL_CHECKER_TEMPLATE,
    input_variables=[
        "query",
        "issue_summary",
        "symptoms",
        "hypotheses",
        "web_results",
        "rag_results",
    ],
)
