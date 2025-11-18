# Logging with Model Information

**Status:** ✅ Implemented
**Version:** Added in v2.1

## What Changed

All node execution logs now show which LLM model is being used in real-time.

### Before:
```
---MASTER PLANNER---
---STRATEGIC PLANNER---
---SYNTHESIZER---
```

### After:
```
---MASTER PLANNER (ollama/llama3+command-r)---
---STRATEGIC PLANNER (ollama/llama3+command-r)---
---SYNTHESIZER (ollama/llama3+command-r)---
```

Or with Gemini:
```
---MASTER PLANNER (gemini/gemini-2.5-flash)---
---STRATEGIC PLANNER (gemini/gemini-2.5-flash)---
---SYNTHESIZER (gemini/gemini-2.5-flash)---
```

## Benefits

1. **Transparency**: Know exactly which model processed each node
2. **Debugging**: Quickly verify the correct model provider is being used
3. **Performance Analysis**: Correlate execution times with model types
4. **LangSmith Traces**: Model info visible in all traces
5. **Comparative Testing**: Easy to see model differences in logs

## Implementation

### New Utility Function

Added to `src/utils/logging_utils.py`:

```python
def print_node_header(node_name: str):
    """
    Print a standardized node header with model information.

    Example:
        print_node_header("MASTER PLANNER")
        # Outputs: ---MASTER PLANNER (ollama/llama3+command-r)---
    """
    model_info = get_current_model_info()
    print(f"---{node_name} ({model_info})---")
```

### Updated Nodes

All execution nodes now use `print_node_header()`:

**Updated Files:**
- ✅ `src/nodes/master_planner_node.py`
- ✅ `src/nodes/planner_node.py`
- ✅ `src/nodes/synthesizer_node.py`
- ✅ `src/nodes/evaluator_node.py`
- ✅ `src/nodes/analyzer_node.py`
- ✅ `src/nodes/searcher_node.py`
- ✅ `src/nodes/rag_retriever_node.py`
- ✅ `src/nodes/subtask_router.py`
- ✅ `src/nodes/subtask_executor.py`
- ✅ `src/nodes/depth_evaluator_node.py`
- ✅ `src/nodes/drill_down_generator.py`
- ✅ `src/nodes/plan_revisor_node.py`

### Example Usage

```python
from src.utils.logging_utils import print_node_header

def my_node(state):
    print_node_header("MY NODE")  # Shows: ---MY NODE (ollama/llama3+command-r)---
    # ... rest of node logic
```

## Model Information Format

### Ollama Format:
```
ollama/llama3+command-r
```
- Indicates local Ollama is being used
- Shows multiple models available (planner uses llama3, evaluator uses command-r)

### Gemini Format:
```
gemini/gemini-2.5-flash
```
- Indicates Google Gemini API is being used
- Shows specific model version

## Where You'll See It

### 1. Console Output

When running any command:
```bash
python main.py run "your query"
```

You'll see:
```
---MASTER PLANNER (ollama/llama3+command-r)---
  Analyzing query: your query...
```

### 2. Log Files

In `logs/execution_*.log`:
```
[14:23:45.123] NODE:
--- MASTER PLANNER (ollama/llama3+command-r) ---
[14:23:45.456] INFO: Analyzing query: your query...
```

### 3. LangSmith Traces

Model info appears in all LangSmith execution traces, making it easy to:
- Compare performance across model providers
- Verify correct model usage in production
- Debug model-specific issues

## Testing the Feature

### Test Different Providers

```bash
# Test with Ollama
python switch_model_provider.py ollama
python main.py run "test query"
# Should show: (ollama/llama3+command-r)

# Test with Gemini
python switch_model_provider.py gemini
python main.py run "test query"
# Should show: (gemini/gemini-2.5-flash)
```

### Verify in Logs

```bash
# Run evaluation
python evaluate_agent.py --dry-run --limit 1

# Check the log
tail -100 logs/execution_*.log | grep "---"
```

## Use Cases

### 1. Performance Comparison

Compare execution logs with different models:

```bash
# Run with Ollama
python switch_model_provider.py ollama
python main.py run "complex query" > ollama_output.log

# Run with Gemini
python switch_model_provider.py gemini
python main.py run "complex query" > gemini_output.log

# Compare execution times per node
diff ollama_output.log gemini_output.log
```

### 2. Debugging Model Issues

If a specific node fails or gives poor results:
- Check the log to see which model was used
- Verify it matches your expectations
- Switch providers and retry

### 3. Cost Tracking

When using Gemini:
- Count how many nodes executed
- Estimate API costs based on node count
- Identify which nodes use the most tokens

## Related Documentation

- **Model Provider Guide**: `docs/MODEL_PROVIDER_GUIDE.md`
- **Gemini Setup**: `docs/GEMINI_SETUP_GUIDE.md`
- **Logging Utilities**: `src/utils/logging_utils.py`
- **Switch Script**: `switch_model_provider.py`

## Summary

✅ All nodes now show which LLM is being used
✅ Visible in console output, logs, and LangSmith traces
✅ Automatically updates when switching providers
✅ No manual configuration needed

**Example Output:**
```
---MASTER PLANNER (ollama/llama3+command-r)---
  Analyzing query: What is quantum computing?...

  ✓ Complexity Assessment: SIMPLE
  Execution Mode: simple

---STRATEGIC PLANNER (ollama/llama3+command-r)---
  Checking knowledge base contents...
  KB Status: Knowledge base contains 859 chunks

---SYNTHESIZER (ollama/llama3+command-r)---
  Mode: SIMPLE
  ✓ Report generated successfully
```

This makes it crystal clear which model is handling each step of your research workflow!
