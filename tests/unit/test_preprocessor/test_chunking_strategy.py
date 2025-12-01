"""
Unit tests for chunking_strategy module.

Tests the ChunkingStrategy class for intelligent chunk size selection.
"""

import pytest
from langchain_core.documents import Document

from src.preprocessor.chunking_strategy import (
    ChunkingConfig,
    ChunkingMethod,
    ChunkingStrategy,
    select_chunking_strategy,
)


class TestChunkingConfig:
    """Test ChunkingConfig dataclass."""

    def test_chunking_config_creation(self):
        """Test basic ChunkingConfig creation."""
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100,
        )

        assert config.method == ChunkingMethod.RECURSIVE
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.min_chunk_size == 100

    def test_chunking_config_with_separators(self):
        """Test ChunkingConfig with custom separators."""
        separators = ["\n\n", "\n", " "]
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=500,
            chunk_overlap=100,
            separators=separators,
        )

        assert config.separators == separators

    def test_chunking_config_with_headers(self):
        """Test ChunkingConfig with markdown headers."""
        headers = [("#", "h1"), ("##", "h2")]
        config = ChunkingConfig(
            method=ChunkingMethod.MARKDOWN_HEADERS,
            chunk_size=1500,
            chunk_overlap=300,
            headers_to_split_on=headers,
        )

        assert config.headers_to_split_on == headers


class TestChunkingStrategy:
    """Test ChunkingStrategy class."""

    def test_initialization(self):
        """Test ChunkingStrategy initializes correctly."""
        strategy = ChunkingStrategy()

        assert strategy.stats["total_documents"] == 0
        assert strategy.stats["total_chunks"] == 0
        assert strategy.stats["filtered_small_chunks"] == 0
        assert strategy.stats["chunks_by_method"] == {}

    def test_select_config_markdown(self):
        """Test config selection for markdown files."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="markdown",
            file_size=10000,
            has_complex_structure=True,  # Required for MARKDOWN_HEADERS method
        )

        assert config.method == ChunkingMethod.MARKDOWN_HEADERS
        assert config.headers_to_split_on is not None

    def test_select_config_pdf(self):
        """Test config selection for PDF files."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="pdf",
            file_size=50000,
        )

        assert config.method == ChunkingMethod.RECURSIVE
        assert config.separators is not None

    def test_select_config_plain_text(self):
        """Test config selection for plain text files."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="plain_text",
            file_size=5000,
        )

        assert config.method == ChunkingMethod.RECURSIVE

    def test_select_config_code_python(self):
        """Test config selection for Python code."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="code",
            file_size=10000,
            programming_language="python",
        )

        assert config.method == ChunkingMethod.CODE_AWARE
        assert config.separators is not None
        assert "class " in str(config.separators)  # Python-specific separators

    def test_select_config_code_javascript(self):
        """Test config selection for JavaScript code."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="code",
            file_size=8000,
            programming_language="javascript",
        )

        assert config.method == ChunkingMethod.CODE_AWARE
        assert "function " in str(config.separators)

    def test_select_config_code_csharp(self):
        """Test config selection for C# code."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="code",
            file_size=12000,
            programming_language="csharp",
        )

        assert config.method == ChunkingMethod.CODE_AWARE
        assert "namespace " in str(config.separators)

    def test_select_config_japanese_language(self):
        """Test config adjustment for Japanese language."""
        strategy = ChunkingStrategy()

        english_config = strategy.select_config(
            structure_type="plain_text",
            file_size=10000,
            language="english",
        )

        japanese_config = strategy.select_config(
            structure_type="plain_text",
            file_size=10000,
            language="japanese",
        )

        # Japanese should have larger chunk size
        assert japanese_config.chunk_size > english_config.chunk_size

    def test_select_config_large_file(self):
        """Test config adjustment for large files."""
        strategy = ChunkingStrategy()

        small_config = strategy.select_config(
            structure_type="plain_text",
            file_size=10000,  # 10KB
        )

        large_config = strategy.select_config(
            structure_type="plain_text",
            file_size=2 * 1024 * 1024,  # 2MB
        )

        # Large files should have larger chunk size
        assert large_config.chunk_size > small_config.chunk_size
        assert large_config.metadata.get("large_file") is True

    def test_select_config_fallback_to_default(self):
        """Test fallback to plain_text config for unknown types."""
        strategy = ChunkingStrategy()

        config = strategy.select_config(
            structure_type="unknown_type",
            file_size=5000,
        )

        # Should fall back to plain_text config
        assert config.method == ChunkingMethod.RECURSIVE


