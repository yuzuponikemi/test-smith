from langchain_community.tools import TavilySearchResults
import os

def searcher(state):
    print("---SEARCHER---")
    
    # Get the Tavily API key from the environment
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("Tavily API key not found in environment variables. Please set the TAVILY_API_KEY environment variable.")

    plan = state["plan"]
    all_results = []
    for query in plan:
        print(f"Searching for: {query}")
        search = TavilySearchResults(max_results=5)
        search_results = search.invoke({"query": query})
        all_results.append(search_results)
    return {"search_results": all_results}
