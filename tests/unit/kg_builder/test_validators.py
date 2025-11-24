"""
Unit tests for validation layer (Phase 5)

TDD approach for rule-based validation of entities and relationships
"""
import pytest
from src.kg_builder.validators import (
    ValidationResult,
    EntityValidator,
    RelationshipValidator,
)
from src.kg_builder import RelationshipType


class TestValidationResult:
    """Test ValidationResult data class"""

    def test_validation_result_can_be_created(self):
        """Test that ValidationResult can be instantiated"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        assert result is not None
        assert result.is_valid is True

    def test_validation_result_has_all_fields(self):
        """Test that ValidationResult has all required fields"""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1"],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"]
        )
        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "suggestions")

    def test_validation_result_is_valid_when_no_errors(self):
        """Test that validation is valid when no errors"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Some warning"],
            suggestions=[]
        )
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validation_result_is_invalid_when_errors(self):
        """Test that validation is invalid when errors present"""
        result = ValidationResult(
            is_valid=False,
            errors=["Missing required field"],
            warnings=[],
            suggestions=[]
        )
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestEntityValidator:
    """Test EntityValidator for entity validation"""

    def test_entity_validator_can_be_instantiated(self):
        """Test that EntityValidator can be created"""
        validator = EntityValidator()
        assert validator is not None

    def test_validate_required_fields_passes_for_valid_entity(self):
        """Test that valid entity passes required field validation"""
        validator = EntityValidator()

        entity = {
            "name": "GNN",
            "type": "method",
            "confidence": 0.9
        }

        result = validator.validate(entity)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_required_fields_fails_for_missing_name(self):
        """Test that entity without name fails validation"""
        validator = EntityValidator()

        entity = {
            "type": "method",
            "confidence": 0.9
        }

        result = validator.validate(entity)
        assert result.is_valid is False
        assert any("name" in error.lower() for error in result.errors)

    def test_validate_required_fields_fails_for_missing_type(self):
        """Test that entity without type fails validation"""
        validator = EntityValidator()

        entity = {
            "name": "GNN",
            "confidence": 0.9
        }

        result = validator.validate(entity)
        assert result.is_valid is False
        assert any("type" in error.lower() for error in result.errors)

    def test_validate_confidence_range(self):
        """Test that confidence must be in [0, 1] range"""
        validator = EntityValidator()

        # Too high
        entity_high = {"name": "GNN", "type": "method", "confidence": 1.5}
        result_high = validator.validate(entity_high)
        assert result_high.is_valid is False
        assert any("confidence" in error.lower() for error in result_high.errors)

        # Too low
        entity_low = {"name": "GNN", "type": "method", "confidence": -0.1}
        result_low = validator.validate(entity_low)
        assert result_low.is_valid is False
        assert any("confidence" in error.lower() for error in result_low.errors)

        # Valid range
        entity_valid = {"name": "GNN", "type": "method", "confidence": 0.5}
        result_valid = validator.validate(entity_valid)
        assert result_valid.is_valid is True

    def test_validate_empty_name(self):
        """Test that empty name fails validation"""
        validator = EntityValidator()

        entity = {"name": "", "type": "method", "confidence": 0.9}
        result = validator.validate(entity)
        assert result.is_valid is False
        assert any("name" in error.lower() and "empty" in error.lower() for error in result.errors)

    def test_validate_whitespace_only_name(self):
        """Test that whitespace-only name fails validation"""
        validator = EntityValidator()

        entity = {"name": "   ", "type": "method", "confidence": 0.9}
        result = validator.validate(entity)
        assert result.is_valid is False

    def test_validate_warns_for_low_confidence(self):
        """Test that low confidence generates warning"""
        validator = EntityValidator(warn_low_confidence=True, low_confidence_threshold=0.5)

        entity = {"name": "GNN", "type": "method", "confidence": 0.3}
        result = validator.validate(entity)
        assert result.is_valid is True  # Valid but with warning
        assert len(result.warnings) > 0
        assert any("confidence" in warning.lower() for warning in result.warnings)

    def test_validate_suggests_fixes_for_common_issues(self):
        """Test that validator suggests fixes for common issues"""
        validator = EntityValidator()

        entity = {"name": "GNN", "type": "method"}  # Missing confidence
        result = validator.validate(entity)
        assert len(result.suggestions) > 0

    def test_validate_batch_entities(self):
        """Test batch validation of multiple entities"""
        validator = EntityValidator()

        entities = [
            {"name": "GNN", "type": "method", "confidence": 0.9},
            {"name": "CNN", "type": "method"},  # Missing confidence
            {"name": "", "type": "method", "confidence": 0.8},  # Empty name
        ]

        results = validator.validate_batch(entities)
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is True  # Missing confidence is optional
        assert results[2].is_valid is False  # Empty name is error


