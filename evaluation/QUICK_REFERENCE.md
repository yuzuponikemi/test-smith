# Evaluation Quick Reference

## Model Provider

```bash
# Switch to Gemini (fast, paid)
python switch_model_provider.py gemini

# Switch to Ollama (free, local)
python switch_model_provider.py ollama

# Check current provider
python switch_model_provider.py status
```

## Common Commands

```bash
# Dry run with 3 examples (local only)
python evaluate_agent.py --dry-run --limit 3

# Full evaluation with default graph
python evaluate_agent.py

# Evaluate specific graph
python evaluate_agent.py --graph quick_research

# Compare graphs
python evaluate_agent.py --compare quick_research deep_research

# Filter by category
python evaluate_agent.py --category factual_lookup

# Filter by complexity
python evaluate_agent.py --complexity simple --limit 5

# Custom evaluators
python evaluate_agent.py --evaluators accuracy hallucination rag_usage

# Named experiment
python evaluate_agent.py --experiment-name "baseline_v2.1"
```

## Key Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Accuracy | >0.8 | 0.6-0.8 | <0.6 |
| Completeness | >0.75 | 0.5-0.75 | <0.5 |
| Hallucination | >0.85 | 0.7-0.85 | <0.7 |
| Execution Time (simple) | <30s | 30-60s | >60s |
| Execution Time (deep) | <120s | 120-180s | >180s |
| Success Rate | >95% | 90-95% | <90% |

## Evaluators

**Heuristic (Fast)**
- `response_length` - Appropriate length
- `execution_time` - Performance
- `rag_usage` - Source selection
- `no_errors` - Stability
- `graph_selection` - Graph choice
- `citation_quality` - Attribution

**LLM-as-Judge (Nuanced)**
- `accuracy` - Factual correctness
- `completeness` - Coverage
- `hallucination` - Fabrication (↑=better)
- `relevance` - Query alignment
- `structure` - Organization

## Dataset Categories

- `factual_lookup` - Simple facts
- `claim_verification` - Fact-checking
- `comparative_analysis` - Comparisons
- `complex_topic` - Deep research
- `internal_documentation` - RAG tests
- `edge_case` - Error handling
- `hallucination_detection` - Truthfulness

## Workflow

1. **Develop**: Make changes to graph/prompts/models
2. **Dry Run**: `--dry-run --limit 3` to test locally
3. **Incremental**: Test category/complexity subsets
4. **Full Run**: Evaluate complete dataset
5. **Review**: Check LangSmith dashboard
6. **Iterate**: Fix issues, re-evaluate
7. **Baseline**: Save as named experiment for comparison

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dataset not found | Check path: `evaluation/datasets/research_test_cases.json` |
| LangSmith upload fails | Verify `LANGCHAIN_API_KEY` in `.env` |
| Evaluator timeout | Reduce concurrency or increase timeout |
| Inconsistent scores | Use temperature=0 for evaluator model |
| Out of memory | Set `max_concurrency=1` |

## View Results

**LangSmith Dashboard**: https://smith.langchain.com/
- Datasets tab → Your dataset
- Experiments tab → Your runs
- Select multiple → Compare button

**Local Reports**: `evaluation/results/eval_summary_*.txt`
