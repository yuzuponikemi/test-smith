"""
Codebase Ingestion Script - Digest entire repositories for coding agent

This script indexes entire codebases into ChromaDB for use by a coding agent
that can answer questions about the repository structure, code patterns, and
implementation details.

Features:
- Recursive directory traversal with .gitignore support
- Code-aware chunking for multiple programming languages
- File path and structure metadata preservation
- Repository-level context (README, config files)
- Symbol tracking (functions, classes, imports)

Usage:
    # Ingest current repository
    python scripts/ingest/ingest_codebase.py .

    # Ingest a specific repository path
    python scripts/ingest/ingest_codebase.py /path/to/repo

    # With custom collection name
    python scripts/ingest/ingest_codebase.py . --collection my_project_code

    # Skip certain directories
    python scripts/ingest/ingest_codebase.py . --skip-dirs node_modules,dist,.git
"""

import argparse
import fnmatch
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.preprocessor import ChunkingStrategy, ContentCleaner, DocumentAnalyzer, QualityMetrics
from src.utils.embedding_utils import (
    DEFAULT_EMBEDDING_MODEL,
    get_embeddings,
    get_model_config,
    store_embedding_metadata,
)

# Configuration
CHROMA_DB_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "codebase_collection"

# Default directories to skip
DEFAULT_SKIP_DIRS = {
    ".git",
    ".svn",
    ".hg",  # Version control
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",  # Dependencies/cache
    "dist",
    "build",
    "target",
    "out",
    "bin",  # Build outputs
    ".idea",
    ".vscode",
    ".eclipse",  # IDE configs
    "coverage",
    ".nyc_output",
    "htmlcov",  # Coverage reports
    ".tox",
    ".eggs",
    "*.egg-info",  # Python packaging
}

# Priority files that should be processed first (for context)
PRIORITY_FILES = {
    "README.md",
    "README.rst",
    "README.txt",
    "README",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "ARCHITECTURE.md",
    "package.json",
    "setup.py",
    "pyproject.toml",
    "Cargo.toml",
    "requirements.txt",
    "go.mod",
    "pom.xml",
    "build.gradle",
}

