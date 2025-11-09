# Document Design Evaluation Guide

## Reproducible Metrics for RAG-Friendly Documentation

This guide provides objective, reproducible metrics to evaluate whether your documentation is well-designed for RAG (Retrieval Augmented Generation) systems.

---

## Table of Contents

1. [Evaluation Philosophy](#evaluation-philosophy)
2. [Automated Metrics from Ingestion](#automated-metrics-from-ingestion)
3. [Manual Content Evaluation](#manual-content-evaluation)
4. [Scoring System](#scoring-system)
5. [Evaluation Workflow](#evaluation-workflow)
6. [Example Evaluations](#example-evaluations)
7. [Continuous Improvement Process](#continuous-improvement-process)

---

## Evaluation Philosophy

### What We're Measuring

**Good documentation for RAG should produce:**
- Self-contained chunks that make sense independently
- Consistent terminology across documents
- Appropriate chunk sizes for semantic meaning
- Low duplication rate
- High semantic diversity

### Two-Level Evaluation

1. **Automated Metrics** - Calculated from ingestion pipeline
2. **Manual Quality Assessment** - Human review of content structure

Both are necessary for comprehensive evaluation.

---

## Automated Metrics from Ingestion

Run the preprocessor to get these metrics:

```bash
python ingest_with_preprocessor.py
```

### Metric 1: Chunk Size Distribution

**Target Distribution:**
```
very_small (<100 chars):    < 5% of chunks
small (100-500 chars):      15-25% of chunks
medium (500-1000 chars):    50-60% of chunks ← IDEAL ZONE
large (1000-1500 chars):    15-25% of chunks
very_large (>1500 chars):   < 5% of chunks
```

**Scoring:**
- ✅ **Excellent**: 55-65% in medium range, <5% very small
- ⚠️ **Good**: 45-70% in medium range, <10% very small
- ❌ **Poor**: <40% in medium range, or >15% very small

**Why it matters:** Medium chunks contain enough information to be meaningful but aren't overwhelming.

**To check:**
Look for "Size Distribution" in the ingestion log.

### Metric 2: Median Chunk Size

**Target: 500-800 characters**

**Scoring:**
- ✅ **Excellent**: 500-800 chars
- ⚠️ **Good**: 400-1000 chars
- ⚠️ **Needs Improvement**: 200-400 or 1000-1500 chars
- ❌ **Poor**: <200 or >1500 chars

**Why it matters:** Median shows the typical chunk size. If it's too small, sections lack context. If too large, chunks are unfocused.

**To check:**
Look for "Median Size" under "Chunk Size Statistics" in the log.

### Metric 3: Duplication Rate

**Exact + Near Duplicates / Total Chunks**

**Target: <5% duplication**

**Scoring:**
- ✅ **Excellent**: <5% duplicates
- ⚠️ **Good**: 5-10% duplicates
- ⚠️ **Needs Improvement**: 10-20% duplicates
- ❌ **Poor**: >20% duplicates

**Why it matters:** High duplication suggests:
- Repeated boilerplate (headers, footers)
- Copy-pasted sections
- Template content in multiple docs

**To check:**
Look for "Duplicates" count per file in the processing log.

**Common causes of duplication:**
- Repeated "References" sections
- Same bibliography format in all docs
- Copy-pasted disclaimers
- Template headers like "0. 書誌情報 (Bibliographic Information)"

### Metric 4: Quality Score

**Target: >0.7 (Good)**

**Scoring:**
- ✅ **Excellent**: 0.9+
- ✅ **Good**: 0.75-0.89
- ⚠️ **Fair**: 0.6-0.74
- ⚠️ **Poor**: 0.4-0.59
- ❌ **Very Poor**: <0.4

**Why it matters:** Composite score based on chunk size appropriateness, uniqueness ratio, and vocabulary diversity.

**To check:**
Look for "Overall quality" in the Quality Metrics Report.

### Metric 5: Vocabulary Diversity

**Unique words / Total words**

**Target: 25-50%**

**Scoring:**
- ✅ **Excellent**: 35-50% diversity
- ⚠️ **Good**: 25-35% diversity
- ⚠️ **Needs Improvement**: 15-25% diversity
- ❌ **Poor**: <15% diversity

**Why it matters:** Low diversity suggests:
- Repetitive content
- Over-use of same terms
- Lack of varied examples

**To check:**
Look for "Vocabulary Diversity" in Quality Metrics Report.

### Metric 6: Uniqueness Ratio

**Unique chunks / Total chunks**

**Target: >95%**

**Scoring:**
- ✅ **Excellent**: >95% unique
- ⚠️ **Good**: 90-95% unique
- ⚠️ **Needs Improvement**: 80-90% unique
- ❌ **Poor**: <80% unique

**Why it matters:** Different from duplication rate - this measures truly distinct content.

**To check:**
Look for "Uniqueness Ratio" in Quality Metrics Report.

### Metric 7: PCA Variance Components

**Number of components needed for 95% variance**

**Target: 20-40 components**

**Scoring:**
- ✅ **Excellent**: 25-40 components
- ⚠️ **Good**: 15-25 or 40-60 components
- ⚠️ **Needs Improvement**: 10-15 or 60-80 components
- ❌ **Poor**: <10 or >80 components

**Why it matters:**
- Too few (<15): Content is too similar, lacks diversity
- Too many (>60): Content is too scattered, lacks coherence

**To check:**
Run Section 3.0 in chroma_explorer.ipynb after ingestion.

---

## Manual Content Evaluation

Use these checklists to manually evaluate document quality.

### Evaluation Checklist 1: Section Independence

**Randomly select 10 sections** from your documentation.

For each section, score:

1. **Can this section be understood without reading other sections?**
   - 2 points: Fully self-contained
   - 1 point: Mostly clear but missing some context
   - 0 points: Requires reading other sections

2. **Does the section mention the main topic explicitly?**
   - 2 points: Topic mentioned in header AND content
   - 1 point: Topic mentioned in content only
   - 0 points: Topic not mentioned (relies on document title)

3. **Is the section adequately detailed?**
   - 2 points: 500+ characters with complete explanation
   - 1 point: 200-500 characters with basic info
   - 0 points: <200 characters or just a link

**Section Independence Score: (Total points / 60) × 100**

- ✅ **Excellent**: 85-100%
- ⚠️ **Good**: 70-84%
- ⚠️ **Needs Improvement**: 50-69%
- ❌ **Poor**: <50%

### Evaluation Checklist 2: Term Consistency

**Create a term frequency table:**

1. Pick 5 key concepts in your documentation
2. List all terms used to refer to each concept
3. Count occurrences of each term

**Example:**

| Concept | Terms Used | Primary Term % |
|---------|------------|----------------|
| Database | "database" (45), "DB" (12), "data store" (3) | 75% |
| Configuration | "configuration" (30), "config" (25), "settings" (10) | 46% |
| Document | "document" (50), "doc" (8), "file" (15), "resource" (7) | 63% |

**Consistency Score:**
Average the "Primary Term %" for all concepts.

- ✅ **Excellent**: >80% (one term dominates)
- ⚠️ **Good**: 60-80%
- ⚠️ **Needs Improvement**: 40-60%
- ❌ **Poor**: <40% (terms used randomly)

### Evaluation Checklist 3: Header Descriptiveness

**Analyze all H2 and H3 headers** in your documentation.

Count headers in each category:

1. **Generic headers** (e.g., "Overview", "Introduction", "Details", "Step 1")
2. **Topic-specific headers** (e.g., "PostgreSQL Installation", "Database Configuration")
3. **Fully descriptive headers** (e.g., "Installing PostgreSQL on Ubuntu", "Configuring PostgreSQL Connection Settings")

**Descriptiveness Score:**

```
Score = (Fully Descriptive × 2 + Topic-Specific × 1) / (Total Headers × 2) × 100
```

- ✅ **Excellent**: >80% (mostly fully descriptive)
- ⚠️ **Good**: 60-80%
- ⚠️ **Needs Improvement**: 40-60%
- ❌ **Poor**: <40% (mostly generic headers)

### Evaluation Checklist 4: Acronym Definition

**Find all acronyms** in your documentation.

For each acronym, check:
- ✅ Defined on first use with "Full Term (Acronym)" pattern
- ⚠️ Defined but not on first use
- ❌ Never defined

**Acronym Score:**

```
Score = (Defined on first use / Total unique acronyms) × 100
```

- ✅ **Excellent**: 100% (all defined on first use)
- ⚠️ **Good**: 80-99%
- ⚠️ **Needs Improvement**: 50-79%
- ❌ **Poor**: <50%

### Evaluation Checklist 5: Cross-Reference Quality

**Find 10 cross-references** (links or "see section X" statements).

For each reference, score:

1. **Does the reference include a description of the linked content?**
   - 2 points: Clear description of what's being referenced
   - 1 point: Vague description
   - 0 points: No description (e.g., "see above")

2. **Would the sentence make sense without the link?**
   - 2 points: Provides value even without following the link
   - 1 point: Some context but incomplete
   - 0 points: Only "Click here" or "See section X"

**Cross-Reference Score: (Total points / 40) × 100**

- ✅ **Excellent**: 85-100%
- ⚠️ **Good**: 70-84%
- ⚠️ **Needs Improvement**: 50-69%
- ❌ **Poor**: <50%

---

## Scoring System

### Overall Document Design Score

Calculate weighted average:

```
Overall Score =
  (Chunk Size Distribution × 0.15) +
  (Median Chunk Size × 0.10) +
  (Duplication Rate × 0.15) +
  (Quality Score × 0.15) +
  (Vocabulary Diversity × 0.10) +
  (Section Independence × 0.15) +
  (Term Consistency × 0.10) +
  (Header Descriptiveness × 0.10)
```

**Grade Scale:**

| Score | Grade | Action Required |
|-------|-------|-----------------|
| 90-100 | A+ | Excellent - Maintain quality |
| 80-89 | A | Very good - Minor improvements |
| 70-79 | B | Good - Review specific weak areas |
| 60-69 | C | Needs improvement - Restructure sections |
| 50-59 | D | Poor - Major revision needed |
| <50 | F | Very poor - Complete rewrite recommended |

---

## Evaluation Workflow

### Step 1: Run Automated Evaluation

```bash
# Clean database
./clean_and_reingest.sh

# The script will output automated metrics
```

**Save the log file:**
```bash
cp ingestion_preprocessed_*.log evaluation_$(date +%Y%m%d).log
```

### Step 2: Extract Automated Metrics

From the log file, record:

| Metric | Target | Your Score | Status |
|--------|--------|------------|--------|
| Median Chunk Size | 500-800 | ___ chars | ___ |
| Medium % | 50-60% | ___ % | ___ |
| Very Small % | <5% | ___ % | ___ |
| Duplication Rate | <5% | ___ % | ___ |
| Quality Score | >0.7 | ___ | ___ |
| Vocabulary Diversity | 25-50% | ___ % | ___ |
| Uniqueness Ratio | >95% | ___ % | ___ |

### Step 3: Run PCA Analysis

```bash
jupyter notebook chroma_explorer.ipynb
```

Run Section 3.0 and record:
- Components for 95% variance: ___

### Step 4: Manual Evaluation

Complete the 5 checklists above:

| Checklist | Score | Status |
|-----------|-------|--------|
| Section Independence | ___ % | ___ |
| Term Consistency | ___ % | ___ |
| Header Descriptiveness | ___ % | ___ |
| Acronym Definition | ___ % | ___ |
| Cross-Reference Quality | ___ % | ___ |

### Step 5: Calculate Overall Score

Plug all scores into the formula above.

### Step 6: Identify Weak Areas

For each metric scoring <70%, create action items:

**Example:**
- Duplication Rate: 15% (Poor) → Action: Remove repeated bibliography sections
- Section Independence: 55% (Needs Improvement) → Action: Add topic names to headers

### Step 7: Document Results

Create an evaluation report:

```markdown
# Documentation Evaluation Report - [Date]

## Overall Score: [Score] ([Grade])

## Automated Metrics
- Median Chunk Size: [X] chars ([Status])
- Duplication Rate: [X]% ([Status])
- Quality Score: [X] ([Status])
[etc...]

## Manual Evaluation
- Section Independence: [X]% ([Status])
- Term Consistency: [X]% ([Status])
[etc...]

## Action Items
1. [Highest priority item]
2. [Second priority item]
3. [etc...]

## Next Evaluation Date: [Date + 1 month]
```

---

## Example Evaluations

### Example 1: Poor Documentation

**Automated Metrics:**
- Median chunk size: 45 chars ❌
- Duplication rate: 18% ❌
- Quality score: 0.35 ❌
- Vocabulary diversity: 18% ⚠️
- Components for 95% variance: 8 ❌

**Manual Evaluation:**
- Section independence: 40% ❌
- Term consistency: 35% ❌
- Header descriptiveness: 25% ❌

**Overall Score: 38 (F - Very Poor)**

**Diagnosis:**
- Chunks too small (45 chars) - sections lack detail
- High duplication - copy-pasted boilerplate
- Low PCA components - content too similar
- Generic headers - poor discoverability

**Action Items:**
1. Expand sections to 500+ chars each
2. Remove duplicated bibliography sections
3. Add topic names to all headers
4. Establish consistent terminology

---

### Example 2: Excellent Documentation

**Automated Metrics:**
- Median chunk size: 650 chars ✅
- Duplication rate: 3% ✅
- Quality score: 0.82 ✅
- Vocabulary diversity: 38% ✅
- Components for 95% variance: 32 ✅

**Manual Evaluation:**
- Section independence: 88% ✅
- Term consistency: 85% ✅
- Header descriptiveness: 90% ✅

**Overall Score: 89 (A - Very Good)**

**Diagnosis:**
- Excellent chunk sizes and distribution
- Low duplication
- High semantic diversity (32 PCA components)
- Consistent terminology
- Descriptive headers

**Action Items:**
1. Maintain current standards
2. Document style guide for new contributors
3. Re-evaluate in 3 months

---

## Continuous Improvement Process

### Monthly Evaluation Cycle

1. **Week 1:** Run automated evaluation
2. **Week 2:** Complete manual checklists
3. **Week 3:** Calculate scores and identify issues
4. **Week 4:** Implement improvements

### Track Progress Over Time

Create a tracking spreadsheet:

| Date | Overall Score | Median Chunk | Duplication | Quality | Section Indep. | Notes |
|------|---------------|--------------|-------------|---------|----------------|-------|
| 2025-01 | 38 (F) | 45 chars | 18% | 0.35 | 40% | Initial eval |
| 2025-02 | 68 (C) | 420 chars | 8% | 0.62 | 65% | Expanded sections |
| 2025-03 | 85 (A) | 620 chars | 4% | 0.79 | 85% | Added topic headers |

### Setting Improvement Goals

**Example 90-Day Plan:**

**Month 1 Goal: Reach Grade C (60-69)**
- Focus: Increase chunk sizes
- Action: Expand all sections <500 chars

**Month 2 Goal: Reach Grade B (70-79)**
- Focus: Reduce duplication
- Action: Remove boilerplate, unique content

**Month 3 Goal: Reach Grade A (80-89)**
- Focus: Improve independence
- Action: Add topic names to headers, define terms

---

## Troubleshooting Common Issues

### Issue: Median Chunk Size Too Small (<300 chars)

**Symptoms:**
- Many very_small chunks
- Poor quality score
- Low PCA components

**Causes:**
- Sections too short
- Too many headers
- List-heavy content without explanation

**Fixes:**
1. Combine related sections
2. Add explanatory paragraphs to lists
3. Expand examples with context
4. Target 500+ chars per section

---

### Issue: High Duplication Rate (>10%)

**Symptoms:**
- Many duplicate warnings in logs
- Duplicates concentrated in specific files
- Similar chunks across documents

**Causes:**
- Repeated templates (bibliography, references)
- Copy-pasted disclaimers
- Shared headers in all docs

**Fixes:**
1. Remove or shorten repeated sections
2. Use links instead of duplicating content
3. Consolidate shared info in one master doc
4. Make document-specific variations

---

### Issue: Low Vocabulary Diversity (<20%)

**Symptoms:**
- Repetitive language
- Same phrases used many times
- Monotonous content

**Causes:**
- Over-reliance on specific terms
- Lack of examples
- Technical jargon without explanation

**Fixes:**
1. Use synonyms appropriately
2. Add varied examples
3. Define terms in different ways
4. Include use cases and scenarios

---

### Issue: Poor Section Independence (<60%)

**Symptoms:**
- Many "see above" references
- Pronouns without clear antecedents
- Context-dependent explanations

**Causes:**
- Linear writing style
- Assuming reader follows order
- Incomplete section headers

**Fixes:**
1. Add topic names to headers
2. Replace pronouns with nouns
3. Make cross-references descriptive
4. Include key context in each section

---

### Issue: Low PCA Components (<15)

**Symptoms:**
- All data compressed into few dimensions
- Embeddings cluster tightly
- Poor retrieval diversity

**Causes:**
- Content too similar
- Repetitive structure
- Lack of varied examples

**Root cause is usually:** Small chunks + high duplication

**Fixes:**
1. Address chunk size issues first
2. Reduce duplication
3. Add diverse examples
4. Cover different aspects of topics

---

## Tools and Scripts

### Quick Evaluation Script

Create `evaluate_docs.sh`:

```bash
#!/bin/bash

echo "================================"
echo "Document Evaluation Tool"
echo "================================"
echo ""

# Run ingestion
echo "Running ingestion with preprocessor..."
python ingest_with_preprocessor.py

# Extract key metrics from log
LOG_FILE=$(ls -t ingestion_preprocessed_*.log | head -1)

echo ""
echo "================================"
echo "Quick Metrics Summary"
echo "================================"

echo ""
echo "Chunk Size:"
grep "Median Size:" "$LOG_FILE"

echo ""
echo "Duplication:"
grep "Removal rate:" "$LOG_FILE"

echo ""
echo "Quality:"
grep "Overall quality:" "$LOG_FILE"

echo ""
echo "Full report: $LOG_FILE"
echo ""
```

Make executable: `chmod +x evaluate_docs.sh`

Run: `./evaluate_docs.sh`

---

## Summary

**Key Metrics to Monitor:**

1. **Median chunk size** (target: 500-800 chars)
2. **Duplication rate** (target: <5%)
3. **Quality score** (target: >0.7)
4. **Section independence** (target: >80%)
5. **Term consistency** (target: >80%)

**Evaluation Frequency:**

- **After major changes:** Immediate re-evaluation
- **Regular cadence:** Monthly evaluation
- **New documentation:** Evaluate before adding to production

**Remember:** Documentation is an iterative process. Start with baseline evaluation, set realistic improvement goals, and track progress over time.

---

## See Also

- `WRITING_RAG_FRIENDLY_DOCUMENTATION.md` - Best practices for writing
- `RAG_DATA_PREPARATION_GUIDE.md` - Understanding the RAG pipeline
- `PREPROCESSOR_QUICKSTART.md` - Using the preprocessor

---

**Document evaluation is not a one-time activity - it's a continuous quality improvement process!**
