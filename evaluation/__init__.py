"""
Test-Smith Evaluation Framework

This package provides comprehensive evaluation capabilities for the
Test-Smith multi-agent research system.

Components:
- datasets/: Test case datasets in JSON format
- evaluators.py: Custom evaluation functions
- evaluate_agent.py: Main evaluation runner (CLI)
- results/: Evaluation results and reports

Quick Start:
    # Run full evaluation
    python evaluate_agent.py

    # Dry run with 3 examples
    python evaluate_agent.py --dry-run --limit 3

    # Compare graphs
    python evaluate_agent.py --compare quick_research deep_research
"""

__version__ = "1.0.0"
