# GitHub Workflow and CI/CD Documentation

## Overview

Test-Smith uses **GitHub Actions** for continuous integration and deployment (CI/CD). The system includes two primary workflows that ensure code quality, test graph functionality, and enable AI-assisted development through Claude Code.

**Workflow Files:**
- `.github/workflows/test-graphs.yml` - Automated testing of LangGraph workflows
- `.github/workflows/claude.yml` - Claude Code AI assistant integration

**Key Features:**
- Automated graph compilation and execution testing
- Multi-Python version support (3.10, 3.11, 3.12)
- Gemini API integration for CI testing (avoids Ollama dependency)
- Manual workflow triggers with customizable parameters
- Claude Code integration for issue/PR assistance
- Artifact preservation for debugging

---

## Workflow 1: Graph Testing (`test-graphs.yml`)

### Purpose

Validates that all LangGraph workflows compile correctly and can execute basic queries without requiring local Ollama setup. Uses **Google Gemini API** as the model provider for lightweight, cloud-based testing.

### Trigger Conditions

**Automatic Triggers:**
```yaml
on:
  push:
    branches: [ main, develop, claude/* ]
  pull_request:
    branches: [ main, develop ]
```

**Manual Trigger:**
Via GitHub Actions UI with customizable parameters:
- `graph_type`: Which graph to test (quick_research, deep_research, fact_check, comparative)
- `test_query`: Custom query to execute (default: "What is Python programming language?")
- `run_full_suite`: Run all graphs or just one (default: true)
- `python_version`: Python version to test (3.10, 3.11, 3.12)

### Jobs and Steps

#### Job 1: `test-graph-compilation`

**Runtime:** Ubuntu Latest with Python 3.11 (configurable)

**Steps:**

1. **Checkout code** - Uses `actions/checkout@v4`

2. **Set up Python** - Uses `actions/setup-python@v5` with pip caching

3. **Install system dependencies**
   ```bash
   sudo apt-get install -y sqlite3 libsqlite3-dev
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements-ci.txt
   ```
   Uses lightweight CI requirements (no heavy ML packages like PyTorch/Transformers)

5. **Create .env file**
   ```bash
   MODEL_PROVIDER=gemini
   GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}
   TAVILY_API_KEY=${{ secrets.TAVILY_API_KEY }}
   LANGCHAIN_TRACING_V2=false
   ```

6. **Verify environment setup**
   - Validates critical environment variables
   - Ensures MODEL_PROVIDER, GOOGLE_API_KEY, TAVILY_API_KEY are set

7. **Test graph imports and compilation**
   ```python
   from src.graphs import list_graphs, get_graph, get_default_graph

   # Test each graph can be compiled
   for graph_name in list_graphs().keys():
       graph = get_graph(graph_name)
       assert graph is not None
   ```

8. **Test model initialization**
   - Tests Gemini model initialization for all agents:
     - Planner model
     - Analyzer model
     - Synthesizer model
     - Evaluator model

9. **Run simple test query**
   ```bash
   python main.py run "$TEST_QUERY" --graph "$GRAPH_TYPE"
   ```
   - Executes a full graph workflow
   - Saves output to `test_output.txt`
   - Validates report generation

10. **Test graph listing command**
    ```bash
    python main.py graphs
    python main.py graphs --detailed
    ```

11. **Verify graph structure**
    - Validates deep_research and quick_research graph node structures

12. **Upload test output**
    - Preserves test output as artifact for 7 days
    - Always runs (even on failure) for debugging

#### Job 2: `test-with-tavily-only`

**Runtime:** Ubuntu Latest (only on PRs or manual trigger, NOT on push)

**Purpose:** Tests that Tavily web search integration works independently

**Steps:**
- Checkout code
- Set up Python
- Install dependencies
- Validate TAVILY_API_KEY configuration

---

## Workflow 2: Claude Code Integration (`claude.yml`)

### Purpose

Enables **Claude Code AI assistant** to respond to mentions in GitHub issues, pull requests, and comments. Claude can analyze code, suggest improvements, fix bugs, and assist with development tasks.

### Trigger Conditions

**Event-Based Triggers:**
```yaml
on:
  issue_comment:           # When someone comments on an issue
  pull_request_review_comment:  # When someone comments on PR code
  issues:                  # When issue is opened or assigned
  pull_request_review:     # When PR review is submitted
```

