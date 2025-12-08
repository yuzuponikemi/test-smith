from src.models import get_evaluation_model
from src.prompts.evaluator_prompt import EVALUATOR_PROMPT
from src.schemas import Evaluation
from src.utils.logging_utils import print_node_header
from src.utils.structured_logging import log_evaluation_result, log_node_execution, log_performance


def _get_strictness_guidance(depth_config) -> str:
    """Generate strictness guidance based on research depth config."""
    strictness = depth_config.evaluator_strictness
    min_sources = depth_config.min_sources_required

    guidance_map = {
        "lenient": (
            f"\n## Evaluation Strictness: LENIENT\n"
            f"- Be forgiving with information gaps\n"
            f"- Mark as SUFFICIENT if basic facts are covered\n"
            f"- Minimum sources needed: {min_sources}\n"
        ),
        "standard": (
            f"\n## Evaluation Strictness: STANDARD\n"
            f"- Balance thoroughness with efficiency\n"
            f"- Require good coverage of main points\n"
            f"- Minimum sources needed: {min_sources}\n"
        ),
        "strict": (
            f"\n## Evaluation Strictness: STRICT\n"
            f"- Require comprehensive coverage\n"
            f"- Multiple perspectives must be represented\n"
            f"- Minimum sources needed: {min_sources}\n"
            f"- Mark as INSUFFICIENT if any significant gaps exist\n"
        ),
        "very_strict": (
            f"\n## Evaluation Strictness: VERY STRICT\n"
            f"- Demand exhaustive coverage from all angles\n"
            f"- Require deep analysis with extensive evidence\n"
            f"- Minimum sources needed: {min_sources}\n"
            f"- Only mark SUFFICIENT if truly comprehensive\n"
        ),
    }
    return guidance_map.get(strictness, guidance_map["standard"])


def evaluator_node(state):
    print_node_header("EVALUATOR")

    with log_node_execution("evaluator", state) as logger:
        model = get_evaluation_model()

        # Get context for evaluation
        original_query = state.get("query", "")
        allocation_strategy = state.get("allocation_strategy", "")
        analyzed_data = state.get("analyzed_data", [])
        loop_count = state.get("loop_count", 0)
        research_depth = state.get("research_depth", "standard")

        # Get depth-aware evaluation settings
        from src.config.research_depth import get_depth_config

        depth_config = get_depth_config(research_depth)

        logger.info(
            "evaluation_start",
            data_count=len(analyzed_data),
            iteration=loop_count,
            depth=research_depth,
            strictness=depth_config.evaluator_strictness,
        )
        print(f"  Evaluating iteration {loop_count} (depth={research_depth}, strictness={depth_config.evaluator_strictness})")

        # Use structured output for reliable evaluation
        structured_llm = model.with_structured_output(Evaluation)

        # Build depth-aware evaluation guidance
        strictness_guidance = _get_strictness_guidance(depth_config)

        prompt = EVALUATOR_PROMPT.format(
            original_query=original_query,
            allocation_strategy=allocation_strategy,
            analyzed_data=analyzed_data,
            loop_count=loop_count,
        ) + strictness_guidance

        try:
            with log_performance(logger, "evaluation_llm_call"):
                evaluation = structured_llm.invoke(prompt)

            result = "sufficient" if evaluation.is_sufficient else "insufficient"

            # Log evaluation result
            log_evaluation_result(logger, evaluation.is_sufficient, evaluation.reason, loop_count)

            print(f"  Result: {result}")
            print(f"  Reason: {evaluation.reason[:100]}...")

            return {"evaluation": result, "reason": evaluation.reason}

        except Exception as e:
            logger.warning("evaluation_fallback", error_type=type(e).__name__, error_message=str(e))
            print(f"  Warning: Structured evaluation failed, using fallback: {e}")

            message = model.invoke(prompt)
            return {"evaluation": message.content, "reason": "Fallback evaluation used"}
