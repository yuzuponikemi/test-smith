# Codebase Management System

This document explains how Test-Smith manages multiple code repositories for the code investigation workflow.

## Overview

Test-Smith can ingest multiple code repositories into separate vector store collections, allowing you to:
- Search a single codebase
- Compare multiple codebases side-by-side
- Analyze how different projects implement similar concepts

## Key Files

### 1. `codebases.yaml` - Configuration File

**Purpose:** Defines which repositories should be ingested and how.

**Location:** `/Users/ikmx/source/personal/test-smith/codebases.yaml`

**Format:**
```yaml
repositories:
  - name: my-project              # Unique identifier
    path: /path/to/repo          # Local filesystem path
    description: "Project description"
    enabled: true                 # Set to false to skip during batch ingestion
    ingestion_options:
      min_quality: 0.5           # Quality threshold (0.0-1.0)
      chunk_size: 1000           # Target chunk size in characters
```

**Use Cases:**
- Add new repositories to the ingestion pipeline
- Enable/disable repositories without deleting configuration
- Set custom ingestion parameters per repository
- Document which repositories are available

**Who manages it:** You (manually edit to add/remove repos)

---

### 2. `codebase_registry.json` - State Tracking Database

**Purpose:** Tracks which repositories have been ingested and their metadata.

**Location:** `/Users/ikmx/source/personal/test-smith/codebase_registry.json`

**Format:**
```json
{
  "version": "1.0",
  "codebases": {
    "my-project": {
      "name": "my-project",
      "description": "Project description",
      "repo_path": "/path/to/repo",
      "collection_name": "codebase_my-project",
      "embedding_model": "mxbai-embed-large",
      "chunk_count": 1246,
      "file_count": 133,
      "ingested_at": "2025-11-21T11:19:27.613615",
      "updated_at": "2025-11-21T11:25:12.874000",
      "repo_url": "https://github.com/user/repo.git",
      "branch": "main",
      "commit_hash": "abc1234",
      "commit_date": "2025-11-21 00:18:54 +0900"
    }
  }
}
```

**Use Cases:**
- View which repositories have been successfully ingested
- Check ingestion timestamps and chunk counts
- Track git metadata (commit hash, branch, etc.)
- Verify embedding model consistency across collections

**Who manages it:**
- Automatically updated by `ingest_codebases.py` (batch script)
- Manually updated if using `ingest_codebase.py` (direct script)

---

## Ingestion Scripts

### Option 1: Batch Ingestion (Recommended) ⭐

**Script:** `scripts/ingest/ingest_codebases.py` (plural)

**What it does:**
1. Reads `codebases.yaml`
2. Ingests all repositories where `enabled: true`
3. Automatically updates `codebase_registry.json`
4. Creates collections named `codebase_<name>`

**Usage:**
```bash
# Ingest all enabled repositories
python scripts/ingest/ingest_codebases.py

# Ingest specific repository by name
python scripts/ingest/ingest_codebases.py --repo my-project
```

**Advantages:**
- ✅ Registry automatically updated
- ✅ Batch processing multiple repos
- ✅ Configuration-driven (YAML)
- ✅ Git metadata captured

**When to use:**
- Initial setup with multiple repos
- Re-ingesting repos defined in YAML
- Production/automated workflows

---

### Option 2: Direct Ingestion

**Script:** `scripts/ingest/ingest_codebase.py` (singular)

**What it does:**
1. Ingests a single repository by path
2. Creates a collection with specified name
3. Does NOT update `codebase_registry.json` (manual update needed)

**Usage:**
```bash
# Ingest a specific directory
python scripts/ingest/ingest_codebase.py /path/to/repo --collection codebase_my_project
```

**Advantages:**
- ✅ Quick ad-hoc ingestion
- ✅ No YAML config needed
- ✅ Flexible collection naming

**Disadvantages:**
- ❌ Registry not automatically updated
- ❌ Manual metadata management

**When to use:**
- Quick testing
- One-off ingestion
- Non-standard collection names

---

## Workflow Examples

### Adding a New Repository

**Step 1:** Add to `codebases.yaml`
```yaml
repositories:
  - name: new-project
    path: /Users/ikmx/source/personal/new-project
    description: "My new project"
    enabled: true
    ingestion_options:
      min_quality: 0.5
```

**Step 2:** Run batch ingestion
```bash
python scripts/ingest/ingest_codebases.py --repo new-project
```

**Step 3:** Verify ingestion
```bash
python main.py list-codebases
```

**Result:**
- ✅ Collection `codebase_new-project` created in ChromaDB
- ✅ Registry updated with metadata
- ✅ Ready for code investigation queries

---

### Comparing Two Repositories

**Query a single repository:**
```bash
python main.py run "How does authentication work?" \
  --graph code_investigation \
  --collection codebase_my_project
```

**Compare two repositories:**
```bash
python main.py run "How do these repos handle authentication differently?" \
  --graph code_investigation \
  --collections codebase_project_a codebase_project_b
```

