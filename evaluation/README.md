# Test-Smith Evaluation Framework

**Status:** ✅ Fully Operational
**Version:** 1.0
**LangSmith Integration:** Enabled

## What We Built

A comprehensive agent evaluation system with:

✅ **20 Test Cases** covering all graph types and complexity levels
✅ **11 Custom Evaluators** (6 heuristic + 5 LLM-as-judge)
✅ **LangSmith Integration** for experiment tracking
✅ **Comparative Analysis** across multiple graphs
✅ **Automated Reporting** with metrics and insights
✅ **CLI Tool** for easy execution

## Quick Start

### 1. Test Locally (Recommended First Step)

```bash
python evaluate_agent.py --dry-run --limit 3
```

### 2. Run Full Evaluation

```bash
python evaluate_agent.py
```

### 3. View Results in LangSmith

Visit: https://smith.langchain.com/

## Project Structure

```
evaluation/
├── README.md                    # This file
├── QUICK_REFERENCE.md           # Command cheat sheet
├── __init__.py                  # Package initialization
├── evaluators.py                # Custom evaluator functions
├── datasets/
│   └── research_test_cases.json # 20 test cases
└── results/                     # Auto-generated reports
```

## Key Files

| File | Purpose |
|------|---------|
| `evaluate_agent.py` | Main CLI runner (root directory) |
| `evaluation/evaluators.py` | 11 custom evaluators |
| `evaluation/datasets/research_test_cases.json` | Test dataset |
| `docs/EVALUATION_GUIDE.md` | Complete documentation |
| `evaluation/QUICK_REFERENCE.md` | Quick command reference |

## Test Dataset Coverage

**20 Examples:**
- Simple (20%): Quick fact lookups
- Medium (35%): Standard research queries
- High (35%): Deep, complex analysis
- Edge Cases (10%): Error handling, hallucinations

**Graph Coverage:**
- quick_research: 30%
- deep_research: 40%
- fact_check: 10%
- comparative: 10%
- Edge cases: 10%

## Evaluator Capabilities

### Heuristic Evaluators (Fast)
1. **response_length** - Checks appropriate verbosity
2. **execution_time** - Performance benchmarks
3. **rag_usage** - Verifies RAG vs web allocation
4. **no_errors** - Stability check
5. **graph_selection** - Correct graph usage
6. **citation_quality** - Source attribution

### LLM-as-Judge Evaluators (Nuanced)
7. **accuracy** - Factual correctness
8. **completeness** - Coverage of all aspects
9. **hallucination** - Fabrication detection (higher = better)
10. **relevance** - Query alignment
11. **structure** - Organization quality

## Common Use Cases

### Regression Testing

```bash
# Before making changes
python evaluate_agent.py --experiment-name "baseline_v2.1"

# After changes
python evaluate_agent.py --experiment-name "after_prompt_tuning"

# Compare in LangSmith
```

### Performance Benchmarking

```bash
python evaluate_agent.py \
  --category speed_test \
  --evaluators execution_time response_length
```

### RAG Quality Testing

```bash
python evaluate_agent.py \
  --category internal_documentation \
  --evaluators rag_usage accuracy
```

### Graph Comparison

```bash
python evaluate_agent.py \
  --compare quick_research deep_research \
  --category complex_topic
```

### Hallucination Detection

```bash
python evaluate_agent.py \
  --category hallucination_detection \
  --evaluators hallucination accuracy
```

## Example Output

```
================================================================================
Running Evaluation: quick_research_eval_20250117_143022
================================================================================
Graph: quick_research
Dataset: research_agent_evaluation_v1
Examples: 5
Evaluators: 9
================================================================================

Running example 1/5: simple_factual_001
  Query: What is the capital of France?
  Output length: 156 chars
  Execution time: 28.3s
  Evaluations: 9
    response_length: 1.0 - Appropriate length (156 chars) for simple query
    execution_time: 1.0 - Completed in 28.3s (within 30s threshold)
    rag_usage: 0.8 - Used RAG only
    no_errors: 1.0 - Completed without errors
    accuracy: 1.0 - All facts correct, mentions Paris
    relevance: 1.0 - Directly addresses the query
    hallucination: 1.0 - No fabrications detected

✓ Evaluation complete!
  View results in LangSmith: https://smith.langchain.com/
```

## Next Steps

1. **Read the full guide**: `docs/EVALUATION_GUIDE.md`
2. **Try a dry run**: `python evaluate_agent.py --dry-run --limit 3`
3. **Add your test cases**: Edit `evaluation/datasets/research_test_cases.json`
4. **Create custom evaluators**: For domain-specific metrics
5. **Set up CI/CD**: Automate evaluation on every commit

## Troubleshooting

**Issue:** "Dataset not found"
**Solution:** Check path is `evaluation/datasets/research_test_cases.json`

**Issue:** "LangSmith upload failed"
**Solution:** Verify `LANGCHAIN_API_KEY` in `.env` file

**Issue:** "Evaluator timeout"
**Solution:** Run with `--dry-run` first, or reduce `max_concurrency`

## Documentation

- **Full Guide**: `docs/EVALUATION_GUIDE.md` (comprehensive)
- **Quick Reference**: `evaluation/QUICK_REFERENCE.md` (commands)
- **LangSmith Docs**: https://docs.langchain.com/langsmith/

## Example Test Cases

View `evaluation/datasets/research_test_cases.json` for:
- Simple factual lookups
- Complex deep research queries
- Fact-checking scenarios
- Comparative analyses
- RAG-specific tests
- Hallucination detection
- Edge case handling

## Verified Working

✅ Dataset loading and filtering
✅ Graph execution with all 4 graph types
✅ All 11 evaluators functioning
✅ Dry run mode for local testing
✅ LangSmith integration ready
✅ Comparative evaluation support
✅ Custom experiment naming

---

**Ready to start?**

```bash
python evaluate_agent.py --dry-run --limit 3
```

Then view the full guide: `docs/EVALUATION_GUIDE.md`
