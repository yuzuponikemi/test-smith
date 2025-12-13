import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langgraph.errors import GraphRecursionError

load_dotenv()

from langgraph.checkpoint.sqlite import SqliteSaver

# Import new graph registry system (depends on MODEL_PROVIDER being set)
from src.config.research_depth import get_depth_config
from src.graphs import get_default_graph, get_graph, list_graphs
from src.utils.logging_utils import (
    get_recent_logs,
    get_recent_reports,
    save_report,
    setup_execution_logger,
)
from src.utils.streaming_output import StreamingFormatter


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
        """,
    )
    parser.add_argument("--version", action="version", version="%(prog)s 2.1")
    subparsers = parser.add_subparsers(dest="command")

    # Graphs command - list available workflows
    graphs_parser = subparsers.add_parser(
        "graphs",
        help="List all available graph workflows",
        description="Display all registered graph workflows with their descriptions and use cases",
    )
    graphs_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information including features and performance metrics",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the LangGraph agent")
    run_parser.add_argument("query", type=str, help="The query to send to the agent")
    run_parser.add_argument(
        "--graph",
        type=str,
        default=None,
        help=f"Graph workflow to use (default: {get_default_graph()}). Use 'python main.py graphs' to see available options.",
    )
    run_parser.add_argument(
        "--thread-id", type=str, help="The thread ID to use for the conversation"
    )
    run_parser.add_argument(
        "--no-log", action="store_true", help="Disable file logging (console only)"
    )
    run_parser.add_argument(
        "--no-report", action="store_true", help="Don't save final report to file"
    )
    run_parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming progressive output (real-time updates)",
    )
    run_parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output in streaming mode"
    )
    run_parser.add_argument(
        "--depth",
        type=str,
        choices=["quick", "standard", "deep", "comprehensive"],
        default="standard",
        help="Research depth level: quick (1-2 pages), standard (3-5 pages), deep (6-10 pages), comprehensive (10+ pages)",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List recent reports or logs")
    list_parser.add_argument("type", choices=["reports", "logs"], help="Type of files to list")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of files to show")
    list_parser.add_argument(
        "--mode", choices=["simple", "hierarchical"], help="Filter reports by execution mode"
    )

    args = parser.parse_args()

    if args.command == "graphs":
        # Display available graph workflows
        graphs = list_graphs()
        print("\n" + "=" * 80)
        print("AVAILABLE GRAPH WORKFLOWS")
        print("=" * 80 + "\n")

        for graph_name, metadata in graphs.items():
            print(f"📊 {graph_name}")
            print(f"   {metadata.get('description', 'No description')}")
            print(f"   Version: {metadata.get('version', 'N/A')}")
            print(f"   Complexity: {metadata.get('complexity', 'N/A')}")

            if args.detailed:
                print("\n   Use Cases:")
                for use_case in metadata.get("use_cases", []):
                    print(f"   • {use_case}")

                if "features" in metadata:
                    print("\n   Features:")
                    for feature in metadata["features"]:
                        print(f"   • {feature}")

                if "performance" in metadata:
                    perf = metadata["performance"]
                    print("\n   Performance:")
                    for key, value in perf.items():
                        print(f"   • {key}: {value}")

            print()

        print("=" * 80)
        print(f"\nDefault graph: {get_default_graph()}")
        print('\nUsage: python main.py run "your query" --graph <graph_name>')
        print("=" * 80 + "\n")

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
            print(f"[System] Research depth: {args.depth}")
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

            # Get depth-aware recursion limit
            depth_config = get_depth_config(args.depth)
            current_recursion_limit = depth_config.recursion_limit

            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": current_recursion_limit,
            }

            # Setup logger if enabled
            logger = None if args.no_log else setup_execution_logger(args.query, thread_id)

            # Setup streaming formatter if enabled
            streaming_formatter = None
            if args.stream:
                use_colors = not args.no_color
                streaming_formatter = StreamingFormatter(
                    graph_name=graph_name, use_colors=use_colors
                )

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
            inputs = {"query": args.query, "loop_count": 0, "research_depth": args.depth}

            # Execution loop with GraphRecursionError handling
            execution_complete = False
            while not execution_complete:
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

                            # Ensure value is a dictionary before accessing fields
                            if isinstance(value, dict):
                                # Track special nodes for metadata
                                if (
                                    key == "master_planner"
                                    and "master_plan" in value
                                    and logger
                                    and value.get("master_plan")
                                ):
                                    logger.log_master_plan(value["master_plan"])

                                if key == "planner" and "allocation_strategy" in value and logger:
                                    logger.log_queries(
                                        value.get("rag_queries", []),
                                        value.get("web_queries", []),
                                        value.get("allocation_strategy", ""),
                                    )

                                # Update final state
                                final_state.update(value)
                            else:
                                # Handle non-dict output (e.g. string errors or simple values)
                                if logger:
                                    logger.log(f"Received non-dict output from {key}: {value}", "WARNING")
                                elif not args.stream:
                                    print(f"[{key}] {value}")
                                    
                                # For simple string outputs, we might want to store them in final_state with the key
                                # But final_state expects to update with a dict. 
                                # We'll skip updating final_state for non-dict values to avoid crashing .update()
                                pass

                    # Execution completed successfully
                    execution_complete = True

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
                                metadata["complexity_reasoning"] = master_plan.get(
                                    "complexity_reasoning", ""
                                )

                        report_path = save_report(
                            final_state["report"], args.query, execution_mode, metadata
                        )

                    # Save causal graph data if available (for causal_inference graph)
                    if "causal_graph_data" in final_state and graph_name == "causal_inference":
                        # Create output directory if needed
                        Path("causal_graphs").mkdir(exist_ok=True)

                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        graph_file = Path("causal_graphs") / f"causal_graph_{timestamp}.json"

                        # Save graph data to JSON
                        with open(graph_file, "w") as f:
                            json.dump(final_state["causal_graph_data"], f, indent=2)

                        print(f"\n✓ Causal graph data saved to: {graph_file}")
                        print(f"  Visualize with: python visualize_causal_graph.py {graph_file}")

                        # Also save as causal_graph.json for easy access
                        latest_file = Path("causal_graphs") / "causal_graph.json"
                        with open(latest_file, "w") as f:
                            json.dump(final_state["causal_graph_data"], f, indent=2)
                        print(f"  Latest graph also saved to: {latest_file}\n")

                        if logger:
                            logger.log(f"Report saved to: {report_path}")

                    # Save research data if available (for deep_research graph)
                    if "aggregated_findings" in final_state and final_state["aggregated_findings"]:
                        # Create output directory if needed
                        research_data_dir = Path("research_data")
                        research_data_dir.mkdir(exist_ok=True)

                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        findings_file = research_data_dir / f"findings_{timestamp}.json"

                        # Prepare research data with additional context
                        research_data = {
                            "query": args.query,
                            "graph": graph_name,
                            "depth": args.depth,
                            "thread_id": thread_id,
                            "timestamp": timestamp,
                            "aggregated_findings": final_state["aggregated_findings"],
                        }

                        # Include report outline if available
                        if "report_outline" in final_state and final_state["report_outline"]:
                            research_data["report_outline"] = final_state["report_outline"]

                        # Include review result if available
                        if "review_result" in final_state and final_state["review_result"]:
                            research_data["review_result"] = final_state["review_result"]

                        # Save research data to JSON
                        with open(findings_file, "w", encoding="utf-8") as f:
                            json.dump(research_data, f, indent=2, ensure_ascii=False)

                        print(f"\n✓ Research data saved to: {findings_file}")

                        # Also save as latest.json for easy access
                        latest_file = research_data_dir / "latest.json"
                        with open(latest_file, "w", encoding="utf-8") as f:
                            json.dump(research_data, f, indent=2, ensure_ascii=False)
                        print(f"  Latest data also saved to: {latest_file}")

                        if logger:
                            logger.log(f"Research data saved to: {findings_file}")

                    # Finalize logger
                    if logger:
                        logger.finalize(final_state.get("report", ""))

                except GraphRecursionError:
                    # Handle recursion limit reached - ask user if they want to continue
                    print("\n" + "=" * 60)
                    print("⚠️  再帰制限に到達しました")
                    print(f"   現在の制限: {current_recursion_limit} ステップ")
                    print(f"   追加可能: +{depth_config.recursion_extension} ステップ")
                    print("=" * 60)

                    if logger:
                        logger.log(
                            f"GraphRecursionError: limit {current_recursion_limit} reached",
                            "WARNING",
                        )

                    # Ask user if they want to continue
                    user_input = input("\n調査を続行しますか？ (yes/no): ").strip().lower()

                    if user_input in ("yes", "y", "はい"):
                        # Extend the recursion limit and continue
                        current_recursion_limit += depth_config.recursion_extension
                        config["recursion_limit"] = current_recursion_limit
                        print(f"\n✓ 再帰制限を {current_recursion_limit} に拡張して続行します...\n")

                        if logger:
                            logger.log(
                                f"User extended recursion limit to {current_recursion_limit}",
                                "INFO",
                            )
                        # Continue the while loop to retry
                    else:
                        # User chose not to continue
                        print("\n調査を中断します。")
                        if logger:
                            logger.log("User chose not to continue after recursion limit", "INFO")

                        # Generate partial report if we have any data
                        if final_state.get("analyzed_data"):
                            print("収集済みのデータで部分的なレポートを生成します...\n")
                            # The synthesizer will use whatever data is available
                            execution_complete = True
                        else:
                            execution_complete = True
                            print("十分なデータが収集されていないため、レポートを生成できません。")

                except Exception as e:
                    if logger:
                        logger.log_error(e, "main execution loop")
                    raise

    elif args.command == "list":
        if args.type == "reports":
            reports = get_recent_reports(limit=args.limit, execution_mode=args.mode)
            print(f"\nRecent Reports ({len(reports)}):")
            print("=" * 80)
            for i, report in enumerate(reports, 1):
                size_kb = report.stat().st_size / 1024
                mtime = report.stat().st_mtime
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i:2}. {report.name}")
                print(f"    Size: {size_kb:.1f} KB | Modified: {mtime_str}")
                print(f"    Path: {report}")
                print()

        elif args.type == "logs":
            logs = get_recent_logs(limit=args.limit)
            print(f"\nRecent Execution Logs ({len(logs)}):")
            print("=" * 80)
            for i, log in enumerate(logs, 1):
                size_kb = log.stat().st_size / 1024
                mtime = log.stat().st_mtime
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i:2}. {log.name}")
                print(f"    Size: {size_kb:.1f} KB | Modified: {mtime_str}")
                print(f"    Path: {log}")
                print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
