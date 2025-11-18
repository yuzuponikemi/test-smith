# Gemini API Setup Guide

This guide helps you set up Gemini API for Test-Smith evaluations.

## Current Status

**✅ Ollama** is working perfectly (free, local)
**❌ Gemini** requires valid API key setup

## Why Gemini?

- ⚡ **5-10x faster** than Ollama
- 🎯 **More consistent** LLM-as-judge evaluations
- 💰 **Very affordable** (~$0.02-0.05 per full evaluation)

## Prerequisites

### Step 1: Get a Google AI Studio API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

**Note:** Google AI Studio provides free API access with generous quotas (perfect for development/testing).

### Step 2: Verify API Access

Test your key:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{"contents":[{"parts":[{"text":"Say hello"}]}]}'
```

You should see a JSON response with "Hello" or similar.

## Setup Instructions

### 1. Add API Key to .env

Edit `.env` file:
```bash
# Existing keys
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
TAVILY_API_KEY="your-tavily-key"

# Add Gemini key
GOOGLE_API_KEY="AIza..."  # Your actual key from Step 1
MODEL_PROVIDER="gemini"
```

### 2. Install Dependencies (Already Done)

```bash
pip install langchain-google-genai
pip install --upgrade google-ai-generativelanguage
```

### 3. Switch to Gemini

```bash
python switch_model_provider.py gemini
```

### 4. Verify Setup

```bash
python verify_model_provider.py
```

You should see:
```
✅ SUCCESS: Using Gemini API
   Model: gemini-pro
```

### 5. Test with Simple Query

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
import os

llm = ChatGoogleGenerativeAI(
    model='gemini-pro',
    google_api_key=os.getenv('GOOGLE_API_KEY')
)

response = llm.invoke('Say hello')
print(f'SUCCESS: {response.content}')
"
```

## Troubleshooting

### Error: "404 models/gemini-pro not found"

**Cause:** API key might be invalid or API not enabled

**Solution:**
1. Check your API key at https://makersuite.google.com/app/apikey
2. Create a new key if needed
3. Ensure you're using the key from **Google AI Studio**, not Google Cloud Console

### Error: "403 Permission denied"

**Cause:** API quota exceeded or billing required

**Solution:**
1. Check quota at https://makersuite.google.com/
2. For higher quotas, you may need to enable billing in Google Cloud
3. Free tier is usually sufficient for development

### Error: "API key not found in .env"

**Solution:**
```bash
# Check .env file
cat .env | grep GOOGLE_API_KEY

# Add if missing
echo 'GOOGLE_API_KEY="your-key-here"' >> .env
```

### API is slow or timing out

**Cause:** Network issues or API rate limiting

**Solution:**
1. Check internet connection
2. Try again in a few minutes
3. Switch to Ollama temporarily:
   ```bash
   python switch_model_provider.py ollama
   ```

## Model Options

### gemini-pro (Recommended - Currently Used)

- ✅ Stable and well-supported
- ✅ Works with Google AI Studio free tier
- ✅ Good balance of speed and quality
- ⚠️ Older model (pre-1.5 generation)

### gemini-1.5-flash (Newer, Faster)

- ⚡ Even faster than gemini-pro
- 💰 Cheaper than gemini-pro
- ❌ May require Google Cloud setup
- ❌ Not available on all free tiers

To switch:
```python
# Edit src/models.py
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"  # Instead of "gemini-pro"
```

### gemini-1.5-pro (Highest Quality)

- 🎯 Best quality
- 🐌 Slower than Flash
- 💰 More expensive
- Use for critical evaluations only

## Cost Estimation (Google AI Studio)

**Free Tier (as of Jan 2025):**
- 60 requests per minute
- Usually sufficient for development

**If you enable billing:**
- gemini-pro: ~$0.0005 per 1K characters
- Full 20-example evaluation: ~$0.01-0.02
- 100 evaluations/day: ~$1-2/day

## When to Use Each Provider

| Scenario | Recommended | Why |
|----------|-------------|-----|
| **Development** | Ollama | Free, unlimited, private |
| **Quick testing** | Ollama | No API dependencies |
| **Production baselines** | Gemini | Fast, consistent |
| **Large-scale evaluation** | Gemini | 5-10x faster |
| **Privacy-sensitive data** | Ollama | All local |
| **Offline work** | Ollama | No internet needed |

## Current Fix Applied

We've changed the default model to `gemini-pro` which is more stable:

```python
# src/models.py (line 9)
DEFAULT_GEMINI_MODEL = "gemini-pro"  # Was "gemini-1.5-flash"
```

This should work with most Google AI Studio API keys.

## Next Steps

### If you have a valid API key:

1. Add it to `.env`:
   ```bash
   GOOGLE_API_KEY="AIza..."
   ```

2. Test the connection:
   ```bash
   python verify_model_provider.py
   ```

3. Run evaluation:
   ```bash
   python evaluate_agent.py --dry-run --limit 1
   ```

### If you don't have an API key yet:

**Continue using Ollama** (currently active):
```bash
# Verify Ollama is working
python verify_model_provider.py

# Run evaluation with Ollama
python evaluate_agent.py --dry-run --limit 3
```

Ollama works perfectly and is completely free! You can get valid API key later when you need the speed boost.

## Documentation

- **Google AI Studio**: https://makersuite.google.com/
- **Gemini API Docs**: https://ai.google.dev/docs
- **Model Pricing**: https://ai.google.dev/pricing
- **Model Provider Guide**: docs/MODEL_PROVIDER_GUIDE.md

## Summary

✅ **Fixed Issues:**
- Import order bug (`.env` loaded before imports)
- Dependency conflicts
- Model name changed to stable `gemini-pro`

❌ **Remaining:**
- Need valid Google AI Studio API key

🚀 **Current Status:**
- **Ollama is working** (recommended for now)
- **Gemini ready** when you add valid API key

---

**Want to try Gemini?** Get a free API key at https://makersuite.google.com/app/apikey

**Happy with Ollama?** No action needed - it works great!
