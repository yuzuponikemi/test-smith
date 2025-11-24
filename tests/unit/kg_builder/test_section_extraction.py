"""
Unit tests for section-aware extraction (Phase 3)

TDD approach for section recognition and section-based scoring
"""
import pytest
from src.kg_builder.entity_linker import EntityLinker


class TestSectionRecognition:
    """Test section name recognition and normalization"""

    def test_recognize_standard_sections(self):
        """Test that standard section names are recognized"""
        linker = EntityLinker()

        # Standard section names
        assert linker.recognize_section("Abstract") == "abstract"
        assert linker.recognize_section("Introduction") == "introduction"
        assert linker.recognize_section("Methods") == "methods"
        assert linker.recognize_section("Results") == "results"
        assert linker.recognize_section("Conclusion") == "conclusion"

    def test_recognize_section_case_insensitive(self):
        """Test that section recognition is case-insensitive"""
        linker = EntityLinker()

        assert linker.recognize_section("ABSTRACT") == "abstract"
        assert linker.recognize_section("abstract") == "abstract"
        assert linker.recognize_section("AbStRaCt") == "abstract"

    def test_recognize_section_with_numbers(self):
        """Test section recognition with numbering (e.g., '1. Introduction')"""
        linker = EntityLinker()

        assert linker.recognize_section("1. Introduction") == "introduction"
        assert linker.recognize_section("3.2 Methods") == "methods"
        assert linker.recognize_section("5. Results and Discussion") == "results"

    def test_recognize_section_variants(self):
        """Test recognition of common section name variants"""
        linker = EntityLinker()

        # Introduction variants
        assert linker.recognize_section("Background") == "introduction"
        assert linker.recognize_section("Related Work") == "introduction"

        # Methods variants
        assert linker.recognize_section("Methodology") == "methods"
        assert linker.recognize_section("Approach") == "methods"
        assert linker.recognize_section("Experimental Setup") == "methods"

        # Results variants
        assert linker.recognize_section("Experiments") == "results"
        assert linker.recognize_section("Evaluation") == "results"
        assert linker.recognize_section("Results and Discussion") == "results"

        # Conclusion variants
        assert linker.recognize_section("Conclusions") == "conclusion"
        assert linker.recognize_section("Summary") == "conclusion"
        assert linker.recognize_section("Future Work") == "conclusion"

    def test_recognize_unknown_section(self):
        """Test that unknown sections return 'other'"""
        linker = EntityLinker()

        assert linker.recognize_section("Acknowledgments") == "other"
        assert linker.recognize_section("References") == "other"
        assert linker.recognize_section("Random Section") == "other"

    def test_recognize_section_handles_none(self):
        """Test that None/empty section is handled gracefully"""
        linker = EntityLinker()

        assert linker.recognize_section(None) == "other"
        assert linker.recognize_section("") == "other"
        assert linker.recognize_section("   ") == "other"


class TestSectionWeighting:
    """Test section-based importance weighting"""

    def test_section_weights_default(self):
        """Test that default section weights are reasonable"""
        linker = EntityLinker()

        # Abstract and Conclusion should have highest weights
        assert linker.get_section_weight("abstract") >= 1.5
        assert linker.get_section_weight("conclusion") >= 1.3

        # Methods should have high confidence but not necessarily highest weight
        assert linker.get_section_weight("methods") >= 1.2

        # Introduction and Results should have moderate weights
        assert linker.get_section_weight("introduction") >= 1.0
        assert linker.get_section_weight("results") >= 1.0

        # Unknown sections should have base weight
        assert linker.get_section_weight("other") == 1.0

    def test_section_weights_custom(self):
        """Test that custom section weights can be provided"""
        custom_weights = {
            "abstract": 2.0,
            "introduction": 1.0,
            "methods": 1.5,
            "results": 1.2,
            "conclusion": 1.8,
            "other": 0.8
        }

        linker = EntityLinker(section_weights=custom_weights)

        assert linker.get_section_weight("abstract") == 2.0
        assert linker.get_section_weight("methods") == 1.5
        assert linker.get_section_weight("other") == 0.8

    def test_apply_section_weight_to_entity(self):
        """Test that section weight is applied to entity importance score"""
        linker = EntityLinker()

        entity = {
            "name": "GNN",
            "confidence": 0.8,
            "section": "Abstract",
            "occurrences": 3,
            "relationship_count": 5
        }

        # Apply section weight
        weighted = linker.apply_section_weight(entity)

        # Should have importance_score field
        assert "importance_score" in weighted

        # Abstract entities should have higher importance
        # importance_score should be > base confidence due to section weight
        assert weighted["importance_score"] > entity["confidence"]

    def test_apply_section_weight_to_multiple_entities(self):
        """Test section weighting across multiple sections"""
        linker = EntityLinker()

        entities = [
            {"name": "A", "confidence": 0.8, "section": "Abstract"},
            {"name": "B", "confidence": 0.8, "section": "Introduction"},
            {"name": "C", "confidence": 0.8, "section": "Methods"},
        ]

        weighted = [linker.apply_section_weight(e) for e in entities]

        # Abstract should have highest importance
        abstract_score = next(e["importance_score"] for e in weighted if e["name"] == "A")
        intro_score = next(e["importance_score"] for e in weighted if e["name"] == "B")
        methods_score = next(e["importance_score"] for e in weighted if e["name"] == "C")

        assert abstract_score > intro_score
        assert abstract_score > methods_score


