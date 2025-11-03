from langchain_core.prompts import PromptTemplate

PLANNER_PROMPT = PromptTemplate.from_template("""
Your task is to generate a list of search queries to answer the user's query.
Query: {query}

Previous plan and feedback (if any):
{feedback}

Based on the feedback, refine the plan to gather the missing information. If there is no feedback, create a new plan.

Respond with a list of search queries, one per line.
{format_instructions}
""")
