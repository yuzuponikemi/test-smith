"""
Pytest configuration and shared fixtures
"""
import pytest
from typing import List, Dict


@pytest.fixture
def sample_entities() -> List[Dict[str, any]]:
    """Sample entities for testing entity linking"""
    return [
        {
            "name": "GNN",
            "type": "method",
            "confidence": 0.95,
        },
        {
            "name": "Graph Neural Network",
            "type": "method",
            "confidence": 0.92,
        },
        {
            "name": "graph neural networks",
            "type": "method",
            "confidence": 0.88,
        },
        {
            "name": "CNN",
            "type": "method",
            "confidence": 0.93,
        },
        {
            "name": "Convolutional Neural Network",
            "type": "method",
            "confidence": 0.91,
        },
    ]


@pytest.fixture
def sample_abbreviations() -> Dict[str, str]:
    """Sample abbreviation dictionary"""
    return {
        "GNN": "Graph Neural Network",
        "CNN": "Convolutional Neural Network",
        "RNN": "Recurrent Neural Network",
        "LSTM": "Long Short-Term Memory",
        "GRU": "Gated Recurrent Unit",
        "NLP": "Natural Language Processing",
        "CV": "Computer Vision",
        "ML": "Machine Learning",
        "DL": "Deep Learning",
        "AI": "Artificial Intelligence",
    }


@pytest.fixture
def sample_entity_pairs() -> List[tuple]:
    """Sample entity pairs for similarity testing"""
    return [
        ("Graph Neural Network", "graph neural networks", True),  # Should match
        ("GNN", "Graph Neural Network", True),  # Should match (abbreviation)
        ("CNN", "RNN", False),  # Should not match (different concepts)
        ("neural network", "Neural Network", True),  # Should match (case)
        ("Transformer", "BERT", False),  # Should not match (related but different)
    ]
