
import nbformat as nbf
import sys

# Create a new notebook object
b = nbf.v4.new_notebook()

# --- Cell 1: Title ---
cell1_text = """
# ChromaDB Explorer Notebook

This notebook provides an interactive way to explore your ChromaDB instance, inspect collections, view documents, and visualize embeddings.
"""
b['cells'] = [nbf.v4.new_markdown_cell(cell1_text)]

# --- Cell 2: Check Python Executable ---
cell2_code = """
import sys
print(f"Python executable: {sys.executable}")
"""
b['cells'].append(nbf.v4.new_code_cell(cell2_code))


# --- Cell 3: Imports and Initialization ---
cell3_code = """
import chromadb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import numpy as np
import os

# --- Configuration ---
# Set the path to your ChromaDB persistent directory
# Make sure this path is correct relative to where you run the notebook
CHROMA_DB_PATH = "./chroma_db"

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
print(f"ChromaDB client initialized, connected to: {CHROMA_DB_PATH}")
"""
b['cells'].append(nbf.v4.new_code_cell(cell3_code))

# --- Cell 4: List Collections (Markdown) ---
cell4_text = """
## 1. List Collections

Run the cell below to see all available collections in your ChromaDB.
"""
b['cells'].append(nbf.v4.new_markdown_cell(cell4_text))

# --- Cell 5: List Collections (Code) ---
cell5_code = """
collections = client.list_collections()
if collections:
    print("Available Collections:")
    for i, collection in enumerate(collections):
        print(f"{i+1}. {collection.name}")
else:
    print("No collections found in the database.")
"""
b['cells'].append(nbf.v4.new_code_cell(cell5_code))

# --- Cell 6: Select Collection (Markdown) ---
cell6_text = """
## 2. Select a Collection and Inspect its Content

Enter the name of the collection you want to inspect. If you don't specify one, it will try to select the first available collection.
"""
b['cells'].append(nbf.v4.new_markdown_cell(cell6_text))

# --- Cell 7: Select Collection (Code) ---
cell7_code = """
selected_collection_name = input("Enter collection name (or leave blank to select the first one): ").strip()

if not selected_collection_name and collections:
    selected_collection = collections[0]
    selected_collection_name = selected_collection.name
    print(f"No collection name entered, selecting the first one: {selected_collection_name}")
elif selected_collection_name:
    try:
        selected_collection = client.get_collection(name=selected_collection_name)
        print(f"Selected collection: {selected_collection_name}")
    except Exception as e:
        print(f"Error: Collection '{selected_collection_name}' not found. Please check the name and try again. {e}")
        selected_collection = None
else:
    print("No collections available to select.")
    selected_collection = None

if selected_collection:
    # Get all documents from the collection
    # Limit to a reasonable number for display to avoid overwhelming the notebook
    try:
        results = selected_collection.get(ids=None, where=None, limit=100, include=['documents', 'metadatas', 'embeddings'])
        
        documents = results['documents']
        metadatas = results['metadatas']
        embeddings = results['embeddings']
        ids = results['ids']

        print(f"\nTotal documents in collection '{selected_collection_name}': {selected_collection.count()}")
        print(f"Displaying first {len(documents)} documents.")

        if documents:
            df = pd.DataFrame({
                'id': ids,
                'document': documents,
                'metadata': metadatas
            })
            print("\nSample Documents:")
            display(df.head())

            print("\nMetadata Keys Distribution:")
            all_metadata_keys = []
            for meta in metadatas:
                if meta: # Ensure metadata is not None
                    all_metadata_keys.extend(meta.keys())
            if all_metadata_keys:
                metadata_key_counts = pd.Series(all_metadata_keys).value_counts()
                display(metadata_key_counts)
            else:
                print("No metadata found for these documents.")
        else:
            print("No documents found in the selected collection.")

    except Exception as e:
        print(f"Error retrieving documents from collection: {e}")
else:
    print("Cannot proceed without a selected collection.")
"""
b['cells'].append(nbf.v4.new_code_cell(cell7_code))

# --- Cell 8: Visualize Embeddings (Markdown) ---
cell8_text = """
## 3. Visualize Embeddings (if available)

If your documents have embeddings, this section will attempt to reduce their dimensionality using PCA and t-SNE for visualization. This helps to see clusters or relationships between your document chunks.
"""
b['cells'].append(nbf.v4.new_markdown_cell(cell8_text))

