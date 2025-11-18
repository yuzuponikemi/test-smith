# Logging & Debugging Guide

Debug execution, analyze logs, and manage research reports.

---

## Overview

Test-Smith uses a dual-output system:
- **Execution Logs** (`logs/`) - Node-by-node execution traces
- **Research Reports** (`reports/`) - Final markdown reports

---

## Directory Structure

```
test-smith/
├── logs/
│   ├── execution_20251112_143022_Compare_LangGraph.log
│   └── ...
├── reports/
│   ├── report_20251112_143528_hierarchical_Compare.md
│   └── ...
```

### Naming Convention

**Logs:**
```
execution_{YYYYMMDD}_{HHMMSS}_{query}.log
```

**Reports:**
```
report_{YYYYMMDD}_{HHMMSS}_{mode}_{query}.md
```

---

## Viewing Output

### List Recent Files

```bash
# Reports
python main.py list reports --limit 10

# Hierarchical reports only
python main.py list reports --mode hierarchical

# Logs
python main.py list logs --limit 10
```

### View Files

```bash
cat logs/execution_*.log
cat reports/report_*.md
```

### Watch Execution

```bash
# In another terminal
tail -f logs/execution_*.log
```

---

## Log Content

### Header

```log
================================================================================
Test-Smith Execution Log
================================================================================
Query: Compare LangGraph and AutoGPT
Thread ID: 7b3a2f5e-9c8d-4e2a-b1f3-8d7c6e5a4b3c
Start Time: 2025-11-12T14:30:22.451293
```

### Node Execution

```log
[14:30:22.500] NODE: --- MASTER_PLANNER ---

[14:30:25.123] MASTER_PLAN: Complexity: COMPLEX
[14:30:25.124] MASTER_PLAN: Subtasks: 5
```

### Subtask Progress

```log
[14:30:25.300] SUBTASK: ━━━ Subtask: task_1 ━━━
[14:30:25.301] SUBTASK:   description: Analyze LangGraph architecture
```

### Footer

```log
================================================================================
Execution Complete
================================================================================
Duration: 305.67 seconds
================================================================================
```

---

## Report Structure

Reports include YAML metadata:

```markdown
---
generated_by: Test-Smith v2.2
execution_mode: hierarchical
timestamp: 2025-11-12T14:35:28.123456
query: "Compare LangGraph and AutoGPT"
thread_id: "7b3a2f5e..."
subtask_count: 5
---

# Report Title

## Executive Summary
...
```

---

## Debugging Commands

### Find Errors

```bash
grep -r "ERROR" logs/
```

### Check Master Plan

```bash
grep -A 20 "MASTER_PLAN" logs/execution_*.log
```

### Track Subtasks

```bash
grep "SUBTASK" logs/execution_*.log
```

### Check Duration

```bash
grep "Duration:" logs/execution_*.log
```

### Query Allocation

```bash
grep -A 5 "Allocation Strategy" logs/execution_*.log
```

---

## Common Issues

### Master Planner: 0 Subtasks

**Symptom:** Complex query treated as simple

**Check:**
```bash
grep "Subtasks: 0" logs/*.log
```

**Fix:** Verify `command-r` model is available

### RAG Returns Irrelevant

**Symptom:** Poor quality analysis

**Check:**
```bash
grep "Retrieved.*documents" logs/*.log
```

**Fix:** Improve embedding quality or queries

### Web Search Fails

**Symptom:** Missing web results

**Check:**
```bash
grep "Searching web" logs/*.log
```

**Fix:** Verify Tavily API key in `.env`

### Slow Execution

**Symptom:** >5 minutes for simple queries

**Check:**
```bash
grep "Duration:" logs/*.log
```

**Fix:** Check model response times

---

## Usage Options

### Full Output (Default)

```bash
python main.py run "Query"
```
- Creates log in `logs/`
- Saves report in `reports/`
- Displays progress

### No Logging

```bash
python main.py run "Query" --no-log
```

### No Report

```bash
python main.py run "Query" --no-report
```

### Console Only

```bash
python main.py run "Query" --no-log --no-report
```

---

## LangSmith Integration

### Configure

```bash
# .env
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-key"
LANGCHAIN_PROJECT="deep-research-v1-proto"
```

### View Traces

Navigate to https://smith.langchain.com/ and select your project.

---

## Maintenance

### Cleanup Old Files

```python
from src.utils.logging_utils import cleanup_old_files

# Preview
cleanup_old_files(days=30, dry_run=True)

# Delete
cleanup_old_files(days=30, dry_run=False)
```

### Check Disk Usage

```bash
du -sh logs/ reports/
```

### Archive Important Reports

```bash
mkdir -p archive/2025-11
cp reports/important_report.md archive/2025-11/
git add archive/
```

---

## Best Practices

### When to Log

Always log for:
- Complex queries
- Debugging
- Performance analysis
- Production runs

Use `--no-log` for:
- Quick tests
- Development iterations

### Research Journal

Keep notes on important reports:

```bash
echo "2025-11-12: Good comparison - report_*.md" >> research_journal.md
```

### Debugging Workflow

1. Reproduce with logging enabled
2. Check log for errors/timing
3. Examine Master Plan
4. Review query allocation
5. Compare with successful runs

---

## Quick Reference

### Commands

```bash
# Run with full output
python main.py run "Query"

# Console only
python main.py run "Query" --no-log --no-report

# List files
python main.py list reports --limit 10
python main.py list logs --limit 10
```

### Search Commands

```bash
grep "ERROR" logs/*.log
grep "MASTER_PLAN" logs/*.log
grep "Duration:" logs/*.log
```

---

## Related Documentation

- **[Evaluation Guide](evaluation-guide.md)** - Test the system
- **[System Overview](../architecture/system-overview.md)** - Architecture
