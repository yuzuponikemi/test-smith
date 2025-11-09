# Document Preprocessor Quick Start

Get started with intelligent document preprocessing in 5 minutes!

## What This Does

The preprocessor automatically:
- ✅ Analyzes document quality
- ✅ Selects optimal chunking strategy per document
- ✅ Removes duplicates and boilerplate
- ✅ Filters tiny/useless chunks
- ✅ Calculates quality metrics
- ✅ Provides actionable recommendations

## Installation

Already installed! The preprocessor is part of this project.

## Basic Usage

### Option 1: Use the Full Pipeline (Recommended)

```bash
# Clean and ingest with intelligent preprocessing
python ingest_with_preprocessor.py
```

That's it! The preprocessor will:
1. Analyze all documents in `documents/`
2. Select best chunking strategy for each
3. Clean and deduplicate
4. Ingest to ChromaDB
5. Generate detailed reports

### Option 2: Analysis Only (No Ingestion)

```python
from src.preprocessor import DocumentAnalyzer

analyzer = DocumentAnalyzer()
analyses = analyzer.analyze_directory('documents')
analyzer.print_report()

# Check problematic files
problematic = analyzer.get_problematic_files(threshold=0.5)
for doc in problematic:
    print(f"{doc.filename}: {doc.issues}")
```

### Option 3: Custom Pipeline

```python
from src.preprocessor import (
    DocumentAnalyzer,
    ChunkingStrategy,
    ContentCleaner,
    QualityMetrics
)

# 1. Analyze documents
analyzer = DocumentAnalyzer()
analysis = analyzer.analyze_file("documents/paper.pdf")

# 2. Select chunking strategy
strategy = ChunkingStrategy()
config = strategy.select_config(
    structure_type=analysis.structure_type,
    file_size=analysis.file_size,
    language=analysis.language
)

# 3. Chunk documents
chunks = strategy.chunk_documents(documents, config)

# 4. Clean and deduplicate
cleaner = ContentCleaner()
clean_chunks = cleaner.clean_and_deduplicate(chunks)

# 5. Check quality
metrics = QualityMetrics()
results = metrics.calculate_metrics(clean_chunks)
metrics.print_report()
```

## Command-Line Options

```bash
# Set minimum quality threshold (skip low-quality files)
python ingest_with_preprocessor.py --min-quality 0.5

# Skip document analysis (faster, but less intelligent)
python ingest_with_preprocessor.py --skip-analysis

# Disable near-duplicate detection (faster, but more duplicates)
python ingest_with_preprocessor.py --disable-deduplication

# Disable boilerplate removal
python ingest_with_preprocessor.py --disable-boilerplate
```

## Understanding the Reports

### 1. Document Analysis Report

```
DOCUMENT ANALYSIS REPORT
================================================================================

Total Files Analyzed: 11

Quality Distribution:
  High Quality (≥0.7):   8 files
  Medium Quality (0.4-0.7): 2 files
  Low Quality (<0.4):    1 file
  Average Quality Score: 0.72

⚠️  Files Needing Attention (1):

  2025-09-11.md (Quality: 0.20)
    ❌ Very small file (57 bytes) - may create useless chunks
    💡 Recommendations:
       - Consider removing this file or combining with related content
```

**What to do:** Remove or fix files with quality < 0.5

### 2. Chunking Statistics

```
CHUNKING STATISTICS
================================================================================

Documents processed: 10
Total chunks created: 832
Small chunks filtered: 91

Chunks by method:
  recursive: 500 (60.1%)
  markdown_headers: 332 (39.9%)

Average chunks per document: 83.2
```

**What to look for:** Avg chunks per document should be reasonable (10-100)

### 3. Content Cleaning Statistics

```
CONTENT CLEANING STATISTICS
================================================================================

Input chunks: 832
Output chunks: 741
Total removed: 91
Removal rate: 10.9%

Removal breakdown:
  Exact duplicates: 72
  Near duplicates: 11
  Boilerplate: 5
  Too small: 3
```

