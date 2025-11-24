"""
Unit tests for confidence score filtering (Phase 2)

TDD approach for confidence-based entity filtering and scoring
"""
import pytest
from src.kg_builder.entity_linker import EntityLinker


class TestConfidenceFiltering:
    """Test confidence score filtering"""

    def test_filter_entities_by_confidence_threshold(self):
        """Test that entities below confidence threshold are filtered out"""
        linker = EntityLinker(confidence_threshold=0.5)

        entities = [
            {"name": "GNN", "type": "method", "confidence": 0.95},
            {"name": "CNN", "type": "method", "confidence": 0.85},
            {"name": "RNN", "type": "method", "confidence": 0.45},  # Below threshold
            {"name": "LSTM", "type": "method", "confidence": 0.25},  # Below threshold
        ]

        filtered = linker.filter_by_confidence(entities)

        # Should only keep entities with confidence >= 0.5
        assert len(filtered) == 2
        entity_names = [e["name"] for e in filtered]
        assert "GNN" in entity_names
        assert "CNN" in entity_names
        assert "RNN" not in entity_names
        assert "LSTM" not in entity_names

    def test_filter_entities_default_threshold(self):
        """Test that default confidence threshold is 0.3"""
        linker = EntityLinker()

        entities = [
            {"name": "Entity1", "confidence": 0.4},
            {"name": "Entity2", "confidence": 0.2},
        ]

        filtered = linker.filter_by_confidence(entities)

        # Default threshold is 0.3
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Entity1"

    def test_filter_entities_with_missing_confidence(self):
        """Test that entities without confidence field are handled gracefully"""
        linker = EntityLinker(confidence_threshold=0.5)

        entities = [
            {"name": "Entity1", "confidence": 0.8},
            {"name": "Entity2"},  # No confidence field
        ]

        filtered = linker.filter_by_confidence(entities)

        # Entity without confidence should be excluded (or assigned default 0.0)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Entity1"

    def test_filter_entities_preserves_metadata(self):
        """Test that filtering preserves entity metadata"""
        linker = EntityLinker(confidence_threshold=0.5)

        entities = [
            {"name": "GNN", "type": "method", "confidence": 0.95, "section": "Methods"},
        ]

        filtered = linker.filter_by_confidence(entities)

        assert filtered[0]["type"] == "method"
        assert filtered[0]["section"] == "Methods"

    def test_filter_entities_zero_threshold(self):
        """Test that threshold of 0.0 keeps all entities"""
        linker = EntityLinker(confidence_threshold=0.0)

        entities = [
            {"name": "Entity1", "confidence": 0.01},
            {"name": "Entity2", "confidence": 0.99},
        ]

        filtered = linker.filter_by_confidence(entities)

        assert len(filtered) == 2

    def test_filter_entities_one_threshold(self):
        """Test that threshold of 1.0 requires perfect confidence"""
        linker = EntityLinker(confidence_threshold=1.0)

        entities = [
            {"name": "Entity1", "confidence": 0.99},
            {"name": "Entity2", "confidence": 1.0},
        ]

        filtered = linker.filter_by_confidence(entities)

        assert len(filtered) == 1
        assert filtered[0]["name"] == "Entity2"


