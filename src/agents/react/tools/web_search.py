"""web_search tool: thin wrapper over the existing SearchProviderManager."""

from __future__ import annotations

from typing import Any

from src.utils.search_providers.provider_manager import SearchProviderManager

from .base import Tool, ToolError, ToolResult


class WebSearchTool(Tool):
    def __init__(self, manager: SearchProviderManager | None = None, max_results: int = 5):
        self._manager = manager or SearchProviderManager()
        self._max_results = max_results

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web. Returns a numbered list of {title, url, snippet}. "
            "Snippets are short — use web_fetch to read a specific page in full."
        )

    @property
    def input_schema(self) -> str:
        return '{"query": "<search query>", "max_results": 5}'

    def run(self, args: dict[str, Any]) -> ToolResult:
        query = (args.get("query") or "").strip()
        if not query:
            raise ToolError("web_search requires a non-empty 'query' argument")
        max_results = int(args.get("max_results") or self._max_results)

        try:
            results = self._manager.search(query, max_results=max_results)
        except Exception as e:
            raise ToolError(f"search failed: {e}") from e

        if not results:
            return ToolResult(observation=f"No results for query: {query}")

        lines = [f"Search results for: {query}"]
        for i, r in enumerate(results, 1):
            title = r.get("title") or "(no title)"
            url = r.get("url") or ""
            content = (r.get("content") or "").strip().replace("\n", " ")
            if len(content) > 400:
                content = content[:400] + "…"
            lines.append(f"[{i}] {title}\n    URL: {url}\n    Snippet: {content}")
        return ToolResult(observation="\n".join(lines))
