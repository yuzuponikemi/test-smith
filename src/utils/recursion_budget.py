"""
Recursion Budget Utilities - Phase 4.1

Provides budget-aware control for drill-down and plan revision decisions
to prevent hitting recursion limits.
"""


def calculate_recursion_budget(state):
    """
    Calculate remaining recursion budget and provide recommendations.

    Uses estimation based on observable state (loop_count, subtask_index)
    since node_execution_count may not be accurately tracked.

    Args:
        state: Current agent state with recursion tracking

    Returns:
        dict: Budget analysis with recommendations
    """
    # Constants for estimation (based on typical graph execution patterns)
    NODES_PER_SUBTASK_ITERATION = 8  # planner→searcher→rag→analyzer→evaluator→...
    NODES_PER_SIMPLE_ITERATION = 6  # planner→searcher→rag→analyzer→evaluator→router

    limit = state.get("recursion_limit", 150)

    # Get tracked count (may be 0 if not properly incremented in nodes)
    tracked_count = state.get("node_execution_count", 0)

    # Get observable state for estimation
    loop_count = state.get("loop_count", 0)
    execution_mode = state.get("execution_mode", "simple")

    # Estimate current count based on execution mode
    master_plan = state.get("master_plan", {})
    if execution_mode == "hierarchical" or master_plan:
        total_subtasks = len(master_plan.get("subtasks", [])) if master_plan else 0
        current_index = state.get("current_subtask_index", 0)
        remaining_subtasks = max(0, total_subtasks - current_index)

        # Estimate: master_planner (1) + subtasks processed * nodes per subtask
        # Each subtask can have multiple inner iterations (loop_count resets per subtask)
        estimated_count = (
            1
            + (current_index * NODES_PER_SUBTASK_ITERATION)
            + (loop_count * NODES_PER_SIMPLE_ITERATION)
        )
    else:
        # Simple mode: just count loop iterations
        estimated_count = loop_count * NODES_PER_SIMPLE_ITERATION
        remaining_subtasks = 0
        current_index = 0

    # Use maximum of tracked and estimated count (hybrid approach)
    # - tracked_count: accurate if nodes are properly incrementing
    # - estimated_count: fallback when tracking is incomplete
    current_count = max(tracked_count, estimated_count)
    remaining = max(0, limit - current_count)

    # Calculate percentage used
    usage_percent = (current_count / limit) * 100 if limit > 0 else 100

    # Estimate average recursions per subtask (for hierarchical mode)
    if (execution_mode == "hierarchical" or master_plan) and current_index > 0:
        avg_per_subtask = current_count / current_index
    else:
        avg_per_subtask = NODES_PER_SUBTASK_ITERATION

    # Estimated total needed
    estimated_total_needed = current_count + (remaining_subtasks * avg_per_subtask)

    # Budget status
    if usage_percent >= 90:
        status = "critical"
        message = f"🔴 CRITICAL: {usage_percent:.1f}% used ({remaining} remaining)"
    elif usage_percent >= 70:
        status = "warning"
        message = f"🟡 WARNING: {usage_percent:.1f}% used ({remaining} remaining)"
    elif usage_percent >= 50:
        status = "caution"
        message = f"🟠 CAUTION: {usage_percent:.1f}% used ({remaining} remaining)"
    else:
        status = "healthy"
        message = f"🟢 HEALTHY: {usage_percent:.1f}% used ({remaining} remaining)"

    # Recommendations
    recommendations = {"allow_drill_down": True, "allow_plan_revision": True, "max_new_subtasks": 5}

    if status == "critical":
        recommendations["allow_drill_down"] = False
        recommendations["allow_plan_revision"] = False
        recommendations["max_new_subtasks"] = 0
    elif status == "warning":
        recommendations["allow_drill_down"] = False  # Disable drill-down
        recommendations["allow_plan_revision"] = True  # Allow minimal revision
        recommendations["max_new_subtasks"] = 1  # Max 1 new subtask
    elif status == "caution":
        recommendations["allow_drill_down"] = remaining_subtasks <= 3  # Only if few subtasks left
        recommendations["allow_plan_revision"] = True
        recommendations["max_new_subtasks"] = 2

    return {
        "current_count": current_count,
        "limit": limit,
        "remaining": remaining,
        "usage_percent": usage_percent,
        "status": status,
        "message": message,
        "remaining_subtasks": remaining_subtasks,
        "avg_per_subtask": avg_per_subtask,
        "estimated_total_needed": estimated_total_needed,
        "will_exceed": estimated_total_needed > limit,
        "recommendations": recommendations,
    }


def increment_execution_count(state):
    """
    Increment the node execution counter.

    Args:
        state: Current agent state

    Returns:
        dict: Updated state with incremented counter
    """
    current_count = state.get("node_execution_count", 0)
    return {"node_execution_count": current_count + 1}


def log_budget_status(budget_analysis, context=""):
    """
    Log budget status with context.

    Args:
        budget_analysis: Result from calculate_recursion_budget
        context: Additional context (e.g., "Drill-Down", "Plan Revision")
    """
    status = budget_analysis["status"]
    message = budget_analysis["message"]

    print(f"\n  💰 Recursion Budget ({context}): {message}")

    if budget_analysis["will_exceed"]:
        estimated = budget_analysis["estimated_total_needed"]
        limit = budget_analysis["limit"]
        print(f"  ⚠️  Estimated total needed: {estimated:.0f} (exceeds limit of {limit})")

    if status in ["warning", "critical"]:
        print(f"  📊 Current: {budget_analysis['current_count']}/{budget_analysis['limit']}")
        print(f"  📉 Remaining subtasks: {budget_analysis['remaining_subtasks']}")
        print(f"  📈 Avg per subtask: {budget_analysis['avg_per_subtask']:.1f}")

    recommendations = budget_analysis["recommendations"]
    if not recommendations["allow_drill_down"]:
        print("  🚫 Drill-down DISABLED due to budget constraints")
    if not recommendations["allow_plan_revision"]:
        print("  🚫 Plan revision DISABLED due to budget constraints")
    elif recommendations["max_new_subtasks"] < 5:
        print(f"  ⚠️  Max new subtasks limited to: {recommendations['max_new_subtasks']}")
