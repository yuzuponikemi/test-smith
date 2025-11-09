from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

def rag_retriever(state):
    print("---RAG RETRIEVER---")
    plan = state["plan"]
    all_results = []
    
    # Initialize ChromaDB
    embeddings = OllamaEmbeddings(model="llama3")
    vectorstore = Chroma(
        collection_name="research_agent_collection",
        embedding_function=embeddings,
        persist_directory="chroma_db",
    )
    
    for query in plan:
        print(f"Retrieving from RAG for: {query}")
        retriever = vectorstore.as_retriever()
        documents = retriever.get_relevant_documents(query)
        
        # Format the documents into a string
        doc_string = ""
        for doc in documents:
            doc_string += f"Content: {doc.page_content}\n"
            if doc.metadata:
                doc_string += f"Source: {doc.metadata.get('source', 'N/A')}\n"
            doc_string += "---\n"
        
        all_results.append(doc_string)
        
    return {"rag_results": all_results}
