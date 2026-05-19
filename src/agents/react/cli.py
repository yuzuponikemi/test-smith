"""CLI for running the ReAct agent standalone.

Usage:
    uv run python -m src.agents.react.cli "<question>" [--max-iterations N] [--model role]

This is intentionally separate from the existing graph CLI so it can be
tested independently of the LangGraph pipeline.
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from src.models import _get_model_for_role  # noqa: E402

from .agent import ReActAgent
from .tools import FinalAnswerTool, WebFetchTool, WebSearchTool


def _build_default_agent(role: str, max_iterations: int, temperature: float) -> ReActAgent:
    llm = _get_model_for_role(role, temperature=temperature)
    tools = [WebSearchTool(), WebFetchTool(), FinalAnswerTool()]
    return ReActAgent(llm=llm, tools=tools, max_iterations=max_iterations, verbose=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ReAct research agent.")
    parser.add_argument("question", help="Question to research.")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=12,
        help="Maximum number of ReAct iterations (default: 12).",
    )
    parser.add_argument(
        "--role",
        default="quality",
        choices=["fast", "balanced", "quality"],
        help="Model role (uses current MODEL_QUALITY profile).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="LLM temperature (default: 0.3).",
    )
    args = parser.parse_args(argv)

    agent = _build_default_agent(
        role=args.role,
        max_iterations=args.max_iterations,
        temperature=args.temperature,
    )
    result = agent.run(args.question)

    print("\n" + "=" * 70)
    print(f"Stopped: {result.stopped_reason}  ({result.total_seconds:.1f}s, "
          f"{len(result.steps)} iterations)")
    print("=" * 70)
    if result.answer:
        print("\nFinal Answer:\n")
        print(result.answer)
    else:
        print("\nNo final answer produced.")
    return 0 if result.answer else 1


if __name__ == "__main__":
    sys.exit(main())
