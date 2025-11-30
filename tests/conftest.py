"""Pytest configuration and fixtures for Test-Smith."""

import random
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_random_seeds() -> None:
    """Set random seeds for reproducibility."""
    random.seed(42)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_query() -> str:
    """Provide a sample research query."""
    return "What is the capital of France?"


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "benchmark: marks tests as performance benchmarks")
    config.addinivalue_line("markers", "scientific: marks tests that verify scientific accuracy")