**Activation Condition:**
Claude only runs when `@claude` is mentioned in:
- Issue body or title
- Issue comments
- PR review comments
- PR review body

### Configuration

**Required Permissions:**
```yaml
permissions:
  contents: write        # Modify repository files
  pull-requests: write   # Comment on PRs
  issues: write          # Comment on issues
  id-token: write        # Authentication
  actions: read          # Read CI results
```

**Required Secret:**
- `ANTHROPIC_API_KEY` - API key for Claude Code

### Steps

1. **Checkout repository**
   ```yaml
   uses: actions/checkout@v5
   with:
     fetch-depth: 1
   ```

2. **Run Claude Code**
   ```yaml
   uses: anthropics/claude-code-action@v1
   with:
     anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
   ```

### Optional Customization

**Custom Trigger Phrase:**
```yaml
trigger_phrase: "/claude"  # Instead of @claude
```

**Assignee Trigger:**
```yaml
assignee_trigger: "claude-bot"  # Trigger when user assigned
```

**Claude Arguments:**
```yaml
claude_args: |
  --model claude-opus-4-1-20250805
  --max-turns 10
  --allowedTools "Bash(npm install),Bash(npm run build)"
  --system-prompt "Follow coding standards. Ensure tests."
```

**Advanced Settings:**
```yaml
settings: |
  {
    "env": {
      "NODE_ENV": "test"
    }
  }
```

---

## Required GitHub Secrets

To use these workflows, configure the following secrets in **Settings → Secrets and variables → Actions**:

| Secret Name | Purpose | Used By |
|-------------|---------|---------|
| `GOOGLE_API_KEY` | Google Gemini API for LLM testing | test-graphs.yml |
| `TAVILY_API_KEY` | Web search API for research | test-graphs.yml |
| `ANTHROPIC_API_KEY` | Claude Code AI assistant | claude.yml |

**Setting Secrets:**
1. Navigate to repository Settings
2. Go to Secrets and variables → Actions
3. Click "New repository secret"
4. Add name and value
5. Save

---

## CI Requirements Strategy

### Full Development Environment

**File:** `requirements.txt` (207 packages)

Includes:
- Full ML stack (PyTorch, Transformers, etc.)
- Document processing (Unstructured, OCR)
- Visualization (Jupyter, Matplotlib, Plotly)
- Complete development tools

**Usage:** Local development, full feature testing

### CI Testing Environment

**File:** `requirements-ci.txt` (44 packages)

Includes only:
- Core LangChain/LangGraph packages
- Gemini API integration
- Tavily web search
- ChromaDB (vector store)
- Essential utilities (dotenv, pydantic, typer)
- pytest for testing

**Benefits:**
- **Fast installation:** ~30-40 seconds vs 5-10 minutes
- **Lower bandwidth:** ~50 MB vs 2+ GB
- **Fewer failures:** Fewer dependencies = fewer version conflicts
- **Cost-effective:** Shorter CI run times

### Dependency Management

**Update Process:**
1. Edit `requirements.in` for high-level dependencies
2. Run `pip-compile requirements.in` to generate `requirements.txt`
3. Manually maintain `requirements-ci.txt` with minimal subset
4. Test both files to ensure compatibility

---

## Model Provider Architecture

### Local Development (Ollama)

**Models:**
- `llama3` - Planner, analyzer, synthesizer
- `command-r` - Evaluator
- `nomic-embed-text` - Embeddings

**Configuration (.env):**
```bash
MODEL_PROVIDER=ollama  # or omit (default)
TAVILY_API_KEY=your_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
```

### CI Testing (Gemini)

**Models:**
- `gemini-1.5-flash` - All agents (configurable in `src/models.py`)

**Configuration (.env - CI):**
```bash
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}
TAVILY_API_KEY=${{ secrets.TAVILY_API_KEY }}
LANGCHAIN_TRACING_V2=false
```

**Why Gemini for CI?**
- No local model installation required
- Faster startup time
- Cloud-based (no memory constraints)
- Cost-effective for testing
- Easy to configure in GitHub Actions

---

## Running Workflows Manually

### Test Graphs Workflow

1. **Navigate to Actions tab** in GitHub
2. **Select "Test Graphs with Gemini"** workflow
3. **Click "Run workflow"** dropdown
4. **Configure parameters:**
   - Branch: Select branch to test
   - Graph workflow to test: Choose graph type
   - Custom test query: Enter query (or use default)
   - Run full test suite: Enable/disable
   - Python version: Select version
