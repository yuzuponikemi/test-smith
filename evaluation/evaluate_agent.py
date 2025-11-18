"""
Test-Smith Agent Evaluation Runner

This script orchestrates comprehensive evaluation of the research agent system
using LangSmith's evaluation framework.

Features:
- Load test datasets from JSON
- Run experiments with different graph configurations
- Apply custom evaluators (heuristic + LLM-as-judge)
- Upload results to LangSmith for analysis
- Generate local summary reports

Usage:
    # Evaluate default graph with full dataset
    python evaluate_agent.py

    # Evaluate specific graph
    python evaluate_agent.py --graph quick_research

    # Evaluate with subset of test cases
    python evaluate_agent.py --limit 5 --category factual_lookup

    # Compare multiple graphs
    python evaluate_agent.py --compare quick_research deep_research

    # Dry run (no LangSmith upload)
    python evaluate_agent.py --dry-run
"""

import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

# IMPORTANT: Load .env BEFORE any imports that read environment variables
from dotenv import load_dotenv
load_dotenv()

from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_core.runnables import RunnableLambda

# Import graph system (these depend on MODEL_PROVIDER being set)
from src.graphs import get_graph, list_graphs, get_default_graph
from langgraph.checkpoint.sqlite import SqliteSaver

# Import evaluators
from evaluation.evaluators import (
    ALL_EVALUATORS,
    get_evaluators_for_example,
    HEURISTIC_EVALUATORS,
    LLM_EVALUATORS
)


# ============================================================================
# DATASET MANAGEMENT
# ============================================================================

def load_dataset(dataset_path: str = "evaluation/datasets/research_test_cases.json") -> Dict:
    """Load test dataset from JSON file."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with open(path, 'r') as f:
        return json.load(f)


def filter_examples(
    dataset: Dict,
    category: Optional[str] = None,
    complexity: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Filter test examples based on criteria.

    Args:
        dataset: Full dataset dictionary
        category: Filter by category (e.g., "factual_lookup")
        complexity: Filter by complexity (e.g., "high")
        limit: Maximum number of examples to return

    Returns:
        Filtered list of examples
    """
    examples = dataset.get("examples", [])

    if category:
        examples = [ex for ex in examples if ex.get("category") == category]

    if complexity:
        examples = [ex for ex in examples if ex.get("complexity") == complexity]

    if limit:
        examples = examples[:limit]

    return examples


def upload_dataset_to_langsmith(
    client: Client,
    dataset: Dict,
    examples: List[Dict],
    dataset_name: Optional[str] = None
) -> str:
    """
    Upload dataset to LangSmith.

    Args:
        client: LangSmith client
        dataset: Dataset metadata
        examples: Filtered examples to upload
        dataset_name: Override dataset name

    Returns:
        Dataset name in LangSmith
    """
    name = dataset_name or dataset.get("dataset_name", "research_agent_eval")
    description = dataset.get("description", "Research agent evaluation dataset")

    # Check if dataset exists
    try:
        existing_dataset = client.read_dataset(dataset_name=name)
        print(f"✓ Dataset '{name}' already exists in LangSmith")
        return name
    except:
        pass

    # Create new dataset
    print(f"Creating dataset '{name}' in LangSmith...")

    # Convert examples to LangSmith format
    langsmith_examples = []
    for ex in examples:
        langsmith_examples.append({
            "inputs": {
                "query": ex["input"],
                "metadata": ex.get("metadata", {}),
                "category": ex.get("category"),
                "complexity": ex.get("complexity")
            },
            "outputs": {
                "reference_output": ex.get("reference_output", ""),
                "expected_graph": ex.get("expected_graph"),
                "evaluation_criteria": ex.get("evaluation_criteria", {})
            }
        })

    # Create dataset
    dataset_obj = client.create_dataset(
        dataset_name=name,
        description=description
    )

    # Add examples
    for ex in langsmith_examples:
        client.create_example(
            dataset_id=dataset_obj.id,
            inputs=ex["inputs"],
            outputs=ex["outputs"]
        )

    print(f"✓ Uploaded {len(langsmith_examples)} examples to LangSmith")
    return name


# ============================================================================
# AGENT WRAPPER FOR EVALUATION
# ============================================================================

