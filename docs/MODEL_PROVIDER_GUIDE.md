# Model Provider Guide: Ollama vs Gemini

## Quick Switch

```bash
# Switch to Gemini (fast, paid)
python switch_model_provider.py gemini

# Switch to Ollama (free, local)
python switch_model_provider.py ollama

# Check current provider
python switch_model_provider.py status
```

## Provider Comparison

### Gemini (gemini-1.5-flash)

**Pros:**
- ⚡ **Very Fast**: Responses in 1-3 seconds
- 🎯 **High Quality**: Excellent for LLM-as-judge evaluation
- 🔄 **Consistent**: Low variance in evaluator scores
- 🌐 **Scalable**: No local resource limits
- 🛠️ **No Setup**: Works immediately with API key

**Cons:**
- 💰 **Costs Money**: ~$0.075 per 1M input tokens, $0.30 per 1M output tokens
- 🔑 **Requires API Key**: Must have Google API access
- 🌐 **Requires Internet**: Cannot work offline
- 📊 **Usage Limits**: Rate limits may apply

**Best For:**
- Production evaluation runs
- Large-scale testing (100+ examples)
- Time-sensitive evaluations
- When consistency is critical
- Teams without GPU hardware

**Estimated Costs (as of Jan 2025):**
- Full 20-example evaluation: ~$0.01-0.05
- 100 examples with all evaluators: ~$0.20-0.50
- Daily regression testing: ~$0.50-2.00/day

### Ollama (llama3 / command-r)

**Pros:**
- 🆓 **Completely Free**: No API costs
- 🔒 **Private**: All data stays local
- 🔌 **Offline**: Works without internet
- 🚀 **Unlimited**: No rate limits or quotas
- 🧪 **Experimentation-Friendly**: Test freely without cost concerns

**Cons:**
- 🐌 **Slower**: 10-30 seconds per response (hardware dependent)
- 💻 **Requires Resources**: Needs good CPU/GPU
- 📊 **Higher Variance**: LLM-as-judge scores may vary more
- ⚙️ **Setup Required**: Must install and run Ollama
- 🔄 **Model Management**: Need to pull and manage models

**Best For:**
- Development and testing
- Budget-conscious projects
- Privacy-sensitive data
- Offline environments
- Learning and experimentation
- When speed is not critical

**Hardware Requirements:**
- **Minimum**: 16GB RAM, 4-core CPU
- **Recommended**: 32GB RAM, 8-core CPU, GPU with 8GB+ VRAM
- **Optimal**: 64GB RAM, GPU with 16GB+ VRAM

## When to Use Each

### Use Gemini When:

1. **Running Production Evaluations**
   ```bash
   python switch_model_provider.py gemini
   python evaluate_agent.py --experiment-name "production_baseline"
   ```

2. **Comparing Multiple Graphs**
   ```bash
   # Gemini is 5-10x faster for comparative analysis
   python evaluate_agent.py --compare quick_research deep_research fact_check comparative
   ```

3. **Large-Scale Testing**
   ```bash
   # All 20 examples complete in ~5-10 minutes with Gemini
   python evaluate_agent.py
   ```

4. **CI/CD Pipelines**
   ```yaml
   # Fast feedback in automated testing
   - run: python evaluate_agent.py --category regression_test
   ```

### Use Ollama When:

1. **Development and Iteration**
   ```bash
   python switch_model_provider.py ollama
   python evaluate_agent.py --dry-run --limit 3
   ```

2. **Cost Sensitivity**
   ```bash
   # Free unlimited testing during development
   python evaluate_agent.py --category factual_lookup
   ```

3. **Privacy Requirements**
   ```bash
   # Test with sensitive internal documentation
   python evaluate_agent.py --category internal_documentation
   ```

4. **Offline Work**
   ```bash
   # Works without internet connection
   python evaluate_agent.py --limit 5
   ```

## Hybrid Approach (Recommended)

**Best Practice:** Use both strategically

```bash
# Development: Use Ollama
python switch_model_provider.py ollama
python evaluate_agent.py --dry-run --limit 3

# Quick iterations with Ollama
python evaluate_agent.py --category factual_lookup --limit 5

# Production baseline: Switch to Gemini
python switch_model_provider.py gemini
python evaluate_agent.py --experiment-name "v2.1_baseline"

# Final validation with Gemini
python evaluate_agent.py --compare quick_research deep_research
```

## Performance Comparison

