"""
Enhanced Diagnostic Ingestion Script for ChromaDB

This script provides detailed logging, validation, and quality checks
during the document ingestion process to help debug embedding issues.
"""

import os
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
DOCUMENTS_DIR = "documents"
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "research_agent_collection"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"

# Setup detailed logging
log_filename = f"ingestion_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmbeddingQualityChecker:
    """Monitors embedding quality during ingestion"""

    def __init__(self):
        self.embedding_samples = []
        self.embedding_stats = {
            'mean': [],
            'std': [],
            'min': [],
            'max': []
        }
        self.similarities = []

    def add_embedding(self, embedding: List[float], doc_text: str = None):
        """Store embedding sample for analysis"""
        emb_array = np.array(embedding)

        # Store sample (keep first 10)
        if len(self.embedding_samples) < 10:
            self.embedding_samples.append({
                'embedding': embedding[:10],  # Store first 10 dims
                'full_mean': float(np.mean(emb_array)),
                'full_std': float(np.std(emb_array)),
                'text_preview': doc_text[:100] if doc_text else None
            })

        # Track statistics
        self.embedding_stats['mean'].append(float(np.mean(emb_array)))
        self.embedding_stats['std'].append(float(np.std(emb_array)))
        self.embedding_stats['min'].append(float(np.min(emb_array)))
        self.embedding_stats['max'].append(float(np.max(emb_array)))

    def check_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        sim = cosine_similarity([emb1], [emb2])[0][0]
        self.similarities.append(float(sim))
        return sim

    def get_report(self) -> str:
        """Generate quality report"""
        if not self.embedding_stats['mean']:
            return "No embeddings analyzed yet."

        report = []
        report.append("\n" + "="*80)
        report.append("EMBEDDING QUALITY REPORT")
        report.append("="*80)

        # Overall statistics
        report.append(f"\nTotal embeddings analyzed: {len(self.embedding_stats['mean'])}")
        report.append(f"\nAcross all embeddings:")
        report.append(f"  Mean of means: {np.mean(self.embedding_stats['mean']):.6f}")
        report.append(f"  Mean of stds:  {np.mean(self.embedding_stats['std']):.6f}")
        report.append(f"  Overall min:   {np.min(self.embedding_stats['min']):.6f}")
        report.append(f"  Overall max:   {np.max(self.embedding_stats['max']):.6f}")

        # Check for issues
        avg_std = np.mean(self.embedding_stats['std'])
        if avg_std < 0.01:
            report.append(f"\n⚠️  WARNING: Very low std deviation ({avg_std:.6f})")
            report.append("   Embeddings may be too similar - model might not be working!")

        # Similarity analysis
        if len(self.similarities) > 0:
            report.append(f"\nPairwise similarities (consecutive chunks):")
            report.append(f"  Mean similarity: {np.mean(self.similarities):.4f}")
            report.append(f"  Min similarity:  {np.min(self.similarities):.4f}")
            report.append(f"  Max similarity:  {np.max(self.similarities):.4f}")

            high_sim = sum(1 for s in self.similarities if s > 0.95)
            if high_sim > len(self.similarities) * 0.5:
                report.append(f"\n⚠️  WARNING: {high_sim}/{len(self.similarities)} pairs have >0.95 similarity")
                report.append("   This is unusually high!")

        # Sample embeddings
        report.append(f"\nSample embeddings (first 10 dimensions):")
        for i, sample in enumerate(self.embedding_samples[:3]):
            report.append(f"\n  Sample {i+1}:")
            report.append(f"    Text: {sample['text_preview']}")
            report.append(f"    First 10 dims: {sample['embedding']}")
            report.append(f"    Full mean: {sample['full_mean']:.6f}, std: {sample['full_std']:.6f}")

        report.append("\n" + "="*80)
        return "\n".join(report)


