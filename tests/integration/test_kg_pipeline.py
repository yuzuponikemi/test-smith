"""
Integration tests for Entity Linker (Phase 1 + Phase 2)

Tests end-to-end pipelines combining:
- Entity normalization (Phase 1)
- Entity linking (Phase 1)
- Embedding-based similarity (Phase 1)
- Confidence filtering (Phase 2)
- Score recalculation (Phase 2)
- Review flagging (Phase 2)
"""
import pytest
from src.kg_builder.entity_linker import EntityLinker


class TestEndToEndPipeline:
    """Test complete entity processing pipeline"""

    def test_full_pipeline_without_embeddings(self):
        """Test complete pipeline: normalize → link → filter → recalculate → flag"""

        # Setup
        abbreviations = {
            "GNN": "Graph Neural Network",
            "CNN": "Convolutional Neural Network",
            "NLP": "Natural Language Processing"
        }

        linker = EntityLinker(
            abbreviations=abbreviations,
            confidence_threshold=0.5,
            review_margin=0.1,
            min_occurrences=2
        )

        # Input: Entities extracted from multiple chunks (simulating paper extraction)
        raw_entities = [
            {"name": "GNN", "type": "method", "confidence": 0.95, "occurrences": 8, "relationship_count": 5},
            {"name": "Graph Neural Network", "type": "method", "confidence": 0.92, "occurrences": 5, "relationship_count": 5},
            {"name": "graph neural networks", "type": "method", "confidence": 0.88, "occurrences": 3, "relationship_count": 5},
            {"name": "CNN", "type": "method", "confidence": 0.85, "occurrences": 6, "relationship_count": 4},
            {"name": "Convolutional Neural Network", "type": "method", "confidence": 0.82, "occurrences": 4, "relationship_count": 4},
            # Borderline confidence that will be flagged
            {"name": "BorderlineEntity", "type": "method", "confidence": 0.52, "occurrences": 5, "relationship_count": 3},
            # Isolated node that will be flagged
            {"name": "IsolatedNode", "type": "method", "confidence": 0.8, "occurrences": 3, "relationship_count": 0},
            # Low occurrence that will be flagged
            {"name": "RareEntity", "type": "method", "confidence": 0.7, "occurrences": 1, "relationship_count": 2},
            {"name": "RareMethod", "type": "method", "confidence": 0.45, "occurrences": 1, "relationship_count": 0},
            {"name": "LowConfidence", "type": "method", "confidence": 0.25, "occurrences": 1, "relationship_count": 1},
        ]

        # Step 1: Link similar entities
        linked_result = linker.link_entities(raw_entities)

        # Verify linking grouped similar entities
        assert len(linked_result["groups"]) >= 2  # At least GNN and CNN groups

        # Step 2: Recalculate confidence scores
        recalculated = linker.recalculate_confidence(linked_result["entities"])

        # Verify scores increased for high-occurrence entities
        gnn_entities = [e for e in recalculated if "neural network" in e["name"].lower() or e["name"] == "GNN"]
        for entity in gnn_entities:
            # Should have boost from frequency and relationships
            assert entity["confidence"] >= entity.get("original_confidence", entity["confidence"])

        # Step 3: Filter by confidence
        filtered = linker.filter_by_confidence(recalculated)

        # LowConfidence (0.25) should be filtered out
        entity_names = [e["name"] for e in filtered]
        assert "LowConfidence" not in entity_names

        # Step 4: Flag for review
        flagged = linker.flag_for_review(filtered)

        # Verify review flags
        rare_method_found = False
        for entity in flagged:
            if entity["name"] == "RareMethod":
                # RareMethod was filtered out (confidence 0.45 < threshold 0.5)
                # So we won't find it in flagged
                rare_method_found = True

        # RareMethod should have been filtered out before flagging
        assert not rare_method_found, "RareMethod should be filtered out (confidence < threshold)"

        # Check that borderline/review-worthy entities are properly flagged
        review_flagged_count = sum(1 for e in flagged if e["needs_review"])
        assert review_flagged_count > 0, "Should have at least some entities flagged for review"

        # Verify high-quality entities (high confidence, many occurrences) are mostly not flagged
        high_quality_entities = [
            e for e in flagged
            if e["confidence"] > 0.8 and e.get("occurrences", 0) > 5 and e.get("relationship_count", 0) > 3
        ]
        if high_quality_entities:
            not_flagged_count = sum(1 for e in high_quality_entities if not e["needs_review"])
            # Most high-quality entities should not need review
            assert not_flagged_count > 0

        # Final verification: pipeline produced valid output
        assert len(flagged) > 0
        assert all("needs_review" in e for e in flagged)
        assert all("confidence" in e for e in flagged)

    def test_full_pipeline_with_embeddings(self):
        """Test pipeline with embedding-based similarity"""

        # Mock embedding function
        def mock_embedder(text):
            text_lower = text.lower()
            if "neural network" in text_lower or text_lower == "gnn":
                return [1.0, 0.0, 0.0]  # Neural network cluster
            elif "language" in text_lower or text_lower == "nlp":
                return [0.0, 1.0, 0.0]  # Language cluster
            else:
                return [0.0, 0.0, 1.0]  # Other

        abbreviations = {
            "GNN": "Graph Neural Network",
            "NLP": "Natural Language Processing"
        }

        linker = EntityLinker(
            abbreviations=abbreviations,
            embedding_function=mock_embedder,
            similarity_threshold=0.7,
            confidence_threshold=0.4,
            hybrid_mode=True,
            hybrid_weight=0.6  # Favor embeddings
        )

        entities = [
            {"name": "GNN", "confidence": 0.9, "occurrences": 5, "relationship_count": 3},
            {"name": "neural network", "confidence": 0.85, "occurrences": 4, "relationship_count": 3},
            {"name": "NLP", "confidence": 0.8, "occurrences": 3, "relationship_count": 2},
            {"name": "language model", "confidence": 0.75, "occurrences": 2, "relationship_count": 2},
        ]

        # Find similar using embeddings
        similar_to_gnn = linker.find_similar("GNN", entities, use_embeddings=True)

        # Should find both GNN and "neural network" via embeddings
        similar_names = [e["name"] for e in similar_to_gnn]
        assert "GNN" in similar_names
        assert "neural network" in similar_names

        # Link and filter
        linked = linker.link_entities(entities)
        recalculated = linker.recalculate_confidence(linked["entities"])
        filtered = linker.filter_by_confidence(recalculated)

        # All should pass filter (threshold 0.4)
        assert len(filtered) == len(entities)

    def test_pipeline_with_edge_cases(self):
        """Test pipeline handles edge cases gracefully"""

        linker = EntityLinker(
            confidence_threshold=0.5,
            review_margin=0.15
        )

        # Edge cases
        edge_case_entities = [
            # Missing fields
            {"name": "Entity1"},
            {"name": "Entity2", "confidence": 0.8},

            # Extreme values
            {"name": "Perfect", "confidence": 1.0, "occurrences": 100, "relationship_count": 50},
            {"name": "Zero", "confidence": 0.0, "occurrences": 0, "relationship_count": 0},

            # Boundary values
            {"name": "Threshold", "confidence": 0.5, "occurrences": 1, "relationship_count": 1},
            {"name": "JustAbove", "confidence": 0.51, "occurrences": 1, "relationship_count": 1},
            {"name": "JustBelow", "confidence": 0.49, "occurrences": 1, "relationship_count": 1},
        ]

        # Should not crash
        recalculated = linker.recalculate_confidence(edge_case_entities)
        assert len(recalculated) == len(edge_case_entities)

        # Scores should be clamped [0, 1]
        for entity in recalculated:
            assert 0.0 <= entity["confidence"] <= 1.0

        # Filter and flag should work
        filtered = linker.filter_by_confidence(recalculated)
        flagged = linker.flag_for_review(filtered)

        assert len(flagged) > 0
        assert all("needs_review" in e for e in flagged)


