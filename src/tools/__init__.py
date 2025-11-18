"""
Tool Use System for Test-Smith

This module provides a unified interface for executing both:
- Function tools (Python functions with @tool decorator)
- MCP tools (Model Context Protocol external services)

Usage:
    from src.tools import ToolRegistry, get_tool_registry

    # Get singleton registry
    registry = get_tool_registry()

    # List available tools
    tools = registry.list_tools()

    # Execute a tool
    result = await registry.execute_tool("calculator", {"expression": "2+2"})
"""

from src.tools.registry import ToolRegistry, get_tool_registry, MCPServerConfig
from src.tools.function_tools import register_builtin_tools
from src.tools.initialize import initialize_tools, list_available_tools
from src.tools.mcp_config import add_mcp_server, get_enabled_mcp_servers

__all__ = [
    "ToolRegistry",
    "get_tool_registry",
    "MCPServerConfig",
    "register_builtin_tools",
    "initialize_tools",
    "list_available_tools",
    "add_mcp_server",
    "get_enabled_mcp_servers",
]