class TestConfidenceScoreRecalculation:
    """Test confidence score recalculation based on context"""

    def test_recalculate_score_by_frequency(self):
        """Test that entities appearing in multiple chunks get higher scores"""
        linker = EntityLinker()

        entities = [
            {"name": "GNN", "confidence": 0.5, "occurrences": 5},  # Appears 5 times
            {"name": "CNN", "confidence": 0.5, "occurrences": 1},  # Appears 1 time
        ]

        recalculated = linker.recalculate_confidence(entities)

        # GNN should have higher confidence due to frequency
        gnn_score = next(e["confidence"] for e in recalculated if e["name"] == "GNN")
        cnn_score = next(e["confidence"] for e in recalculated if e["name"] == "CNN")

        assert gnn_score > cnn_score

    def test_recalculate_score_by_relationships(self):
        """Test that entities with more relationships get higher scores"""
        linker = EntityLinker()

        entities = [
            {"name": "GNN", "confidence": 0.5, "relationship_count": 10},
            {"name": "CNN", "confidence": 0.5, "relationship_count": 2},
        ]

        recalculated = linker.recalculate_confidence(entities)

        # GNN should have higher confidence due to more relationships
        gnn_score = next(e["confidence"] for e in recalculated if e["name"] == "GNN")
        cnn_score = next(e["confidence"] for e in recalculated if e["name"] == "CNN")

        assert gnn_score > cnn_score

    def test_recalculate_score_isolated_node_penalty(self):
        """Test that isolated nodes (no relationships) get lower scores"""
        linker = EntityLinker()

        entities = [
            {"name": "Connected", "confidence": 0.8, "relationship_count": 5},
            {"name": "Isolated", "confidence": 0.8, "relationship_count": 0},
        ]

        recalculated = linker.recalculate_confidence(entities)

        connected_score = next(e["confidence"] for e in recalculated if e["name"] == "Connected")
        isolated_score = next(e["confidence"] for e in recalculated if e["name"] == "Isolated")

        assert isolated_score < connected_score

    def test_recalculate_score_clamped_to_valid_range(self):
        """Test that recalculated scores stay within [0, 1] range"""
        linker = EntityLinker()

        entities = [
            {"name": "VeryFrequent", "confidence": 0.9, "occurrences": 100, "relationship_count": 50},
        ]

        recalculated = linker.recalculate_confidence(entities)

        score = recalculated[0]["confidence"]
        assert 0.0 <= score <= 1.0

    def test_recalculate_score_combined_factors(self):
        """Test that recalculation considers both frequency and relationships"""
        linker = EntityLinker()

        entities = [
            {"name": "A", "confidence": 0.5, "occurrences": 10, "relationship_count": 10},
            {"name": "B", "confidence": 0.5, "occurrences": 1, "relationship_count": 1},
        ]

        recalculated = linker.recalculate_confidence(entities)

        a_score = next(e["confidence"] for e in recalculated if e["name"] == "A")
        b_score = next(e["confidence"] for e in recalculated if e["name"] == "B")

        # A should have significantly higher score
        assert a_score > b_score
        assert a_score - b_score > 0.1  # Significant difference


class TestReviewFlagging:
    """Test human review flagging for borderline entities"""

    def test_flag_borderline_entities(self):
        """Test that entities near threshold are flagged for review"""
        linker = EntityLinker(
            confidence_threshold=0.5,
            review_margin=0.1  # Flag entities within 0.1 of threshold
        )

        entities = [
            {"name": "High", "confidence": 0.9},      # Well above threshold
            {"name": "Borderline1", "confidence": 0.55},  # Within margin (0.5-0.6)
            {"name": "Borderline2", "confidence": 0.45},  # Within margin (0.4-0.5)
            {"name": "Low", "confidence": 0.2},       # Well below threshold
        ]

        flagged = linker.flag_for_review(entities)

        # Should have review flags
        assert flagged[0]["needs_review"] == False
        assert flagged[1]["needs_review"] == True
        assert flagged[2]["needs_review"] == True
        assert flagged[3]["needs_review"] == False

    def test_flag_entities_with_reason(self):
        """Test that flagged entities include reason for review"""
        linker = EntityLinker(
            confidence_threshold=0.5,
            review_margin=0.1
        )

        entities = [
            {"name": "Borderline", "confidence": 0.52},
        ]

        flagged = linker.flag_for_review(entities)

        assert flagged[0]["needs_review"] == True
        assert "review_reason" in flagged[0]
        assert "borderline" in flagged[0]["review_reason"].lower()

    def test_flag_isolated_nodes(self):
        """Test that isolated nodes are flagged regardless of confidence"""
        linker = EntityLinker()

        entities = [
            {"name": "Isolated", "confidence": 0.9, "relationship_count": 0},
            {"name": "Connected", "confidence": 0.9, "relationship_count": 5},
        ]

        flagged = linker.flag_for_review(entities)

        isolated = next(e for e in flagged if e["name"] == "Isolated")
        connected = next(e for e in flagged if e["name"] == "Connected")

        assert isolated["needs_review"] == True
        assert "isolated" in isolated["review_reason"].lower()
        assert connected["needs_review"] == False

    def test_flag_low_occurrence_entities(self):
        """Test that entities with low occurrence are flagged"""
        linker = EntityLinker(min_occurrences=3)

        entities = [
            {"name": "Rare", "confidence": 0.9, "occurrences": 1},
            {"name": "Common", "confidence": 0.9, "occurrences": 5},
        ]

        flagged = linker.flag_for_review(entities)

        rare = next(e for e in flagged if e["name"] == "Rare")
        common = next(e for e in flagged if e["name"] == "Common")

        assert rare["needs_review"] == True
        assert "low occurrence" in rare["review_reason"].lower()
        assert common["needs_review"] == False
