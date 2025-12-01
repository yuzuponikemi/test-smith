"""
Unit tests for content_cleaner module.

Tests the ContentCleaner class for document cleaning and deduplication.
"""

from langchain_core.documents import Document

from src.preprocessor.content_cleaner import ContentCleaner, clean_documents


class TestContentCleanerInit:
    """Test ContentCleaner initialization."""

    def test_initialization_default(self):
        """Test default initialization."""
        cleaner = ContentCleaner()

        assert cleaner.similarity_threshold == 0.95
        assert cleaner.min_content_length == 50
        assert cleaner.stats["total_input_chunks"] == 0

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        cleaner = ContentCleaner(similarity_threshold=0.90, min_content_length=100)

        assert cleaner.similarity_threshold == 0.90
        assert cleaner.min_content_length == 100


class TestExactDuplicateRemoval:
    """Test exact duplicate detection and removal."""

    def test_remove_exact_duplicates_basic(self):
        """Test removing exact duplicate chunks."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="This is a test"),
            Document(page_content="This is a test"),  # Exact duplicate
            Document(page_content="This is different"),
        ]

        result = cleaner._remove_exact_duplicates(chunks)

        assert len(result) == 2  # Should remove 1 duplicate
        assert cleaner.stats["exact_duplicates_removed"] == 1

    def test_remove_exact_duplicates_all_unique(self):
        """Test with no duplicates."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="Unique A"),
            Document(page_content="Unique B"),
            Document(page_content="Unique C"),
        ]

        result = cleaner._remove_exact_duplicates(chunks)

        assert len(result) == 3  # All kept
        assert cleaner.stats["exact_duplicates_removed"] == 0

    def test_remove_exact_duplicates_all_same(self):
        """Test with all identical chunks."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="Same content"),
            Document(page_content="Same content"),
            Document(page_content="Same content"),
        ]

        result = cleaner._remove_exact_duplicates(chunks)

        assert len(result) == 1  # Only one kept
        assert cleaner.stats["exact_duplicates_removed"] == 2

    def test_remove_exact_duplicates_preserves_metadata(self):
        """Test that metadata is preserved."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="Content", metadata={"source": "doc1.md"}),
            Document(
                page_content="Content", metadata={"source": "doc2.md"}
            ),  # Dup (different meta)
        ]

        result = cleaner._remove_exact_duplicates(chunks)

        assert len(result) == 1
        assert result[0].metadata["source"] == "doc1.md"  # First occurrence kept


