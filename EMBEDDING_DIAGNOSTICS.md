# Embedding Quality Diagnostics Guide

This guide explains how to use the diagnostic tools to identify and fix embedding issues.

## 🚨 Problem Symptoms

Your current symptoms indicate a serious embedding issue:
- **PCA variance**: Only 1 component needed for 99% variance (should need 20-30+)
- **Visualization**: All dots clustered in one spot (should be spread out)
- **Similarity**: Documents are too similar (embeddings likely identical)

## 📋 Diagnostic Tools

### 1. Enhanced Ingestion Script (`ingest_diagnostic.py`)

**Features:**
- **Real-time embedding quality checks** - Tests embeddings as they're generated
- **Chunking validation** - Ensures documents are split correctly
- **Duplicate detection** - Identifies identical chunks
- **Similarity analysis** - Compares consecutive chunks
- **Detailed logging** - Everything is saved to a timestamped log file
- **Pre-flight model test** - Validates Ollama is working before processing

**What it checks:**
1. ✅ Ollama connectivity
2. ✅ Embedding model functionality
3. ✅ Document loading and parsing
4. ✅ Chunk size and overlap
5. ✅ Embedding dimension and values
6. ✅ Embedding variance and diversity
7. ✅ Pairwise similarities

### 2. Notebook Diagnostics (Section 2.2)

After ingestion, the notebook provides:
- Duplicate embedding detection
- Diversity analysis across dimensions
- Pairwise similarity distributions
- Visual diagnostics (histograms, variance plots)

## 🔧 How to Use

### Quick Start

```bash
# Clean and re-ingest with diagnostics
./clean_and_reingest.sh
```

This script will:
1. Backup existing ChromaDB
2. Check Ollama is running
3. Verify the embedding model
4. Run diagnostic ingestion
5. Generate detailed logs

### Manual Process

If you prefer step-by-step:

```bash
# 1. Backup current database (optional)
mv chroma_db chroma_db_backup_$(date +%Y%m%d_%H%M%S)

# 2. Verify Ollama is running
ollama list
# Should show nomic-embed-text

# 3. Test the model manually
ollama run nomic-embed-text
# Type some text and verify it responds

# 4. Activate virtual environment
source .venv/bin/activate

# 5. Run diagnostic ingestion
python3 ingest_diagnostic.py
```

## 📊 Understanding the Output

### Healthy Embeddings

```
✓ Embedding model test PASSED
  - Test similarity: 0.6234 (should be < 0.9)
  - Std dev: 0.0234, 0.0189 (should be > 0.01)

EMBEDDING QUALITY REPORT
  Mean of stds: 0.023456 (should be > 0.01)
  Mean similarity: 0.7234 (should be 0.3 - 0.8)
```

### Problematic Embeddings

```
⚠️ WARNING: Very low std deviation (0.003421)
⚠️ WARNING: Very high similarity for different texts!
⚠️ WARNING: 45/50 pairs have >0.95 similarity

🚨 CRITICAL: Overall std deviation is very low
```

## 🔍 Common Issues and Solutions

### Issue 1: "Embedding model test FAILED"

**Symptoms:**
- Test similarity > 0.95
- Very low std deviation (< 0.01)
- Empty or invalid embeddings

**Solutions:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Re-pull the model
ollama pull nomic-embed-text

# Test manually
python3 << 'EOF'
from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")
emb = embeddings.embed_query("test")
print(f"Dimension: {len(emb)}")
print(f"Sample: {emb[:5]}")
EOF
```

### Issue 2: "High duplicate rate"

**Symptoms:**
- Many identical chunks detected
- Duplicate hash warnings in logs

**Solutions:**
- Check if source documents contain repetitive content
- Verify chunk_overlap isn't too high (200 is reasonable)
- Review the sample chunks in the log to see what's duplicated

### Issue 3: "Suspiciously high average similarity"

**Symptoms:**
- Mean similarity > 0.95
- All chunks from different documents very similar

**Solutions:**
- Verify documents are actually different (check file contents)
- Check if all documents are about the same topic (expected to be similar)
- Look at "Dimension variance" plot - should have variation
- Review embedding sample values in log - should differ between chunks

### Issue 4: "Chunks too large/small"

**Symptoms:**
- Average chunk size >> 1000 chars
- Or chunks are tiny (< 100 chars)

**Solutions:**
- Check document format (PDF, Markdown, etc.)
- Verify UnstructuredLoader is parsing correctly
- Review sample chunks in log file
- Adjust CHUNK_SIZE and CHUNK_OVERLAP if needed

## 📈 Analyzing the Log File

The log file contains step-by-step processing:

```
Step 1: Loading document...
✓ Loaded 1 document(s)
  Total characters: 12543
  Content preview: The Future of AI in Medicine...

