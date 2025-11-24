# Structured Logging Guide

Test-Smith uses `structlog` for machine-readable, queryable logging.

## Overview

**Structured logging** provides:
- **Machine-readable logs**: Easy to parse, filter, and analyze
- **Contextual information**: Automatic binding of query, node, thread_id
- **Performance metrics**: Automatic timing of operations
- **Development-friendly**: Human-readable console output
- **Production-ready**: JSON output for log aggregation tools

## Configuration

### Environment Variables

Control logging behavior via `.env`:

```bash
# Log format: false (human-readable) or true (JSON)
STRUCTURED_LOGS_JSON=false

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

**Development** (default):
- Human-readable console output with colors
- Shows all context fields clearly
- Easy to read during debugging

**Production**:
- JSON-formatted logs
- Machine-parseable
- Compatible with Elasticsearch, Splunk, CloudWatch

## Usage in Nodes

### Basic Pattern

```python
from src.utils.structured_logging import log_node_execution

def my_node(state):
    with log_node_execution("my_node", state) as logger:
        # Your node logic here
        logger.info("processing_start", item_count=len(items))

        # Automatic performance logging
        with log_performance(logger, "expensive_operation"):
            result = expensive_function()

        logger.info("processing_complete", results=len(result))

        return {"output": result}
```

### Helper Functions

#### Query Allocation

```python
from src.utils.structured_logging import log_query_allocation

log_query_allocation(logger, rag_queries, web_queries, strategy)
# Logs: query_allocation event with counts and strategy
```

#### Evaluation Result

```python
from src.utils.structured_logging import log_evaluation_result

log_evaluation_result(logger, is_sufficient, reason, loop_count)
# Logs: evaluation_complete event with decision
```

#### Analysis Summary

```python
from src.utils.structured_logging import log_analysis_summary

log_analysis_summary(logger, web_count, rag_count, code_count)
# Logs: analysis_start event with result counts
```

#### KB Status

```python
from src.utils.structured_logging import log_kb_status

log_kb_status(logger, kb_info)
# Logs: kb_status event with availability and chunks
```

## Log Output Examples

### Development Mode (Human-Readable)

```
2025-01-24T10:30:45.123Z [info] node_start node=planner query="What is TDD?" loop_count=0 model=gemini/gemini-2.5-flash
2025-01-24T10:30:45.234Z [info] kb_check_start
2025-01-24T10:30:45.456Z [info] operation_complete operation=kb_contents_check duration_ms=123.45
2025-01-24T10:30:45.567Z [info] kb_status available=True total_chunks=150 document_count=5
2025-01-24T10:30:45.678Z [info] llm_invoke_start has_feedback=False
2025-01-24T10:30:47.890Z [info] operation_complete operation=strategic_planning duration_ms=2212.34
2025-01-24T10:30:47.891Z [info] query_allocation rag_query_count=2 web_query_count=1 total_queries=3 strategy="Use RAG for basics, web for current tools"
2025-01-24T10:30:47.892Z [info] node_end node=planner execution_time_ms=2769.12 status=success
```

### Production Mode (JSON)

```json
{"event": "node_start", "level": "info", "timestamp": "2025-01-24T10:30:45.123Z", "node": "planner", "query": "What is TDD?", "loop_count": 0, "model": "gemini/gemini-2.5-flash"}
{"event": "kb_check_start", "level": "info", "timestamp": "2025-01-24T10:30:45.234Z", "node": "planner", "query": "What is TDD?"}
{"event": "operation_complete", "level": "info", "timestamp": "2025-01-24T10:30:45.456Z", "node": "planner", "operation": "kb_contents_check", "duration_ms": 123.45}
{"event": "kb_status", "level": "info", "timestamp": "2025-01-24T10:30:45.567Z", "node": "planner", "available": true, "total_chunks": 150, "document_count": 5}
{"event": "query_allocation", "level": "info", "timestamp": "2025-01-24T10:30:47.891Z", "node": "planner", "rag_query_count": 2, "web_query_count": 1, "total_queries": 3, "strategy": "Use RAG for basics, web for current tools"}
{"event": "node_end", "level": "info", "timestamp": "2025-01-24T10:30:47.892Z", "node": "planner", "execution_time_ms": 2769.12, "status": "success"}
```

## Log Analysis

### Query Examples

**Find slow operations:**
```bash
# JSON logs
cat logs/structured_*.log | jq 'select(.duration_ms > 1000)'

