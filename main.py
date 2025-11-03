import argparse
from dotenv import load_dotenv
from src.graph import workflow
from langgraph.checkpoint.sqlite import SqliteSaver
import uuid

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="LangChain 1.0 Monitoring Prototype")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the LangGraph agent")
    run_parser.add_argument("query", type=str, help="The query to send to the agent")
    run_parser.add_argument("--thread-id", type=str, help="The thread ID to use for the conversation")

    args = parser.parse_args()

    if args.command == "run":
        with SqliteSaver.from_conn_string(":memory:") as memory:
            app = workflow.compile(checkpointer=memory)
            thread_id = args.thread_id if args.thread_id else str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            print("Running the LangGraph agent...")
            inputs = {"query": args.query, "loop_count": 0}
            for output in app.stream(inputs, config=config):
                for key, value in output.items():
                    print(f"Output from node '{key}':")
                    print("---")
                    print(value)
                print("\n---\n")

if __name__ == "__main__":
    main()