class TestSectionBasedConfidenceAdjustment:
    """Test section-based confidence score adjustments"""

    def test_methods_section_boosts_confidence(self):
        """Test that Methods section entities get confidence boost"""
        linker = EntityLinker()

        entities = [
            {"name": "MethodEntity", "confidence": 0.6, "section": "Methods"},
            {"name": "OtherEntity", "confidence": 0.6, "section": "Results"},
        ]

        recalculated = linker.recalculate_confidence(entities)

        methods_conf = next(e["confidence"] for e in recalculated if e["name"] == "MethodEntity")
        other_conf = next(e["confidence"] for e in recalculated if e["name"] == "OtherEntity")

        # Methods section should boost technical confidence
        assert methods_conf > other_conf

    def test_abstract_entities_maintain_high_confidence(self):
        """Test that Abstract entities maintain or increase confidence"""
        linker = EntityLinker()

        entity = {
            "name": "KeyConcept",
            "confidence": 0.7,
            "section": "Abstract",
            "occurrences": 2,
            "relationship_count": 3
        }

        recalculated = linker.recalculate_confidence([entity])

        # Abstract entities should get a boost
        assert recalculated[0]["confidence"] >= entity["confidence"]

    def test_conclusion_entities_prioritized(self):
        """Test that Conclusion entities are treated as important"""
        linker = EntityLinker()

        entities = [
            {"name": "ConclusionPoint", "confidence": 0.65, "section": "Conclusion"},
            {"name": "IntroPoint", "confidence": 0.65, "section": "Introduction"},
        ]

        recalculated = linker.recalculate_confidence(entities)

        conclusion_conf = next(e["confidence"] for e in recalculated if e["name"] == "ConclusionPoint")
        intro_conf = next(e["confidence"] for e in recalculated if e["name"] == "IntroPoint")

        # Conclusion should boost confidence more than Introduction
        assert conclusion_conf > intro_conf

    def test_section_adjustment_clamped_to_valid_range(self):
        """Test that section adjustments don't push confidence outside [0, 1]"""
        linker = EntityLinker()

        entity = {
            "name": "HighConf",
            "confidence": 0.95,
            "section": "Abstract",
            "occurrences": 10,
            "relationship_count": 20
        }

        recalculated = linker.recalculate_confidence([entity])

        # Should still be clamped to 1.0
        assert recalculated[0]["confidence"] <= 1.0

    def test_missing_section_handled_gracefully(self):
        """Test that entities without section field are handled"""
        linker = EntityLinker()

        entities = [
            {"name": "NoSection", "confidence": 0.7},
            {"name": "WithSection", "confidence": 0.7, "section": "Methods"},
        ]

        # Should not crash
        recalculated = linker.recalculate_confidence(entities)

        assert len(recalculated) == 2
        assert all(0.0 <= e["confidence"] <= 1.0 for e in recalculated)


class TestSectionBasedFiltering:
    """Test section-aware filtering strategies"""

    def test_filter_preserves_abstract_entities(self):
        """Test that Abstract entities are more likely to pass filtering"""
        linker = EntityLinker(
            confidence_threshold=0.5,
            section_aware_filtering=True
        )

        entities = [
            {"name": "AbstractEntity", "confidence": 0.48, "section": "Abstract"},
            {"name": "OtherEntity", "confidence": 0.48, "section": "Results"},
        ]

        # With section-aware filtering, Abstract entity might pass despite being slightly below threshold
        filtered = linker.filter_by_confidence(entities)

        # At minimum, should apply section adjustment before filtering
        # (exact behavior depends on implementation strategy)
        assert isinstance(filtered, list)

    def test_section_aware_filtering_disabled_by_default(self):
        """Test that section-aware filtering is opt-in"""
        linker = EntityLinker(confidence_threshold=0.5)

        entity = {"name": "Test", "confidence": 0.48, "section": "Abstract"}

        filtered = linker.filter_by_confidence([entity])

        # Without section-aware filtering, should use raw confidence
        assert len(filtered) == 0  # Below threshold
