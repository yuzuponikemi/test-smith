from src.utils.logging_utils import print_node_header
from src.utils.search_providers import SearchProviderManager


def searcher(state):
    """
    Searcher Node - Executes web searches with automatic provider fallback

    Supports multiple search providers with automatic fallback:
    - Tavily (high-quality, requires API key)
    - DuckDuckGo (free, no API key required)
    - Brave Search (optional, requires API key)

    Uses strategically allocated web_queries from the planner.
    These queries are specifically chosen for information that needs:
    - Recent events or current data
    - General knowledge not in KB
    - External sources and references

    Environment Variables:
        SEARCH_PROVIDER_PRIORITY: Comma-separated provider priority (default: "tavily,duckduckgo")
        TAVILY_API_KEY: API key for Tavily (optional)
        BRAVE_API_KEY: API key for Brave Search (optional)
    """
    print_node_header("SEARCHER")

    web_queries = state.get("web_queries", [])

    if not web_queries:
        print("  No web queries allocated - skipping web search")
        return {"search_results": []}

    print(f"  Executing {len(web_queries)} web searches")

    # Initialize search provider manager
    try:
        manager = SearchProviderManager()
        print(f"  Available providers: {', '.join(manager.get_available_providers())}")
    except Exception as e:
        print(f"  ⚠️  Failed to initialize search providers: {e}")
        return {"search_results": []}

    all_results = []
    for query in web_queries:
        print(f"  Searching web for: {query}")
        try:
            # Search with automatic fallback
            search_results = manager.search(query, max_results=5, attempt_all=True)
            all_results.append(search_results)

        except Exception as e:
            # All providers failed
            error_msg = str(e)
            print(f"    ⚠️  All search providers failed: {error_msg}")

            error_info = [
                {
                    "content": f"⚠️ Web search failed for query: {query}\n"
                    f"Error: {error_msg}\n"
                    f"Tip: Check your search provider configuration",
                    "url": "",
                }
            ]
            all_results.append(error_info)

    print(f"  Completed {len(all_results)} web searches")
    return {"search_results": all_results}
