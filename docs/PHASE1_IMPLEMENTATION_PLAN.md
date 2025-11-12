# Phase 1 Implementation Plan: Hierarchical Foundation

**Status:** 📋 Ready to Implement
**Target:** v2.0-alpha
**Goal:** Add basic hierarchical capabilities without breaking existing system
**Estimated Effort:** 2-3 days of focused development

## Overview

Phase 1 introduces the **Master Planner** and basic subtask execution loop, while maintaining 100% backward compatibility with the current system.

**Key Principle:** Simple queries use the current flow, complex queries get decomposed into subtasks.

## Success Criteria

- ✅ Simple queries work exactly as before (zero regression)
- ✅ Complex queries decompose into 2-5 subtasks
- ✅ Each subtask executes through existing Strategic Planner → Searcher/RAG → Analyzer → Evaluator
- ✅ Synthesizer combines multiple subtask results coherently
- ✅ All existing tests pass
- ✅ New hierarchical tests pass

## Architecture Changes

### Before (v1.0):
```
User Query
    ↓
Strategic Planner → web_queries + rag_queries
    ↓
Searcher + RAG (parallel)
    ↓
Analyzer
    ↓
Evaluator
    ↓
[Loop max 2x if insufficient]
    ↓
Synthesizer
```

### After (v2.0-alpha):
```
User Query
    ↓
Master Planner (NEW)
    ├─ Simple? → Delegate to Strategic Planner (existing flow)
    └─ Complex? → Decompose into subtasks
        ↓
        [For each subtask]
            Strategic Planner → web_queries + rag_queries
            Searcher + RAG
            Analyzer (subtask-focused)
            Evaluator (subtask-focused)
        ↓
        Synthesizer (multi-subtask aware)
```

## Implementation Tasks

### Task 1: Create Schema Updates

**File:** `src/schemas.py`

**Add:**
```python
from typing import List, Optional
from pydantic import BaseModel, Field

class SubTask(BaseModel):
    """
    Represents a single subtask in hierarchical decomposition
    """
    subtask_id: str = Field(description="Unique identifier (e.g., 'task_1')")
    description: str = Field(description="Clear description of what this subtask should accomplish")
    focus_area: str = Field(description="Specific aspect this subtask covers")
    priority: int = Field(description="Execution order (1 = first)")
    dependencies: List[str] = Field(
        default=[],
        description="List of subtask_ids that must complete before this one"
    )
    estimated_importance: float = Field(
        ge=0.0, le=1.0,
        description="Importance score (0-1) for resource allocation"
    )

class MasterPlan(BaseModel):
    """
    Master plan with complexity detection and subtask decomposition
    """
    is_complex: bool = Field(description="Whether the query requires hierarchical decomposition")
    complexity_reasoning: str = Field(description="Explanation of complexity assessment")
    execution_mode: str = Field(description="'simple' or 'hierarchical'")
    subtasks: List[SubTask] = Field(
        default=[],
        description="List of subtasks (empty if simple mode)"
    )
    overall_strategy: str = Field(description="High-level strategy for addressing the query")

# Note: Keep existing schemas (StrategicPlan, Evaluation, etc.) unchanged
```

**Testing:**
```python
# Test schema validation
plan = MasterPlan(
    is_complex=True,
    complexity_reasoning="Query has multiple parts",
    execution_mode="hierarchical",
    subtasks=[
        SubTask(
            subtask_id="task_1",
            description="Research LangGraph architecture",
            focus_area="Technical architecture",
            priority=1,
            dependencies=[],
            estimated_importance=0.9
        )
    ],
    overall_strategy="Compare two frameworks systematically"
)
```

### Task 2: Update State Management

**File:** `src/graph.py`

**Modify `AgentState`:**
```python
from typing import TypedDict, Annotated, Optional
import operator

class AgentState(TypedDict):
    # Original query
    query: str

    # NEW: Hierarchical mode fields
    execution_mode: str  # "simple" or "hierarchical"
    master_plan: Optional[dict]  # MasterPlan as dict
    current_subtask_id: Optional[str]  # Which subtask is currently executing
    current_subtask_index: int  # Index in subtask list
    subtask_results: dict  # subtask_id → analyzed_data

    # Existing fields (used per-subtask in hierarchical mode)
    web_queries: list[str]
    rag_queries: list[str]
    allocation_strategy: str
    search_results: Annotated[list[str], operator.add]
    rag_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]
    report: str
    evaluation: str
    reason: str
    loop_count: int
```

