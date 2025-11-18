"""
MCP Server Configuration

This file defines the MCP servers that can be connected to for external tools.
Users can add their own MCP servers here.

Example MCP servers:
- filesystem: File system operations
- memory: Persistent memory/knowledge graph
- puppeteer: Web browser automation
- github: GitHub API operations
"""

from src.tools.registry import MCPServerConfig


# Default MCP server configurations
# Users can customize these or add new ones

MCP_SERVERS = {
    # Example: Filesystem MCP server
    # Uncomment and configure to use
    #
    # "filesystem": MCPServerConfig(
    #     name="filesystem",
    #     transport="stdio",
    #     command="npx",
    #     args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
    # ),

    # Example: Memory MCP server (knowledge graph)
    # Uncomment and configure to use
    #
    # "memory": MCPServerConfig(
    #     name="memory",
    #     transport="stdio",
    #     command="npx",
    #     args=["-y", "@modelcontextprotocol/server-memory"],
    # ),

    # Example: GitHub MCP server
    # Uncomment and configure to use (requires GITHUB_TOKEN env var)
    #
    # "github": MCPServerConfig(
    #     name="github",
    #     transport="stdio",
    #     command="npx",
    #     args=["-y", "@modelcontextprotocol/server-github"],
    #     env={"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")},
    # ),

    # Example: Custom SSE server
    # "custom_api": MCPServerConfig(
    #     name="custom_api",
    #     transport="sse",
    #     url="http://localhost:8000/sse",
    # ),
}


def get_enabled_mcp_servers() -> dict[str, MCPServerConfig]:
    """
    Get all enabled MCP server configurations.

    Returns:
        Dictionary of server name to MCPServerConfig
    """
    # Filter to only return servers that are actually configured
    return {
        name: config
        for name, config in MCP_SERVERS.items()
        if config is not None
    }


def add_mcp_server(
    name: str,
    transport: str,
    command: str = None,
    args: list = None,
    url: str = None,
    env: dict = None
) -> None:
    """
    Add a new MCP server configuration at runtime.

    Args:
        name: Unique name for the server
        transport: "stdio" or "sse"
        command: Command to run (for stdio)
        args: Command arguments (for stdio)
        url: Server URL (for sse)
        env: Environment variables
    """
    MCP_SERVERS[name] = MCPServerConfig(
        name=name,
        transport=transport,
        command=command,
        args=args or [],
        url=url,
        env=env or {}
    )
