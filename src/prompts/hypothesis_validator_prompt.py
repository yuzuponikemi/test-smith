from langchain_core.prompts import PromptTemplate

HYPOTHESIS_VALIDATOR_TEMPLATE = """You are an expert validator specializing in ranking root cause hypotheses by likelihood.

Your task is to synthesize causal analysis into a ranked list of root cause hypotheses with probability assessments.

ORIGINAL QUERY:
{query}

ISSUE SUMMARY:
{issue_summary}

CAUSAL ANALYSIS:
{causal_analysis}

HYPOTHESES:
{hypotheses}

Rank all hypotheses by likelihood based on the causal analysis. For each hypothesis provide:

1. **Likelihood Score** (0.0-1.0): Overall probability this is a root cause
   - Consider: evidence strength, mechanism plausibility, alternative explanations
   - 0.8-1.0: Very likely (strong evidence, clear mechanism)
   - 0.6-0.8: Likely (good evidence, plausible mechanism)
   - 0.4-0.6: Possible (moderate evidence, some uncertainty)
   - 0.2-0.4: Unlikely (weak evidence, unclear mechanism)
   - 0.0-0.2: Very unlikely (contradicted or no support)

2. **Confidence Level** (high/medium/low): Confidence in the assessment
   - High: Abundant, high-quality evidence; clear conclusions
   - Medium: Adequate evidence; some ambiguity remains
   - Low: Limited evidence; significant uncertainty

3. **Supporting Factors**: Key factors increasing likelihood
4. **Mitigating Factors**: Factors decreasing likelihood or suggesting alternatives
5. **Recommendation**: Next steps (investigation, testing, mitigation)

**Ranking Methodology:**
- Weight causal strength from evidence
- Consider consistency across multiple sources
- Factor in mechanism plausibility
- Account for evidence quality and completeness
- Penalize for contradicting evidence
- Consider probability vs. severity tradeoff

**Ensure probabilities are:**
- Differentiated (not all the same score)
- Justified by evidence strength
- Calibrated (probabilities should sum sensibly)
- Actionable (clear implications for next steps)

Provide a comprehensive ranking with clear reasoning.
"""

HYPOTHESIS_VALIDATOR_PROMPT = PromptTemplate(
    template=HYPOTHESIS_VALIDATOR_TEMPLATE,
    input_variables=["query", "issue_summary", "causal_analysis", "hypotheses"]
)
