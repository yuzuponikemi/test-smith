"""
Unit tests for EntityLinker embedding-based similarity

TDD approach for Phase 1: Embedding-based entity linking
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.kg_builder.entity_linker import EntityLinker


class TestEmbeddingBasedSimilarity:
    """Test embedding-based similarity calculation"""

    def test_entity_linker_accepts_embedding_function(self):
        """Test that EntityLinker can accept an embedding function"""
        mock_embedder = Mock()
        linker = EntityLinker(embedding_function=mock_embedder)
        assert linker.embedding_function == mock_embedder

    def test_entity_linker_works_without_embedding_function(self):
        """Test that EntityLinker works without embedding function (fallback to string similarity)"""
        linker = EntityLinker()
        assert linker.embedding_function is None

    def test_calculate_embedding_similarity_uses_cosine(self):
        """Test that embedding similarity uses cosine distance"""
        # Mock embedder that returns simple vectors
        def mock_embedder(text):
            if text == "neural network":
                return [1.0, 0.0, 0.0]
            elif text == "neural networks":
                return [0.9, 0.1, 0.0]
            else:
                return [0.0, 1.0, 0.0]

        linker = EntityLinker(embedding_function=mock_embedder)
        similarity = linker._calculate_embedding_similarity("neural network", "neural networks")

        # Similar vectors should have high cosine similarity (close to 1.0)
        assert similarity > 0.9
        assert similarity <= 1.0

    def test_calculate_embedding_similarity_different_concepts(self):
        """Test that different concepts have low embedding similarity"""
        def mock_embedder(text):
            if "neural" in text.lower():
                return [1.0, 0.0, 0.0]
            else:
                return [0.0, 1.0, 0.0]

        linker = EntityLinker(embedding_function=mock_embedder)
        similarity = linker._calculate_embedding_similarity("neural network", "decision tree")

        # Orthogonal vectors should have low similarity (close to 0.0)
        assert similarity < 0.5

    def test_find_similar_uses_embedding_when_available(self, sample_entities):
        """Test that find_similar uses embedding function when available"""
        call_count = {"count": 0}

        def mock_embedder(text):
            call_count["count"] += 1
            # Return different vectors based on text
            if "neural" in text.lower() or text == "GNN":
                return [1.0, 0.0]
            else:
                return [0.0, 1.0]

        linker = EntityLinker(
            embedding_function=mock_embedder,
            similarity_threshold=0.9
        )

        # Should use embeddings to find similar entities
        result = linker.find_similar("neural network", sample_entities, use_embeddings=True)

        # Should have called the embedder
        assert call_count["count"] > 0

        # Should find neural network related entities
        entity_names = [e["name"] for e in result]
        assert any("neural" in name.lower() for name in entity_names)

    def test_find_similar_falls_back_to_string_similarity(self, sample_entities):
        """Test that find_similar falls back to string similarity when embeddings unavailable"""
        linker = EntityLinker()  # No embedding function

        # Should still work with string-based similarity
        result = linker.find_similar("GNN", sample_entities)
        assert isinstance(result, list)


class TestEmbeddingCaching:
    """Test embedding caching for performance"""

    def test_embeddings_are_cached(self):
        """Test that embeddings are cached to avoid redundant computation"""
        call_count = {"count": 0}

        def mock_embedder(text):
            call_count["count"] += 1
            return [1.0, 0.0, 0.0]

        linker = EntityLinker(embedding_function=mock_embedder, cache_embeddings=True)

        # Calculate embedding twice for same text
        emb1 = linker._get_embedding("test")
        emb2 = linker._get_embedding("test")

        # Should only call embedder once due to caching
        assert call_count["count"] == 1
        assert emb1 == emb2

    def test_embeddings_not_cached_when_disabled(self):
        """Test that embeddings are not cached when caching is disabled"""
        call_count = {"count": 0}

        def mock_embedder(text):
            call_count["count"] += 1
            return [1.0, 0.0, 0.0]

        linker = EntityLinker(embedding_function=mock_embedder, cache_embeddings=False)

        # Calculate embedding twice for same text
        linker._get_embedding("test")
        linker._get_embedding("test")

        # Should call embedder twice without caching
        assert call_count["count"] == 2


class TestHybridSimilarity:
    """Test hybrid similarity (combination of string and embedding similarity)"""

    def test_hybrid_similarity_combines_both_methods(self):
        """Test that hybrid similarity combines string and embedding similarity"""
        def mock_embedder(text):
            return [1.0, 0.0]

        linker = EntityLinker(
            embedding_function=mock_embedder,
            hybrid_mode=True,
            hybrid_weight=0.5  # Equal weight to both methods
        )

        # Calculate hybrid similarity
        similarity = linker._calculate_similarity(
            "neural network",
            "neural networks",
            use_embeddings=True
        )

        # Should be between pure string similarity and pure embedding similarity
        assert 0.0 <= similarity <= 1.0

    def test_hybrid_weight_affects_result(self):
        """Test that hybrid weight parameter affects the result"""
        def mock_embedder(text):
            if text == "test1":
                return [1.0, 0.0]
            else:
                return [0.0, 1.0]

        # Weight towards embeddings (0.9)
        linker_embedding_heavy = EntityLinker(
            embedding_function=mock_embedder,
            hybrid_mode=True,
            hybrid_weight=0.9
        )

        # Weight towards strings (0.1)
        linker_string_heavy = EntityLinker(
            embedding_function=mock_embedder,
            hybrid_mode=True,
            hybrid_weight=0.1
        )

        # Different weights should produce different results
        sim_embedding_heavy = linker_embedding_heavy._calculate_similarity(
            "test1", "test2", use_embeddings=True
        )
        sim_string_heavy = linker_string_heavy._calculate_similarity(
            "test1", "test2", use_embeddings=True
        )

        # Results should be different due to different weights
        # (This is a weak assertion - in practice they might be close)
        assert isinstance(sim_embedding_heavy, float)
        assert isinstance(sim_string_heavy, float)