**Note:** We'll use dict for `master_plan` instead of MasterPlan directly because LangGraph state needs JSON-serializable types.

### Task 3: Create Master Planner Node

**File:** `src/nodes/master_planner_node.py` (NEW)

```python
from src.models import get_planner_model
from src.prompts.master_planner_prompt import MASTER_PLANNER_PROMPT
from src.schemas import MasterPlan

def master_planner(state):
    """
    Detects query complexity and creates Master Plan

    Simple queries: Delegates to Strategic Planner (existing flow)
    Complex queries: Decomposes into subtasks
    """
    print("---MASTER PLANNER---")

    query = state["query"]

    # Get KB metadata for context (reuse existing function)
    from src.nodes.planner_node import check_kb_contents
    kb_info = check_kb_contents()

    # Invoke LLM with structured output
    model = get_planner_model()
    structured_llm = model.with_structured_output(MasterPlan)

    prompt = MASTER_PLANNER_PROMPT.format(
        query=query,
        kb_summary=kb_info['summary'],
        kb_available=kb_info['available']
    )

    try:
        master_plan = structured_llm.invoke(prompt)

        print(f"\n  Complexity: {'COMPLEX' if master_plan.is_complex else 'SIMPLE'}")
        print(f"  Reasoning: {master_plan.complexity_reasoning}")
        print(f"  Execution Mode: {master_plan.execution_mode}")

        if master_plan.is_complex:
            print(f"  Subtasks: {len(master_plan.subtasks)}")
            for subtask in master_plan.subtasks:
                print(f"    - [{subtask.priority}] {subtask.description}")

        # Convert to dict for state (LangGraph requires JSON-serializable)
        return {
            "execution_mode": master_plan.execution_mode,
            "master_plan": master_plan.dict(),
            "current_subtask_index": 0,
            "subtask_results": {}
        }

    except Exception as e:
        print(f"  Warning: Master planning failed, using simple mode: {e}")
        # Fallback: treat as simple query
        return {
            "execution_mode": "simple",
            "master_plan": None,
            "current_subtask_index": 0,
            "subtask_results": {}
        }
```

### Task 4: Create Master Planner Prompt

**File:** `src/prompts/master_planner_prompt.py` (NEW)

```python
MASTER_PLANNER_PROMPT = """You are a research complexity analyzer and task decomposer.

## User Query
{query}

## Knowledge Base Status
{kb_summary}
KB Available: {kb_available}

## Your Task

Analyze the query and decide:
1. Is this query **SIMPLE** (single focused question) or **COMPLEX** (multi-faceted, requires decomposition)?
2. If complex, decompose into 2-5 subtasks

## Complexity Criteria

**SIMPLE Query (use existing single-pass research):**
- Single focused question
- Can be answered comprehensively in one research iteration
- Examples:
  - "What is LangGraph?"
  - "How does ChromaDB work?"
  - "最新のGPT-4の性能について"

**COMPLEX Query (requires hierarchical decomposition):**
- Multiple questions or aspects (e.g., "Compare X and Y", "Explain history, present, and future")
- Requires deep analysis ("包括的に", "詳しく", "徹底的に")
- Spans multiple domains (technical + social, history + future, etc.)
- Explicitly asks for comprehensive coverage
- Length > 100 characters (heuristic)
- Examples:
  - "Compare LangGraph and AutoGPT in terms of architecture and use cases"
  - "日本のAI研究の歴史から現在、そして今後の展望について包括的に"
  - "Explain the technical architecture, business model, and social impact of ChatGPT"

## Subtask Decomposition Strategies

If complex, use one of these strategies:

1. **Temporal Decomposition:**
   - Query: "History and future of X"
   - Subtasks: [Historical background, Current state, Future prospects]

2. **Aspect-Based Decomposition:**
   - Query: "Comprehensive analysis of X"
   - Subtasks: [Technical aspects, Business aspects, Social impact]

3. **Comparative Decomposition:**
   - Query: "Compare A and B"
   - Subtasks: [A's characteristics, B's characteristics, Comparison]

4. **Sequential Decomposition:**
   - Query: "How to implement X"
   - Subtasks: [Prerequisites, Implementation steps, Best practices]

5. **Topic-Focused Decomposition:**
   - Query with "特に...について詳しく"
   - Subtasks: [General overview, Deep dive on specific topic 1, Deep dive on specific topic 2]

## Subtask Design Guidelines

Each subtask should:
- Be **self-contained** (can be researched independently)
- Have **clear focus** (specific aspect or question)
- Be **manageable** (not too broad)
- Have **clear priority** (execution order)
- Specify **dependencies** (if one subtask needs results from another)
- Have **importance score** (for resource allocation)

Target: 2-5 subtasks
- Too few (1): Not worth decomposing
- Too many (6+): Over-decomposed, execution overhead

## Output Format

Provide:
1. **is_complex** (boolean): true if hierarchical decomposition needed
2. **complexity_reasoning** (string): Explain why complex or simple
3. **execution_mode** (string): "simple" or "hierarchical"
4. **subtasks** (list): Empty if simple, 2-5 subtasks if complex
5. **overall_strategy** (string): High-level approach

## Examples

**Example 1: Simple Query**
```
Query: "What is LangGraph?"