class TestChunkDocuments:
    """Test document chunking functionality."""

    def test_chunk_documents_empty_list(self):
        """Test chunking with empty document list."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=500,
            chunk_overlap=100,
        )

        result = strategy.chunk_documents([], config)

        assert result == []
        assert strategy.stats["total_documents"] == 0

    def test_chunk_documents_recursive(self):
        """Test recursive chunking."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=100,  # Small size to force splitting
            chunk_overlap=20,
            min_chunk_size=50,
        )

        # Create a document longer than chunk_size
        documents = [Document(page_content="a" * 300)]

        result = strategy.chunk_documents(documents, config)

        assert len(result) > 1  # Should be split into multiple chunks
        assert strategy.stats["total_documents"] == 1
        assert strategy.stats["total_chunks"] > 1

    def test_chunk_documents_filters_small_chunks(self):
        """Test that small chunks are filtered out."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=50,
            chunk_overlap=10,
            min_chunk_size=30,  # Minimum size
        )

        # Create mixed content
        documents = [
            Document(page_content="Very long content that will be chunked properly " * 10),
        ]

        result = strategy.chunk_documents(documents, config)

        # All chunks should be >= min_chunk_size
        for chunk in result:
            assert len(chunk.page_content) >= config.min_chunk_size

    def test_chunk_documents_adds_metadata(self):
        """Test that chunking adds metadata to chunks."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1000,
            chunk_overlap=200,
        )

        documents = [Document(page_content="Test content " * 50)]

        result = strategy.chunk_documents(documents, config, source="test.txt")

        # Check metadata was added
        for chunk in result:
            assert "chunking_method" in chunk.metadata
            assert chunk.metadata["chunking_method"] == "recursive"
            assert chunk.metadata["chunk_size_config"] == 1000
            assert chunk.metadata["source"] == "test.txt"

    def test_chunk_documents_updates_stats(self):
        """Test that stats are updated correctly."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=200,
            chunk_overlap=50,
            min_chunk_size=50,
        )

        documents = [
            Document(page_content="a" * 500),
            Document(page_content="b" * 500),
        ]

        result = strategy.chunk_documents(documents, config)

        assert strategy.stats["total_documents"] == 2
        assert strategy.stats["total_chunks"] == len(result)
        assert "recursive" in strategy.stats["chunks_by_method"]

    def test_chunk_documents_code_aware(self):
        """Test code-aware chunking."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.CODE_AWARE,
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50,
            separators=["\n\nclass ", "\n\ndef ", "\n\n", "\n"],
            metadata={"programming_language": "python"},
        )

        python_code = """
class MyClass:
    def method1(self):
        pass

def function1():
    pass

class AnotherClass:
    def method2(self):
        pass
"""

        documents = [Document(page_content=python_code)]
        result = strategy.chunk_documents(documents, config)

        # Should preserve metadata
        for chunk in result:
            assert chunk.metadata.get("programming_language") == "python"


class TestMarkdownHeaderChunking:
    """Test markdown header-based chunking."""

    def test_chunk_with_markdown_headers(self):
        """Test chunking using markdown headers."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.MARKDOWN_HEADERS,
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=10,  # Low threshold to avoid filtering
            headers_to_split_on=[("#", "h1"), ("##", "h2")],
        )

        markdown_content = """# Main Title

This is the introduction with enough content to meet minimum requirements.

## Section 1

Content for section 1 with additional text to ensure it's not too small.

## Section 2

