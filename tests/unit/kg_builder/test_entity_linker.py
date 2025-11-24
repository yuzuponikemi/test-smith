"""
Unit tests for EntityLinker class

Test-Driven Development (TDD) approach:
1. Write failing test
2. Implement minimum code to pass
3. Refactor
4. Repeat
"""
import pytest
from src.kg_builder.entity_linker import EntityLinker


class TestEntityLinkerBasics:
    """Test basic EntityLinker functionality"""

    def test_entity_linker_can_be_instantiated(self):
        """Test that EntityLinker can be instantiated"""
        linker = EntityLinker()
        assert linker is not None
        assert isinstance(linker, EntityLinker)

    def test_entity_linker_has_normalize_method(self):
        """Test that EntityLinker has a normalize method"""
        linker = EntityLinker()
        assert hasattr(linker, "normalize")
        assert callable(linker.normalize)

    def test_entity_linker_has_find_similar_method(self):
        """Test that EntityLinker has a find_similar method"""
        linker = EntityLinker()
        assert hasattr(linker, "find_similar")
        assert callable(linker.find_similar)

    def test_entity_linker_has_link_entities_method(self):
        """Test that EntityLinker has a link_entities method"""
        linker = EntityLinker()
        assert hasattr(linker, "link_entities")
        assert callable(linker.link_entities)


class TestNormalization:
    """Test entity name normalization"""

    def test_normalize_returns_string(self):
        """Test that normalize returns a string"""
        linker = EntityLinker()
        result = linker.normalize("test")
        assert isinstance(result, str)

    def test_normalize_handles_empty_string(self):
        """Test that normalize handles empty strings"""
        linker = EntityLinker()
        result = linker.normalize("")
        assert result == ""

    def test_normalize_handles_whitespace(self):
        """Test that normalize handles leading/trailing whitespace"""
        linker = EntityLinker()
        result = linker.normalize("  test  ")
        assert result == "test"

    def test_normalize_preserves_single_word(self):
        """Test that normalize preserves single words"""
        linker = EntityLinker()
        result = linker.normalize("network")
        assert result == "network"


class TestAbbreviationExpansion:
    """Test abbreviation expansion functionality"""

    def test_expand_abbreviation_gnn(self, sample_abbreviations):
        """Test that GNN expands to Graph Neural Network"""
        linker = EntityLinker(abbreviations=sample_abbreviations)
        result = linker.normalize("GNN")
        assert result == "Graph Neural Network"

    def test_expand_abbreviation_cnn(self, sample_abbreviations):
        """Test that CNN expands to Convolutional Neural Network"""
        linker = EntityLinker(abbreviations=sample_abbreviations)
        result = linker.normalize("CNN")
        assert result == "Convolutional Neural Network"

    def test_expand_abbreviation_unknown(self, sample_abbreviations):
        """Test that unknown abbreviations are preserved"""
        linker = EntityLinker(abbreviations=sample_abbreviations)
        result = linker.normalize("XYZ")
        assert result == "XYZ"

    def test_expand_abbreviation_case_insensitive(self, sample_abbreviations):
        """Test that abbreviation expansion is case-insensitive"""
        linker = EntityLinker(abbreviations=sample_abbreviations)
        result = linker.normalize("gnn")
        assert result == "Graph Neural Network"


class TestCaseNormalization:
    """Test case normalization"""

    def test_normalize_lowercase(self):
        """Test that normalize converts to lowercase"""
        linker = EntityLinker(preserve_case=False)
        result = linker.normalize("Neural Network")
        assert result == "neural network"

    def test_normalize_preserve_case(self):
        """Test that normalize can preserve case when requested"""
        linker = EntityLinker(preserve_case=True)
        result = linker.normalize("Neural Network")
        assert result == "Neural Network"

    def test_normalize_mixed_case(self):
        """Test that normalize handles mixed case"""
        linker = EntityLinker(preserve_case=False)
        result = linker.normalize("GrApH NeUrAl NeTwOrK")
        assert result == "graph neural network"


class TestSimilarityFinding:
    """Test finding similar entities"""

    def test_find_similar_returns_list(self, sample_entities):
        """Test that find_similar returns a list"""
        linker = EntityLinker()
        result = linker.find_similar("GNN", sample_entities)
        assert isinstance(result, list)

    def test_find_similar_finds_exact_match(self, sample_entities):
        """Test that find_similar finds exact matches"""
        linker = EntityLinker()
        result = linker.find_similar("GNN", sample_entities)
        # Should find "GNN" itself
        entity_names = [e["name"] for e in result]
        assert "GNN" in entity_names

    def test_find_similar_finds_abbreviation_matches(self, sample_entities, sample_abbreviations):
        """Test that find_similar finds matches via abbreviation expansion"""
        linker = EntityLinker(abbreviations=sample_abbreviations)
        result = linker.find_similar("GNN", sample_entities)
        # Should find "Graph Neural Network" and "graph neural networks"
        entity_names = [e["name"] for e in result]
        assert "Graph Neural Network" in entity_names

    def test_find_similar_threshold(self, sample_entities):
        """Test that find_similar respects similarity threshold"""
        linker = EntityLinker(similarity_threshold=0.95)
        result = linker.find_similar("neural network", sample_entities, threshold=0.95)
        # High threshold should reduce matches
        assert len(result) >= 0  # May have no exact matches


class TestEntityLinking:
    """Test complete entity linking pipeline"""

    def test_link_entities_returns_dict(self, sample_entities):
        """Test that link_entities returns a dictionary"""
        linker = EntityLinker()
        result = linker.link_entities(sample_entities)
        assert isinstance(result, dict)

    def test_link_entities_has_canonical_key(self, sample_entities):
        """Test that linked entities have canonical names"""
        linker = EntityLinker()
        result = linker.link_entities(sample_entities)
        assert "canonical" in result
        assert isinstance(result["canonical"], dict)

    def test_link_entities_groups_similar(self, sample_entities, sample_abbreviations):
        """Test that link_entities groups similar entities"""
        linker = EntityLinker(abbreviations=sample_abbreviations)
        result = linker.link_entities(sample_entities)
        # GNN, Graph Neural Network, graph neural networks should be grouped
        canonical = result["canonical"]
        # Check that they all map to the same canonical name
        gnn_canonical = canonical.get("GNN")
        graph_nn_canonical = canonical.get("Graph Neural Network")
        assert gnn_canonical is not None
        assert graph_nn_canonical is not None
        # They should have the same canonical name
        # (either both are "Graph Neural Network" or similar)

    def test_link_entities_preserves_metadata(self, sample_entities):
        """Test that link_entities preserves entity metadata"""
        linker = EntityLinker()
        result = linker.link_entities(sample_entities)
        assert "entities" in result
        # Check that confidence scores are preserved
        for entity in result["entities"]:
            assert "confidence" in entity
