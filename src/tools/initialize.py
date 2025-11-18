"""
Tool Initialization Module

This module provides functions to initialize the tool registry with
built-in function tools and configured MCP servers.
"""

import asyncio
from src.tools.registry import get_tool_registry
from src.tools.function_tools import register_builtin_tools
from src.tools.mcp_config import get_enabled_mcp_servers


def initialize_tools(
    enable_builtin: bool = True,
    enable_mcp: bool = True,
    mcp_servers: list[str] = None
) -> None:
    """
    Initialize the tool registry with configured tools.

    Args:
        enable_builtin: Register built-in function tools
        enable_mcp: Connect to configured MCP servers
        mcp_servers: Specific MCP servers to connect (None = all enabled)
    """
    print("\n=== Initializing Tool System ===\n")

    registry = get_tool_registry()

    # Register built-in function tools
    if enable_builtin:
        register_builtin_tools(registry)

    # Connect to MCP servers
    if enable_mcp:
        mcp_configs = get_enabled_mcp_servers()

        if mcp_servers:
            # Filter to only specified servers
            mcp_configs = {
                name: config
                for name, config in mcp_configs.items()
                if name in mcp_servers
            }

        if mcp_configs:
            print(f"\nConnecting to {len(mcp_configs)} MCP server(s)...")

            for name, config in mcp_configs.items():
                try:
                    registry.add_mcp_server(config)

                    # Connect and discover tools
                    asyncio.run(registry.connect_mcp_server(name))
                    print(f"  Connected to MCP server: {name}")

                except Exception as e:
                    print(f"  Failed to connect to {name}: {e}")
        else:
            print("\nNo MCP servers configured")

    # Summary
    tools = registry.list_tools()
    function_tools = [t for t in tools if t.tool_type == "function"]
    mcp_tools = [t for t in tools if t.tool_type == "mcp"]

    print(f"\n=== Tool System Initialized ===")
    print(f"  Function tools: {len(function_tools)}")
    print(f"  MCP tools: {len(mcp_tools)}")
    print(f"  Total tools: {len(tools)}")

    if tools:
        print("\nAvailable tools:")
        for tool in tools:
            print(f"  - {tool.name} ({tool.tool_type}): {tool.description[:60]}...")

    print()


def list_available_tools() -> None:
    """Print a list of all available tools with details."""
    registry = get_tool_registry()
    tools = registry.list_tools()

    if not tools:
        print("No tools registered. Run initialize_tools() first.")
        return

    print("\n=== Available Tools ===\n")

    # Group by type
    function_tools = [t for t in tools if t.tool_type == "function"]
    mcp_tools = [t for t in tools if t.tool_type == "mcp"]

    if function_tools:
        print("## Function Tools\n")
        for tool in function_tools:
            print(f"### {tool.name}")
            print(f"  {tool.description}")
            if tool.parameters:
                props = tool.parameters.get("properties", {})
                if props:
                    print(f"  Parameters: {', '.join(props.keys())}")
            print()

    if mcp_tools:
        print("## MCP Tools\n")
        for tool in mcp_tools:
            print(f"### {tool.name} (from {tool.source})")
            print(f"  {tool.description}")
            print()


# Convenience function for testing
async def test_tool(tool_name: str, arguments: dict) -> str:
    """
    Test a specific tool with given arguments.

    Args:
        tool_name: Name of the tool to test
        arguments: Arguments to pass to the tool

    Returns:
        Tool execution result
    """
    registry = get_tool_registry()

    if not registry.has_tool(tool_name):
        return f"Tool '{tool_name}' not found"

    result = await registry.execute_tool(tool_name, arguments)
    return result