Output:
{
  "is_complex": false,
  "complexity_reasoning": "Single focused question about one concept. Can be answered comprehensively in one research pass.",
  "execution_mode": "simple",
  "subtasks": [],
  "overall_strategy": "Research LangGraph definition, architecture, and use cases using existing single-pass flow."
}
```

**Example 2: Complex Query (Comparison)**
```
Query: "Compare LangGraph and AutoGPT in terms of architecture and use cases"

Output:
{
  "is_complex": true,
  "complexity_reasoning": "Query requires comparison of two frameworks across multiple dimensions (architecture, use cases). Needs systematic decomposition for comprehensive coverage.",
  "execution_mode": "hierarchical",
  "subtasks": [
    {
      "subtask_id": "task_1",
      "description": "Research LangGraph architecture and core design principles",
      "focus_area": "LangGraph technical architecture",
      "priority": 1,
      "dependencies": [],
      "estimated_importance": 0.9
    },
    {
      "subtask_id": "task_2",
      "description": "Research AutoGPT architecture and core design principles",
      "focus_area": "AutoGPT technical architecture",
      "priority": 2,
      "dependencies": [],
      "estimated_importance": 0.9
    },
    {
      "subtask_id": "task_3",
      "description": "Identify typical use cases and applications for LangGraph",
      "focus_area": "LangGraph use cases",
      "priority": 3,
      "dependencies": ["task_1"],
      "estimated_importance": 0.8
    },
    {
      "subtask_id": "task_4",
      "description": "Identify typical use cases and applications for AutoGPT",
      "focus_area": "AutoGPT use cases",
      "priority": 4,
      "dependencies": ["task_2"],
      "estimated_importance": 0.8
    },
    {
      "subtask_id": "task_5",
      "description": "Compare and contrast the two frameworks based on gathered information",
      "focus_area": "Comparative analysis",
      "priority": 5,
      "dependencies": ["task_1", "task_2", "task_3", "task_4"],
      "estimated_importance": 1.0
    }
  ],
  "overall_strategy": "Systematic comparison: research each framework independently (architecture, use cases), then synthesize comparison. Task 5 depends on all prior tasks for comprehensive comparison."
}
```

**Example 3: Complex Query (Japanese, Multi-temporal)**
```
Query: "日本のAI研究の歴史、現状、そして今後の展望について包括的に調べてください"

