# Installation & Setup

This guide covers the complete setup process for Test-Smith.

---

## Prerequisites

### Required Software

- **Python 3.8+** - Core runtime
- **Ollama** - Local LLM inference
- **Git** - Version control

### Required API Keys

- **Tavily API Key** - Web search ([Get free key](https://tavily.com/))
- **LangSmith API Key** (optional) - Observability ([Get free key](https://smith.langchain.com/))
- **Google API Key** (optional) - For Gemini models ([Get key](https://makersuite.google.com/app/apikey))

---

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/test-smith.git
cd test-smith
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or for development:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### 4. Install and Configure Ollama

```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3
ollama pull command-r
ollama pull nomic-embed-text

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

```bash
# Required: Tavily Web Search
TAVILY_API_KEY="tvly-your-key-here"

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"

# Optional: Gemini (for faster inference)
GOOGLE_API_KEY="AIza..."
MODEL_PROVIDER="ollama"  # or "gemini"
```

### 6. Verify Installation

```bash
# Check version
python main.py --version

# List available graphs
python main.py graphs

# Run test query
python main.py run "What is LangGraph?"
```

---

## Directory Structure

After installation, your project should look like:

```
test-smith/
├── .env                    # Environment configuration
├── .venv/                  # Virtual environment
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── src/                    # Source code
│   ├── graphs/             # Workflow definitions
│   ├── nodes/              # Processing nodes
│   ├── prompts/            # LLM prompts
│   └── preprocessor/       # Document preprocessing
├── documents/              # RAG source documents
├── chroma_db/              # Vector database
├── logs/                   # Execution logs
└── reports/                # Generated reports
```

---

## Troubleshooting

### Ollama Won't Start

```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Or restart Ollama app
```

### Model Not Found

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
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TAVILY_API_KEY'))"
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.8+
```

---

## Next Steps

- **[Quick Start](quick-start.md)** - Run your first research query
- **[Model Providers](model-providers.md)** - Configure Ollama or Gemini
- **[RAG Guide](../knowledge-base/rag-guide.md)** - Add documents to the knowledge base
