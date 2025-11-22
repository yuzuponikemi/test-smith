from langchain_core.prompts import PromptTemplate

EVIDENCE_PLANNER_TEMPLATE = """You are a strategic research planner specializing in evidence gathering for causal analysis.

Your task is to plan targeted queries to gather evidence for evaluating root cause hypotheses.

ORIGINAL QUERY:
{query}

ISSUE SUMMARY:
{issue_summary}

HYPOTHESES TO INVESTIGATE:
{hypotheses}

KNOWLEDGE BASE STATUS:
{kb_info}

Plan strategic queries to gather evidence for validating/refuting each hypothesis:

1. **RAG Queries** (for knowledge base retrieval):
   - Domain-specific documentation
   - Internal system specifications
   - Historical incident reports
   - Established patterns and known issues

2. **Web Queries** (for external search):
   - Current best practices
   - Common failure modes
   - External documentation
   - Community knowledge and experiences
   - Recent developments

For each hypothesis, consider what evidence would:
- **Support** the causal relationship
- **Refute** the causal relationship
- **Clarify** the mechanism
- **Establish** precedence or correlation

Strategy: Allocate queries efficiently between KB and web based on:
- Type of information needed (internal vs external)
- Specificity to your domain
- Recency requirements
- Technical depth needed

Generate 4-8 targeted queries total (split between RAG and web based on KB contents).
"""

EVIDENCE_PLANNER_PROMPT = PromptTemplate(
    template=EVIDENCE_PLANNER_TEMPLATE,
    input_variables=["query", "issue_summary", "hypotheses", "kb_info"]
)
