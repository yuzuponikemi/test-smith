def save_subtask_result(state):
    """
    Saves current subtask result before moving to next subtask

    Stores analyzed_data under subtask_id in subtask_results dict.
    This allows the synthesizer to access individual subtask results
    rather than a merged accumulation.
    """
    print("---SAVE SUBTASK RESULT---")

    current_subtask_id = state.get("current_subtask_id")
    analyzed_data = state.get("analyzed_data", [])
    subtask_results = dict(state.get("subtask_results", {}))  # Create copy to avoid mutation

    if not current_subtask_id:
        print("  ⚠ Warning: No current_subtask_id, skipping save")
        return {}

    # Get the most recent analyzed_data entry (for this subtask)
    # Note: analyzed_data accumulates across subtasks due to operator.add
    # We want only the latest entry which belongs to current subtask
    if analyzed_data:
        latest_analysis = analyzed_data[-1]
        subtask_results[current_subtask_id] = latest_analysis
        print(f"  ✓ Saved results for subtask: {current_subtask_id}")
        print(f"    Analysis length: {len(latest_analysis)} characters")
    else:
        print(f"  ⚠ Warning: No analyzed data for subtask {current_subtask_id}")
        subtask_results[current_subtask_id] = "No analysis generated for this subtask."

    # Increment subtask index for next iteration
    current_index = state.get("current_subtask_index", 0)
    new_index = current_index + 1

    print(f"  Moving to subtask index: {new_index}\n")

    return {
        "subtask_results": subtask_results,
        "current_subtask_index": new_index,
        "current_subtask_id": ""  # Clear for next subtask
    }
