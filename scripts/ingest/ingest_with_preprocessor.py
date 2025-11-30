"""
Enhanced Document Ingestion with Intelligent Preprocessing

This script uses the preprocessor modules to:
1. Analyze document quality before ingestion
2. Select optimal chunking strategy per document
3. Clean and deduplicate content
4. Calculate quality metrics
5. Provide detailed reporting

Usage:
    python ingest_with_preprocessor.py

    # Or with custom settings
    python ingest_with_preprocessor.py --min-quality 0.5 --skip-analysis
"""

import argparse
import logging
import os
from datetime import datetime

from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_unstructured import UnstructuredLoader

from src.preprocessor import ChunkingStrategy, ContentCleaner, DocumentAnalyzer, QualityMetrics
from src.utils.embedding_utils import (
    DEFAULT_EMBEDDING_MODEL,
    get_embeddings,
    get_model_config,
    store_embedding_metadata,
)

# Configuration
DOCUMENTS_DIR = "documents"
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "research_agent_collection"

# Setup logging
log_filename = f"ingestion_preprocessed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class PreprocessedIngestion:
    """Manages document ingestion with preprocessing"""

    def __init__(
        self,
        documents_dir: str = DOCUMENTS_DIR,
        chroma_db_dir: str = CHROMA_DB_DIR,
        collection_name: str = COLLECTION_NAME,
        min_quality_score: float = 0.0,
        enable_near_duplicate_detection: bool = True,
        enable_boilerplate_removal: bool = True,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        """
        Args:
            documents_dir: Directory containing source documents
            chroma_db_dir: ChromaDB persistence directory
            collection_name: Name of the collection
            min_quality_score: Minimum quality score to include file (0-1)
            enable_near_duplicate_detection: Remove near-duplicates
            enable_boilerplate_removal: Remove common boilerplate
            embedding_model: Ollama embedding model to use
        """
        self.documents_dir = documents_dir
        self.chroma_db_dir = chroma_db_dir
        self.collection_name = collection_name
        self.min_quality_score = min_quality_score
        self.enable_near_duplicate_detection = enable_near_duplicate_detection
        self.enable_boilerplate_removal = enable_boilerplate_removal
        self.embedding_model = embedding_model
        self.model_config = get_model_config(embedding_model)

        # Initialize components
        self.analyzer = DocumentAnalyzer()
        self.chunking_strategy = ChunkingStrategy()
        self.cleaner = ContentCleaner(similarity_threshold=0.95, min_content_length=100)
        self.quality_metrics = QualityMetrics()

        # Statistics
        self.stats = {
            "files_analyzed": 0,
            "files_skipped_low_quality": 0,
            "files_processed": 0,
            "files_failed": 0,
            "total_chunks_before_cleaning": 0,
            "total_chunks_after_cleaning": 0,
            "total_chunks_ingested": 0,
        }

    def run(self, skip_analysis: bool = False):
        """Run the complete ingestion pipeline"""

        logger.info("=" * 80)
        logger.info("DOCUMENT INGESTION WITH PREPROCESSING")
        logger.info("=" * 80)
        logger.info(f"Started at: {datetime.now()}")
        logger.info(f"Log file: {log_filename}")

        # Phase 1: Document Analysis
        if not skip_analysis:
            logger.info("\n" + "=" * 80)
            logger.info("PHASE 1: DOCUMENT ANALYSIS")
            logger.info("=" * 80)

            analyses = self.analyzer.analyze_directory(self.documents_dir)
            self.stats["files_analyzed"] = len(analyses)

            self.analyzer.print_report()

            # Filter out low-quality files
            good_files = [a for a in analyses if a.quality_score >= self.min_quality_score]
            self.stats["files_skipped_low_quality"] = len(analyses) - len(good_files)

            if self.stats["files_skipped_low_quality"] > 0:
                logger.warning(
                    f"\nSkipping {self.stats['files_skipped_low_quality']} low-quality files"
                )

            file_analyses = {a.filepath: a for a in good_files}
        else:
            logger.info("Skipping document analysis phase")
            # Process all files
            file_analyses = {}
            for filename in os.listdir(self.documents_dir):
                filepath = os.path.join(self.documents_dir, filename)
                if os.path.isfile(filepath):
                    file_analyses[filepath] = None

        # Phase 2: Embedding Model Setup
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: EMBEDDING MODEL SETUP")
        logger.info("=" * 80)

        embeddings = get_embeddings(self.embedding_model)

        logger.info(f"✓ Embedding model: {self.embedding_model}")
        logger.info(f"✓ Dimensions: {self.model_config.get('dimensions', 'unknown')}")

        # Initialize vector store
        vectorstore = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.chroma_db_dir,
            embedding_function=embeddings,
        )

        logger.info(f"✓ Vector store initialized: {self.chroma_db_dir}")

        # Store embedding model metadata for retrieval alignment
        store_embedding_metadata(vectorstore, self.embedding_model)

        # Phase 3: Document Processing
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: DOCUMENT PROCESSING & CHUNKING")
        logger.info("=" * 80)

        all_chunks = []
        failed_files = []

        for filepath, analysis in file_analyses.items():
            filename = os.path.basename(filepath)

            try:
                logger.info(f"\n📄 Processing: {filename}")

                # Load document
                loader = UnstructuredLoader(file_path=filepath)
                documents = loader.load()

                if not documents:
                    logger.warning(f"  No content extracted from {filename}")
                    failed_files.append(filename)
                    continue

                logger.info(f"  ✓ Loaded {len(documents)} document(s)")

                # Filter metadata
                filtered_docs = filter_complex_metadata(documents)

                # Select chunking strategy
                if analysis:
                    config = self.chunking_strategy.select_config(
                        structure_type=analysis.structure_type,
                        file_size=analysis.file_size,
                        language=analysis.language,
                        has_complex_structure=analysis.metadata.get("has_tables", False)
                        or analysis.metadata.get("has_code_blocks", False),
                    )
                    logger.info(f"  ✓ Chunking method: {config.method.value}")
                    logger.info(
                        f"    Chunk size: {config.chunk_size}, Overlap: {config.chunk_overlap}"
                    )
                else:
                    # Default config
                    from src.preprocessor.chunking_strategy import ChunkingConfig, ChunkingMethod

                    config = ChunkingConfig(
                        method=ChunkingMethod.RECURSIVE,
                        chunk_size=1000,
                        chunk_overlap=200,
                        min_chunk_size=100,
                    )

                # Chunk documents
                chunks = self.chunking_strategy.chunk_documents(
                    filtered_docs, config, source=filepath
                )

                logger.info(f"  ✓ Created {len(chunks)} chunks")
                self.stats["total_chunks_before_cleaning"] += len(chunks)

                # Add to collection
                all_chunks.extend(chunks)
                self.stats["files_processed"] += 1

            except Exception as e:
                logger.error(f"  ✗ Failed to process {filename}: {e}")
                failed_files.append(filename)
                self.stats["files_failed"] += 1

        # Phase 4: Content Cleaning
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: CONTENT CLEANING & DEDUPLICATION")
        logger.info("=" * 80)

        logger.info(f"Chunks before cleaning: {len(all_chunks)}")

        cleaned_chunks = self.cleaner.clean_and_deduplicate(
            all_chunks,
            remove_near_duplicates=self.enable_near_duplicate_detection,
            remove_boilerplate=self.enable_boilerplate_removal,
        )

        logger.info(f"Chunks after cleaning: {len(cleaned_chunks)}")

        self.stats["total_chunks_after_cleaning"] = len(cleaned_chunks)
        self.cleaner.print_stats()

        # Phase 5: Quality Analysis
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5: QUALITY METRICS")
        logger.info("=" * 80)

        metrics = self.quality_metrics.calculate_metrics(cleaned_chunks)
        self.quality_metrics.print_report()

        # Phase 6: Ingestion
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 6: VECTOR STORE INGESTION")
        logger.info("=" * 80)

        if cleaned_chunks:
            logger.info(f"Adding {len(cleaned_chunks)} chunks to vector store...")

            try:
                # Add in batches (use model-specific batch size for stability)
                batch_size = self.model_config.get("max_batch_size", 10)
                total_batches = (len(cleaned_chunks) - 1) // batch_size + 1
                logger.info(f"  Using batch size: {batch_size}")
                for i in range(0, len(cleaned_chunks), batch_size):
                    batch = cleaned_chunks[i : i + batch_size]
                    vectorstore.add_documents(batch)
                    batch_num = i // batch_size + 1
                    if batch_num % 10 == 0 or batch_num == total_batches:
                        logger.info(f"  Progress: {batch_num}/{total_batches} batches")

                self.stats["total_chunks_ingested"] = len(cleaned_chunks)
                logger.info("✓ Successfully ingested all chunks")

            except Exception as e:
                logger.error(f"✗ Failed to ingest chunks: {e}")
                self.stats["files_failed"] += len(file_analyses)

        # Final Report
        self.print_final_report(failed_files, metrics)

        logger.info(f"\n✓ Full log saved to: {log_filename}")
        logger.info("=" * 80)

    def print_final_report(self, failed_files: list[str], metrics: dict):
        """Print final ingestion report"""

        logger.info("\n" + "=" * 80)
        logger.info("FINAL INGESTION REPORT")
        logger.info("=" * 80)

        logger.info("\n📊 Processing Summary:")
        logger.info(f"  Files analyzed: {self.stats['files_analyzed']}")
        logger.info(f"  Files processed: {self.stats['files_processed']}")
        logger.info(f"  Files skipped (low quality): {self.stats['files_skipped_low_quality']}")
        logger.info(f"  Files failed: {self.stats['files_failed']}")

        logger.info("\n📦 Chunk Summary:")
        logger.info(f"  Chunks created: {self.stats['total_chunks_before_cleaning']}")
        logger.info(f"  Chunks after cleaning: {self.stats['total_chunks_after_cleaning']}")
        logger.info(f"  Chunks ingested: {self.stats['total_chunks_ingested']}")

        reduction_rate = (
            (
                (
                    self.stats["total_chunks_before_cleaning"]
                    - self.stats["total_chunks_after_cleaning"]
                )
                / self.stats["total_chunks_before_cleaning"]
            )
            if self.stats["total_chunks_before_cleaning"] > 0
            else 0
        )

        logger.info(f"  Reduction rate: {reduction_rate:.1%}")

        if failed_files:
            logger.warning(f"\n⚠️  Failed Files ({len(failed_files)}):")
            for f in failed_files:
                logger.warning(f"  - {f}")

        logger.info("\n📈 Quality Assessment:")
        logger.info(f"  Overall quality: {metrics.get('quality_grade', 'Unknown')}")
        logger.info(f"  Quality score: {metrics.get('quality_score', 0):.2f}/1.00")

        recommendations = self.quality_metrics.get_recommendations()
        if recommendations:
            logger.info("\n💡 Recommendations:")
            for rec in recommendations:
                logger.info(f"  - {rec}")

        logger.info(f"\n✅ Vector store location: {self.chroma_db_dir}")
        logger.info(f"✅ Collection name: {self.collection_name}")


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description="Ingest documents with intelligent preprocessing")

    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.0,
        help="Minimum quality score to include file (0.0-1.0, default: 0.0)",
    )

    parser.add_argument("--skip-analysis", action="store_true", help="Skip document analysis phase")

    parser.add_argument(
        "--disable-deduplication", action="store_true", help="Disable near-duplicate detection"
    )

    parser.add_argument(
        "--disable-boilerplate", action="store_true", help="Disable boilerplate removal"
    )

    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Ollama embedding model (default: {DEFAULT_EMBEDDING_MODEL})",
    )

    args = parser.parse_args()

    # Run ingestion
    ingestion = PreprocessedIngestion(
        min_quality_score=args.min_quality,
        enable_near_duplicate_detection=not args.disable_deduplication,
        enable_boilerplate_removal=not args.disable_boilerplate,
        embedding_model=args.embedding_model,
    )

    ingestion.run(skip_analysis=args.skip_analysis)


if __name__ == "__main__":
    main()