# Development logs
grep "duration_ms" logs/structured_*.log | awk '$NF > 1000'
```

**Track node execution times:**
```bash
# Average execution time per node
cat logs/structured_*.log | jq 'select(.event == "node_end") | {node, execution_time_ms}' | jq -s 'group_by(.node) | map({node: .[0].node, avg_time: (map(.execution_time_ms) | add / length)})'
```

**Find errors:**
```bash
# JSON logs
cat logs/structured_*.log | jq 'select(.level == "error")'
```

**Track query allocation patterns:**
```bash
# Distribution of RAG vs Web queries
cat logs/structured_*.log | jq 'select(.event == "query_allocation") | {rag: .rag_query_count, web: .web_query_count}'
```

## Benefits

### 1. Performance Monitoring

Automatic timing of:
- Node execution
- LLM API calls
- KB retrieval
- Web search

### 2. Debugging

Contextual information automatically included:
- Query text
- Loop iteration
- Node name
- Model used

### 3. Production Monitoring

JSON logs enable:
- Aggregation in log management tools
- Alerting on error patterns
- Performance dashboards
- Query pattern analysis

### 4. Backward Compatibility

- Old `print()` statements still work
- Visual feedback maintained
- Gradual migration possible

## Migration from Print-Based Logging

### Before (Old Style)

```python
def my_node(state):
    print_node_header("MY NODE")
    print(f"Processing {len(items)} items...")

    start_time = time.time()
    result = process(items)
    duration = time.time() - start_time

    print(f"Processed in {duration:.2f}s")
    return {"result": result}
```

### After (Structured Logging)

```python
def my_node(state):
    print_node_header("MY NODE")

    with log_node_execution("my_node", state) as logger:
        logger.info("processing_start", item_count=len(items))

        with log_performance(logger, "item_processing"):
            result = process(items)

        logger.info("processing_complete", result_count=len(result))
        return {"result": result}
```

**Advantages:**
- Automatic timing
- Machine-readable
- Context automatically bound
- No manual string formatting

## Best Practices

### 1. Use Descriptive Event Names

✅ Good:
```python
logger.info("kb_retrieval_complete", chunks_found=5)
logger.info("llm_invoke_start", has_feedback=True)
```

❌ Bad:
```python
logger.info("done")  # Too generic
logger.info("step_1")  # Not descriptive
```

### 2. Include Relevant Context

✅ Good:
```python
logger.info("query_allocation",
            rag_queries=len(rag),
            web_queries=len(web),
            strategy=strategy)
```

❌ Bad:
```python
logger.info("allocated")  # Missing context
```

### 3. Use Performance Logging for Operations

✅ Good:
```python
with log_performance(logger, "vector_search"):
    results = vectorstore.similarity_search(query)
```

❌ Bad:
```python
start = time.time()
results = vectorstore.similarity_search(query)
duration = time.time() - start
logger.info("search_done", duration=duration)  # Manual timing
```

### 4. Log Errors with Context

✅ Good:
```python
try:
    plan = structured_llm.invoke(prompt)
except Exception as e:
    logger.error("structured_output_failed",
                 error_type=type(e).__name__,
                 error_message=str(e),
                 fallback="json_parsing")
    # Handle fallback
```

❌ Bad:
```python
try:
    plan = structured_llm.invoke(prompt)
except Exception as e:
    logger.error("error", error=str(e))  # Minimal context
```

## See Also

- [structlog Documentation](https://www.structlog.org/)
- [Logging Best Practices](https://www.python.org/dev/peps/pep-0282/)
- [src/utils/structured_logging.py](../src/utils/structured_logging.py) - Implementation