Step 2: Filtering metadata...
✓ Filtered 1 document(s)

Step 3: Splitting into chunks (size=1000, overlap=200)...
✓ Created 15 chunks
  Unique chunks: 15
  Duplicates: 0
  Avg chunk size: 987.3 chars

  Chunk 0 (1024 chars):
    The Future of AI in Medicine...

Step 4: Generating sample embeddings...
  Generating embedding for chunk 0...
    Dimension: 768
    Mean: 0.023456, Std: 0.034521
    Sample values: [0.034, -0.012, 0.056, -0.023, 0.001]

  Generating embedding for chunk 1...
    Dimension: 768
    Mean: 0.019234, Std: 0.031245
    Sample values: [0.029, -0.008, 0.043, -0.019, 0.003]
    Similarity with previous chunk: 0.7834
```

**What to check:**
- ✅ All documents load successfully
- ✅ Chunk counts match expectations
- ✅ Chunk sizes are around 1000 chars
- ✅ Embeddings have dimension 768 (for nomic-embed-text)
- ✅ Embedding std > 0.01
- ✅ Consecutive chunk similarity 0.6 - 0.9 (related content)
- ✅ Cross-document similarity < 0.9 (different content)

## 🎯 After Re-ingestion

1. **Check the log file** for any errors or warnings
   ```bash
   cat ingestion_diagnostic_*.log | grep -E "(WARNING|ERROR|CRITICAL)"
   ```

2. **Run the notebook** and go to Section 2.2
   - Should see improved diversity
   - PCA should need 20+ components for 95% variance
   - Similarity distribution should be spread out

3. **Review visualizations**
   - Dots should be spread across the space
   - Different sources should form distinct clusters
   - Points should not all overlap

## 🆘 Still Having Issues?

If problems persist after re-ingestion:

1. **Try a minimal test:**
   ```bash
   # Create test documents
   echo "The quick brown fox jumps over the lazy dog." > documents/test1.txt
   echo "Python is a popular programming language." > documents/test2.txt
   echo "The stock market went up today." > documents/test3.txt

   # Move other documents temporarily
   mkdir documents_backup
   mv documents/*.{md,pdf} documents_backup/ 2>/dev/null || true

   # Re-run ingestion with just test files
   python3 ingest_diagnostic.py
   ```

2. **Check Ollama version:**
   ```bash
   ollama --version
   # Update if old: brew upgrade ollama (macOS) or download from ollama.ai
   ```

3. **Try a different model:**
   ```python
   # In ingest_diagnostic.py, change:
   EMBEDDING_MODEL = "all-minilm"  # Smaller, faster model
   ```

4. **Check system resources:**
   - Ollama needs ~4GB RAM for nomic-embed-text
   - Check Activity Monitor (macOS) or htop (Linux)

## 📝 Summary

**Before you run:**
- ✅ Ollama is running (`ollama list`)
- ✅ Model is installed (`nomic-embed-text` shown)
- ✅ Virtual environment is activated

**What to expect:**
- Detailed logging for every step
- Quality checks on embeddings
- Similarity analysis between chunks
- Final diagnostic reports
- Timestamped log file for review

**Success indicators:**
- ✅ "Embedding model test PASSED"
- ✅ Std deviation > 0.01
- ✅ Mean similarity 0.3 - 0.8
- ✅ PCA needs 20+ components for 95% variance
- ✅ Visualization shows spread-out clusters