Output:
{
  "is_complex": true,
  "complexity_reasoning": "Query explicitly requests comprehensive (包括的) coverage across three time periods (history, present, future). Requires temporal decomposition for deep analysis of each period.",
  "execution_mode": "hierarchical",
  "subtasks": [
    {
      "subtask_id": "task_1",
      "description": "日本のAI研究の歴史的背景と発展（1950年代〜1990年代）",
      "focus_area": "歴史的背景",
      "priority": 1,
      "dependencies": [],
      "estimated_importance": 0.9
    },
    {
      "subtask_id": "task_2",
      "description": "日本の現代AI研究の動向と主要プロジェクト（2000年代〜現在）",
      "focus_area": "現状分析",
      "priority": 2,
      "dependencies": ["task_1"],
      "estimated_importance": 1.0
    },
    {
      "subtask_id": "task_3",
      "description": "日本のAI研究の今後の展望と課題",
      "focus_area": "未来予測",
      "priority": 3,
      "dependencies": ["task_1", "task_2"],
      "estimated_importance": 0.9
    }
  ],
  "overall_strategy": "Temporal decomposition: Historical foundation → Current state → Future prospects. Each period gets thorough research, then synthesized into comprehensive report."
}
```

Now analyze the user's query and create the Master Plan.
"""
```

### Task 5: Create Subtask Router

**File:** `src/nodes/subtask_router.py` (NEW)

```python
def subtask_router(state):
    """
    Routes execution based on Master Plan mode

    Returns:
    - "simple" → Use existing Strategic Planner flow
    - "execute_subtask" → Execute next subtask in hierarchical mode
    - "synthesize" → All subtasks complete, synthesize results
    """
    print("---SUBTASK ROUTER---")

    execution_mode = state.get("execution_mode", "simple")

    if execution_mode == "simple":
        print("  Mode: SIMPLE - using existing flow")
        return "simple"

    # Hierarchical mode
    master_plan = state.get("master_plan")
    if not master_plan:
        print("  Warning: Hierarchical mode but no master plan, falling back to simple")
        return "simple"

    current_index = state.get("current_subtask_index", 0)
    total_subtasks = len(master_plan["subtasks"])

    if current_index < total_subtasks:
        print(f"  Mode: HIERARCHICAL - executing subtask {current_index + 1}/{total_subtasks}")
        return "execute_subtask"
    else:
        print(f"  Mode: HIERARCHICAL - all {total_subtasks} subtasks complete, synthesizing")
        return "synthesize"
```

### Task 6: Create Subtask Executor

**File:** `src/nodes/subtask_executor.py` (NEW)

```python
def subtask_executor(state):
    """
    Prepares state for executing a single subtask

    Extracts current subtask from Master Plan and sets up context
    for Strategic Planner to execute this specific subtask
    """
    print("---SUBTASK EXECUTOR---")

    master_plan = state["master_plan"]
    current_index = state["current_subtask_index"]
    subtasks = master_plan["subtasks"]

    if current_index >= len(subtasks):
        print("  Error: No more subtasks to execute")
        return {}

    current_subtask = subtasks[current_index]

    print(f"\n  Subtask {current_index + 1}/{len(subtasks)}")
    print(f"  ID: {current_subtask['subtask_id']}")
    print(f"  Description: {current_subtask['description']}")
    print(f"  Focus: {current_subtask['focus_area']}")
    print(f"  Priority: {current_subtask['priority']}")
    print(f"  Importance: {current_subtask['estimated_importance']}\n")

    # Prepare subtask-specific query
    # The Strategic Planner will receive this focused query instead of original
    subtask_query = f"{current_subtask['description']} (Focus: {current_subtask['focus_area']})"

    return {
        "current_subtask_id": current_subtask["subtask_id"],
        "query": subtask_query,  # Override query for this subtask
        "loop_count": 0,  # Reset loop counter for this subtask
        # Clear previous subtask's results
        "search_results": [],
        "rag_results": [],
        "analyzed_data": []
    }
```

### Task 7: Update Graph Structure

**File:** `src/graph.py`

