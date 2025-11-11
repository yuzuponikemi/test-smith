# Chunking Strategy Evaluation for RAG Applications

## A Practical Guide to Measuring Retrieval Quality

This guide explains how to evaluate and optimize chunking strategies from the **application side** - measuring how well different chunking approaches perform during actual retrieval and answer generation.

---

## Table of Contents

1. [Overview: Two Types of Evaluation](#overview-two-types-of-evaluation)
2. [Retrieval Quality Metrics](#retrieval-quality-metrics)
3. [Creating Test Sets](#creating-test-sets)
4. [Evaluation Framework Design](#evaluation-framework-design)
5. [Implementation Guide](#implementation-guide)
6. [Comparing Chunking Strategies](#comparing-chunking-strategies)
7. [A/B Testing Methodology](#ab-testing-methodology)
8. [Continuous Monitoring](#continuous-monitoring)

---

## Overview: Two Types of Evaluation

### Preprocessing Evaluation (Already Covered)

**What**: Measures document/chunk quality before retrieval
**When**: During ingestion
**Metrics**: Chunk size, duplication rate, quality score
**Tool**: `ingest_with_preprocessor.py`, `DOCUMENT_DESIGN_EVALUATION.md`

### Application-Side Evaluation (This Guide)

**What**: Measures retrieval effectiveness during actual use
**When**: After ingestion, during query time
**Metrics**: Precision, recall, answer quality, latency
**Tool**: Test set evaluation, A/B testing

**Key Difference:** Preprocessing evaluation tells you if your chunks are well-formed. Application evaluation tells you if they actually help answer questions.

---

## Retrieval Quality Metrics

### 1. Precision

**Definition:** Of the chunks retrieved, how many are actually relevant?

```
Precision = Relevant Chunks Retrieved / Total Chunks Retrieved
```

**Example:**
- Query: "How to configure PostgreSQL authentication?"
- Retrieved 5 chunks, 4 are about PostgreSQL auth, 1 is about MySQL
- Precision = 4/5 = 0.80

**Ideal Value:** >0.8

**High Precision Means:**
- Few irrelevant chunks in results
- Clean, focused retrieval
- Better context for LLM

### 2. Recall

**Definition:** Of all relevant chunks in the database, how many were retrieved?

```
Recall = Relevant Chunks Retrieved / Total Relevant Chunks in DB
```

**Example:**
- Database has 10 chunks about PostgreSQL authentication
- Query retrieved 4 of them
- Recall = 4/10 = 0.40

**Ideal Value:** >0.6 (depends on k)

**High Recall Means:**
- Not missing important information
- Comprehensive coverage
- Better answer completeness

### 3. F1 Score

**Definition:** Harmonic mean of precision and recall

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**Ideal Value:** >0.7

**Why It Matters:** Balances precision and recall - a single metric to optimize

### 4. Mean Reciprocal Rank (MRR)

**Definition:** Average of reciprocal ranks of first relevant chunk

```
MRR = (1/N) × Σ(1 / rank of first relevant chunk)
```

**Example:**
- Query 1: First relevant chunk at position 1 → 1/1 = 1.0
- Query 2: First relevant chunk at position 3 → 1/3 = 0.33
- Query 3: First relevant chunk at position 2 → 1/2 = 0.50
- MRR = (1.0 + 0.33 + 0.50) / 3 = 0.61

**Ideal Value:** >0.7

**Why It Matters:** Measures if relevant chunks appear early in results

### 5. Normalized Discounted Cumulative Gain (NDCG)

**Definition:** Measures ranking quality with position weighting

```
DCG = Σ (relevance score / log₂(position + 1))
NDCG = DCG / Ideal DCG
```

**Ideal Value:** >0.8

**Why It Matters:** Rewards relevant chunks appearing in top positions

### 6. Answer Quality Metrics

**Definition:** Human or LLM evaluation of final answer quality

**Aspects to Measure:**
- **Accuracy**: Is the answer factually correct?
- **Completeness**: Does it answer all parts of the question?
- **Relevance**: Does it stay on topic?
- **Coherence**: Is it well-structured?

**Rating Scale:**
- 5: Excellent - Perfect answer
- 4: Good - Minor issues
- 3: Fair - Partially correct
- 2: Poor - Mostly incorrect
- 1: Very Poor - Completely wrong

### 7. Latency

**Definition:** Time from query to answer

**Components:**
- Retrieval time (embedding + similarity search)
- LLM generation time
- Total end-to-end time

**Ideal Values:**
- Retrieval: <500ms
- Generation: <3s (depends on model)
- Total: <5s

### 8. Context Window Utilization

**Definition:** How much of retrieved context actually fits in LLM window

```
Utilization = Characters Used / Max Context Window
```

**Ideal Value:** 50-80%

**Why It Matters:**
- Too low: Wasting context capacity
- Too high: Risk of truncation

---

## Creating Test Sets

### Golden Test Set Components

A good test set needs:

1. **Queries** - Representative user questions
2. **Expected Chunks** - Which chunks should be retrieved
3. **Expected Answers** - What the correct answer should be

### Example Test Set Format

```json
{
  "test_cases": [
    {
      "id": "test_001",
      "query": "How do I configure PostgreSQL to allow remote connections?",
      "category": "configuration",
      "difficulty": "easy",
      "expected_chunks": [
        "documents/postgresql-setup.md:chunk_42",
        "documents/postgresql-setup.md:chunk_43"
      ],
      "expected_answer_contains": [
        "listen_addresses",
        "postgresql.conf",
        "pg_hba.conf"
      ],
      "metadata": {
        "requires_multi_hop": false,
        "specificity": "high"
      }
    },
    {
      "id": "test_002",
      "query": "What's the difference between PostgreSQL roles and users?",
      "category": "concepts",
      "difficulty": "medium",
      "expected_chunks": [
        "documents/postgresql-auth.md:chunk_12",
        "documents/postgresql-auth.md:chunk_15"
      ],
      "expected_answer_contains": [
        "role",
        "user",
        "LOGIN privilege"
      ],
      "metadata": {
        "requires_multi_hop": true,
        "specificity": "medium"
      }
    }
  ]
}
```

### Test Set Design Principles

**1. Coverage**
- Represent all document types in your knowledge base
- Cover different query types (factual, how-to, conceptual)
- Include edge cases

**2. Difficulty Distribution**
- 40% Easy queries (direct fact retrieval)
- 40% Medium queries (require 2-3 chunks)
- 20% Hard queries (require reasoning across multiple chunks)

**3. Size**
- Minimum: 20 test cases for basic evaluation
- Recommended: 50-100 test cases for reliable statistics
- Comprehensive: 200+ test cases for production systems

**4. Query Types to Include**

| Type | Example | Purpose |
|------|---------|---------|
| Factual | "What is the default PostgreSQL port?" | Tests basic retrieval |
| Procedural | "How do I backup a PostgreSQL database?" | Tests multi-step info |
| Conceptual | "Why use connection pooling?" | Tests understanding |
| Comparative | "Difference between md5 and scram-sha-256?" | Tests relationships |
| Troubleshooting | "How to fix 'could not connect' error?" | Tests problem-solving |

### Creating Your Test Set

**Method 1: From Real Queries**

1. Collect actual user queries (from logs, support tickets)
2. Select representative samples
3. Manually identify correct answers and chunks
4. Validate with domain experts

**Method 2: Synthetic Generation**

1. Review your documentation
2. For each major topic, create 3-5 questions
3. Mark which chunks should answer each question
4. Have someone else validate

**Method 3: Hybrid Approach**

1. Start with 20 real queries
2. Identify gaps in coverage
3. Create synthetic queries to fill gaps
4. Validate entire set

---

## Evaluation Framework Design

### Architecture

```
┌─────────────────────────────────────────────────┐
│         Chunking Strategy Evaluator             │
└─────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Strategy │  │ Strategy │  │ Strategy │
  │    A     │  │    B     │  │    C     │
  │ (1000ch) │  │ (500ch)  │  │(Markdown)│
  └──────────┘  └──────────┘  └──────────┘
        │              │              │
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Test Set       │
              │  (50 queries)   │
              └─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Metric         │
              │  Calculation    │
              └─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Comparison     │
              │  Report         │
              └─────────────────┘
```

### Key Components

**1. Strategy Ingestion Module**
- Ingests documents with different chunking configs
- Creates separate vector stores per strategy
- Tracks strategy metadata

**2. Query Execution Module**
- Runs each test query against each strategy
- Records retrieved chunks and metadata
- Captures timing information

**3. Metric Calculation Module**
- Compares retrieved vs expected chunks
- Calculates precision, recall, F1, MRR, NDCG
- Evaluates answer quality

**4. Reporting Module**
- Generates comparison tables
- Creates visualizations
- Provides actionable recommendations

---

## Implementation Guide

### Step 1: Create Test Set

```python
# test_set.py
from dataclasses import dataclass
from typing import List

@dataclass
class TestCase:
    id: str
    query: str
    category: str
    expected_chunks: List[str]  # List of chunk IDs
    expected_keywords: List[str]
    difficulty: str  # 'easy', 'medium', 'hard'

# Create test set
test_cases = [
    TestCase(
        id="test_001",
        query="How do I configure PostgreSQL authentication?",
        category="configuration",
        expected_chunks=[
            "postgresql-setup.md:chunk_42",
            "postgresql-setup.md:chunk_43"
        ],
        expected_keywords=["pg_hba.conf", "authentication", "md5"],
        difficulty="easy"
    ),
    # Add more test cases...
]
```

### Step 2: Ingest with Multiple Strategies

```python
# ingest_strategies.py
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

class StrategyIngestion:
    """Ingest documents with different chunking strategies"""

    def __init__(self, documents_dir: str):
        self.documents_dir = documents_dir
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

    def ingest_strategy_a(self):
        """Strategy A: Large chunks (1000 chars)"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        # Load and split documents
        chunks = self._load_and_split(splitter)

        # Create vector store
        vectorstore = Chroma(
            collection_name="strategy_a_1000",
            persist_directory="chroma_db_strategy_a",
            embedding_function=self.embeddings
        )

        vectorstore.add_documents(chunks)
        return vectorstore

    def ingest_strategy_b(self):
        """Strategy B: Small chunks (500 chars)"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )

        chunks = self._load_and_split(splitter)

        vectorstore = Chroma(
            collection_name="strategy_b_500",
            persist_directory="chroma_db_strategy_b",
            embedding_function=self.embeddings
        )

        vectorstore.add_documents(chunks)
        return vectorstore

    def ingest_strategy_c(self):
        """Strategy C: Markdown-aware (header-based)"""
        # Implementation...
        pass
```

### Step 3: Run Evaluation

```python
# evaluate_strategies.py
from typing import List, Dict
import time

class ChunkingEvaluator:
    """Evaluate different chunking strategies"""

    def __init__(self, test_cases: List[TestCase]):
        self.test_cases = test_cases

    def evaluate_strategy(self, vectorstore, strategy_name: str, k: int = 5):
        """Evaluate a single strategy"""
        results = []

        for test_case in self.test_cases:
            # Retrieve chunks
            start_time = time.time()
            retrieved = vectorstore.similarity_search(
                test_case.query,
                k=k
            )
            retrieval_time = time.time() - start_time

            # Calculate metrics
            precision = self._calculate_precision(
                retrieved, test_case.expected_chunks
            )
            recall = self._calculate_recall(
                retrieved, test_case.expected_chunks
            )
            f1 = self._calculate_f1(precision, recall)
            mrr = self._calculate_mrr(
                retrieved, test_case.expected_chunks
            )

            results.append({
                'test_id': test_case.id,
                'query': test_case.query,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'mrr': mrr,
                'retrieval_time': retrieval_time,
                'num_retrieved': len(retrieved)
            })

        # Aggregate results
        return self._aggregate_results(results, strategy_name)

    def _calculate_precision(self, retrieved, expected):
        """Calculate precision"""
        if not retrieved:
            return 0.0

        retrieved_ids = {self._get_chunk_id(chunk) for chunk in retrieved}
        expected_ids = set(expected)

        relevant = retrieved_ids & expected_ids
        return len(relevant) / len(retrieved_ids)

    def _calculate_recall(self, retrieved, expected):
        """Calculate recall"""
        if not expected:
            return 0.0

        retrieved_ids = {self._get_chunk_id(chunk) for chunk in retrieved}
        expected_ids = set(expected)

        relevant = retrieved_ids & expected_ids
        return len(relevant) / len(expected_ids)

    def _calculate_f1(self, precision, recall):
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def _calculate_mrr(self, retrieved, expected):
        """Calculate Mean Reciprocal Rank"""
        retrieved_ids = [self._get_chunk_id(chunk) for chunk in retrieved]
        expected_ids = set(expected)

        for i, chunk_id in enumerate(retrieved_ids, 1):
            if chunk_id in expected_ids:
                return 1.0 / i
        return 0.0

    def _get_chunk_id(self, chunk):
        """Extract chunk ID from metadata"""
        # Assuming chunks have source + position metadata
        return f"{chunk.metadata.get('source', '')}:chunk_{chunk.metadata.get('chunk_index', 0)}"

    def _aggregate_results(self, results: List[Dict], strategy_name: str):
        """Aggregate results across all test cases"""
        import numpy as np

        return {
            'strategy': strategy_name,
            'num_queries': len(results),
            'avg_precision': np.mean([r['precision'] for r in results]),
            'avg_recall': np.mean([r['recall'] for r in results]),
            'avg_f1': np.mean([r['f1'] for r in results]),
            'avg_mrr': np.mean([r['mrr'] for r in results]),
            'avg_retrieval_time': np.mean([r['retrieval_time'] for r in results]),
            'detailed_results': results
        }
```

### Step 4: Generate Comparison Report

```python
# report_generator.py
import pandas as pd
import matplotlib.pyplot as plt

class ReportGenerator:
    """Generate evaluation reports"""

    def generate_report(self, results: List[Dict]):
        """Generate comprehensive comparison report"""
        # Create summary table
        df = pd.DataFrame([
            {
                'Strategy': r['strategy'],
                'Precision': f"{r['avg_precision']:.3f}",
                'Recall': f"{r['avg_recall']:.3f}",
                'F1 Score': f"{r['avg_f1']:.3f}",
                'MRR': f"{r['avg_mrr']:.3f}",
                'Avg Time (ms)': f"{r['avg_retrieval_time']*1000:.1f}"
            }
            for r in results
        ])

        print("\n" + "="*80)
        print("CHUNKING STRATEGY EVALUATION REPORT")
        print("="*80)
        print("\n" + df.to_string(index=False))

        # Visualizations
        self._plot_metrics(results)
        self._plot_difficulty_breakdown(results)

        # Recommendations
        self._generate_recommendations(results)

    def _plot_metrics(self, results):
        """Plot metric comparison"""
        strategies = [r['strategy'] for r in results]
        metrics = {
            'Precision': [r['avg_precision'] for r in results],
            'Recall': [r['avg_recall'] for r in results],
            'F1 Score': [r['avg_f1'] for r in results],
            'MRR': [r['avg_mrr'] for r in results]
        }

        x = range(len(strategies))
        width = 0.2

        fig, ax = plt.subplots(figsize=(12, 6))

        for i, (metric, values) in enumerate(metrics.items()):
            offset = width * i
            ax.bar([p + offset for p in x], values, width, label=metric)

        ax.set_xlabel('Strategy')
        ax.set_ylabel('Score')
        ax.set_title('Chunking Strategy Performance Comparison')
        ax.set_xticks([p + width * 1.5 for p in x])
        ax.set_xticks Labels(strategies)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig('strategy_comparison.png')
        plt.close()

    def _generate_recommendations(self, results):
        """Generate actionable recommendations"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)

        # Find best strategy overall
        best_f1 = max(results, key=lambda x: x['avg_f1'])
        print(f"\n✅ Best Overall Strategy: {best_f1['strategy']}")
        print(f"   F1 Score: {best_f1['avg_f1']:.3f}")

        # Find fastest strategy
        fastest = min(results, key=lambda x: x['avg_retrieval_time'])
        print(f"\n⚡ Fastest Strategy: {fastest['strategy']}")
        print(f"   Avg Time: {fastest['avg_retrieval_time']*1000:.1f}ms")

        # Find best precision
        best_precision = max(results, key=lambda x: x['avg_precision'])
        print(f"\n🎯 Most Precise Strategy: {best_precision['strategy']}")
        print(f"   Precision: {best_precision['avg_precision']:.3f}")

        # Find best recall
        best_recall = max(results, key=lambda x: x['avg_recall'])
        print(f"\n📚 Best Recall Strategy: {best_recall['strategy']}")
        print(f"   Recall: {best_recall['avg_recall']:.3f}")
```

### Step 5: Run Complete Evaluation

```python
# run_evaluation.py
from test_set import test_cases
from ingest_strategies import StrategyIngestion
from evaluate_strategies import ChunkingEvaluator
from report_generator import ReportGenerator

def main():
    print("Starting chunking strategy evaluation...")

    # Step 1: Ingest with different strategies
    print("\n1. Ingesting documents with different strategies...")
    ingestion = StrategyIngestion("documents/")

    strategy_a = ingestion.ingest_strategy_a()
    strategy_b = ingestion.ingest_strategy_b()
    strategy_c = ingestion.ingest_strategy_c()

    # Step 2: Evaluate each strategy
    print("\n2. Evaluating strategies...")
    evaluator = ChunkingEvaluator(test_cases)

    results = [
        evaluator.evaluate_strategy(strategy_a, "Strategy A: 1000 chars"),
        evaluator.evaluate_strategy(strategy_b, "Strategy B: 500 chars"),
        evaluator.evaluate_strategy(strategy_c, "Strategy C: Markdown"),
    ]

    # Step 3: Generate report
    print("\n3. Generating report...")
    reporter = ReportGenerator()
    reporter.generate_report(results)

    print("\n✅ Evaluation complete!")

if __name__ == "__main__":
    main()
```

---

## Comparing Chunking Strategies

### Common Strategies to Test

**1. Fixed-Size Chunking**
```python
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
```

**Trade-offs:**
- Small chunks (500): Better precision, lower recall
- Large chunks (1500): Better recall, lower precision
- Medium chunks (1000): Balanced

**2. Semantic Chunking**
```python
# Based on sentence boundaries, paragraphs
SentenceSplitter(chunk_size=1000)
```

**Trade-offs:**
- Preserves semantic units
- May create variable-sized chunks
- Better context coherence

**3. Markdown-Aware Chunking**
```python
MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")]
)
```

**Trade-offs:**
- Structure-aware
- Better for documentation
- Variable sizes

**4. Hybrid Approach**
```python
# Markdown headers + recursive fallback
```

**Trade-offs:**
- Best of both worlds
- More complex implementation
- Usually best results

### Example Comparison Results

```
CHUNKING STRATEGY EVALUATION REPORT
================================================================================

Strategy                    Precision  Recall  F1 Score   MRR    Avg Time (ms)
Strategy A: 1000 chars          0.856   0.723     0.784  0.891        245.3
Strategy B: 500 chars           0.912   0.645     0.756  0.823        198.7
Strategy C: Markdown            0.891   0.778     0.831  0.912        267.1

RECOMMENDATIONS
================================================================================

✅ Best Overall Strategy: Strategy C: Markdown
   F1 Score: 0.831

⚡ Fastest Strategy: Strategy B: 500 chars
   Avg Time: 198.7ms

🎯 Most Precise Strategy: Strategy B: 500 chars
   Precision: 0.912

📚 Best Recall Strategy: Strategy C: Markdown
   Recall: 0.778
```

**Analysis:**
- Markdown strategy wins overall (F1: 0.831)
- Small chunks have best precision but miss information (low recall)
- Large chunks have good balance
- Trade-off: 30% slower for 5% better F1

---

## A/B Testing Methodology

### Production A/B Testing

**Scenario:** You want to test a new chunking strategy without disrupting existing users.

**Implementation:**

```python
import random

class ABTestRetriever:
    """A/B test different retrieval strategies"""

    def __init__(self, strategy_a_store, strategy_b_store, split_ratio=0.5):
        self.strategy_a = strategy_a_store
        self.strategy_b = strategy_b_store
        self.split_ratio = split_ratio
        self.metrics = {'a': [], 'b': []}

    def retrieve(self, query: str, user_id: str = None):
        """Route to strategy A or B based on user"""
        # Deterministic routing based on user_id
        if user_id:
            # Hash user_id to get consistent assignment
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            use_strategy_a = (hash_val % 100) < (self.split_ratio * 100)
        else:
            # Random assignment
            use_strategy_a = random.random() < self.split_ratio

        strategy_used = 'a' if use_strategy_a else 'b'
        store = self.strategy_a if use_strategy_a else self.strategy_b

        # Retrieve
        start_time = time.time()
        results = store.similarity_search(query, k=5)
        latency = time.time() - start_time

        # Log metrics
        self.metrics[strategy_used].append({
            'query': query,
            'latency': latency,
            'num_results': len(results),
            'timestamp': time.time()
        })

        return results, strategy_used

    def get_metrics_summary(self):
        """Get A/B test metrics summary"""
        import numpy as np

        return {
            'strategy_a': {
                'queries': len(self.metrics['a']),
                'avg_latency': np.mean([m['latency'] for m in self.metrics['a']]),
                'median_latency': np.median([m['latency'] for m in self.metrics['a']])
            },
            'strategy_b': {
                'queries': len(self.metrics['b']),
                'avg_latency': np.mean([m['latency'] for m in self.metrics['b']]),
                'median_latency': np.median([m['latency'] for m in self.metrics['b']])
            }
        }
```

### Collecting User Feedback

```python
class FeedbackCollector:
    """Collect implicit and explicit feedback"""

    def __init__(self):
        self.feedback = []

    def log_implicit_feedback(self, query_id: str, strategy: str,
                             user_clicked_result: bool,
                             time_spent: float):
        """Log implicit signals"""
        self.feedback.append({
            'query_id': query_id,
            'strategy': strategy,
            'clicked': user_clicked_result,
            'time_spent': time_spent,
            'feedback_type': 'implicit'
        })

    def log_explicit_feedback(self, query_id: str, strategy: str,
                             rating: int):
        """Log explicit ratings"""
        self.feedback.append({
            'query_id': query_id,
            'strategy': strategy,
            'rating': rating,  # 1-5
            'feedback_type': 'explicit'
        })

    def analyze_feedback(self):
        """Analyze collected feedback"""
        strategy_a_ratings = [
            f['rating'] for f in self.feedback
            if f['strategy'] == 'a' and f['feedback_type'] == 'explicit'
        ]
        strategy_b_ratings = [
            f['rating'] for f in self.feedback
            if f['strategy'] == 'b' and f['feedback_type'] == 'explicit'
        ]

        return {
            'strategy_a_avg_rating': np.mean(strategy_a_ratings) if strategy_a_ratings else 0,
            'strategy_b_avg_rating': np.mean(strategy_b_ratings) if strategy_b_ratings else 0,
            'total_feedback': len(self.feedback)
        }
```

---

## Continuous Monitoring

### Metrics to Track Over Time

**1. Retrieval Quality Drift**

Track if retrieval quality decreases as knowledge base grows:

```python
class QualityMonitor:
    """Monitor retrieval quality over time"""

    def __init__(self):
        self.history = []

    def evaluate_weekly(self, vectorstore, test_set):
        """Run weekly evaluation"""
        evaluator = ChunkingEvaluator(test_set)
        results = evaluator.evaluate_strategy(vectorstore, "production")

        self.history.append({
            'timestamp': datetime.now(),
            'db_size': vectorstore.get_collection().count(),
            'avg_f1': results['avg_f1'],
            'avg_precision': results['avg_precision'],
            'avg_recall': results['avg_recall']
        })

    def plot_trends(self):
        """Plot quality trends"""
        df = pd.DataFrame(self.history)

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Quality metrics
        axes[0].plot(df['timestamp'], df['avg_f1'], label='F1', marker='o')
        axes[0].plot(df['timestamp'], df['avg_precision'], label='Precision', marker='s')
        axes[0].plot(df['timestamp'], df['avg_recall'], label='Recall', marker='^')
        axes[0].set_ylabel('Score')
        axes[0].set_title('Retrieval Quality Over Time')
        axes[0].legend()
        axes[0].grid(alpha=0.3)

        # Database size
        axes[1].plot(df['timestamp'], df['db_size'], color='green', marker='o')
        axes[1].set_ylabel('Number of Chunks')
        axes[1].set_title('Knowledge Base Growth')
        axes[1].grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig('quality_trends.png')
```

**2. Query Category Performance**

Track performance per query type:

```python
def analyze_by_category(results):
    """Analyze performance by query category"""
    from collections import defaultdict

    category_metrics = defaultdict(list)

    for result in results['detailed_results']:
        # Assuming test cases have category info
        category = result.get('category', 'unknown')
        category_metrics[category].append(result['f1'])

    print("\nPerformance by Category:")
    for category, f1_scores in category_metrics.items():
        avg_f1 = np.mean(f1_scores)
        print(f"  {category}: F1={avg_f1:.3f} ({len(f1_scores)} queries)")
```

---

## Summary

### Evaluation Workflow

1. **Create Test Set** (50-100 representative queries)
2. **Ingest Multiple Strategies** (different chunk sizes/methods)
3. **Run Evaluation** (calculate metrics for each strategy)
4. **Analyze Results** (compare F1, precision, recall, MRR)
5. **Select Winner** (balance quality vs latency)
6. **A/B Test in Production** (validate with real users)
7. **Monitor Continuously** (track quality over time)

### Key Takeaways

- **No universal best strategy** - depends on your documents and queries
- **Balance precision and recall** - F1 score is your friend
- **Test with real queries** - synthetic tests may not represent reality
- **Monitor continuously** - quality can drift as KB grows
- **Consider latency** - 5% better F1 for 2x latency may not be worth it

### Next Steps

1. Create your test set using real queries
2. Implement the evaluation framework
3. Test 3-5 chunking strategies
4. Select winner based on your priorities (quality vs speed)
5. Deploy and monitor

---

## See Also

- **[RAG Data Preparation Guide](RAG_DATA_PREPARATION_GUIDE.md)** - Preprocessing fundamentals
- **[Document Design Evaluation](DOCUMENT_DESIGN_EVALUATION.md)** - Preprocessing metrics
- **[System Overview](system-overview.md)** - Complete architecture

---

**Remember**: The best chunking strategy is the one that works best for YOUR specific documents and queries. Always validate with real data!
