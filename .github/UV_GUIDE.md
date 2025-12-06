# UV Usage Guide - Test-Smith

This guide explains how to use **uv** for dependency management in the Test-Smith project. UV is a fast, modern Python package manager written in Rust that replaces pip, pip-tools, and virtualenv.

## 📋 Table of Contents

- [Why UV?](#why-uv)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Dependency Management](#dependency-management)
- [Running Commands](#running-commands)
- [CI/CD Integration](#cicd-integration)
- [Migration from pip](#migration-from-pip)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Why UV?

UV provides several advantages over traditional pip:

| Feature | UV | pip |
|---------|-----|-----|
| **Speed** | ⚡ 10-100x faster | 🐌 Slow |
| **Reproducibility** | 🔒 uv.lock file | ⚠️ Requires pip-tools |
| **Dependency Resolution** | 🎯 Advanced resolver | ⚠️ Basic resolver |
| **Caching** | 💾 Global cache | 📦 Per-project cache |
| **Virtual Environments** | ✨ Automatic | 🔧 Manual |

**Performance Example:**
- UV: Install all dependencies in ~5 seconds
- pip: Install all dependencies in ~2 minutes

---

## 📦 Installation

### macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation

```bash
uv --version
```

---

## 🎯 Basic Usage

### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd test-smith

# Create virtual environment and install dependencies
uv sync

# Or install with all extras (dev tools)
uv sync --all-extras
```

**What happens:**
- UV reads `pyproject.toml`
- Creates `.venv/` automatically if it doesn't exist
- Installs all dependencies
- Generates `uv.lock` for reproducibility

### 2. Running Python Code

**✅ Recommended: Use `uv run`**

```bash
# Run main script
uv run python main.py run "Your query"

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run any Python script
uv run python scripts/ingest/ingest_with_preprocessor.py
```

**Why `uv run`?**
- ✅ No need to activate venv manually
- ✅ Automatically uses project's Python version
- ✅ Works in any directory within the project
- ✅ Cleaner CI/CD scripts

**❌ Old way (still works but not recommended):**

```bash
source .venv/bin/activate
python main.py run "Your query"
deactivate
```

---

## 📚 Dependency Management

### Adding Dependencies

```bash
# Add a production dependency
uv add langchain-openai

# Add a development dependency
uv add --dev pytest-asyncio

# Add a specific version
uv add "numpy>=2.0,<3.0"

# Add from git
uv add git+https://github.com/user/repo.git
```

**What happens:**
- Dependency is added to `pyproject.toml`
- `uv.lock` is updated
- Package is installed immediately

### Removing Dependencies

```bash
# Remove a dependency
uv remove langchain-openai

# Remove a dev dependency
uv remove --dev pytest-asyncio
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package langchain

# Sync after update
uv sync
```

### Viewing Dependencies

```bash
# List installed packages
uv pip list

# Show dependency tree
uv tree

# Show outdated packages
uv pip list --outdated
```

---

## 🔧 Running Commands

### Development Workflow

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy src

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_nodes/test_planner_node.py -v
```

### Running Scripts

```bash
# Ingest documents
uv run python scripts/ingest/ingest_with_preprocessor.py

# Test code investigation
uv run python scripts/testing/test_code_investigation.py

# Visualize graphs
uv run python scripts/visualization/visualize_graphs.py
```

### Jupyter Notebooks

```bash
# Launch Jupyter
uv run jupyter notebook

# Or JupyterLab
uv run jupyter lab
```

---

## 🤖 CI/CD Integration

### GitHub Actions

UV is already configured in `.github/workflows/ci.yml` and `.github/workflows/test-graphs.yml`.

**Key steps:**

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"

- name: Set up Python
  run: uv python install 3.11

- name: Install dependencies
  run: uv sync --all-extras

- name: Run tests
  run: uv run pytest
```

**Benefits:**
- ✅ Faster CI builds (cached dependencies)
- ✅ Reproducible builds (uv.lock)
- ✅ Simpler scripts (no venv activation needed)

---

## 🔄 Migration from pip

If you're used to pip, here's the mapping:

| pip Command | UV Equivalent |
|------------|---------------|
| `pip install <package>` | `uv add <package>` |
| `pip install -r requirements.txt` | `uv sync` |
| `pip install -e .` | `uv sync` |
| `pip install -e ".[dev]"` | `uv sync --all-extras` |
| `pip uninstall <package>` | `uv remove <package>` |
| `pip list` | `uv pip list` |
| `pip freeze` | `uv pip freeze` |
| `pip-compile requirements.in` | `uv lock` |
| `python -m venv .venv` | `uv venv` (automatic) |
| `source .venv/bin/activate && python script.py` | `uv run python script.py` |

---

## 🐛 Troubleshooting

### "uv: command not found"

**Solution:** Add UV to your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

### "No Python interpreter found"

**Solution:** Install Python via uv:

```bash
uv python install 3.11
```

### "Lock file out of date"

**Solution:** Regenerate lock file:

```bash
uv lock
uv sync
```

### "Dependency resolution failed"

**Solution:** Check for conflicting versions:

```bash
# Try upgrading packages
uv lock --upgrade

# Or remove the problematic package and re-add it
uv remove <package>
uv add <package>
```

### "Virtual environment not found"

**Solution:** UV creates `.venv/` automatically, but if it's missing:

```bash
uv venv
uv sync
```

### "uv run doesn't find my module"

**Solution:** Make sure you've synced dependencies:

```bash
uv sync
```

---

## 📖 Additional Resources

- **UV Documentation**: https://docs.astral.sh/uv/
- **UV GitHub**: https://github.com/astral-sh/uv
- **pyproject.toml Spec**: https://packaging.python.org/en/latest/specifications/pyproject-toml/

---

## 🎓 Best Practices for Test-Smith

### ✅ DO

- **Always use `uv run`** for running scripts and commands
- **Use `uv sync`** to install dependencies (not `pip install`)
- **Commit `uv.lock`** to version control for reproducibility
- **Use `uv add`** to add new dependencies (updates pyproject.toml automatically)
- **Run `uv lock --upgrade`** periodically to update dependencies

### ❌ DON'T

- Don't use `pip install` directly (breaks uv.lock)
- Don't manually activate `.venv/` (use `uv run` instead)
- Don't edit `requirements.txt` (use `pyproject.toml` instead)
- Don't commit `.venv/` directory to git (it's in .gitignore)

---

## 📝 Example Workflow

Here's a typical development workflow with UV:

```bash
# 1. Clone and setup
git clone <repository-url>
cd test-smith
uv sync --all-extras

# 2. Create a new branch
git checkout -b feature/my-feature

# 3. Make changes to code
# ... edit files ...

# 4. Add a new dependency if needed
uv add langchain-openai

# 5. Run tests locally
uv run ruff check .
uv run ruff format .
uv run mypy src
uv run pytest

# 6. Run the application
uv run python main.py run "Test query"

# 7. Commit changes (including uv.lock if dependencies changed)
git add .
git commit -m "feat: Add new feature"
git push origin feature/my-feature

# 8. Create pull request
# CI will automatically run with UV
```

---

## 🚨 For AI Coding Agents

**IMPORTANT:** When working on this repository:

1. **ALWAYS use `uv run`** for executing Python scripts
2. **NEVER use `pip install`** - use `uv add` instead
3. **NEVER suggest creating requirements.txt** - dependencies are in `pyproject.toml`
4. **ALWAYS run `uv sync`** after pulling changes
5. **ALWAYS commit `uv.lock`** if dependencies change

**Example commands for agents:**

```bash
# ✅ CORRECT
uv run python main.py run "query"
uv add langchain-openai
uv sync

# ❌ INCORRECT
python main.py run "query"
pip install langchain-openai
pip install -r requirements.txt
```

---

## 📞 Need Help?

- Check the [UV troubleshooting guide](https://docs.astral.sh/uv/guides/troubleshooting/)
- Ask in the project's GitHub issues
- Review the [CI configuration](.github/workflows/ci.yml) for examples
