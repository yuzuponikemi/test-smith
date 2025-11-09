# RAG Data Preparation: The Complete Guide

**A comprehensive guide for learners on preparing high-quality data for Retrieval-Augmented Generation systems**

---

## Table of Contents

1. [Why Data Quality Matters in RAG](#why-data-quality-matters)
2. [Understanding the RAG Pipeline](#understanding-the-rag-pipeline)
3. [Document Preprocessing Fundamentals](#document-preprocessing-fundamentals)
4. [Chunking Strategies Deep Dive](#chunking-strategies-deep-dive)
5. [Embedding Quality](#embedding-quality)
6. [Common Pitfalls and Solutions](#common-pitfalls)
7. [Best Practices Checklist](#best-practices-checklist)
8. [Practical Examples](#practical-examples)

---

## Why Data Quality Matters

### The Foundation of RAG Systems

In Retrieval-Augmented Generation (RAG), your system is only as good as its data. Unlike traditional databases where exact matching works, vector databases rely on **semantic similarity**. Poor data quality leads to:

❌ **Bad retrieval** - Relevant information isn't found
❌ **Hallucinations** - LLM makes up information
❌ **Context pollution** - Irrelevant chunks waste context window
❌ **Poor user experience** - Wrong or incomplete answers

✅ **Good data quality leads to:**
- Accurate retrieval
- Relevant context
- Better LLM responses
- Faster queries
- Lower costs (less token usage)

### Real-World Impact

**Example from our diagnostic analysis:**

**Before preprocessing:**
```
- 832 chunks created
- 91 duplicates (11%)
- Median chunk size: 38 chars
- PCA variance: 99% in 1 component
- Result: All embeddings clustered, poor retrieval
```

**After preprocessing:**
```
- 741 unique chunks
- Median chunk size: ~600 chars
- PCA variance: distributed across 20+ components
- Result: Diverse embeddings, excellent retrieval
```

---

## Understanding the RAG Pipeline

### The Complete Flow

```
1. DOCUMENTS (PDF, Markdown, Text)
   ↓
2. LOADING (UnstructuredLoader, PyPDF, etc.)
   ↓
3. PREPROCESSING ← YOU ARE HERE
   ├── Quality Analysis
   ├── Content Cleaning
   └── Deduplication
   ↓
4. CHUNKING
   ├── Strategy Selection
   ├── Splitting
   └── Filtering
   ↓
5. EMBEDDING (nomic-embed-text, OpenAI, etc.)
   ↓
6. VECTOR DATABASE (ChromaDB, Pinecone, etc.)
   ↓
7. RETRIEVAL (Similarity search)
   ↓
8. GENERATION (LLM with context)
```

### Where Most Problems Occur

**70% of RAG issues come from steps 3-4 (Preprocessing & Chunking)**

Why? Because:
- Documents are messy (PDFs especially)
- One-size-fits-all chunking fails
- Duplicates create noise
- Small chunks have no context
- Large chunks waste tokens

---

## Document Preprocessing Fundamentals

### Step 1: Document Analysis

**Before processing, understand your documents:**

```python
from src.preprocessor import DocumentAnalyzer

analyzer = DocumentAnalyzer()
analysis = analyzer.analyze_file("documents/paper.pdf")

print(f"Quality Score: {analysis.quality_score}")
print(f"Issues: {analysis.issues}")
print(f"Recommendations: {analysis.recommendations}")
```

**What to check:**

1. **File Size**
   - Too small (< 200 bytes): Probably placeholder or test file
   - Too large (> 50MB): May cause memory issues

2. **Content Type**
   - Markdown: Look for header structure
   - PDF: Check for text vs. scanned images
   - Plain text: Verify encoding (UTF-8)

3. **Language Detection**
   - English: Standard chunking works
   - Japanese/Chinese: Need larger chunks (characters ≠ words)
   - Mixed: Use hybrid approach

4. **Structure Detection**
   - Headers/sections: Use semantic chunking
   - Flat text: Use fixed-size chunking
   - Code blocks: Preserve code structure

### Step 2: Content Cleaning

**Remove noise before chunking:**

```python
from src.preprocessor import ContentCleaner

cleaner = ContentCleaner(
    similarity_threshold=0.95,  # 95% similar = duplicate
    min_content_length=100      # Minimum 100 chars
)

clean_chunks = cleaner.clean_and_deduplicate(
    chunks,
    remove_near_duplicates=True,
    remove_boilerplate=True
)
```

**What gets removed:**

1. **Exact Duplicates**
   - Same text = same hash
   - Common in academic papers (repeated headers)

2. **Near Duplicates**
   - 95%+ similarity
   - Example: "0. 書誌情報" appearing in multiple files

3. **Boilerplate**
   - Text appearing in >20% of documents
   - Headers, footers, copyright notices

4. **Too-Small Chunks**
   - Less than 100 characters
   - Not enough semantic meaning

### Step 3: Deduplication Strategies

**Three levels of deduplication:**

#### Level 1: Exact Matching (Fast)
```python
seen_hashes = set()
for chunk in chunks:
    hash = md5(chunk.content).hexdigest()
    if hash not in seen_hashes:
        unique_chunks.append(chunk)
```

**When to use:** Always. Zero cost, high value.

#### Level 2: Near-Duplicate (Medium)
```python
similarity = SequenceMatcher(None, text1, text2).ratio()
if similarity < 0.95:
    unique_chunks.append(chunk)
```

**When to use:** Documents with templates (academic papers, reports).

**Cost:** O(n²) comparisons - use for <1000 chunks.

#### Level 3: Semantic Deduplication (Slow)
```python
# Compare embeddings
similarity = cosine_similarity(emb1, emb2)
if similarity < 0.98:
    unique_chunks.append(chunk)
```

**When to use:** Critical applications requiring maximum quality.

**Cost:** Requires embedding all chunks first.

---

## Chunking Strategies Deep Dive

### Why Chunking Matters

**The Goldilocks Problem:**

- **Too small** (< 200 chars): No context, poor retrieval
- **Too large** (> 2000 chars): Irrelevant info, wastes tokens
- **Just right** (500-1500 chars): Good context, relevant results

### Strategy 1: Fixed-Size Chunking

**How it works:**
```python
chunk_size = 1000
chunk_overlap = 200

# Split every 1000 chars, overlap 200
```

**Pros:**
- Simple, predictable
- Works for most documents
- Fast processing

**Cons:**
- Breaks mid-sentence
- Ignores document structure
- May split code/tables

**Best for:**
- Plain text
- Books, articles
- When you don't know document structure

**Example:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]  # Try these in order
)

chunks = text_splitter.split_documents(documents)
```

### Strategy 2: Semantic (Header-Based) Chunking

**How it works:**
```python
# Split by markdown headers
# Each section = one chunk
# Further split if section > chunk_size
```

**Pros:**
- Preserves meaning
- Natural boundaries
- Better context

**Cons:**
- Requires structured documents
- Sections may be too large/small
- More complex

**Best for:**
- Markdown documentation
- Technical docs with headers
- Academic papers with sections

**Example:**
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)

md_chunks = markdown_splitter.split_text(markdown_doc)
```

### Strategy 3: Hybrid Chunking

**How it works:**
```python
# 1. Split by headers (semantic)
# 2. Further split large sections (fixed-size)
# 3. Combine small sections
```

**Pros:**
- Best of both worlds
- Flexible sizing
- Maintains structure

**Cons:**
- Most complex
- Requires tuning
- Slower processing

**Best for:**
- Complex documents
- Mixed content types
- Production systems

**Example:**
```python
from src.preprocessor import ChunkingStrategy

strategy = ChunkingStrategy()

# Hybrid chunking for academic papers
chunks = strategy.chunk_documents(
    documents,
    config=ChunkingConfig(
        method=ChunkingMethod.HYBRID,
        chunk_size=1500,
        chunk_overlap=300,
        min_chunk_size=200
    )
)
```

### Chunk Size Guidelines by Language

**English:**
```
Minimum: 200 characters (~40 words)
Optimal: 500-1000 characters (~100-200 words)
Maximum: 1500 characters (~300 words)
```

**Japanese/Chinese:**
```
Minimum: 300 characters
Optimal: 600-1200 characters
Maximum: 2000 characters

Why larger? Each character carries more meaning than English letters.
```

**Mixed Languages:**
```
Use Japanese/Chinese settings (larger chunks)
Overlap: 250-300 characters
```

### Overlap Strategy

**Why overlap matters:**

```
Without overlap:
[Chunk 1: "...about cats."] [Chunk 2: "Dogs are..."]
                          ↑ Information at boundary lost

With overlap:
[Chunk 1: "...about cats. Dogs are..."]
              [Chunk 2: "...cats. Dogs are different..."]
                          ↑ Boundary information preserved
```

**Overlap guidelines:**

- **General rule:** 15-20% of chunk size
- **Chunk 1000 → Overlap 200**
- **Chunk 1500 → Overlap 300**

**Too much overlap:** Waste (duplicate embeddings)
**Too little overlap:** Context loss at boundaries

### Document-Specific Strategies

#### Academic Papers (PDF)
```python
config = ChunkingConfig(
    method=ChunkingMethod.RECURSIVE,
    chunk_size=1500,
    chunk_overlap=300,
    min_chunk_size=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**Why:** Papers have dense information, need more context.

#### Technical Documentation (Markdown)
```python
config = ChunkingConfig(
    method=ChunkingMethod.MARKDOWN_HEADERS,
    chunk_size=1000,
    chunk_overlap=200,
    headers_to_split_on=[("#", "h1"), ("##", "h2")]
)
```

**Why:** Clear section boundaries, preserve structure.

#### Code Files
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Language-specific separators
python_splitter = RecursiveCharacterTextSplitter.from_language(
    language="python",
    chunk_size=800,
    chunk_overlap=100
)
```

**Why:** Preserve class/function boundaries.

#### Chat Logs
```python
config = ChunkingConfig(
    method=ChunkingMethod.RECURSIVE,
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ": ", " "]  # Split on message boundaries
)
```

**Why:** Each message is a unit of meaning.

---

## Embedding Quality

### What Makes Good Embeddings

**Good embeddings capture:**
- Semantic meaning
- Context
- Relationships
- Nuance

**Signs of good embeddings:**
- Different topics → Different clusters
- Similar meaning → Close in vector space
- PCA needs 20+ components for 95% variance

**Signs of bad embeddings:**
- Everything clusters together
- Random distribution
- PCA: 1-2 components for 99% variance

### Embedding Models Comparison

| Model | Dimensions | Best For | Speed |
|-------|-----------|----------|-------|
| nomic-embed-text | 768 | General purpose, local | Fast |
| OpenAI text-embedding-3-small | 1536 | Production, quality | Medium |
| OpenAI text-embedding-3-large | 3072 | Max quality | Slow |
| all-MiniLM-L6-v2 | 384 | Fast retrieval | Very fast |

**For learning/prototyping:** nomic-embed-text (free, local, good quality)
**For production:** OpenAI text-embedding-3-small (best quality/cost ratio)

### Testing Embedding Quality

```python
from sklearn.metrics.pairwise import cosine_similarity

# Test with different texts
emb1 = embeddings.embed_query("The sky is blue")
emb2 = embeddings.embed_query("Python programming")
emb3 = embeddings.embed_query("The ocean is blue")

sim_12 = cosine_similarity([emb1], [emb2])[0][0]  # Should be low (~0.3)
sim_13 = cosine_similarity([emb1], [emb3])[0][0]  # Should be high (~0.7)

print(f"Different topics: {sim_12:.2f}")  # < 0.5 = good
print(f"Similar meaning: {sim_13:.2f}")   # > 0.6 = good
```

**Red flags:**
- All similarities > 0.95 → Model not working
- All similarities random → Wrong model or corrupted

---

## Common Pitfalls

### Pitfall 1: "My PCA shows 99% variance in 1 component"

**Symptom:** All embeddings cluster together.

**Causes:**
1. ✅ **Duplicate chunks** (most common)
2. ✅ **Tiny chunks** (no semantic meaning)
3. ❌ Embedding model not working
4. ✅ Documents too similar

**Solution:**
```python
# Enable aggressive deduplication
cleaner = ContentCleaner(
    similarity_threshold=0.90,  # Lower threshold
    min_content_length=150      # Larger minimum
)

# Check chunk sizes
print(f"Median chunk: {np.median([len(c.page_content) for c in chunks])}")
# Should be > 200
```

### Pitfall 2: "Chunks are too small"

**Symptom:** Median chunk size < 200 characters.

**Causes:**
1. UnstructuredLoader splits aggressively
2. Markdown with many short sections
3. min_chunk_size not set

**Solution:**
```python
# Filter small chunks
chunks = [c for c in chunks if len(c.page_content) >= 150]

# Or adjust chunking
config.min_chunk_size = 200
```

### Pitfall 3: "Retrieval returns irrelevant results"

**Symptom:** Search for "Python" returns "Java" content.

**Causes:**
1. Chunks too large (context pollution)
2. Chunks too small (no context)
3. Poor query formulation

**Solution:**
```python
# Test different chunk sizes
for size in [500, 1000, 1500]:
    chunks = split_with_size(docs, size)
    test_retrieval(chunks, "Python tutorials")
    # Measure relevance
```

### Pitfall 4: "Ollama embedding errors"

**Symptom:** `500 Internal Server Error` from Ollama.

**Causes:**
1. Batch too large
2. Memory issues
3. Ollama crashed

**Solution:**
```python
# Use smaller batches
batch_size = 50
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    vectorstore.add_documents(batch)
```

### Pitfall 5: "Japanese text creates tiny chunks"

**Symptom:** Japanese documents → 20-char chunks.

**Cause:** Character vs. word differences.

**Solution:**
```python
# Increase chunk size for Japanese
if language == 'japanese':
    chunk_size = int(base_chunk_size * 1.5)
    min_chunk_size = 150
```

---

## Best Practices Checklist

### Before Ingestion

- [ ] Review source documents (remove test/placeholder files)
- [ ] Check file formats (PDFs: text vs scanned)
- [ ] Verify encodings (UTF-8 for all text files)
- [ ] Estimate total size (avoid >10GB without batching)

### During Preprocessing

- [ ] Run document analysis first
- [ ] Remove files with quality score < 0.5
- [ ] Enable deduplication (exact + near-duplicate)
- [ ] Filter chunks < 100 characters
- [ ] Use appropriate chunking strategy per document type
- [ ] Set overlap to 15-20% of chunk size

### After Ingestion

- [ ] Check quality metrics (quality score > 0.7)
- [ ] Verify chunk size distribution (median 500-1000)
- [ ] Test PCA (should need 20+ components for 95%)
- [ ] Test retrieval with sample queries
- [ ] Monitor duplicate rate (should be < 5%)

### Production Checklist

- [ ] Version your preprocessing pipeline
- [ ] Log all settings (chunk size, overlap, model)
- [ ] Monitor embedding quality metrics
- [ ] Set up alerts for quality degradation
- [ ] Implement A/B testing for chunking strategies
- [ ] Regular re-ingestion (documents change)

---

## Practical Examples

### Example 1: Simple Blog Posts

**Scenario:** Personal blog, markdown files, English, 500-2000 words each.

```python
from src.preprocessor import ChunkingStrategy, ChunkingConfig, ChunkingMethod

config = ChunkingConfig(
    method=ChunkingMethod.MARKDOWN_HEADERS,
    chunk_size=1000,
    chunk_overlap=200,
    min_chunk_size=150,
    headers_to_split_on=[("##", "h2")]  # Split by section
)

strategy = ChunkingStrategy()
chunks = strategy.chunk_documents(documents, config)
```

**Why this works:**
- Blog posts have clear sections
- Moderate length
- Header-based preserves topic boundaries

### Example 2: Academic Papers (Mixed Languages)

**Scenario:** Research papers, PDF, English + Japanese, 10-30 pages.

```python
config = ChunkingConfig(
    method=ChunkingMethod.RECURSIVE,
    chunk_size=1500,  # Larger for academic content
    chunk_overlap=300,
    min_chunk_size=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# Enable aggressive cleaning
cleaner = ContentCleaner(
    similarity_threshold=0.92,  # Catch bibliography duplicates
    min_content_length=200
)

chunks = strategy.chunk_documents(documents, config)
clean_chunks = cleaner.clean_and_deduplicate(
    chunks,
    remove_near_duplicates=True,
    remove_boilerplate=True  # Remove repeated headers
)
```

**Why this works:**
- Academic content needs more context
- PDFs have repeated elements (headers/footers)
- Bibliography sections create duplicates

### Example 3: Code Documentation

**Scenario:** Python code + markdown docs, structured, lots of code blocks.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# For code files
code_splitter = RecursiveCharacterTextSplitter.from_language(
    language="python",
    chunk_size=800,
    chunk_overlap=100
)

# For markdown docs
doc_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["```\n", "\n\n", "\n", " "]  # Preserve code blocks
)

# Process separately
code_chunks = code_splitter.split_documents(code_docs)
doc_chunks = doc_splitter.split_documents(text_docs)

all_chunks = code_chunks + doc_chunks
```

**Why this works:**
- Code has different structure than prose
- Code blocks should not be split
- Separate processing for separate content

### Example 4: Customer Support Tickets

**Scenario:** Support tickets, short text, Q&A format, lots of duplicates.

```python
config = ChunkingConfig(
    method=ChunkingMethod.RECURSIVE,
    chunk_size=600,  # Shorter for Q&A
    chunk_overlap=100,
    min_chunk_size=100,
    separators=["\n\nQ:", "\nQ:", "\n\n", "\n"]
)

# Aggressive deduplication (many similar questions)
cleaner = ContentCleaner(
    similarity_threshold=0.88,  # Catch similar questions
    min_content_length=50
)

clean_chunks = cleaner.clean_and_deduplicate(
    chunks,
    remove_near_duplicates=True
)
```

**Why this works:**
- Q&A pairs are natural chunks
- Many similar questions (dedup aggressively)
- Shorter chunks OK (focused questions)

---

## Advanced Topics

### Dynamic Chunk Sizing

**Adapt chunk size based on content:**

```python
def adaptive_chunk_size(content_length: int, complexity: str) -> int:
    """
    Adjust chunk size based on document characteristics
    """
    base_size = 1000

    # Longer documents → larger chunks (more context)
    if content_length > 50000:
        base_size = 1500
    elif content_length < 5000:
        base_size = 800

    # Complex content → larger chunks
    if complexity == 'high':  # Technical, dense
        base_size = int(base_size * 1.2)
    elif complexity == 'low':  # Simple, conversational
        base_size = int(base_size * 0.8)

    return base_size
```

### Metadata Enrichment

**Add context to chunks:**

```python
for chunk in chunks:
    chunk.metadata.update({
        'source_type': 'academic_paper',
        'year': 2024,
        'section': extract_section(chunk),
        'keywords': extract_keywords(chunk),
        'chunk_position': index / len(chunks)  # Relative position
    })
```

**Benefits:**
- Filter by metadata (e.g., year > 2020)
- Re-rank by relevance
- Better attribution

### Quality Monitoring

**Track metrics over time:**

```python
from src.preprocessor import QualityMetrics

metrics = QualityMetrics()
results = metrics.calculate_metrics(chunks)

# Log for monitoring
logger.info(f"Quality score: {results['quality_score']}")
logger.info(f"Median size: {results['median_chunk_size']}")
logger.info(f"Uniqueness: {results['uniqueness_ratio']}")

# Alert if degraded
if results['quality_score'] < 0.6:
    alert("Data quality degraded!")
```

---

## Summary

### Key Takeaways

1. **Data quality determines RAG quality** - Spend time on preprocessing
2. **One size doesn't fit all** - Different documents need different strategies
3. **Deduplication is critical** - 10-30% duplicates are common
4. **Chunk size matters** - 500-1500 chars is usually right
5. **Test and measure** - Use quality metrics to validate

### Your Workflow

```
1. Analyze documents → Remove low-quality files
2. Select strategy → Match document type
3. Chunk intelligently → Preserve meaning
4. Clean & deduplicate → Remove noise
5. Measure quality → Validate results
6. Test retrieval → Ensure it works
7. Monitor → Watch for degradation
```

### Next Steps

- [ ] Run preprocessor on your documents
- [ ] Review quality metrics
- [ ] Test different chunking strategies
- [ ] Compare retrieval quality
- [ ] Iterate and improve

**Remember:** RAG is iterative. Start simple, measure, improve. Your first preprocessing pipeline won't be perfect, and that's OK!

---

## Resources

### Tools in This Repository

- `src/preprocessor/document_analyzer.py` - Analyze document quality
- `src/preprocessor/chunking_strategy.py` - Smart chunking selection
- `src/preprocessor/content_cleaner.py` - Deduplication and cleaning
- `src/preprocessor/quality_metrics.py` - Quality measurement
- `ingest_with_preprocessor.py` - Full pipeline implementation

### Further Reading

- LangChain Text Splitters: https://python.langchain.com/docs/modules/data_connection/document_transformers/
- ChromaDB Documentation: https://docs.trychroma.com/
- Vector Database Concepts: https://www.pinecone.io/learn/vector-database/
- RAG Best Practices: https://docs.llamaindex.ai/en/stable/optimizing/production_rag/

### Getting Help

If you encounter issues:
1. Check `EMBEDDING_DIAGNOSTICS.md` for troubleshooting
2. Run quality analysis: `python -c "from src.preprocessor import DocumentAnalyzer; analyzer = DocumentAnalyzer(); analyzer.analyze_directory('documents'); analyzer.print_report()"`
3. Review logs in `ingestion_preprocessed_*.log`
4. Compare before/after metrics

---

**Happy preprocessing! 🚀**
