"""
Unit tests for quality_metrics module.

Tests the QualityMetrics class for calculating document quality metrics.
"""

import pytest
from langchain_core.documents import Document

from src.preprocessor.quality_metrics import QualityMetrics


class TestQualityMetrics:
    """Test QualityMetrics class initialization and basic functionality."""

    def test_initialization(self):
        """Test QualityMetrics initializes correctly."""
        qm = QualityMetrics()
        assert qm.metrics == {}

    def test_calculate_metrics_empty_chunks(self):
        """Test metrics calculation with empty chunk list."""
        qm = QualityMetrics()
        result = qm.calculate_metrics([])

        assert result["status"] == "no_chunks"
        assert result["total_chunks"] == 0

    def test_calculate_metrics_single_chunk(self):
        """Test metrics calculation with single chunk."""
        qm = QualityMetrics()
        chunks = [Document(page_content="This is a test chunk with some content.")]

        result = qm.calculate_metrics(chunks)

        assert result["total_chunks"] == 1
        assert result["mean_chunk_size"] > 0
        assert result["median_chunk_size"] > 0
        assert "quality_score" in result
        assert "quality_grade" in result

    def test_calculate_metrics_multiple_chunks(self):
        """Test metrics calculation with multiple chunks."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="First chunk with some content. " * 10),
            Document(page_content="Second chunk with different content. " * 10),
            Document(page_content="Third chunk with more words here. " * 10),
        ]

        result = qm.calculate_metrics(chunks)

        assert result["total_chunks"] == 3
        assert result["mean_chunk_size"] > 0
        assert result["std_chunk_size"] >= 0
        assert 0.0 <= result["quality_score"] <= 1.0


class TestSizeDistribution:
    """Test chunk size distribution calculation."""

    def test_size_distribution_very_small_chunks(self):
        """Test distribution for very small chunks (<100 chars)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Small"),  # <100
            Document(page_content="Tiny"),  # <100
            Document(page_content="Short"),  # <100
        ]

        result = qm.calculate_metrics(chunks)
        dist = result["size_distribution"]

        assert dist["very_small"] == 3
        assert dist["small"] == 0
        assert dist["medium"] == 0
        assert dist["large"] == 0
        assert dist["very_large"] == 0

    def test_size_distribution_small_chunks(self):
        """Test distribution for small chunks (100-500 chars)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="a" * 150),  # 150 chars
            Document(page_content="b" * 300),  # 300 chars
            Document(page_content="c" * 450),  # 450 chars
        ]

        result = qm.calculate_metrics(chunks)
        dist = result["size_distribution"]

        assert dist["very_small"] == 0
        assert dist["small"] == 3
        assert dist["medium"] == 0

    def test_size_distribution_medium_chunks(self):
        """Test distribution for medium chunks (500-1000 chars)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="x" * 600),
            Document(page_content="y" * 800),
            Document(page_content="z" * 950),
        ]

        result = qm.calculate_metrics(chunks)
        dist = result["size_distribution"]

        assert dist["medium"] == 3
        assert dist["small"] == 0
        assert dist["large"] == 0

    def test_size_distribution_large_chunks(self):
        """Test distribution for large chunks (1000-1500 chars)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="a" * 1100),
            Document(page_content="b" * 1400),
        ]

        result = qm.calculate_metrics(chunks)
        dist = result["size_distribution"]

        assert dist["large"] == 2
        assert dist["medium"] == 0
        assert dist["very_large"] == 0

    def test_size_distribution_very_large_chunks(self):
        """Test distribution for very large chunks (>1500 chars)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="x" * 2000),
            Document(page_content="y" * 3000),
        ]

        result = qm.calculate_metrics(chunks)
        dist = result["size_distribution"]

        assert dist["very_large"] == 2
        assert dist["large"] == 0

    def test_size_distribution_mixed(self):
        """Test distribution with mixed chunk sizes."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="a" * 50),  # very_small
            Document(page_content="b" * 200),  # small
            Document(page_content="c" * 700),  # medium
            Document(page_content="d" * 1200),  # large
            Document(page_content="e" * 2000),  # very_large
        ]

        result = qm.calculate_metrics(chunks)
        dist = result["size_distribution"]

        assert dist["very_small"] == 1
        assert dist["small"] == 1
        assert dist["medium"] == 1
        assert dist["large"] == 1
        assert dist["very_large"] == 1


class TestDiversityMetrics:
    """Test content diversity metrics calculation."""

    def test_diversity_all_unique(self):
        """Test diversity with all unique chunks."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Unique content A"),
            Document(page_content="Unique content B"),
            Document(page_content="Unique content C"),
        ]

        result = qm.calculate_metrics(chunks)

        assert result["uniqueness_ratio"] == 1.0  # All unique
        assert result["total_vocabulary_size"] > 0
        assert result["vocabulary_diversity"] > 0

    def test_diversity_with_duplicates(self):
        """Test diversity with duplicate chunks."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Same content"),
            Document(page_content="Same content"),  # Duplicate
            Document(page_content="Different content"),
        ]

        result = qm.calculate_metrics(chunks)

        # 2 unique out of 3 total = 0.666...
        assert result["uniqueness_ratio"] < 1.0
        assert result["uniqueness_ratio"] > 0.5

    def test_diversity_all_identical(self):
        """Test diversity with all identical chunks."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Same content"),
            Document(page_content="Same content"),
            Document(page_content="Same content"),
        ]

        result = qm.calculate_metrics(chunks)

        # Only 1 unique out of 3 total
        assert result["uniqueness_ratio"] == 1 / 3

    def test_vocabulary_diversity_high(self):
        """Test high vocabulary diversity (many unique words)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="apple banana cherry date elderberry"),
            Document(page_content="fig grape honeydew kiwi lemon"),
        ]

        result = qm.calculate_metrics(chunks)

        # All words are unique, so diversity should be 1.0
        assert result["vocabulary_diversity"] == 1.0

    def test_vocabulary_diversity_low(self):
        """Test low vocabulary diversity (repeated words)."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="test test test test test"),
            Document(page_content="test test test test test"),
        ]

        result = qm.calculate_metrics(chunks)

        # Only 1 unique word out of 10 total = 0.1
        assert result["vocabulary_diversity"] == 0.1

    def test_avg_words_per_chunk(self):
        """Test average words per chunk calculation."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="one two three four five"),  # 5 words
            Document(page_content="six seven eight nine ten"),  # 5 words
        ]

        result = qm.calculate_metrics(chunks)

        # 10 total words / 2 chunks = 5
        assert result["avg_words_per_chunk"] == 5.0


class TestCommonWords:
    """Test common word detection."""

    def test_find_common_words_basic(self):
        """Test finding common words across chunks."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="testing testing testing code code"),
            Document(page_content="testing code development"),
        ]

        result = qm.calculate_metrics(chunks)
        top_words = result["top_common_words"]

        # "testing" appears 4 times, "code" appears 3 times
        assert len(top_words) > 0
        assert top_words[0][0] in ["testing", "code"]

    def test_find_common_words_filters_short_words(self):
        """Test that short words are filtered out."""
        qm = QualityMetrics()

        # The default min_length is 4 in _find_common_words
        common_words = qm._find_common_words(
            [
                Document(page_content="a an the it testing development"),
                Document(page_content="is at on in testing development"),
            ],
            min_length=4,
        )

        # Short words should be filtered, only "testing" and "development" remain
        word_list = [word for word, _ in common_words]
        assert "testing" in word_list
        assert "development" in word_list
        assert "a" not in word_list
        assert "an" not in word_list
        assert "the" not in word_list


