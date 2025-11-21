"""
Batch Codebase Ingestion Script

Reads codebases.yaml configuration file and ingests multiple repositories
into separate ChromaDB collections. Each repository gets its own collection
named: codebase_{repo_name}

Features:
- Config-based repository management
- Auto-detection of git metadata (branch, commit, URL)
- Registry tracking for all ingested codebases
- Quality preprocessing and validation
- Progress tracking and error handling
- Selective ingestion (--repos flag)

Usage:
    # Ingest all enabled repositories
    python scripts/ingest/ingest_codebases.py

    # Ingest specific repositories only
    python scripts/ingest/ingest_codebases.py --repos test-smith my-other-project

    # Dry run (show what would be ingested)
    python scripts/ingest/ingest_codebases.py --dry-run

    # Force re-ingestion (clear existing collections)
    python scripts/ingest/ingest_codebases.py --force
"""

import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
from src.utils.embedding_utils import get_embeddings, store_embedding_metadata
from src.utils.codebase_registry import CodebaseRegistry, format_codebase_list
from src.preprocessor import DocumentAnalyzer


class CodebaseIngestor:
    """Handles batch ingestion of multiple code repositories"""

    def __init__(self, config_file: str = "codebases.yaml", verbose: bool = True):
        """
        Initialize ingestor.

        Args:
            config_file: Path to YAML configuration file
            verbose: Enable verbose logging
        """
        self.config_file = Path(config_file)
        self.verbose = verbose
        self.config = self._load_config()
        self.registry = CodebaseRegistry(
            self.config["global_settings"].get("registry_file", "codebase_registry.json")
        )

        # Global settings
        self.embedding_model = self.config["global_settings"].get("embedding_model", "mxbai-embed-large")
        self.persist_directory = self.config["global_settings"].get("persist_directory", "chroma_db")
        self.batch_size = self.config["global_settings"].get("batch_size", 10)
        self.auto_detect_git = self.config["global_settings"].get("auto_detect_git", True)

    def _load_config(self) -> dict:
        """Load YAML configuration file"""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                f"Please create codebases.yaml in the project root."
            )

        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)

        if "repositories" not in config:
            raise ValueError("Configuration must contain 'repositories' section")

        return config

    def _log(self, message: str, level: str = "INFO"):
        """Log message if verbose enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def _collect_documents(self, repo_path: Path, repo_config: dict) -> tuple[List[str], Dict]:
        """
        Collect and preprocess documents from repository.

        Args:
            repo_path: Path to repository
            repo_config: Repository configuration

        Returns:
            Tuple of (document_contents, statistics)
        """
        ingestion_options = repo_config.get("ingestion_options", {})
        file_extensions = ingestion_options.get("file_extensions", [".py", ".md"])
        exclude_patterns = ingestion_options.get("exclude_patterns", [])
        min_quality = ingestion_options.get("min_quality", 0.5)

        self._log(f"Collecting documents from: {repo_path}")
        self._log(f"File extensions: {', '.join(file_extensions)}")

        # Collect files
        all_files = []
        for ext in file_extensions:
            files = list(repo_path.rglob(f"*{ext}"))
            all_files.extend(files)

        # Filter out excluded patterns
        filtered_files = []
        for file_path in all_files:
            exclude = False
            for pattern in exclude_patterns:
                if file_path.match(pattern):
                    exclude = True
                    break
            if not exclude:
                filtered_files.append(file_path)

        self._log(f"Found {len(filtered_files)} files (filtered from {len(all_files)} total)")

        # Process documents
        analyzer = DocumentAnalyzer()

        documents = []
        stats = {
            "total_files": len(filtered_files),
            "processed_files": 0,
            "skipped_files": 0,
        }

        for file_path in filtered_files:
            try:
                # Analyze quality
                analysis = analyzer.analyze_file(str(file_path))

                # Read content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if not content.strip():
                    self._log(f"Skipping empty file: {file_path.name}", "DEBUG")
                    stats["skipped_files"] += 1
                    continue

                if analysis.quality_score < min_quality:
                    self._log(f"Skipping low quality file: {file_path.name} (score: {analysis.quality_score:.2f})", "WARN")
                    stats["skipped_files"] += 1
                    continue

                # Create document with metadata (no chunking - ChromaDB handles it)
                rel_path = str(file_path.relative_to(repo_path))
                doc = Document(
                    page_content=content,
                    metadata={
                        'source': str(file_path),
                        'relative_path': rel_path,
                        'filename': file_path.name,
                        'file_type': analysis.file_type,
                        'programming_language': analysis.programming_language or 'unknown',
                        'quality_score': analysis.quality_score,
                    }
                )

                documents.append(doc)
                stats["processed_files"] += 1

            except Exception as e:
                self._log(f"Error processing {file_path.name}: {e}", "ERROR")
                stats["skipped_files"] += 1

        self._log(f"Collection complete: {stats['processed_files']} files, {stats['skipped_files']} skipped")

        return documents, stats

    def ingest_repository(self, repo_config: dict, force: bool = False) -> bool:
        """
        Ingest a single repository into ChromaDB.

        Args:
            repo_config: Repository configuration
            force: Force re-ingestion (clear existing collection)

        Returns:
            True if successful, False otherwise
        """
        name = repo_config["name"]
        repo_path = Path(repo_config["path"]).resolve()
        description = repo_config.get("description", "")
        collection_name = f"codebase_{name}"

        self._log(f"\n{'=' * 80}")
        self._log(f"Ingesting Repository: {name}")
        self._log(f"{'=' * 80}")

        # Validate repository path
        if not repo_path.exists():
            self._log(f"Repository path not found: {repo_path}", "ERROR")
            return False

        # Check if collection already exists
        if self.registry.exists(name) and not force:
            self._log(f"Repository '{name}' already ingested. Use --force to re-ingest.", "WARN")
            return False

        try:
            # Collect and preprocess documents
            documents, stats = self._collect_documents(repo_path, repo_config)

            if not documents:
                self._log("No documents collected. Skipping ingestion.", "WARN")
                return False

            # Create embeddings
            self._log(f"Creating embeddings using {self.embedding_model}...")
            embeddings = get_embeddings(self.embedding_model)

            # Initialize ChromaDB
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )

            # Store embedding metadata
            store_embedding_metadata(vectorstore, self.embedding_model)

            # Clear existing collection if force mode
            if force:
                self._log("Force mode: Clearing existing collection...", "WARN")
                vectorstore.delete_collection()
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=embeddings,
                    persist_directory=self.persist_directory
                )
                store_embedding_metadata(vectorstore, self.embedding_model)

            # Filter metadata and add documents in batches
            self._log(f"Adding {len(documents)} documents to collection in batches of {self.batch_size}...")
            filtered_docs = filter_complex_metadata(documents)

            for i in range(0, len(filtered_docs), self.batch_size):
                batch = filtered_docs[i:i + self.batch_size]
                vectorstore.add_documents(batch)
                if self.verbose and (i // self.batch_size) % 5 == 0:
                    progress = min(i + self.batch_size, len(filtered_docs))
                    self._log(f"Progress: {progress}/{len(filtered_docs)} documents")

            # Update registry
            self._log("Updating codebase registry...")
            self.registry.add_or_update(
                name=name,
                repo_path=str(repo_path),
                description=description,
                chunk_count=len(filtered_docs),  # Number of documents added
                file_count=stats["processed_files"],
                embedding_model=self.embedding_model,
                collection_name=collection_name,
                auto_detect_git=self.auto_detect_git
            )

            self._log(f"✓ Successfully ingested '{name}'")
            self._log(f"  Collection: {collection_name}")
            self._log(f"  Files: {stats['processed_files']}")
            self._log(f"  Documents: {len(filtered_docs)}")

            return True

        except Exception as e:
            self._log(f"Error ingesting repository: {e}", "ERROR")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return False

    def ingest_all(self, selected_repos: List[str] = None, force: bool = False, dry_run: bool = False):
        """
        Ingest all enabled repositories from config.

        Args:
            selected_repos: List of repository names to ingest (None = all enabled)
            force: Force re-ingestion
            dry_run: Show what would be ingested without doing it
        """
        repositories = self.config.get("repositories", [])

        # Filter repositories
        to_ingest = []
        for repo in repositories:
            if not repo.get("enabled", True):
                continue

            if selected_repos and repo["name"] not in selected_repos:
                continue

            to_ingest.append(repo)

        if not to_ingest:
            print("No repositories to ingest.")
            return

        print(f"\n{'=' * 80}")
        print(f"BATCH CODEBASE INGESTION")
        print(f"{'=' * 80}")
        print(f"Repositories to ingest: {len(to_ingest)}")
        print(f"Embedding model: {self.embedding_model}")
        print(f"Persist directory: {self.persist_directory}")
        if dry_run:
            print("DRY RUN MODE - No changes will be made")
        print(f"{'=' * 80}\n")

        if dry_run:
            for repo in to_ingest:
                print(f"Would ingest: {repo['name']}")
                print(f"  Path: {repo['path']}")
                print(f"  Collection: codebase_{repo['name']}")
                print()
            return

        # Ingest repositories
        results = {"success": 0, "failed": 0, "skipped": 0}

        for i, repo in enumerate(to_ingest, 1):
            print(f"\n[{i}/{len(to_ingest)}] Processing: {repo['name']}")
            success = self.ingest_repository(repo, force=force)

            if success:
                results["success"] += 1
            elif self.registry.exists(repo["name"]) and not force:
                results["skipped"] += 1
            else:
                results["failed"] += 1

        # Print summary
        print(f"\n{'=' * 80}")
        print("INGESTION COMPLETE")
        print(f"{'=' * 80}")
        print(f"Successful: {results['success']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Failed: {results['failed']}")
        print(f"{'=' * 80}\n")

        # Show registry stats
        stats = self.registry.get_stats()
        print(f"Total registered codebases: {stats['total_codebases']}")
        print(f"Total chunks: {stats['total_chunks']:,}")
        print(f"Total files: {stats['total_files']:,}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Batch Codebase Ingestion - Ingest multiple repositories from config file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all enabled repositories
  python scripts/ingest/ingest_codebases.py

  # Ingest specific repositories
  python scripts/ingest/ingest_codebases.py --repos test-smith my-other-project

  # Dry run
  python scripts/ingest/ingest_codebases.py --dry-run

  # Force re-ingestion
  python scripts/ingest/ingest_codebases.py --force
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default="codebases.yaml",
        help="Path to YAML configuration file (default: codebases.yaml)"
    )
    parser.add_argument(
        "--repos",
        type=str,
        nargs="+",
        help="Specific repository names to ingest (default: all enabled)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion (clear existing collections)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without doing it"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose logging"
    )

    args = parser.parse_args()

    try:
        ingestor = CodebaseIngestor(
            config_file=args.config,
            verbose=not args.quiet
        )

        ingestor.ingest_all(
            selected_repos=args.repos,
            force=args.force,
            dry_run=args.dry_run
        )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
