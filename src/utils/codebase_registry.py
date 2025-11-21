"""
Codebase Registry System

Manages metadata for all ingested code repositories, tracking:
- Repository information (name, path, URL, branch, commit)
- Ingestion metadata (timestamp, chunk count, file count)
- Embedding configuration (model, dimensions)
- Collection names and status

Registry is stored in codebase_registry.json and provides:
- Add/update repository entries
- Query repository metadata
- List all ingested codebases
- Validate collection existence
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class CodebaseRegistry:
    """Manages registry of ingested code repositories"""

    def __init__(self, registry_file: str = "codebase_registry.json"):
        """
        Initialize registry manager.

        Args:
            registry_file: Path to registry JSON file
        """
        self.registry_file = Path(registry_file)
        self.registry = self._load_registry()

    def _load_registry(self) -> dict:
        """Load registry from file, create if doesn't exist"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"version": "1.0", "codebases": {}}

    def _save_registry(self):
        """Save registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def add_or_update(
        self,
        name: str,
        repo_path: str,
        description: str = "",
        chunk_count: int = 0,
        file_count: int = 0,
        embedding_model: str = "mxbai-embed-large",
        collection_name: Optional[str] = None,
        auto_detect_git: bool = True
    ) -> dict:
        """
        Add or update a codebase entry in the registry.

        Args:
            name: Repository identifier (used in collection name)
            repo_path: Path to repository
            description: Human-readable description
            chunk_count: Number of chunks ingested
            file_count: Number of files processed
            embedding_model: Embedding model used
            collection_name: ChromaDB collection name (defaults to codebase_{name})
            auto_detect_git: Auto-detect git metadata

        Returns:
            Dictionary with codebase metadata
        """
        repo_path = Path(repo_path).resolve()
        collection_name = collection_name or f"codebase_{name}"

        # Build metadata
        metadata = {
            "name": name,
            "description": description,
            "repo_path": str(repo_path),
            "collection_name": collection_name,
            "embedding_model": embedding_model,
            "chunk_count": chunk_count,
            "file_count": file_count,
            "ingested_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Auto-detect git information if enabled
        if auto_detect_git and (repo_path / ".git").exists():
            git_info = self._get_git_info(repo_path)
            metadata.update(git_info)

        # Update registry
        if name in self.registry["codebases"]:
            # Preserve original ingestion timestamp
            metadata["ingested_at"] = self.registry["codebases"][name].get(
                "ingested_at", metadata["ingested_at"]
            )

        self.registry["codebases"][name] = metadata
        self._save_registry()

        return metadata

    def _get_git_info(self, repo_path: Path) -> dict:
        """
        Extract git metadata from repository.

        Args:
            repo_path: Path to git repository

        Returns:
            Dictionary with git metadata
        """
        git_info = {}

        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["repo_url"] = result.stdout.strip()

            # Get current branch
            result = subprocess.run(
                ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()

            # Get current commit hash
            result = subprocess.run(
                ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["commit_hash"] = result.stdout.strip()[:7]

            # Get commit date
            result = subprocess.run(
                ["git", "-C", str(repo_path), "log", "-1", "--format=%ci"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["commit_date"] = result.stdout.strip()

        except Exception as e:
            # Silently ignore git errors
            pass

        return git_info

    def get(self, name: str) -> Optional[dict]:
        """
        Get metadata for a specific codebase.

        Args:
            name: Repository identifier

        Returns:
            Dictionary with codebase metadata or None if not found
        """
        return self.registry["codebases"].get(name)

    def get_by_collection(self, collection_name: str) -> Optional[dict]:
        """
        Get metadata by collection name.

        Args:
            collection_name: ChromaDB collection name

        Returns:
            Dictionary with codebase metadata or None if not found
        """
        for codebase in self.registry["codebases"].values():
            if codebase["collection_name"] == collection_name:
                return codebase
        return None

    def list_all(self) -> List[dict]:
        """
        List all registered codebases.

        Returns:
            List of codebase metadata dictionaries
        """
        return list(self.registry["codebases"].values())

    def remove(self, name: str) -> bool:
        """
        Remove a codebase from registry.

        Args:
            name: Repository identifier

        Returns:
            True if removed, False if not found
        """
        if name in self.registry["codebases"]:
            del self.registry["codebases"][name]
            self._save_registry()
            return True
        return False

    def exists(self, name: str) -> bool:
        """
        Check if a codebase is registered.

        Args:
            name: Repository identifier

        Returns:
            True if exists, False otherwise
        """
        return name in self.registry["codebases"]

    def get_collection_names(self) -> List[str]:
        """
        Get list of all collection names.

        Returns:
            List of ChromaDB collection names
        """
        return [cb["collection_name"] for cb in self.registry["codebases"].values()]

    def get_stats(self) -> dict:
        """
        Get aggregate statistics across all codebases.

        Returns:
            Dictionary with statistics
        """
        codebases = list(self.registry["codebases"].values())

        if not codebases:
            return {
                "total_codebases": 0,
                "total_chunks": 0,
                "total_files": 0,
                "embedding_models": []
            }

        return {
            "total_codebases": len(codebases),
            "total_chunks": sum(cb.get("chunk_count", 0) for cb in codebases),
            "total_files": sum(cb.get("file_count", 0) for cb in codebases),
            "embedding_models": list(set(cb.get("embedding_model", "unknown") for cb in codebases))
        }


def format_codebase_list(codebases: List[dict]) -> str:
    """
    Format codebase list for display.

    Args:
        codebases: List of codebase metadata dictionaries

    Returns:
        Formatted string for console output
    """
    if not codebases:
        return "No codebases registered."

    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("REGISTERED CODEBASES")
    lines.append("=" * 80 + "\n")

    for i, cb in enumerate(codebases, 1):
        lines.append(f"{i}. {cb['name']}")
        if cb.get("description"):
            lines.append(f"   {cb['description']}")
        lines.append(f"   Collection: {cb['collection_name']}")
        lines.append(f"   Path: {cb['repo_path']}")

        if cb.get("repo_url"):
            lines.append(f"   URL: {cb['repo_url']}")
        if cb.get("branch"):
            lines.append(f"   Branch: {cb['branch']} @ {cb.get('commit_hash', 'unknown')}")

        lines.append(f"   Chunks: {cb.get('chunk_count', 0):,} | Files: {cb.get('file_count', 0)}")
        lines.append(f"   Embedding: {cb.get('embedding_model', 'unknown')}")
        lines.append(f"   Last Updated: {cb.get('updated_at', 'unknown')}")
        lines.append("")

    return "\n".join(lines)
