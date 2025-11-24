"""
Knowledge Graph Builder Package

This package provides tools for extracting and building knowledge graphs
from research documents (papers, articles, etc.).

Phase 1 Focus: Entity Normalization and Linking
- Normalize entity names (abbreviations, case, aliases)
- Link similar entities based on embeddings
- Determine canonical names
"""

from src.kg_builder.entity_linker import EntityLinker

__all__ = ["EntityLinker"]
