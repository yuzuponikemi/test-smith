from src.utils.logging_utils import print_node_header


def subtask_router(state):
    """
    Routes execution based on Master Plan mode

    Returns:
    - "simple" → Use existing Strategic Planner flow (no decomposition)
    - "execute_subtask" → Execute next subtask in hierarchical mode
    - "synthesize" → All subtasks complete, synthesize results
    """
    print_node_header("SUBTASK ROUTER")

    execution_mode = state.get("execution_mode", "simple")

    if execution_mode == "simple":
        print("  Mode: SIMPLE - using existing single-pass flow")
        return "simple"

    # Hierarchical mode
    master_plan = state.get("master_plan")
    if not master_plan:
        print("  ⚠ Warning: Hierarchical mode but no master plan, falling back to simple")
        return "simple"

    current_index = state.get("current_subtask_index", 0)
    total_subtasks = len(master_plan.get("subtasks", []))

    if current_index < total_subtasks:
        subtask_id = master_plan["subtasks"][current_index]["subtask_id"]
        print(
            f"  Mode: HIERARCHICAL - executing subtask {current_index + 1}/{total_subtasks} ({subtask_id})"
        )
        return "execute_subtask"
    else:
        print(f"  Mode: HIERARCHICAL - all {total_subtasks} subtasks complete, ready to synthesize")
        return "synthesize"
