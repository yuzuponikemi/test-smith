"""Minimal self-hosted ReAct loop for the test-smith inner research agent.

Design notes
------------
- Prompt format is classic ReAct: Thought / Action / Action Input.
- Action Input is JSON. The parser is tolerant of single quotes and
  trailing commentary so weaker local models can still drive the loop.
- The scratchpad is the full transcript; no summarisation for the MVP.
- `final_answer` is itself a tool, which keeps the contract uniform.
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .tools.base import Tool, ToolError, ToolResult

# Cap how much of an Observation gets folded back into the scratchpad.
# The full observation is still shown in the verbose log; we only truncate
# the copy that re-enters the prompt so context length stays bounded.
_MAX_OBSERVATION_IN_SCRATCHPAD = 3000
# Ollama streaming sometimes drops the connection on long contexts; we
# retry the LLM call a couple of times before giving up.
_LLM_RETRY_COUNT = 3
_LLM_RETRY_BACKOFF = 4.0


@dataclass
class ReActStep:
    iteration: int
    thought: str
    action: str
    action_input: dict[str, Any]
    observation: str
    duration_seconds: float


@dataclass
class ReActResult:
    answer: str | None
    steps: list[ReActStep] = field(default_factory=list)
    stopped_reason: str = ""
    total_seconds: float = 0.0


_SYSTEM_PROMPT_TEMPLATE = """\
You are a meticulous research agent. You answer the user's question by repeatedly
choosing a tool, observing its result, and reasoning about what to do next.

Tools available to you:
{tools_block}

Use exactly this format for every step, and STOP after Action Input:

Thought: <your reasoning about what to do next, in 1-3 sentences>
Action: <one of the tool names listed above>
Action Input: <a single JSON object matching that tool's input schema>

After your message ends, the SYSTEM (not you) will append:

Observation: <the tool's result>

Then on the next turn you produce the next Thought / Action / Action Input.
Continue until you have enough verified information, then call the
`final_answer` tool with your complete answer.

Hard rules:
1. Always output Thought, Action, and Action Input on separate lines, in that order.
2. Action Input MUST be valid JSON on a single line (no markdown fences, no commentary).
3. Do not invent tool names or fields outside the schemas above.
4. NEVER write your own "Observation:" line. Stop after Action Input and wait.
5. NEVER produce more than one Thought/Action/Action-Input triple per message.
6. To finish, you MUST use the `final_answer` tool with the same Action / Action Input
   syntax. Do not write "final_answer:" inline or skip the JSON.
7. Prefer to verify uncertain facts by fetching primary sources with web_fetch
   before answering. Snippets from web_search are often incomplete.
8. When a list or table is suspicious (gaps, missing items, only partial coverage),
   actively search for and fetch the original source to fill the gaps.