class ChunkAnalyzer:
    """Analyzes document chunking quality"""

    def __init__(self):
        self.chunk_sizes = []
        self.chunk_overlaps = []
        self.chunks_by_source = {}
        self.chunk_hashes = set()
        self.duplicate_count = 0

    def analyze_chunks(self, chunks: List, source: str) -> Dict:
        """Analyze chunks from a document"""
        analysis = {
            'count': len(chunks),
            'sizes': [],
            'unique': 0,
            'duplicates': 0,
            'samples': []
        }

        for i, chunk in enumerate(chunks):
            text = chunk.page_content
            size = len(text)

            # Track size
            analysis['sizes'].append(size)
            self.chunk_sizes.append(size)

            # Check for duplicates
            chunk_hash = hashlib.md5(text.encode()).hexdigest()
            if chunk_hash in self.chunk_hashes:
                analysis['duplicates'] += 1
                self.duplicate_count += 1
                logger.warning(f"  Duplicate chunk detected in {source}")
            else:
                self.chunk_hashes.add(chunk_hash)
                analysis['unique'] += 1

            # Store samples
            if i < 3:
                analysis['samples'].append({
                    'index': i,
                    'size': size,
                    'preview': text[:200]
                })

        self.chunks_by_source[source] = analysis
        return analysis

    def get_report(self) -> str:
        """Generate chunking report"""
        if not self.chunk_sizes:
            return "No chunks analyzed yet."

        report = []
        report.append("\n" + "="*80)
        report.append("CHUNKING ANALYSIS REPORT")
        report.append("="*80)

        report.append(f"\nTotal chunks created: {len(self.chunk_sizes)}")
        report.append(f"Total unique chunks: {len(self.chunk_hashes)}")
        report.append(f"Total duplicates: {self.duplicate_count}")

        report.append(f"\nChunk size statistics:")
        report.append(f"  Mean: {np.mean(self.chunk_sizes):.1f} chars")
        report.append(f"  Median: {np.median(self.chunk_sizes):.1f} chars")
        report.append(f"  Min: {np.min(self.chunk_sizes)} chars")
        report.append(f"  Max: {np.max(self.chunk_sizes)} chars")
        report.append(f"  Std: {np.std(self.chunk_sizes):.1f} chars")

        # Check if chunking is working as expected
        if np.mean(self.chunk_sizes) > CHUNK_SIZE * 1.5:
            report.append(f"\n⚠️  WARNING: Average chunk size ({np.mean(self.chunk_sizes):.0f}) >> configured size ({CHUNK_SIZE})")
            report.append("   Chunking may not be working correctly!")

        # Per-source breakdown
        report.append(f"\nPer-source breakdown:")
        for source, analysis in sorted(self.chunks_by_source.items()):
            report.append(f"\n  {os.path.basename(source)}:")
            report.append(f"    Total chunks: {analysis['count']}")
            report.append(f"    Unique: {analysis['unique']}, Duplicates: {analysis['duplicates']}")
            report.append(f"    Avg size: {np.mean(analysis['sizes']):.1f} chars")

        report.append("\n" + "="*80)
        return "\n".join(report)


def test_embedding_model(embeddings: OllamaEmbeddings) -> bool:
    """Test if embedding model is working correctly"""
    logger.info("Testing embedding model...")

    try:
        # Test with two very different texts
        test1 = "The sky is blue and clouds are white."
        test2 = "Python is a programming language used for data science."

        emb1 = embeddings.embed_query(test1)
        emb2 = embeddings.embed_query(test2)

        # Check if embeddings are valid
        if not emb1 or not emb2:
            logger.error("Embedding model returned empty embeddings!")
            return False

        # Check dimensions
        if len(emb1) != len(emb2):
            logger.error(f"Embedding dimension mismatch: {len(emb1)} vs {len(emb2)}")
            return False

        logger.info(f"✓ Embedding dimension: {len(emb1)}")

        # Check if embeddings are different
        emb1_array = np.array(emb1)
        emb2_array = np.array(emb2)

        similarity = cosine_similarity([emb1], [emb2])[0][0]
        logger.info(f"✓ Test similarity: {similarity:.4f}")

        # Sample values
        logger.info(f"✓ Sample from emb1: {emb1[:5]}")
        logger.info(f"✓ Sample from emb2: {emb2[:5]}")

        # Check variance
        std1 = np.std(emb1_array)
        std2 = np.std(emb2_array)
        logger.info(f"✓ Std dev - emb1: {std1:.6f}, emb2: {std2:.6f}")

        if similarity > 0.95:
            logger.warning("⚠️  Very high similarity for different texts!")
            logger.warning("   Embedding model may not be working correctly.")
            return False

        if std1 < 0.01 or std2 < 0.01:
            logger.warning("⚠️  Very low variance in embeddings!")
            logger.warning("   Embedding model may not be working correctly.")
            return False

        logger.info("✓ Embedding model test PASSED")
        return True

    except Exception as e:
        logger.error(f"Embedding model test FAILED: {e}")
        return False


