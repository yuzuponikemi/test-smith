from src.models import get_master_planner_model
from src.prompts.master_planner_prompt import MASTER_PLANNER_PROMPT
from src.schemas import MasterPlan
from src.utils.logging_utils import print_node_header


def master_planner(state):
    """
    Master Planner - Detects query complexity and creates Master Plan

    Simple queries: Delegates to Strategic Planner (existing flow)
    Complex queries: Decomposes into subtasks for hierarchical execution

    Phase 1 (v2.0-alpha): Basic hierarchical decomposition
    """
    print_node_header("MASTER PLANNER")

    query = state["query"]
    print(f"  Analyzing query: {query[:100]}...")

    # Get KB metadata for context (reuse existing function from Strategic Planner)
    from src.nodes.planner_node import check_kb_contents

    kb_info = check_kb_contents()

    # Invoke LLM with structured output (using command-r for better structured output)
    model = get_master_planner_model()
    structured_llm = model.with_structured_output(MasterPlan)

    prompt = MASTER_PLANNER_PROMPT.format(
        query=query, kb_summary=kb_info["summary"], kb_available=kb_info["available"]
    )

    try:
        master_plan = structured_llm.invoke(prompt)

        # Log results
        complexity = "COMPLEX" if master_plan.is_complex else "SIMPLE"
        print(f"\n  ✓ Complexity Assessment: {complexity}")
        print(f"  Reasoning: {master_plan.complexity_reasoning[:200]}...")
        print(f"  Execution Mode: {master_plan.execution_mode}")

        if master_plan.is_complex:
            print(f"\n  Subtasks Generated: {len(master_plan.subtasks)}")
            for subtask in master_plan.subtasks:
                deps = f" (depends: {subtask.dependencies})" if subtask.dependencies else ""
                print(
                    f"    {subtask.priority}. [{subtask.subtask_id}] {subtask.description[:80]}...{deps}"
                )
            print(f"\n  Overall Strategy: {master_plan.overall_strategy[:200]}...\n")
        else:
            print(f"  Strategy: {master_plan.overall_strategy[:150]}...\n")

        # Convert to dict for state (LangGraph requires JSON-serializable types)
        return {
            "execution_mode": master_plan.execution_mode,
            "master_plan": master_plan.dict() if master_plan.is_complex else None,
            "current_subtask_index": 0,
            "current_subtask_id": "",
            "subtask_results": {},
            # Phase 2 fields
            "max_depth": 2,  # Maximum recursion depth for Phase 2-beta
            "subtask_evaluations": {},
            # Phase 4 fields (Dynamic Replanning)
            "revision_count": 0,
            "plan_revisions": [],
            "max_revisions": 3,  # Maximum allowed plan revisions
            "max_total_subtasks": 20,  # Maximum total subtasks (including added ones)
            "revision_triggers": [],
            # Phase 4.1 fields (Budget-Aware Control)
            "node_execution_count": 0,  # Track recursion usage
            "recursion_limit": 150,  # Default limit (should match config)
            "budget_warnings": [],
        }

    except Exception as e:
        print("  ⚠ Warning: Master planning failed, falling back to simple mode")
        print(f"  Error: {e}")

        # Fallback: treat as simple query
        return {
            "execution_mode": "simple",
            "master_plan": None,
            "current_subtask_index": 0,
            "current_subtask_id": "",
            "subtask_results": {},
        }