5. **Click green "Run workflow"** button
6. **Monitor progress** in real-time
7. **Download artifacts** (test_output.txt) after completion

### Claude Code Workflow

**Cannot be triggered manually** - event-driven only

**To trigger:**
1. Create/open an issue
2. Mention `@claude` in title, body, or comment
3. Wait for workflow to start (usually <30 seconds)
4. Claude will respond with analysis/code/suggestions

---

## Workflow Outputs and Artifacts

### Test Graphs Workflow

**Console Output:**
- Graph compilation status for each graph
- Model initialization confirmation
- Test query execution results
- Graph listing output
- Structure verification results

**Artifacts (retained 7 days):**
- `test-output/test_output.txt` - Full test execution log

**Access Artifacts:**
1. Go to workflow run
2. Scroll to bottom
3. Click "test-output" under Artifacts
4. Download ZIP file

### Claude Code Workflow

**Output:**
- Comments on issues/PRs with Claude's analysis
- Code suggestions or modifications
- Links to relevant documentation
- Explanations of errors/bugs

---

## Best Practices

### For Contributors

1. **Test locally first**
   ```bash
   python main.py run "test query" --graph quick_research
   python main.py graphs --detailed
   ```

2. **Use meaningful branch names**
   - `feature/add-new-graph`
   - `fix/planner-bug`
   - `claude/*` branches auto-trigger CI

3. **Write descriptive commit messages**
   - CI runs on every push to main/develop
   - Clear messages help debug CI failures

4. **Check CI status before merging**
   - Green checkmark = all tests passed
   - Red X = investigate failures
   - Download artifacts for debugging

### For Maintainers

1. **Monitor secret expiration**
   - Gemini API keys may have quotas
   - Tavily API keys may expire
   - Anthropic API keys require active subscription

2. **Update dependencies regularly**
   ```bash
   pip-compile requirements.in
   # Manually sync core deps to requirements-ci.txt
   ```

3. **Review Claude Code suggestions**
   - Claude's code is not automatically merged
   - Review changes before accepting
   - Claude respects repository permissions

4. **Adjust workflow timeouts if needed**
   - Default GitHub Actions timeout: 6 hours
   - Graph tests typically complete in 2-5 minutes
   - Long-running tests may indicate issues

### For Using Claude Code

1. **Be specific in requests**
   - Good: "@claude fix the planner allocation bug in src/nodes/planner_node.py"
   - Bad: "@claude help"

2. **Provide context**
   - Reference specific files, line numbers, error messages
   - Link to related issues/PRs
   - Include example inputs/outputs

3. **Ask follow-up questions**
   - Claude maintains conversation context
   - Can iterate on solutions
   - Can explain reasoning

4. **Review before merging**
   - Claude is an assistant, not a replacement for code review
   - Validate logic, security, performance
   - Run local tests before merging

---

## Troubleshooting

### Graph Compilation Failures

**Symptom:** `assert graph is not None` fails

**Causes:**
- Missing dependencies in `requirements-ci.txt`
- Import errors in graph files
- State schema mismatches

**Solution:**
1. Check workflow logs for import errors
2. Verify all graph dependencies in `requirements-ci.txt`
3. Test locally: `python -c "from src.graphs import get_graph; get_graph('deep_research')"`

### Model Initialization Failures

**Symptom:** `model is None` assertion fails

**Causes:**
- `GOOGLE_API_KEY` secret not set
- Invalid API key
- Gemini API quota exceeded

**Solution:**
1. Verify secret exists in repository settings
2. Test API key validity manually
3. Check Google Cloud console for quota limits
4. Consider rate limiting in workflow

### Test Query Execution Failures

**Symptom:** Test output is empty or incomplete

**Causes:**
- `TAVILY_API_KEY` missing or invalid
- Network issues in GitHub Actions
- Query timeout

**Solution:**
1. Verify Tavily API key secret
2. Check Tavily API status
3. Try simpler test query
4. Increase timeout in workflow file

### Claude Code Not Responding

**Symptom:** Mentioning `@claude` doesn't trigger workflow

**Causes:**
- `ANTHROPIC_API_KEY` secret not set
- Workflow file syntax error
- Permissions insufficient