**What to look for:**
- Removal rate 10-30% is normal
- >50% suggests a problem with source documents

### 4. Quality Metrics

```
QUALITY METRICS REPORT
================================================================================

📊 Overall Quality: Good (0.78/1.00)

📏 Chunk Size Statistics:
  Total Chunks: 741
  Mean Size: 652.3 characters
  Median Size: 587.0 characters

📈 Size Distribution:
   very_small:     8 ( 1.1%)
        small:   142 (19.2%)
       medium:   423 (57.1%)
        large:   158 (21.3%)
   very_large:    10 ( 1.3%)

🎨 Content Diversity:
  Uniqueness Ratio: 100.00%
  Vocabulary Diversity: 42.34%

💡 Recommendations:
  ✅ Data quality looks good! Ready for embedding.
```

**What to look for:**
- Quality score > 0.7 = good
- Median size 500-1000 = optimal
- Uniqueness > 95% = good
- Few very_small chunks

## Troubleshooting

### "Chunks are too small (median < 200)"

**Fix:**
```python
config = ChunkingConfig(
    chunk_size=1500,  # Increase from 1000
    min_chunk_size=200  # Filter more aggressively
)
```

### "Too many duplicates (>20% removal rate)"

**Causes:**
- Documents share templates (academic papers)
- Repeated headers/footers in PDFs
- Actually duplicate content

**Fix:**
```python
# More aggressive near-duplicate detection
cleaner = ContentCleaner(
    similarity_threshold=0.90  # Lower from 0.95
)
```

### "Quality score < 0.5"

**Common causes:**
1. Tiny test files in documents/
2. Placeholder files
3. Corrupted PDFs

**Fix:**
```bash
# Remove problematic files
rm documents/placeholder.txt
rm documents/test*.md

# Re-run
python ingest_with_preprocessor.py
```

### "Ollama 500 errors"

**Fix:** Use batch processing
```python
# In ingest_with_preprocessor.py, batching is automatic
# Default batch_size = 100

# If still failing, reduce batch size:
batch_size = 50  # Change in the code
```

## Comparing Before/After

### Before (using basic ingest.py)

```
Total chunks: 832
Duplicates: 91 (11%)
Median chunk: 38 chars ❌
Quality: Unknown
PCA: 99% in 1 component ❌
```

### After (using ingest_with_preprocessor.py)

```
Total chunks: 741
Duplicates: 0 (deduped) ✅
Median chunk: 587 chars ✅
Quality: 0.78 (Good) ✅
PCA: 20+ components for 95% ✅
```

## Next Steps

1. **Run the preprocessor:**
   ```bash
   python ingest_with_preprocessor.py
   ```

2. **Check the log file:**
   ```bash
   cat ingestion_preprocessed_*.log
   ```

3. **Review quality in notebook:**
   ```bash
   jupyter notebook chroma_explorer.ipynb
   # Run Section 2.2 - Embedding Quality Diagnostics
   # Run Section 3.0 - PCA Variance Analysis
   ```

4. **Test retrieval:**
   ```python
   # Query your database
   results = collection.query(
       query_texts=["What are the latest AI techniques?"],
       n_results=5
   )
   ```

5. **Read the full guide:**
   See `docs/RAG_DATA_PREPARATION_GUIDE.md` for comprehensive details

## Learn More

- **Full Guide:** `docs/RAG_DATA_PREPARATION_GUIDE.md`
- **Diagnostics:** `EMBEDDING_DIAGNOSTICS.md`
- **Code:** `src/preprocessor/` directory

## Common Patterns

### For Academic Papers

```python
python ingest_with_preprocessor.py --min-quality 0.3
```

Why: Papers have complex structure, some may score lower but are still valuable

### For Blog Posts

```python
python ingest_with_preprocessor.py --min-quality 0.6
```

Why: Simple content, expect higher quality scores

### For Mixed Content

```python
python ingest_with_preprocessor.py  # Use defaults
```

Why: Let the analyzer adapt per document

---

**Ready to go! Run `python ingest_with_preprocessor.py` and enjoy high-quality embeddings! 🚀**
