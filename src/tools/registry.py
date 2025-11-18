"""
Tool Registry - Unified management for function and MCP tools

This registry provides:
- Registration of function tools (Python functions)
- Connection to MCP servers for external tools
- Unified interface for tool discovery and execution
- Thread-safe singleton pattern
"""

import asyncio
import json
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel

# MCP imports (optional - graceful fallback if not installed)
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP package not installed. MCP tools will not be available.")
    print("Install with: pip install mcp")


@dataclass
class ToolInfo:
    """Information about a registered tool"""
    name: str
    description: str
    parameters: dict  # JSON Schema
    tool_type: str  # "function" or "mcp"
    source: str  # Module name for function, server name for MCP


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection"""
    name: str
    transport: str  # "stdio" or "sse"
    command: Optional[str] = None  # For stdio transport
    args: list = field(default_factory=list)  # For stdio transport
    url: Optional[str] = None  # For SSE transport
    env: dict = field(default_factory=dict)  # Environment variables


class ToolRegistry:
    """
    Unified registry for function tools and MCP tools.

    Supports:
    - Function tools: Python functions decorated with LangChain's @tool
    - MCP tools: Tools from MCP servers via stdio or SSE transport
    """

    def __init__(self):
        self._function_tools: dict[str, BaseTool] = {}
        self._mcp_servers: dict[str, MCPServerConfig] = {}
        self._mcp_sessions: dict[str, Any] = {}  # Active MCP sessions
        self._mcp_tools: dict[str, dict] = {}  # tool_name -> {server, tool_info}
        self._initialized = False

    def register_function_tool(self, tool: BaseTool) -> None:
        """
        Register a LangChain tool (function tool).

        Args:
            tool: A LangChain BaseTool instance
        """
        self._function_tools[tool.name] = tool
        print(f"  Registered function tool: {tool.name}")

    def register_function(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        args_schema: Optional[type[BaseModel]] = None
    ) -> None:
        """
        Register a plain Python function as a tool.

        Args:
            func: The function to register
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            args_schema: Pydantic model for arguments
        """
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or "No description"

        tool = StructuredTool.from_function(
            func=func,
            name=tool_name,
            description=tool_desc,
            args_schema=args_schema
        )
        self.register_function_tool(tool)

    def add_mcp_server(self, config: MCPServerConfig) -> None:
        """
        Add an MCP server configuration.

        Args:
            config: MCP server configuration
        """
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP package not installed. Run: pip install mcp")

        self._mcp_servers[config.name] = config
        print(f"  Added MCP server config: {config.name} ({config.transport})")

    async def connect_mcp_server(self, server_name: str) -> None:
        """
        Connect to an MCP server and discover its tools.

        Args:
            server_name: Name of the server (must be added via add_mcp_server first)
        """
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP package not installed")

        if server_name not in self._mcp_servers:
            raise ValueError(f"Unknown MCP server: {server_name}")

        config = self._mcp_servers[server_name]

        try:
            if config.transport == "stdio":
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env or None
                )

                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()

                        # Discover tools
                        tools_result = await session.list_tools()

                        for tool in tools_result.tools:
                            self._mcp_tools[tool.name] = {
                                "server": server_name,
                                "tool": tool,
                                "session_factory": lambda: self._create_mcp_session(config)
                            }
                            print(f"  Discovered MCP tool: {tool.name} from {server_name}")

            elif config.transport == "sse":
                async with sse_client(config.url) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()

                        # Discover tools
                        tools_result = await session.list_tools()

                        for tool in tools_result.tools:
                            self._mcp_tools[tool.name] = {
                                "server": server_name,
                                "tool": tool,
                                "session_factory": lambda: self._create_mcp_session(config)
                            }
                            print(f"  Discovered MCP tool: {tool.name} from {server_name}")

            else:
                raise ValueError(f"Unknown transport: {config.transport}")

        except Exception as e:
            print(f"  Error connecting to MCP server {server_name}: {e}")
            raise

    async def _create_mcp_session(self, config: MCPServerConfig):
        """Create a new MCP session for tool execution"""
        if config.transport == "stdio":
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or None
            )
            return stdio_client(server_params)
        elif config.transport == "sse":
            return sse_client(config.url)

    def list_tools(self) -> list[ToolInfo]:
        """
        List all available tools (function + MCP).

        Returns:
            List of ToolInfo objects
        """
        tools = []

        # Function tools
        for name, tool in self._function_tools.items():
            # Get schema
            schema = {}
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()

            tools.append(ToolInfo(
                name=name,
                description=tool.description,
                parameters=schema,
                tool_type="function",
                source=tool.__class__.__module__
            ))

        # MCP tools
        for name, info in self._mcp_tools.items():
            tool = info["tool"]
            tools.append(ToolInfo(
                name=name,
                description=tool.description or "No description",
                parameters=tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                tool_type="mcp",
                source=info["server"]
            ))

        return tools

    def get_tool_schemas(self) -> list[dict]:
        """
        Get tool schemas in OpenAI function calling format.

        Returns:
            List of tool schemas for LLM function calling
        """
        schemas = []

        for tool_info in self.list_tools():
            schema = {
                "type": "function",
                "function": {
                    "name": tool_info.name,
                    "description": tool_info.description,
                    "parameters": tool_info.parameters or {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            schemas.append(schema)

        return schemas

    async def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        # Check function tools first
        if tool_name in self._function_tools:
            tool = self._function_tools[tool_name]
            try:
                # LangChain tools can be sync or async
                if asyncio.iscoroutinefunction(tool._run):
                    result = await tool._arun(**arguments)
                else:
                    result = tool._run(**arguments)
                return result
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"

        # Check MCP tools
        if tool_name in self._mcp_tools:
            return await self._execute_mcp_tool(tool_name, arguments)

        return f"Error: Unknown tool '{tool_name}'"

    async def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute an MCP tool"""
        if not MCP_AVAILABLE:
            return "Error: MCP package not installed"

        info = self._mcp_tools[tool_name]
        config = self._mcp_servers[info["server"]]

        try:
            if config.transport == "stdio":
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env or None
                )

                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments)
                        return result.content

            elif config.transport == "sse":
                async with sse_client(config.url) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments)
                        return result.content

        except Exception as e:
            return f"Error executing MCP tool {tool_name}: {str(e)}"

    def execute_tool_sync(self, tool_name: str, arguments: dict) -> Any:
        """
        Synchronous wrapper for execute_tool.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, need to handle differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.execute_tool(tool_name, arguments)
                )
                return future.result()
        except RuntimeError:
            # No running loop, we can use asyncio.run
            return asyncio.run(self.execute_tool(tool_name, arguments))

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered"""
        return tool_name in self._function_tools or tool_name in self._mcp_tools

    def get_tools_for_llm(self) -> list[BaseTool]:
        """
        Get function tools as LangChain tools for LLM binding.

        Returns:
            List of LangChain BaseTool objects
        """
        return list(self._function_tools.values())


# Singleton instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry singleton.

    Returns:
        The global ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
