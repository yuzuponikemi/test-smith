from src.utils.logging_utils import print_node_header
from src.utils.search_providers import SearchProviderManager
from datetime import datetime


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

    Returns both legacy search_results and new web_sources for provenance tracking.

    Environment Variables:
        SEARCH_PROVIDER_PRIORITY: Comma-separated provider priority (default: "tavily,duckduckgo")
        TAVILY_API_KEY: API key for Tavily (optional)
        BRAVE_API_KEY: API key for Brave Search (optional)
    """
    print_node_header("SEARCHER")

    web_queries = state.get("web_queries", [])

    if not web_queries:
        print("  No web queries allocated - skipping web search")
        return {"search_results": [], "web_sources": []}

    print(f"  Executing {len(web_queries)} web searches")

    # Initialize search provider manager
    try:
        manager = SearchProviderManager()
        print(f"  Available providers: {', '.join(manager.get_available_providers())}")
    except Exception as e:
        print(f"  ⚠️  Failed to initialize search providers: {e}")
        return {"search_results": [], "web_sources": []}

    all_results = []
    web_sources = []  # New: structured provenance tracking
    source_counter = 0

    for query in web_queries:
        print(f"  Searching web for: {query}")
        timestamp = datetime.now().isoformat()

        try:
            # Search with automatic fallback
            search_results = manager.search(query, max_results=5, attempt_all=True)
            all_results.append(search_results)

            # Extract structured source metadata for provenance
            if isinstance(search_results, list):
                for result in search_results:
                    source_counter += 1
                    source_id = f"web_{source_counter}"

                    # Extract fields from search result dict
                    url = result.get("url", "")
                    title = result.get("title", "Unknown Title")
                    content = result.get("content", "")
                    # Note: score is not included in to_dict(), so use default
                    score = result.get("score", 0.5)

                    # Create structured source reference
                    source_ref = {
                        "source_id": source_id,
                        "source_type": "web",
                        "url": url,
                        "title": title,
                        "content_snippet": content[:500] if content else "",
                        "query_used": query,
                        "timestamp": timestamp,
                        "relevance_score": float(score) if score else 0.5,
                        "metadata": {
                            "search_provider": "auto",  # Could be tavily, duckduckgo, etc.
                            "full_content_length": len(content) if content else 0,
                        }
                    }
                    web_sources.append(source_ref)

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
    print(f"  Captured {len(web_sources)} source references for provenance")

    return {
        "search_results": all_results,
        "web_sources": web_sources
    }
