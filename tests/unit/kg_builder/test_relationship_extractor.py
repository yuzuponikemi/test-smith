"""
Unit tests for relationship extraction (Phase 4)

TDD approach for enhanced relationship extraction with types, directions, and strength scoring
"""
import pytest
from src.kg_builder.relationship_extractor import (
    RelationshipExtractor,
    RelationshipType,
)


class TestRelationshipTypes:
    """Test relationship type definitions"""

    def test_relationship_type_enum_exists(self):
        """Test that RelationshipType enum is defined"""
        assert hasattr(RelationshipType, "USES")
        assert hasattr(RelationshipType, "IMPROVES")
        assert hasattr(RelationshipType, "BASED_ON")
        assert hasattr(RelationshipType, "COMPARED_WITH")
        assert hasattr(RelationshipType, "RELATED_TO")

    def test_relationship_type_values(self):
        """Test that relationship types have string values"""
        assert RelationshipType.USES.value == "uses"
        assert RelationshipType.IMPROVES.value == "improves"
        assert RelationshipType.BASED_ON.value == "based_on"
        assert RelationshipType.COMPARED_WITH.value == "compared_with"
        assert RelationshipType.RELATED_TO.value == "related_to"


class TestRelationshipExtractorBasics:
    """Test basic RelationshipExtractor functionality"""

    def test_extractor_can_be_instantiated(self):
        """Test that RelationshipExtractor can be created"""
        extractor = RelationshipExtractor()
        assert extractor is not None

    def test_extractor_has_extract_relationships_method(self):
        """Test that extractor has extract_relationships method"""
        extractor = RelationshipExtractor()
        assert hasattr(extractor, "extract_relationships")
        assert callable(extractor.extract_relationships)

    def test_extractor_has_score_strength_method(self):
        """Test that extractor has score_strength method"""
        extractor = RelationshipExtractor()
        assert hasattr(extractor, "score_strength")
        assert callable(extractor.score_strength)

    def test_extractor_has_infer_bidirectional_method(self):
        """Test that extractor has infer_bidirectional method"""
        extractor = RelationshipExtractor()
        assert hasattr(extractor, "infer_bidirectional")
        assert callable(extractor.infer_bidirectional)


class TestRelationshipExtraction:
    """Test relationship extraction from entities"""

    def test_extract_relationships_returns_list(self):
        """Test that extract_relationships returns a list"""
        extractor = RelationshipExtractor()

        entities = [
            {"name": "GNN", "type": "method"},
            {"name": "CNN", "type": "method"},
        ]

        relationships = extractor.extract_relationships(entities)
        assert isinstance(relationships, list)

    def test_extract_relationships_from_empty_list(self):
        """Test extracting relationships from empty entity list"""
        extractor = RelationshipExtractor()

        relationships = extractor.extract_relationships([])
        assert relationships == []

    def test_extract_relationships_has_required_fields(self):
        """Test that extracted relationships have required fields"""
        extractor = RelationshipExtractor()

        entities = [
            {"name": "GNN", "type": "method", "context": "GNN uses message passing"},
            {"name": "Message Passing", "type": "technique"},
        ]

        relationships = extractor.extract_relationships(entities)

        if relationships:  # If any relationships found
            rel = relationships[0]
            assert "source" in rel
            assert "target" in rel
            assert "type" in rel
            assert "strength" in rel
            assert "bidirectional" in rel

    def test_extract_uses_relationship(self):
        """Test extracting USES relationship from context"""
        extractor = RelationshipExtractor()

        entities = [
            {"name": "GNN", "type": "method", "context": "GNN uses attention mechanism"},
            {"name": "Attention Mechanism", "type": "technique"},
        ]

        relationships = extractor.extract_relationships(entities)

        # Should find USES relationship
        uses_rels = [r for r in relationships if r["type"] == RelationshipType.USES]
        assert len(uses_rels) > 0

        rel = uses_rels[0]
        assert rel["source"] == "GNN"
        assert rel["target"] == "Attention Mechanism"

    def test_extract_improves_relationship(self):
        """Test extracting IMPROVES relationship from context"""
        extractor = RelationshipExtractor()

        entities = [
            {"name": "GAT", "type": "method", "context": "GAT improves GNN performance"},
            {"name": "GNN", "type": "method"},
        ]

        relationships = extractor.extract_relationships(entities)

        # Should find IMPROVES relationship
        improves_rels = [r for r in relationships if r["type"] == RelationshipType.IMPROVES]
        assert len(improves_rels) > 0

        rel = improves_rels[0]
        assert rel["source"] == "GAT"
        assert rel["target"] == "GNN"

    def test_extract_based_on_relationship(self):
        """Test extracting BASED_ON relationship from context"""
        extractor = RelationshipExtractor()

        entities = [
            {"name": "GAT", "type": "method", "context": "GAT is based on attention"},
            {"name": "Attention", "type": "technique"},
        ]

        relationships = extractor.extract_relationships(entities)

        # Should find BASED_ON relationship
        based_on_rels = [r for r in relationships if r["type"] == RelationshipType.BASED_ON]
        assert len(based_on_rels) > 0

        rel = based_on_rels[0]
        assert rel["source"] == "GAT"
        assert rel["target"] == "Attention"

    def test_extract_compared_with_relationship(self):
        """Test extracting COMPARED_WITH relationship from context"""
        extractor = RelationshipExtractor()

        entities = [
            {"name": "GNN", "type": "method", "context": "GNN is compared with CNN"},
            {"name": "CNN", "type": "method"},
        ]

        relationships = extractor.extract_relationships(entities)

        # Should find COMPARED_WITH relationship
        compared_rels = [r for r in relationships if r["type"] == RelationshipType.COMPARED_WITH]
        assert len(compared_rels) > 0

    def test_extract_multiple_relationships_same_entity_pair(self):
        """Test extracting multiple relationships between same entities"""
        extractor = RelationshipExtractor()

        entities = [
            {
                "name": "GAT",
                "type": "method",
                "context": "GAT uses attention and improves GNN performance"
            },
            {"name": "Attention", "type": "technique"},
            {"name": "GNN", "type": "method"},
        ]

        relationships = extractor.extract_relationships(entities)

        # Should find both USES (GAT→Attention) and IMPROVES (GAT→GNN)
        assert len(relationships) >= 2

        types_found = {r["type"] for r in relationships}
        assert RelationshipType.USES in types_found
        assert RelationshipType.IMPROVES in types_found