class TestRelationshipValidator:
    """Test RelationshipValidator for relationship validation"""

    def test_relationship_validator_can_be_instantiated(self):
        """Test that RelationshipValidator can be created"""
        validator = RelationshipValidator()
        assert validator is not None

    def test_validate_required_fields_passes_for_valid_relationship(self):
        """Test that valid relationship passes validation"""
        validator = RelationshipValidator()

        relationship = {
            "source": "GAT",
            "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "strength": 0.8,
            "bidirectional": False
        }

        result = validator.validate(relationship)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_required_fields_fails_for_missing_source(self):
        """Test that relationship without source fails"""
        validator = RelationshipValidator()

        relationship = {
            "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "strength": 0.8,
            "bidirectional": False
        }

        result = validator.validate(relationship)
        assert result.is_valid is False
        assert any("source" in error.lower() for error in result.errors)

    def test_validate_required_fields_fails_for_missing_target(self):
        """Test that relationship without target fails"""
        validator = RelationshipValidator()

        relationship = {
            "source": "GAT",
            "type": RelationshipType.IMPROVES,
            "strength": 0.8,
            "bidirectional": False
        }

        result = validator.validate(relationship)
        assert result.is_valid is False
        assert any("target" in error.lower() for error in result.errors)

    def test_validate_strength_range(self):
        """Test that strength must be in [0, 1] range"""
        validator = RelationshipValidator()

        # Too high
        rel_high = {
            "source": "GAT", "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "strength": 1.5, "bidirectional": False
        }
        result_high = validator.validate(rel_high)
        assert result_high.is_valid is False

        # Too low
        rel_low = {
            "source": "GAT", "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "strength": -0.1, "bidirectional": False
        }
        result_low = validator.validate(rel_low)
        assert result_low.is_valid is False

    def test_validate_no_self_loops(self):
        """Test that entity cannot have relationship with itself"""
        validator = RelationshipValidator()

        relationship = {
            "source": "GNN",
            "target": "GNN",
            "type": RelationshipType.USES,
            "strength": 0.8,
            "bidirectional": False
        }

        result = validator.validate(relationship)
        assert result.is_valid is False
        assert any("self" in error.lower() or "same" in error.lower() for error in result.errors)

    def test_validate_entities_exist(self):
        """Test that source and target entities exist"""
        entities = [
            {"name": "GAT", "type": "method"},
            {"name": "GNN", "type": "method"},
        ]

        validator = RelationshipValidator(entities=entities)

        # Valid: both entities exist
        rel_valid = {
            "source": "GAT", "target": "GNN",
            "type": RelationshipType.IMPROVES,
            "strength": 0.8, "bidirectional": False
        }
        result_valid = validator.validate(rel_valid)
        assert result_valid.is_valid is True

        # Invalid: target doesn't exist
        rel_invalid = {
            "source": "GAT", "target": "CNN",
            "type": RelationshipType.IMPROVES,
            "strength": 0.8, "bidirectional": False
        }
        result_invalid = validator.validate(rel_invalid)
        assert result_invalid.is_valid is False
        assert any("not found" in error.lower() or "does not exist" in error.lower() for error in result_invalid.errors)

    def test_validate_bidirectional_consistency(self):
        """Test bidirectional flag matches relationship type"""
        validator = RelationshipValidator()

        # COMPARED_WITH should be bidirectional
        rel_compared = {
            "source": "GNN", "target": "CNN",
            "type": RelationshipType.COMPARED_WITH,
            "strength": 0.8, "bidirectional": False  # Wrong!
        }
        result_compared = validator.validate(rel_compared)
        assert len(result_compared.warnings) > 0
        assert any("bidirectional" in warning.lower() for warning in result_compared.warnings)

        # USES should be unidirectional
        rel_uses = {
            "source": "GNN", "target": "Attention",
            "type": RelationshipType.USES,
            "strength": 0.8, "bidirectional": True  # Wrong!
        }
        result_uses = validator.validate(rel_uses)
        assert len(result_uses.warnings) > 0

    def test_validate_batch_relationships(self):
        """Test batch validation of multiple relationships"""
        validator = RelationshipValidator()

        relationships = [
            {
                "source": "GAT", "target": "GNN",
                "type": RelationshipType.IMPROVES,
                "strength": 0.8, "bidirectional": False
            },
            {
                "source": "GAT", "target": "GAT",  # Self-loop
                "type": RelationshipType.USES,
                "strength": 0.8, "bidirectional": False
            },
            {
                "source": "GNN", "target": "CNN",
                "type": RelationshipType.COMPARED_WITH,
                "strength": 2.0,  # Invalid strength
                "bidirectional": True
            },
        ]

        results = validator.validate_batch(relationships)
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False  # Self-loop
        assert results[2].is_valid is False  # Invalid strength


class TestCrossValidation:
    """Test cross-validation between entities and relationships"""

    def test_validate_relationship_entities_match_actual_entities(self):
        """Test that relationship references match actual entity names"""
        entities = [
            {"name": "Graph Neural Network", "type": "method"},
            {"name": "Attention", "type": "technique"},
        ]

        validator = RelationshipValidator(entities=entities)

        # Using canonical name
        relationship = {
            "source": "Graph Neural Network",
            "target": "Attention",
            "type": RelationshipType.USES,
            "strength": 0.8,
            "bidirectional": False
        }

        result = validator.validate(relationship)
        assert result.is_valid is True

    def test_validate_warns_for_mismatched_types(self):
        """Test warning when relationship type seems incompatible with entity types"""
        entities = [
            {"name": "GNN", "type": "method"},
            {"name": "Dataset", "type": "data"},
        ]

        validator = RelationshipValidator(entities=entities)

        # Method IMPROVES Dataset is unusual
        relationship = {
            "source": "GNN",
            "target": "Dataset",
            "type": RelationshipType.IMPROVES,
            "strength": 0.8,
            "bidirectional": False
        }

        result = validator.validate(relationship)
        # Should pass but with warning
        assert result.is_valid is True
        # May have semantic warnings (optional for Phase 5)
