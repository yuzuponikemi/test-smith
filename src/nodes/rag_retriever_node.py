from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

def rag_retriever(state):
    """
    RAG Retriever Node - Retrieves relevant chunks from ChromaDB knowledge base

    Uses nomic-embed-text for embedding queries (same model used during ingestion)
    to ensure embeddings are in the same vector space.
    """
    print("---RAG RETRIEVER---")
    plan = state["plan"]
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

    for query in plan:
        print(f"Retrieving from RAG for: {query}")

        try:
            documents = retriever.get_relevant_documents(query)

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
            print(f"  Retrieved {len(documents)} documents")

        except Exception as e:
            print(f"  Error retrieving for query '{query}': {e}")
            all_results.append(f"Error retrieving from knowledge base: {str(e)}\n")

    return {"rag_results": all_results}
