"""
Embedding Utilities - Centralized embedding model configuration

This module ensures alignment between embedding creation (ingestion) and
embedding usage (retrieval) by:
1. Providing a single source of truth for embedding models
2. Storing embedding model info in collection metadata
3. Dynamically selecting the correct model during retrieval

Usage:
    # During ingestion
    from src.utils.embedding_utils import get_embeddings, store_embedding_metadata

    embeddings = get_embeddings()  # Uses default model
    vectorstore = Chroma(...)
    store_embedding_metadata(vectorstore, "mxbai-embed-large")

    # During retrieval
    from src.utils.embedding_utils import get_embeddings_for_collection

    embeddings = get_embeddings_for_collection("chroma_db", "my_collection")
"""

from langchain_ollama import OllamaEmbeddings

# Default embedding model configuration
DEFAULT_EMBEDDING_MODEL = "mxbai-embed-large"
OLLAMA_BASE_URL = "http://localhost:11434"

# Supported embedding models with their configurations
EMBEDDING_MODELS = {
    "mxbai-embed-large": {
        "dimensions": 1024,
        "description": "State-of-the-art large embedding model from mixedbread.ai",
        "max_batch_size": 10,  # Conservative batch size for stability
    },
    "nomic-embed-text": {
        "dimensions": 768,
        "description": "Nomic AI's text embedding model",
        "max_batch_size": 5,
    },
    "snowflake-arctic-embed": {
        "dimensions": 1024,
        "description": "Snowflake's frontier embedding model",
        "max_batch_size": 10,
    },
    "snowflake-arctic-embed2": {
        "dimensions": 1024,
        "description": "Snowflake's latest multilingual embedding model",
        "max_batch_size": 10,
    },
}


def get_embeddings(model: str = DEFAULT_EMBEDDING_MODEL) -> OllamaEmbeddings:
    """
    Get an OllamaEmbeddings instance for the specified model.

    Args:
        model: Embedding model name (default: mxbai-embed-large)

    Returns:
        OllamaEmbeddings instance
    """
    return OllamaEmbeddings(
        model=model,
        base_url=OLLAMA_BASE_URL
    )


def get_model_config(model: str) -> dict:
    """
    Get configuration for a specific embedding model.

    Args:
        model: Embedding model name

    Returns:
        Model configuration dict
    """
    return EMBEDDING_MODELS.get(model, {
        "dimensions": 768,
        "description": "Unknown model",
        "max_batch_size": 5,
    })


def store_embedding_metadata(vectorstore, model: str):
    """
    Store embedding model information in collection metadata.

    This allows retrieval code to know which embedding model was used
    during ingestion and use the same model for queries.

    Args:
        vectorstore: Chroma vectorstore instance
        model: Embedding model name that was used
    """
    try:
        # ChromaDB stores metadata at collection level
        collection = vectorstore._collection

        # Get existing metadata or create new
        existing_metadata = collection.metadata or {}

        # Add embedding info
        existing_metadata["embedding_model"] = model
        existing_metadata["embedding_dimensions"] = get_model_config(model).get("dimensions", 768)

        # Update collection metadata
        collection.modify(metadata=existing_metadata)

        print(f"  Stored embedding metadata: model={model}")

    except Exception as e:
        print(f"  Warning: Could not store embedding metadata: {e}")


def get_embedding_model_from_collection(persist_directory: str, collection_name: str) -> str:
    """
    Retrieve the embedding model used for a collection.

    Args:
        persist_directory: ChromaDB persistence directory
        collection_name: Name of the collection

    Returns:
        Embedding model name (defaults to DEFAULT_EMBEDDING_MODEL if not found)
    """
    try:
        import chromadb

        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=persist_directory)

        # Get collection
        collection = client.get_collection(collection_name)

        # Get metadata
        metadata = collection.metadata or {}
        model = metadata.get("embedding_model", DEFAULT_EMBEDDING_MODEL)

        return model

    except Exception as e:
        print(f"  Warning: Could not retrieve embedding metadata: {e}")
        print(f"  Using default model: {DEFAULT_EMBEDDING_MODEL}")
        return DEFAULT_EMBEDDING_MODEL


def get_embeddings_for_collection(persist_directory: str, collection_name: str) -> OllamaEmbeddings:
    """
    Get the correct embedding model for a collection.

    This ensures that retrieval uses the same embedding model that was
    used during ingestion.

    Args:
        persist_directory: ChromaDB persistence directory
        collection_name: Name of the collection

    Returns:
        OllamaEmbeddings instance configured for the collection's model
    """
    model = get_embedding_model_from_collection(persist_directory, collection_name)
    print(f"  Using embedding model: {model}")
    return get_embeddings(model)


def print_embedding_info():
    """Print information about available embedding models."""
    print("Available Embedding Models:")
    print(f"  Default: {DEFAULT_EMBEDDING_MODEL}")
    print()
    for name, config in EMBEDDING_MODELS.items():
        marker = " (default)" if name == DEFAULT_EMBEDDING_MODEL else ""
        print(f"  {name}{marker}")
        print(f"    Dimensions: {config['dimensions']}")
        print(f"    Description: {config['description']}")
        print()
