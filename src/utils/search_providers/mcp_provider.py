"""
MCP (Model Context Protocol) Search Provider

Uses a local MCP server (e.g., local-search-mcp) for search operations.
No API key required - connects to local server via stdio.
"""

import json
import os
import re
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .base_provider import BaseSearchProvider, SearchResult


class MCPSearchProvider(BaseSearchProvider):
    """MCP search provider implementation"""

    def __init__(
        self,
        server_command: Optional[str] = None,
        server_args: Optional[str] = None,
        server_env: Optional[str] = None,
    ):
        """
        Initialize MCP provider

        Args:
            server_command: Command to start MCP server (e.g., "uv")
            server_args: Space-separated arguments for the server command
            server_env: JSON string of environment variables for the server
        """
        super().__init__(api_key=None)

        # Get configuration from environment or parameters
        self.server_command = server_command or os.environ.get(
            "MCP_SERVER_COMMAND", "uv"
        )
        self.server_args_str = server_args or os.environ.get(
            "MCP_SERVER_ARGS", "--directory /path/to/local-search-mcp run src/server.py"
        )
        self.server_env_str = server_env or os.environ.get("MCP_SERVER_ENV", "{}")

        # Parse server arguments
        self.server_args = self.server_args_str.split()

        # Parse environment variables
        try:
            self.server_env = json.loads(self.server_env_str)
        except json.JSONDecodeError:
            print(f"[{self.name}] Warning: Failed to parse MCP_SERVER_ENV, using empty dict")
            self.server_env = {}

        # Create server parameters
        self.server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=self.server_env if self.server_env else None,
        )

    @property
    def name(self) -> str:
        return "mcp"

    @property
    def requires_api_key(self) -> bool:
        return False

    def _parse_wikipedia_response(self, raw_text: str) -> list[SearchResult]:
        """
        Parse MCP server response into SearchResult objects

        The local-search-mcp server returns text in format:
        Title: <title>
        Source: <url>
        Content: <content>

        Args:
            raw_text: Raw text response from MCP server

        Returns:
            List of SearchResult objects
        """
        results = []

        # Pattern to match Wikipedia article format
        # Matches: Title: ... \n Source: ... \n Content: ...
        pattern = r"Title:\s*(.+?)\s*\nSource:\s*(.+?)\s*\nContent:\s*(.+?)(?=\n\nTitle:|$)"

        matches = re.finditer(pattern, raw_text, re.DOTALL)

        for match in matches:
            title = match.group(1).strip()
            source = match.group(2).strip()
            content = match.group(3).strip()

            # Create a local URL format for identification
            url = f"local://Wikipedia/{title.replace(' ', '_')}"

            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    content=content,
                )
            )

        # If no matches found, return the raw text as a single result
        if not results:
            results.append(
                SearchResult(
                    title="MCP Search Result",
                    url="local://mcp/result",
                    content=raw_text,
                )
            )

        return results

    async def _async_search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """
        Internal async search implementation

        Args:
            query: Search query string
            max_results: Maximum number of results (passed to MCP tool if supported)

        Returns:
            List of SearchResult objects

        Raises:
            ConnectionError: If MCP server fails to start
            Exception: If search operation fails
        """
        try:
            # Connect to MCP server via stdio
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    # List available tools (optional, for debugging)
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]

                    if "search_wikipedia" not in tool_names:
                        raise Exception(
                            f"MCP server does not provide 'search_wikipedia' tool. "
                            f"Available tools: {tool_names}"
                        )

                    # Call the search_wikipedia tool
                    result = await session.call_tool(
                        "search_wikipedia",
                        arguments={"query": query},
                    )

                    # Extract text content from result
                    if hasattr(result, "content") and result.content:
                        # MCP returns content as a list of content items
                        raw_text = ""
                        for item in result.content:
                            if hasattr(item, "text"):
                                raw_text += item.text
                            elif isinstance(item, dict) and "text" in item:
                                raw_text += item["text"]
                            else:
                                raw_text += str(item)

                        # Parse the response
                        return self._parse_wikipedia_response(raw_text)
                    else:
                        raise Exception(f"MCP server returned unexpected result format: {result}")

        except ConnectionError as e:
            raise ConnectionError(
                f"Failed to connect to MCP server. "
                f"Command: {self.server_command} {' '.join(self.server_args)}. "
                f"Error: {str(e)}"
            ) from e
        except Exception as e:
            raise Exception(f"MCP search failed: {str(e)}") from e

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """
        Execute search using MCP server

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If search fails
        """
        import asyncio

        # Run async search in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._async_search(query, max_results))

    def is_configured(self) -> bool:
        """
        Check if MCP provider is properly configured

        Returns:
            True if server command and args are set
        """
        # Check if the server command and args contain placeholder paths
        if "/path/to/local-search-mcp" in self.server_args_str:
            return False

        return True