def create_agent_wrapper(graph_name: str):
    """
    Create a runnable wrapper for the agent that works with LangSmith evaluate().

    Args:
        graph_name: Name of graph to use (e.g., "quick_research")

    Returns:
        Runnable that takes inputs and returns outputs
    """
    builder = get_graph(graph_name)

    def run_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with given inputs and return outputs.

        Args:
            inputs: Dict with 'query' and optional 'metadata'

        Returns:
            Dict with 'report' and other state fields
        """
        query = inputs.get("query", "")
        metadata = inputs.get("metadata", {})

        # Build and configure graph
        with SqliteSaver.from_conn_string(":memory:") as memory:
            uncompiled_graph = builder.get_uncompiled_graph()
            app = uncompiled_graph.compile(checkpointer=memory)

            config = {
                "configurable": {"thread_id": f"eval-{time.time()}"},
                "recursion_limit": 150
            }

            # Run the graph
            start_time = time.time()
            final_state = {}

            try:
                for output in app.stream({"query": query, "loop_count": 0}, config=config):
                    for key, value in output.items():
                        final_state.update(value)

                execution_time = time.time() - start_time

                # Add metadata to output
                final_state["execution_time"] = execution_time
                final_state["graph_type"] = graph_name

                return final_state

            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    "report": "",
                    "error": str(e),
                    "execution_time": execution_time,
                    "graph_type": graph_name
                }

    return RunnableLambda(run_agent)


# ============================================================================
# EVALUATION EXECUTION
# ============================================================================

def run_evaluation(
    graph_name: str,
    dataset_name: str,
    examples: List[Dict],
    evaluators: List,
    experiment_name: Optional[str] = None,
    dry_run: bool = False,
    max_concurrency: int = 1
) -> Any:
    """
    Run evaluation experiment.

    Args:
        graph_name: Graph to evaluate
        dataset_name: Dataset name in LangSmith
        examples: Test examples (used for evaluator selection)
        evaluators: List of evaluator functions
        experiment_name: Optional experiment name
        dry_run: If True, don't upload to LangSmith
        max_concurrency: Number of parallel test executions (default: 1)

    Returns:
        Evaluation results
    """
    if not experiment_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"{graph_name}_eval_{timestamp}"

    print(f"\n{'='*80}")
    print(f"Running Evaluation: {experiment_name}")
    print(f"{'='*80}")
    print(f"Graph: {graph_name}")
    print(f"Dataset: {dataset_name}")
    print(f"Examples: {len(examples)}")
    print(f"Evaluators: {len(evaluators)}")
    print(f"Dry Run: {dry_run}")
    print(f"{'='*80}\n")

    # Create agent wrapper
    agent = create_agent_wrapper(graph_name)

    # Run evaluation
    if dry_run:
        print("DRY RUN: Skipping LangSmith upload")
        # Run locally without LangSmith
        results = []
        for i, example in enumerate(examples[:3], 1):  # Limit to 3 in dry run
            print(f"\nRunning example {i}/{min(3, len(examples))}: {example['id']}")
            query = example["input"]

            # Run agent
            output = agent.invoke({"query": query, "metadata": example.get("metadata", {})})

            # Create mock run and example objects
            class MockRun:
                def __init__(self, outputs):
                    self.outputs = outputs
                    self.error = outputs.get("error")

            class MockExample:
                def __init__(self, ex):
                    self.inputs = {
                        "input": ex["input"],
                        "metadata": ex.get("metadata", {}),
                        "category": ex.get("category"),
                        "complexity": ex.get("complexity")
                    }
                    self.outputs = {
                        "reference_output": ex.get("reference_output", "")
                    }

            mock_run = MockRun(output)
            mock_example = MockExample(example)

            # Run evaluators
            eval_results = {}
            for evaluator in evaluators:
                result = evaluator(mock_run, mock_example)
                if result:
                    eval_results[result["key"]] = result

            print(f"  Query: {query[:100]}...")
            print(f"  Output length: {len(output.get('report', ''))} chars")
            print(f"  Execution time: {output.get('execution_time', 0):.1f}s")
            print(f"  Evaluations: {len(eval_results)}")
            for key, result in eval_results.items():
                score = result.get("score")
                comment = result.get("comment", "")[:100]
                print(f"    {key}: {score} - {comment}")

            results.append({
                "example": example,
                "output": output,
                "evaluations": eval_results
            })

        return results

    else:
        # Use LangSmith evaluate()
        return evaluate(
            agent,
            data=dataset_name,
            evaluators=evaluators,
            experiment_prefix=experiment_name,
            max_concurrency=max_concurrency,
        )


def generate_summary_report(results: Any, output_path: str = "evaluation/results"):
    """
    Generate a summary report from evaluation results.

    Args:
        results: Evaluation results from LangSmith
        output_path: Directory to save report
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"eval_summary_{timestamp}.txt"

    with open(report_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("TEST-SMITH EVALUATION SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Results: {results}\n\n")

        # Add more detailed formatting based on results structure
        # This will be populated with actual LangSmith results

    print(f"\n✓ Summary report saved: {report_file}")


# ============================================================================
# COMPARATIVE EVALUATION
# ============================================================================

def compare_graphs(
    graph_names: List[str],
    dataset_name: str,
    examples: List[Dict],
    evaluators: List,
    max_concurrency: int = 1
):
    """
    Run comparative evaluation across multiple graphs.

    Args:
        graph_names: List of graph names to compare
        dataset_name: Dataset name
        examples: Test examples
        evaluators: Evaluator functions
        max_concurrency: Number of parallel test executions (default: 1)
    """
    print(f"\n{'='*80}")
    print(f"COMPARATIVE EVALUATION: {', '.join(graph_names)}")
    print(f"{'='*80}\n")

    results = {}
    for graph_name in graph_names:
        print(f"\nEvaluating {graph_name}...")
        result = run_evaluation(
            graph_name=graph_name,
            dataset_name=dataset_name,
            examples=examples,
            evaluators=evaluators,
            experiment_name=f"compare_{graph_name}",
            max_concurrency=max_concurrency
        )
        results[graph_name] = result

    # Generate comparison report
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    for graph_name, result in results.items():
        print(f"\n{graph_name}:")
        print(f"  Status: {result}")

    return results


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    # Note: load_dotenv() is called at module import time (top of file)
    # to ensure environment variables are available before any model imports

    parser = argparse.ArgumentParser(
        description="Evaluate Test-Smith research agent using LangSmith",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full evaluation with all test cases
  python evaluate_agent.py

  # Evaluate specific graph
  python evaluate_agent.py --graph quick_research

  # Test specific category
  python evaluate_agent.py --category factual_lookup --limit 5

  # Compare graphs
  python evaluate_agent.py --compare quick_research deep_research

  # Dry run (local only, no LangSmith)
  python evaluate_agent.py --dry-run --limit 3
        """
    )

    parser.add_argument(
        "--graph",
        type=str,
        default=None,
        help="Graph to evaluate (default: deep_research)"
    )

    parser.add_argument(
        "--compare",
        nargs="+",
        help="Compare multiple graphs (space-separated)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="evaluation/datasets/research_test_cases.json",
        help="Path to test dataset JSON"
    )

    parser.add_argument(
        "--category",
        type=str,
        help="Filter by category (e.g., factual_lookup, deep_research)"
    )

    parser.add_argument(
        "--complexity",
        type=str,
        choices=["simple", "medium", "high", "very_high"],
        help="Filter by complexity level"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of test examples"
    )

    parser.add_argument(
        "--evaluators",
        nargs="+",
        choices=list(ALL_EVALUATORS.keys()),
        help="Specific evaluators to use (default: auto-select based on example)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run locally without uploading to LangSmith"
    )

    parser.add_argument(
        "--experiment-name",
        type=str,
        help="Custom experiment name"
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of test cases to run in parallel (default: 1 for clean output, increase for speed)"
    )

    args = parser.parse_args()

    # Load dataset
    print(f"Loading dataset: {args.dataset}")
    dataset = load_dataset(args.dataset)
    examples = filter_examples(
        dataset,
        category=args.category,
        complexity=args.complexity,
        limit=args.limit
    )

    print(f"✓ Loaded {len(examples)} test examples")

    # Setup evaluators
    if args.evaluators:
        evaluators = [ALL_EVALUATORS[name] for name in args.evaluators]
        print(f"✓ Using specified evaluators: {args.evaluators}")
    else:
        # Use recommended evaluators (mix of heuristic and LLM)
        evaluators = list(HEURISTIC_EVALUATORS.values()) + [
            LLM_EVALUATORS["accuracy"],
            LLM_EVALUATORS["relevance"],
            LLM_EVALUATORS["hallucination"]
        ]
        print(f"✓ Using default evaluator set ({len(evaluators)} evaluators)")

    # Upload dataset to LangSmith (unless dry run)
    dataset_name = dataset.get("dataset_name", "research_agent_eval")
    if not args.dry_run:
        client = Client()
        dataset_name = upload_dataset_to_langsmith(client, dataset, examples)

    # Run evaluation
    if args.compare:
        # Comparative evaluation
        results = compare_graphs(
            graph_names=args.compare,
            dataset_name=dataset_name,
            examples=examples,
            evaluators=evaluators
        )
    else:
        # Single graph evaluation
        graph_name = args.graph or get_default_graph()
        results = run_evaluation(
            graph_name=graph_name,
            dataset_name=dataset_name,
            examples=examples,
            evaluators=evaluators,
            experiment_name=args.experiment_name,
            dry_run=args.dry_run,
            max_concurrency=args.concurrency
        )

    # Generate summary report
    if not args.dry_run:
        generate_summary_report(results)

    print("\n✓ Evaluation complete!")
    if not args.dry_run:
        print("  View results in LangSmith: https://smith.langchain.com/")


if __name__ == "__main__":
    main()