class TestMetadataCoverage:
    """Test metadata coverage calculation."""

    def test_metadata_coverage_no_metadata(self):
        """Test metadata coverage with no metadata."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Content 1"),
            Document(page_content="Content 2"),
        ]

        result = qm.calculate_metrics(chunks)

        assert result["chunks_with_source"] == 0
        assert result["chunks_with_chunking_method"] == 0
        assert result["avg_metadata_fields"] == 0

    def test_metadata_coverage_with_source(self):
        """Test metadata coverage with source field."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Content 1", metadata={"source": "doc1.md"}),
            Document(page_content="Content 2", metadata={"source": "doc2.md"}),
            Document(page_content="Content 3"),  # No metadata
        ]

        result = qm.calculate_metrics(chunks)

        assert result["chunks_with_source"] == 2
        assert "source" in result["metadata_keys"]

    def test_metadata_coverage_with_chunking_method(self):
        """Test metadata coverage with chunking_method field."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Content", metadata={"chunking_method": "recursive"}),
        ]

        result = qm.calculate_metrics(chunks)

        assert result["chunks_with_chunking_method"] == 1
        assert "chunking_method" in result["metadata_keys"]

    def test_metadata_coverage_multiple_fields(self):
        """Test metadata coverage with multiple fields."""
        qm = QualityMetrics()
        chunks = [
            Document(
                page_content="Content",
                metadata={"source": "doc.md", "chunking_method": "markdown", "custom": "value"},
            ),
        ]

        result = qm.calculate_metrics(chunks)

        assert result["chunks_with_source"] == 1
        assert result["chunks_with_chunking_method"] == 1
        assert len(result["metadata_keys"]) == 3
        assert "custom" in result["metadata_keys"]
        assert result["avg_metadata_fields"] == 3.0


class TestQualityScore:
    """Test quality score calculation."""

    def test_quality_score_excellent_chunks(self):
        """Test quality score for excellent quality chunks."""
        qm = QualityMetrics()
        # Create high-quality chunks: good size, all unique, diverse vocabulary
        chunks = [
            Document(page_content=" ".join([f"word{i}" for i in range(100)])),  # ~500 chars
            Document(page_content=" ".join([f"term{i}" for i in range(100)])),  # ~500 chars
            Document(page_content=" ".join([f"text{i}" for i in range(100)])),  # ~500 chars
        ]

        result = qm.calculate_metrics(chunks)

        assert result["quality_score"] >= 0.7  # Should be high quality
        assert result["uniqueness_ratio"] == 1.0  # All unique
        assert result["vocabulary_diversity"] == 1.0  # All words unique

    def test_quality_score_poor_chunks(self):
        """Test quality score for poor quality chunks."""
        qm = QualityMetrics()
        # Create low-quality chunks: too small, duplicates, low diversity
        chunks = [
            Document(page_content="a"),  # Too small
            Document(page_content="a"),  # Duplicate
            Document(page_content="a"),  # Duplicate
        ]

        result = qm.calculate_metrics(chunks)

        assert result["quality_score"] < 0.5  # Should be low quality
        assert result["uniqueness_ratio"] < 0.5

    def test_quality_score_range(self):
        """Test that quality score is always between 0 and 1."""
        qm = QualityMetrics()
        test_cases = [
            [Document(page_content="x" * 100)],
            [Document(page_content="y" * 1000)],
            [Document(page_content="z" * 5000)],
        ]

        for chunks in test_cases:
            result = qm.calculate_metrics(chunks)
            assert 0.0 <= result["quality_score"] <= 1.0


class TestQualityGrade:
    """Test quality grade assignment."""

    def test_quality_grade_excellent(self):
        """Test 'Excellent' grade for score >= 0.9."""
        qm = QualityMetrics()
        grade = qm._get_quality_grade(0.95)
        assert grade == "Excellent"

    def test_quality_grade_good(self):
        """Test 'Good' grade for score 0.75-0.89."""
        qm = QualityMetrics()
        assert qm._get_quality_grade(0.85) == "Good"
        assert qm._get_quality_grade(0.75) == "Good"

    def test_quality_grade_fair(self):
        """Test 'Fair' grade for score 0.6-0.74."""
        qm = QualityMetrics()
        assert qm._get_quality_grade(0.70) == "Fair"
        assert qm._get_quality_grade(0.60) == "Fair"

    def test_quality_grade_poor(self):
        """Test 'Poor' grade for score 0.4-0.59."""
        qm = QualityMetrics()
        assert qm._get_quality_grade(0.50) == "Poor"
        assert qm._get_quality_grade(0.40) == "Poor"

    def test_quality_grade_very_poor(self):
        """Test 'Very Poor' grade for score < 0.4."""
        qm = QualityMetrics()
        assert qm._get_quality_grade(0.30) == "Very Poor"
        assert qm._get_quality_grade(0.10) == "Very Poor"
        assert qm._get_quality_grade(0.0) == "Very Poor"


class TestRecommendations:
    """Test recommendation generation."""

    def test_recommendations_no_metrics(self):
        """Test recommendations when no metrics calculated."""
        qm = QualityMetrics()
        recommendations = qm.get_recommendations()

        assert "Calculate metrics first" in recommendations

    def test_recommendations_small_chunks(self):
        """Test recommendation for chunks that are too small."""
        qm = QualityMetrics()
        chunks = [Document(page_content="a" * 150) for _ in range(5)]
        qm.calculate_metrics(chunks)

        recommendations = qm.get_recommendations()

        assert any("Increase minimum chunk size" in rec for rec in recommendations)

    def test_recommendations_large_chunks(self):
        """Test recommendation for chunks that are too large."""
        qm = QualityMetrics()
        chunks = [Document(page_content="a" * 3000) for _ in range(5)]
        qm.calculate_metrics(chunks)

        recommendations = qm.get_recommendations()

        assert any("Decrease chunk size" in rec for rec in recommendations)

    def test_recommendations_low_uniqueness(self):
        """Test recommendation for low uniqueness."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Same content " * 50),
            Document(page_content="Same content " * 50),
            Document(page_content="Same content " * 50),
            Document(page_content="Different " * 50),
        ]
        qm.calculate_metrics(chunks)

        recommendations = qm.get_recommendations()

        assert any("near-duplicate detection" in rec for rec in recommendations)

    def test_recommendations_low_vocabulary(self):
        """Test recommendation for low vocabulary diversity."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="test test test test test " * 20),
            Document(page_content="test test test test test " * 20),
        ]
        qm.calculate_metrics(chunks)

        recommendations = qm.get_recommendations()

        assert any("repetitive" in rec for rec in recommendations)

    def test_recommendations_too_many_small_chunks(self):
        """Test recommendation for too many very small chunks."""
        qm = QualityMetrics()
        # Create 10 very small chunks and 2 medium chunks
        chunks = [Document(page_content="a" * 50) for _ in range(10)]
        chunks.extend([Document(page_content="b" * 600) for _ in range(2)])
        qm.calculate_metrics(chunks)

        recommendations = qm.get_recommendations()

        # 10/12 = 83% very small, which is > 15%
        assert any("very small chunks" in rec for rec in recommendations)

    def test_recommendations_good_quality(self):
        """Test that good quality data gets positive recommendation."""
        qm = QualityMetrics()
        # Create good quality chunks
        chunks = [
            Document(page_content=" ".join([f"word{i}" for i in range(j * 100, (j + 1) * 100)]))
            for j in range(10)
        ]
        qm.calculate_metrics(chunks)

        recommendations = qm.get_recommendations()

        assert any("good" in rec.lower() for rec in recommendations)


class TestPrintReport:
    """Test report printing (basic smoke test)."""

    def test_print_report_no_metrics(self, capsys):
        """Test print_report when no metrics calculated."""
        qm = QualityMetrics()
        qm.print_report()

        captured = capsys.readouterr()
        assert "No metrics calculated yet" in captured.out

    def test_print_report_with_metrics(self, capsys):
        """Test print_report with calculated metrics."""
        qm = QualityMetrics()
        chunks = [
            Document(page_content="Test content " * 50, metadata={"source": "test.md"}),
            Document(page_content="More content " * 50, metadata={"source": "test2.md"}),
        ]
        qm.calculate_metrics(chunks)
        qm.print_report()

        captured = capsys.readouterr()

        # Check that key sections appear in output
        assert "QUALITY METRICS REPORT" in captured.out
        assert "Overall Quality" in captured.out
        assert "Chunk Size Statistics" in captured.out
        assert "Content Diversity" in captured.out
        assert "Metadata Coverage" in captured.out
