"""ReAct agent — public API façade.

Re-exports the public surface from ``src.agents.react``. Internal
implementation lives in ``src/``; this module exists so external
packages (factfull etc.) can avoid depending on the ``src.*`` namespace.
"""

from src.agents.react.agent import ReActAgent, ReActResult, ReActStep
from src.agents.react.tools import (
    FinalAnswerTool,
    Tool,
    ToolError,
    ToolResult,
    WebFetchTool,
    WebSearchTool,
)

__all__ = [
    "ReActAgent",
    "ReActResult",
    "ReActStep",
    "Tool",
    "ToolError",
    "ToolResult",
    "WebSearchTool",
    "WebFetchTool",
    "FinalAnswerTool",
]