**Solution:**
1. Verify secret exists
2. Check workflow file for YAML errors
3. Ensure workflow has required permissions
4. Check GitHub Actions logs for errors

### CI Requirements Out of Sync

**Symptom:** Local code works but CI fails with import errors

**Causes:**
- New dependency added to code but not `requirements-ci.txt`
- Version mismatch between requirements files

**Solution:**
1. Add missing dependency to `requirements-ci.txt`
2. Match versions with `requirements.txt`
3. Test CI requirements locally:
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install -r requirements-ci.txt
   python main.py graphs
   ```

---

## Extending the CI/CD System

### Adding a New Graph Test

**Edit `.github/workflows/test-graphs.yml`:**

1. **Add to manual trigger options:**
   ```yaml
   graph_type:
     options:
       - quick_research
       - deep_research
       - fact_check
       - comparative
       - my_new_graph  # Add here
   ```

2. **Graph auto-detected by existing test:**
   ```python
   # Already tests all graphs in list_graphs()
   for graph_name in list_graphs().keys():
       graph = get_graph(graph_name)
   ```

3. **Register graph in `src/graphs/__init__.py`:**
   ```python
   from src.graphs.my_new_graph import MyNewGraphBuilder

   def _auto_register_graphs():
       register_graph("my_new_graph", MyNewGraphBuilder())
   ```

### Adding Custom Validation Steps

**Example: Validate RAG retrieval works**

Add step to `.github/workflows/test-graphs.yml`:

```yaml
- name: Test RAG retrieval
  run: |
    echo "Testing RAG retrieval functionality..."
    python -c "
    from src.nodes.rag_retriever_node import rag_retriever

    # Mock state
    state = {
        'rag_queries': ['test query'],
        'rag_results': []
    }

    # Note: Will fail in CI without ingested data
    # This is a compilation/import test only
    print('✓ RAG retriever imported successfully')
    "
```

### Adding Performance Benchmarks

**Example: Measure graph execution time**

```yaml
- name: Benchmark graph performance
  run: |
    echo "Running performance benchmarks..."
    python -c "
    import time
    from src.graphs import get_graph

    start = time.time()
    graph = get_graph('quick_research')
    compile_time = time.time() - start

    assert compile_time < 5.0, f'Compilation too slow: {compile_time}s'
    print(f'✓ Graph compiled in {compile_time:.2f}s')
    "
```

### Adding Code Quality Checks

**Example: Add linting/formatting**

```yaml
- name: Run code quality checks
  run: |
    pip install black flake8 mypy

    # Format check
    black --check src/

    # Linting
    flake8 src/ --max-line-length=100

    # Type checking
    mypy src/ --ignore-missing-imports
```

---

## Security Considerations

### Secret Management

**Best Practices:**
- ✅ Use GitHub Secrets (encrypted at rest)
- ✅ Never commit secrets to repository
- ✅ Rotate secrets regularly
- ✅ Use minimal permissions for API keys
- ❌ Don't print secrets in logs
- ❌ Don't expose secrets in artifacts

**Current .env Handling:**
- `.env` file created dynamically in CI
- Not committed to repository
- Loaded via `python-dotenv`
- Secrets injected from GitHub Secrets

### Workflow Permissions

**Principle of Least Privilege:**

```yaml
permissions:
  contents: write        # Only if modifying files
  pull-requests: write   # Only if commenting on PRs
  issues: write          # Only if commenting on issues
  id-token: write        # For OIDC authentication
  actions: read          # For reading workflow results
```

**Review Regularly:**
- Audit who has access to repository secrets
- Review workflow permissions quarterly
- Disable unused workflows

### Dependency Security

**Automated Updates:**
- Consider Dependabot for security updates
- Pin exact versions in requirements files
- Review changelogs before updating

**Vulnerability Scanning:**
```bash
pip install safety
safety check -r requirements.txt
```

**Add to CI:**
```yaml
- name: Security scan
  run: |
    pip install safety
    safety check -r requirements-ci.txt
