"""
Simulate LangGraph Studio execution trace visualization

This script runs the code_execution graph and displays
the execution trace in a Studio-like format.
"""

from datetime import datetime

from src.studio_graphs import code_execution


def simulate_studio_execution(query: str):
    """Run graph and display Studio-like trace"""

    print("\n" + "=" * 80)
    print("🎬 LangGraph Studio - Execution Trace")
    print("=" * 80)
    print(f"\n📝 Query: {query}")
    print("🔧 Graph: code_execution")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-" * 80)

    # Initial state
    config = {"configurable": {"thread_id": "studio_demo"}}
    inputs = {"query": query, "loop_count": 0}

    print("\n📊 Execution Flow:\n")

    node_count = 0
    for step in code_execution.stream(inputs, config=config):
        node_count += 1

        for node_name, node_output in step.items():
            print(f"\n[{node_count}] Node: {node_name}")
            print("-" * 40)

            # Display key outputs
            if "rag_queries" in node_output:
                print(f"  RAG Queries: {node_output['rag_queries']}")
            if "web_queries" in node_output:
                print(f"  Web Queries: {node_output['web_queries']}")
            if "allocation_strategy" in node_output:
                strategy = node_output["allocation_strategy"]
                print(f"  Strategy: {strategy[:100]}...")
            if "analyzed_data" in node_output:
                print(f"  Analyzed: {len(node_output['analyzed_data'])} items")
            if "code_execution_results" in node_output:
                results = node_output["code_execution_results"]
                if results:
                    result = results[0]
                    print("  Code Execution:")
                    print(f"    Success: {result.get('success', False)}")
                    print(f"    Output: {result.get('output', '')[:100]}...")
                    print(f"    Mode: {result.get('execution_mode', 'unknown')}")
                    print(f"    Time: {result.get('execution_time', 0):.2f}s")
            if "evaluation" in node_output:
                print(f"  Evaluation: {node_output['evaluation'][:100]}...")
            if "report" in node_output:
                print(f"  Report Generated: {len(node_output['report'])} chars")

            print()

    print("=" * 80)
    print(f"✅ Execution completed - {node_count} nodes executed")
    print("=" * 80)
    print("\n💡 In LangGraph Studio, you would see:")
    print("  • Interactive graph visualization")
    print("  • Step-by-step execution with state changes")
    print("  • Ability to inspect each node's input/output")
    print("  • Time-travel debugging")
    print("  • State modification and replay")
    print("\n")


if __name__ == "__main__":
    # Test query
    query = "Calculate the average of 15, 25, 35, and 45"

    try:
        simulate_studio_execution(query)
    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
