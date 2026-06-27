"""final_answer tool: terminates the ReAct loop with the agent's answer."""

from __future__ import annotations

from typing import Any

from .base import Tool, ToolError, ToolResult


class FinalAnswerTool(Tool):
    @property
    def name(self) -> str:
        return "final_answer"

    @property
    def is_terminal_intent(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return (
            "Provide the final answer to the user and stop the loop. "
            "Only call this once you have enough verified information."
        )

    @property
    def input_schema(self) -> str:
        return '{"answer": "<the full answer text shown to the user>"}'

    def run(self, args: dict[str, Any]) -> ToolResult:
        answer = args.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ToolError("final_answer requires a non-empty 'answer' string")
        return ToolResult(observation=answer, is_terminal=True, final_payload=answer)
