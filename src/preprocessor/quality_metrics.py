"""
Quality Metrics - Evaluates preprocessing results

Calculates metrics to assess the quality of preprocessed data:
- Chunk size distribution
- Content diversity
- Semantic coherence
- Coverage metrics
"""

from collections import Counter

import numpy as np
from langchain.schema import Document


class QualityMetrics:
    """Calculates quality metrics for preprocessed documents"""

    def __init__(self):
        self.metrics = {}

    def calculate_metrics(self, chunks: list[Document]) -> dict:
        """Calculate comprehensive quality metrics"""

        if not chunks:
            return {'status': 'no_chunks', 'total_chunks': 0}

        # Basic statistics
        chunk_lengths = [len(chunk.page_content) for chunk in chunks]
        word_counts = [len(chunk.page_content.split()) for chunk in chunks]

        # Chunk size metrics
        size_metrics = {
            'total_chunks': len(chunks),
            'mean_chunk_size': np.mean(chunk_lengths),
            'median_chunk_size': np.median(chunk_lengths),
            'std_chunk_size': np.std(chunk_lengths),
            'min_chunk_size': np.min(chunk_lengths),
            'max_chunk_size': np.max(chunk_lengths),
            'mean_word_count': np.mean(word_counts),
            'median_word_count': np.median(word_counts),
        }

        # Size distribution
        size_distribution = self._calculate_size_distribution(chunk_lengths)

        # Content diversity metrics
        diversity_metrics = self._calculate_diversity(chunks)

        # Metadata coverage
        metadata_metrics = self._calculate_metadata_coverage(chunks)

        # Quality score
        quality_score = self._calculate_quality_score(
            size_metrics,
            diversity_metrics,
            len(chunks)
        )

        self.metrics = {
            **size_metrics,
            'size_distribution': size_distribution,
            **diversity_metrics,
            **metadata_metrics,
            'quality_score': quality_score,
            'quality_grade': self._get_quality_grade(quality_score)
        }

        return self.metrics

    def _calculate_size_distribution(self, chunk_lengths: list[int]) -> dict[str, int]:
        """Calculate distribution of chunk sizes"""

        distribution = {
            'very_small': 0,    # < 100 chars
            'small': 0,         # 100-500
            'medium': 0,        # 500-1000
            'large': 0,         # 1000-1500
            'very_large': 0,    # > 1500
        }

        for length in chunk_lengths:
            if length < 100:
                distribution['very_small'] += 1
            elif length < 500:
                distribution['small'] += 1
            elif length < 1000:
                distribution['medium'] += 1
            elif length < 1500:
                distribution['large'] += 1
            else:
                distribution['very_large'] += 1

        return distribution

    def _calculate_diversity(self, chunks: list[Document]) -> dict:
        """Calculate content diversity metrics"""

        # Unique content ratio
        unique_contents = {chunk.page_content for chunk in chunks}
        uniqueness_ratio = len(unique_contents) / len(chunks) if chunks else 0

        # Vocabulary diversity (unique words)
        all_words = []
        for chunk in chunks:
            words = chunk.page_content.lower().split()
            all_words.extend(words)

        total_words = len(all_words)
        unique_words = len(set(all_words))
        vocabulary_diversity = unique_words / total_words if total_words > 0 else 0

        # Content overlap (approximate)
        # Calculate what percentage of chunks share common words
        common_words = self._find_common_words(chunks)

        return {
            'uniqueness_ratio': uniqueness_ratio,
            'vocabulary_diversity': vocabulary_diversity,
            'total_vocabulary_size': unique_words,
            'avg_words_per_chunk': total_words / len(chunks) if chunks else 0,
            'top_common_words': common_words[:10],
        }

    def _find_common_words(self, chunks: list[Document], min_length: int = 4) -> list[tuple]:
        """Find most common words across chunks"""

        word_counter = Counter()

        for chunk in chunks:
            words = chunk.page_content.lower().split()
            # Filter out very short words
            meaningful_words = [w for w in words if len(w) >= min_length]
            word_counter.update(meaningful_words)

        # Return top 20 most common words
        return word_counter.most_common(20)

    def _calculate_metadata_coverage(self, chunks: list[Document]) -> dict:
        """Calculate metadata coverage"""

        # Count how many chunks have various metadata fields
        has_source = sum(1 for c in chunks if 'source' in c.metadata)
        has_chunking_method = sum(1 for c in chunks if 'chunking_method' in c.metadata)

        # Collect all metadata keys
        all_metadata_keys = set()
        for chunk in chunks:
            all_metadata_keys.update(chunk.metadata.keys())

        return {
            'chunks_with_source': has_source,
            'chunks_with_chunking_method': has_chunking_method,
            'metadata_keys': list(all_metadata_keys),
            'avg_metadata_fields': np.mean([len(c.metadata) for c in chunks]) if chunks else 0,
        }

    def _calculate_quality_score(self,
                                 size_metrics: dict,
                                 diversity_metrics: dict,
                                 num_chunks: int) -> float:
        """
        Calculate overall quality score (0-1)

        Factors:
        - Chunk size appropriateness (not too small, not too large)
        - Content diversity (high uniqueness)
        - Vocabulary richness
        """

        score = 0.0

        # Size score (0-0.4)
        median_size = size_metrics['median_chunk_size']
        if 300 <= median_size <= 1500:
            size_score = 0.4
        elif 150 <= median_size <= 2000:
            size_score = 0.3
        elif 100 <= median_size <= 2500:
            size_score = 0.2
        else:
            size_score = 0.1

        score += size_score

        # Diversity score (0-0.4)
        uniqueness = diversity_metrics['uniqueness_ratio']
        if uniqueness >= 0.95:
            diversity_score = 0.4
        elif uniqueness >= 0.85:
            diversity_score = 0.3
        elif uniqueness >= 0.70:
            diversity_score = 0.2
        else:
            diversity_score = 0.1

        score += diversity_score

        # Vocabulary score (0-0.2)
        vocab_diversity = diversity_metrics['vocabulary_diversity']
        if vocab_diversity >= 0.5:
            vocab_score = 0.2
        elif vocab_diversity >= 0.3:
            vocab_score = 0.15
        elif vocab_diversity >= 0.1:
            vocab_score = 0.1
        else:
            vocab_score = 0.05

        score += vocab_score

        return min(1.0, score)

    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to grade"""

        if score >= 0.9:
            return 'Excellent'
        elif score >= 0.75:
            return 'Good'
        elif score >= 0.6:
            return 'Fair'
        elif score >= 0.4:
            return 'Poor'
        else:
            return 'Very Poor'

    def print_report(self):
        """Print detailed metrics report"""

        if not self.metrics:
            print("No metrics calculated yet. Run calculate_metrics() first.")
            return

        print("\n" + "="*80)
        print("QUALITY METRICS REPORT")
        print("="*80)

        m = self.metrics

        print(f"\n📊 Overall Quality: {m['quality_grade']} ({m['quality_score']:.2f}/1.00)")

        print("\n📏 Chunk Size Statistics:")
        print(f"  Total Chunks: {m['total_chunks']}")
        print(f"  Mean Size: {m['mean_chunk_size']:.1f} characters")
        print(f"  Median Size: {m['median_chunk_size']:.1f} characters")
        print(f"  Std Dev: {m['std_chunk_size']:.1f}")
        print(f"  Range: {m['min_chunk_size']} - {m['max_chunk_size']} characters")
        print(f"  Mean Words: {m['mean_word_count']:.1f} words/chunk")

        print("\n📈 Size Distribution:")
        dist = m['size_distribution']
        total = m['total_chunks']
        for category, count in dist.items():
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {category:>12}: {count:>5} ({percentage:>5.1f}%)")

        print("\n🎨 Content Diversity:")
        print(f"  Uniqueness Ratio: {m['uniqueness_ratio']:.2%}")
        print(f"  Vocabulary Diversity: {m['vocabulary_diversity']:.2%}")
        print(f"  Total Vocabulary: {m['total_vocabulary_size']} unique words")
        print(f"  Avg Words/Chunk: {m['avg_words_per_chunk']:.1f}")

        if m['top_common_words']:
            print("\n  Top 10 Common Words:")
            for word, count in m['top_common_words'][:10]:
                print(f"    '{word}': {count}")

        print("\n📋 Metadata Coverage:")
        print(f"  Chunks with source: {m['chunks_with_source']}/{m['total_chunks']}")
        print(f"  Chunks with chunking_method: {m['chunks_with_chunking_method']}/{m['total_chunks']}")
        print(f"  Metadata fields: {', '.join(m['metadata_keys'])}")

        # Recommendations
        print("\n💡 Recommendations:")

        if m['median_chunk_size'] < 300:
            print("  ⚠️  Chunks are quite small - consider increasing chunk size or filtering more aggressively")

        if m['median_chunk_size'] > 2000:
            print("  ⚠️  Chunks are quite large - consider decreasing chunk size for better retrieval")

        if m['uniqueness_ratio'] < 0.85:
            print("  ⚠️  High duplication rate - enable near-duplicate detection")

        if m['vocabulary_diversity'] < 0.2:
            print("  ⚠️  Low vocabulary diversity - documents may be too similar or repetitive")

        if dist['very_small'] > total * 0.1:
            print(f"  ⚠️  {dist['very_small']} very small chunks detected - increase min_chunk_size filter")

        if m['quality_score'] >= 0.75:
            print("  ✅ Data quality looks good! Ready for embedding.")

        print("\n" + "="*80)

    def get_recommendations(self) -> list[str]:
        """Get actionable recommendations based on metrics"""

        if not self.metrics:
            return ["Calculate metrics first"]

        recommendations = []
        m = self.metrics

        # Size recommendations
        if m['median_chunk_size'] < 200:
            recommendations.append("Increase minimum chunk size to at least 200 characters")
        elif m['median_chunk_size'] > 2500:
            recommendations.append("Decrease chunk size to improve retrieval granularity")

        # Diversity recommendations
        if m['uniqueness_ratio'] < 0.80:
            recommendations.append("Enable near-duplicate detection to improve uniqueness")

        if m['vocabulary_diversity'] < 0.15:
            recommendations.append("Review source documents - content may be too repetitive")

        # Distribution recommendations
        dist = m['size_distribution']
        if dist['very_small'] > m['total_chunks'] * 0.15:
            recommendations.append("Too many very small chunks - increase min_chunk_size filter")

        # Overall
        if m['quality_score'] < 0.5:
            recommendations.append("Consider reviewing document preprocessing pipeline")

        if not recommendations:
            recommendations.append("Quality metrics look good!")

        return recommendations
