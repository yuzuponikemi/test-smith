from langchain_community.tools import TavilySearchResults
import os

from src.utils.logging_utils import print_node_header
def searcher(state):
    """
    Searcher Node - Executes web searches via Tavily API

    Uses strategically allocated web_queries from the planner.
    These queries are specifically chosen for information that needs:
    - Recent events or current data
    - General knowledge not in KB
    - External sources and references
    """
    print_node_header("SEARCHER")

    # Get the Tavily API key from the environment
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("Tavily API key not found in environment variables. Please set the TAVILY_API_KEY environment variable.")

    web_queries = state.get("web_queries", [])

    if not web_queries:
        print("  No web queries allocated - skipping web search")
        return {"search_results": []}

    print(f"  Executing {len(web_queries)} web searches")

    all_results = []
    for query in web_queries:
        print(f"  Searching web for: {query}")
        search = TavilySearchResults(max_results=5)
        search_results = search.invoke({"query": query})
        all_results.append(search_results)

    print(f"  Completed {len(all_results)} web searches")
    return {"search_results": all_results}
