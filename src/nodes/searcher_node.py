from langchain_community.tools import DuckDuckGoSearchRun

def searcher(state):
    print("---SEARCHER---")
    plan = state["plan"]
    all_results = []
    for query in plan:
        print(f"Searching for: {query}")
        search = DuckDuckGoSearchRun(region="en-us")
        search_results = search.run(query)
        all_results.append(search_results)
    return {"search_results": all_results}
