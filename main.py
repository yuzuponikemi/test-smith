import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langgraph.checkpoint.sqlite import SqliteSaver

# Import new graph registry system (depends on MODEL_PROVIDER being set)
from src.graphs import get_default_graph, get_graph, list_graphs
from src.utils.logging_utils import (
    get_recent_logs,
    get_recent_reports,
    save_report,
    setup_execution_logger,
)
from src.utils.streaming_output import StreamingFormatter

# Keep backward compatibility - import old graph
try:
    from src.graph import graph as legacy_graph
except ImportError:
    legacy_graph = None

def main():
    # Note: load_dotenv() is called at module import time (top of file)
    parser = argparse.ArgumentParser(
        description="Test-Smith v2.1 - Multi-Graph Research Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available graph workflows
  python main.py graphs

  # Run with default graph (deep_research)
  python main.py run "What is quantum computing?"

  # Run with streaming output (real-time progress updates)
  python main.py run "What is quantum computing?" --stream

  # Run with specific graph
  python main.py run "Compare Python vs Go" --graph comparative
  python main.py run "Is the sky blue?" --graph fact_check
  python main.py run "Quick overview of Docker" --graph quick_research

  # Combine streaming with specific graph
  python main.py run "Why is my app slow?" --graph causal_inference --stream
        """
    )
    parser.add_argument("--version", action="version", version="%(prog)s 2.1")
    subparsers = parser.add_subparsers(dest="command")

    # Graphs command - list available workflows
    graphs_parser = subparsers.add_parser(
        "graphs",
        help="List all available graph workflows",
        description="Display all registered graph workflows with their descriptions and use cases"
    )
    graphs_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information including features and performance metrics"
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the LangGraph agent")
    run_parser.add_argument("query", type=str, help="The query to send to the agent")
    run_parser.add_argument(
        "--graph",
        type=str,
        default=None,
        help=f"Graph workflow to use (default: {get_default_graph()}). Use 'python main.py graphs' to see available options."
    )
    run_parser.add_argument("--thread-id", type=str, help="The thread ID to use for the conversation")
    run_parser.add_argument("--no-log", action="store_true", help="Disable file logging (console only)")
    run_parser.add_argument("--no-report", action="store_true", help="Don't save final report to file")
    run_parser.add_argument("--stream", action="store_true", help="Enable streaming progressive output (real-time updates)")
    run_parser.add_argument("--no-color", action="store_true", help="Disable colored output in streaming mode")

    # List command
    list_parser = subparsers.add_parser("list", help="List recent reports or logs")
    list_parser.add_argument("type", choices=["reports", "logs"], help="Type of files to list")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of files to show")
    list_parser.add_argument("--mode", choices=["simple", "hierarchical"], help="Filter reports by execution mode")

    args = parser.parse_args()

    if args.command == "graphs":
        # Display available graph workflows
        graphs = list_graphs()
        print("\n" + "="*80)
        print("AVAILABLE GRAPH WORKFLOWS")
        print("="*80 + "\n")

        for graph_name, metadata in graphs.items():
            print(f"📊 {graph_name}")
            print(f"   {metadata.get('description', 'No description')}")
            print(f"   Version: {metadata.get('version', 'N/A')}")
            print(f"   Complexity: {metadata.get('complexity', 'N/A')}")

            if args.detailed:
                print("\n   Use Cases:")
                for use_case in metadata.get('use_cases', []):
                    print(f"   • {use_case}")

                if 'features' in metadata:
                    print("\n   Features:")
                    for feature in metadata['features']:
                        print(f"   • {feature}")

                if 'performance' in metadata:
                    perf = metadata['performance']
                    print("\n   Performance:")
                    for key, value in perf.items():
                        print(f"   • {key}: {value}")

            print()

        print("="*80)
        print(f"\nDefault graph: {get_default_graph()}")
        print("\nUsage: python main.py run \"your query\" --graph <graph_name>")
        print("="*80 + "\n")

    elif args.command == "run":
        # Select graph workflow (auto-select if not specified)
        if args.graph:
            # User explicitly specified graph
            graph_name = args.graph
            selection_mode = "manual"
        else:
            # Auto-select based on query (MCP-aligned: load only necessary graph)
            from src.utils.graph_selector import auto_select_graph, explain_selection
            graph_name = auto_select_graph(args.query)
            selection_mode = "auto"

        try:
            builder = get_graph(graph_name)
            print(f"[System] Using graph workflow: {graph_name} ({selection_mode})")
            print(f"[System] Description: {builder.get_metadata().get('description', 'N/A')}")

            # Show selection reasoning if auto-selected
            if selection_mode == "auto" and not args.no_log:
                from src.utils.graph_selector import explain_selection
                print("\n[Auto-Selection Reasoning]")
                print(explain_selection(args.query, graph_name))
            print()
        except KeyError as e:
            print(f"Error: {e}")
            print(f"\nAvailable graphs: {', '.join(list_graphs().keys())}")
            print("Use 'python main.py graphs' for detailed information")
            return

        with SqliteSaver.from_conn_string(":memory:") as memory:
            # Get uncompiled graph and compile with checkpointer
            uncompiled_graph = builder.get_uncompiled_graph()
            app = uncompiled_graph.compile(checkpointer=memory)
            thread_id = args.thread_id if args.thread_id else str(uuid.uuid4())
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 150  # Increased for Phase 4 dynamic replanning (default: 25, Phase 1-3: 100)
            }

            # Setup logger if enabled
            logger = None if args.no_log else setup_execution_logger(args.query, thread_id)

            # Setup streaming formatter if enabled
            streaming_formatter = None
            if args.stream:
                use_colors = not args.no_color
                streaming_formatter = StreamingFormatter(graph_name=graph_name, use_colors=use_colors)

            if logger:
                logger.log("Starting Test-Smith execution", "INFO")
                logger.log(f"Query: {args.query}")
                logger.log(f"Thread ID: {thread_id}")
                if args.stream:
                    logger.log("Streaming mode enabled", "INFO")
            elif not args.stream:
                print("Running the LangGraph agent...")

            # Track state for report saving
            final_state = {}
            inputs = {"query": args.query, "loop_count": 0}

            try:
                for output in app.stream(inputs, config=config):
                    for key, value in output.items():
                        # Streaming output (real-time progressive updates)
                        if streaming_formatter:
                            streaming_formatter.process_node_output(key, value)

                        # Log node execution (file logging)
                        if logger:
                            logger.log_node_start(key)
                            logger.log_node_end(key, value)
                        elif not args.stream:
                            # Default verbose output (only if not streaming)
                            print(f"Output from node '{key}':")
                            print("---")
                            print(value)
                            print("\n---\n")

                        # Track special nodes for metadata
                        if key == "master_planner" and "master_plan" in value:
                            if logger and value.get("master_plan"):
                                logger.log_master_plan(value["master_plan"])

                        if key == "planner" and "allocation_strategy" in value:
                            if logger:
                                logger.log_queries(
                                    value.get("rag_queries", []),
                                    value.get("web_queries", []),
                                    value.get("allocation_strategy", "")
                                )

                        # Update final state
                        final_state.update(value)

                # Finalize streaming output
                if streaming_formatter:
                    streaming_formatter.finalize()

                # Save final report if available
                if "report" in final_state and not args.no_report:
                    execution_mode = final_state.get("execution_mode", "simple")
                    metadata = {
                        "thread_id": thread_id,
                    }

                    # Add hierarchical metadata if available
                    if execution_mode == "hierarchical" and "master_plan" in final_state:
                        master_plan = final_state["master_plan"]
                        if master_plan:
                            metadata["subtask_count"] = len(master_plan.get("subtasks", []))
                            metadata["complexity_reasoning"] = master_plan.get("complexity_reasoning", "")

                    report_path = save_report(
                        final_state["report"],
                        args.query,
                        execution_mode,
                        metadata
                    )

                # Save causal graph data if available (for causal_inference graph)
                if "causal_graph_data" in final_state and graph_name == "causal_inference":
                    # Create output directory if needed
                    Path("causal_graphs").mkdir(exist_ok=True)

                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    graph_file = Path("causal_graphs") / f"causal_graph_{timestamp}.json"

                    # Save graph data to JSON
                    with open(graph_file, 'w') as f:
                        json.dump(final_state["causal_graph_data"], f, indent=2)

                    print(f"\n✓ Causal graph data saved to: {graph_file}")
                    print(f"  Visualize with: python visualize_causal_graph.py {graph_file}")

                    # Also save as causal_graph.json for easy access
                    latest_file = Path("causal_graphs") / "causal_graph.json"
                    with open(latest_file, 'w') as f:
                        json.dump(final_state["causal_graph_data"], f, indent=2)
                    print(f"  Latest graph also saved to: {latest_file}\n")

                    if logger:
                        logger.log(f"Report saved to: {report_path}")

                # Finalize logger
                if logger:
                    logger.finalize(final_state.get("report", ""))

            except Exception as e:
                if logger:
                    logger.log_error(e, "main execution loop")
                raise

    elif args.command == "list":
        if args.type == "reports":
            reports = get_recent_reports(limit=args.limit, execution_mode=args.mode)
            print(f"\nRecent Reports ({len(reports)}):")
            print("="*80)
            for i, report in enumerate(reports, 1):
                size_kb = report.stat().st_size / 1024
                mtime = report.stat().st_mtime
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i:2}. {report.name}")
                print(f"    Size: {size_kb:.1f} KB | Modified: {mtime_str}")
                print(f"    Path: {report}")
                print()

        elif args.type == "logs":
            logs = get_recent_logs(limit=args.limit)
            print(f"\nRecent Execution Logs ({len(logs)}):")
            print("="*80)
            for i, log in enumerate(logs, 1):
                size_kb = log.stat().st_size / 1024
                mtime = log.stat().st_mtime
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i:2}. {log.name}")
                print(f"    Size: {size_kb:.1f} KB | Modified: {mtime_str}")
                print(f"    Path: {log}")
                print()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
