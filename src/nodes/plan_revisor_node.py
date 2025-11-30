"""
Plan Revisor Node - Phase 4: Dynamic Replanning

Analyzes subtask execution results and determines if the Master Plan should be
revised to add new subtasks, adjust priorities, or change scope based on discoveries.
"""

from src.models import get_evaluation_model
from src.prompts.plan_revisor_prompt import PLAN_REVISOR_PROMPT
from src.schemas import PlanRevision
from src.utils.logging_utils import print_node_header
from src.utils.recursion_budget import (
    calculate_recursion_budget,
    increment_execution_count,
    log_budget_status,
)


def plan_revisor(state):
    """
    Analyzes subtask results and decides if Master Plan needs revision.

    This node enables adaptive research by detecting:
    - New important topics discovered during research
    - Scope adjustments needed (too narrow/broad)
    - Contradictions requiring resolution
    - Importance shifts (unexpected significance)

    Safety Controls (Phase 4):
    - Respects max_revisions limit (default: 3)
    - Respects max_total_subtasks limit (default: 20)
    - Only revises for important, actionable discoveries

    Phase 4.1 Enhancement - Budget-Aware Control:
    - Checks recursion budget before allowing revisions
    - Limits number of new subtasks based on remaining budget
    - Disables plan revision if budget is critical

    Args:
        state: Current agent state with subtask results and plan

    Returns:
        dict: Updated state with revised master_plan (if revision needed)
    """
    print_node_header("PLAN REVISOR")

    # Track execution
    state.update(increment_execution_count(state))

    execution_mode = state.get("execution_mode", "simple")

    # Only run in hierarchical mode
    if execution_mode != "hierarchical":
        print("  Mode: SIMPLE - skipping plan revision")
        return {}

    # Check recursion budget FIRST (Phase 4.1)
    budget = calculate_recursion_budget(state)
    log_budget_status(budget, context="Plan Revision Decision")

    if not budget["recommendations"]["allow_plan_revision"]:
        print(f"  🚫 PLAN REVISION DISABLED: Recursion budget {budget['status']}")
        print(f"     Current: {budget['current_count']}/{budget['limit']}")
        print("     Skipping revision to conserve budget for remaining subtasks")
        return {}

    # Get current state
    master_plan = state.get("master_plan", {})
    current_subtask_id = state.get("current_subtask_id")
    analyzed_data = state.get("analyzed_data", [])
    depth_evaluation = state.get("depth_evaluation", {})
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)
    max_total_subtasks = state.get("max_total_subtasks", 20)
    plan_revisions = state.get("plan_revisions", [])
    revision_triggers = state.get("revision_triggers", [])
    original_query = state.get("query", "")

    # Get current subtask details
    subtasks = master_plan.get("subtasks", [])
    current_subtask = None
    for st in subtasks:
        if st["subtask_id"] == current_subtask_id:
            current_subtask = st
            break

    if not current_subtask:
        print(f"  Warning: Could not find current subtask {current_subtask_id}")
        return {}

    # Calculate metrics
    completed_subtasks = state.get("current_subtask_index", 0)
    total_subtasks = len(subtasks)
    remaining_subtasks = total_subtasks - completed_subtasks

    print(f"  Analyzing subtask: {current_subtask_id}")
    print(f"  Progress: {completed_subtasks}/{total_subtasks} completed")
    print(f"  Revision budget: {revision_count}/{max_revisions} used")
    print(f"  Subtask budget: {total_subtasks}/{max_total_subtasks} used")

    # Skip revision if at limits
    if revision_count >= max_revisions:
        print(f"  ⚠️  At max revision limit ({max_revisions}) - skipping revision analysis")
        return {}

    if total_subtasks >= max_total_subtasks:
        print(f"  ⚠️  At max subtask limit ({max_total_subtasks}) - skipping revision analysis")
        return {}

    # Format findings
    subtask_findings = "\n\n".join(analyzed_data) if analyzed_data else "No findings available"

    depth_eval_summary = f"""
    - Sufficient: {depth_evaluation.get("is_sufficient", "Unknown")}
    - Quality: {depth_evaluation.get("depth_quality", "Unknown")}
    - Drill-down needed: {depth_evaluation.get("drill_down_needed", "Unknown")}
    - Reasoning: {depth_evaluation.get("reasoning", "No reasoning provided")}
    """

    # Format master plan for prompt
    master_plan_summary = f"""
    Execution Mode: {master_plan.get("execution_mode", "Unknown")}
    Overall Strategy: {master_plan.get("overall_strategy", "No strategy provided")}

    Subtasks:
    """
    for i, st in enumerate(subtasks):
        status = "COMPLETED" if i < completed_subtasks else "PENDING"
        master_plan_summary += f"""
    [{status}] {st["subtask_id"]}: {st["description"]}
              Focus: {st["focus_area"]}
              Priority: {st["priority"]}, Importance: {st["estimated_importance"]}
    """

    # Prepare prompt
    prompt = PLAN_REVISOR_PROMPT.format(
        original_query=original_query,
        master_plan=master_plan_summary,
        total_subtasks=total_subtasks,
        completed_subtasks=completed_subtasks,
        remaining_subtasks=remaining_subtasks,
        current_subtask_id=current_subtask_id,
        current_subtask_description=current_subtask["description"],
        current_subtask_focus=current_subtask["focus_area"],
        current_subtask_importance=current_subtask["estimated_importance"],
        subtask_findings=subtask_findings,
        depth_evaluation=depth_eval_summary,
        revision_count=revision_count,
        max_revisions=max_revisions,
        max_total_subtasks=max_total_subtasks,
    )

    # Invoke LLM with structured output
    try:
        model = get_evaluation_model()
        structured_llm = model.with_structured_output(PlanRevision)

        revision = structured_llm.invoke(prompt)

        print(f"\n  Revision Decision: {'REVISE' if revision.should_revise else 'NO REVISION'}")
        print(f"  Trigger Type: {revision.trigger_type}")
        print(f"  Reasoning: {revision.revision_reasoning[:200]}...")

        if not revision.should_revise:
            print("  ✓ No revision needed - continuing with current plan")
            return {}

        # === REVISION NEEDED ===
        print("\n  🔄 APPLYING PLAN REVISION")

        # Limit new subtasks based on recursion budget (Phase 4.1)
        max_new_allowed = budget["recommendations"]["max_new_subtasks"]
        new_subtasks_to_add = revision.new_subtasks[:max_new_allowed]

        if len(revision.new_subtasks) > max_new_allowed:
            print(
                f"  ⚠️  Budget constraint: Limiting new subtasks from {len(revision.new_subtasks)} to {max_new_allowed}"
            )
            print(
                f"     Skipping: {len(revision.new_subtasks) - max_new_allowed} subtasks due to recursion budget"
            )

        print(f"  New subtasks: {len(new_subtasks_to_add)}")
        print(f"  Removed subtasks: {len(revision.removed_subtasks)}")
        print(f"  Priority changes: {len(revision.priority_changes)}")

        # Apply revision to master plan
        updated_subtasks = subtasks.copy()

        # Add new subtasks (limited by budget)
        for new_st in new_subtasks_to_add:
            # Convert Pydantic model to dict
            new_st_dict = new_st.dict()
            updated_subtasks.append(new_st_dict)
            print(f"    + Added: {new_st.subtask_id} - {new_st.description}")

        # Remove subtasks (mark as skipped, don't delete)
        # We keep them in the list but flag them
        for remove_id in revision.removed_subtasks:
            for st in updated_subtasks:
                if st["subtask_id"] == remove_id:
                    st["skipped"] = True
                    print(f"    - Skipped: {remove_id}")

        # Apply priority changes
        for st_id, new_priority in revision.priority_changes.items():
            for st in updated_subtasks:
                if st["subtask_id"] == st_id:
                    old_priority = st["priority"]
                    st["priority"] = new_priority
                    print(f"    ⚡ Priority change: {st_id} ({old_priority} → {new_priority})")

        # Sort by priority (maintaining execution order)
        # Note: We insert new tasks while respecting priorities
        updated_subtasks.sort(key=lambda x: x["priority"])

        # Update master plan
        updated_master_plan = master_plan.copy()
        updated_master_plan["subtasks"] = updated_subtasks

        # Track revision
        revision_dict = revision.dict()
        plan_revisions.append(revision_dict)
        revision_triggers.append(revision.trigger_type)

        new_revision_count = revision_count + 1
        new_total_subtasks = len(updated_subtasks)

        print("\n  ✓ Plan revised successfully")
        print(f"  New total subtasks: {new_total_subtasks}")
        print(f"  Revisions used: {new_revision_count}/{max_revisions}")
        print(f"  Impact: {revision.estimated_impact[:150]}...")

        return {
            "master_plan": updated_master_plan,
            "revision_count": new_revision_count,
            "plan_revisions": plan_revisions,
            "revision_triggers": revision_triggers,
        }

    except Exception as e:
        print(f"  ⚠️  Plan revision failed: {e}")
        print("  Continuing with current plan")
        return {}