**Additions:**
```python
from src.nodes.master_planner_node import master_planner
from src.nodes.subtask_router import subtask_router
from src.nodes.subtask_executor import subtask_executor

# Add new nodes
workflow.add_node("master_planner", master_planner)
workflow.add_node("subtask_router", subtask_router)
workflow.add_node("subtask_executor", subtask_executor)

# Update entry point
workflow.set_entry_point("master_planner")  # Changed from "planner"

# Add routing after master planner
workflow.add_conditional_edges(
    "master_planner",
    subtask_router,
    {
        "simple": "planner",  # Existing flow
        "execute_subtask": "subtask_executor",
        "synthesize": "synthesizer"
    }
)

# Subtask execution flow
workflow.add_edge("subtask_executor", "planner")

# After evaluator, check if more subtasks
def post_evaluator_router(state):
    execution_mode = state.get("execution_mode", "simple")

    if execution_mode == "simple":
        # Use existing router logic
        loop_count = state.get("loop_count", 0)
        if "sufficient" in state["evaluation"].lower() or loop_count >= 2:
            return "synthesizer"
        else:
            return "planner"

    # Hierarchical mode: save subtask result and check if more subtasks
    # (We'll implement result saving in Task 8)
    current_index = state.get("current_subtask_index", 0)
    master_plan = state.get("master_plan")

    if master_plan and current_index + 1 < len(master_plan["subtasks"]):
        return "next_subtask"
    else:
        return "synthesizer"

workflow.add_conditional_edges(
    "evaluator",
    post_evaluator_router,
    {
        "planner": "planner",  # Simple mode loop
        "next_subtask": "subtask_router",  # Hierarchical mode: next subtask
        "synthesizer": "synthesizer"
    }
)
```

### Task 8: Implement Subtask Result Aggregation

**File:** `src/nodes/subtask_result_aggregator.py` (NEW)

```python
def save_subtask_result(state):
    """
    Saves current subtask result before moving to next subtask

    Stores analyzed_data under subtask_id in subtask_results
    """
    print("---SAVE SUBTASK RESULT---")

    current_subtask_id = state.get("current_subtask_id")
    analyzed_data = state.get("analyzed_data", [])
    subtask_results = state.get("subtask_results", {})

    if current_subtask_id:
        # Save this subtask's analysis
        subtask_results[current_subtask_id] = analyzed_data
        print(f"  Saved results for {current_subtask_id}")

    # Increment subtask index
    current_index = state.get("current_subtask_index", 0)
    new_index = current_index + 1

    return {
        "subtask_results": subtask_results,
        "current_subtask_index": new_index
    }
```

**Update graph:**
```python
# Insert result aggregation before routing to next subtask
workflow.add_node("save_subtask_result", save_subtask_result)

# Modify post_evaluator_router to save results first
# (Update edge: evaluator → save_subtask_result → subtask_router)
```

### Task 9: Update Synthesizer for Multi-Subtask Mode

**File:** `src/nodes/synthesizer_node.py`

**Modify to handle hierarchical results:**
```python
def synthesizer_node(state):
    print("---SYNTHESIZER---")
    model = get_synthesizer_model()

    original_query = state.get("query", "")
    execution_mode = state.get("execution_mode", "simple")

    if execution_mode == "hierarchical":
        # Multi-subtask synthesis
        master_plan = state.get("master_plan", {})
        subtask_results = state.get("subtask_results", {})

        print(f"  Mode: HIERARCHICAL")
        print(f"  Subtasks completed: {len(subtask_results)}")

        # Use hierarchical synthesis prompt
        prompt = HIERARCHICAL_SYNTHESIZER_PROMPT.format(
            original_query=original_query,
            master_plan=master_plan,
            subtask_results=subtask_results
        )

    else:
        # Simple mode (existing behavior)
        print(f"  Mode: SIMPLE")
        # ... existing synthesis code ...

    message = model.invoke(prompt)
    print("  Report generated successfully")

    return {"report": message.content}
```

### Task 10: Create Hierarchical Synthesizer Prompt

**File:** `src/prompts/synthesizer_prompt.py`

**Add:**
```python
HIERARCHICAL_SYNTHESIZER_PROMPT = """You are a hierarchical report synthesizer.

## Original User Query
{original_query}

## Master Plan Executed
{master_plan}

This shows how the query was decomposed into subtasks.

## Subtask Results
{subtask_results}

Each subtask was researched independently. Your job is to synthesize these into a unified, comprehensive report.

## Your Task

Create a comprehensive final report that:

1. **Integrates all subtask findings** into a cohesive narrative
2. **Follows the logical structure** suggested by the subtask decomposition
3. **Identifies cross-subtask insights** and connections
4. **Addresses the original query** comprehensively
5. **Maintains clear organization** with sections per subtask or logical grouping

## Report Structure

Suggested structure (adapt based on subtasks):

**[Title Based on Original Query]**

**Summary**
Brief overview of key findings across all subtasks

**[Section per Subtask or Logical Grouping]**
Synthesize findings from related subtasks
Include specific details and evidence
Note connections to other sections

**Synthesis & Insights**
Cross-cutting insights
How subtasks relate to each other
Overall picture emerging from all research

**Conclusion**
Final answer to original query
Key takeaways

**Sources**
Note which subtasks used RAG vs web sources

Generate the comprehensive report now:
"""
```

