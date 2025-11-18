# Evaluation Guide

Testing Test-Smith using the LangSmith evaluation framework.

---

## Overview

The evaluation framework provides:
- 20 curated test cases
- 11 evaluators (6 heuristic + 5 LLM-as-judge)
- LangSmith integration for tracking
- Comparative analysis across graphs

---

## Quick Start

### 1. Install Dependencies

```bash
pip install langsmith
```

### 2. Configure Environment

```bash
# .env
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"
```

### 3. Run Dry Run

```bash
python evaluation/evaluate_agent.py --dry-run --limit 3
```

### 4. Run Full Evaluation

```bash
python evaluation/evaluate_agent.py --graph quick_research
```

### 5. View Results

Navigate to https://smith.langchain.com/ and select your project.

---

## Evaluators

### Heuristic Evaluators (Fast)

| Evaluator | Measures | Score |
|-----------|----------|-------|
| `response_length` | Appropriate length | 0.0-1.0 |
| `execution_time` | Performance | 0.0-1.0 |
| `rag_usage` | Correct RAG/web use | 0.0-1.0 |
| `no_errors` | Successful execution | 0.0/1.0 |
| `graph_selection` | Appropriate graph | 0.0-1.0 |
| `citation_quality` | Source attribution | 0.0-1.0 |

### LLM-as-Judge Evaluators (Nuanced)

| Evaluator | Measures | Model |
|-----------|----------|-------|
| `accuracy` | Factual correctness | command-r |
| `completeness` | Coverage | command-r |
| `hallucination` | Fabrication (lower=better) | command-r |
| `relevance` | Addresses query | command-r |
| `structure` | Organization | command-r |

---

## Running Evaluations

### Basic

```bash
python evaluation/evaluate_agent.py
```

### Filter by Category

```bash
python evaluation/evaluate_agent.py --category factual_lookup
python evaluation/evaluate_agent.py --category complex_topic
```

### Filter by Complexity

```bash
python evaluation/evaluate_agent.py --complexity simple
python evaluation/evaluate_agent.py --complexity high
```

### Limit Examples

```bash
python evaluation/evaluate_agent.py --limit 5
```

### Specify Graph

```bash
python evaluation/evaluate_agent.py --graph quick_research
```

### Custom Experiment

```bash
python evaluation/evaluate_agent.py --experiment-name "baseline_v2.2"
```

### Specific Evaluators

```bash
python evaluation/evaluate_agent.py --evaluators accuracy hallucination rag_usage
```

---

## Comparative Analysis

### Compare Graphs

```bash
python evaluation/evaluate_agent.py --compare quick_research deep_research
python evaluation/evaluate_agent.py --compare quick_research fact_check comparative
```

### In LangSmith

1. Navigate to dashboard
2. Select "Experiments" tab
3. Ctrl+Click multiple experiments
4. Click "Compare"

---

## Dataset Structure

### Location

```
evaluation/datasets/research_test_cases.json
```

### Test Case Format

```json
{
  "id": "deep_research_001",
  "input": "Explain quantum computing",
  "reference_output": "A comprehensive report...",
  "expected_graph": "deep_research",
  "complexity": "high",
  "category": "complex_topic",
  "evaluation_criteria": {
    "depth": "Should cover multiple subtopics"
  }
}
```

### Categories

- **factual_lookup** (20%): Simple facts
- **claim_verification** (10%): Fact-checking
- **comparative_analysis** (10%): Comparisons
- **complex_topic** (25%): Deep research
- **internal_documentation** (10%): RAG tests
- **edge_case** (10%): Error handling
- **special_tests** (15%): Hallucination, speed

---

## Interpreting Results

### Key Metrics

| Metric | Red Flag |
|--------|----------|
| Accuracy | <0.7 |
| Hallucination | <0.8 |
| RAG Usage | 0.0 on internal docs |
| Execution Time | >120s for simple |
| Success Rate | <90% |

### Dashboard View

```
Accuracy:       0.85  (avg)
Completeness:   0.78
Hallucination:  0.92  (higher = better)
Execution Time: 45.2s (avg)
Success Rate:   95%
```

---

## Best Practices

### 1. Start with Dry Runs

```bash
python evaluation/evaluate_agent.py --dry-run --limit 3
```

### 2. Incremental Testing

```bash
python evaluation/evaluate_agent.py --complexity simple
python evaluation/evaluate_agent.py --complexity medium
python evaluation/evaluate_agent.py --complexity high
```

### 3. Focus Testing

```bash
# Testing RAG
python evaluation/evaluate_agent.py --category internal_documentation \
  --evaluators rag_usage accuracy
```

### 4. Baseline Comparison

```bash
# Before changes
python evaluation/evaluate_agent.py --experiment-name "baseline"

# After changes
python evaluation/evaluate_agent.py --experiment-name "after_changes"
```

---

## Troubleshooting

### "Dataset not found"

```bash
ls evaluation/datasets/research_test_cases.json
```

### "LangSmith upload failed"

```bash
echo $LANGCHAIN_API_KEY
python evaluation/evaluate_agent.py --dry-run --limit 1
```

### "Evaluator timeout"

Increase timeout in `evaluation/evaluators.py`:
```python
llm.timeout = 60
```

### "Inconsistent scores"

Use temperature=0:
```python
def get_evaluation_model():
    return _get_model(temperature=0.0)
```

---

## Custom Evaluators

Create in `evaluation/evaluators.py`:

```python
def evaluate_custom(run, example):
    output = run.outputs.get("report", "")
    score = your_scoring_logic(output)
    return {
        "key": "custom_metric",
        "score": score,
        "comment": "Explanation"
    }

ALL_EVALUATORS["custom_metric"] = evaluate_custom
```

---

## CI/CD Integration

```yaml
# .github/workflows/evaluate.yml
- run: |
    python evaluation/evaluate_agent.py \
      --category regression_test \
      --experiment-name "pr-${{ github.event.pull_request.number }}"
```

---

## Related Documentation

- **[Logging & Debugging](logging-debugging.md)** - Debug execution
- **[Model Providers](../getting-started/model-providers.md)** - Configure models
- **[System Overview](../architecture/system-overview.md)** - Architecture