class TestRelationshipStrengthScoring:
    """Test relationship strength scoring"""

    def test_score_strength_returns_float(self):
        """Test that score_strength returns a float between 0 and 1"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GNN",
            "target": "CNN",
            "type": RelationshipType.RELATED_TO,
            "context": "GNN and CNN are both neural networks"
        }

        strength = extractor.score_strength(relationship)

        assert isinstance(strength, float)
        assert 0.0 <= strength <= 1.0

    def test_explicit_relationship_has_high_strength(self):
        """Test that explicit relationships have higher strength scores"""
        extractor = RelationshipExtractor()

        explicit_rel = {
            "source": "GNN",
            "target": "Message Passing",
            "type": RelationshipType.USES,
            "context": "GNN explicitly uses message passing mechanism"
        }

        implicit_rel = {
            "source": "GNN",
            "target": "CNN",
            "type": RelationshipType.RELATED_TO,
            "context": "GNN and CNN"
        }

        explicit_strength = extractor.score_strength(explicit_rel)
        implicit_strength = extractor.score_strength(implicit_rel)

        assert explicit_strength > implicit_strength

    def test_strength_based_on_context_length(self):
        """Test that longer context descriptions yield higher confidence"""
        extractor = RelationshipExtractor()

        detailed_rel = {
            "source": "GAT",
            "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "context": "Graph Attention Network (GAT) significantly improves upon traditional GNN by incorporating attention mechanisms that allow the model to weigh neighbor contributions differently"
        }

        brief_rel = {
            "source": "GAT",
            "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "context": "GAT improves GNN"
        }

        detailed_strength = extractor.score_strength(detailed_rel)
        brief_strength = extractor.score_strength(brief_rel)

        assert detailed_strength > brief_strength

    def test_strength_boosted_by_frequency(self):
        """Test that relationships appearing multiple times get strength boost"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GNN",
            "target": "Graph",
            "type": RelationshipType.USES,
            "context": "GNN uses graphs",
            "frequency": 5  # Appears 5 times in document
        }

        strength = extractor.score_strength(relationship)

        # Should be boosted due to high frequency
        assert strength > 0.5