# Setup logging
log_filename = f"codebase_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class GitignoreParser:
    """Parse and apply .gitignore patterns"""

    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.patterns: list[str] = []
        self._load_gitignore()

    def _load_gitignore(self):
        """Load patterns from .gitignore file"""
        gitignore_path = os.path.join(self.repo_root, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        self.patterns.append(line)
            logger.info(f"Loaded {len(self.patterns)} patterns from .gitignore")

    def should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored based on .gitignore patterns"""
        rel_path = os.path.relpath(path, self.repo_root)

        for pattern in self.patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith("/"):
                dir_pattern = pattern[:-1]
                if (
                    fnmatch.fnmatch(rel_path, dir_pattern)
                    or fnmatch.fnmatch(rel_path, f"*/{dir_pattern}")
                    or rel_path.startswith(dir_pattern + "/")
                ):
                    return True
            # Handle regular patterns
            else:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                    os.path.basename(path), pattern
                ):
                    return True

        return False


class CodebaseIngestion:
    """Manages codebase ingestion with code-aware preprocessing"""

    def __init__(
        self,
        repo_path: str,
        chroma_db_dir: str = CHROMA_DB_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        skip_dirs: set[str] | None = None,
        min_quality_score: float = 0.0,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        """
        Args:
            repo_path: Path to the repository root
            chroma_db_dir: ChromaDB persistence directory
            collection_name: Name of the collection
            skip_dirs: Additional directories to skip
            min_quality_score: Minimum quality score to include file (0-1)
            embedding_model: Ollama embedding model to use
        """
        self.repo_path = os.path.abspath(repo_path)
        self.repo_name = os.path.basename(self.repo_path)
        self.chroma_db_dir = chroma_db_dir
        self.collection_name = collection_name
        self.min_quality_score = min_quality_score
        self.embedding_model = embedding_model
        self.model_config = get_model_config(embedding_model)

        # Combine default and custom skip dirs
        self.skip_dirs = DEFAULT_SKIP_DIRS.copy()
        if skip_dirs:
            self.skip_dirs.update(skip_dirs)

        # Initialize components
        self.analyzer = DocumentAnalyzer()
        self.chunking_strategy = ChunkingStrategy()
        self.cleaner = ContentCleaner(
            similarity_threshold=0.95,
            min_content_length=50,  # Lower threshold for code
        )
        self.quality_metrics = QualityMetrics()
        self.gitignore = GitignoreParser(self.repo_path)

        # Statistics
        self.stats = {
            "files_found": 0,
            "files_analyzed": 0,
            "files_skipped": 0,
            "files_processed": 0,
            "files_failed": 0,
            "total_chunks": 0,
            "languages": {},
        }

    def discover_files(self) -> list[str]:
        """Discover all relevant files in the repository"""
        files = []
        priority_files = []

        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out directories to skip
            dirs[:] = [
                d
                for d in dirs
                if d not in self.skip_dirs
                and not self.gitignore.should_ignore(os.path.join(root, d))
            ]

            for filename in filenames:
                filepath = os.path.join(root, filename)

                # Skip gitignored files
                if self.gitignore.should_ignore(filepath):
                    continue

                # Check if supported extension
                ext = Path(filename).suffix.lower()
                if ext in self.analyzer.SUPPORTED_EXTENSIONS:
                    if filename in PRIORITY_FILES:
                        priority_files.append(filepath)
                    else:
                        files.append(filepath)

        # Priority files first for better context
        all_files = priority_files + files
        self.stats["files_found"] = len(all_files)

        logger.info(f"Discovered {len(all_files)} files ({len(priority_files)} priority)")
        return all_files

    def run(self):
        """Run the complete codebase ingestion pipeline"""

        logger.info("=" * 80)
        logger.info("CODEBASE INGESTION")
        logger.info("=" * 80)
        logger.info(f"Repository: {self.repo_path}")
        logger.info(f"Started at: {datetime.now()}")

        # Phase 1: File Discovery
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: FILE DISCOVERY")
        logger.info("=" * 80)

        files = self.discover_files()
        if not files:
            logger.error("No supported files found in repository")
            return

        # Phase 2: Embedding Model Setup
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: EMBEDDING MODEL SETUP")
        logger.info("=" * 80)

        embeddings = get_embeddings(self.embedding_model)
        logger.info(f"Embedding model: {self.embedding_model}")
        logger.info(f"Dimensions: {self.model_config.get('dimensions', 'unknown')}")

        # Initialize vector store
        vectorstore = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.chroma_db_dir,
            embedding_function=embeddings,
        )
        logger.info(f"Vector store: {self.chroma_db_dir}/{self.collection_name}")

        # Store embedding model metadata for retrieval alignment
        store_embedding_metadata(vectorstore, self.embedding_model)

        # Phase 3: File Analysis & Chunking
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: FILE ANALYSIS & CHUNKING")
        logger.info("=" * 80)

        all_chunks = []
        failed_files = []

        for filepath in files:
            rel_path = os.path.relpath(filepath, self.repo_path)
            filename = os.path.basename(filepath)

            try:
                # Analyze file
                analysis = self.analyzer.analyze_file(filepath)
                self.stats["files_analyzed"] += 1

                # Skip low quality files
                if analysis.quality_score < self.min_quality_score:
                    logger.debug(f"Skipping low quality: {rel_path}")
                    self.stats["files_skipped"] += 1
                    continue

                # Track languages
                if analysis.programming_language:
                    lang = analysis.programming_language
                    self.stats["languages"][lang] = self.stats["languages"].get(lang, 0) + 1

                # Read file content
                try:
                    with open(filepath, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read {rel_path}: {e}")
                    failed_files.append(rel_path)
                    continue

                if not content.strip():
                    logger.debug(f"Empty file: {rel_path}")
                    continue

                # Create document with rich metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filepath,
                        "relative_path": rel_path,
                        "filename": filename,
                        "repository": self.repo_name,
                        "file_type": analysis.file_type,
                        "programming_language": analysis.programming_language or "unknown",
                        "quality_score": analysis.quality_score,
                        **{
                            k: v
                            for k, v in analysis.metadata.items()
                            if isinstance(v, (str, int, float, bool))
                        },
                    },
                )

                # Filter complex metadata for ChromaDB compatibility
                filtered_docs = filter_complex_metadata([doc])

                # Select chunking strategy
                config = self.chunking_strategy.select_config(
                    structure_type=analysis.structure_type,
                    file_size=analysis.file_size,
                    language=analysis.language,
                    has_complex_structure=analysis.metadata.get("has_code_blocks", False),
                    programming_language=analysis.programming_language,
                )

                # Chunk documents
                chunks = self.chunking_strategy.chunk_documents(
                    filtered_docs, config, source=filepath
                )

                # Add relative path to each chunk
                for chunk in chunks:
                    chunk.metadata["relative_path"] = rel_path
                    chunk.metadata["repository"] = self.repo_name

                all_chunks.extend(chunks)
                self.stats["files_processed"] += 1

                if len(all_chunks) % 100 == 0:
                    logger.info(
                        f"Progress: {self.stats['files_processed']} files, {len(all_chunks)} chunks"
                    )

            except Exception as e:
                logger.error(f"Failed to process {rel_path}: {e}")
                failed_files.append(rel_path)
                self.stats["files_failed"] += 1

        logger.info(f"Created {len(all_chunks)} chunks from {self.stats['files_processed']} files")

        # Phase 4: Content Cleaning
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: CONTENT CLEANING")
        logger.info("=" * 80)

        logger.info(f"Chunks before cleaning: {len(all_chunks)}")

        cleaned_chunks = self.cleaner.clean_and_deduplicate(
            all_chunks,
            remove_near_duplicates=True,
            remove_boilerplate=False,  # Don't remove code patterns
        )

        logger.info(f"Chunks after cleaning: {len(cleaned_chunks)}")
        self.stats["total_chunks"] = len(cleaned_chunks)

        # Phase 5: Quality Metrics
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
            logger.info(f"Ingesting {len(cleaned_chunks)} chunks...")

            try:
                # Add in batches (use model-specific batch size for stability)
                batch_size = self.model_config.get("max_batch_size", 10)
                total_batches = (len(cleaned_chunks) - 1) // batch_size + 1
                logger.info(f"  Using batch size: {batch_size}")
                for i in range(0, len(cleaned_chunks), batch_size):
                    batch = cleaned_chunks[i : i + batch_size]
                    vectorstore.add_documents(batch)
                    batch_num = i // batch_size + 1
                    if batch_num % 20 == 0 or batch_num == total_batches:
                        logger.info(
                            f"  Progress: {batch_num}/{total_batches} batches ({i + len(batch)}/{len(cleaned_chunks)} chunks)"
                        )

                logger.info("Successfully ingested all chunks")

            except Exception as e:
                logger.error(f"Failed to ingest: {e}")
                raise

        # Final Report
        self.print_final_report(failed_files, metrics)

        logger.info(f"\nLog saved to: {log_filename}")

    def print_final_report(self, failed_files: list[str], metrics: dict):
        """Print final ingestion report"""

        logger.info("\n" + "=" * 80)
        logger.info("FINAL REPORT")
        logger.info("=" * 80)

        logger.info(f"\nRepository: {self.repo_name}")
        logger.info(f"Collection: {self.collection_name}")

        logger.info("\nFile Statistics:")
        logger.info(f"  Found: {self.stats['files_found']}")
        logger.info(f"  Analyzed: {self.stats['files_analyzed']}")
        logger.info(f"  Processed: {self.stats['files_processed']}")
        logger.info(f"  Skipped: {self.stats['files_skipped']}")
        logger.info(f"  Failed: {self.stats['files_failed']}")

        logger.info("\nLanguage Distribution:")
        for lang, count in sorted(self.stats["languages"].items(), key=lambda x: -x[1]):
            logger.info(f"  {lang}: {count} files")

        logger.info("\nChunk Statistics:")
        logger.info(f"  Total chunks: {self.stats['total_chunks']}")
        logger.info(f"  Quality grade: {metrics.get('quality_grade', 'Unknown')}")

        if failed_files:
            logger.warning(f"\nFailed Files ({len(failed_files)}):")
            for f in failed_files[:10]:  # Show first 10
                logger.warning(f"  - {f}")
            if len(failed_files) > 10:
                logger.warning(f"  ... and {len(failed_files) - 10} more")

        logger.info(f"\nVector store location: {self.chroma_db_dir}")
        logger.info(f"Collection name: {self.collection_name}")
        logger.info("=" * 80)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description="Ingest a codebase into ChromaDB for coding agent")

    parser.add_argument("repo_path", help="Path to the repository root")

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Collection name (default: {DEFAULT_COLLECTION_NAME})",
    )

    parser.add_argument(
        "--skip-dirs", default="", help="Comma-separated list of additional directories to skip"
    )

    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.0,
        help="Minimum quality score (0.0-1.0, default: 0.0)",
    )

    parser.add_argument(
        "--chroma-dir", default=CHROMA_DB_DIR, help=f"ChromaDB directory (default: {CHROMA_DB_DIR})"
    )

    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Ollama embedding model (default: {DEFAULT_EMBEDDING_MODEL})",
    )

    args = parser.parse_args()

    # Parse skip dirs
    skip_dirs = set()
    if args.skip_dirs:
        skip_dirs = {d.strip() for d in args.skip_dirs.split(",")}

    # Validate repo path
    if not os.path.isdir(args.repo_path):
        logger.error(f"Repository path not found: {args.repo_path}")
        sys.exit(1)

    # Run ingestion
    ingestion = CodebaseIngestion(
        repo_path=args.repo_path,
        chroma_db_dir=args.chroma_dir,
        collection_name=args.collection,
        skip_dirs=skip_dirs,
        min_quality_score=args.min_quality,
        embedding_model=args.embedding_model,
    )

    ingestion.run()


if __name__ == "__main__":
    main()
