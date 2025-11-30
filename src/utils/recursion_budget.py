"""
Recursion Budget Utilities - Phase 4.1

Provides budget-aware control for drill-down and plan revision decisions
to prevent hitting recursion limits.
"""


def calculate_recursion_budget(state):
    """
    Calculate remaining recursion budget and provide recommendations.

    Args:
        state: Current agent state with recursion tracking

    Returns:
        dict: Budget analysis with recommendations
    """
    current_count = state.get("node_execution_count", 0)
    limit = state.get("recursion_limit", 150)
    remaining = limit - current_count

    # Calculate percentage used
    usage_percent = (current_count / limit) * 100 if limit > 0 else 100

    # Estimate remaining subtasks
    master_plan = state.get("master_plan", {})
    if master_plan:
        total_subtasks = len(master_plan.get("subtasks", []))
        current_index = state.get("current_subtask_index", 0)
        remaining_subtasks = total_subtasks - current_index
    else:
        remaining_subtasks = 0

    # Estimate average recursions per subtask
    avg_per_subtask = current_count / max(current_index, 1) if current_index > 0 else 10

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
