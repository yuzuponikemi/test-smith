# CI/CD Guide

Automated testing and deployment for Test-Smith.

---

## GitHub Actions

### Basic Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run linter
        run: uv run ruff check .
```

---

## Evaluation Workflow

### Automated Evaluation

```yaml
name: Evaluation

on:
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run evaluation
        run: |
          python evaluation/evaluate_agent.py \
            --category regression_test \
            --experiment-name "pr-${{ github.event.pull_request.number }}"
        env:
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
```

### Required Secrets

Configure in repository settings:

- `LANGCHAIN_API_KEY` - LangSmith API key
- `TAVILY_API_KEY` - Tavily API key
- `GOOGLE_API_KEY` (optional) - Gemini API key

---

## Pre-commit Hooks

### Setup

```bash
uv add --dev pre-commit
pre-commit install
```

### Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        args: ['--line-length=120']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black']
```

---

## Environment Variables

### Development

```bash
# .env (local development)
TAVILY_API_KEY="your-key"
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-key"
MODEL_PROVIDER="ollama"
```

### CI/CD

```yaml
env:
  TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
  LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
  MODEL_PROVIDER: "gemini"  # Faster for CI
```

---

## Best Practices

### 1. Use Gemini in CI

Faster evaluation (1-3s vs 10-30s per query):

```yaml
env:
  MODEL_PROVIDER: "gemini"
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

### 2. Limit Test Scope

```yaml
# Fast smoke test
- run: python evaluation/evaluate_agent.py --dry-run --limit 3

# Full test on main
- run: python evaluation/evaluate_agent.py --limit 10
```

### 3. Cache Dependencies

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### 4. Parallel Jobs

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: flake8 src/

  test:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/

  evaluate:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - run: python evaluation/evaluate_agent.py
```

---

## Deployment

### Manual Deployment

```bash
# Tag release
git tag v2.2.0
git push origin v2.2.0
```

### Automated Release

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

---

## Monitoring

### LangSmith Integration

Track evaluation results:

```yaml
- run: |
    python evaluation/evaluate_agent.py \
      --experiment-name "${{ github.sha }}"
```

View at https://smith.langchain.com/

### Notifications

```yaml
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        body: 'Evaluation failed. Check actions log.'
      })
```

---

## Related Documentation

- **[Evaluation Guide](evaluation-guide.md)** - Test framework
- **[Installation](../getting-started/installation.md)** - Setup