class TestNearDuplicateRemoval:
    """Test near-duplicate detection and removal."""

    def test_remove_near_duplicates_high_similarity(self):
        """Test removing near-duplicates with high similarity."""
        cleaner = ContentCleaner(similarity_threshold=0.90)
        chunks = [
            Document(page_content="Python programming language documentation reference"),
            Document(
                page_content="Python programming language documentation referenc"
            ),  # 98%+ similar
            Document(page_content="Completely different content about JavaScript"),
        ]

        result = cleaner._remove_near_duplicates(chunks)

        # Should remove the near-duplicate
        assert len(result) == 2
        assert cleaner.stats["near_duplicates_removed"] == 1

    def test_remove_near_duplicates_low_similarity(self):
        """Test that dissimilar chunks are kept."""
        cleaner = ContentCleaner(similarity_threshold=0.95)
        chunks = [
            Document(page_content="Python is a programming language"),
            Document(page_content="JavaScript is a programming language"),  # Similar but < 95%
            Document(page_content="Rust is a systems programming language"),
        ]

        result = cleaner._remove_near_duplicates(chunks)

        # All should be kept
        assert len(result) == 3
        assert cleaner.stats["near_duplicates_removed"] == 0

    def test_remove_near_duplicates_single_chunk(self):
        """Test with single chunk."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content="Only one chunk")]

        result = cleaner._remove_near_duplicates(chunks)

        assert len(result) == 1
        assert cleaner.stats["near_duplicates_removed"] == 0

    def test_remove_near_duplicates_empty(self):
        """Test with empty list."""
        cleaner = ContentCleaner()
        chunks: list[Document] = []

        result = cleaner._remove_near_duplicates(chunks)

        assert len(result) == 0


class TestSimilarityCalculation:
    """Test similarity calculation."""

    def test_calculate_similarity_identical(self):
        """Test similarity of identical texts."""
        cleaner = ContentCleaner()
        text1 = "This is a test"
        text2 = "This is a test"

        similarity = cleaner._calculate_similarity(text1, text2)

        assert similarity == 1.0

    def test_calculate_similarity_completely_different(self):
        """Test similarity of completely different texts."""
        cleaner = ContentCleaner()
        text1 = "Python programming"
        text2 = "xyz abc def"

        similarity = cleaner._calculate_similarity(text1, text2)

        assert similarity < 0.5

    def test_calculate_similarity_empty_text(self):
        """Test similarity with empty text."""
        cleaner = ContentCleaner()

        assert cleaner._calculate_similarity("", "test") == 0.0
        assert cleaner._calculate_similarity("test", "") == 0.0
        assert cleaner._calculate_similarity("", "") == 0.0

    def test_calculate_similarity_very_different_lengths(self):
        """Test similarity with very different length texts."""
        cleaner = ContentCleaner()
        text1 = "a"
        text2 = "a" * 100  # 100x longer

        similarity = cleaner._calculate_similarity(text1, text2)

        # Length ratio < 0.5, should return 0.0
        assert similarity == 0.0


class TestBoilerplateRemoval:
    """Test boilerplate detection and removal."""

    def test_remove_boilerplate_frequent_content(self):
        """Test removal of frequently appearing content."""
        cleaner = ContentCleaner()
        # Create 10 chunks, where "boilerplate" appears 5 times (50%)
        chunks = [Document(page_content="Boilerplate text")] * 5
        chunks.extend([Document(page_content=f"Unique content {i}") for i in range(5)])

        result = cleaner._remove_boilerplate(chunks)

        # Boilerplate (50% > 20%) should be removed
        assert len(result) == 5  # Only unique content kept
        assert cleaner.stats["boilerplate_removed"] == 5

    def test_remove_boilerplate_no_frequent_content(self):
        """Test with no boilerplate."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content=f"Unique {i}") for i in range(10)]

        result = cleaner._remove_boilerplate(chunks)

        assert len(result) == 10  # All kept
        assert cleaner.stats["boilerplate_removed"] == 0

    def test_remove_boilerplate_threshold_edge_case(self):
        """Test boilerplate threshold (20% rule)."""
        cleaner = ContentCleaner()
        # 20 chunks, one appears 4 times (20%) - just at threshold
        chunks = [Document(page_content="Borderline")] * 4
        chunks.extend([Document(page_content=f"Unique {i}") for i in range(16)])

        result = cleaner._remove_boilerplate(chunks)

        # 4/20 = 20%, which is >= threshold, should be removed
        assert len(result) == 16
        assert cleaner.stats["boilerplate_removed"] == 4


class TestSmallChunkFiltering:
    """Test filtering of small chunks."""

    def test_filter_small_chunks_below_threshold(self):
        """Test removal of chunks below minimum length."""
        cleaner = ContentCleaner(min_content_length=50)
        chunks = [
            Document(page_content="a" * 30),  # Too small
            Document(page_content="b" * 60),  # OK
            Document(page_content="c" * 40),  # Too small
            Document(page_content="d" * 100),  # OK
        ]

        result = cleaner._filter_small_chunks(chunks)

        assert len(result) == 2  # Only 2 above threshold
        assert cleaner.stats["too_small_removed"] == 2

    def test_filter_small_chunks_all_large(self):
        """Test with all chunks above threshold."""
        cleaner = ContentCleaner(min_content_length=50)
        chunks = [Document(page_content="x" * 100) for _ in range(5)]

        result = cleaner._filter_small_chunks(chunks)

        assert len(result) == 5
        assert cleaner.stats["too_small_removed"] == 0

    def test_filter_small_chunks_strips_whitespace(self):
        """Test that whitespace is stripped before length check."""
        cleaner = ContentCleaner(min_content_length=50)
        chunks = [
            Document(page_content="   " + "a" * 30 + "   "),  # 30 chars after strip - too small
            Document(page_content="   " + "b" * 60 + "   "),  # 60 chars after strip - OK
        ]

        result = cleaner._filter_small_chunks(chunks)

        assert len(result) == 1
        assert cleaner.stats["too_small_removed"] == 1


