"""
Test Phase 4: Dynamic Replanning

This test verifies that the plan revisor can detect important discoveries
and adaptively add new subtasks to the master plan.

Expected Behavior:
1. Master Planner creates initial plan
2. Subtasks execute
3. If important discoveries are made, Plan Revisor adds new subtasks
4. Execution continues with updated plan
5. Final report includes insights from both original and added subtasks
"""

import os

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

from src.graphs import get_graph

load_dotenv()

# Get deep_research graph builder
_graph_builder = get_graph("deep_research")


def test_dynamic_replanning():
    """
    Test adaptive research with a query that should trigger plan revision.

    Query focuses on a topic where discoveries during research should reveal
    important related topics not in the original plan.
    """

    # This query is complex and will likely discover important related topics
    # during execution that warrant adding new subtasks
    test_query = """
    Analyze the history and evolution of multi-agent AI systems, focusing on
    the architectural patterns and coordination mechanisms used in systems like
    AutoGPT, LangGraph, and similar frameworks. Provide a comprehensive overview.
    """

    print("=" * 80)
    print("PHASE 4 TEST: Dynamic Replanning")
    print("=" * 80)
    print(f"\nQuery: {test_query}\n")
    print("=" * 80)

    # Set up checkpointing
    with SqliteSaver.from_conn_string(":memory:") as memory:
        app = _graph_builder.build(checkpointer=memory)

        # Configure for test with higher recursion limit for dynamic replanning
        config = {
            "configurable": {"thread_id": "test-phase4-dynamic-replanning"},
            "recursion_limit": 150,  # Higher limit needed for dynamic replanning
        }

        print("\n🚀 Starting execution with dynamic replanning enabled...")
        print("=" * 80)

        # Run the graph
        result = None
        for event in app.stream({"query": test_query}, config=config, stream_mode="values"):
            result = event

        print("\n" + "=" * 80)
        print("EXECUTION COMPLETE")
        print("=" * 80)

        # Analyze results
        if result:
            print("\n📊 PHASE 4 ANALYSIS")
            print("=" * 80)

            execution_mode = result.get("execution_mode", "unknown")
            print(f"Execution Mode: {execution_mode}")

            if execution_mode == "hierarchical":
                master_plan = result.get("master_plan", {})
                initial_subtasks = len(master_plan.get("subtasks", []))
                print(f"Total Subtasks (including revisions): {initial_subtasks}")

                revision_count = result.get("revision_count", 0)
                print(f"Plan Revisions Made: {revision_count}")

                if revision_count > 0:
                    print("\n✅ PHASE 4 SUCCESS: Plan was revised during execution!")
                    print("\nRevision History:")
                    plan_revisions = result.get("plan_revisions", [])
                    for i, rev in enumerate(plan_revisions, 1):
                        print(f"\n  Revision {i}:")
                        print(f"    Trigger: {rev.get('trigger_type', 'unknown')}")
                        print(f"    Reasoning: {rev.get('revision_reasoning', 'N/A')[:200]}...")
                        print(f"    New Subtasks Added: {len(rev.get('new_subtasks', []))}")
                        for new_st in rev.get("new_subtasks", []):
                            print(
                                f"      + {new_st.get('subtask_id', 'unknown')}: {new_st.get('description', 'N/A')[:80]}..."
                            )
                        print(f"    Impact: {rev.get('estimated_impact', 'N/A')[:150]}...")

                    revision_triggers = result.get("revision_triggers", [])
                    print(f"\n  Trigger Types: {', '.join(revision_triggers)}")

                else:
                    print("\n⚠️  No plan revisions were made")
                    print("    This could mean:")
                    print("    - Discoveries were within expected scope")
                    print("    - Existing subtasks already covered related areas")
                    print("    - No high-importance discoveries warranted revision")

                print("\n📈 Subtask Execution:")
                subtask_results = result.get("subtask_results", {})
                print(f"  Completed Subtasks: {len(subtask_results)}")

                print("\n📄 Final Report Length:", len(result.get("report", "")), "characters")

            else:
                print("\n⚠️  Query was treated as SIMPLE, not COMPLEX")
                print("    Dynamic replanning only works in hierarchical mode")

            print("\n" + "=" * 80)

            # Save report if generated
            if "report" in result:
                report = result["report"]
                output_file = "reports/test_phase4_dynamic_replanning.md"

                os.makedirs("reports", exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("# Phase 4 Test: Dynamic Replanning\n\n")
                    f.write(f"**Query:** {test_query}\n\n")
                    f.write(f"**Execution Mode:** {execution_mode}\n")
                    if execution_mode == "hierarchical":
                        f.write(f"**Revisions Made:** {revision_count}\n")
                        f.write(f"**Total Subtasks:** {initial_subtasks}\n")
                    f.write("\n---\n\n")
                    f.write(report)

                print(f"Report saved to: {output_file}")

        else:
            print("\n❌ ERROR: No result returned from graph execution")


if __name__ == "__main__":
    test_dynamic_replanning()
