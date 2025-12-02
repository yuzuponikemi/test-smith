import os
from datetime import datetime

from langchain_chroma import Chroma

from src.utils.embedding_utils import get_embeddings_for_collection
from src.utils.logging_utils import print_node_header


def rag_retriever(state):
    """
    RAG Retriever Node - Retrieves relevant chunks from ChromaDB knowledge base

    Uses strategically allocated rag_queries from the planner.
    These queries are specifically chosen for information that should be in:
    - Internal documentation
    - Domain-specific knowledge
    - Established concepts and procedures

    IMPORTANT: Dynamically selects embedding model from collection metadata
    to ensure embeddings match the model used during ingestion.

    Returns both legacy rag_results and new rag_sources for provenance tracking.
    """
    print_node_header("RAG RETRIEVER")
    rag_queries = state.get("rag_queries", [])

    if not rag_queries:
        print("  No RAG queries allocated - skipping knowledge base search")
        return {"rag_results": [], "rag_sources": []}

    print(f"  Executing {len(rag_queries)} knowledge base searches")

    all_results = []
    rag_sources = []  # New: structured provenance tracking
    source_counter = 0

    # Initialize ChromaDB with correct embedding model (from collection metadata)
    collection_name = "research_agent_collection"
    persist_directory = "chroma_db"

    embeddings = get_embeddings_for_collection(persist_directory, collection_name)
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    for query in rag_queries:
        print(f"  Retrieving from KB for: {query}")
        timestamp = datetime.now().isoformat()

        try:
            # Use similarity search with scores for provenance
            docs_with_scores = vectorstore.similarity_search_with_score(query, k=5)

            # Format the documents into a string (legacy format)
            doc_string = ""
            if docs_with_scores:
                doc_string += (
                    f"=== Retrieved {len(docs_with_scores)} relevant chunks for '{query}' ===\n\n"
                )

                for i, (doc, score) in enumerate(docs_with_scores, 1):
                    source_counter += 1
                    source_id = f"rag_{source_counter}"

                    # Legacy format
                    doc_string += f"[Chunk {i}]\n"
                    doc_string += f"Content: {doc.page_content}\n"
                    if doc.metadata:
                        doc_string += f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                    doc_string += "---\n"

                    # Extract structured source metadata for provenance
                    source_file = (
                        doc.metadata.get("source", "Unknown") if doc.metadata else "Unknown"
                    )

                    # Create structured source reference
                    source_ref = {
                        "source_id": source_id,
                        "source_type": "rag",
                        "url": None,  # KB sources don't have URLs
                        "title": os.path.basename(source_file)
                        if source_file != "Unknown"
                        else "Unknown Document",
                        "content_snippet": doc.page_content[:500] if doc.page_content else "",
                        "query_used": query,
                        "timestamp": timestamp,
                        "relevance_score": float(1 - score)
                        if score
                        else 0.5,  # Convert distance to similarity
                        "metadata": {
                            "source_file": source_file,
                            "chunk_index": i,
                            "full_content_length": len(doc.page_content) if doc.page_content else 0,
                            **{k: v for k, v in (doc.metadata or {}).items() if k != "source"},
                        },
                    }
                    rag_sources.append(source_ref)
            else:
                doc_string = f"No relevant chunks found for query: {query}\n"

            all_results.append(doc_string)
            print(f"    Retrieved {len(docs_with_scores)} documents")

        except Exception as e:
            print(f"    Error retrieving for query '{query}': {e}")
            all_results.append(f"Error retrieving from knowledge base: {str(e)}\n")

    print(f"  Completed {len(all_results)} KB searches")
    print(f"  Captured {len(rag_sources)} source references for provenance")

    return {"rag_results": all_results, "rag_sources": rag_sources}
