# Installation & Setup

This guide covers the complete setup process for Test-Smith using **UV**, the modern Python package manager.

---

## Prerequisites

### Required Software

- **Python 3.9.2+** - Core runtime (UV can install this for you)
- **UV** - Modern package manager ([Installation guide](#1-install-uv))
- **Git** - Version control

### Optional: LLM Providers

Choose one or both:

- **Google Gemini API** (Recommended) - Cloud-based LLMs ([Get free key](https://makersuite.google.com/app/apikey))
- **Ollama** (Optional) - Local LLM inference ([Download](https://ollama.ai/))

### Required API Keys

- **Tavily API Key** - Web search ([Get free key](https://tavily.com/))
- **LangSmith API Key** (optional) - Observability ([Get free key](https://smith.langchain.com/))

---

## Installation Steps

### 1. Install UV

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify installation:**
```bash
uv --version
```

### 2. Clone Repository

```bash
git clone https://github.com/your-repo/test-smith.git
cd test-smith
```

### 3. Install Dependencies

UV will automatically create a virtual environment and install all dependencies:

```bash
# Install all dependencies (including dev tools)
uv sync --all-extras
```

**What happens:**
- ✅ Creates `.venv/` automatically
- ✅ Installs all dependencies from `pyproject.toml`
- ✅ Generates `uv.lock` for reproducibility
- ✅ Takes ~5 seconds (vs ~2 minutes with pip!)

### 4. Configure LLM Provider

#### Option A: Google Gemini (Recommended, Default)

**Advantages:**
- ✅ No local installation required
- ✅ Faster inference
- ✅ Lower resource usage
- ✅ Free tier available

**Setup:**
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env` (see step 5)
3. No additional setup needed!

#### Option B: Ollama (Local Models)

**Advantages:**
- ✅ Fully offline
- ✅ No API costs
- ✅ Data privacy

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3           # Main reasoning model (4.7GB)
ollama pull command-r        # Advanced reasoning (20GB)
ollama pull nomic-embed-text # Embeddings (274MB)

# Verify models
ollama list
```

Expected output:
```
NAME              ID          SIZE   MODIFIED
llama3:latest     ...         4.7GB  ...
command-r:latest  ...         20GB   ...
nomic-embed-text  ...         274MB  ...
```

### 5. Configure Environment

Create a `.env` file in the project root:

**For Google Gemini (Default):**
```bash
# Model Provider
MODEL_PROVIDER="gemini"

# Google Gemini API Key (required)
GOOGLE_API_KEY="your-google-api-key-here"

# Web Search (required)
TAVILY_API_KEY="tvly-your-key-here"

# LangSmith (optional - for observability)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Logging (optional)
STRUCTURED_LOGS_JSON="false"
LOG_LEVEL="INFO"
```

**For Ollama (Local):**
```bash
# Model Provider
MODEL_PROVIDER="ollama"

# Web Search (required)
TAVILY_API_KEY="tvly-your-key-here"

# LangSmith (optional - for observability)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Logging (optional)
STRUCTURED_LOGS_JSON="false"
LOG_LEVEL="INFO"
```

### 6. Verify Installation

```bash
# Check version
uv run python main.py --version

# List available graphs
uv run python main.py graphs

# Run test query
uv run python main.py run "What is LangGraph?"
```

**Expected output:**
- Graph list showing available workflows
- Research process with planner → searcher → analyzer → synthesizer
- Final comprehensive report

---

## Directory Structure

After installation, your project should look like:

```
test-smith/
├── .env                    # Environment configuration
├── .venv/                  # Virtual environment (auto-created by UV)
├── uv.lock                 # Dependency lock file
├── pyproject.toml          # Project configuration & dependencies
├── main.py                 # CLI entry point
├── src/                    # Source code
│   ├── graphs/             # Workflow definitions
│   ├── nodes/              # Processing nodes
│   ├── prompts/            # LLM prompts
│   └── preprocessor/       # Document preprocessing
├── documents/              # RAG source documents
├── chroma_db/              # Vector database (created on first run)
├── logs/                   # Execution logs
└── reports/                # Generated reports
```

---

## Troubleshooting

### UV Command Not Found

**Solution:** Add UV to your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

### Ollama Won't Start (If using Ollama)

```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Or restart Ollama app
```

### Model Not Found (If using Ollama)

```bash
# Pull missing model
ollama pull llama3

# Verify it's installed
ollama list
```

### API Key Errors

```bash
# Verify .env file exists
cat .env

# Check environment variable is loaded
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TAVILY_API_KEY'))"
```

### Import Errors

```bash
# Regenerate lock file
uv lock

# Reinstall dependencies
uv sync --all-extras
```

### "No solution found" Dependency Error

**This is the error you just fixed!**

Solution: The `pyproject.toml` now has `requires-python = ">=3.9.2"` which resolves dependency conflicts.

```bash
# If you still see this, try:
uv lock --upgrade
uv sync --all-extras
```

---

## Legacy Installation (Not Recommended)

<details>
<summary>⚠️ Using pip (Deprecated)</summary>

**Note:** This method is deprecated. Use UV for better performance and reproducibility.

```bash
# Clone repository
git clone https://github.com/your-repo/test-smith.git
cd test-smith

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"
```

**Why not pip?**
- 🐌 10-100x slower than UV
- ⚠️ No reproducible builds
- 🔧 Manual venv management required
- ❌ Weaker dependency resolution

</details>

---

## Next Steps

- **[Quick Start](quick-start.md)** - Run your first research query
- **[Model Providers](model-providers.md)** - Configure Ollama or Gemini
- **[UV Usage Guide](../../.github/UV_GUIDE.md)** - Complete UV documentation
- **[RAG Guide](../knowledge-base/rag-guide.md)** - Add documents to the knowledge base

---

## Additional Resources

- **[UV Documentation](https://docs.astral.sh/uv/)** - Official UV docs
- **[UV Troubleshooting](../../.github/UV_GUIDE.md#-troubleshooting)** - Common issues and solutions
- **[Migration from pip](../../.github/UV_GUIDE.md#-migration-from-pip)** - If you're used to pip
