from langchain_community.tools import TavilySearchResults
import os
from datetime import datetime

from src.utils.logging_utils import print_node_header

def searcher(state):
    """
    Searcher Node - Executes web searches via Tavily API

    Uses strategically allocated web_queries from the planner.
    These queries are specifically chosen for information that needs:
    - Recent events or current data
    - General knowledge not in KB
    - External sources and references

    Returns both legacy search_results and new web_sources for provenance tracking.
    """
    print_node_header("SEARCHER")

    # Get the Tavily API key from the environment
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("Tavily API key not found in environment variables. Please set the TAVILY_API_KEY environment variable.")

    web_queries = state.get("web_queries", [])

    if not web_queries:
        print("  No web queries allocated - skipping web search")
        return {"search_results": [], "web_sources": []}

    print(f"  Executing {len(web_queries)} web searches")

    all_results = []
    web_sources = []  # New: structured provenance tracking
    source_counter = 0

    for query in web_queries:
        print(f"  Searching web for: {query}")
        search = TavilySearchResults(max_results=5)
        search_results = search.invoke({"query": query})
        all_results.append(search_results)

        # Extract structured source metadata for provenance
        timestamp = datetime.now().isoformat()

        if isinstance(search_results, list):
            for result in search_results:
                source_counter += 1
                source_id = f"web_{source_counter}"

                # Extract fields from Tavily result
                url = result.get("url", "")
                title = result.get("title", "Unknown Title")
                content = result.get("content", "")
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
                        "search_engine": "tavily",
                        "full_content_length": len(content) if content else 0,
                    }
                }
                web_sources.append(source_ref)

    print(f"  Completed {len(all_results)} web searches")
    print(f"  Captured {len(web_sources)} source references for provenance")

    return {
        "search_results": all_results,
        "web_sources": web_sources
    }
