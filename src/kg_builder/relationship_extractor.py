"""
Relationship Extractor - Extracts and scores relationships between entities

Phase 4 Implementation:
1. Relationship type classification (USES, IMPROVES, BASED_ON, COMPARED_WITH, RELATED_TO)
2. Relationship strength scoring
3. Bidirectional relationship inference
4. Context-based relationship detection
"""
from typing import Dict, List, Optional
from enum import Enum
import re
import numpy as np


class RelationshipType(Enum):
    """Enumeration of relationship types in knowledge graphs"""
    USES = "uses"  # Entity A uses entity B (e.g., "GNN uses message passing")
    IMPROVES = "improves"  # Entity A improves entity B (e.g., "GAT improves GNN")
    BASED_ON = "based_on"  # Entity A is based on entity B (e.g., "GAT is based on attention")
    COMPARED_WITH = "compared_with"  # Entity A is compared with entity B (bidirectional)
    RELATED_TO = "related_to"  # Generic relationship (bidirectional)


class RelationshipExtractor:
    """
    Extracts relationships between entities from knowledge graphs.

    Features:
    - Relationship type classification
    - Context-based pattern matching
    - Strength scoring
    - Bidirectional inference
    """

    def __init__(self, min_strength: float = 0.0):
        """
        Initialize RelationshipExtractor

        Args:
            min_strength: Minimum strength threshold (0-1) for keeping relationships
        """
        self.min_strength = min_strength

        # Pattern definitions for relationship detection
        self._relationship_patterns = {
            RelationshipType.USES: [
                r'\b(\w+)\s+uses?\s+(\w+)',
                r'\b(\w+)\s+utilizes?\s+(\w+)',
                r'\b(\w+)\s+employs?\s+(\w+)',
                r'\b(\w+)\s+applies?\s+(\w+)',
            ],
            RelationshipType.IMPROVES: [
                r'\b(\w+)\s+improves?\s+(\w+)',
                r'\b(\w+)\s+outperforms?\s+(\w+)',
                r'\b(\w+)\s+surpasses?\s+(\w+)',
                r'\b(\w+)\s+(?:achieves?|gets?)\s+better\s+(?:results?|performance)\s+than\s+(\w+)',
            ],
            RelationshipType.BASED_ON: [
                r'\b(\w+)\s+(?:is\s+)?based\s+on\s+(\w+)',
                r'\b(\w+)\s+builds?\s+(?:up)?on\s+(\w+)',
                r'\b(\w+)\s+derives?\s+from\s+(\w+)',
                r'\b(\w+)\s+extends?\s+(\w+)',
            ],
            RelationshipType.COMPARED_WITH: [
                r'\b(\w+)\s+(?:is\s+)?compared\s+(?:with|to|against)\s+(\w+)',
                r'\b(\w+)\s+vs\.?\s+(\w+)',
                r'\b(\w+)\s+versus\s+(\w+)',
            ],
        }

        # Bidirectional relationship types
        self._bidirectional_types = {
            RelationshipType.COMPARED_WITH,
            RelationshipType.RELATED_TO,
        }

    def extract_relationships(self, entities: List[Dict]) -> List[Dict]:
        """
        Extract relationships from a list of entities

        Args:
            entities: List of entity dictionaries with "name", "type", and optional "context"

        Returns:
            List of relationship dictionaries with:
            - source: Source entity name
            - target: Target entity name
            - type: RelationshipType
            - strength: Confidence score (0-1)
            - bidirectional: Whether relationship is bidirectional
            - context: Supporting text (if available)
        """
        if not entities:
            return []

        relationships = []

        # Extract relationships from entity contexts
        for entity in entities:
            if "context" not in entity or not entity["context"]:
                continue

            context = entity["context"]
            entity_name = entity["name"]

            # Try to match relationship patterns
            for rel_type, patterns in self._relationship_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, context, re.IGNORECASE)

                    for match in matches:
                        source = match.group(1)
                        target = match.group(2)

                        # Check if matched terms correspond to actual entities
                        source_entity = self._find_entity_by_name(entities, source)
                        target_entity = self._find_entity_by_name(entities, target)

                        if source_entity and target_entity:
                            relationship = {
                                "source": source_entity["name"],
                                "target": target_entity["name"],
                                "type": rel_type,
                                "context": context,
                                "frequency": 1,
                            }

                            # Score strength
                            relationship["strength"] = self.score_strength(relationship)

                            # Infer bidirectionality
                            relationship["bidirectional"] = self.infer_bidirectional(relationship)

                            # Filter by minimum strength
                            if relationship["strength"] >= self.min_strength:
                                # Include entity metadata
                                relationship["source_metadata"] = {
                                    "type": source_entity.get("type"),
                                    "confidence": source_entity.get("confidence"),
                                }
                                relationship["target_metadata"] = {
                                    "type": target_entity.get("type"),
                                    "confidence": target_entity.get("confidence"),
                                }

                                relationships.append(relationship)

            # Additional pass: Check for relationships where subject is implicit
            # (e.g., "GAT uses attention and improves GNN" - "improves GNN" has no explicit subject)
            relationships.extend(self._extract_implicit_subject_relationships(entity, entities, context))

        # Deduplicate relationships
        relationships = self._deduplicate_relationships(relationships)

        return relationships

    def score_strength(self, relationship: Dict) -> float:
        """
        Score the strength/confidence of a relationship

        Factors:
        - Context length (longer = more detailed = higher confidence)
        - Relationship type (explicit types like USES have higher strength)
        - Frequency (how many times relationship appears)

        Args:
            relationship: Relationship dictionary

        Returns:
            Strength score (0-1)
        """
        base_score = 0.5

        # Factor 1: Relationship type specificity
        rel_type = relationship.get("type")
        if rel_type in [RelationshipType.USES, RelationshipType.IMPROVES, RelationshipType.BASED_ON]:
            # Explicit relationships have higher base score
            base_score = 0.7
        elif rel_type == RelationshipType.COMPARED_WITH:
            base_score = 0.6
        else:  # RELATED_TO
            base_score = 0.4

        # Factor 2: Context richness (longer context = higher confidence)
        context = relationship.get("context", "")
        if context:
            # Normalize context length contribution (0.0 to 0.2)
            context_boost = min(0.2, len(context) / 500)
            base_score += context_boost

        # Factor 3: Frequency boost
        frequency = relationship.get("frequency", 1)
        if frequency > 1:
            # Logarithmic boost for frequency
            frequency_boost = min(0.2, np.log(frequency) * 0.05)
            base_score += frequency_boost

        # Clamp to [0, 1]
        strength = max(0.0, min(1.0, base_score))

        return strength

    def infer_bidirectional(self, relationship: Dict) -> bool:
        """
        Infer whether a relationship is bidirectional

        Rules:
        - COMPARED_WITH: Always bidirectional
        - RELATED_TO: Always bidirectional
        - USES, IMPROVES, BASED_ON: Always unidirectional

        Args:
            relationship: Relationship dictionary

        Returns:
            True if bidirectional, False if unidirectional
        """
        rel_type = relationship.get("type")
        return rel_type in self._bidirectional_types

    def _find_entity_by_name(self, entities: List[Dict], name: str) -> Optional[Dict]:
        """
        Find an entity by name (case-insensitive partial match)

        Args:
            entities: List of entities
            name: Entity name to search for

        Returns:
            Matching entity or None
        """
        name_lower = name.lower()

        # First try exact match
        for entity in entities:
            if entity["name"].lower() == name_lower:
                return entity

        # Then try partial match
        for entity in entities:
            entity_name_lower = entity["name"].lower()
            if name_lower in entity_name_lower or entity_name_lower in name_lower:
                return entity

        return None

    def _extract_implicit_subject_relationships(
        self,
        source_entity: Dict,
        all_entities: List[Dict],
        context: str
    ) -> List[Dict]:
        """
        Extract relationships where the subject is implicit (e.g., "and improves GNN")

        Args:
            source_entity: The entity providing context (assumed subject)
            all_entities: All entities to check against
            context: The text context

        Returns:
            List of relationships with implicit subject
        """
        relationships = []

        # Patterns for implicit subject (e.g., "and improves GNN", "to improve GNN")
        implicit_patterns = {
            RelationshipType.USES: [
                r'\band\s+uses?\s+(\w+)',
                r'\band\s+utilizes?\s+(\w+)',
                r'\band\s+employs?\s+(\w+)',
                r'\bto\s+use\s+(\w+)',
                r'\bto\s+utilize\s+(\w+)',
            ],
            RelationshipType.IMPROVES: [
                r'\band\s+improves?\s+(\w+)',
                r'\band\s+outperforms?\s+(\w+)',
                r'\bto\s+improve\s+(\w+)',
                r'\bto\s+outperform\s+(\w+)',
            ],
            RelationshipType.BASED_ON: [
                r'\band\s+(?:is\s+)?based\s+on\s+(\w+)',
                r'\band\s+extends?\s+(\w+)',
                r'\bto\s+extend\s+(\w+)',
            ],
        }

        for rel_type, patterns in implicit_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, context, re.IGNORECASE)

                for match in matches:
                    target_name = match.group(1)

                    # Find target entity
                    target_entity = self._find_entity_by_name(all_entities, target_name)

                    if target_entity and target_entity["name"] != source_entity["name"]:
                        relationship = {
                            "source": source_entity["name"],
                            "target": target_entity["name"],
                            "type": rel_type,
                            "context": context,
                            "frequency": 1,
                        }

                        # Score strength
                        relationship["strength"] = self.score_strength(relationship)

                        # Infer bidirectionality
                        relationship["bidirectional"] = self.infer_bidirectional(relationship)

                        # Filter by minimum strength
                        if relationship["strength"] >= self.min_strength:
                            # Include entity metadata
                            relationship["source_metadata"] = {
                                "type": source_entity.get("type"),
                                "confidence": source_entity.get("confidence"),
                            }
                            relationship["target_metadata"] = {
                                "type": target_entity.get("type"),
                                "confidence": target_entity.get("confidence"),
                            }

                            relationships.append(relationship)

        return relationships

    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """
        Remove duplicate relationships

        Args:
            relationships: List of relationships

        Returns:
            Deduplicated list
        """
        seen = set()
        deduplicated = []

        for rel in relationships:
            # Create a unique key for the relationship
            key = (
                rel["source"],
                rel["target"],
                rel["type"].value if isinstance(rel["type"], RelationshipType) else rel["type"]
            )

            if key not in seen:
                seen.add(key)
                deduplicated.append(rel)
            else:
                # If duplicate, update frequency
                for existing_rel in deduplicated:
                    existing_key = (
                        existing_rel["source"],
                        existing_rel["target"],
                        existing_rel["type"].value if isinstance(existing_rel["type"], RelationshipType) else existing_rel["type"]
                    )
                    if existing_key == key:
                        existing_rel["frequency"] = existing_rel.get("frequency", 1) + 1
                        # Recalculate strength with updated frequency
                        existing_rel["strength"] = self.score_strength(existing_rel)
                        break

        return deduplicated
