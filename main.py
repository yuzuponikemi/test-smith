import argparse
from dotenv import load_dotenv
from src.graph import graph  # Import uncompiled StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from src.utils.logging_utils import setup_execution_logger, save_report, get_recent_reports, get_recent_logs
import uuid

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Test-Smith v2.0-alpha - Hierarchical Research Agent")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0-alpha")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the LangGraph agent")
    run_parser.add_argument("query", type=str, help="The query to send to the agent")
    run_parser.add_argument("--thread-id", type=str, help="The thread ID to use for the conversation")
    run_parser.add_argument("--no-log", action="store_true", help="Disable file logging (console only)")
    run_parser.add_argument("--no-report", action="store_true", help="Don't save final report to file")

    # List command
    list_parser = subparsers.add_parser("list", help="List recent reports or logs")
    list_parser.add_argument("type", choices=["reports", "logs"], help="Type of files to list")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of files to show")
    list_parser.add_argument("--mode", choices=["simple", "hierarchical"], help="Filter reports by execution mode")

    args = parser.parse_args()

    if args.command == "run":
        with SqliteSaver.from_conn_string(":memory:") as memory:
            app = graph.compile(checkpointer=memory)
            thread_id = args.thread_id if args.thread_id else str(uuid.uuid4())
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 150  # Increased for Phase 4 dynamic replanning (default: 25, Phase 1-3: 100)
            }

            # Setup logger if enabled
            logger = None if args.no_log else setup_execution_logger(args.query, thread_id)

            if logger:
                logger.log(f"Starting Test-Smith execution", "INFO")
                logger.log(f"Query: {args.query}")
                logger.log(f"Thread ID: {thread_id}")
            else:
                print("Running the LangGraph agent...")

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