```

---

## Monitoring and Observability

### GitHub Actions Dashboard

**View Workflow Status:**
1. Go to repository → Actions tab
2. See all workflow runs with status
3. Filter by workflow, branch, actor
4. View trends over time

**Key Metrics:**
- Success rate (should be >95%)
- Average duration (2-5 minutes for graph tests)
- Failure patterns (specific tests failing repeatedly)

### LangSmith Integration

**Disabled in CI by default** to reduce costs and complexity:

```bash
LANGCHAIN_TRACING_V2=false
```

**To enable for debugging:**

```yaml
- name: Create .env file
  run: |
    cat > .env << EOF
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=${{ secrets.LANGCHAIN_API_KEY }}
    LANGCHAIN_PROJECT=ci-testing
    EOF
```

**Benefits:**
- Detailed execution traces
- Token usage tracking
- Performance metrics per node
- Error analysis

### Notification Setup

**GitHub Actions Notifications:**
- Configure in Settings → Notifications
- Email on workflow failure
- Slack/Discord webhooks available

**Example Slack Notification:**

```yaml
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "❌ Graph tests failed on ${{ github.ref }}"
      }
```

---

## Performance Optimization

### Caching Strategies

**Current Caching:**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    cache: 'pip'  # Caches pip dependencies
```

**Advanced Caching:**

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements-ci.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- name: Cache ChromaDB
  uses: actions/cache@v4
  with:
    path: chroma_db/
    key: ${{ runner.os }}-chroma-${{ hashFiles('documents/**') }}
```

**Benefits:**
- Faster dependency installation (2-5x speedup)
- Reduced bandwidth usage
- Lower costs

### Parallel Testing

**Current Setup:** Sequential jobs

**Optimization:** Matrix strategy for parallel testing

```yaml
strategy:
  matrix:
    graph: [quick_research, deep_research, fact_check, comparative]
    python-version: ['3.10', '3.11', '3.12']

steps:
  - name: Test ${{ matrix.graph }} on Python ${{ matrix.python-version }}
    run: |
      python main.py run "test" --graph ${{ matrix.graph }}
```

**Benefits:**
- Test all graphs simultaneously
- Multi-version testing
- Faster feedback

**Tradeoff:**
- Higher concurrent runner usage
- May hit API rate limits
- More complex configuration

---

## Migration Guide

### From Ollama-Only to Gemini CI

**Completed in recent commits:**
1. ✅ Added `MODEL_PROVIDER` environment variable
2. ✅ Created `src/models.py` with provider switching
3. ✅ Updated workflows to use Gemini
4. ✅ Created `requirements-ci.txt` with minimal deps
5. ✅ Removed Ollama setup from CI

**If you have old workflows:**

```diff
- - name: Install Ollama
-   run: |
-     curl -fsSL https://ollama.com/install.sh | sh
-     ollama pull llama3

+ - name: Create .env file
+   run: |
+     echo "MODEL_PROVIDER=gemini" >> .env
+     echo "GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}" >> .env
```

### Adding Test Coverage

**Current Status:** No pytest tests written

**Recommended Approach:**

1. **Create `tests/` directory:**
   ```bash
   mkdir -p tests/unit tests/integration
   ```

2. **Add unit tests for nodes:**
   ```python
   # tests/unit/test_planner.py
   def test_planner_output_structure():
       from src.schemas import StrategicPlan
       # Test StrategicPlan schema validation
   ```

3. **Add integration tests for graphs:**
   ```python
   # tests/integration/test_graphs.py
   def test_quick_research_compilation():
       from src.graphs import get_graph
       graph = get_graph('quick_research')
       assert graph is not None
   ```

4. **Update workflow:**
   ```yaml
   - name: Run pytest
     run: |
       pytest tests/ -v --cov=src --cov-report=xml

   - name: Upload coverage
     uses: codecov/codecov-action@v4
     with:
       file: ./coverage.xml
   ```

---

## Conclusion

The Test-Smith CI/CD system provides:

✅ **Automated Testing** - Every push validated
✅ **Multi-Environment Support** - Gemini (CI) + Ollama (local)
✅ **AI-Powered Assistance** - Claude Code integration
✅ **Flexible Execution** - Manual triggers with parameters
✅ **Cost-Effective** - Minimal dependencies for CI
✅ **Developer-Friendly** - Clear outputs, downloadable artifacts

**Next Steps:**
1. Set up required secrets in repository settings
2. Test workflows on feature branch
3. Review artifacts and outputs
4. Consider adding test coverage
5. Customize Claude Code for your workflow

**Resources:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

**Questions?** Open an issue and mention `@claude` for assistance!
