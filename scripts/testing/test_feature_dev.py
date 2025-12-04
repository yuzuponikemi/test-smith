#!/usr/bin/env python3
"""
Test script for the Feature Development workflow.

This script demonstrates the 7-phase feature development workflow
inspired by Claude Code's feature-dev plugin.

Usage:
    python scripts/testing/test_feature_dev.py
"""

import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graphs import get_graph


def setup_logging():
    """Configure logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("test_feature_dev.log"),
        ],
    )


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_feature_dev_workflow():
    """Test the complete feature development workflow."""
    print_section("Feature Development Workflow Test")

    # Initialize the graph
    print("📦 Loading feature_dev graph...")
    try:
        builder = get_graph("feature_dev")
        workflow = builder.build()
        metadata = builder.get_metadata()
        print(f"✓ Graph loaded: {metadata['display_name']}")
        print(f"  Description: {metadata['description']}")
        print(f"  Phases: {', '.join(metadata['phases'])}")
    except Exception as e:
        print(f"❌ Failed to load graph: {e}")
        return

    # Test feature request
    feature_request = """
    Add a new graph workflow for automated bug triage.

    The workflow should:
    - Analyze bug reports from user input
    - Search the codebase for similar issues
    - Classify the bug by severity and type
    - Suggest potential root causes
    - Recommend files to investigate
    """

    print("\n📝 Feature Request:")
    print(feature_request)

    # Initialize state
    initial_state = {
        "feature_request": feature_request,
        # Initialize all required fields
        "clarified_requirements": "",
        "feature_scope": "",
        "constraints": "",
        "exploration_results": [],
        "similar_features": [],
        "relevant_files": [],
        "codebase_patterns": "",
        "questions": [],
        "user_answers": "",
        "awaiting_user_input": False,
        "architecture_proposals": [],
        "chosen_architecture": None,
        "architecture_decision": "",
        "implementation_approved": False,
        "implementation_plan": "",
        "files_created": [],
        "files_modified": [],
        "implementation_log": [],
        "review_findings": [],
        "critical_issues": [],
        "review_approved": False,
        "summary": "",
        "next_steps": [],
        "current_phase": "discovery",
        "phase_history": [],
    }

    # ===== Phase 1: Discovery =====
    print_section("Phase 1: Discovery")
    try:
        result = workflow.invoke(initial_state)
        print("✓ Discovery complete")
        print(f"\nClarified Requirements:\n{result.get('clarified_requirements', 'N/A')[:300]}...\n")
        print(f"Scope:\n{result.get('feature_scope', 'N/A')[:200]}...\n")

        # Check if workflow ended (waiting for user input)
        if result.get("current_phase") == "clarification" and result.get(
            "awaiting_user_input"
        ):
            print("\n⏸️  Workflow paused: Waiting for clarifying questions")
            questions = result.get("questions", [])
            if questions:
                print(f"\n❓ {len(questions)} Clarifying Questions:")
                for i, q in enumerate(questions, 1):
                    print(f"  {i}. {q}")

                # Simulate user answers
                print("\n💬 Simulating user answers...")
                result["user_answers"] = """
                1. Support Python codebases initially, expand later
                2. Analyze last 50 similar issues
                3. Use simple severity scoring (critical, high, medium, low)
                4. No RAG integration needed for MVP
                """
                result["awaiting_user_input"] = False

                # Continue workflow
                print("\n▶️  Resuming workflow...")
                result = workflow.invoke(result)

        # ===== Phase 2-3: Exploration & Clarification =====
        print_section("Phase 2-3: Exploration & Clarification")
        print(f"✓ Current phase: {result.get('current_phase')}")
        print(f"Relevant files found: {len(result.get('relevant_files', []))}")
        if result.get("relevant_files"):
            print("\nKey files:")
            for f in result.get("relevant_files", [])[:5]:
                print(f"  - {f}")

        # ===== Phase 4: Architecture =====
        if result.get("architecture_proposals"):
            print_section("Phase 4: Architecture Design")
            proposals = result.get("architecture_proposals", [])
            print(f"✓ {len(proposals)} architecture proposals generated:\n")

            for i, proposal in enumerate(proposals, 1):
                print(f"{i}. {proposal['approach_name']}")
                print(f"   Description: {proposal['description']}")
                print(f"   Complexity: {proposal['complexity_score']}/10")
                print(f"   Pros: {', '.join(proposal['pros'][:2])}")
                print(f"   Cons: {', '.join(proposal['cons'][:2])}")
                print()

            # Simulate user choosing architecture
            print("💬 Simulating user choice: Option 3 (Pragmatic Balance)")
            result["chosen_architecture"] = proposals[2] if len(proposals) >= 3 else proposals[0]
            result["architecture_decision"] = "Chose pragmatic balance for speed + quality"
            result["awaiting_user_input"] = False
            result["implementation_approved"] = True

            # Continue workflow
            result = workflow.invoke(result)

        # ===== Phase 5: Implementation =====
        if result.get("implementation_log"):
            print_section("Phase 5: Implementation")
            print("✓ Implementation complete")
            print(f"Files created: {len(result.get('files_created', []))}")
            print(f"Files modified: {len(result.get('files_modified', []))}")

        # ===== Phase 6: Review =====
        if result.get("review_findings"):
            print_section("Phase 6: Quality Review")
            findings = result.get("review_findings", [])
            critical = result.get("critical_issues", [])

            print(f"✓ Review complete: {len(findings)} findings")
            print(f"  Critical issues: {len(critical)}")

            if findings:
                print("\nTop findings:")
                for f in findings[:3]:
                    print(
                        f"  [{f['severity'].upper()}] {f['category']}: {f['description'][:80]}..."
                    )

            # Simulate user approval
            print("\n💬 Simulating user approval: Proceed to summary")
            result["review_approved"] = True
            result["awaiting_user_input"] = False

            # Continue workflow
            result = workflow.invoke(result)

        # ===== Phase 7: Summary =====
        if result.get("summary"):
            print_section("Phase 7: Summary")
            summary = result.get("summary", "")
            print(summary[:500])
            print("\n...")

            next_steps = result.get("next_steps", [])
            if next_steps:
                print("\n📋 Next Steps:")
                for i, step in enumerate(next_steps[:5], 1):
                    print(f"  {i}. {step}")

        print_section("✅ Test Complete")
        print(f"Final phase: {result.get('current_phase')}")
        print(f"Phase history: {' → '.join(result.get('phase_history', []))}")

    except Exception as e:
        print(f"\n❌ Error during workflow execution: {e}")
        import traceback

        traceback.print_exc()


def test_graph_registration():
    """Test that the graph is properly registered."""
    print_section("Graph Registration Test")

    from src.graphs import list_graphs

    graphs = list_graphs()

    if "feature_dev" in graphs:
        print("✓ feature_dev graph is registered")
        metadata = graphs["feature_dev"]
        print(f"\nMetadata:")
        print(json.dumps(metadata, indent=2))
    else:
        print("❌ feature_dev graph NOT registered")
        print(f"Available graphs: {', '.join(graphs.keys())}")


if __name__ == "__main__":
    setup_logging()

    print("\n🧪 Feature Development Workflow Tests\n")

    # Test 1: Graph registration
    test_graph_registration()

    # Test 2: Full workflow
    test_feature_dev_workflow()

    print("\n✅ All tests complete!\n")
