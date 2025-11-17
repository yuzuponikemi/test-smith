from langchain.prompts import PromptTemplate

ISSUE_ANALYZER_TEMPLATE = """You are an expert issue analyst specializing in root cause analysis.

Your task is to analyze the following problem statement and extract key information:

PROBLEM STATEMENT:
{query}

Please analyze this issue and extract:
1. **Symptoms**: Observable effects, behaviors, or manifestations of the problem
2. **Context**: Relevant background, constraints, environment, and conditions
3. **Scope**: What systems/components are affected, timeframe, when it occurs

Use systematic thinking:
- What can be observed directly?
- What is the environment/context?
- What are the boundaries of this issue?
- What is the impact?

Provide a structured analysis that will serve as the foundation for generating root cause hypotheses.
"""

ISSUE_ANALYZER_PROMPT = PromptTemplate(
    template=ISSUE_ANALYZER_TEMPLATE,
    input_variables=["query"]
)