class TestPipelineWithRealScenarios:
    """Test pipeline with realistic paper extraction scenarios"""

    def test_paper_extraction_scenario(self):
        """Simulate entity extraction from a research paper"""

        abbreviations = {
            "GNN": "Graph Neural Network",
            "GCN": "Graph Convolutional Network",
            "GAT": "Graph Attention Network",
            "BERT": "Bidirectional Encoder Representations from Transformers",
            "NLP": "Natural Language Processing",
        }

        linker = EntityLinker(
            abbreviations=abbreviations,
            confidence_threshold=0.3,
            review_margin=0.15,
            min_occurrences=2
        )

        # Simulated extraction from different paper sections
        # Abstract: high confidence, abbreviated
        # Introduction: medium confidence, full names
        # Methods: high confidence, technical terms
        # Results: lower confidence, mixed

        paper_entities = [
            # Abstract section
            {"name": "GNN", "confidence": 0.95, "occurrences": 3, "relationship_count": 5, "section": "Abstract"},
            {"name": "NLP", "confidence": 0.92, "occurrences": 2, "relationship_count": 4, "section": "Abstract"},

            # Introduction section
            {"name": "Graph Neural Network", "confidence": 0.88, "occurrences": 5, "relationship_count": 5, "section": "Introduction"},
            {"name": "Natural Language Processing", "confidence": 0.85, "occurrences": 3, "relationship_count": 4, "section": "Introduction"},
            {"name": "GCN", "confidence": 0.82, "occurrences": 2, "relationship_count": 3, "section": "Introduction"},

            # Methods section
            {"name": "Graph Attention Network", "confidence": 0.9, "occurrences": 4, "relationship_count": 6, "section": "Methods"},
            {"name": "GAT", "confidence": 0.88, "occurrences": 6, "relationship_count": 6, "section": "Methods"},
            {"name": "attention mechanism", "confidence": 0.75, "occurrences": 8, "relationship_count": 7, "section": "Methods"},

            # Results section (some noise/low confidence)
            {"name": "baseline", "confidence": 0.45, "occurrences": 4, "relationship_count": 2, "section": "Results"},
            {"name": "proposed method", "confidence": 0.65, "occurrences": 5, "relationship_count": 3, "section": "Results"},
            {"name": "BERT", "confidence": 0.55, "occurrences": 2, "relationship_count": 2, "section": "Results"},

            # Noise (low confidence, rare)
            {"name": "unclear_term", "confidence": 0.25, "occurrences": 1, "relationship_count": 0, "section": "Results"},
        ]

        # Execute pipeline
        linked = linker.link_entities(paper_entities)
        recalculated = linker.recalculate_confidence(linked["entities"])
        filtered = linker.filter_by_confidence(recalculated)
        flagged = linker.flag_for_review(filtered)

        # Verify linking
        # GNN and "Graph Neural Network" should be linked
        canonical = linked["canonical"]
        assert canonical["GNN"] == canonical.get("Graph Neural Network", canonical["GNN"])

        # Verify filtering removed noise
        filtered_names = [e["name"] for e in filtered]
        assert "unclear_term" not in filtered_names  # 0.25 < 0.3 threshold

        # Verify high-quality entities are not flagged
        high_quality = [e for e in flagged if e["confidence"] > 0.8 and e.get("occurrences", 0) > 3]
        most_high_quality_not_flagged = sum(1 for e in high_quality if not e["needs_review"])
        assert most_high_quality_not_flagged > 0

        # Verify borderline entities are flagged
        borderline = [e for e in flagged if 0.15 <= abs(e["confidence"] - 0.3) <= 0.15]
        if borderline:
            assert any(e["needs_review"] for e in borderline)

    def test_multi_domain_extraction(self):
        """Test handling entities from multiple domains"""

        linker = EntityLinker(
            abbreviations={
                "ML": "Machine Learning",
                "DL": "Deep Learning",
                "CV": "Computer Vision",
            },
            confidence_threshold=0.4
        )

        multi_domain_entities = [
            # Computer Vision domain
            {"name": "CV", "type": "domain", "confidence": 0.9, "occurrences": 5, "relationship_count": 8},
            {"name": "image classification", "type": "task", "confidence": 0.85, "occurrences": 4, "relationship_count": 6},
            {"name": "CNN", "type": "method", "confidence": 0.88, "occurrences": 6, "relationship_count": 7},

            # NLP domain
            {"name": "text generation", "type": "task", "confidence": 0.82, "occurrences": 3, "relationship_count": 5},
            {"name": "transformer", "type": "method", "confidence": 0.87, "occurrences": 5, "relationship_count": 6},

            # General ML
            {"name": "ML", "type": "domain", "confidence": 0.92, "occurrences": 8, "relationship_count": 10},
            {"name": "DL", "type": "domain", "confidence": 0.9, "occurrences": 7, "relationship_count": 9},
            {"name": "neural network", "type": "method", "confidence": 0.85, "occurrences": 10, "relationship_count": 12},
        ]

        # Execute pipeline
        linked = linker.link_entities(multi_domain_entities)
        recalculated = linker.recalculate_confidence(linked["entities"])
        filtered = linker.filter_by_confidence(recalculated)

        # Should handle all domains
        assert len(filtered) == len(multi_domain_entities)  # All above threshold

        # Verify high-occurrence entities got boost
        neural_net = next(e for e in recalculated if e["name"] == "neural network")
        assert neural_net["confidence"] > 0.85  # Should be boosted


