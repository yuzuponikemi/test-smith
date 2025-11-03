def search_query_generator(state):
    print("---SEARCH QUERY GENERATOR---")
    plan = state["plan"]
    query = plan.pop(0)
    return {"plan": plan, "current_search_query": query}