class TestNormalization:
    """Test content normalization."""

    def test_normalize_multiple_spaces(self):
        """Test normalization of multiple spaces."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content="This  has   multiple    spaces")]

        result = cleaner._normalize_chunks(chunks)

        assert result[0].page_content == "This has multiple spaces"

    def test_normalize_multiple_newlines(self):
        """Test normalization of excessive newlines."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content="Line 1\n\n\n\n\nLine 2")]

        result = cleaner._normalize_chunks(chunks)

        # Should reduce to double newline
        assert "\n\n\n\n\n" not in result[0].page_content
        assert "Line 1" in result[0].page_content
        assert "Line 2" in result[0].page_content

    def test_normalize_strips_leading_trailing_whitespace(self):
        """Test stripping of leading/trailing whitespace."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content="   Content with spaces   ")]

        result = cleaner._normalize_chunks(chunks)

        assert result[0].page_content == "Content with spaces"

    def test_normalize_preserves_single_spaces(self):
        """Test that single spaces are preserved."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content="Normal text with single spaces")]

        result = cleaner._normalize_chunks(chunks)

        assert result[0].page_content == "Normal text with single spaces"


class TestCleanAndDeduplicate:
    """Test full cleaning pipeline."""

    def test_clean_and_deduplicate_full_pipeline(self):
        """Test complete cleaning pipeline."""
        cleaner = ContentCleaner(min_content_length=20, similarity_threshold=0.95)
        chunks = [
            Document(page_content="Good content " * 10),  # Good
            Document(page_content="Good content " * 10),  # Exact duplicate
            Document(page_content="Too short"),  # Too small
            Document(page_content="  Needs   normalization  "),  # Needs normalization
        ]

        result = cleaner.clean_and_deduplicate(chunks)

        # Should have: original good content + normalized content
        assert len(result) <= 2
        assert cleaner.stats["total_input_chunks"] == 4
        assert cleaner.stats["exact_duplicates_removed"] >= 1

    def test_clean_and_deduplicate_empty(self):
        """Test with empty input."""
        cleaner = ContentCleaner()
        result = cleaner.clean_and_deduplicate([])

        assert result == []
        assert cleaner.stats["total_input_chunks"] == 0

    def test_clean_and_deduplicate_skip_near_duplicates(self):
        """Test with near-duplicate removal disabled."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="Similar content A" * 10),
            Document(page_content="Similar content B" * 10),  # Near-duplicate
        ]

        result = cleaner.clean_and_deduplicate(chunks, remove_near_duplicates=False)

        # Both should be kept (no near-duplicate removal)
        assert len(result) == 2
        assert cleaner.stats["near_duplicates_removed"] == 0

    def test_clean_and_deduplicate_skip_boilerplate(self):
        """Test with boilerplate removal disabled."""
        cleaner = ContentCleaner(min_content_length=10)  # Low threshold
        chunks = [Document(page_content="Common content " * 10)] * 10

        result = cleaner.clean_and_deduplicate(chunks, remove_boilerplate=False)

        # Should only remove exact duplicates, not boilerplate
        assert len(result) == 1  # Exact duplicates removed
        assert cleaner.stats["boilerplate_removed"] == 0


class TestPatternDetection:
    """Test common pattern detection."""

    def test_detect_common_patterns_urls(self):
        """Test detection of URL patterns."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="Check https://example.com for more"),
            Document(page_content="Visit http://test.org"),
            Document(page_content="No URLs here"),
        ]

        patterns = cleaner.detect_common_patterns(chunks)

        assert patterns["urls"] == 2

    def test_detect_common_patterns_copyright(self):
        """Test detection of copyright patterns."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="© 2024 Company"),
            Document(page_content="Copyright 2024"),
            Document(page_content="No copyright here"),  # Case-insensitive match
        ]

        patterns = cleaner.detect_common_patterns(chunks)

        # Case-insensitive search, so all 3 match
        assert patterns["copyright"] == 3

    def test_detect_common_patterns_doi(self):
        """Test detection of DOI patterns."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="doi.org/10.1234/example"),
            Document(page_content="Regular content"),
        ]

        patterns = cleaner.detect_common_patterns(chunks)

        assert patterns["doi"] == 1