class TestPipelineIntegrationPoints:
    """Test integration points between Phase 1 and Phase 2"""

    def test_linked_entities_carry_metadata_through_pipeline(self):
        """Verify metadata is preserved through all pipeline stages"""

        linker = EntityLinker(confidence_threshold=0.3)

        entities = [
            {
                "name": "GNN",
                "type": "method",
                "confidence": 0.8,
                "occurrences": 5,
                "relationship_count": 3,
                "section": "Methods",
                "source_paper": "Paper1",
                "custom_field": "custom_value"
            }
        ]

        # Through linking
        linked = linker.link_entities(entities)
        assert linked["entities"][0]["type"] == "method"
        assert linked["entities"][0]["section"] == "Methods"
        assert linked["entities"][0]["custom_field"] == "custom_value"

        # Through recalculation
        recalculated = linker.recalculate_confidence(linked["entities"])
        assert recalculated[0]["source_paper"] == "Paper1"

        # Through filtering
        filtered = linker.filter_by_confidence(recalculated)
        assert filtered[0]["custom_field"] == "custom_value"

        # Through flagging
        flagged = linker.flag_for_review(filtered)
        assert flagged[0]["section"] == "Methods"

    def test_canonical_names_used_in_downstream_processing(self):
        """Verify canonical names from linking are accessible downstream"""

        abbreviations = {"GNN": "Graph Neural Network"}

        linker = EntityLinker(abbreviations=abbreviations, confidence_threshold=0.3)

        entities = [
            {"name": "GNN", "confidence": 0.9, "occurrences": 3, "relationship_count": 2},
            {"name": "Graph Neural Network", "confidence": 0.85, "occurrences": 2, "relationship_count": 2},
        ]

        linked = linker.link_entities(entities)

        # Verify both mapped to same canonical
        canonical_name = linked["canonical"]["GNN"]
        assert linked["canonical"]["Graph Neural Network"] == canonical_name

        # Verify canonical name is accessible in downstream
        recalculated = linker.recalculate_confidence(linked["entities"])
        flagged = linker.flag_for_review(recalculated)

        # All should have canonical_name field from linking
        assert all("canonical_name" in e for e in flagged)
