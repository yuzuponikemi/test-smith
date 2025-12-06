.PHONY: help install install-dev sync test lint format typecheck ci clean

# ============================================================================
# Test-Smith Makefile - UV-based Task Automation
# ============================================================================

help:  ## Show this help message
	@echo "Test-Smith Development Tasks (UV-based)"
	@echo "========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# Dependency Management (UV)
# ----------------------------------------------------------------------------

sync:  ## Sync dependencies from pyproject.toml (UV)
	@echo "📦 Syncing dependencies with UV..."
	uv sync --all-extras
	@echo "✅ Dependencies synced"

install: sync  ## Install all dependencies (alias for sync)

install-dev: sync  ## Install development dependencies (alias for sync)

lock:  ## Update uv.lock file
	@echo "🔒 Updating uv.lock..."
	uv lock --upgrade
	@echo "✅ Lock file updated"

# ----------------------------------------------------------------------------
# Code Quality Checks
# ----------------------------------------------------------------------------

lint:  ## Run ruff linter
	@echo "🔍 Running ruff linter..."
	uv run ruff check .

format:  ## Run ruff formatter
	@echo "🎨 Running ruff formatter..."
	uv run ruff format .

format-check:  ## Check if code is formatted (CI mode)
	@echo "🎨 Checking code formatting..."
	uv run ruff format --check .

typecheck:  ## Run mypy type checker
	@echo "🔍 Running mypy type checker..."
	uv run mypy src --no-error-summary

# ----------------------------------------------------------------------------
# Testing
# ----------------------------------------------------------------------------

test:  ## Run pytest with coverage
	@echo "🧪 Running pytest..."
	uv run pytest -v

test-fast:  ## Run pytest without slow tests
	@echo "🧪 Running fast tests only..."
	uv run pytest -v -m "not slow and not requires_api"

test-cov:  ## Run pytest with coverage report
	@echo "🧪 Running pytest with coverage..."
	uv run pytest -v --cov=src --cov-report=term-missing --cov-report=html

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
# Application
# ----------------------------------------------------------------------------

run:  ## Run the application (usage: make run QUERY="your question")
	@if [ -z "$(QUERY)" ]; then \
		echo "Usage: make run QUERY=\"your question\""; \
		exit 1; \
	fi
	uv run python main.py run "$(QUERY)"

graphs:  ## List available graph workflows
	@echo "📊 Available graph workflows:"
	uv run python main.py graphs

# ----------------------------------------------------------------------------
# Knowledge Base
# ----------------------------------------------------------------------------

ingest:  ## Ingest documents into knowledge base
	@echo "📚 Ingesting documents..."
	uv run python scripts/ingest/ingest_with_preprocessor.py

ingest-diagnostic:  ## Run diagnostic ingestion
	@echo "🔬 Running diagnostic ingestion..."
	uv run python scripts/ingest/ingest_diagnostic.py

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
