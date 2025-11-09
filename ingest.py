import os
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
# --- 修正点 1: フィルタリング用ユーティリティをインポート ---
from langchain_community.vectorstores.utils import filter_complex_metadata

# Directory containing the documents
DOCUMENTS_DIR = "documents"
# Chroma DB persistence directory
CHROMA_DB_DIR = "chroma_db"
# Collection name
COLLECTION_NAME = "research_agent_collection"

def main():
    """
    Ingests documents from the DOCUMENTS_DIR, creates embeddings, and stores them in ChromaDB.
    """
    print("Starting document ingestion...")

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11434"
    )

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
    )

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    total_docs_ingested = 0
    total_chunks_created = 0

    for filename in os.listdir(DOCUMENTS_DIR):
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        if os.path.isfile(filepath):
            try:
                print(f"Processing document: {filename}")
                loader = UnstructuredLoader(file_path=filepath)
                documents = loader.load()

                if not documents:
                    print(f"No content found in document: {filename}")
                    continue

                # --- 修正点 2: ChromaDBが受け入れられるようメタデータをフィルタリング ---
                filtered_documents = filter_complex_metadata(documents)
                # -----------------------------------------------------------------

                # フィルタリング済みのドキュメントを渡す
                splits = text_splitter.split_documents(filtered_documents)
                vectorstore.add_documents(splits)

                total_docs_ingested += 1
                total_chunks_created += len(splits)
                print(f"Successfully processed and added to vector store: {filename}")

            except Exception as e:
                print(f"Failed to process document {filename}: {e}")

    print("\nDocument ingestion complete.")
    print(f"Vector store updated at: {CHROMA_DB_DIR}")
    print(f"Total number of documents ingested: {total_docs_ingested}")
    print(f"Total number of chunks created: {total_chunks_created}")


if __name__ == "__main__":
    main()