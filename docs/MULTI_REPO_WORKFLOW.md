# Multi-Repository Codebase Management

**Version:** Test-Smith v2.2
**Feature:** Config-based multi-repository ingestion and investigation

## Overview

Test-Smith now supports ingesting and investigating multiple code repositories through a powerful config-based system. Each repository is stored in its own ChromaDB collection, providing clean isolation, targeted queries, and efficient management.

## Architecture

### Key Components

1. **codebases.yaml** - Configuration file defining repositories to ingest
2. **CodebaseRegistry** - Centralized metadata tracking for all repositories
3. **Batch Ingestion Script** - Automated ingestion from config file
4. **Code Investigation Graph** - Specialized workflow with collection selection
5. **CLI Commands** - Easy management and querying

### Collection Naming

Each repository gets its own collection:
```
codebase_{repo_name}
```

Examples:
- `codebase_test_smith` - This repository
- `codebase_my_dotnet_app` - Your C# application
- `codebase_customer_portal` - Customer portal repository

## Quick Start

### 1. Configure Repositories

Edit `codebases.yaml` to define your repositories:

```yaml
repositories:
  - name: test-smith
    path: .
    description: "Test-Smith - Multi-Graph Research Agent"
    enabled: true
    ingestion_options:
      min_quality: 0.5
      file_extensions:
        - .py
        - .md
      exclude_patterns:
        - "**/__pycache__/**"
        - "**/.venv/**"

  - name: my-csharp-app
    path: /Users/you/projects/my-csharp-app
    description: "My C# Application - Windows Forms"
    enabled: true
    ingestion_options:
      min_quality: 0.5
      file_extensions:
        - .cs
        - .csproj
        - .sln
        - .xaml
      exclude_patterns:
        - "**/bin/**"
        - "**/obj/**"
```

### 2. Ingest Repositories

```bash
# Activate virtual environment
source .venv/bin/activate

# Ingest all enabled repositories
python scripts/ingest/ingest_codebases.py

# Ingest specific repositories only
python scripts/ingest/ingest_codebases.py --repos test-smith my-csharp-app

# Dry run (see what would be ingested)
python scripts/ingest/ingest_codebases.py --dry-run

# Force re-ingestion (clear and rebuild)
python scripts/ingest/ingest_codebases.py --force
```

### 3. List Ingested Codebases

```bash
# List all registered codebases
python main.py list-codebases

# Show aggregate statistics
python main.py list-codebases --stats
```

### 4. Query Specific Repository

```bash
# Query test-smith repository
python main.py run "How does the graph registry work?" \
  --graph code_investigation \
  --collection codebase_test_smith

# Query your C# application
python main.py run "Where is the authentication logic?" \
  --graph code_investigation \
  --collection codebase_my_csharp_app

# Default to codebase_collection if no collection specified
python main.py run "How does this work?" --graph code_investigation
```

## Configuration Reference

### Repository Configuration

Each repository in `codebases.yaml` supports:

```yaml
- name: my-repo              # Required: Unique identifier (used in collection name)
  path: /path/to/repo        # Required: Absolute or relative path
  description: "..."         # Optional: Human-readable description
  enabled: true              # Optional: Enable/disable ingestion (default: true)
  ingestion_options:         # Optional: Override global settings
    min_quality: 0.5         # Minimum quality score (0.0-1.0)
    file_extensions:         # File types to include
      - .py
      - .cs
      - .md
    exclude_patterns:        # Glob patterns to exclude
      - "**/__pycache__/**"
      - "**/bin/**"
```

### Global Settings

```yaml
global_settings:
  embedding_model: mxbai-embed-large  # Ollama embedding model
  persist_directory: chroma_db        # ChromaDB storage location
  registry_file: codebase_registry.json  # Registry metadata file
  batch_size: 10                      # Embedding batch size
  auto_detect_git: true               # Extract git metadata
  verbose: true                       # Enable detailed logging
```

## Registry System

The registry (`codebase_registry.json`) tracks metadata for all ingested repositories:

```json
{
  "version": "1.0",
  "codebases": {
    "test-smith": {
      "name": "test-smith",
      "description": "Test-Smith - Multi-Graph Research Agent",
      "repo_path": "/Users/you/test-smith",
      "collection_name": "codebase_test_smith",
      "embedding_model": "mxbai-embed-large",
      "chunk_count": 1180,
      "file_count": 126,
      "repo_url": "https://github.com/you/test-smith",
      "branch": "main",
      "commit_hash": "983813f",
      "ingested_at": "2025-11-21T00:15:00",
      "updated_at": "2025-11-21T01:30:00"
    }
  }
}
```

### Registry API

Python API for programmatic access:

```python
from src.utils.codebase_registry import CodebaseRegistry

# Initialize registry
registry = CodebaseRegistry()

# Get metadata for a specific codebase
metadata = registry.get("test-smith")
print(f"Collection: {metadata['collection_name']}")
print(f"Chunks: {metadata['chunk_count']}")

# List all codebases
codebases = registry.list_all()

# Get aggregate statistics
stats = registry.get_stats()
print(f"Total codebases: {stats['total_codebases']}")
print(f"Total chunks: {stats['total_chunks']}")
```

## Best Practices

### 1. One Collection Per Repository

**Why?**
- Clean isolation and independent updates
- Targeted queries with less noise
- Better performance with smaller search spaces
- Easy to version control (different branches)

### 2. Meaningful Repository Names

Use descriptive, URL-safe names:
- ✅ `my-customer-portal`
- ✅ `backend_api`
- ✅ `mobile_app_ios`
- ❌ `repo1`
- ❌ `test`

### 3. Configure File Extensions Appropriately

Include only relevant file types:

**Python project:**
```yaml
file_extensions:
  - .py
  - .md
  - .yaml
  - .txt
```

**C# project:**
```yaml
file_extensions:
  - .cs
  - .csproj
  - .sln
  - .xaml
  - .resx
  - .md
```

**Full-stack project:**
```yaml
file_extensions:
  - .py
  - .js
  - .jsx
  - .ts
  - .tsx
  - .cs
  - .md
```

### 4. Use Exclude Patterns Aggressively

Exclude build artifacts, dependencies, and generated code:

```yaml
exclude_patterns:
  # Python
  - "**/__pycache__/**"
  - "**/.venv/**"
  - "**/venv/**"

  # C#
  - "**/bin/**"
  - "**/obj/**"
  - "**/.vs/**"
  - "**/packages/**"

  # JavaScript
  - "**/node_modules/**"
  - "**/dist/**"
  - "**/build/**"

  # General
  - "**/.git/**"
  - "**/logs/**"
  - "**/reports/**"
```

### 5. Quality Filtering

Set appropriate quality thresholds:

- **min_quality: 0.7** - Strict (only high-quality docs)
- **min_quality: 0.5** - Moderate (balanced)
- **min_quality: 0.3** - Permissive (include more files)

### 6. Regular Updates

Re-ingest after major changes:

```bash
# Update specific repository
python scripts/ingest/ingest_codebases.py --repos my-repo --force

# Update all repositories
python scripts/ingest/ingest_codebases.py --force
```

## Workflow Examples

### Example 1: Multi-Repository Investigation

```bash
# Configure multiple repositories in codebases.yaml
# - frontend (React/TypeScript)
# - backend (Python/FastAPI)
# - mobile (React Native)

# Ingest all
python scripts/ingest/ingest_codebases.py

# Investigate each separately
python main.py run "How is authentication implemented?" \
  --graph code_investigation \
  --collection codebase_frontend

python main.py run "How is authentication implemented?" \
  --graph code_investigation \
  --collection codebase_backend

python main.py run "How is authentication implemented?" \
  --graph code_investigation \
  --collection codebase_mobile
```

### Example 2: Branch-Specific Analysis

