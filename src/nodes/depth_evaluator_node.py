from src.models import get_evaluation_model
from src.prompts.depth_evaluator_prompt import DEPTH_EVALUATOR_PROMPT
from src.schemas import DepthEvaluation
from src.utils.logging_utils import print_node_header


def depth_evaluator(state):
    """
    Depth Evaluator - Assesses subtask result depth and determines drill-down needs

    Used in hierarchical mode (Phase 2) to evaluate if a subtask has been explored
    sufficiently or if it needs deeper investigation through child subtasks.

    Returns DepthEvaluation with:
    - is_sufficient: Whether current depth is adequate
    - depth_quality: "superficial", "adequate", or "deep"
    - drill_down_needed: Whether to create child subtasks
    - drill_down_areas: Specific areas for deeper exploration
    - reasoning: Explanation of the assessment
    """
    print_node_header("DEPTH EVALUATOR")

    # Get current subtask context
    master_plan = state.get("master_plan", {})
    current_subtask_id = state.get("current_subtask_id", "")
    analyzed_data = state.get("analyzed_data", [])
    original_query = state.get("query", "")
    max_depth = state.get("max_depth", 2)  # Default max depth for Phase 2-beta

    # Find current subtask details
    all_subtasks = master_plan.get("subtasks", [])
    current_subtask = None
    for subtask in all_subtasks:
        if subtask["subtask_id"] == current_subtask_id:
            current_subtask = subtask
            break

    if not current_subtask:
        print(f"  ⚠ Warning: Could not find subtask {current_subtask_id}, defaulting to sufficient")
        return {
            "depth_evaluation": {
                "is_sufficient": True,
                "depth_quality": "adequate",
                "drill_down_needed": False,
                "drill_down_areas": [],
                "reasoning": "Could not find subtask details, marking as sufficient to continue."
            }
        }

    # Get current depth from subtask
    current_depth = current_subtask.get("depth", 0)

    # Get most recent analysis (for this subtask)
    latest_analysis = analyzed_data[-1] if analyzed_data else "No analysis available"

    print(f"  Evaluating subtask: {current_subtask_id}")
    print(f"  Depth: {current_depth}/{max_depth}")
    print(f"  Importance: {current_subtask.get('estimated_importance', 0.5)}")

    # Calculate recursion status
    if current_depth >= max_depth:
        recursion_status = "⚠️ At max depth - cannot drill down further"
    else:
        levels_remaining = max_depth - current_depth
        recursion_status = f"✓ Can drill down ({levels_remaining} levels remaining)"

    # Build prompt
    prompt = DEPTH_EVALUATOR_PROMPT.format(
        original_query=original_query,
        subtask_id=current_subtask_id,
        subtask_description=current_subtask.get("description", ""),
        subtask_focus=current_subtask.get("focus_area", ""),
        subtask_importance=current_subtask.get("estimated_importance", 0.5),
        current_depth=current_depth,
        max_depth=max_depth,
        recursion_status=recursion_status,
        analyzed_data=latest_analysis
    )

    # Get LLM evaluation with structured output
    model = get_evaluation_model()
    structured_llm = model.with_structured_output(DepthEvaluation)

    try:
        depth_eval = structured_llm.invoke(prompt)

        # Log results
        print(f"  Depth Quality: {depth_eval.depth_quality}")
        print(f"  Is Sufficient: {depth_eval.is_sufficient}")
        print(f"  Drill-Down Needed: {depth_eval.drill_down_needed}")

        if depth_eval.drill_down_needed:
            print(f"  Drill-Down Areas ({len(depth_eval.drill_down_areas)}):")
            for area in depth_eval.drill_down_areas:
                print(f"    - {area[:80]}...")

        print(f"  Reasoning: {depth_eval.reasoning[:150]}...")

        # Convert to dict for state
        return {
            "depth_evaluation": depth_eval.dict()
        }

    except Exception as e:
        print("  ⚠ Warning: Depth evaluation failed, defaulting to sufficient")
        print(f"  Error: {e}")

        # Fallback: mark as sufficient to avoid blocking
        return {
            "depth_evaluation": {
                "is_sufficient": True,
                "depth_quality": "adequate",
                "drill_down_needed": False,
                "drill_down_areas": [],
                "reasoning": f"Depth evaluation failed with error, marked as sufficient. Error: {str(e)[:100]}"
            }
        }
