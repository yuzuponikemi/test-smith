from src.models import get_analyzer_model
from src.prompts.analyzer_prompt import ANALYZER_PROMPT

def analyzer_node(state):
    print("---ANALYZER---")
    model = get_analyzer_model()

    # Get strategic context
    original_query = state.get("query", "")
    allocation_strategy = state.get("allocation_strategy", "No strategy provided")
    web_queries = state.get("web_queries", [])
    rag_queries = state.get("rag_queries", [])

    # Get results separately to maintain source context
    web_results = state.get("search_results", [])
    rag_results = state.get("rag_results", [])

    print(f"  Analyzing {len(web_results)} web results and {len(rag_results)} RAG results")
    print(f"  Strategy: {allocation_strategy[:100]}...")

    prompt = ANALYZER_PROMPT.format(
        original_query=original_query,
        allocation_strategy=allocation_strategy,
        web_queries=web_queries,
        rag_queries=rag_queries,
        web_results=web_results,
        rag_results=rag_results
    )

    message = model.invoke(prompt)
    return {"analyzed_data": [message.content]}
