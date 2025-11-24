"""
Entity Linker - Normalizes and links similar entities in knowledge graphs

Phase 1 Implementation:
1. Entity name normalization (abbreviations, case, whitespace)
2. Similarity-based entity linking (string + embedding)
3. Canonical name determination

Phase 2 Implementation:
1. Confidence score filtering
2. Confidence recalculation (frequency/relationship boosts)
3. Review flagging (borderline/isolated/low-occurrence)

Phase 3 Implementation:
1. Section recognition and normalization
2. Section-based importance weighting
3. Section-aware confidence adjustment
"""
from typing import Dict, List, Optional, Callable
from difflib import SequenceMatcher
import numpy as np


class EntityLinker:
    """
    Links and normalizes entity names to reduce redundancy in knowledge graphs.

    Features:
    - Abbreviation expansion (e.g., GNN -> Graph Neural Network)
    - Case normalization
    - Whitespace handling
    - Similarity-based entity matching
    - Canonical name determination
    """

    def __init__(
        self,
        abbreviations: Optional[Dict[str, str]] = None,
        preserve_case: bool = False,
        similarity_threshold: float = 0.8,
        embedding_function: Optional[Callable[[str], List[float]]] = None,
        cache_embeddings: bool = True,
        hybrid_mode: bool = False,
        hybrid_weight: float = 0.5,
        confidence_threshold: float = 0.3,
        review_margin: float = 0.1,
        min_occurrences: int = 1,
        section_weights: Optional[Dict[str, float]] = None,
        section_aware_filtering: bool = False
    ):
        """
        Initialize EntityLinker

        Args:
            abbreviations: Dictionary mapping abbreviations to full names
            preserve_case: If True, preserve original case; if False, lowercase
            similarity_threshold: Minimum similarity score (0-1) for entity matching
            embedding_function: Function that converts text to embedding vector
            cache_embeddings: If True, cache embeddings to avoid redundant computation
            hybrid_mode: If True, combine string and embedding similarity
            hybrid_weight: Weight for embedding similarity in hybrid mode (0-1)
            confidence_threshold: Minimum confidence score (0-1) for keeping entities
            review_margin: Margin around threshold for flagging borderline entities
            min_occurrences: Minimum number of occurrences to avoid review flag
            section_weights: Custom weights for paper sections (Phase 3)
            section_aware_filtering: If True, apply section weights before filtering (Phase 3)
        """
        self.abbreviations = abbreviations or {}
        self.preserve_case = preserve_case
        self.similarity_threshold = similarity_threshold
        self.embedding_function = embedding_function
        self.cache_embeddings = cache_embeddings
        self.hybrid_mode = hybrid_mode
        self.hybrid_weight = hybrid_weight
        self.confidence_threshold = confidence_threshold
        self.review_margin = review_margin
        self.min_occurrences = min_occurrences
        self.section_aware_filtering = section_aware_filtering

        # Create case-insensitive lookup for abbreviations
        self._abbrev_lookup = {k.upper(): v for k, v in self.abbreviations.items()}

        # Embedding cache
        self._embedding_cache: Dict[str, List[float]] = {}

        # Phase 3: Section weights for importance scoring
        self.section_weights = section_weights or {
            "abstract": 1.5,      # High importance - key concepts
            "introduction": 1.1,  # Moderate importance
            "methods": 1.3,       # High technical confidence
            "results": 1.2,       # Important findings
            "conclusion": 1.4,    # High importance - final takeaways
            "other": 1.0          # Base weight
        }

    def normalize(self, name: str) -> str:
        """
        Normalize an entity name

        Steps:
        1. Strip whitespace
        2. Expand abbreviations (preserves abbreviation dictionary case)
        3. Normalize case (preserves case for likely abbreviations)

        Args:
            name: Entity name to normalize

        Returns:
            Normalized entity name
        """
        if not name:
            return ""

        # Strip whitespace
        normalized = name.strip()

        # Expand abbreviations (case-insensitive lookup)
        upper_name = normalized.upper()
        if upper_name in self._abbrev_lookup:
            # Return the expanded form exactly as defined in the dictionary
            return self._abbrev_lookup[upper_name]

        # Normalize case (preserve case for likely abbreviations or if preserve_case=True)
        if not self.preserve_case:
            # Check if this looks like an abbreviation (all uppercase, length 2-10)
            if self._looks_like_abbreviation(normalized):
                # Preserve case for likely abbreviations
                return normalized
            normalized = normalized.lower()

        return normalized

    def _looks_like_abbreviation(self, name: str) -> bool:
        """
        Heuristic to detect if a name looks like an abbreviation

        Args:
            name: Entity name to check

        Returns:
            True if name looks like an abbreviation
        """
        # All uppercase and reasonable length (2-10 chars)
        return name.isupper() and 2 <= len(name) <= 10

    def find_similar(
        self,
        entity_name: str,
        entity_list: List[Dict],
        threshold: Optional[float] = None,
        use_embeddings: bool = True
    ) -> List[Dict]:
        """
        Find entities similar to the given name

        Args:
            entity_name: Entity name to search for
            entity_list: List of entity dictionaries with "name" key
            threshold: Override default similarity threshold
            use_embeddings: If True and embedding_function is available, use embeddings

        Returns:
            List of similar entities
        """
        if threshold is None:
            threshold = self.similarity_threshold

        # Normalize the query entity
        normalized_query = self.normalize(entity_name)

        similar = []
        for entity in entity_list:
            normalized_entity = self.normalize(entity["name"])

            # Exact match
            if normalized_query == normalized_entity:
                similar.append(entity)
                continue

            # Similarity match
            similarity = self._calculate_similarity(
                normalized_query,
                normalized_entity,
                use_embeddings=use_embeddings
            )
            if similarity >= threshold:
                similar.append(entity)

        return similar

    def link_entities(self, entities: List[Dict]) -> Dict:
        """
        Link similar entities and determine canonical names

        Args:
            entities: List of entity dictionaries with "name" and other metadata

        Returns:
            Dictionary containing:
            - canonical: Mapping from original names to canonical names
            - entities: List of entities with canonical names
            - groups: Groups of similar entities
        """
        # Group similar entities
        groups = []
        processed = set()

        for i, entity in enumerate(entities):
            entity_name = entity["name"]

            if entity_name in processed:
                continue

            # Find all similar entities
            similar = self.find_similar(entity_name, entities)

            if len(similar) > 1:
                # Create a group
                group_names = [e["name"] for e in similar]
                groups.append(group_names)

                # Mark as processed
                for name in group_names:
                    processed.add(name)

        # Determine canonical names for each group
        canonical = {}
        for group in groups:
            # Choose the most common/standard form as canonical
            # For now, choose the longest non-abbreviated form
            canonical_name = self._choose_canonical(group)

            for name in group:
                canonical[name] = canonical_name

        # Add singleton entities (not in any group)
        for entity in entities:
            if entity["name"] not in canonical:
                canonical[entity["name"]] = entity["name"]

        # Create linked entities with canonical names
        linked_entities = []
        for entity in entities:
            linked_entity = entity.copy()
            linked_entity["canonical_name"] = canonical[entity["name"]]
            linked_entities.append(linked_entity)

        return {
            "canonical": canonical,
            "entities": linked_entities,
            "groups": groups
        }

    def _calculate_similarity(
        self,
        name1: str,
        name2: str,
        use_embeddings: bool = True
    ) -> float:
        """
        Calculate similarity between two entity names

        Supports three modes:
        1. String similarity (SequenceMatcher)
        2. Embedding similarity (cosine distance)
        3. Hybrid (weighted combination)

        Args:
            name1: First entity name
            name2: Second entity name
            use_embeddings: If True, use embeddings when available

        Returns:
            Similarity score (0-1)
        """
        # String-based similarity
        string_sim = SequenceMatcher(None, name1, name2).ratio()

        # If no embedding function or not using embeddings, return string similarity
        if not use_embeddings or self.embedding_function is None:
            return string_sim

        # Embedding-based similarity
        embedding_sim = self._calculate_embedding_similarity(name1, name2)

        # Hybrid mode: combine both
        if self.hybrid_mode:
            return (
                self.hybrid_weight * embedding_sim +
                (1 - self.hybrid_weight) * string_sim
            )

        # Default: use embedding similarity
        return embedding_sim

    def _calculate_embedding_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate cosine similarity between embeddings of two entity names

        Args:
            name1: First entity name
            name2: Second entity name

        Returns:
            Cosine similarity score (0-1)
        """
        if self.embedding_function is None:
            raise ValueError("No embedding function provided")

        # Get embeddings
        emb1 = np.array(self._get_embedding(name1))
        emb2 = np.array(self._get_embedding(name2))

        # Calculate cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = dot_product / (norm1 * norm2)

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, cosine_sim))

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text, with optional caching

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.embedding_function is None:
            raise ValueError("No embedding function provided")

        # Check cache
        if self.cache_embeddings and text in self._embedding_cache:
            return self._embedding_cache[text]

        # Compute embedding
        embedding = self.embedding_function(text)

        # Store in cache
        if self.cache_embeddings:
            self._embedding_cache[text] = embedding

        return embedding

    def _choose_canonical(self, names: List[str]) -> str:
        """
        Choose canonical name from a group of similar names

        Strategy:
        1. Prefer expanded forms over abbreviations
        2. Prefer longer names (likely more descriptive)
        3. Prefer title case over other cases

        Args:
            names: List of similar entity names

        Returns:
            Canonical name
        """
        if not names:
            return ""

        if len(names) == 1:
            return names[0]

        # Sort by length (descending) to prefer longer, more descriptive names
        sorted_names = sorted(names, key=len, reverse=True)

        # Prefer non-all-uppercase names (likely not abbreviations)
        non_abbrev = [n for n in sorted_names if not n.isupper()]

        if non_abbrev:
            return non_abbrev[0]

        return sorted_names[0]

    # Phase 2: Confidence Score Filtering and Recalculation

    def filter_by_confidence(self, entities: List[Dict]) -> List[Dict]:
        """
        Filter entities by confidence threshold

        Args:
            entities: List of entity dictionaries with "confidence" field

        Returns:
            Filtered list of entities above confidence threshold
        """
        filtered = []
        for entity in entities:
            confidence = entity.get("confidence", 0.0)
            if confidence >= self.confidence_threshold:
                filtered.append(entity)

        return filtered

    def recalculate_confidence(self, entities: List[Dict]) -> List[Dict]:
        """
        Recalculate confidence scores based on contextual factors

        Factors considered:
        - Occurrence frequency (how many times entity appears)
        - Relationship count (how many connections entity has)
        - Isolated node penalty (entities with no relationships)
        - Section-based confidence boost (Phase 3):
          * Methods: +0.15 (high technical confidence)
          * Abstract: +0.10 (key concepts)
          * Conclusion: +0.12 (important takeaways)

        Args:
            entities: List of entity dictionaries

        Returns:
            List of entities with updated confidence scores
        """
        recalculated = []

        for entity in entities:
            original_confidence = entity.get("confidence", 0.5)
            occurrences = entity.get("occurrences", 1)
            relationship_count = entity.get("relationship_count", 0)
            section = entity.get("section")

            # Base score
            new_confidence = original_confidence

            # Frequency boost (logarithmic scale to avoid over-boosting)
            if occurrences > 1:
                frequency_boost = min(0.2, np.log(occurrences) * 0.05)
                new_confidence += frequency_boost

            # Relationship boost
            if relationship_count > 0:
                relationship_boost = min(0.2, relationship_count * 0.02)
                new_confidence += relationship_boost
            else:
                # Isolated node penalty
                new_confidence -= 0.1

            # Phase 3: Section-based confidence adjustment
            if section:
                normalized_section = self.recognize_section(section)

                # Methods section: boost technical confidence
                if normalized_section == "methods":
                    new_confidence += 0.15

                # Abstract section: boost for key concepts
                elif normalized_section == "abstract":
                    new_confidence += 0.10

                # Conclusion section: boost for important takeaways
                elif normalized_section == "conclusion":
                    new_confidence += 0.12

            # Clamp to [0, 1] range
            new_confidence = max(0.0, min(1.0, new_confidence))

            # Update entity
            updated_entity = entity.copy()
            updated_entity["confidence"] = new_confidence
            recalculated.append(updated_entity)

        return recalculated

    def flag_for_review(self, entities: List[Dict]) -> List[Dict]:
        """
        Flag entities that need human review

        Entities are flagged if:
        - Confidence is borderline (within review_margin of threshold)
        - Entity is isolated (no relationships)
        - Entity has low occurrence count

        Args:
            entities: List of entity dictionaries

        Returns:
            List of entities with review flags and reasons
        """
        flagged = []

        for entity in entities:
            entity_copy = entity.copy()
            confidence = entity.get("confidence", 0.5)
            relationship_count = entity.get("relationship_count")  # None if not present
            occurrences = entity.get("occurrences")  # None if not present

            needs_review = False
            review_reasons = []

            # Check if borderline confidence
            lower_bound = self.confidence_threshold - self.review_margin
            upper_bound = self.confidence_threshold + self.review_margin

            if lower_bound <= confidence <= upper_bound:
                needs_review = True
                review_reasons.append(f"Borderline confidence ({confidence:.2f})")

            # Check if isolated node (only if relationship_count is explicitly set)
            if relationship_count is not None and relationship_count == 0:
                needs_review = True
                review_reasons.append("Isolated node (no relationships)")

            # Check if low occurrence (only if occurrences is explicitly set)
            if occurrences is not None and occurrences < self.min_occurrences:
                needs_review = True
                review_reasons.append(f"Low occurrence (appears {occurrences} times)")

            # Add review flags
            entity_copy["needs_review"] = needs_review
            if needs_review:
                entity_copy["review_reason"] = "; ".join(review_reasons)

            flagged.append(entity_copy)

        return flagged

    # Phase 3: Section-aware Extraction

    def recognize_section(self, section_name: Optional[str]) -> str:
        """
        Recognize and normalize section names

        Handles:
        - Standard section names (Abstract, Introduction, Methods, Results, Conclusion)
        - Case-insensitive matching
        - Numbered sections (e.g., "1. Introduction")
        - Common variants (e.g., "Background" -> "introduction")

        Args:
            section_name: Raw section name from document

        Returns:
            Normalized section name (lowercase)
        """
        if not section_name or not section_name.strip():
            return "other"

        # Remove leading/trailing whitespace
        normalized = section_name.strip()

        # Remove numbering (e.g., "1. Introduction" -> "Introduction")
        import re
        normalized = re.sub(r'^[\d\.\s]+', '', normalized).strip()

        # Convert to lowercase for matching
        lower_section = normalized.lower()

        # Section mapping with variants
        section_mappings = {
            # Abstract
            "abstract": "abstract",

            # Introduction variants
            "introduction": "introduction",
            "background": "introduction",
            "related work": "introduction",
            "literature review": "introduction",

            # Methods variants
            "methods": "methods",
            "methodology": "methods",
            "approach": "methods",
            "experimental setup": "methods",
            "implementation": "methods",

            # Results variants
            "results": "results",
            "experiments": "results",
            "evaluation": "results",
            "results and discussion": "results",
            "findings": "results",

            # Conclusion variants
            "conclusion": "conclusion",
            "conclusions": "conclusion",
            "summary": "conclusion",
            "future work": "conclusion",
            "discussion": "conclusion",
        }

        # Exact match
        if lower_section in section_mappings:
            return section_mappings[lower_section]

        # Partial match (check if any key is in the section name)
        for key, value in section_mappings.items():
            if key in lower_section:
                return value

        return "other"

    def get_section_weight(self, section: str) -> float:
        """
        Get importance weight for a section

        Args:
            section: Normalized section name

        Returns:
            Section weight multiplier
        """
        # Normalize section name
        normalized_section = self.recognize_section(section)

        # Return weight from mapping
        return self.section_weights.get(normalized_section, 1.0)

    def apply_section_weight(self, entity: Dict) -> Dict:
        """
        Apply section-based importance weighting to an entity

        Calculates importance_score = confidence * section_weight

        Args:
            entity: Entity dictionary with "section" field

        Returns:
            Entity with added "importance_score" field
        """
        entity_copy = entity.copy()

        # Get section and confidence
        section = entity.get("section")
        confidence = entity.get("confidence", 0.5)

        # Get section weight
        section_weight = self.get_section_weight(section) if section else 1.0

        # Calculate importance score
        importance_score = confidence * section_weight

        # Add to entity
        entity_copy["importance_score"] = importance_score

        return entity_copy
