# RAG Knowledge Base Guide

Complete guide for managing the Test-Smith knowledge base using RAG (Retrieval-Augmented Generation).

---

## Overview

Test-Smith uses a RAG system to augment research with domain-specific knowledge:

- **Document Storage**: `documents/` directory
- **Vector Database**: ChromaDB (`chroma_db/`)
- **Embedding Model**: nomic-embed-text (768 dimensions)
- **Retrieval**: Semantic similarity search

---

## Quick Start

### 1. Add Documents

Place files in the `documents/` directory:

```bash
# Supported formats: .txt, .md, .pdf, .docx
cp your-docs/* documents/
```

### 2. Run Ingestion

```bash
# Recommended: Full preprocessing pipeline
python scripts/ingest/ingest_with_preprocessor.py

# With quality filtering
python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.5
```

### 3. Verify

```bash
# Check ingestion log
cat ingestion_preprocessed_*.log

# Run a query to test retrieval
python main.py run "Query about your documents"
```

---

## Ingestion Pipelines

### Production Pipeline (Recommended)

**Script:** `scripts/ingest/ingest_with_preprocessor.py`

**6-Phase Process:**

1. **Document Analysis** - Quality scoring and recommendations
2. **Embedding Setup** - Initialize Ollama embeddings
3. **Chunking** - Smart strategy selection per document
4. **Cleaning** - Deduplication and boilerplate removal
5. **Quality Metrics** - Validation and reporting
6. **Ingestion** - Batch processing to ChromaDB

```bash
# Standard ingestion
python scripts/ingest/ingest_with_preprocessor.py

# Skip low-quality files
python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.5

# Skip analysis (faster)
python scripts/ingest/ingest_with_preprocessor.py --skip-analysis
```

### Diagnostic Pipeline

**Script:** `scripts/ingest/ingest_diagnostic.py`

For debugging embedding issues:

```bash
python scripts/ingest/ingest_diagnostic.py
```

### Clean Re-ingest

**Script:** `scripts/ingest/clean_and_reingest.sh`

Complete database refresh:

```bash
./scripts/ingest/clean_and_reingest.sh
```

---

## Understanding RAG Pipeline

```
DOCUMENTS → LOADING → PREPROCESSING → CHUNKING → EMBEDDING → VECTOR DB → RETRIEVAL
```

### Where Problems Occur

**70% of RAG issues come from preprocessing and chunking**

- Documents are messy (PDFs especially)
- One-size-fits-all chunking fails
- Duplicates create noise
- Small chunks lack context
- Large chunks waste tokens

---

## Chunking Strategies

### Fixed-Size Chunking

Best for plain text, general documents.

```python
chunk_size = 1000
chunk_overlap = 200
```

### Markdown Header Chunking

Best for structured markdown documentation.

```python
headers_to_split_on = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]
```

### Hybrid Chunking

Combines both approaches - best for complex documents.

### Size Guidelines

| Language | Min | Optimal | Max |
|----------|-----|---------|-----|
| English | 200 chars | 500-1000 chars | 1500 chars |
| Japanese/Chinese | 300 chars | 600-1200 chars | 2000 chars |

### Overlap

- **General rule**: 15-20% of chunk size
- **Chunk 1000 → Overlap 200**

---

## Quality Indicators

### Healthy Embeddings

- Median chunk size: 500-800 characters
- Duplication rate: <5%
- Quality score: >0.7
- PCA components for 95% variance: 20-40
- Mean cosine similarity: 0.3-0.8

### Problematic Embeddings

- Median chunk size: <200 characters
- Duplication rate: >15%
- Quality score: <0.5
- PCA components for 99% variance: <10
- Mean similarity: >0.95

---

## Analyzing Your Database

### ChromaDB Explorer Notebook

```bash
jupyter notebook chroma_explorer.ipynb
```

**Key Sections:**

1. **Basic Exploration** - Collection stats, document counts
2. **Data Quality** - Embedding diagnostics, duplicates
3. **PCA Analysis** - Variance distribution, clustering

### Checking Quality Metrics

After ingestion, review the log:

```bash
# Quality metrics summary
grep "Overall quality:" ingestion_preprocessed_*.log

# Chunk size
grep "Median Size:" ingestion_preprocessed_*.log

# Duplication
grep "Removal rate:" ingestion_preprocessed_*.log
```

---

## Troubleshooting

### "Chunks are too small"

**Symptom**: Median chunk size < 200 characters

**Solution**:
```python
# Increase chunk size in preprocessor
chunk_size = 1500
min_chunk_size = 200
```

### "Too many duplicates"

**Symptom**: >20% removal rate

**Solution**:
```python
# More aggressive near-duplicate detection
similarity_threshold = 0.90  # Lower from 0.95
```

### "Poor retrieval quality"

**Symptom**: Irrelevant results returned

**Solutions**:
1. Increase chunk size (more context)
2. Decrease chunk size (more focused)
3. Improve document quality
4. Use better query formulation

### "PCA shows 99% in 1 component"

**Symptom**: All embeddings cluster together

**Causes**:
- Duplicate chunks
- Tiny chunks
- Documents too similar

**Solution**: Run full preprocessing with deduplication

### "Ollama embedding errors"

**Symptom**: 500 Internal Server Error

**Solution**: Reduce batch size
```python
batch_size = 50  # Down from 100
```

---

## Best Practices

### Document Preparation

1. **Remove test/placeholder files** before ingestion
2. **Check PDF quality** - text vs scanned
3. **Verify encoding** - UTF-8 for all text
4. **Target 2,000-10,000 words** per document

### Quality Control

1. **Run analysis first** - review quality scores
2. **Filter low-quality** - use `--min-quality 0.5`
3. **Check metrics** - median size, duplication rate
4. **Test retrieval** - verify with sample queries

### Maintenance

1. **Monitor quality over time** - track scores
2. **Re-ingest when documents change**
3. **Archive old evaluations**
4. **Update preprocessing parameters** as needed

---

## Configuration Reference

### Key Parameters

| Parameter | Location | Default | Purpose |
|-----------|----------|---------|---------|
| `chunk_size` | preprocessor | 1000 | Target chunk size |
| `chunk_overlap` | preprocessor | 200 | Overlap between chunks |
| `min_chunk_size` | preprocessor | 100 | Filter tiny chunks |
| `similarity_threshold` | cleaner | 0.95 | Near-duplicate threshold |
| `min_quality_score` | CLI arg | 0.0 | Filter low-quality files |

### File Locations

| Content | Location |
|---------|----------|
| Source documents | `documents/` |
| Vector database | `chroma_db/` |
| Ingestion scripts | `scripts/ingest/` |
| Preprocessor code | `src/preprocessor/` |

---

## Related Documentation

- **[Writing Documentation](writing-docs.md)** - Create RAG-friendly content
- **[Quality Evaluation](quality-evaluation.md)** - Measure documentation quality
- **[Preprocessor](preprocessor.md)** - Detailed preprocessor usage
