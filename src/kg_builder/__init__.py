"""
Knowledge Graph Builder Package

This package provides tools for extracting and building knowledge graphs
from research documents (papers, articles, etc.).

Phases:
- Phase 1: Entity Normalization and Linking
- Phase 2: Confidence Score Filtering and Recalculation
- Phase 3: Section-aware Extraction
- Phase 4: Enhanced Relationship Extraction
- Phase 5: Validation Layer
"""

from src.kg_builder.entity_linker import EntityLinker
from src.kg_builder.relationship_extractor import RelationshipExtractor, RelationshipType
from src.kg_builder.validators import ValidationResult, EntityValidator, RelationshipValidator

__all__ = [
    "EntityLinker",
    "RelationshipExtractor",
    "RelationshipType",
    "ValidationResult",
    "EntityValidator",
    "RelationshipValidator",
]
