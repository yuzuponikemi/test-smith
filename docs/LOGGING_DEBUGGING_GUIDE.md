# Logging, Debugging, and Report Management Guide

**Test-Smith v2.0-alpha**

This guide provides comprehensive information about logging, debugging, and report management in Test-Smith.

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Execution Logs](#execution-logs)
4. [Research Reports](#research-reports)
5. [Usage Examples](#usage-examples)
6. [Debugging Techniques](#debugging-techniques)
7. [LangSmith Integration](#langsmith-integration)
8. [Best Practices](#best-practices)
9. [Maintenance](#maintenance)

---

## Overview

Test-Smith uses a dual-output system for tracking execution and preserving research results:

- **Execution Logs** (`logs/`) - Detailed node-by-node execution traces for debugging and performance analysis
- **Research Reports** (`reports/`) - Final markdown reports with metadata for sharing and archiving

Both directories are:
- ✅ Tracked by Git (via `.gitkeep` files)
- ❌ Contents ignored by Git (in `.gitignore`)
- 📝 Important for local tracking and debugging

---

## Directory Structure

```
test-smith/
├── logs/                                  # Execution logs directory
│   ├── .gitkeep                          # Ensures directory is tracked
│   ├── execution_20251112_143022_Compare_LangGraph_and_AutoGPT.log
│   └── execution_20251112_151530_transformer_vs_RNN.log
│
├── reports/                               # Research reports directory
│   ├── .gitkeep                          # Ensures directory is tracked
│   ├── report_20251112_143528_hierarchical_Compare_LangGraph.md
│   └── report_20251112_151845_simple_What_is_BERT.md
│
├── src/
│   └── utils/
│       └── logging_utils.py              # Centralized logging utilities
│
└── main.py                                # CLI with integrated logging
```

### File Naming Conventions

**Execution Logs:**
```
execution_{YYYYMMDD}_{HHMMSS}_{sanitized_query}.log
```

**Research Reports:**
```
report_{YYYYMMDD}_{HHMMSS}_{execution_mode}_{sanitized_query}.md
```

Where:
- `execution_mode`: `simple` or `hierarchical`
- `sanitized_query`: First 50 characters, alphanumeric and underscores only

---

## Execution Logs

### What's Logged

Execution logs provide a complete trace of the agent's execution:

1. **Header Information**
   - Query text
   - Thread ID
   - Start timestamp

2. **Node Execution**
   - Node name and execution order
   - Input/output for each node
   - Timestamps for performance analysis

3. **Master Plan Details** (hierarchical mode)
   - Complexity assessment
   - Subtask decomposition
   - Dependencies and priorities

4. **Query Allocation**
   - RAG queries
   - Web queries
   - Strategic allocation reasoning

5. **Subtask Execution** (hierarchical mode)
   - Subtask ID and description
   - Focus area
   - Execution progress

6. **Footer Information**
   - End timestamp
   - Total duration
   - Log file path

### Log Format Example

```log
================================================================================
Test-Smith Execution Log
================================================================================
Query: Compare LangGraph and AutoGPT in terms of architecture and use cases
Thread ID: 7b3a2f5e-9c8d-4e2a-b1f3-8d7c6e5a4b3c
Start Time: 2025-11-12T14:30:22.451293
================================================================================

[14:30:22.452] INFO: Starting Test-Smith execution
[14:30:22.452] INFO: Query: Compare LangGraph and AutoGPT...
[14:30:22.453] INFO: Thread ID: 7b3a2f5e-9c8d-4e2a-b1f3-8d7c6e5a4b3c

[14:30:22.500] NODE:
--- MASTER_PLANNER ---

[14:30:25.123] MASTER_PLAN:
================================================================================
[14:30:25.124] MASTER_PLAN: Complexity: COMPLEX
[14:30:25.124] MASTER_PLAN: Execution Mode: hierarchical
[14:30:25.125] MASTER_PLAN: Subtasks: 5

[14:30:25.125] MASTER_PLAN:
  Subtask 1: task_1
[14:30:25.126] MASTER_PLAN:     Description: Analyze LangGraph architecture
[14:30:25.126] MASTER_PLAN:     Focus: LangGraph technical analysis
[14:30:25.127] MASTER_PLAN:     Priority: 1, Importance: 0.9
...

[14:30:25.200] NODE: Output from 'master_planner':
  execution_mode: hierarchical
  master_plan: {5 keys}
  current_subtask_index: 0

[14:30:25.300] SUBTASK:
━━━ Subtask: task_1 ━━━
[14:30:25.301] SUBTASK:   subtask_id: task_1
[14:30:25.301] SUBTASK:   description: Analyze LangGraph architecture
...

================================================================================
Execution Complete
================================================================================
End Time: 2025-11-12T14:35:28.123456
Duration: 305.67 seconds
Log File: logs/execution_20251112_143022_Compare_LangGraph_and_AutoGPT.log
================================================================================
```

### Viewing Logs

**List recent logs:**
```bash
python main.py list logs --limit 10
```

**View specific log:**
```bash
cat logs/execution_20251112_143022_Compare_LangGraph_and_AutoGPT.log
```

**Tail a running execution** (in another terminal):
```bash
tail -f logs/execution_*.log
```

**Search logs for errors:**
```bash
grep "ERROR" logs/execution_*.log
```

---

## Research Reports

### Report Structure

Reports are saved as Markdown files with YAML front matter metadata:

```markdown
---
generated_by: Test-Smith v2.0-alpha
execution_mode: hierarchical
timestamp: 2025-11-12T14:35:28.123456
query: "Compare LangGraph and AutoGPT in terms of architecture and use cases"
thread_id: "7b3a2f5e-9c8d-4e2a-b1f3-8d7c6e5a4b3c"
subtask_count: 5
complexity_reasoning: "The query involves comparing two different frameworks..."
---

# LangGraph vs AutoGPT: Comprehensive Architectural Comparison

## Executive Summary

This report synthesizes findings from 5 independent research subtasks...

[Report content continues...]
```

### Metadata Fields

**Common Fields** (all reports):
- `generated_by`: System version identifier
- `execution_mode`: `simple` or `hierarchical`
- `timestamp`: ISO 8601 timestamp
- `query`: Original user query
- `thread_id`: Unique execution thread ID

**Hierarchical Mode Additional Fields:**
- `subtask_count`: Number of subtasks executed
- `complexity_reasoning`: Why the query was classified as complex

### Viewing Reports

**List recent reports:**
```bash
# All reports
python main.py list reports --limit 10

# Only hierarchical reports
python main.py list reports --mode hierarchical

# Only simple reports
python main.py list reports --mode simple
```

**Open a report:**
```bash
# In default markdown viewer
open reports/report_20251112_143528_hierarchical_Compare_LangGraph.md

# Or with your preferred editor
code reports/report_20251112_143528_hierarchical_Compare_LangGraph.md
```

---

## Usage Examples

### Basic Execution (with logging and report)

```bash
python main.py run "Compare LangGraph and AutoGPT"
```

This will:
- ✅ Create execution log in `logs/`
- ✅ Save final report in `reports/`
- ✅ Display progress in console

### Console-Only Mode (no files)

```bash
python main.py run "What is BERT?" --no-log --no-report
```

This will:
- ❌ No execution log saved
- ❌ No report saved
- ✅ Display progress in console only

### Disable Logging Only

```bash
python main.py run "Explain transformers" --no-log
```

This will:
- ❌ No execution log saved
- ✅ Save final report in `reports/`
- ✅ Display progress in console

### Disable Report Saving Only

```bash
python main.py run "Quick test query" --no-report
```

This will:
- ✅ Create execution log in `logs/`
- ❌ No report saved
- ✅ Display progress in console

### Using Thread IDs for Conversation

```bash
# First query
python main.py run "What is LangGraph?" --thread-id my-session-123

# Follow-up query in same thread
python main.py run "How does it compare to AutoGPT?" --thread-id my-session-123
```

---

## Debugging Techniques

### 1. Finding Failures

**Search logs for errors:**
```bash
grep -r "ERROR" logs/
```

**Find specific node failures:**
```bash
grep -A 10 "master_planner" logs/execution_*.log
```

### 2. Analyzing Execution Flow

**Check Master Plan decisions:**
```bash
grep -A 20 "MASTER_PLAN" logs/execution_*.log
```

**Track subtask execution:**
```bash
grep "SUBTASK" logs/execution_*.log
```

### 3. Performance Analysis

**Extract timestamps:**
```bash
grep -E "\[.*\]" logs/execution_*.log | head -20
```

**Check total duration:**
```bash
grep "Duration:" logs/execution_*.log
```

### 4. Query Allocation Analysis

**Review RAG vs Web allocation:**
```bash
grep -A 5 "Allocation Strategy" logs/execution_*.log
```

### 5. Common Issues and Solutions

| Issue | Symptom | Debug Command | Solution |
|-------|---------|---------------|----------|
| Master Planner generates 0 subtasks | Complex query treated as simple | `grep "Subtasks: 0" logs/*.log` | Check if `command-r` model is available |
| RAG retrieval returns irrelevant results | Poor quality analysis | `grep "Retrieved.*documents" logs/*.log` | Improve embedding quality or query formulation |
| Web search fails | Missing web results | `grep "Searching web" logs/*.log` | Check Tavily API key in `.env` |
| Slow execution | Long duration in logs | `grep "Duration:" logs/*.log` | Check model response times, consider timeout adjustments |

### 6. Debugging Hierarchical Execution

**Verify subtask decomposition:**
```bash
# Check how many subtasks were created
grep "Subtasks Generated" logs/execution_*.log

# View subtask details
grep -A 30 "MASTER_PLAN" logs/execution_*.log | grep -E "(Subtask|Description|Priority|Dependencies)"
```

**Track subtask progress:**
```bash
# See which subtask is currently executing
grep "Subtask.*/" logs/execution_*.log
```

**Verify all subtasks completed:**
```bash
# Count subtask executions
grep -c "━━━ Subtask:" logs/execution_*.log
```

---

## LangSmith Integration

### Current Status

**Test-Smith v2.0-alpha does NOT currently integrate with LangSmith.**

We use local file-based logging instead for several reasons:
1. ✅ **No external dependencies** - Works offline
2. ✅ **Full data privacy** - All logs stay local
3. ✅ **Simple debugging** - Standard text files, easy to `grep`
4. ✅ **Version control friendly** - `.gitignore` prevents accidental commits

### Future LangSmith Integration (Planned)

LangSmith integration is planned for future versions and would provide:

- 🔍 **Visual trace inspection** - See execution graphs in browser
- 📊 **Performance dashboards** - Aggregate metrics across runs
- 🏷️ **Tagging and organization** - Categorize runs by project/experiment
- 🔗 **Team collaboration** - Share traces with team members
- 📈 **A/B testing** - Compare different prompt variations

### How to Add LangSmith (When Needed)

If you want to add LangSmith tracking:

1. **Install LangSmith SDK:**
   ```bash
   pip install langsmith
   ```

2. **Add environment variables to `.env`:**
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
   LANGCHAIN_API_KEY="your-api-key"
   LANGCHAIN_PROJECT="test-smith"
   ```

3. **Update `main.py`:**
   ```python
   import os
   os.environ["LANGCHAIN_TRACING_V2"] = "true"
   os.environ["LANGCHAIN_PROJECT"] = "test-smith"
   ```

LangSmith will automatically trace all LangChain operations without changing node code.

**Recommendation:** Start with local file logging for development, add LangSmith when you need collaborative debugging or production monitoring.

---

## Best Practices

### 1. When to Use File Logging

**Always use file logging (default) for:**
- ✅ Complex hierarchical queries
- ✅ Debugging issues
- ✅ Performance analysis
- ✅ Production runs
- ✅ Experiments you may want to review later

**Use `--no-log` for:**
- ❌ Quick tests
- ❌ Development iterations
- ❌ Disk space constraints

### 2. When to Save Reports

**Always save reports (default) for:**
- ✅ Research you want to keep
- ✅ Sharing results with others
- ✅ Building a knowledge base
- ✅ Comparing different approaches

**Use `--no-report` for:**
- ❌ Test runs
- ❌ Debug iterations
- ❌ Queries with known bad output

### 3. Organizing Logs and Reports

**Use descriptive queries:**
```bash
# Good - query describes the topic clearly
python main.py run "Compare transformer vs RNN architectures for NLP"

# Bad - vague query makes files hard to find
python main.py run "compare stuff"
```

**Create a research journal:**
```bash
# Keep notes on which reports are important
echo "2025-11-12: Great hierarchical comparison report - report_20251112_143528_*" >> research_journal.md
```

### 4. Monitoring Execution

**Watch logs in real-time:**
```bash
# Terminal 1: Run agent
python main.py run "Complex research query"

# Terminal 2: Watch log output
watch -n 1 'ls -lt logs/ | head -5 && tail -20 logs/execution_*.log'
```

### 5. Debugging Workflow

When investigating issues:

1. **Reproduce with logging enabled** (default behavior)
2. **Check the execution log** for errors and timing
3. **Examine Master Plan** decisions if hierarchical
4. **Review query allocation** strategy
5. **Inspect node outputs** for anomalies
6. **Compare with previous successful runs**

---

## Maintenance

### Cleanup Old Files

The logging system includes a cleanup utility:

```python
from src.utils.logging_utils import cleanup_old_files

# Dry run - see what would be deleted
deleted_count = cleanup_old_files(days=30, dry_run=True)
print(f"Would delete {deleted_count['logs']} logs and {deleted_count['reports']} reports")

# Actually delete files older than 30 days
deleted_count = cleanup_old_files(days=30, dry_run=False)
print(f"Deleted {deleted_count['logs']} logs and {deleted_count['reports']} reports")
```

**Automated cleanup script** (`scripts/cleanup_old_files.py`):

```python
#!/usr/bin/env python3
"""Clean up old log and report files."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging_utils import cleanup_old_files

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean up old logs and reports")
    parser.add_argument("--days", type=int, default=30, help="Delete files older than N days")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")

    args = parser.parse_args()

    deleted = cleanup_old_files(days=args.days, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\nWould delete:")
    else:
        print(f"\nDeleted:")

    print(f"  - {deleted['logs']} log files")
    print(f"  - {deleted['reports']} report files")
```

**Usage:**
```bash
# See what would be deleted
python scripts/cleanup_old_files.py --dry-run --days 30

# Actually delete
python scripts/cleanup_old_files.py --days 30
```

### Disk Space Monitoring

**Check logs directory size:**
```bash
du -sh logs/
```

**Check reports directory size:**
```bash
du -sh reports/
```

**Find largest files:**
```bash
# Largest logs
ls -lhS logs/ | head -10

# Largest reports
ls -lhS reports/ | head -10
```

### Archiving Important Reports

Create an archive for important research:

```bash
# Create archive directory
mkdir -p archive/2025-11

# Move important reports
cp reports/report_20251112_143528_hierarchical_Compare_LangGraph.md \
   archive/2025-11/

# Add to git (since archive/ is not ignored)
git add archive/2025-11/
git commit -m "Archive: LangGraph vs AutoGPT comparison"
```

---

## Quick Reference

### Commands

```bash
# Run with logging and report (default)
python main.py run "your query"

# Run without logging
python main.py run "your query" --no-log

# Run without report saving
python main.py run "your query" --no-report

# Console only (no files)
python main.py run "your query" --no-log --no-report

# List recent reports
python main.py list reports --limit 10

# List hierarchical reports only
python main.py list reports --mode hierarchical

# List recent logs
python main.py list logs --limit 10
```

### File Locations

| Content | Directory | Git Tracked? |
|---------|-----------|--------------|
| Execution logs | `logs/` | Directory yes, contents no |
| Research reports | `reports/` | Directory yes, contents no |
| Important archived reports | `archive/` | Yes (manual) |

### Log Analysis Commands

```bash
# Find errors
grep -r "ERROR" logs/

# Find specific node
grep -A 10 "node_name" logs/execution_*.log

# Check Master Plans
grep -A 20 "MASTER_PLAN" logs/execution_*.log

# Subtask execution
grep "SUBTASK" logs/execution_*.log

# Execution duration
grep "Duration:" logs/execution_*.log

# Recent executions
ls -lt logs/ | head -5
```

---

## Support

For issues, questions, or suggestions:

1. Check execution logs in `logs/` for error messages
2. Review this guide for common issues and solutions
3. Check `docs/SYSTEM_OVERVIEW.md` for architecture understanding
4. Open an issue in the project repository

---

**Document Version:** 2.0-alpha
**Last Updated:** 2025-11-12
**Related Docs:**
- [System Overview](SYSTEM_OVERVIEW.md)
- [Phase 1 Implementation Plan](PHASE1_IMPLEMENTATION_PLAN.md)
- [Hierarchical Task Decomposition](HIERARCHICAL_TASK_DECOMPOSITION.md)
