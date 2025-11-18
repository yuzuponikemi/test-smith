# Model Providers Guide

Test-Smith supports two model providers: **Ollama** (local) and **Gemini** (cloud).

---

## Quick Switch

```bash
# Switch to Gemini (fast, cloud)
python scripts/utils/switch_model_provider.py gemini

# Switch to Ollama (free, local)
python scripts/utils/switch_model_provider.py ollama

# Check current provider
python scripts/utils/switch_model_provider.py status
```

---

## Provider Comparison

| Feature | Ollama | Gemini |
|---------|--------|--------|
| **Cost** | Free | Pay-per-use (~$0.01-0.05/query) |
| **Speed** | 10-30s per response | 1-3s per response |
| **Privacy** | All data local | Data sent to Google |
| **Offline** | Yes | No |
| **Setup** | Install + pull models | API key only |
| **Consistency** | Medium | High |

---

## Ollama Setup

### Installation

```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Mac
brew install ollama

# Windows
# Download from https://ollama.ai/download
```

### Pull Required Models

```bash
ollama pull llama3           # General reasoning
ollama pull command-r        # Evaluation and synthesis
ollama pull nomic-embed-text # Embeddings for RAG

# Verify
ollama list
```

### Configuration

In `.env`:
```bash
MODEL_PROVIDER="ollama"
OLLAMA_BASE_URL="http://localhost:11434"  # Optional, default
```

### Hardware Requirements

| Level | RAM | CPU | GPU |
|-------|-----|-----|-----|
| Minimum | 16GB | 4-core | Optional |
| Recommended | 32GB | 8-core | 8GB VRAM |
| Optimal | 64GB | 16-core | 16GB VRAM |

### Troubleshooting

**Cannot connect to Ollama:**
```bash
# Start Ollama service
ollama serve

# Check if running
ollama list
```

**Model not found:**
```bash
ollama pull llama3
```

**Slow performance:**
- Upgrade hardware (more RAM, better GPU)
- Use smaller models (but lower quality)
- Close other applications

---

## Gemini Setup

### Get API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### Test API Key

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{"contents":[{"parts":[{"text":"Say hello"}]}]}'
```

### Configuration

In `.env`:
```bash
GOOGLE_API_KEY="AIza..."
MODEL_PROVIDER="gemini"
```

### Model Options

| Model | Speed | Quality | Cost | Use For |
|-------|-------|---------|------|---------|
| `gemini-pro` | Fast | Good | Low | Most tasks |
| `gemini-1.5-flash` | Very Fast | Good | Very Low | Speed-critical |
| `gemini-1.5-pro` | Medium | Best | Higher | Critical analysis |

To change model, edit `src/models.py`:
```python
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"  # Default: "gemini-pro"
```

### Cost Estimation

**Free Tier (Google AI Studio):**
- 60 requests per minute
- Sufficient for development

**With Billing:**
- gemini-pro: ~$0.0005 per 1K characters
- Full research query: ~$0.01-0.05
- 100 queries/day: ~$1-5/day

### Troubleshooting

**404 models/gemini-pro not found:**
- Verify API key at https://makersuite.google.com/app/apikey
- Use Google AI Studio key, not Google Cloud Console

**403 Permission denied:**
- Check quota at https://makersuite.google.com/
- May need to enable billing for higher quotas

**API timeout:**
- Check internet connection
- Retry in a few minutes
- Switch to Ollama temporarily

---

## When to Use Each

### Use Ollama When:

- **Developing and iterating** - Free unlimited testing
- **Privacy required** - Sensitive data stays local
- **Offline work** - No internet needed
- **Learning** - Experiment without cost concerns

```bash
python scripts/utils/switch_model_provider.py ollama
python main.py run "Test query" --graph quick_research
```

### Use Gemini When:

- **Production runs** - Fast, consistent results
- **Large-scale evaluation** - 5-10x faster
- **Time-sensitive** - Quick turnaround needed
- **Comparison testing** - Consistent benchmarks

```bash
python scripts/utils/switch_model_provider.py gemini
python main.py run "Production query" --graph deep_research
```

### Hybrid Approach (Recommended)

```bash
# Development: Ollama (free)
python scripts/utils/switch_model_provider.py ollama
python main.py run "Test query" --graph quick_research

# Production: Gemini (fast)
python scripts/utils/switch_model_provider.py gemini
python main.py run "Final analysis" --graph deep_research
```

---

## Model Configuration Details

### Current Model Assignments

| Task | Ollama Model | Gemini Model |
|------|--------------|--------------|
| Planning | llama3 | gemini-pro |
| Analysis | command-r | gemini-pro |
| Evaluation | command-r | gemini-pro |
| Synthesis | command-r | gemini-pro |
| Embeddings | nomic-embed-text | N/A (uses Ollama) |

### Customizing Models

Edit `src/models.py`:

```python
def get_planner_model():
    return _get_model(
        gemini_model="gemini-1.5-flash",  # Faster for planning
        ollama_model="llama3",
        temperature=0.7
    )

def get_evaluation_model():
    return _get_model(
        gemini_model="gemini-pro",       # Better quality for evaluation
        ollama_model="command-r",
        temperature=0.5                   # More consistent
    )
```

---

## Performance Benchmarks

### 20 Example Evaluation

| Provider | Total Time | Avg per Query | Cost |
|----------|------------|---------------|------|
| Gemini | 5-10 min | 15-30s | $0.01-0.05 |
| Ollama | 30-60 min | 90-180s | $0 |

### Complex Hierarchical Query

| Provider | Time | Subtasks | Notes |
|----------|------|----------|-------|
| Gemini | 2-5 min | 5-7 | Consistent |
| Ollama | 10-20 min | 5-7 | Hardware dependent |

---

## Summary

- **Development**: Use Ollama (free, unlimited, private)
- **Production**: Use Gemini (fast, consistent)
- **Switch easily**: `python scripts/utils/switch_model_provider.py <provider>`
- **Check status**: `python scripts/utils/switch_model_provider.py status`

---

## Next Steps

- **[Quick Start](quick-start.md)** - Run your first query
- **[Evaluation Guide](../development/evaluation-guide.md)** - Benchmark with LangSmith
- **[System Overview](../architecture/system-overview.md)** - Understand model usage in architecture
