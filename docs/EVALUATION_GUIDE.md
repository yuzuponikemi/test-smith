# Test-Smith Evaluation Guide

**Version:** 1.0
**Last Updated:** January 2025

This guide explains how to evaluate the Test-Smith research agent system using LangSmith's evaluation framework.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Dataset Structure](#dataset-structure)
4. [Evaluators](#evaluators)
5. [Running Evaluations](#running-evaluations)
6. [Comparative Analysis](#comparative-analysis)
7. [Interpreting Results](#interpreting-results)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The evaluation framework provides:

- **📊 Test Datasets**: 20 curated test cases covering different complexity levels
- **🎯 Custom Evaluators**: 11 evaluators (6 heuristic + 5 LLM-as-judge)
- **🔬 LangSmith Integration**: Automatic upload and experiment tracking
- **📈 Comparative Analysis**: Compare different graphs side-by-side
- **📝 Automated Reports**: Summary reports with key metrics

### Evaluation Dimensions

1. **Accuracy**: Factual correctness of information
2. **Completeness**: Coverage of all relevant aspects
3. **Hallucination**: Detection of fabricated information
4. **Relevance**: How well the output addresses the query
5. **Structure**: Organization and readability
6. **Performance**: Execution time and efficiency
7. **Source Attribution**: Proper use of RAG vs web search

---

## Quick Start

### 1. Install Dependencies

```bash
pip install langsmith
```

### 2. Set Up Environment

Ensure your `.env` file has LangSmith credentials:

```bash
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-key-here"
LANGCHAIN_PROJECT="deep-research-v1-proto"
```

### 3. Run a Dry Run

Test locally without uploading to LangSmith:

```bash
python evaluate_agent.py --dry-run --limit 3
```

### 4. Run Full Evaluation

```bash
python evaluate_agent.py --graph quick_research
```

### 5. View Results

Results are automatically uploaded to LangSmith:

```
https://smith.langchain.com/
→ Navigate to your project
→ Select "Datasets" tab
→ View experiment results
```

---

## Dataset Structure

### Location

```
evaluation/datasets/research_test_cases.json
```

### Example Test Case

```json
{
  "id": "deep_research_001",
  "input": "Explain quantum computing and its potential applications",
  "reference_output": "A comprehensive report covering...",
  "expected_graph": "deep_research",
  "complexity": "high",
  "category": "complex_topic",
  "evaluation_criteria": {
    "depth": "Should cover multiple subtopics comprehensively",
    "technical_accuracy": "Should correctly explain quantum principles"
  },
  "metadata": {
    "expected_subtasks": 4,
    "min_execution_time": 60,
    "should_use_hierarchical": true
  }
}
```

### Test Case Categories

1. **factual_lookup** (20%): Simple fact-based questions
2. **claim_verification** (10%): Fact-checking tasks
3. **comparative_analysis** (10%): Side-by-side comparisons
4. **complex_topic** (25%): Deep research on complex subjects
5. **internal_documentation** (10%): RAG-specific tests
6. **edge_case** (10%): Error handling and robustness
7. **special_tests** (15%): Hallucination, speed, ambiguity tests

### Complexity Levels

- **simple**: Quick lookups (<30s expected)
- **medium**: Standard research (30-60s expected)
- **high**: Deep analysis (60-180s expected)
- **very_high**: Multi-faceted synthesis (180s+ expected)

---

## Evaluators

### Heuristic Evaluators (Fast, Deterministic)

| Evaluator | What It Measures | Score Range |
|-----------|------------------|-------------|
| `response_length` | Appropriate response length for complexity | 0.0 - 1.0 |
| `execution_time` | Performance within expected thresholds | 0.0 - 1.0 |
| `rag_usage` | Correct use of RAG vs web search | 0.0 - 1.0 |
| `no_errors` | Successful execution without errors | 0.0 / 1.0 |
| `graph_selection` | Appropriate graph chosen for query | 0.0 - 1.0 |
| `citation_quality` | Presence of source attributions | 0.0 - 1.0 |

### LLM-as-Judge Evaluators (Nuanced, Context-Aware)

| Evaluator | What It Measures | Model Used |
|-----------|------------------|------------|
| `accuracy` | Factual correctness | Ollama (command-r) |
| `completeness` | Coverage of all aspects | Ollama (command-r) |
| `hallucination` | Fabricated information (lower = better) | Ollama (command-r) |
| `relevance` | Addressing the specific query | Ollama (command-r) |
| `structure` | Organization and clarity | Ollama (command-r) |

### Evaluator Selection

By default, the system auto-selects evaluators based on test case category:

```python
# Simple queries
- no_errors, response_length, accuracy, relevance, execution_time

# Complex queries
+ completeness, structure, citation_quality

# RAG-specific queries
+ rag_usage

# Hallucination tests
+ hallucination
```

Override with `--evaluators`:

```bash
python evaluate_agent.py --evaluators accuracy hallucination rag_usage
```

---

## Running Evaluations

### Basic Evaluation

```bash
# Evaluate default graph (deep_research) with all test cases
python evaluate_agent.py
```

### Filter by Category

```bash
# Test only factual lookups
python evaluate_agent.py --category factual_lookup

# Test only complex topics
python evaluate_agent.py --category complex_topic
```

### Filter by Complexity

```bash
# Test only simple queries
python evaluate_agent.py --complexity simple

# Test high complexity queries
python evaluate_agent.py --complexity high
```

### Limit Number of Examples

```bash
# Run on first 5 examples
python evaluate_agent.py --limit 5

# Quick test with 3 examples
python evaluate_agent.py --dry-run --limit 3
```

### Specify Graph

```bash
# Evaluate quick_research graph
python evaluate_agent.py --graph quick_research

# Evaluate fact_check graph
python evaluate_agent.py --graph fact_check
```

### Custom Experiment Name

```bash
python evaluate_agent.py --experiment-name "quick_research_v2_baseline"
```

---

## Comparative Analysis

### Compare Multiple Graphs

```bash
# Compare quick vs deep research
python evaluate_agent.py --compare quick_research deep_research

# Compare all graph types
python evaluate_agent.py --compare quick_research fact_check comparative deep_research
```

### What Gets Compared

- **Accuracy scores** across same test cases
- **Execution time** differences
- **Completeness** of responses
- **RAG vs web usage patterns**
- **Success rate** (no errors)

### Viewing Comparison in LangSmith

1. Navigate to LangSmith dashboard
2. Select "Experiments" tab
3. Select multiple experiments (Ctrl/Cmd + Click)
4. Click "Compare" button
5. View side-by-side metrics and examples

---

## Interpreting Results

### LangSmith Dashboard

After running evaluation, you'll see:

#### Aggregate Metrics

```
Accuracy:       0.85  (avg across all examples)
Completeness:   0.78
Hallucination:  0.92  (higher = less hallucination)
Execution Time: 45.2s (avg)
Success Rate:   95%   (no errors)
```

#### Per-Example Results

Click on individual examples to see:
- Input query
- Agent output
- All evaluator scores
- Comments/reasoning
- Trace (full execution path)

### Key Metrics to Watch

1. **Accuracy < 0.7**: Review factual errors
2. **Hallucination < 0.8**: System fabricating information
3. **RAG Usage = 0.0** on internal docs: RAG not being used
4. **Execution Time > 120s** for simple queries: Performance issue
5. **Success Rate < 90%**: Stability problems

### Red Flags

- **All scores near 0.5**: LLM evaluator is uncertain
- **Execution time variance > 100s**: Inconsistent performance
- **Hallucination trend decreasing**: Model drift or prompt issues
- **RAG never used**: Knowledge base not accessible

---

## Best Practices

### 1. Start with Dry Runs

Always test locally first:

```bash
python evaluate_agent.py --dry-run --limit 3
```

### 2. Use Incremental Evaluation

Don't run all 20 examples immediately:

```bash
# Start with simple
python evaluate_agent.py --complexity simple

# Then medium
python evaluate_agent.py --complexity medium

# Finally high
python evaluate_agent.py --complexity high
```

### 3. Focus on Specific Concerns

If testing a specific feature:

```bash
# Testing RAG improvements
python evaluate_agent.py --category internal_documentation \
  --evaluators rag_usage accuracy

# Testing speed optimizations
python evaluate_agent.py --evaluators execution_time response_length \
  --limit 10
```

### 4. Maintain Evaluation History

Use descriptive experiment names:

```bash
python evaluate_agent.py \
  --experiment-name "deep_research_post_phase4_improvements" \
  --graph deep_research
```

### 5. Compare Baselines

Before making changes:

```bash
# Establish baseline
python evaluate_agent.py --experiment-name "baseline_v2.1"

# After changes
python evaluate_agent.py --experiment-name "after_prompt_tuning"

# Compare in LangSmith
```

### 6. Add New Test Cases

When you find edge cases in production:

```json
{
  "id": "production_failure_001",
  "input": "Query that failed in production",
  "reference_output": "Expected behavior",
  "category": "regression_test",
  "complexity": "medium"
}
```

### 7. Use Category-Specific Datasets

Create focused datasets:

```bash
# Speed benchmarks
evaluation/datasets/speed_benchmark.json

# RAG quality tests
evaluation/datasets/rag_quality.json

# Hallucination tests
evaluation/datasets/hallucination_detection.json
```

---

## Troubleshooting

### Issue: "Dataset not found"

```bash
# Check path
ls evaluation/datasets/research_test_cases.json

# Use absolute path if needed
python evaluate_agent.py --dataset /full/path/to/dataset.json
```

### Issue: "LangSmith upload failed"

```bash
# Verify credentials
echo $LANGCHAIN_API_KEY

# Test with dry run
python evaluate_agent.py --dry-run --limit 1

# Check LangSmith status
# Visit: https://status.langchain.com/
```

### Issue: "Evaluator timeout"

LLM-as-judge evaluators may timeout on slow models:

```python
# In evaluators.py, add timeout
def create_llm_evaluator(...):
    llm = get_evaluation_model()
    llm.timeout = 60  # 60 second timeout
```

### Issue: "Inconsistent scores"

LLM evaluators have inherent variance. Solutions:

1. **Run with repetitions**:
   ```python
   # In evaluate_agent.py
   evaluate(..., num_repetitions=3)
   ```

2. **Use temperature=0**:
   ```python
   # In src/models.py
   def get_evaluation_model():
       return _get_model(temperature=0.0)
   ```

3. **Add few-shot examples** to evaluator prompts

### Issue: "Out of memory"

Reduce concurrency:

```python
# In evaluate_agent.py
evaluate(..., max_concurrency=1)
```

### Issue: "Graph not found"

```bash
# List available graphs
python main.py graphs

# Use exact name
python evaluate_agent.py --graph quick_research
```

---

## Advanced Usage

### Custom Evaluators

Create your own evaluators in `evaluation/evaluators.py`:

```python
def evaluate_custom_metric(run: Any, example: Any) -> Dict[str, Any]:
    """Your custom evaluation logic."""
    output = run.outputs.get("report", "")

    # Your scoring logic
    score = your_scoring_function(output)

    return {
        "key": "custom_metric",
        "score": score,
        "comment": "Explanation of score"
    }

# Register it
ALL_EVALUATORS["custom_metric"] = evaluate_custom_metric
```

### Programmatic Usage

```python
from evaluate_agent import run_evaluation, load_dataset
from evaluation.evaluators import ALL_EVALUATORS

# Load dataset
dataset = load_dataset()
examples = dataset["examples"][:5]

# Select evaluators
evaluators = [
    ALL_EVALUATORS["accuracy"],
    ALL_EVALUATORS["hallucination"]
]

# Run evaluation
results = run_evaluation(
    graph_name="quick_research",
    dataset_name="my_dataset",
    examples=examples,
    evaluators=evaluators,
    experiment_name="programmatic_eval"
)
```

### CI/CD Integration

```yaml
# .github/workflows/evaluate.yml
name: Agent Evaluation

on:
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Regression Tests
        run: |
          python evaluate_agent.py \
            --category regression_test \
            --experiment-name "pr-${{ github.event.pull_request.number }}"
        env:
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
```

---

## Next Steps

1. **Run your first evaluation**:
   ```bash
   python evaluate_agent.py --dry-run --limit 3
   ```

2. **Review the LangSmith dashboard**:
   https://smith.langchain.com/

3. **Add your own test cases**: Edit `evaluation/datasets/research_test_cases.json`

4. **Create custom evaluators**: For domain-specific metrics

5. **Set up automated evaluation**: Run on every commit or weekly

---

## Resources

- **LangSmith Docs**: https://docs.langchain.com/langsmith/
- **Evaluation Concepts**: https://docs.langchain.com/langsmith/evaluation-concepts
- **Test-Smith Architecture**: docs/system-overview.md
- **RAG Best Practices**: docs/RAG_DATA_PREPARATION_GUIDE.md

---

**Questions or Issues?**

- Check `evaluation/evaluators.py` for evaluator implementation
- Review `evaluate_agent.py` for CLI options
- See example results in `evaluation/results/`
