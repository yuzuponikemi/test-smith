from langchain_core.prompts import PromptTemplate

EVALUATOR_PROMPT = PromptTemplate.from_template("""
Based on the analysis of the search results, decide if the information is sufficient to create a comprehensive report that compares and contrasts the economic policies of Franklin D. Roosevelt's New Deal with the policies of Margaret Thatcher in the UK, and explains the long-term effects of each.

Respond with only one of the following two words: 'sufficient' or 'insufficient'.

Analysis: {analyzed_data}
""")