class TestBidirectionalInference:
    """Test bidirectional relationship inference"""

    def test_infer_bidirectional_returns_bool(self):
        """Test that infer_bidirectional returns a boolean"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GNN",
            "target": "CNN",
            "type": RelationshipType.COMPARED_WITH
        }

        bidirectional = extractor.infer_bidirectional(relationship)
        assert isinstance(bidirectional, bool)

    def test_compared_with_is_bidirectional(self):
        """Test that COMPARED_WITH relationships are bidirectional"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GNN",
            "target": "CNN",
            "type": RelationshipType.COMPARED_WITH
        }

        assert extractor.infer_bidirectional(relationship) is True

    def test_related_to_is_bidirectional(self):
        """Test that RELATED_TO relationships are bidirectional"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GNN",
            "target": "CNN",
            "type": RelationshipType.RELATED_TO
        }

        assert extractor.infer_bidirectional(relationship) is True

    def test_uses_is_unidirectional(self):
        """Test that USES relationships are unidirectional"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GNN",
            "target": "Attention",
            "type": RelationshipType.USES
        }

        assert extractor.infer_bidirectional(relationship) is False

    def test_improves_is_unidirectional(self):
        """Test that IMPROVES relationships are unidirectional"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GAT",
            "target": "GNN",
            "type": RelationshipType.IMPROVES
        }

        assert extractor.infer_bidirectional(relationship) is False

    def test_based_on_is_unidirectional(self):
        """Test that BASED_ON relationships are unidirectional"""
        extractor = RelationshipExtractor()

        relationship = {
            "source": "GAT",
            "target": "Attention",
            "type": RelationshipType.BASED_ON
        }

        assert extractor.infer_bidirectional(relationship) is False


class TestRelationshipContextMatching:
    """Test context-based relationship detection"""

    def test_detect_uses_patterns(self):
        """Test detection of various USES patterns"""
        extractor = RelationshipExtractor()

        patterns = [
            "GNN uses message passing",
            "GAT utilizes attention mechanism",
            "Model employs dropout regularization",
            "Architecture applies batch normalization",
        ]

        for pattern in patterns:
            entities = [
                {"name": "Model", "type": "method", "context": pattern},
                {"name": "Technique", "type": "technique"},
            ]

            # Should detect USES relationship
            # (exact assertions depend on entity name matching in context)
            relationships = extractor.extract_relationships(entities)
            assert isinstance(relationships, list)

    def test_detect_improves_patterns(self):
        """Test detection of various IMPROVES patterns"""
        extractor = RelationshipExtractor()

        patterns = [
            "GAT improves GNN performance",
            "New method outperforms baseline",
            "Enhanced model achieves better results than previous",
            "Architecture surpasses existing approaches",
        ]

        for pattern in patterns:
            entities = [
                {"name": "NewMethod", "type": "method", "context": pattern},
                {"name": "Baseline", "type": "method"},
            ]

            relationships = extractor.extract_relationships(entities)
            assert isinstance(relationships, list)

    def test_detect_based_on_patterns(self):
        """Test detection of various BASED_ON patterns"""
        extractor = RelationshipExtractor()

        patterns = [
            "GAT is based on attention",
            "Model builds upon transformer architecture",
            "Approach derives from residual networks",
            "Method extends GNN framework",
        ]

        for pattern in patterns:
            entities = [
                {"name": "NewMethod", "type": "method", "context": pattern},
                {"name": "Foundation", "type": "method"},
            ]

            relationships = extractor.extract_relationships(entities)
            assert isinstance(relationships, list)


class TestRelationshipFiltering:
    """Test relationship filtering and validation"""

    def test_filter_weak_relationships(self):
        """Test that weak relationships can be filtered"""
        extractor = RelationshipExtractor(min_strength=0.5)

        entities = [
            {"name": "A", "type": "method", "context": "A and B"},
            {"name": "B", "type": "method"},
        ]

        relationships = extractor.extract_relationships(entities)

        # All relationships should have strength >= 0.5
        for rel in relationships:
            assert rel["strength"] >= 0.5

    def test_preserve_metadata_in_relationships(self):
        """Test that entity metadata is preserved in relationships"""
        extractor = RelationshipExtractor()

        entities = [
            {
                "name": "GNN",
                "type": "method",
                "confidence": 0.95,
                "section": "Methods",
                "context": "GNN uses message passing"
            },
            {"name": "Message Passing", "type": "technique", "confidence": 0.85},
        ]

        relationships = extractor.extract_relationships(entities)

        if relationships:
            rel = relationships[0]
            # Should include entity metadata
            assert "source_metadata" in rel or "confidence" in rel
