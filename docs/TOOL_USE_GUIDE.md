# Tool Use Guide - Test-Smith Phase 5

**Status:** Implemented
**Version:** 2.2 (Phase 5 - Computational Enhancement)

## Overview

Phase 5 introduces **Tool Use** capabilities to Test-Smith, enabling the research agent to:

- Perform calculations and verify numerical claims
- Execute statistical analysis on data
- Parse and analyze JSON/structured data
- Convert units and perform date calculations
- Run Python code for custom computations
- Connect to external MCP servers for additional tools

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Tool Use System                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  Analyzer → Tool Planner → Tool Executor →      │
│                    ↓              ↓              │
│              Tool Registry    Aggregator        │
│             ┌────┴────┐          ↓              │
│        Function    MCP      Depth Evaluator     │
│         Tools     Tools                          │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Built-in Function Tools

### 1. Calculator (`calculator`)
Evaluates mathematical expressions safely.

```python
# Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, exp, abs, round
# Example: "sqrt(16) + 2**3" returns "12.0"
```

### 2. Statistics Analyzer (`statistics_analyzer`)
Performs statistical analysis on number lists.

```python
# Operations: mean, median, mode, stdev, variance, summary
# Example: {"numbers": [10, 20, 30], "operation": "mean"}
```

### 3. JSON Parser (`json_parser`)
Parses JSON and extracts values using dot notation.

```python
# Example: {"json_string": '{"data": {"value": 42}}', "query": "data.value"}
```

### 4. Unit Converter (`unit_converter`)
Converts between common units.

```python
# Supports: length, temperature, weight, data sizes
# Example: {"value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"}
```

### 5. Text Analyzer (`text_analyzer`)
Analyzes text for various metrics.

```python
# Operations: word_count, char_count, sentence_count, readability, summary
# Example: {"text": "...", "analysis_type": "readability"}
```

### 6. Date Calculator (`date_calculator`)
Calculates date differences or adds days.

```python
# Operations: diff, add
# Example: {"operation": "diff", "date1": "2024-01-01", "date2": "2024-12-31"}
```

### 7. Python Executor (`python_executor`)
Executes Python code in a sandboxed environment.

```python
# Safe execution with restricted builtins
# Example: {"code": "print(sum([1,2,3,4,5]))"}
```

## Usage

### Basic Usage

```bash
# Run with tools enabled (default)
python main.py run "What is the compound growth rate if $100 grows to $150 in 3 years?"

# Disable tools
python main.py run "Simple query" --no-tools

# List available tools
python main.py tools

# Initialize and list tools with MCP
python main.py tools --initialize
```

### MCP Server Integration

#### Configuring MCP Servers

Edit `src/tools/mcp_config.py` to add MCP servers:

```python
from src.tools.registry import MCPServerConfig

MCP_SERVERS = {
    "filesystem": MCPServerConfig(
        name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
    ),

    "github": MCPServerConfig(
        name="github",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": "your-token"},
    ),

    "custom_api": MCPServerConfig(
        name="custom_api",
        transport="sse",
        url="http://localhost:8000/sse",
    ),
}
```

#### Running with MCP Servers

```bash
# Connect to specific MCP servers
python main.py run "Query" --mcp-servers filesystem,github
```

### Programmatic Usage

```python
from src.tools import get_tool_registry, initialize_tools

# Initialize
initialize_tools(enable_builtin=True, enable_mcp=True)

# Get registry
registry = get_tool_registry()

# Execute a tool
result = registry.execute_tool_sync("calculator", {"expression": "2+2"})
print(result)  # "Result: 4"

# List all tools
tools = registry.list_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

## Creating Custom Tools

### Function Tools

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.tools import get_tool_registry

# Define input schema
class MyToolInput(BaseModel):
    query: str = Field(description="Input query")

# Create tool with decorator
@tool("my_tool", args_schema=MyToolInput)
def my_tool(query: str) -> str:
    """Description of what my tool does."""
    return f"Result for: {query}"

# Register
registry = get_tool_registry()
registry.register_function_tool(my_tool)
```