# --- Cell 9: Visualize Embeddings (Code) ---
cell9_code = """
if 'embeddings' in locals() and embeddings and len(embeddings) > 1:
    print(f"Found {len(embeddings)} embeddings with dimension {len(embeddings[0])}.")
    embeddings_array = np.array(embeddings)

    # Reduce dimensionality for visualization
    if embeddings_array.shape[1] > 2:
        print("Applying PCA for dimensionality reduction...")
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(embeddings_array)
        
        plt.figure(figsize=(10, 7))
        sns.scatterplot(
            x=pca_result[:,0], y=pca_result[:,1],
            hue=[m.get('source', 'unknown') if m else 'unknown' for m in metadatas], # Color by 'source' if available
            legend='full',
            alpha=0.7
        )
        plt.title('Embeddings Visualization (PCA)')
        plt.xlabel('PCA Component 1')
        plt.ylabel('PCA Component 2')
        plt.show()

        # t-SNE for potentially better clustering visualization (can be slow for many points)
        if len(embeddings) < 1000: # Limit t-SNE for performance
            print("Applying t-SNE for dimensionality reduction (this may take a moment)...")
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)-1))
            tsne_result = tsne.fit_transform(embeddings_array)

            plt.figure(figsize=(10, 7))
            sns.scatterplot(
                x=tsne_result[:,0], y=tsne_result[:,1],
                hue=[m.get('source', 'unknown') if m else 'unknown' for m in metadatas], # Color by 'source' if available
                legend='full',
                alpha=0.7
            )
            plt.title('Embeddings Visualization (t-SNE)')
            plt.xlabel('t-SNE Component 1')
            plt.ylabel('t-SNE Component 2')
            plt.show()
        else:
            print("Skipping t-SNE for performance reasons (too many embeddings).")
    else:
        print("Embeddings dimension is 2 or less, no reduction needed for visualization.")
        plt.figure(figsize=(10, 7))
        sns.scatterplot(
            x=embeddings_array[:,0], y=embeddings_array[:,1],
            hue=[m.get('source', 'unknown') if m else 'unknown' for m in metadatas], # Color by 'source' if available
            legend='full',
            alpha=0.7
        )
        plt.title('Embeddings Visualization (Original 2D)')
        plt.xlabel('Embedding Dimension 1')
        plt.ylabel('Embedding Dimension 2')
        plt.show()
else:
    print("No embeddings available or not enough embeddings to visualize for the selected collection.")
"""
b['cells'].append(nbf.v4.new_code_cell(cell9_code))

# --- Cell 10: Advanced Visualization (Markdown) ---
cell10_text = """
## 4. Advanced Visualization: Pair Plot of First 4 Principal Components

This section visualizes the first 4 principal components of the embeddings using a pair plot. This can help to see relationships between these components. It also shows the explained variance ratio for each component, which tells you how much of the total information is captured by each dimension.
"""
b['cells'].append(nbf.v4.new_markdown_cell(cell10_text))

# --- Cell 11: Advanced Visualization (Code) ---
cell11_code = """
if 'embeddings' in locals() and embeddings and len(embeddings) > 4:
    print("Applying PCA to reduce to 4 dimensions for pair plot...")
    pca_4d = PCA(n_components=4)
    pca_result_4d = pca_4d.fit_transform(np.array(embeddings))

    print("\nExplained Variance Ratio (Coverage) for each of the 4 dimensions:")
    for i, ratio in enumerate(pca_4d.explained_variance_ratio_):
        print(f"  Principal Component {i+1}: {ratio:.4f} ({ratio*100:.2f}%)")
    print(f"Total variance explained by 4 components: {np.sum(pca_4d.explained_variance_ratio_):.4f} ({np.sum(pca_4d.explained_variance_ratio_)*100:.2f}%)")

    pca_df = pd.DataFrame(pca_result_4d, columns=['PC1', 'PC2', 'PC3', 'PC4'])
    
    # Add source metadata for coloring the plot, if available
    pca_df['source'] = [m.get('source', 'unknown') if m else 'unknown' for m in metadatas]

    print("\nGenerating pair plot... (this may take a moment)")
    sns.pairplot(pca_df, hue='source', vars=['PC1', 'PC2', 'PC3', 'PC4'], plot_kws={'alpha': 0.6})
    plt.suptitle('Pair Plot of the First 4 Principal Components', y=1.02)
    plt.show()
else:
    print("Not enough embeddings (must be > 4) to generate a 4D pair plot.")

"""
b['cells'].append(nbf.v4.new_code_cell(cell11_code))


# --- Cell 12: Search (Markdown) ---
cell12_text = """
## 5. Search within a Collection (Optional)

You can perform a similarity search within the selected collection. Enter a query text and specify how many results you want.
"""
b['cells'].append(nbf.v4.new_markdown_cell(cell12_text))

# --- Cell 13: Search (Code) ---
cell13_code = """
if 'selected_collection' in locals() and selected_collection:
    query_text = input("Enter a query to search within the collection (or leave blank to skip): ").strip()
    if query_text:
        try:
            n_results_str = input("How many results to retrieve? (default: 5): ").strip()
            n_results = int(n_results_str) if n_results_str.isdigit() else 5

            search_results = selected_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            print(f"\nSearch Results for '{query_text}':")
            if search_results['documents'] and search_results['documents'][0]:
                search_df = pd.DataFrame({
                    'document': search_results['documents'][0],
                    'metadata': search_results['metadatas'][0],
                    'distance': search_results['distances'][0]
                })
                display(search_df)
            else:
                print("No results found for your query.")
        except Exception as e:
            print(f"Error during search: {e}")
    else:
        print("Query text was empty, skipping search.")
else:
    print("Cannot perform search without a selected collection.")
"""
b['cells'].append(nbf.v4.new_code_cell(cell13_code))

# Write the notebook to a file
with open('chroma_explorer.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Successfully created chroma_explorer.ipynb")
