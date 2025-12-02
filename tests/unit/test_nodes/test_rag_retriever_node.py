"""
Tests for RAG Retriever Node - Knowledge base retrieval from ChromaDB

Coverage target: 100%
Testing strategy: Mock ChromaDB and embeddings, test all code paths
"""

from typing import Any
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.nodes.rag_retriever_node import rag_retriever

# ============================================================================
# Test RAG Retriever Node
# ============================================================================


class TestRAGRetrieverNode:
    """Test RAG retriever node logic"""

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_no_rag_queries_skips_retrieval(
        self, mock_get_embeddings, mock_chroma, mock_print_header
    ):
        """Should skip retrieval when no rag_queries in state"""
        # Arrange
        state: dict[str, Any] = {"rag_queries": []}

        # Act
        result = rag_retriever(state)

        # Assert
        assert result == {"rag_results": [], "rag_sources": []}
        mock_print_header.assert_called_once_with("RAG RETRIEVER")
        mock_get_embeddings.assert_not_called()
        mock_chroma.assert_not_called()

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_missing_rag_queries_key_skips_retrieval(
        self, mock_get_embeddings, mock_chroma, mock_print_header
    ):
        """Should skip retrieval when rag_queries key is missing"""
        # Arrange
        state: dict[str, Any] = {}  # No rag_queries key

        # Act
        result = rag_retriever(state)

        # Assert
        assert result == {"rag_results": [], "rag_sources": []}
        mock_print_header.assert_called_once_with("RAG RETRIEVER")
        mock_get_embeddings.assert_not_called()
        mock_chroma.assert_not_called()

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_successful_single_retrieval(self, mock_get_embeddings, mock_chroma, mock_print_header):
        """Should execute successful retrieval with single query"""
        # Arrange
        state: dict[str, Any] = {"rag_queries": ["What is LangGraph?"]}

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock retrieved documents with scores
        mock_doc1 = Document(
            page_content="LangGraph is a framework for building stateful workflows.",
            metadata={"source": "docs/langgraph.md"},
        )
        mock_doc2 = Document(
            page_content="It uses directed graphs to represent agent workflows.",
            metadata={"source": "docs/architecture.md"},
        )

        # Mock vectorstore with similarity_search_with_score
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.15),  # (doc, distance_score)
            (mock_doc2, 0.25),
        ]
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert len(result["rag_results"]) == 1
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 2  # 2 documents retrieved

        # Check formatted output contains expected content
        formatted_output = result["rag_results"][0]
        assert "Retrieved 2 relevant chunks" in formatted_output
        assert "What is LangGraph?" in formatted_output
        assert "LangGraph is a framework" in formatted_output
        assert "It uses directed graphs" in formatted_output
        assert "docs/langgraph.md" in formatted_output
        assert "docs/architecture.md" in formatted_output

        # Verify embeddings were initialized correctly
        mock_get_embeddings.assert_called_once_with("chroma_db", "research_agent_collection")

        # Verify Chroma was initialized correctly
        mock_chroma.assert_called_once_with(
            collection_name="research_agent_collection",
            embedding_function=mock_embeddings,
            persist_directory="chroma_db",
        )

        # Verify similarity_search_with_score was called with correct query
        mock_vectorstore.similarity_search_with_score.assert_called_once_with(
            "What is LangGraph?", k=5
        )

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_successful_multiple_retrievals(
        self, mock_get_embeddings, mock_chroma, mock_print_header
    ):
        """Should execute multiple successful retrievals"""
        # Arrange
        state: dict[str, Any] = {
            "rag_queries": [
                "What is LangGraph?",
                "How does ChromaDB work?",
                "Explain RAG architecture",
            ]
        }

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock vectorstore with different results for each query
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.side_effect = [
            [(Document(page_content="LangGraph answer", metadata={"source": "doc1.md"}), 0.1)],
            [(Document(page_content="ChromaDB answer", metadata={"source": "doc2.md"}), 0.2)],
            [(Document(page_content="RAG answer", metadata={"source": "doc3.md"}), 0.3)],
        ]
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert len(result["rag_results"]) == 3
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 3  # 3 queries, each with 1 document

        # Check each result contains expected query
        assert "What is LangGraph?" in result["rag_results"][0]
        assert "How does ChromaDB work?" in result["rag_results"][1]
        assert "Explain RAG architecture" in result["rag_results"][2]

        # Verify similarity_search_with_score was called 3 times
        assert mock_vectorstore.similarity_search_with_score.call_count == 3

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_empty_retrieval_results(self, mock_get_embeddings, mock_chroma, mock_print_header):
        """Should handle empty retrieval results (no documents found)"""
        # Arrange
        state: dict[str, Any] = {"rag_queries": ["Very obscure query"]}

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock vectorstore with empty results
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.return_value = []  # No documents found
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert len(result["rag_results"]) == 1
        assert "No relevant chunks found for query: Very obscure query" in result["rag_results"][0]
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 0  # No documents found

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_retrieval_error_handling(self, mock_get_embeddings, mock_chroma, mock_print_header):
        """Should handle retrieval errors gracefully"""
        # Arrange
        state: dict[str, Any] = {"rag_queries": ["Query that will fail"]}

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock vectorstore to raise exception
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.side_effect = Exception(
            "ChromaDB connection failed"
        )
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert len(result["rag_results"]) == 1
        assert "Error retrieving from knowledge base" in result["rag_results"][0]
        assert "ChromaDB connection failed" in result["rag_results"][0]
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 0  # Error occurred, no sources

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_mixed_success_and_failure(self, mock_get_embeddings, mock_chroma, mock_print_header):
        """Should handle mix of successful and failed retrievals"""
        # Arrange
        state: dict[str, Any] = {
            "rag_queries": [
                "Successful query 1",
                "Failed query",
                "Successful query 2",
            ]
        }

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock vectorstore with mixed results
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.side_effect = [
            [(Document(page_content="Success 1", metadata={"source": "doc1.md"}), 0.1)],
            Exception("Retrieval failed"),
            [(Document(page_content="Success 2", metadata={"source": "doc2.md"}), 0.2)],
        ]
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert len(result["rag_results"]) == 3
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 2  # Only 2 successful retrievals

        # First result: successful
        assert "Success 1" in result["rag_results"][0]

        # Second result: error
        assert "Error retrieving from knowledge base" in result["rag_results"][1]
        assert "Retrieval failed" in result["rag_results"][1]

        # Third result: successful
        assert "Success 2" in result["rag_results"][2]

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_document_formatting_without_metadata(
        self, mock_get_embeddings, mock_chroma, mock_print_header
    ):
        """Should handle documents without metadata gracefully"""
        # Arrange
        state: dict[str, Any] = {"rag_queries": ["Test query"]}

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock document without metadata
        mock_doc = Document(
            page_content="Content without metadata",
            metadata={},  # Empty metadata
        )

        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.return_value = [(mock_doc, 0.1)]
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert len(result["rag_results"]) == 1
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 1  # 1 document retrieved

        formatted_output = result["rag_results"][0]

        # Should contain content
        assert "Content without metadata" in formatted_output

        # When metadata is empty, Source line is not included
        # (Source is only shown when metadata is not empty)
        assert "Source:" not in formatted_output

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_retrieval_k_parameter(self, mock_get_embeddings, mock_chroma, mock_print_header):
        """Should configure retriever with k=5 parameter"""
        # Arrange
        state: dict[str, Any] = {"rag_queries": ["Test query"]}

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (Document(page_content=f"Result {i}", metadata={}), 0.1 * i) for i in range(5)
        ]
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        # Verify k=5 was passed to similarity_search_with_score
        mock_vectorstore.similarity_search_with_score.assert_called_once_with("Test query", k=5)

        # Should retrieve 5 documents
        assert "Retrieved 5 relevant chunks" in result["rag_results"][0]
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 5  # 5 documents retrieved

    @patch("src.nodes.rag_retriever_node.print_node_header")
    @patch("src.nodes.rag_retriever_node.Chroma")
    @patch("src.nodes.rag_retriever_node.get_embeddings_for_collection")
    def test_results_ordering_preserved(self, mock_get_embeddings, mock_chroma, mock_print_header):
        """Should preserve order of retrieval results"""
        # Arrange
        state: dict[str, Any] = {
            "rag_queries": [
                "Query A",
                "Query B",
                "Query C",
            ]
        }

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_get_embeddings.return_value = mock_embeddings

        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search_with_score.side_effect = [
            [(Document(page_content="Result A", metadata={}), 0.1)],
            [(Document(page_content="Result B", metadata={}), 0.2)],
            [(Document(page_content="Result C", metadata={}), 0.3)],
        ]
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = rag_retriever(state)

        # Assert
        assert "rag_sources" in result
        assert len(result["rag_sources"]) == 3  # 3 documents retrieved

        # Results should be in same order as queries
        assert "Query A" in result["rag_results"][0]
        assert "Result A" in result["rag_results"][0]

        assert "Query B" in result["rag_results"][1]
        assert "Result B" in result["rag_results"][1]

        assert "Query C" in result["rag_results"][2]
        assert "Result C" in result["rag_results"][2]
