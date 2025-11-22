from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from src.utils.logging_utils import print_node_header
def rag_retriever(state):
    """
    RAG Retriever Node - Retrieves relevant chunks from ChromaDB knowledge base

    Uses strategically allocated rag_queries from the planner.
    These queries are specifically chosen for information that should be in:
    - Internal documentation
    - Domain-specific knowledge
    - Established concepts and procedures

    IMPORTANT: Uses nomic-embed-text for embedding queries (same model used during ingestion)
    to ensure embeddings are in the same vector space.
    """
    print_node_header("RAG RETRIEVER")
    rag_queries = state.get("rag_queries", [])

    if not rag_queries:
        print("  No RAG queries allocated - skipping knowledge base search")
        return {"rag_results": []}

    print(f"  Executing {len(rag_queries)} knowledge base searches")

    all_results = []

    # Initialize ChromaDB with correct embedding model
    # IMPORTANT: Must use nomic-embed-text (same model used in ingestion)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(
        collection_name="research_agent_collection",
        embedding_function=embeddings,
        persist_directory="chroma_db",
    )

    # Configure retriever with k=5 chunks per query
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    for query in rag_queries:
        print(f"  Retrieving from KB for: {query}")

        try:
            # Use invoke() instead of get_relevant_documents() for newer LangChain versions
            documents = retriever.invoke(query)

            # Format the documents into a string
            doc_string = ""
            if documents:
                doc_string += f"=== Retrieved {len(documents)} relevant chunks for '{query}' ===\n\n"
                for i, doc in enumerate(documents, 1):
                    doc_string += f"[Chunk {i}]\n"
                    doc_string += f"Content: {doc.page_content}\n"
                    if doc.metadata:
                        doc_string += f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                    doc_string += "---\n"
            else:
                doc_string = f"No relevant chunks found for query: {query}\n"

            all_results.append(doc_string)
            print(f"    Retrieved {len(documents)} documents")

        except Exception as e:
            print(f"    Error retrieving for query '{query}': {e}")
            all_results.append(f"Error retrieving from knowledge base: {str(e)}\n")

    print(f"  Completed {len(all_results)} KB searches")
    return {"rag_results": all_results}
