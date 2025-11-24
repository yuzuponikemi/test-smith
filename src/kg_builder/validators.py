"""
Validators - Rule-based validation for entities and relationships

Phase 5 Implementation:
1. ValidationResult data class
2. EntityValidator for entity validation
3. RelationshipValidator for relationship validation
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from src.kg_builder.relationship_extractor import RelationshipType


@dataclass
class ValidationResult:
    """Result of validation with errors, warnings, and suggestions"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class EntityValidator:
    """
    Validates entities for required fields and data quality

    Features:
    - Required field validation (name, type)
    - Confidence range validation [0, 1]
    - Empty/whitespace name detection
    - Low confidence warnings
    - Batch validation support
    """

    def __init__(
        self,
        warn_low_confidence: bool = False,
        low_confidence_threshold: float = 0.5
    ):
        """
        Initialize EntityValidator

        Args:
            warn_low_confidence: If True, warn about low confidence entities
            low_confidence_threshold: Threshold for low confidence warning
        """
        self.warn_low_confidence = warn_low_confidence
        self.low_confidence_threshold = low_confidence_threshold

    def validate(self, entity: Dict) -> ValidationResult:
        """
        Validate a single entity

        Args:
            entity: Entity dictionary

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        suggestions = []

        # Check required field: name
        if "name" not in entity:
            errors.append("Missing required field: 'name'")
        elif not entity["name"] or not entity["name"].strip():
            errors.append("Entity name cannot be empty or whitespace-only")

        # Check required field: type
        if "type" not in entity:
            errors.append("Missing required field: 'type'")

        # Check confidence range
        if "confidence" in entity:
            confidence = entity["confidence"]
            if not isinstance(confidence, (int, float)):
                errors.append(f"Confidence must be numeric, got {type(confidence).__name__}")
            elif confidence < 0.0 or confidence > 1.0:
                errors.append(f"Confidence must be in [0, 1] range, got {confidence}")
            elif self.warn_low_confidence and confidence < self.low_confidence_threshold:
                warnings.append(f"Low confidence ({confidence:.2f}) below threshold ({self.low_confidence_threshold})")
        else:
            # Missing confidence is allowed but suggest adding it
            suggestions.append("Consider adding 'confidence' field for quality assessment")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_batch(self, entities: List[Dict]) -> List[ValidationResult]:
        """
        Validate multiple entities

        Args:
            entities: List of entity dictionaries

        Returns:
            List of ValidationResults
        """
        return [self.validate(entity) for entity in entities]


class RelationshipValidator:
    """
    Validates relationships for required fields and logical consistency

    Features:
    - Required field validation (source, target, type, strength, bidirectional)
    - Strength range validation [0, 1]
    - Self-loop detection
    - Entity existence validation
    - Bidirectional consistency checking
    - Batch validation support
    """

    def __init__(self, entities: Optional[List[Dict]] = None):
        """
        Initialize RelationshipValidator

        Args:
            entities: Optional list of entities to validate against
        """
        self.entities = entities or []
        self._entity_names = {e["name"] for e in self.entities if "name" in e}

    def validate(self, relationship: Dict) -> ValidationResult:
        """
        Validate a single relationship

        Args:
            relationship: Relationship dictionary

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        suggestions = []

        # Check required fields
        if "source" not in relationship:
            errors.append("Missing required field: 'source'")
        if "target" not in relationship:
            errors.append("Missing required field: 'target'")
        if "type" not in relationship:
            errors.append("Missing required field: 'type'")

        # Check strength range
        if "strength" in relationship:
            strength = relationship["strength"]
            if not isinstance(strength, (int, float)):
                errors.append(f"Strength must be numeric, got {type(strength).__name__}")
            elif strength < 0.0 or strength > 1.0:
                errors.append(f"Strength must be in [0, 1] range, got {strength}")

        # Check for self-loops (entity relating to itself)
        if "source" in relationship and "target" in relationship:
            if relationship["source"] == relationship["target"]:
                errors.append(f"Self-loop detected: entity '{relationship['source']}' cannot relate to itself")

        # Check entity existence (if entities provided)
        if self.entities:
            if "source" in relationship and relationship["source"] not in self._entity_names:
                errors.append(f"Source entity '{relationship['source']}' not found in entity list")
            if "target" in relationship and relationship["target"] not in self._entity_names:
                errors.append(f"Target entity '{relationship['target']}' not found in entity list")

        # Check bidirectional consistency
        if "type" in relationship and "bidirectional" in relationship:
            rel_type = relationship["type"]
            bidirectional = relationship["bidirectional"]

            # Expected bidirectionality based on type
            expected_bidirectional = rel_type in [
                RelationshipType.COMPARED_WITH,
                RelationshipType.RELATED_TO
            ]

            if bidirectional != expected_bidirectional:
                warnings.append(
                    f"Bidirectional flag ({bidirectional}) inconsistent with type "
                    f"'{rel_type.value if isinstance(rel_type, RelationshipType) else rel_type}' "
                    f"(expected {expected_bidirectional})"
                )

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_batch(self, relationships: List[Dict]) -> List[ValidationResult]:
        """
        Validate multiple relationships

        Args:
            relationships: List of relationship dictionaries

        Returns:
            List of ValidationResults
        """
        return [self.validate(relationship) for relationship in relationships]