---

### Viewing Registered Codebases

**List all:**
```bash
python main.py list-codebases
```

**With statistics:**
```bash
python main.py list-codebases --stats
```

**Output:**
```
================================================================================
REGISTERED CODEBASES
================================================================================

1. test-smith
   Test-Smith - Multi-Graph Research Agent System
   Collection: codebase_test_smith
   Chunks: 1,246 | Files: 133
   Embedding: mxbai-embed-large
   Last Updated: 2025-11-21T11:25:12.874000

2. local-deepr
   Local DeepR - Research/Analysis Application
   Collection: codebase_local-deepr
   Chunks: 15 | Files: 15
   ...
```

---

## ChromaDB Collections

Each ingested repository creates a separate ChromaDB collection:

**Naming Convention:** `codebase_<repo-name>`

**Location:** `chroma_db/` directory

**Examples:**
- test-smith → `codebase_test_smith`
- local-deepr → `codebase_local-deepr`
- flappy-bird-csharp → `codebase_flappy-bird-csharp`

**Why separate collections?**
- Isolation: Each repo's embeddings are independent
- Flexibility: Query single or multiple repos
- Comparison: Side-by-side analysis across repos
- Alignment: All use same embedding model (mxbai-embed-large)

---

## File Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Layer                       │
├─────────────────────────────────────────────────────────────┤
│  codebases.yaml                                             │
│  • Defines available repositories                           │
│  • User-edited configuration                                │
│  • enabled/disabled per repo                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ingestion Scripts                         │
├─────────────────────────────────────────────────────────────┤
│  ingest_codebases.py (batch)    ingest_codebase.py (direct)│
│  • Reads YAML config            • Takes path as argument    │
│  • Updates registry             • Manual registry update    │
│  • Batch processing             • Single repo               │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    State Tracking Layer                      │
├─────────────────────────────────────────────────────────────┤
│  codebase_registry.json                                     │
│  • Tracks ingested repositories                             │
│  • Metadata (chunks, files, timestamps)                     │
│  • Git info (commit, branch)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
├─────────────────────────────────────────────────────────────┤
│  chroma_db/                                                 │
│  ├── codebase_test_smith/     (1,246 chunks)               │
│  ├── codebase_local-deepr/    (15 chunks)                  │
│  └── codebase_flappy-bird-csharp/ (13 chunks)              │
│                                                             │
│  • Separate collection per repository                       │
│  • Embeddings via mxbai-embed-large                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Query Layer                               │
├─────────────────────────────────────────────────────────────┤
│  main.py --graph code_investigation                         │
│  • --collection <name>        (single repo)                │
│  • --collections <n1> <n2>    (comparison mode)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Registry out of sync with YAML

**Problem:** `codebases.yaml` has 3 repos, but `codebase_registry.json` only has 2.

**Cause:** Used direct ingestion script (`ingest_codebase.py`) which doesn't update registry.

**Solution:**
1. Use batch script: `python scripts/ingest/ingest_codebases.py --repo missing-repo`
2. Or manually add entry to `codebase_registry.json` with correct metadata

---

### Collection not found

**Error:** `Collection 'codebase_xyz' not found`

**Checks:**
1. Verify collection exists: `python main.py list-codebases`
2. Check ChromaDB: `ls -la chroma_db/`
3. Ensure ingestion completed successfully

---

### Wrong embedding model

**Problem:** Collections using different embedding models can't be compared.

**Check:**
```bash
python main.py list-codebases | grep "Embedding:"
```

All should show: `Embedding: mxbai-embed-large`

**Fix:** Re-ingest with correct model in `src/utils/embeddings.py`

---

## Best Practices

1. **Always use batch ingestion** for repos defined in YAML
2. **Keep registry in sync** - verify after any manual ingestion
3. **Use descriptive names** - helps identify collections later
4. **Document repositories** in YAML descriptions
5. **Version control YAML** - track which repos are configured
6. **Check quality scores** - ensure embeddings are good quality (>0.7)
7. **Consistent embedding models** - always use mxbai-embed-large

---

## Related Documentation

- **Code Investigation Graph:** `src/graphs/code_investigation_graph.py`
- **Retriever Implementation:** `src/nodes/code_assistant_node.py`
- **Comparison Prompts:** `src/prompts/code_investigation_prompts.py`
- **Registry API:** `src/utils/codebase_registry.py`

---

## Quick Reference

**List codebases:**
```bash
python main.py list-codebases
```

**Ingest from YAML:**
```bash
python scripts/ingest/ingest_codebases.py
```

**Direct ingestion:**
```bash
python scripts/ingest/ingest_codebase.py <path> --collection <name>
```

**Single repo query:**
```bash
python main.py run "query" --graph code_investigation --collection codebase_name
```

**Comparison query:**
```bash
python main.py run "query" --graph code_investigation --collections name1 name2
```
