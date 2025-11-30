from src.utils.logging_utils import print_node_header
from src.utils.recursion_budget import (
    calculate_recursion_budget,
    increment_execution_count,
    log_budget_status,
)


def drill_down_generator(state):
    """
    Drill-Down Generator - Creates child subtasks when deeper exploration is needed

    Phase 3 (v2.0) functionality:
    - Checks if current subtask needs drill-down (from depth_evaluation)
    - Creates child SubTasks from drill_down_areas
    - Inserts children into master_plan.subtasks for execution
    - Respects max_depth limit

    Phase 4.1 (Budget-Aware) enhancement:
    - Checks recursion budget before creating child subtasks
    - Limits number of children based on remaining budget
    - Disables drill-down if budget is critical

    Returns updated master_plan with child subtasks added.
    """
    print_node_header("DRILL-DOWN GENERATOR")

    # Track execution
    state.update(increment_execution_count(state))

    # Get current state
    depth_evaluation = state.get("depth_evaluation", {})
    current_subtask_id = state.get("current_subtask_id", "")
    master_plan = state.get("master_plan", {})
    max_depth = state.get("max_depth", 2)

    # Check recursion budget FIRST (Phase 4.1)
    budget = calculate_recursion_budget(state)
    log_budget_status(budget, context="Drill-Down Decision")

    if not budget["recommendations"]["allow_drill_down"]:
        print(f"  🚫 DRILL-DOWN DISABLED: Recursion budget {budget['status']}")
        print(f"     Current: {budget['current_count']}/{budget['limit']}")
        print("     Skipping drill-down to conserve budget for remaining subtasks")
        return {}

    # Check if drill-down is needed
    drill_down_needed = depth_evaluation.get("drill_down_needed", False)

    if not drill_down_needed:
        print("  No drill-down needed, continuing...")
        return {}

    # Find current subtask
    all_subtasks = master_plan.get("subtasks", [])
    current_subtask = None
    for subtask in all_subtasks:
        if subtask["subtask_id"] == current_subtask_id:
            current_subtask = subtask
            break

    if not current_subtask:
        print(f"  ⚠ Warning: Could not find subtask {current_subtask_id}, skipping drill-down")
        return {}

    current_depth = current_subtask.get("depth", 0)

    # Check depth limit
    if current_depth >= max_depth:
        print(f"  ⚠ Max depth {max_depth} reached, cannot drill down further")
        return {}

    # Get drill-down areas
    drill_down_areas = depth_evaluation.get("drill_down_areas", [])
    if not drill_down_areas:
        print("  ⚠ Warning: drill_down_needed but no drill_down_areas provided")
        return {}

    # Limit number of drill-down areas based on budget (Phase 4.1)
    max_children = min(len(drill_down_areas), 3)  # Never more than 3 regardless
    if budget["status"] in ["warning", "caution"]:
        # Further limit based on budget status
        max_children = min(max_children, 2 if budget["status"] == "caution" else 1)
        if len(drill_down_areas) > max_children:
            print(
                f"  ⚠️  Budget constraint: Limiting drill-down from {len(drill_down_areas)} to {max_children} areas"
            )
            drill_down_areas = drill_down_areas[:max_children]

    print(f"  Creating {len(drill_down_areas)} child subtasks for {current_subtask_id}")
    print(f"  Parent depth: {current_depth} → Child depth: {current_depth + 1}")

    # Create child subtasks
    child_subtasks = []
    for idx, area in enumerate(drill_down_areas, start=1):
        child_id = f"{current_subtask_id}.{idx}"

        child_subtask = {
            "subtask_id": child_id,
            "parent_id": current_subtask_id,
            "depth": current_depth + 1,
            "description": area,
            "focus_area": f"Drill-down: {area[:50]}...",
            "priority": len(all_subtasks) + idx,  # Append after existing subtasks
            "dependencies": [current_subtask_id],  # Depends on parent
            "estimated_importance": current_subtask.get("estimated_importance", 0.7),
        }

        child_subtasks.append(child_subtask)
        print(f"    [{child_id}] {area[:80]}...")

    # Insert children into master_plan after current subtask
    # Find insertion point (right after current subtask)
    current_idx = None
    for idx, subtask in enumerate(all_subtasks):
        if subtask["subtask_id"] == current_subtask_id:
            current_idx = idx
            break

    if current_idx is not None:
        # Make a copy of master_plan to modify
        updated_master_plan = dict(master_plan)
        updated_subtasks = list(all_subtasks)

        # Insert children right after parent
        for i, child in enumerate(child_subtasks):
            updated_subtasks.insert(current_idx + 1 + i, child)

        updated_master_plan["subtasks"] = updated_subtasks

        print(f"  ✓ Inserted {len(child_subtasks)} children after index {current_idx}")
        print(f"  Total subtasks: {len(all_subtasks)} → {len(updated_subtasks)}\n")

        return {"master_plan": updated_master_plan}
    else:
        print(f"  ⚠ Error: Could not find insertion point for {current_subtask_id}")
        return {}
