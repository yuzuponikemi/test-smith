import argparse
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
from src.utils.logging_utils import setup_execution_logger, save_report, get_recent_reports, get_recent_logs
from src.utils.langfuse_config import get_langfuse_callback_handler, flush_langfuse, is_langfuse_enabled
import uuid

# Import new graph registry system
from src.graphs import get_graph, list_graphs, get_default_graph

# Keep backward compatibility - import old graph
try:
    from src.graph import graph as legacy_graph
except ImportError:
    legacy_graph = None

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Test-Smith v2.1 - Multi-Graph Research Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available graph workflows
  python main.py graphs

  # Run with default graph (deep_research)
  python main.py run "What is quantum computing?"

  # Run with specific graph
  python main.py run "Compare Python vs Go" --graph comparative
  python main.py run "Is the sky blue?" --graph fact_check
  python main.py run "Quick overview of Docker" --graph quick_research
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
                print(f"\n   Use Cases:")
                for use_case in metadata.get('use_cases', []):
                    print(f"   • {use_case}")

                if 'features' in metadata:
                    print(f"\n   Features:")
                    for feature in metadata['features']:
                        print(f"   • {feature}")

                if 'performance' in metadata:
                    perf = metadata['performance']
                    print(f"\n   Performance:")
                    for key, value in perf.items():
                        print(f"   • {key}: {value}")

            print()

        print("="*80)
        print(f"\nDefault graph: {get_default_graph()}")
        print("\nUsage: python main.py run \"your query\" --graph <graph_name>")
        print("="*80 + "\n")

    elif args.command == "run":
        # Select graph workflow
        graph_name = args.graph if args.graph else get_default_graph()

        try:
            builder = get_graph(graph_name)
            print(f"[System] Using graph workflow: {graph_name}")
            print(f"[System] Description: {builder.get_metadata().get('description', 'N/A')}\n")
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

            # Initialize Langfuse callback handler if enabled
            langfuse_handler = get_langfuse_callback_handler(
                session_id=thread_id,
                metadata={
                    "graph": graph_name,
                    "query": args.query
                }
            )

            # Build config with optional Langfuse callbacks
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 150  # Increased for Phase 4 dynamic replanning (default: 25, Phase 1-3: 100)
            }

            if langfuse_handler:
                config["callbacks"] = [langfuse_handler]

            # Setup logger if enabled
            logger = None if args.no_log else setup_execution_logger(args.query, thread_id)

            if logger:
                logger.log(f"Starting Test-Smith execution", "INFO")
                logger.log(f"Query: {args.query}")
                logger.log(f"Thread ID: {thread_id}")
                logger.log(f"Langfuse tracing: {'ENABLED' if langfuse_handler else 'DISABLED'}")
            else:
                print("Running the LangGraph agent...")
                if langfuse_handler:
                    print(f"[Langfuse] Tracing enabled - session: {thread_id}")

            # Track state for report saving
            final_state = {}
            inputs = {"query": args.query, "loop_count": 0}

            try:
                for output in app.stream(inputs, config=config):
                    for key, value in output.items():
                        # Log node execution
                        if logger:
                            logger.log_node_start(key)
                            logger.log_node_end(key, value)
                        else:
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

                    if logger:
                        logger.log(f"Report saved to: {report_path}")

                # Finalize logger
                if logger:
                    logger.finalize(final_state.get("report", ""))

                # Flush Langfuse traces
                if langfuse_handler:
                    if logger:
                        logger.log("Flushing Langfuse traces...")
                    else:
                        print("[Langfuse] Flushing traces...")
                    flush_langfuse()

            except Exception as e:
                if logger:
                    logger.log_error(e, "main execution loop")
                # Flush Langfuse traces even on error
                if langfuse_handler:
                    flush_langfuse()
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