def process_document(filepath: str, text_splitter, embeddings,
                     chunk_analyzer: ChunkAnalyzer,
                     quality_checker: EmbeddingQualityChecker) -> Tuple[List, bool]:
    """Process a single document with detailed diagnostics"""

    filename = os.path.basename(filepath)
    logger.info("="*80)
    logger.info(f"Processing: {filename}")
    logger.info("="*80)

    try:
        # Step 1: Load document
        logger.info("Step 1: Loading document...")
        loader = UnstructuredLoader(file_path=filepath)
        documents = loader.load()

        if not documents:
            logger.warning(f"No content extracted from {filename}")
            return [], False

        logger.info(f"✓ Loaded {len(documents)} document(s)")
        logger.info(f"  Total characters: {sum(len(doc.page_content) for doc in documents)}")

        # Step 2: Filter metadata
        logger.info("Step 2: Filtering metadata...")
        filtered_documents = filter_complex_metadata(documents)
        logger.info(f"✓ Filtered {len(filtered_documents)} document(s)")

        # Preview content
        if filtered_documents:
            preview = filtered_documents[0].page_content[:200]
            logger.info(f"  Content preview: {preview}...")

        # Step 3: Split into chunks
        logger.info(f"Step 3: Splitting into chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
        splits = text_splitter.split_documents(filtered_documents)
        logger.info(f"✓ Created {len(splits)} chunks")

        # Analyze chunks
        chunk_analysis = chunk_analyzer.analyze_chunks(splits, filepath)
        logger.info(f"  Unique chunks: {chunk_analysis['unique']}")
        logger.info(f"  Duplicates: {chunk_analysis['duplicates']}")
        logger.info(f"  Avg chunk size: {np.mean(chunk_analysis['sizes']):.1f} chars")

        # Show sample chunks
        for sample in chunk_analysis['samples']:
            logger.info(f"\n  Chunk {sample['index']} ({sample['size']} chars):")
            logger.info(f"    {sample['preview']}...")

        # Step 4: Generate embeddings for first few chunks
        logger.info("\nStep 4: Generating sample embeddings...")
        previous_emb = None

        for i, split in enumerate(splits[:3]):  # Sample first 3 chunks
            logger.info(f"  Generating embedding for chunk {i}...")

            try:
                # Generate embedding
                emb = embeddings.embed_query(split.page_content)

                # Quality check
                quality_checker.add_embedding(emb, split.page_content)

                emb_array = np.array(emb)
                logger.info(f"    Dimension: {len(emb)}")
                logger.info(f"    Mean: {np.mean(emb_array):.6f}, Std: {np.std(emb_array):.6f}")
                logger.info(f"    Sample values: {emb[:5]}")

                # Check similarity with previous chunk
                if previous_emb is not None:
                    sim = quality_checker.check_similarity(previous_emb, emb)
                    logger.info(f"    Similarity with previous chunk: {sim:.4f}")

                    if sim > 0.99:
                        logger.warning("    ⚠️  Very high similarity with previous chunk!")

                previous_emb = emb

            except Exception as e:
                logger.error(f"    Failed to generate embedding: {e}")
                return [], False

        logger.info(f"\n✓ Successfully processed {filename}")
        logger.info(f"  Ready to add {len(splits)} chunks to vector store")

        return splits, True

    except Exception as e:
        logger.error(f"✗ Failed to process {filename}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [], False


def main():
    """Main ingestion process with comprehensive diagnostics"""

    logger.info("="*80)
    logger.info("DIAGNOSTIC DOCUMENT INGESTION STARTED")
    logger.info("="*80)
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Timestamp: {datetime.now()}")

    # Initialize analyzers
    chunk_analyzer = ChunkAnalyzer()
    quality_checker = EmbeddingQualityChecker()

    # Configuration summary
    logger.info("\nConfiguration:")
    logger.info(f"  Documents directory: {DOCUMENTS_DIR}")
    logger.info(f"  ChromaDB directory: {CHROMA_DB_DIR}")
    logger.info(f"  Collection name: {COLLECTION_NAME}")
    logger.info(f"  Chunk size: {CHUNK_SIZE}")
    logger.info(f"  Chunk overlap: {CHUNK_OVERLAP}")
    logger.info(f"  Embedding model: {EMBEDDING_MODEL}")
    logger.info(f"  Ollama URL: {OLLAMA_BASE_URL}")

    # Check documents directory
    if not os.path.exists(DOCUMENTS_DIR):
        logger.error(f"Documents directory not found: {DOCUMENTS_DIR}")
        return

    files = [f for f in os.listdir(DOCUMENTS_DIR) if os.path.isfile(os.path.join(DOCUMENTS_DIR, f))]
    logger.info(f"\nFound {len(files)} files in {DOCUMENTS_DIR}:")
    for f in sorted(files):
        filepath = os.path.join(DOCUMENTS_DIR, f)
        size = os.path.getsize(filepath)
        logger.info(f"  - {f} ({size:,} bytes)")

    # Initialize embedding model
    logger.info("\n" + "="*80)
    logger.info("Initializing embedding model...")
    logger.info("="*80)

    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL
    )

    # Test embedding model
    if not test_embedding_model(embeddings):
        logger.error("\n🚨 CRITICAL: Embedding model test failed!")
        logger.error("Please check:")
        logger.error("  1. Is Ollama running? (run 'ollama list')")
        logger.error("  2. Is the model installed? (run 'ollama pull nomic-embed-text')")
        logger.error("  3. Is the base URL correct?")
        logger.error("\nAborting ingestion.")
        return

    # Initialize vector store
    logger.info("\n" + "="*80)
    logger.info("Initializing ChromaDB vector store...")
    logger.info("="*80)

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
    )

    logger.info("✓ Vector store initialized")

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Process each document
    total_docs_ingested = 0
    total_chunks_created = 0
    failed_files = []

    logger.info("\n" + "="*80)
    logger.info("PROCESSING DOCUMENTS")
    logger.info("="*80)

    for filename in sorted(files):
        filepath = os.path.join(DOCUMENTS_DIR, filename)

        splits, success = process_document(
            filepath,
            text_splitter,
            embeddings,
            chunk_analyzer,
            quality_checker
        )

        if success and splits:
            # Add to vector store
            logger.info(f"\nAdding {len(splits)} chunks to vector store...")
            try:
                vectorstore.add_documents(splits)
                logger.info("✓ Successfully added to vector store")

                total_docs_ingested += 1
                total_chunks_created += len(splits)
            except Exception as e:
                logger.error(f"✗ Failed to add to vector store: {e}")
                failed_files.append(filename)
        else:
            failed_files.append(filename)

    # Final reports
    logger.info("\n" + "="*80)
    logger.info("INGESTION COMPLETE")
    logger.info("="*80)

    logger.info(f"\nSummary:")
    logger.info(f"  Total files processed: {len(files)}")
    logger.info(f"  Successfully ingested: {total_docs_ingested}")
    logger.info(f"  Failed: {len(failed_files)}")
    logger.info(f"  Total chunks created: {total_chunks_created}")
    logger.info(f"  Vector store location: {CHROMA_DB_DIR}")

    if failed_files:
        logger.warning(f"\nFailed files:")
        for f in failed_files:
            logger.warning(f"  - {f}")

    # Print analysis reports
    logger.info(chunk_analyzer.get_report())
    logger.info(quality_checker.get_report())

    logger.info(f"\n✓ Full log saved to: {log_filename}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