```bash
# Ingest main branch
- name: myapp-main
  path: /path/to/myapp
  enabled: true

# Ingest develop branch
- name: myapp-develop
  path: /path/to/myapp-develop-clone
  enabled: true

# Compare implementations
python main.py run "How does feature X work?" \
  --graph code_investigation \
  --collection codebase_myapp_main

python main.py run "How does feature X work?" \
  --graph code_investigation \
  --collection codebase_myapp_develop
```

### Example 3: Cross-Language Investigation

```bash
# Configure polyglot repository
- name: fullstack-app
  path: /path/to/fullstack
  ingestion_options:
    file_extensions:
      - .py      # Backend
      - .cs      # Services
      - .tsx     # Frontend
      - .sql     # Database
      - .md      # Docs

# Investigate all layers
python main.py run "Trace user login flow across all layers" \
  --graph code_investigation \
  --collection codebase_fullstack_app
```

## Troubleshooting

### Issue: Collection Not Found

**Error:** `Collection 'codebase_myrepo' not found`

**Solution:**
```bash
# Check registered codebases
python main.py list-codebases

# Verify collection name matches
# Should be: codebase_{name_from_yaml}

# Re-ingest if needed
python scripts/ingest/ingest_codebases.py --repos myrepo --force
```

### Issue: Embedding Model Mismatch

**Error:** `Embedding dimension mismatch`

**Solution:**
- All repositories must use the same embedding model (configured in `global_settings`)
- If changing models, re-ingest all repositories
- Check registry to verify model consistency

### Issue: Low Quality Results

**Symptoms:** Retrieved code is not relevant

**Solutions:**
1. Lower `min_quality` threshold
2. Add more file extensions
3. Review exclude patterns (might be too aggressive)
4. Check if repository was actually ingested: `python main.py list-codebases`

### Issue: Slow Ingestion

**Symptoms:** Ingestion takes very long

**Solutions:**
1. Reduce batch size in `global_settings.batch_size`
2. Add more exclude patterns (reduce file count)
3. Increase `min_quality` to skip low-quality files
4. Use `--repos` to ingest one at a time

## Advanced Usage

### Programmatic Ingestion

```python
from scripts.ingest.ingest_codebases import CodebaseIngestor

ingestor = CodebaseIngestor(config_file="codebases.yaml")

# Ingest specific repositories
ingestor.ingest_all(selected_repos=["repo1", "repo2"])

# Force re-ingestion
ingestor.ingest_all(force=True)
```

### Custom Collection Names

```python
from src.utils.codebase_registry import CodebaseRegistry

registry = CodebaseRegistry()

# Add custom entry
registry.add_or_update(
    name="special-repo",
    repo_path="/path/to/repo",
    description="Special repository",
    collection_name="custom_collection_name",  # Override default
    chunk_count=500,
    file_count=50,
    embedding_model="mxbai-embed-large"
)
```

### Cross-Repository Search (Future Enhancement)

Currently, each query targets one collection. Future enhancement could support:

```bash
# Search multiple repositories simultaneously
python main.py run "Find authentication implementations" \
  --graph code_investigation \
  --collections codebase_frontend,codebase_backend,codebase_mobile
```

## Migration Guide

### From Single Codebase to Multi-Repo

If you previously used `ingest_codebase.py` with `codebase_collection`:

1. **Existing data is preserved** - `codebase_collection` still works
2. **Create `codebases.yaml`** with your current repository
3. **Run batch ingestion** to add to registry
4. **Add new repositories** to config as needed
5. **Use `--collection` flag** to specify target

### Backward Compatibility

```bash
# Old way (still works)
python scripts/ingest/ingest_codebase.py --name myrepo

# New way (recommended)
# 1. Add to codebases.yaml
# 2. Run: python scripts/ingest/ingest_codebases.py

# Querying works the same
python main.py run "How does X work?" \
  --graph code_investigation \
  --collection codebase_collection  # Old default still works
```

## See Also

- **CLAUDE.md** - Main project documentation
- **RAG_DATA_PREPARATION_GUIDE.md** - Ingestion best practices
- **WRITING_RAG_FRIENDLY_DOCUMENTATION.md** - Doc writing guidelines
- **DOCUMENT_DESIGN_EVALUATION.md** - Quality metrics
