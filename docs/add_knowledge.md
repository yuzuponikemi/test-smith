# Adding Knowledge to the Vector Database

This document explains how to add new documents to the vector database, allowing the research assistant to access a wider range of information.

## How it Works

The system uses a process called "ingestion" to build its knowledge base. Here's a simplified overview:

1.  **Document Loading:** The ingestion script reads all files from the `documents` directory. It uses `UnstructuredFileLoader`, which can handle various file formats like `.txt`, `.md`, `.pdf`, `.docx`, and more.
2.  **Text Splitting:** The loaded documents are split into smaller, manageable chunks. This is necessary for the language model to process them effectively.
3.  **Embedding:** Each chunk is converted into a numerical representation (an "embedding") using a local language model (Ollama).
4.  **Vector Store:** These embeddings are stored in a specialized database called a vector store (ChromaDB).

When you ask a question, the system searches this vector store to find the most relevant document chunks and uses them to construct an answer.

## Steps to Add New Documents

Adding new knowledge is straightforward:

1.  **Add Files:** Place the new documents you want to add into the `documents` directory. You can add multiple files at once.

2.  **Run the Ingestion Script:** Open your terminal and run the following command:

    ```bash
    python ingest.py
    ```

The script will process the new documents and add them to the existing vector database.

That's it! The research assistant will now be able to use the information from your newly added documents.
