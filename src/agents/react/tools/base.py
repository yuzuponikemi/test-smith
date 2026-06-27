"""Tool base class for the ReAct agent.

Tools are uniform callables that take a parsed dict of arguments
and return a string observation (or raise ToolError).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ToolError(Exception):
    """Raised when a tool call fails in a way the agent should see."""


@dataclass
class ToolResult:
    """Result returned by a tool call."""

    observation: str
    is_terminal: bool = False
    final_payload: Any = None


class Tool(ABC):
    """Base class for tools usable inside the ReAct loop."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description shown in the agent system prompt."""

    @property
    @abstractmethod
    def input_schema(self) -> str:
        """Human-readable JSON schema example shown in the system prompt."""

    @property
    def is_terminal_intent(self) -> bool:
        """True if calling this tool is the agent's signal to stop.

        Used by the parser to disambiguate multi-action LLM responses:
        when an LLM produces several Action / Action Input pairs in a
        single turn, a terminal-intent tool wins over scratch tools
        (web_search, web_fetch) regardless of position. Override to
        ``True`` in :class:`FinalAnswerTool`-style and "submit"-style
        terminals.
        """
        return False

    @abstractmethod
    def run(self, args: dict[str, Any]) -> ToolResult: ...

    def render_for_prompt(self) -> str:
        return f"- {self.name}: {self.description}\n    Input: {self.input_schema}"