class TestStatistics:
    """Test statistics collection and reporting."""

    def test_get_stats_basic(self):
        """Test basic stats retrieval."""
        cleaner = ContentCleaner()
        chunks = [
            Document(page_content="Content " * 20),
            Document(page_content="Content " * 20),  # Duplicate
        ]

        cleaner.clean_and_deduplicate(chunks)
        stats = cleaner.get_stats()

        assert stats["total_input_chunks"] == 2
        assert stats["total_output_chunks"] >= 1
        assert "removal_rate" in stats

    def test_get_stats_removal_rate(self):
        """Test removal rate calculation."""
        cleaner = ContentCleaner(min_content_length=10)  # Low threshold so chunks aren't filtered
        chunks = [Document(page_content="Same content " * 10)] * 10

        cleaner.clean_and_deduplicate(chunks)
        stats = cleaner.get_stats()

        # 10 input, 1 output (9 duplicates removed)
        expected_rate = 9 / 10
        assert stats["removal_rate"] == expected_rate

    def test_get_stats_no_input(self):
        """Test stats with no input."""
        cleaner = ContentCleaner()
        stats = cleaner.get_stats()

        assert stats["total_input_chunks"] == 0
        assert stats["removal_rate"] == 0.0

    def test_print_stats_smoke_test(self, capsys):
        """Test that print_stats doesn't crash."""
        cleaner = ContentCleaner()
        chunks = [Document(page_content="Test " * 20)]

        cleaner.clean_and_deduplicate(chunks)
        cleaner.print_stats()

        captured = capsys.readouterr()
        assert "CONTENT CLEANING STATISTICS" in captured.out
        assert "Input chunks" in captured.out


class TestConvenienceFunction:
    """Test clean_documents convenience function."""

    def test_clean_documents_basic(self):
        """Test convenience function with default parameters."""
        chunks = [
            Document(page_content="Content " * 30),
            Document(page_content="Content " * 30),  # Duplicate
        ]

        result = clean_documents(chunks)

        assert len(result) == 1  # Duplicate removed

    def test_clean_documents_custom_min_length(self):
        """Test convenience function with custom min_length."""
        chunks = [
            Document(page_content="a" * 50),  # Too small for min_length=100
            Document(page_content="b" * 150),  # OK
        ]

        result = clean_documents(chunks, min_length=100)

        assert len(result) == 1

    def test_clean_documents_disable_near_duplicates(self):
        """Test convenience function with near-duplicate removal disabled."""
        chunks = [
            Document(page_content="Similar A " * 20),
            Document(page_content="Similar B " * 20),
        ]

        result = clean_documents(chunks, remove_near_duplicates=False)

        # Both kept (no near-duplicate removal)
        assert len(result) == 2

    def test_clean_documents_custom_threshold(self):
        """Test convenience function with custom similarity threshold."""
        chunks = [
            Document(page_content="Test content A " * 20),
            Document(page_content="Test content B " * 20),
        ]

        # Lower threshold = more aggressive duplicate removal
        result = clean_documents(chunks, similarity_threshold=0.80)

        # May remove near-duplicates with 80% threshold
        assert len(result) >= 1
