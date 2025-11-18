# Documentation Quality Evaluation

Reproducible metrics for evaluating RAG-friendly documentation.

---

## Overview

Good documentation for RAG should produce:
- Self-contained chunks
- Consistent terminology
- Appropriate chunk sizes (500-800 chars median)
- Low duplication rate (<5%)
- High semantic diversity

---

## Automated Metrics

Run the preprocessor to get these metrics:

```bash
python scripts/ingest/ingest_with_preprocessor.py
```

### Chunk Size Distribution

**Target:**
```
very_small (<100 chars):   < 5%
small (100-500 chars):     15-25%
medium (500-1000 chars):   50-60%  ← IDEAL
large (1000-1500 chars):   15-25%
very_large (>1500 chars):  < 5%
```

**Scoring:**
- Excellent: 55-65% medium, <5% very small
- Good: 45-70% medium, <10% very small
- Poor: <40% medium or >15% very small

### Median Chunk Size

**Target: 500-800 characters**

| Score | Range | Status |
|-------|-------|--------|
| Excellent | 500-800 chars | Optimal |
| Good | 400-1000 chars | Acceptable |
| Needs Work | 200-400 or 1000-1500 chars | Review |
| Poor | <200 or >1500 chars | Fix |

### Duplication Rate

**Target: <5%**

| Score | Rate | Status |
|-------|------|--------|
| Excellent | <5% | Good |
| Good | 5-10% | Acceptable |
| Needs Work | 10-20% | Review |
| Poor | >20% | Fix |

### Quality Score

**Target: >0.7**

| Score | Range | Grade |
|-------|-------|-------|
| Excellent | 0.9+ | A |
| Good | 0.75-0.89 | B |
| Fair | 0.6-0.74 | C |
| Poor | 0.4-0.59 | D |
| Very Poor | <0.4 | F |

### Vocabulary Diversity

**Target: 25-50%** (unique words / total words)

| Score | Range | Status |
|-------|-------|--------|
| Excellent | 35-50% | Good |
| Good | 25-35% | Acceptable |
| Needs Work | 15-25% | Review |
| Poor | <15% | Fix |

### PCA Variance Components

**Target: 20-40 components for 95% variance**

Run Section 3.0 in `chroma_explorer.ipynb`:

| Components | Interpretation |
|------------|----------------|
| <15 | Content too similar, lacks diversity |
| 20-40 | Good diversity and coherence |
| >60 | Content too scattered |

---

## Manual Evaluation Checklists

### Section Independence

Sample 10 random sections and score each:

1. **Understandable alone?**
   - 2 points: Fully self-contained
   - 1 point: Mostly clear
   - 0 points: Requires other sections

2. **Topic mentioned explicitly?**
   - 2 points: In header AND content
   - 1 point: In content only
   - 0 points: Not mentioned

3. **Adequately detailed?**
   - 2 points: 500+ chars, complete
   - 1 point: 200-500 chars, basic
   - 0 points: <200 chars

**Score: (Total / 60) × 100**

### Term Consistency

For 5 key concepts, count term variations:

| Concept | Terms Used | Primary % |
|---------|------------|-----------|
| Database | "database" (45), "DB" (12) | 79% |
| Config | "configuration" (30), "config" (25) | 55% |

**Score: Average of Primary %**
- Excellent: >80%
- Good: 60-80%
- Poor: <40%

### Header Descriptiveness

Categorize all H2/H3 headers:

1. **Generic**: "Overview", "Introduction", "Step 1"
2. **Topic-specific**: "PostgreSQL Installation"
3. **Fully descriptive**: "Installing PostgreSQL on Ubuntu"

**Score: (Fully × 2 + Specific × 1) / (Total × 2) × 100**

### Acronym Definition

Check if all acronyms are defined on first use:

**Score: (Defined on first use / Total) × 100**

---

## Overall Score Calculation

```
Score =
  (Chunk Size Distribution × 0.15) +
  (Median Chunk Size × 0.10) +
  (Duplication Rate × 0.15) +
  (Quality Score × 0.15) +
  (Vocabulary Diversity × 0.10) +
  (Section Independence × 0.15) +
  (Term Consistency × 0.10) +
  (Header Descriptiveness × 0.10)
```

### Grade Scale

| Score | Grade | Action |
|-------|-------|--------|
| 90-100 | A+ | Maintain quality |
| 80-89 | A | Minor improvements |
| 70-79 | B | Review weak areas |
| 60-69 | C | Restructure sections |
| 50-59 | D | Major revision |
| <50 | F | Complete rewrite |

---

## Evaluation Workflow

### Step 1: Automated Evaluation

```bash
./scripts/ingest/clean_and_reingest.sh
cp ingestion_preprocessed_*.log evaluation_$(date +%Y%m%d).log
```

### Step 2: Extract Metrics

| Metric | Target | Your Score |
|--------|--------|------------|
| Median Chunk Size | 500-800 | ___ |
| Medium % | 50-60% | ___ |
| Duplication Rate | <5% | ___ |
| Quality Score | >0.7 | ___ |

### Step 3: PCA Analysis

```bash
jupyter notebook chroma_explorer.ipynb
```

Run Section 3.0, record components for 95% variance.

### Step 4: Manual Evaluation

Complete checklists and record scores.

### Step 5: Calculate Overall Score

### Step 6: Identify Action Items

For each metric <70%, create improvement tasks.

---

## Troubleshooting

### Small Chunks (<300 chars median)

**Causes:**
- Sections too short
- Too many headers
- Lists without explanation

**Fixes:**
- Combine related sections
- Add explanatory text
- Target 500+ chars

### High Duplication (>10%)

**Causes:**
- Repeated templates
- Copy-pasted content
- Shared headers

**Fixes:**
- Remove repeated sections
- Use links instead
- Make variations unique

### Low Diversity (<20%)

**Causes:**
- Repetitive language
- Same phrases repeated
- No varied examples

**Fixes:**
- Use synonyms appropriately
- Add diverse examples
- Vary explanations

### Poor Independence (<60%)

**Causes:**
- "See above" references
- Pronouns without antecedents
- Context-dependent content

**Fixes:**
- Add topic to headers
- Replace pronouns
- Include context per section

---

## Continuous Improvement

### Monthly Cycle

1. Week 1: Run automated evaluation
2. Week 2: Complete manual checklists
3. Week 3: Calculate scores, identify issues
4. Week 4: Implement improvements

### Track Progress

| Date | Score | Median | Duplication | Quality |
|------|-------|--------|-------------|---------|
| 2025-01 | 38 (F) | 45 | 18% | 0.35 |
| 2025-02 | 68 (C) | 420 | 8% | 0.62 |
| 2025-03 | 85 (A) | 620 | 4% | 0.79 |

---

## Related Documentation

- **[RAG Guide](rag-guide.md)** - Complete RAG system guide
- **[Writing Documentation](writing-docs.md)** - Best practices for content
- **[Preprocessor](preprocessor.md)** - Using the preprocessor
