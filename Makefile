.PHONY: help compile install install-dev test lint format typecheck ci clean

# ============================================================================
# Test-Smith Makefile - Task Automation
# ============================================================================

help:  ## Show this help message
	@echo "Test-Smith Development Tasks"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# Dependency Management
# ----------------------------------------------------------------------------

compile:  ## Compile requirements.in to requirements.txt with pinned versions
	@echo "📦 Compiling requirements.in → requirements.txt..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip compile requirements.in -o requirements.txt; \
	elif command -v pip-compile >/dev/null 2>&1; then \
		pip-compile requirements.in -o requirements.txt; \
	else \
		echo "❌ Error: Neither 'uv' nor 'pip-tools' found."; \
		echo "Install one of them:"; \
		echo "  - uv:        curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "  - pip-tools: pip install pip-tools"; \
		exit 1; \
	fi
	@echo "✅ requirements.txt updated"

install:  ## Install production dependencies from requirements.txt
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt
	@echo "✅ Production dependencies installed"

install-dev:  ## Install development dependencies (ruff, mypy, pytest)
	@echo "📦 Installing development dependencies..."
	pip install ruff>=0.3.0 mypy>=1.8.0 pytest>=8.4.2 pytest-cov>=4.1.0
	@echo "✅ Development dependencies installed"

# ----------------------------------------------------------------------------
# Code Quality Checks
# ----------------------------------------------------------------------------

lint:  ## Run ruff linter
	@echo "🔍 Running ruff linter..."
	ruff check .

format:  ## Run ruff formatter
	@echo "🎨 Running ruff formatter..."
	ruff format .

format-check:  ## Check if code is formatted (CI mode)
	@echo "🎨 Checking code formatting..."
	ruff format --check .

typecheck:  ## Run mypy type checker
	@echo "🔍 Running mypy type checker..."
	mypy src

# ----------------------------------------------------------------------------
# Testing
# ----------------------------------------------------------------------------

test:  ## Run pytest with coverage
	@echo "🧪 Running pytest..."
	python -m pytest -v

test-fast:  ## Run pytest without slow tests
	@echo "🧪 Running fast tests only..."
	python -m pytest -v -m "not slow"

test-cov:  ## Run pytest with coverage report
	@echo "🧪 Running pytest with coverage..."
	python -m pytest -v --cov=src --cov-report=term-missing --cov-report=html

# ----------------------------------------------------------------------------
# CI Simulation
# ----------------------------------------------------------------------------

ci:  ## Run all CI checks locally (lint, format, typecheck, test)
	@echo "🚀 Running CI checks locally..."
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "1/4: Ruff Linter"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(MAKE) lint || (echo "❌ Ruff linter failed" && exit 1)
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "2/4: Ruff Formatter"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(MAKE) format-check || (echo "❌ Ruff formatter failed" && exit 1)
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "3/4: Mypy Type Checker"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(MAKE) typecheck || (echo "❌ Mypy type checker failed" && exit 1)
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "4/4: Pytest"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(MAKE) test || (echo "❌ Pytest failed" && exit 1)
	@echo ""
	@echo "✅ All CI checks passed!"

# ----------------------------------------------------------------------------
# Cleanup
# ----------------------------------------------------------------------------

clean:  ## Remove build artifacts and cache files
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-all: clean  ## Remove all generated files including ChromaDB
	@echo "🧹 Deep cleaning (including ChromaDB)..."
	rm -rf chroma_db
	rm -rf dist build
	@echo "✅ Deep cleanup complete"
