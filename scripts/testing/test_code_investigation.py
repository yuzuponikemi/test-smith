"""
Test Code Investigation Graph with Test-Smith Codebase

This script:
1. Ingests the test-smith repository into ChromaDB (codebase_collection)
2. Runs the code_investigation graph with test queries
3. Validates that the graph can answer questions about the codebase

Usage:
    # Run full test (ingest + test queries)
    python scripts/testing/test_code_investigation.py

    # Skip ingestion (use existing collection)
    python scripts/testing/test_code_investigation.py --skip-ingest

    # Run specific test
    python scripts/testing/test_code_investigation.py --test dependency
"""

import argparse
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()


def ingest_repository():
    """Ingest the test-smith repository into ChromaDB"""
    print("=" * 80)
    print("PHASE 1: CODEBASE INGESTION")
    print("=" * 80)

    from scripts.ingest.ingest_codebase import CodebaseIngestion

    # Get repository root
    repo_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print(f"Repository: {repo_path}")
    print("Collection: codebase_collection")

    # Clear existing collection first
    try:
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings

        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vectorstore = Chroma(
            collection_name="codebase_collection",
            persist_directory="chroma_db",
            embedding_function=embeddings,
        )

        # Check if collection exists and has data
        existing_count = vectorstore._collection.count()
        if existing_count > 0:
            print(f"Clearing existing collection ({existing_count} chunks)...")
            vectorstore.delete_collection()
    except Exception as e:
        print(f"Note: Could not check/clear existing collection: {e}")

    # Run ingestion
    ingestion = CodebaseIngestion(
        repo_path=repo_path,
        chroma_db_dir="chroma_db",
        collection_name="codebase_collection",
        min_quality_score=0.3
    )

    start_time = time.time()
    try:
        ingestion.run()
        elapsed = time.time() - start_time
        print(f"\nIngestion completed in {elapsed:.1f}s")
        print(f"Total chunks: {ingestion.stats['total_chunks']}")
        return ingestion.stats
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\nIngestion failed after {elapsed:.1f}s: {e}")
        print("\nTroubleshooting:")
        print("  1. Restart Ollama: pkill ollama && ollama serve")
        print("  2. Or run: ollama pull nomic-embed-text")
        print("  3. Then retry: python scripts/testing/test_code_investigation.py")
        return None