Content for section 2 with more text to pass the minimum threshold.
"""

        documents = [Document(page_content=markdown_content)]
        result = strategy.chunk_documents(documents, config)

        # Should create chunks based on headers (or at least not be empty)
        assert len(result) >= 1

    def test_chunk_hybrid_fallback(self):
        """Test hybrid chunking falls back to recursive."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.HYBRID,
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50,
        )

        # Plain text without markdown headers
        documents = [Document(page_content="Plain text content " * 50)]

        result = strategy.chunk_documents(documents, config)

        # Should still work (fallback to recursive)
        assert len(result) > 0


class TestStatistics:
    """Test statistics collection."""

    def test_get_stats(self):
        """Test getting statistics."""
        strategy = ChunkingStrategy()
        strategy.stats["total_documents"] = 5
        strategy.stats["total_chunks"] = 20

        stats = strategy.get_stats()

        assert stats["total_documents"] == 5
        assert stats["total_chunks"] == 20
        # Should return a copy
        assert stats is not strategy.stats

    def test_print_stats_smoke_test(self, capsys):
        """Test that print_stats doesn't crash."""
        strategy = ChunkingStrategy()
        config = ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=500,
            chunk_overlap=100,
        )

        documents = [Document(page_content="Test " * 100)]
        strategy.chunk_documents(documents, config)

        strategy.print_stats()

        captured = capsys.readouterr()
        assert "CHUNKING STATISTICS" in captured.out
        assert "Documents processed" in captured.out


class TestConvenienceFunction:
    """Test select_chunking_strategy convenience function."""

    def test_select_chunking_strategy_markdown(self):
        """Test convenience function for markdown."""
        config = select_chunking_strategy(
            structure_type="markdown",
            file_size=10000,
            has_complex_structure=True,  # Required for MARKDOWN_HEADERS
        )

        assert isinstance(config, ChunkingConfig)
        assert config.method == ChunkingMethod.MARKDOWN_HEADERS

    def test_select_chunking_strategy_code(self):
        """Test convenience function for code."""
        config = select_chunking_strategy(
            structure_type="code",
            file_size=5000,
            programming_language="python",
        )

        assert config.method == ChunkingMethod.CODE_AWARE
        assert config.metadata.get("programming_language") == "python"

    def test_select_chunking_strategy_japanese(self):
        """Test convenience function with Japanese language."""
        english_config = select_chunking_strategy(
            structure_type="plain_text",
            file_size=10000,
            language="english",
        )

        japanese_config = select_chunking_strategy(
            structure_type="plain_text",
            file_size=10000,
            language="japanese",
        )

        # Japanese should have larger chunk size
        assert japanese_config.chunk_size > english_config.chunk_size

    def test_select_chunking_strategy_large_file(self):
        """Test convenience function with large file."""
        config = select_chunking_strategy(
            structure_type="plain_text",
            file_size=2 * 1024 * 1024,  # 2MB
        )

        assert config.metadata.get("large_file") is True
        assert config.chunk_size >= 1000  # Should have increased chunk size


class TestCodeSeparators:
    """Test language-specific code separators."""

    def test_python_separators_present(self):
        """Test that Python separators are defined."""
        strategy = ChunkingStrategy()

        assert "python" in strategy.CODE_SEPARATORS
        assert "\n\nclass " in strategy.CODE_SEPARATORS["python"]
        assert "\n\ndef " in strategy.CODE_SEPARATORS["python"]

    def test_javascript_separators_present(self):
        """Test that JavaScript separators are defined."""
        strategy = ChunkingStrategy()

        assert "javascript" in strategy.CODE_SEPARATORS
        assert "\n\nfunction " in strategy.CODE_SEPARATORS["javascript"]

    def test_csharp_separators_present(self):
        """Test that C# separators are defined."""
        strategy = ChunkingStrategy()

        assert "csharp" in strategy.CODE_SEPARATORS
        assert "\n\nnamespace " in strategy.CODE_SEPARATORS["csharp"]
        assert "\n\npublic class " in strategy.CODE_SEPARATORS["csharp"]

    def test_default_separators_fallback(self):
        """Test fallback to default separators."""
        strategy = ChunkingStrategy()

        assert "default" in strategy.CODE_SEPARATORS
        assert len(strategy.CODE_SEPARATORS["default"]) > 0
