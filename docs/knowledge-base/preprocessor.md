# Document Preprocessor Guide

Intelligent document preprocessing for high-quality RAG embeddings.

---

## What It Does

The preprocessor automatically:
- Analyzes document quality
- Selects optimal chunking strategy per document
- Removes duplicates and boilerplate
- Filters tiny/useless chunks
- Calculates quality metrics
- Provides actionable recommendations

---

## Quick Start

### Basic Usage

```bash
# Full preprocessing pipeline
python scripts/ingest/ingest_with_preprocessor.py
```

### With Options

```bash
# Filter low-quality files
python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.5

# Skip analysis (faster)
python scripts/ingest/ingest_with_preprocessor.py --skip-analysis

# Disable deduplication
python scripts/ingest/ingest_with_preprocessor.py --disable-deduplication

# Disable boilerplate removal
python scripts/ingest/ingest_with_preprocessor.py --disable-boilerplate
```

---

## Preprocessing Pipeline

### Phase 1: Document Analysis

Analyzes each file in `documents/`:

```python
from src.preprocessor import DocumentAnalyzer

analyzer = DocumentAnalyzer()
analyses = analyzer.analyze_directory('documents')
analyzer.print_report()
```

**Generates:**
- Quality scores (0-1)
- Issue detection
- Recommendations

### Phase 2: Chunking Strategy Selection

Automatically selects best strategy per document:

- **Recursive**: General text
- **Markdown Headers**: Structured markdown
- **Hybrid**: Complex documents

### Phase 3: Content Cleaning

Removes noise before embedding:

- Exact duplicates (MD5 hash)
- Near-duplicates (95% similarity)
- Boilerplate (>20% of docs)
- Tiny chunks (<100 chars)

### Phase 4: Quality Metrics

Calculates and reports:
- Chunk size distribution
- Uniqueness ratio
- Vocabulary diversity
- Overall quality score

### Phase 5: Vector Store Ingestion

Batch processing to ChromaDB with error handling.

---

## Understanding Reports

### Document Analysis Report

```
DOCUMENT ANALYSIS REPORT
================================================================================
Total Files Analyzed: 11
Quality Distribution:
  High Quality (≥0.7):   8 files
  Medium Quality:        2 files
  Low Quality (<0.4):    1 file

⚠️  Files Needing Attention:
  small-file.md (Quality: 0.20)
    ❌ Very small file
    💡 Consider removing or combining
```

### Chunking Statistics

```
CHUNKING STATISTICS
================================================================================
Documents processed: 10
Total chunks: 832
Small chunks filtered: 91

Chunks by method:
  recursive: 500 (60.1%)
  markdown_headers: 332 (39.9%)
```

### Cleaning Statistics

```
CONTENT CLEANING STATISTICS
================================================================================
Input chunks: 832
Output chunks: 741
Removal rate: 10.9%

Breakdown:
  Exact duplicates: 72
  Near duplicates: 11
  Boilerplate: 5
  Too small: 3
```

### Quality Metrics

```
QUALITY METRICS REPORT
================================================================================
📊 Overall Quality: Good (0.78/1.00)

📏 Chunk Size Statistics:
  Median Size: 587 characters

📈 Size Distribution:
   very_small:    8 ( 1.1%)
        small:  142 (19.2%)
       medium:  423 (57.1%)  ← Good
        large:  158 (21.3%)
   very_large:   10 ( 1.3%)

🎨 Content Diversity:
  Uniqueness: 100%
  Vocabulary: 42.34%
```

---

## Programmatic Usage

### Analysis Only

```python
from src.preprocessor import DocumentAnalyzer

analyzer = DocumentAnalyzer()
analysis = analyzer.analyze_file("documents/paper.pdf")

print(f"Quality: {analysis.quality_score}")
print(f"Issues: {analysis.issues}")
```

### Custom Pipeline

```python
from src.preprocessor import (
    DocumentAnalyzer,
    ChunkingStrategy,
    ContentCleaner,
    QualityMetrics
)

# 1. Analyze
analyzer = DocumentAnalyzer()
analysis = analyzer.analyze_file("doc.pdf")

# 2. Select chunking strategy
strategy = ChunkingStrategy()
config = strategy.select_config(
    structure_type=analysis.structure_type,
    file_size=analysis.file_size,
    language=analysis.language
)

# 3. Chunk
chunks = strategy.chunk_documents(documents, config)

# 4. Clean
cleaner = ContentCleaner()
clean_chunks = cleaner.clean_and_deduplicate(chunks)

# 5. Check quality
metrics = QualityMetrics()
results = metrics.calculate_metrics(clean_chunks)
metrics.print_report()
```

---

## Configuration

### Chunking Parameters

```python
from src.preprocessor import ChunkingConfig

config = ChunkingConfig(
    method=ChunkingMethod.RECURSIVE,
    chunk_size=1000,        # Target characters
    chunk_overlap=200,      # Overlap for context
    min_chunk_size=100,     # Filter tiny chunks
)
```

### Cleaning Parameters

```python
from src.preprocessor import ContentCleaner

cleaner = ContentCleaner(
    similarity_threshold=0.95,  # Near-duplicate threshold
    min_content_length=100      # Minimum chunk size
)
```

---

## Common Patterns

### Academic Papers

```bash
python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.3
```

Lower threshold because papers have complex structure.

### Blog Posts

```bash
python scripts/ingest/ingest_with_preprocessor.py --min-quality 0.6
```

Higher threshold for simple content.

### Mixed Content

```bash
python scripts/ingest/ingest_with_preprocessor.py
```

Use defaults and let analyzer adapt.

---

## Troubleshooting

### "Chunks too small"

```python
# Increase chunk size
config = ChunkingConfig(
    chunk_size=1500,
    min_chunk_size=200
)
```

### "Too many duplicates"

```python
# Lower similarity threshold
cleaner = ContentCleaner(
    similarity_threshold=0.90
)
```

### "Quality score < 0.5"

Common causes:
- Tiny test files
- Placeholder content
- Corrupted PDFs

Fix: Remove problematic files before ingestion.

### "Ollama 500 errors"

Reduce batch size in the script:
```python
batch_size = 50  # Down from 100
```

---

## Before/After Comparison

### Before (basic ingest.py)

```
Total chunks: 832
Duplicates: 91 (11%)
Median chunk: 38 chars ❌
Quality: Unknown
PCA: 99% in 1 component ❌
```

### After (ingest_with_preprocessor.py)

```
Total chunks: 741
Duplicates: 0 ✅
Median chunk: 587 chars ✅
Quality: 0.78 ✅
PCA: 20+ components ✅
```

---

## Related Documentation

- **[RAG Guide](rag-guide.md)** - Complete RAG system guide
- **[Writing Documentation](writing-docs.md)** - Create RAG-friendly content
- **[Quality Evaluation](quality-evaluation.md)** - Measure documentation quality