## Testing Plan

### Unit Tests

**Test 1: Schema Validation**
```python
def test_master_plan_schema():
    plan = MasterPlan(
        is_complex=False,
        complexity_reasoning="Simple query",
        execution_mode="simple",
        subtasks=[],
        overall_strategy="Single-pass research"
    )
    assert plan.is_complex == False
    assert len(plan.subtasks) == 0
```

**Test 2: Simple Query (Regression Test)**
```python
def test_simple_query_unchanged():
    """Ensure simple queries work exactly as before"""
    query = "What is LangGraph?"

    # Execute graph
    result = app.invoke({"query": query})

    # Should use simple mode
    assert result["execution_mode"] == "simple"
    assert result["master_plan"] is None or not result["master_plan"]["is_complex"]

    # Should have final report
    assert "report" in result
    assert len(result["report"]) > 100
```

**Test 3: Complex Query Decomposition**
```python
def test_complex_query_decomposition():
    """Test that complex queries get decomposed"""
    query = "Compare LangGraph and AutoGPT in terms of architecture and use cases"

    result = app.invoke({"query": query})

    # Should use hierarchical mode
    assert result["execution_mode"] == "hierarchical"
    assert result["master_plan"]["is_complex"] == True

    # Should have 2-5 subtasks
    subtasks = result["master_plan"]["subtasks"]
    assert 2 <= len(subtasks) <= 5

    # Should have executed all subtasks
    assert len(result["subtask_results"]) == len(subtasks)

    # Should have final report
    assert "report" in result
```

### Integration Tests

**Test 4: End-to-End Hierarchical Execution**
```python
def test_hierarchical_execution_e2e():
    query = "日本のAI研究の歴史、現状、未来について"

    result = app.invoke({"query": query})

    # Verify hierarchical mode used
    assert result["execution_mode"] == "hierarchical"

    # Verify subtasks were created and executed
    master_plan = result["master_plan"]
    assert master_plan["is_complex"] == True

    subtask_count = len(master_plan["subtasks"])
    assert subtask_count >= 2

    # Verify each subtask was executed
    assert len(result["subtask_results"]) == subtask_count

    # Verify report synthesizes all subtasks
    report = result["report"]
    assert len(report) > 500  # Substantial report
    # Check that report mentions key temporal aspects
    assert any(keyword in report for keyword in ["歴史", "現状", "未来"])
```

### Manual Testing Checklist

- [ ] Simple query: "What is ChromaDB?" → Simple mode, report generated
- [ ] Complex query: "Compare LangGraph and LangChain" → Hierarchical mode, 3-5 subtasks, comprehensive report
- [ ] Japanese complex query → Proper decomposition and synthesis
- [ ] Check LangSmith traces → Verify subtask execution flow
- [ ] Check console output → Clear logging of mode and subtasks

## Deployment Checklist

Before merging to main:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing complete
- [ ] No regression in simple queries (run existing test suite)
- [ ] Documentation updated (README.md, CLAUDE.md)
- [ ] Code reviewed
- [ ] LangSmith tracing verified

## Rollback Plan

If Phase 1 causes issues:

1. **Feature flag:** Add `ENABLE_HIERARCHICAL=False` env variable
2. **Graceful degradation:** Master Planner always returns `execution_mode="simple"`
3. **Full rollback:** Revert to previous graph structure

## Next Steps After Phase 1

Once Phase 1 is stable:

1. ✅ Gather user feedback on subtask decomposition quality
2. ✅ Measure performance (latency, cost per complex query)
3. ✅ Identify improvement areas
4. 📋 Begin Phase 2 planning (Depth Evaluation)

---

**Document Version:** 1.0
**Ready to Implement:** Yes
**Estimated Completion:** 2-3 days