Question: {question}
"""

_ACTION_PATTERN = re.compile(r"(?im)^\s*Action\s*:\s*(.+?)\s*$")
_ACTION_INPUT_PATTERN = re.compile(
    r"(?is)^\s*Action\s*Input\s*:\s*(.+?)(?=\n\s*(?:Thought|Action|Observation)\s*:|\Z)",
    re.MULTILINE,
)
_THOUGHT_PATTERN = re.compile(
    r"(?is)^\s*Thought\s*:\s*(.+?)(?=\n\s*Action\s*:|\Z)", re.MULTILINE
)
# Some Ollama models (e.g. gemma4) emit a `<channel|>` (or similar) marker
# between Thought and Action when their internal chat template leaks.
_CHANNEL_MARKER = re.compile(r"<\s*channel\s*\|?\s*>", re.IGNORECASE)
# Bare `final_answer` followed by the answer text. Accepts `:` OR a newline
# separator, since gemma sometimes drops the colon when it gives up on the
# strict Action / Action Input format and just dumps the answer.
_BARE_FINAL_ANSWER = re.compile(
    r"(?is)(?:^|\n)\s*final_answer\b[\s:]+([^\n].+?)\Z",
)


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


def _parse_action_input(raw: str) -> dict[str, Any]:
    """Tolerant JSON parser for Action Input."""
    raw = _strip_code_fences(raw)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        # Try to recover by trimming to the outermost {...}.
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Action Input must be a JSON object")
    return value


class ReActAgent:
    """A simple ReAct loop. Tools must include a final_answer-style tool."""

    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[Tool],
        max_iterations: int = 10,
        verbose: bool = True,
        stream: Any = sys.stdout,
    ):
        self._llm = llm
        self._tools = {t.name: t for t in tools}
        if "final_answer" not in self._tools:
            raise ValueError("Tool list must include a `final_answer` tool.")
        self._max_iterations = max_iterations
        self._verbose = verbose
        self._stream = stream

    def run(self, question: str) -> ReActResult:
        started = time.time()
        scratchpad = ""
        system_prompt = self._build_system_prompt(question)
        result = ReActResult(answer=None)

        for iteration in range(1, self._max_iterations + 1):
            self._log(f"\n══ Iteration {iteration} ══")
            response = self._call_llm(system_prompt, scratchpad)
            self._log(f"\n[LLM raw output]\n{response}\n")

            parsed = self._parse_step(response)
            if parsed is None:
                observation = (
                    "Your previous message did not follow the required format. "
                    "Please reply with Thought / Action / Action Input again, "
                    "using a single JSON object as Action Input."
                )
                scratchpad += f"\n{response}\nObservation: {observation}\n"
                continue

            thought, action, action_input_raw = parsed
            self._log(f"  Thought: {thought.strip()[:300]}")
            self._log(f"  Action: {action}")
            self._log(f"  Action Input: {action_input_raw.strip()[:300]}")

            try:
                action_input = _parse_action_input(action_input_raw)
            except Exception as e:
                observation = (
                    f"Failed to parse Action Input as JSON ({e}). "
                    f"Please reply with a single JSON object."
                )
                scratchpad += (
                    f"\nThought: {thought}\nAction: {action}\n"
                    f"Action Input: {action_input_raw}\nObservation: {observation}\n"
                )
                continue

            tool = self._tools.get(action)
            if tool is None:
                observation = (
                    f"Unknown tool '{action}'. Available tools: "
                    f"{', '.join(self._tools.keys())}."
                )
                scratchpad += (
                    f"\nThought: {thought}\nAction: {action}\n"
                    f"Action Input: {json.dumps(action_input)}\n"
                    f"Observation: {observation}\n"
                )
                continue

            tool_started = time.time()
            try:
                tool_result: ToolResult = tool.run(action_input)
                observation = tool_result.observation
            except ToolError as e:
                tool_result = ToolResult(observation=f"Tool error: {e}")
                observation = tool_result.observation
            except Exception as e:  # pragma: no cover — defensive
                tool_result = ToolResult(observation=f"Unexpected tool error: {e}")
                observation = tool_result.observation
            duration = time.time() - tool_started

            self._log(f"  Observation ({duration:.1f}s):")
            self._log(textwrap.indent(observation[:1200], "    "))
            if len(observation) > 1200:
                self._log(f"    …[+{len(observation) - 1200} chars]")

            step = ReActStep(
                iteration=iteration,
                thought=thought.strip(),
                action=action,
                action_input=action_input,
                observation=observation,
                duration_seconds=duration,
            )
            result.steps.append(step)

            if tool_result.is_terminal:
                result.answer = str(tool_result.final_payload or observation)
                result.stopped_reason = "final_answer"
                result.total_seconds = time.time() - started
                return result

            scratchpad_obs = observation
            if len(scratchpad_obs) > _MAX_OBSERVATION_IN_SCRATCHPAD:
                kept = _MAX_OBSERVATION_IN_SCRATCHPAD
                scratchpad_obs = (
                    scratchpad_obs[:kept]
                    + f"\n…[truncated {len(observation) - kept} chars in scratchpad; "
                    + "if you need more, re-fetch with a narrower `find` keyword]"
                )
            scratchpad += (
                f"\nThought: {thought.strip()}\n"
                f"Action: {action}\n"
                f"Action Input: {json.dumps(action_input, ensure_ascii=False)}\n"
                f"Observation: {scratchpad_obs}\n"
            )

        result.stopped_reason = "max_iterations"
        result.total_seconds = time.time() - started
        return result

    def _build_system_prompt(self, question: str) -> str:
        tools_block = "\n".join(t.render_for_prompt() for t in self._tools.values())
        return _SYSTEM_PROMPT_TEMPLATE.format(tools_block=tools_block, question=question)

    def _call_llm(self, system_prompt: str, scratchpad: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    "Begin." if not scratchpad
                    else f"Previous steps:\n{scratchpad}\n\nContinue with the next "
                         f"Thought / Action / Action Input."
                )
            ),
        ]
        last_err: Exception | None = None
        for attempt in range(1, _LLM_RETRY_COUNT + 1):
            try:
                response = self._llm.invoke(messages)
                content = response.content
                return content if isinstance(content, str) else str(content)
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as e:
                last_err = e
                self._log(
                    f"  [llm] connection error ({type(e).__name__}: {e}); "
                    f"retry {attempt}/{_LLM_RETRY_COUNT - 1} after {_LLM_RETRY_BACKOFF}s"
                )
                if attempt < _LLM_RETRY_COUNT:
                    time.sleep(_LLM_RETRY_BACKOFF)
        raise RuntimeError(f"LLM call failed after {_LLM_RETRY_COUNT} attempts: {last_err}")

    @staticmethod
    def _parse_step(text: str) -> tuple[str, str, str] | None:
        # Strip leaked chat-template markers like `<channel|>` so the
        # downstream regexes see clean newlines.
        text = _CHANNEL_MARKER.sub("\n", text)
        # Stop at the first hallucinated "Observation:" line — anything
        # after it is the model role-playing the system and must be ignored.
        obs_split = re.search(r"(?im)^\s*Observation\s*:", text)
        if obs_split:
            text = text[: obs_split.start()]

        # Priority 1: detect any `final_answer` in the output and prefer it.
        # When the model produces multiple Action steps in one response (a
        # common gemma4 quirk), the trailing `final_answer` is the model's
        # actual decision; the leading web_searches are noise.
        proper_final = re.search(
            r"(?im)^\s*Action\s*:\s*final_answer\s*$", text
        )
        if proper_final:
            after = text[proper_final.end():]
            input_match = _ACTION_INPUT_PATTERN.search(after)
            if input_match:
                thought_match = _THOUGHT_PATTERN.search(text[: proper_final.start()])
                thought = thought_match.group(1) if thought_match else ""
                return thought, "final_answer", input_match.group(1)

        bare = _BARE_FINAL_ANSWER.search(text)
        if bare:
            answer = bare.group(1).strip()
            if answer:
                payload = json.dumps({"answer": answer}, ensure_ascii=False)
                return ("(recovered from bare final_answer)", "final_answer", payload)

        # Priority 2: take the LAST proper Action + Action Input pair.
        # gemma4 sometimes lists several candidate actions; the last one
        # is the model's latest decision.
        action_matches = list(_ACTION_PATTERN.finditer(text))
        if action_matches:
            last_action = action_matches[-1]
            after = text[last_action.end():]
            input_match = _ACTION_INPUT_PATTERN.search(after)
            if input_match:
                thought_match = _THOUGHT_PATTERN.search(text[: last_action.start()])
                thought = thought_match.group(1) if thought_match else ""
                action = last_action.group(1).strip().strip("`'\" ")
                return thought, action, input_match.group(1)

        return None

    def _log(self, msg: str) -> None:
        if self._verbose:
            print(msg, file=self._stream, flush=True)