### MCP Tools

Create an MCP server following the [MCP specification](https://modelcontextprotocol.io/):

```python
# Server-side (Python)
from mcp.server import Server
from mcp.types import Tool

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="my_mcp_tool",
            description="My MCP tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_mcp_tool":
        return f"Result: {arguments['input']}"
```

## Workflow Integration

The tool system integrates into the Deep Research workflow as Phase 5:

```
Master Planner
     ↓
Strategic Planner
     ↓
Searcher + RAG (parallel)
     ↓
Analyzer
     ↓
Tool Planner ← NEW (Phase 5)
     ↓
Tool Executor ← NEW (Phase 5)
     ↓
Tool Aggregator ← NEW (Phase 5)
     ↓
Depth Evaluator / Evaluator
     ↓
... (rest of workflow)
```

### Tool Planner Node

Analyzes current findings and determines:
- Are there numerical claims to verify?
- Are calculations needed?
- Would data analysis improve quality?

### Tool Executor Node

Executes planned tool calls and:
- Handles errors gracefully
- Returns formatted results
- Supports both sync and async execution

### Tool Results Aggregator

Merges tool results with existing analysis for the synthesizer.

## State Fields

The following fields are added to `DeepResearchState`:

```python
# === Tool Use Fields (Phase 5) ===
tools_enabled: bool       # Whether tool use is enabled
tool_calls: list          # Planned tool invocations
tool_results: list        # Results from execution
tool_results_text: str    # Formatted results for synthesis
tool_planning_result: str # Reasoning from planner
```

## Examples

### Example 1: Mathematical Verification

Query: "What is the annual percentage yield if a $10,000 investment grows to $12,500 in 2 years?"

The tool planner will:
1. Detect numerical claims
2. Plan calculator tool call
3. Execute: `((12500/10000)**(1/2) - 1) * 100`
4. Return: "11.8% annual yield"

### Example 2: Statistical Analysis

Query: "Analyze the performance metrics: [85, 92, 78, 95, 88, 91, 76, 94]"

The tool planner will:
1. Detect need for statistics
2. Plan statistics_analyzer call with "summary" operation
3. Return mean, median, stdev, etc.

### Example 3: JSON Data Analysis

Query: "Extract user count from API response: {\"status\": \"ok\", \"data\": {\"users\": 1500}}"

The tool planner will:
1. Detect JSON parsing need
2. Plan json_parser call with query "data.users"
3. Return: "1500"

## Troubleshooting

### "Tool not found" Error

```python
# Check if tool is registered
registry = get_tool_registry()
print(registry.has_tool("my_tool"))  # Should be True

# List all tools
for tool in registry.list_tools():
    print(tool.name)
```

### MCP Connection Failures

1. Ensure MCP package is installed: `pip install mcp`
2. Check server command is correct
3. Verify network connectivity (for SSE)
4. Check environment variables

### Tool Execution Timeout

For long-running tools, increase the timeout:
```python
@tool("slow_tool", args_schema=SlowToolInput)
def slow_tool(input: str) -> str:
    # Long operation
    pass

# Or use async
async def execute():
    result = await registry.execute_tool("slow_tool", {"input": "..."})
```

## Security Considerations

1. **Python Executor**: Runs in sandboxed environment with restricted builtins
2. **MCP Servers**: Only connect to trusted servers
3. **Input Validation**: All tools use Pydantic schemas for validation
4. **No Network Access**: Built-in tools don't make network requests

## Dependencies

Required packages (add to requirements.txt):
```
mcp>=0.1.0  # For MCP tool support (optional)
```

The MCP package is optional - the system works fine with only function tools.

## Future Enhancements

- [ ] Tool result caching
- [ ] Parallel tool execution
- [ ] Tool execution history/replay
- [ ] Custom tool timeout configuration
- [ ] Tool sandboxing improvements (Docker/E2B)
