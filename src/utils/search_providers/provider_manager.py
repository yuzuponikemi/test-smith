"""
Search Provider Manager

Manages multiple search providers with automatic fallback.
Handles provider selection, health checking, and error recovery.
"""

import os
from typing import Any

from .base_provider import BaseSearchProvider
from .duckduckgo_provider import DuckDuckGoProvider
from .mcp_provider import MCPSearchProvider
from .tavily_provider import TavilyProvider


class SearchProviderManager:
    """
    Manages multiple search providers with automatic fallback

    Environment Variables:
        SEARCH_PROVIDER_PRIORITY: Comma-separated list of provider names in priority order
                                  Example: "tavily,duckduckgo"
                                  Default: "tavily,duckduckgo"
        TAVILY_API_KEY: API key for Tavily (optional)
        BRAVE_API_KEY: API key for Brave Search (optional)
    """

    def __init__(self, priority: list[str] | None = None):
        """
        Initialize provider manager

        Args:
            priority: List of provider names in priority order.
                     If None, reads from SEARCH_PROVIDER_PRIORITY env var.
        """
        self.providers: dict[str, BaseSearchProvider] = {}
        self._initialize_providers()

        # Set priority order
        if priority is None:
            priority_str = os.environ.get("SEARCH_PROVIDER_PRIORITY", "tavily,duckduckgo")
            self.priority = [p.strip() for p in priority_str.split(",")]
        else:
            self.priority = priority

        print(f"[SearchProviderManager] Initialized with priority: {self.priority}")

    def _initialize_providers(self):
        """Initialize all available providers"""
        # Tavily
        tavily_key = os.environ.get("TAVILY_API_KEY")
        self.providers["tavily"] = TavilyProvider(api_key=tavily_key)

        # DuckDuckGo (no API key needed)
        self.providers["duckduckgo"] = DuckDuckGoProvider()

        # MCP (Model Context Protocol) - local server
        mcp_command = os.environ.get("MCP_SERVER_COMMAND")
        mcp_args = os.environ.get("MCP_SERVER_ARGS")
        mcp_env = os.environ.get("MCP_SERVER_ENV")
        self.providers["mcp"] = MCPSearchProvider(
            server_command=mcp_command,
            server_args=mcp_args,
            server_env=mcp_env,
        )

        # Note: Brave Search can be added here when implemented
        # brave_key = os.environ.get("BRAVE_API_KEY")
        # self.providers["brave"] = BraveProvider(api_key=brave_key)

    def get_available_providers(self) -> list[str]:
        """
        Get list of properly configured providers

        Returns:
            List of provider names that are configured
        """
        available = []
        for name in self.priority:
            if name in self.providers:
                provider = self.providers[name]
                if provider.is_configured():
                    available.append(name)
                else:
                    print(f"  [{name}] Not configured (missing API key)")

        return available

    def search(
        self, query: str, max_results: int = 5, attempt_all: bool = True
    ) -> list[dict[str, Any]]:
        """
        Execute search with automatic fallback

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            attempt_all: If True, tries all providers until one succeeds.
                        If False, only tries the first available provider.

        Returns:
            List of search results in dictionary format

        Raises:
            Exception: If all providers fail
        """
        available_providers = self.get_available_providers()

        if not available_providers:
            raise Exception(
                "No search providers available. Please configure at least one provider."
            )

        last_error = None
        providers_tried = []

        for provider_name in available_providers:
            provider = self.providers[provider_name]
            providers_tried.append(provider_name)

            try:
                print(f"  [{provider_name}] Attempting search for: {query}")
                results = provider.search(query, max_results)

                # Convert to dict format for compatibility
                dict_results = [r.to_dict() for r in results]

                print(f"  [{provider_name}] ✅ Success - {len(results)} results")
                return dict_results

            except Exception as e:
                last_error = e
                print(f"  [{provider_name}] ❌ Failed: {str(e)}")

                if not attempt_all:
                    break

                # Continue to next provider
                continue

        # All providers failed
        providers_str = ", ".join(providers_tried)
        raise Exception(
            f"All search providers failed ({providers_str}). Last error: {str(last_error)}"
        )

    def health_check_all(self) -> dict[str, bool]:
        """
        Check health of all providers

        Returns:
            Dictionary mapping provider names to health status
        """
        print("[SearchProviderManager] Running health checks...")
        status = {}

        for name, provider in self.providers.items():
            if provider.is_configured():
                is_healthy = provider.health_check()
                status[name] = is_healthy
                status_emoji = "✅" if is_healthy else "❌"
                print(f"  [{name}] {status_emoji}")
            else:
                status[name] = False
                print(f"  [{name}] ⚠️  Not configured")

        return status

    def get_status_report(self) -> str:
        """
        Generate a human-readable status report

        Returns:
            Status report string
        """
        report = ["=== Search Provider Status ===\n"]

        for name in self.priority:
            if name not in self.providers:
                report.append(f"❌ {name}: Not implemented")
                continue

            provider = self.providers[name]

            if not provider.is_configured():
                config_status = "⚠️  Not configured"
                if provider.requires_api_key:
                    config_status += " (missing API key)"
                report.append(f"{config_status} {name}")
            else:
                report.append(f"✅ {name}: Configured and ready")

        report.append(f"\nPriority order: {' → '.join(self.priority)}")

        return "\n".join(report)