def run_test_queries(test_filter=None):
    """Run test queries against the code_investigation graph"""
    print("\n" + "=" * 80)
    print("PHASE 2: CODE INVESTIGATION TESTS")
    print("=" * 80)

    from src.graphs import get_graph

    # Get the code_investigation graph
    builder = get_graph("code_investigation")
    graph = builder.build()

    # Define test queries with expected content
    test_cases = [
        {
            "name": "dependency",
            "query": "What are the dependencies of the CodeInvestigationGraphBuilder class?",
            "expected_keywords": ["CodeInvestigationGraphBuilder", "StateGraph", "import", "node"],
            "description": "Test dependency tracking for a specific class"
        },
        {
            "name": "flow",
            "query": "How does data flow through the dependency_analyzer_node?",
            "expected_keywords": ["state", "code_results", "dependencies", "return"],
            "description": "Test data flow analysis"
        },
        {
            "name": "usage",
            "query": "Where is the DocumentAnalyzer class used in the codebase?",
            "expected_keywords": ["DocumentAnalyzer", "ingest", "preprocessor", "analyze"],
            "description": "Test usage finding"
        },
        {
            "name": "architecture",
            "query": "What is the architecture of the graph registry system?",
            "expected_keywords": ["registry", "register_graph", "get_graph", "BaseGraphBuilder"],
            "description": "Test architecture understanding"
        },
        {
            "name": "implementation",
            "query": "How does the C# code analysis work in the DocumentAnalyzer?",
            "expected_keywords": ["csharp", "class", "method", "namespace", "property"],
            "description": "Test implementation understanding"
        },
    ]

    # Filter tests if specified
    if test_filter:
        test_cases = [t for t in test_cases if t["name"] == test_filter]
        if not test_cases:
            print(f"Error: Test '{test_filter}' not found")
            return []

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{len(test_cases)}: {test['name'].upper()}")
        print(f"{'='*60}")
        print(f"Description: {test['description']}")
        print(f"Query: {test['query']}")

        start_time = time.time()

        try:
            # Run the graph
            result = graph.invoke({
                "query": test["query"],
                "collection_name": "codebase_collection"
            })

            elapsed = time.time() - start_time

            # Extract report
            report = result.get("report", "")

            # Check for expected keywords
            found_keywords = []
            missing_keywords = []
            for keyword in test["expected_keywords"]:
                if keyword.lower() in report.lower():
                    found_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

            # Calculate score
            score = len(found_keywords) / len(test["expected_keywords"]) if test["expected_keywords"] else 1.0
            passed = score >= 0.5  # At least 50% of keywords found

            # Print results
            print(f"\nTime: {elapsed:.1f}s")
            print(f"Report length: {len(report)} chars")
            print(f"Keywords found: {len(found_keywords)}/{len(test['expected_keywords'])}")

            if found_keywords:
                print(f"  Found: {', '.join(found_keywords)}")
            if missing_keywords:
                print(f"  Missing: {', '.join(missing_keywords)}")

            status = "PASS" if passed else "FAIL"
            print(f"\nResult: {status} (score: {score:.0%})")

            # Show report preview
            if report:
                preview = report[:500] + "..." if len(report) > 500 else report
                print(f"\nReport Preview:\n{'-'*40}\n{preview}\n{'-'*40}")

            results.append({
                "name": test["name"],
                "passed": passed,
                "score": score,
                "time": elapsed,
                "report_length": len(report),
                "found_keywords": found_keywords,
                "missing_keywords": missing_keywords
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\nError: {e}")
            print("Result: FAIL (error)")

            results.append({
                "name": test["name"],
                "passed": False,
                "score": 0,
                "time": elapsed,
                "error": str(e)
            })

    return results


def print_summary(ingest_stats, test_results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    if ingest_stats:
        print("\nIngestion:")
        print(f"  Files processed: {ingest_stats.get('files_processed', 0)}")
        print(f"  Total chunks: {ingest_stats.get('total_chunks', 0)}")
        print(f"  Languages: {', '.join(ingest_stats.get('languages', {}).keys())}")

    if test_results:
        passed = sum(1 for r in test_results if r.get("passed", False))
        total = len(test_results)

        print(f"\nTest Results: {passed}/{total} passed")

        for result in test_results:
            status = "✓" if result.get("passed") else "✗"
            name = result.get("name", "unknown")
            score = result.get("score", 0)
            time_taken = result.get("time", 0)

            if "error" in result:
                print(f"  {status} {name}: ERROR - {result['error'][:50]}")
            else:
                print(f"  {status} {name}: {score:.0%} ({time_taken:.1f}s)")

        # Overall status
        print(f"\nOverall: {'PASS' if passed == total else 'FAIL'}")

        return passed == total

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test code_investigation graph with test-smith codebase'
    )

    parser.add_argument(
        '--skip-ingest',
        action='store_true',
        help='Skip ingestion and use existing collection'
    )

    parser.add_argument(
        '--test',
        choices=['dependency', 'flow', 'usage', 'architecture', 'implementation'],
        help='Run only a specific test'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose output'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("CODE INVESTIGATION GRAPH TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now()}")
    print(f"Skip ingestion: {args.skip_ingest}")
    if args.test:
        print(f"Running test: {args.test}")

    # Phase 1: Ingestion
    ingest_stats = None
    if not args.skip_ingest:
        ingest_stats = ingest_repository()
    else:
        print("\nSkipping ingestion (using existing collection)")

    # Phase 2: Test queries
    test_results = run_test_queries(test_filter=args.test)

    # Print summary
    success = print_summary(ingest_stats, test_results)

    print(f"\nCompleted at: {datetime.now()}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