| Metric | Gemini (Flash) | Ollama (llama3) | Ollama (command-r) |
|--------|----------------|-----------------|-------------------|
| **Speed (per eval)** | 1-3s | 10-20s | 15-30s |
| **20 examples** | 5-10 min | 30-60 min | 40-80 min |
| **Cost (20 examples)** | $0.01-0.05 | $0 | $0 |
| **Consistency** | Very High | Medium | Medium |
| **Setup** | API key only | Ollama + models | Ollama + models |
| **Offline** | ❌ | ✅ | ✅ |

## Model Configuration

### Current Settings (src/models.py)

```python
# Gemini Models
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"  # Fast, cost-effective
ADVANCED_GEMINI_MODEL = "gemini-1.5-pro"   # Higher quality, slower, pricier

# Ollama Models
Planner: llama3
Evaluator: command-r
Synthesizer: llama3
Master Planner: command-r
```

### Customizing Models

Edit `src/models.py` to change which models are used:

```python
def get_evaluation_model():
    """Model used for LLM-as-judge evaluators"""
    return _get_model(
        gemini_model="gemini-1.5-flash",  # Fast evaluations
        # gemini_model="gemini-1.5-pro",  # Higher quality, slower
        ollama_model="command-r",
        temperature=0.5  # Lower = more consistent
    )
```

## Cost Optimization

### If Using Gemini:

1. **Use Selective Evaluators**
   ```bash
   # Only run heuristic evaluators (free)
   python evaluate_agent.py --evaluators response_length execution_time rag_usage no_errors
   ```

2. **Limit LLM-as-Judge Calls**
   ```bash
   # Use only critical LLM evaluators
   python evaluate_agent.py --evaluators accuracy hallucination
   ```

3. **Test Incrementally**
   ```bash
   # Start with small subsets
   python evaluate_agent.py --complexity simple --limit 5
   python evaluate_agent.py --complexity medium --limit 5
   ```

4. **Use Caching** (if available)
   - LangSmith may cache some evaluations
   - Avoid re-running identical experiments

### Cost Tracking

Monitor usage in Google Cloud Console:
- Navigate to: https://console.cloud.google.com/
- Select your project
- Go to "APIs & Services" → "Gemini API"
- View usage and costs

## Troubleshooting

### Gemini Issues

**Error: "GOOGLE_API_KEY not found"**
```bash
# Add to .env
GOOGLE_API_KEY="your-api-key-here"

# Verify
python switch_model_provider.py status
```

**Error: "Rate limit exceeded"**
```bash
# Reduce concurrency in evaluate_agent.py
max_concurrency=1  # Instead of 2

# Or add delays between requests
```

**Error: "Invalid API key"**
- Verify key at: https://makersuite.google.com/app/apikey
- Ensure Gemini API is enabled in your Google Cloud project

### Ollama Issues

**Error: "Cannot connect to Ollama"**
```bash
# Start Ollama
ollama serve

# Or restart Ollama app
```

**Error: "Model not found"**
```bash
# Pull required models
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text

# Verify
ollama list
```

**Slow Performance**
- Upgrade hardware (more RAM, better GPU)
- Use smaller models (but lower quality)
- Reduce context length in prompts

## Switching Back and Forth

The switcher is designed for easy testing:

```bash
# Morning: Develop with Ollama (free)
python switch_model_provider.py ollama
python evaluate_agent.py --dry-run --limit 3

# Afternoon: Quick test with Gemini
python switch_model_provider.py gemini
python evaluate_agent.py --category factual_lookup --limit 5

# Evening: Full evaluation with Gemini
python evaluate_agent.py --experiment-name "end_of_day_baseline"

# Back to Ollama for development
python switch_model_provider.py ollama
```

## Recommendations by Use Case

### Solo Developer / Learning
**Use:** Ollama (90%) + Gemini (10% for validation)
- Develop and iterate with Ollama
- Validate important baselines with Gemini

### Team / Production
**Use:** Gemini (80%) + Ollama (20% for dev)
- Fast iteration and consistent results with Gemini
- Use Ollama for privacy-sensitive tests

### Research / Academic
**Use:** Ollama (100%)
- Free, reproducible, controllable
- Can specify exact model versions

### Enterprise / High-Volume
**Use:** Gemini (95%) + Ollama (5% for offline)
- Speed and scale with Gemini
- Ollama as backup for network issues

## Summary

**TL;DR:**

- **Development**: Use Ollama (free, unlimited)
- **Production**: Use Gemini (fast, consistent)
- **Switch easily**: `python switch_model_provider.py <provider>`
- **Check status**: `python switch_model_provider.py status`

---

**Current Status:**
```bash
python switch_model_provider.py status
```

**Next Steps:**
```bash
# Try both and compare
python switch_model_provider.py gemini
python evaluate_agent.py --dry-run --limit 2

python switch_model_provider.py ollama
python evaluate_agent.py --dry-run --limit 2
```
