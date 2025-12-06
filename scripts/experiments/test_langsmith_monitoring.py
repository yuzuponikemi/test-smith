"""
LangSmith Monitoring Test - Phase 4.1 Budget Controls

This test is designed for easy LangSmith Studio v2 monitoring.
Watch budget controls in action!
"""

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

from src.graphs import get_graph

load_dotenv()

# Get deep_research graph builder
_graph_builder = get_graph("deep_research")


def test_with_langsmith_monitoring():
    """
    Simple test query for LangSmith monitoring.

    Watch in LangSmith Studio v2:
    - Budget status updates
    - Adaptive control decisions
    - Drill-down and revision limiting
    """

    # Simple but interesting query that will trigger hierarchical mode
    test_query = """
    Compare the architectural approaches of LangGraph and AutoGPT.
    Include their coordination mechanisms and use cases.
    """

    print("=" * 80)
    print("🔍 LANGSMITH MONITORING TEST - Phase 4.1 Budget Controls")
    print("=" * 80)
    print(f"\n📝 Query: {test_query}\n")
    print("=" * 80)
    print("\n👀 WATCH THIS IN LANGSMITH STUDIO V2:")
    print("   https://smith.langchain.com/")
    print("   Project: deep-research-v1-proto")
    print("\n🎯 Look for:")
    print("   • Budget status messages (🟢🟠🟡🔴)")
    print("   • Drill-down decisions")
    print("   • Plan revision decisions")
    print("   • node_execution_count in state")
    print("=" * 80)

    with SqliteSaver.from_conn_string(":memory:") as memory:
        app = _graph_builder.build(checkpointer=memory)

        config = {
            "configurable": {"thread_id": "langsmith-monitoring-test"},
            "recursion_limit": 150,
        }

        print("\n🚀 Starting execution...\n")
        print("=" * 80)

        result = None
        for event in app.stream({"query": test_query}, config=config, stream_mode="values"):
            result = event

        print("\n" + "=" * 80)
        print("✅ EXECUTION COMPLETE")
        print("=" * 80)

        if result:
            execution_mode = result.get("execution_mode", "unknown")
            print("\n📊 Summary:")
            print(f"   Execution Mode: {execution_mode}")

            if execution_mode == "hierarchical":
                print(
                    f"   Total Subtasks: {len(result.get('master_plan', {}).get('subtasks', []))}"
                )
                print(f"   Revisions Made: {result.get('revision_count', 0)}")
                print(
                    f"   Node Executions: {result.get('node_execution_count', 0)}/{result.get('recursion_limit', 150)}"
                )
                print(
                    f"   Budget Usage: {(result.get('node_execution_count', 0) / result.get('recursion_limit', 150) * 100):.1f}%"
                )

            print("\n🎉 Check LangSmith for detailed trace visualization!")
            print("   https://smith.langchain.com/")


if __name__ == "__main__":
    test_with_langsmith_monitoring()
