def subtask_executor(state):
    """
    Prepares state for executing a single subtask

    Extracts current subtask from Master Plan and sets up context
    for Strategic Planner to execute this specific subtask.

    The Strategic Planner will receive a focused query for this subtask
    instead of the original broad query.
    """
    print("---SUBTASK EXECUTOR---")

    master_plan = state["master_plan"]
    current_index = state["current_subtask_index"]
    subtasks = master_plan["subtasks"]

    if current_index >= len(subtasks):
        print("  ⚠ Error: No more subtasks to execute")
        return {}

    current_subtask = subtasks[current_index]

    # Phase 3: Show depth and parent-child relationships
    depth = current_subtask.get("depth", 0)
    parent_id = current_subtask.get("parent_id", None)
    indent = "  " + "  " * depth  # Indent based on depth

    print(f"\n  ━━━ Subtask {current_index + 1}/{len(subtasks)} ━━━")
    print(f"  ID: {current_subtask['subtask_id']}")
    if parent_id:
        print(f"  Parent: {parent_id} (Depth: {depth})")
    else:
        print(f"  Depth: {depth} (Root)")
    print(f"  Description: {current_subtask['description']}")
    print(f"  Focus: {current_subtask['focus_area']}")
    print(f"  Priority: {current_subtask['priority']}")
    print(f"  Dependencies: {current_subtask.get('dependencies', [])}")
    print(f"  Importance: {current_subtask['estimated_importance']}")

    # Prepare subtask-specific query
    # The Strategic Planner will receive this focused query
    subtask_query = f"{current_subtask['description']}\n\nFocus Area: {current_subtask['focus_area']}"

    print(f"\n  Subtask Query for Strategic Planner:")
    print(f"  \"{subtask_query[:150]}...\"\n")

    return {
        "current_subtask_id": current_subtask["subtask_id"],
        "query": subtask_query,  # Override original query for this subtask
        "loop_count": 0,  # Reset loop counter for this subtask
        # Note: We don't clear search_results/rag_results here
        # because they use operator.add and will accumulate across subtasks
        # We'll handle per-subtask result isolation in the aggregator
    }
