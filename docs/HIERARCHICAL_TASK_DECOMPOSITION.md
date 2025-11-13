# Hierarchical Task Decomposition - Design Document

**Status:** ✅ Phase 3 (v2.0) COMPLETE - Full recursive drill-down execution working
**Target:** DeepResearch-style deep-dive analysis with recursive task decomposition
**Last Updated:** 2025-11-12

## Vision

Transform Test-Smith from a single-query research system into a **hierarchical deep-dive research platform** that can:

1. **Decompose complex topics** into manageable subtasks
2. **Execute subtasks** with appropriate source allocation (RAG vs web)
3. **Evaluate depth** of each subtask result
4. **Recursively drill down** into areas that need more investigation
5. **Synthesize hierarchically** from subtask results to comprehensive final report

**Inspiration:** DeepResearch - ability to autonomously explore topics in depth, following interesting threads, and building comprehensive understanding.

## Current System Limitations

### What We Have Now (v1.0)

```
User Query
    ↓
Strategic Planner → web_queries + rag_queries
    ↓
Searcher + RAG Retriever (parallel)
    ↓
Analyzer
    ↓
Evaluator → sufficient/insufficient?
    ↓
[Loop max 2 times if insufficient]
    ↓
Synthesizer → Final Report
```

**Limitations:**
- ✗ Single-level planning (no task decomposition)
- ✗ Fixed iteration limit (max 2 loops)
- ✗ No recursive exploration
- ✗ Cannot handle multi-faceted complex queries well
- ✗ All information gathering happens at same depth level

### What We Need (v2.0 - Hierarchical)

**Capabilities:**
- ✓ Automatic detection of complex/multi-faceted queries
- ✓ Hierarchical task decomposition (subtasks)
- ✓ Per-subtask execution and evaluation
- ✓ Recursive drill-down based on evaluation
- ✓ Depth-aware synthesis (subtask → topic → final report)
- ✓ Adaptive exploration (follow interesting threads)

## Architecture Design

### High-Level Flow

```
User Query
    ↓
Master Planner (NEW)
    ├─ Is query complex? → Decompose into subtasks
    └─ Is query simple? → Use current Strategic Planner
    ↓
[IF COMPLEX - Hierarchical Mode]
    ↓
For each Subtask:
    ├─ Strategic Planner → web/rag queries for THIS subtask
    ├─ Searcher + RAG Retriever
    ├─ Analyzer (subtask-focused)
    ├─ Depth Evaluator (NEW)
    │   ├─ Is subtask sufficiently explored?
    │   └─ Does this need drill-down? → Create child subtasks
    └─ [Recursive: If drill-down needed, repeat]
    ↓
Hierarchical Synthesizer (NEW)
    ├─ Synthesize each subtask cluster
    ├─ Synthesize topic-level findings
    └─ Create comprehensive final report
```

### New Components

#### 1. Master Planner

**Purpose:** Detect complexity and decompose into subtasks

**Input:**
- User query
- KB metadata (from existing `check_kb_contents()`)

**Output:**
```python
class MasterPlan(BaseModel):
    is_complex: bool
    complexity_reasoning: str
    execution_mode: Literal["simple", "hierarchical"]
    subtasks: List[SubTask]  # Empty if simple mode
    overall_strategy: str

class SubTask(BaseModel):
    subtask_id: str  # e.g., "task_1", "task_1.1" (hierarchical)
    parent_id: Optional[str]  # For recursive subtasks
    depth: int  # 0 = root, 1 = first decomposition, etc.
    description: str
    focus_area: str  # What aspect this subtask covers
    priority: int  # Execution order (1 = first)
    dependencies: List[str]  # Other subtask_ids that must complete first
    estimated_importance: float  # 0-1 scale
```

**Complexity Detection Criteria:**
- Query contains multiple questions (e.g., "Explain X and Y and compare Z")
- Query asks for comprehensive/deep analysis ("詳しく", "徹底的に", "包括的に")
- Query spans multiple time periods (e.g., "history and future of...")
- Query requires both internal knowledge AND external research
- Query length > 200 characters (heuristic)
- LLM judges complexity > threshold

**Decomposition Strategies:**
1. **Temporal:** Past → Present → Future
2. **Aspect-based:** Technical → Business → Social Impact
3. **Comparative:** Topic A → Topic B → Comparison
4. **Hierarchical:** Overview → Details → Implications
5. **Sequential:** Background → Current State → Challenges → Solutions

#### 2. Depth Evaluator

**Purpose:** Evaluate if subtask is sufficiently explored, or needs drill-down

**Input:**
- Subtask description
- Subtask results (analyzed data)
- Current depth level
- Overall query requirements

**Output:**
```python
class DepthEvaluation(BaseModel):
    is_sufficient: bool  # Is this subtask adequately explored?
    depth_quality: Literal["superficial", "adequate", "deep"]
    drill_down_needed: bool  # Should we create child subtasks?
    drill_down_areas: List[str]  # Specific areas to explore deeper
    reasoning: str

# Example:
# Subtask: "日本のAI黎明期を調査"
# Result: Mentions 1980s AI boom but lacks details
# Evaluation:
#   - is_sufficient: False
#   - drill_down_needed: True
#   - drill_down_areas: ["第五世代コンピュータプロジェクト詳細", "主要研究者と貢献"]
```

**Depth Criteria:**
- **Superficial:** Only general statements, no specifics, lacks evidence
- **Adequate:** Specific facts, some context, answers key questions
- **Deep:** Rich detail, multiple perspectives, well-sourced, nuanced analysis

**Drill-Down Decision:**
- Depth level < max_depth (e.g., 3 levels deep)
- Importance score > threshold
- Current results are superficial BUT topic is important
- Contradictions found that need resolution

#### 3. Hierarchical Synthesizer

**Purpose:** Synthesize results hierarchically (bottom-up)

**Strategy:**
1. **Level N (deepest):** Synthesize leaf subtask results
2. **Level N-1:** Synthesize parent tasks using child syntheses
3. **Level 0:** Create final comprehensive report

**Input:**
- Full subtask tree with results
- Depth evaluations
- Original query

**Output:**
- Structured hierarchical report with sections per subtask
- Cross-subtask insights and connections
- Comprehensive final synthesis

### State Management

**Extended AgentState:**
```python
class HierarchicalAgentState(TypedDict):
    # Original fields
    query: str

    # Hierarchical fields (NEW)
    execution_mode: str  # "simple" or "hierarchical"
    master_plan: Optional[MasterPlan]
    current_subtask: Optional[SubTask]
    subtask_results: dict[str, SubTaskResult]  # subtask_id → result
    subtask_evaluations: dict[str, DepthEvaluation]
    max_depth: int  # Max recursion depth (default: 3)
    current_depth: int

    # Existing fields (per-subtask in hierarchical mode)
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

class SubTaskResult(BaseModel):
    subtask_id: str
    analyzed_data: str
    depth_evaluation: DepthEvaluation
    child_subtasks: List[str]  # IDs of drill-down subtasks
    synthesis: str  # Subtask-level synthesis
```

## Planning Strategy: Static vs Dynamic

### 🎯 Chosen Approach: Static Master Plan (Phase 1-3) → Dynamic Replanning (Phase 4+)

**Philosophy:**
実際のリサーチは動的（調べながら新しい方向を発見）ですが、実装は段階的に。まずは「与えられたテーマを徹底的に調べる」静的プランで価値検証し、その後動的再計画を追加します。

### Static Master Plan (v2.0 - Phase 1-3)

**How it works:**
1. Master Plannerが最初に**一度だけ**全サブタスクを生成
2. 各サブタスクを順次実行
3. Depth Evaluatorは深掘りのみ判断（**新しいサブタスクは作らない**）
4. プランは実行中に変更されない

**メリット:**
- ✅ 実装がシンプル
- ✅ 予測可能なコストと時間
- ✅ 「テーマを徹底的に調べる」に最適
- ✅ 価値検証に適している
- ✅ デバッグしやすい

**デメリット:**
- ✗ 調査中の発見を反映できない
- ✗ スコープ変更ができない
- ✗ 新しい重要トピックが見つかっても追加できない

**例:**
```
Initial Plan: [歴史, 現状, 未来]
    ↓
Execute 歴史 → 発見: "第五世代CPUの国際的影響が大きい"
    ↓
    でも新しいサブタスクは作らない（静的プラン）
    代わりに: 深掘りで対応 → [歴史.1: 国際的影響の詳細]
    ↓
Continue with 現状, 未来
```

### Dynamic Replanning (v2.1+ - Phase 4)

**How it works:**
1. Master Plannerが初期プラン生成
2. サブタスク実行後、**Plan Revisor**が結果を分析
3. 必要に応じて：
   - 新しいサブタスクを追加
   - 優先順位を変更
   - スコープを見直し
4. 更新されたプランで実行継続

**新コンポーネント: Plan Revisor**
```python
class PlanRevision(BaseModel):
    should_revise: bool
    revision_reasoning: str
    new_subtasks: List[SubTask]  # 追加するサブタスク
    removed_subtasks: List[str]  # スキップするサブタスクID
    priority_changes: dict[str, int]  # 優先順位変更
    scope_adjustment: str  # スコープの見直し内容
```

**メリット:**
- ✅ 人間的なリサーチプロセス
- ✅ 調査結果に基づいて適応
- ✅ 重要な発見を逃さない
- ✅ より深く、より関連性の高い結果

**デメリット:**
- ✗ 実装が複雑
- ✗ コスト/時間が予測不可能
- ✗ 無限ループのリスク（制御が必要）
- ✗ デバッグが難しい

**例:**
```
Initial Plan: [歴史, 現状, 未来]
    ↓
Execute 歴史 → 発見: "第五世代CPUの国際的影響が大きい"
    ↓
Plan Revisor: "重要な発見。新しいサブタスク追加を推奨"
    ↓
Updated Plan: [歴史, 現状, 未来, 国際的反応(NEW), 欧州比較(NEW)]
    ↓
Continue with updated plan
```

**Why Phase 4?**
- まず静的版で学習（どんなクエリ？どんな発見がある？）
- ユーザーフィードバックを収集
- 動的再計画のトリガー条件を明確化
- その後、動的機能を追加

## Execution Strategies

### Strategy 1: Breadth-First (Recommended for v2.0)

**Approach:** Complete all subtasks at depth N before drilling down

```
Master Plan: [Task 1, Task 2, Task 3]
    ↓
Execute Task 1 → Evaluate → Needs drill-down? → [Task 1.1, Task 1.2]
Execute Task 2 → Evaluate → Sufficient
Execute Task 3 → Evaluate → Needs drill-down? → [Task 3.1]
    ↓
Execute Task 1.1 → Evaluate → Sufficient
Execute Task 1.2 → Evaluate → Sufficient
Execute Task 3.1 → Evaluate → Needs drill-down? → [Task 3.1.1]
    ↓
Execute Task 3.1.1 → Evaluate → Sufficient
    ↓
Hierarchical Synthesis: Bottom-up
```

**Advantages:**
- ✓ Easier to implement
- ✓ Better parallelization opportunities
- ✓ Clearer progress tracking
- ✓ Natural fit with LangGraph structure

**Disadvantages:**
- ✗ May gather unnecessary information if early results change direction
- ✗ Less "organic" exploration feel

### Strategy 2: Depth-First

**Approach:** Fully explore each subtask branch before moving to next

```
Master Plan: [Task 1, Task 2, Task 3]
    ↓
Execute Task 1 → Needs drill-down
    ├─ Execute Task 1.1 → Sufficient
    └─ Execute Task 1.2 → Needs drill-down
        └─ Execute Task 1.2.1 → Sufficient
    ↓
Execute Task 2 → Sufficient
    ↓
Execute Task 3 → Needs drill-down
    └─ Execute Task 3.1 → Sufficient
    ↓
Synthesis
```

**Advantages:**
- ✓ More focused exploration
- ✓ Can adjust strategy based on deep insights
- ✓ More like human research process

**Disadvantages:**
- ✗ Harder to parallelize
- ✗ May go too deep on less important topics
- ✗ More complex state management

### Strategy 3: Hybrid (Future v3.0)

Adaptive strategy that switches between breadth and depth based on:
- Importance scores
- Available time/resources
- Quality of results so far

## Implementation Roadmap

### Phase 1: Foundation (v2.0-alpha)

**Goal:** Add basic hierarchical capabilities without breaking existing system

**Changes:**
1. Create Master Planner node
   - Detects if query is complex
   - If simple: delegates to current Strategic Planner (no changes)
   - If complex: generates flat list of subtasks (no recursion yet)

2. Add subtask loop in graph
   - Execute subtasks sequentially
   - Each subtask uses existing Strategic Planner → Searcher/RAG → Analyzer → Evaluator

3. Simple multi-subtask synthesis
   - Synthesizer receives multiple analyzed_data entries
   - Synthesize with awareness of subtask structure

**State:** Backward compatible - simple queries work exactly as before

**Testing:**
- Simple query: "What is LangGraph?" → Works as current system
- Complex query: "Compare LangGraph and AutoGPT in terms of architecture and use cases" → Decomposes into 3 subtasks

**✅ COMPLETION STATUS (2025-11-12):**

**Implemented Components:**
- ✅ Master Planner node (`src/nodes/master_planner_node.py`)
- ✅ Subtask Router (`src/nodes/subtask_router.py`)
- ✅ Subtask Executor (`src/nodes/subtask_executor.py`)
- ✅ Subtask Result Aggregator (`src/nodes/subtask_result_aggregator.py`)
- ✅ Hierarchical Synthesizer (extended `src/nodes/synthesizer_node.py`)
- ✅ Extended State Management (`src/graph.py` - AgentState)
- ✅ Schemas (`src/schemas.py` - MasterPlan, SubTask)

**Test Results:**
- ✅ Simple query "What is LangGraph?" - Correctly classified as SIMPLE, uses existing flow
- ✅ Complex query "Compare LangGraph and AutoGPT architectures" - Correctly classified as COMPLEX
  - Generated 5 subtasks with priorities and dependencies
  - All 5 subtasks executed successfully
  - Hierarchical synthesis completed successfully
  - Execution time: 549 seconds (~9 minutes)
  - Report generated: `reports/report_20251112_223544_hierarchical_Compare_LangGraph_and_AutoGPT_architectures.md`

**Known Issues Fixed:**
- 🐛 **Recursion Limit Bug:** Initial implementation hit LangGraph's default recursion limit (25) with 5+ subtasks
  - **Fix:** Increased `recursion_limit` to 100 in `main.py:35`
  - **Status:** ✅ Fixed and verified working

**Known Limitations:**
- ⚠️ No recursion/drill-down yet (Phase 1 only does flat decomposition)
- ⚠️ Dependencies tracked but not enforced in execution order (relies on priority ordering)
- ⚠️ Long execution times for complex queries (5 subtasks = ~9 minutes)

**Next Steps:** ~~Proceed to Phase 2 (Depth Evaluation)~~ ✅ **Phase 2 Complete!**

---

### Phase 2: Depth Evaluation (v2.0-beta) ✅ COMPLETE

**Goal:** Add intelligent depth assessment

**Changes:**
1. Replace simple Evaluator with Depth Evaluator for hierarchical mode
   - Assess depth quality
   - Recommend drill-down areas

2. Add drill-down decision logic
   - If depth < max_depth AND quality = superficial AND important → drill down

3. Single-level recursion (depth = 2 max)
   - Parent subtask can spawn 1 level of child subtasks
   - Child subtasks cannot spawn more (yet)

**✅ COMPLETION STATUS (2025-11-12):**

**Implemented Components:**
- ✅ DepthEvaluation schema (`src/schemas.py`) with quality levels: superficial/adequate/deep
- ✅ Updated SubTask schema with depth tracking (parent_id, depth fields)
- ✅ Depth Evaluator prompt template (`src/prompts/depth_evaluator_prompt.py`)
- ✅ Depth Evaluator node (`src/nodes/depth_evaluator_node.py`)
- ✅ Updated AgentState with Phase 2 fields: max_depth, depth_evaluation, subtask_evaluations
- ✅ Graph routing updates (`src/graph.py`):
  - analyzer_router: Routes hierarchical mode to depth_evaluator
  - depth_evaluator → save_result edge
- ✅ Recursion status calculation in depth evaluator

**Test Results:**
- ✅ Simple query "What is LangGraph?" - Uses regular evaluator (backward compatibility maintained)
- ✅ Complex query "Compare React and Vue frameworks" - Uses depth evaluator
  - Generated 7 subtasks
  - Depth evaluator invoked for each subtask
  - Subtask task_1 evaluation: Depth 0/2, Quality: adequate, Sufficient: True, Drill-down: False
  - Proper routing: analyzer → depth_evaluator → save_result → next subtask
  - No errors during execution

**Known Issues Fixed:**
- 🐛 **Prompt Formatting Bug:** Python f-string expression in DEPTH_EVALUATOR_PROMPT caused ValueError
  - **Fix:** Moved recursion_status calculation to node code, passed as format variable
  - **Status:** ✅ Fixed and verified working

**Known Limitations:**
- ⚠️ Drill-down not yet implemented (Phase 2-beta only evaluates, doesn't create child subtasks)
- ⚠️ No recursive execution yet (will be added in Phase 3)
- ⚠️ max_depth hardcoded to 2 in master_planner_node.py:59

**Next Steps:** ~~Proceed to Phase 3 (Full Recursion with drill-down execution)~~ ✅ **Phase 3 Complete!**

### Phase 3: Full Recursion (v2.0) ✅ COMPLETE

**Goal:** Enable multi-level hierarchical exploration with static planning

**Key Constraint:** 🔒 Master Plan is **static** - created once at the beginning

**Changes:**
1. Remove recursion depth restriction (use configurable max_depth)
2. Implement hierarchical synthesis (bottom-up)
3. Add subtask dependency handling
4. Optimize for breadth-first execution

**Testing:**
- DeepResearch-style query: "日本のAI研究の歴史、現状、そして今後の展望について包括的なレポートを作成してください"
- Should decompose → execute → drill-down → synthesize hierarchically
- Verify depth control (doesn't go infinite)
- Verify Master Plan doesn't change during execution

**Deliverable:**
- ✅ Hierarchical deep-dive research capability
- ✅ "与えられたテーマを徹底的に調べる" システム完成
- ✅ Value proposition validated

**✅ COMPLETION STATUS (2025-11-12):**

**Implemented Components:**
- ✅ Drill-Down Generator node (`src/nodes/drill_down_generator.py`)
  - Creates child SubTasks from drill_down_areas
  - Inserts children into master_plan.subtasks dynamically
  - Respects max_depth limit
- ✅ Updated graph routing (`src/graph.py`):
  - depth_evaluator → drill_down_generator → save_result
- ✅ Enhanced subtask_executor with depth logging
  - Shows parent-child relationships
  - Displays depth level for each subtask
- ✅ Linear execution naturally handles hierarchy
  - Children inserted after parent
  - Execute in order: parent → children → next parent

**Test Results:**
- ✅ Complex query "Compare Python and Ruby programming languages"
  - Generated 5 root subtasks (depth 0)
  - task_1 triggered drill-down: created 2 child subtasks (depth 1)
  - Total subtasks: 5 → 7
  - Children executed before next parent
  - Proper parent tracking: "Parent: task_1 (Depth: 1)"
  - Max depth limit respected

**Key Features:**
- ✓ Automatic drill-down when:
  - Importance ≥ 0.7
  - Depth quality = "superficial"
  - Current depth < max_depth
- ✓ Dynamic subtask insertion
- ✓ Hierarchical execution
- ✓ Depth tracking and logging
- ✓ Max depth enforcement

**Known Limitations:**
- ⚠️ Hierarchical synthesis not yet implemented (children results merged with parent, not synthesized hierarchically)
- ⚠️ No dependency-aware execution optimization (executes by index)
- ⚠️ max_depth still hardcoded to 2 in master_planner_node.py:59

**Next Steps:** Proceed to Phase 4 (Dynamic Replanning) for adaptive master plan evolution

---

### Phase 4: Dynamic Replanning (v2.1) 🔄 ADAPTIVE RESEARCH

**Goal:** Enable adaptive research that responds to discoveries

**Key Innovation:** 🔓 Master Plan becomes **dynamic** - evolves based on findings

**New Component: Plan Revisor**

```python
def plan_revisor_node(state):
    """
    Analyzes subtask results and decides if Master Plan needs updating

    Triggers:
    - Significant unexpected findings
    - Important related topics discovered
    - Contradictions that need resolution
    - Scope too narrow/broad based on results
    """
    current_plan = state["master_plan"]
    subtask_results = state["subtask_results"]

    # Analyze if plan revision is needed
    revision = assess_plan_revision(current_plan, subtask_results)

    if revision.should_revise:
        # Update Master Plan
        updated_plan = apply_revisions(current_plan, revision)
        return {"master_plan": updated_plan}

    return {}
```

**Schema Updates:**
```python
class PlanRevision(BaseModel):
    should_revise: bool
    revision_reasoning: str
    trigger_type: Literal["new_topic", "scope_adjustment", "contradiction", "importance_shift"]
    new_subtasks: List[SubTask]
    removed_subtasks: List[str]  # Skip these
    priority_changes: dict[str, int]
    estimated_impact: str  # How this improves final result
```

**Workflow Changes:**
```
Execute Subtask
    ↓
Depth Evaluator
    ↓
Plan Revisor (NEW)
    ├─ Analyze findings
    ├─ Detect: New important topics? Contradictions? Scope issues?
    └─ Decision: Revise plan? Add subtasks? Adjust priorities?
    ↓
[IF REVISION NEEDED]
    Update Master Plan
    Log revision reasoning
    ↓
Continue with updated plan
```

**Safety Controls:**
- Max revisions per execution (e.g., 3)
- Budget control (max total subtasks)
- Revision approval threshold (importance > 0.7)
- Prevent duplicate subtasks

**Testing:**
```
Query: "日本のAI研究について"
    ↓
Initial Plan: [歴史, 現状, 未来]
    ↓
Execute 歴史 subtask
    → Discovers: "第五世代コンピュータプロジェクトが国際的に大きな影響"
    ↓
Plan Revisor:
    - Trigger: "new_topic" (international impact is significant but not in original plan)
    - Decision: Add new subtasks
    - New subtasks: [国際的反応, 欧州との比較]
    ↓
Updated Plan: [歴史, 現状, 未来, 国際的反応(NEW), 欧州比較(NEW)]
    ↓
Continue execution with richer scope
```

**Expected Benefits:**
- ✅ More human-like research process
- ✅ Follows interesting leads
- ✅ Adapts to discoveries
- ✅ Higher quality, more comprehensive results

**Challenges to Address:**
- ✗ Cost/time unpredictability → Add max_revision and max_subtask limits
- ✗ Infinite loops → Strict termination conditions
- ✗ Scope creep → Revision approval threshold
- ✗ Debugging complexity → Comprehensive logging

---

### Phase 5: Advanced Features (v2.2+)

**Future enhancements:**
1. **Parallel subtask execution:** Execute independent subtasks simultaneously
2. **Adaptive depth:** Adjust max_depth based on time/resource constraints
3. **Importance-based prioritization:** Execute high-priority subtasks first
4. **Cross-subtask insight detection:** Identify connections between subtask findings during execution
5. **Interactive mode:** Let user approve drill-down and revision decisions
6. **Dependency-aware execution:** Automatically optimize execution order based on dependencies
7. **Progress visualization:** Real-time subtask tree with completion status
8. **Multi-agent collaboration:** Specialized agents for different subtask types (technical analyst, social analyst, etc.)

## Technical Considerations

### LangGraph Integration

**Option A: Subgraph per Subtask (Recommended)**
```python
# Create a subgraph for subtask execution
subtask_graph = StateGraph(SubTaskState)
subtask_graph.add_node("strategic_planner", planner)
subtask_graph.add_node("searcher", searcher)
# ... etc

# Main graph orchestrates subtasks
main_graph = StateGraph(HierarchicalAgentState)
main_graph.add_node("master_planner", master_planner)
main_graph.add_node("subtask_executor", subtask_graph)  # Invoke subgraph
main_graph.add_node("hierarchical_synthesizer", hierarchical_synthesizer)
```

**Option B: Conditional Routing in Single Graph**
Use routers to handle hierarchical vs simple mode within one graph

### Performance Optimization

**Challenges:**
- Many subtasks × multiple iterations = lots of LLM calls
- Deep hierarchies can take very long

**Solutions:**
1. **Caching:** Cache subtask results (if same subtask appears in different queries)
2. **Parallelization:** Execute independent subtasks in parallel
3. **Streaming:** Stream intermediate results to user
4. **Budget control:** Set max_subtasks, max_depth, max_iterations per subtask
5. **Smart pruning:** Skip low-importance subtasks if time/cost constrained

### Prompt Engineering

**Critical prompts to develop:**

1. **Master Planner Prompt:**
   - Complexity detection instructions
   - Decomposition strategy selection
   - Subtask generation with clear boundaries

2. **Depth Evaluator Prompt:**
   - Depth quality assessment criteria
   - Drill-down decision framework
   - Specific area identification for deeper exploration

3. **Hierarchical Synthesizer Prompt:**
   - Bottom-up synthesis instructions
   - Cross-subtask connection identification
   - Progressive abstraction from details to high-level insights

### State Persistence

**LangGraph Checkpointing:**
- Current system uses SQLite checkpointing
- Hierarchical mode will have much larger state
- Consider chunking state or using external storage for subtask results

**Recommendation:** Store subtask_results in separate table/collection, reference by ID in main state

## Example Walkthrough

### User Query (Complex)

```
日本のAI研究の歴史から現在、そして今後の展望について、
技術的側面と社会的影響の両面から包括的なレポートを作成してください。
特に、第五世代コンピュータプロジェクトの影響と、
現代のディープラーニングブームとの関連性について詳しく調べてください。
```

### Master Planner Output

```python
MasterPlan(
    is_complex=True,
    complexity_reasoning="Query requires multi-temporal analysis (history → present → future), "
                        "multi-aspect analysis (technical + social), and deep-dive into specific "
                        "topic (5th gen computers). This needs hierarchical decomposition.",
    execution_mode="hierarchical",
    subtasks=[
        SubTask(
            subtask_id="task_1",
            depth=0,
            description="日本のAI研究の歴史的背景（1950-1990年代）",
            focus_area="歴史・技術的側面",
            priority=1,
            dependencies=[],
            estimated_importance=0.9
        ),
        SubTask(
            subtask_id="task_2",
            depth=0,
            description="第五世代コンピュータプロジェクトの詳細分析",
            focus_area="歴史・特定プロジェクト",
            priority=2,
            dependencies=["task_1"],  # Needs historical context
            estimated_importance=1.0  # Explicitly requested
        ),
        SubTask(
            subtask_id="task_3",
            depth=0,
            description="現代の日本のAI研究動向（2000年代〜現在）",
            focus_area="現状・技術的側面",
            priority=3,
            dependencies=["task_1"],
            estimated_importance=0.9
        ),
        SubTask(
            subtask_id="task_4",
            depth=0,
            description="ディープラーニングブームと日本の対応",
            focus_area="現状・技術トレンド",
            priority=4,
            dependencies=["task_3"],
            estimated_importance=1.0  # Explicitly requested
        ),
        SubTask(
            subtask_id="task_5",
            depth=0,
            description="AI技術の社会的影響（過去・現在・未来）",
            focus_area="社会的側面",
            priority=5,
            dependencies=["task_1", "task_3"],
            estimated_importance=0.8
        ),
        SubTask(
            subtask_id="task_6",
            depth=0,
            description="日本のAI研究の今後の展望と課題",
            focus_area="未来・戦略",
            priority=6,
            dependencies=["task_3", "task_4", "task_5"],
            estimated_importance=0.9
        ),
    ],
    overall_strategy="Execute in dependency order. Task_2 and Task_4 are explicitly requested "
                    "deep-dive topics - allocate more resources. Historical context (Task_1) "
                    "should query KB heavily. Current trends (Task_3, Task_4) need web search. "
                    "Future outlook (Task_6) synthesis depends on all prior findings."
)
```

### Execution Flow

**Iteration 1: Task 1 (Historical Background)**

Strategic Planner:
```python
StrategicPlan(
    rag_queries=[
        "日本 AI研究 歴史 1950年代",
        "日本 人工知能 黎明期",
        "初期AIブーム 日本"
    ],
    web_queries=[
        "日本AI研究 歴史 timeline",
    ],
    strategy="Historical topic likely in KB if we have Japanese AI history docs. "
            "Use RAG heavily, web for additional context."
)
```

Depth Evaluator Result:
```python
DepthEvaluation(
    is_sufficient=False,
    depth_quality="superficial",
    drill_down_needed=True,
    drill_down_areas=[
        "具体的な研究機関と研究者",
        "主要な技術的ブレークスルー",
        "政府の支援プログラム"
    ],
    reasoning="Retrieved general timeline but lacks specific details about researchers, "
              "institutions, and breakthrough technologies. Given high importance (0.9) "
              "and explicit user interest in historical context, recommend drill-down."
)
```

**Iteration 2: Drill-Down on Task 1**

New subtasks generated:
```python
task_1_1 = SubTask(subtask_id="task_1.1", parent_id="task_1", depth=1,
                   description="日本の主要AI研究機関と研究者（1950-1990）", ...)
task_1_2 = SubTask(subtask_id="task_1.2", parent_id="task_1", depth=1,
                   description="初期AIブームの技術的ブレークスルー", ...)
```

... (Execute drill-down subtasks)

**Iteration 3-8:** Execute remaining root-level subtasks (task_2 through task_6)

Task_2 (Fifth Gen Computer Project) also triggers drill-down due to explicit user request and superficial initial results.

**Final Synthesis:**

Hierarchical Synthesizer:
1. Synthesizes task_1.1, task_1.2 → task_1 synthesis
2. Synthesizes task_2.1, task_2.2, task_2.3 → task_2 synthesis
3. Synthesizes all root-level tasks → Final comprehensive report

**Final Report Structure:**
```markdown
# 日本のAI研究：歴史・現在・未来の包括的分析

## エグゼクティブサマリー
[High-level synthesis of all findings]

## 第1章：日本のAI研究の歴史的発展（1950-1990年代）
### 1.1 黎明期の研究機関と先駆者たち
[From task_1.1 synthesis]

### 1.2 技術的ブレークスルーと初期AIブーム
[From task_1.2 synthesis]

## 第2章：第五世代コンピュータプロジェクト
### 2.1 プロジェクトの概要と目標
[From task_2.1]

### 2.2 技術的成果と限界
[From task_2.2]

### 2.3 国際的影響と遺産
[From task_2.3]

## 第3章：現代のAI研究動向（2000年代〜現在）
[From task_3]

## 第4章：ディープラーニング革命と日本
### 4.1 ディープラーニングブームの到来
[From task_4]

### 4.2 第五世代プロジェクトとの対比
[Cross-subtask insight from task_2 and task_4]

## 第5章：AI技術の社会的影響
[From task_5]

## 第6章：今後の展望と課題
[From task_6, informed by all previous chapters]

## 結論
[Synthesis of key insights across all sections]

## 情報源
- 内部資料：[KB documents consulted]
- 外部資料：[Web sources consulted]
```

## Success Metrics

**How to measure if hierarchical system is working:**

1. **Query Complexity Handling:**
   - Can handle queries with 3+ sub-questions
   - Properly decomposes multi-faceted queries
   - Doesn't over-decompose simple queries

2. **Depth Quality:**
   - Reports show deeper insights than v1.0
   - Specific details and examples (not just general statements)
   - Follows through on user's specific requests (e.g., "特に...について詳しく")

3. **Resource Efficiency:**
   - Doesn't waste queries on unimportant subtasks
   - Drill-down decisions are justified
   - Total LLM calls < (number_of_subtasks × 10) for reasonable queries

4. **Synthesis Quality:**
   - Cross-subtask insights identified
   - Hierarchical structure is logical
   - No major gaps in coverage

5. **User Satisfaction:**
   - Reports feel comprehensive
   - Depth matches user expectations
   - "DeepResearch-like" quality achieved

## References & Inspiration

- **DeepResearch:** Multi-agent research system with autonomous depth exploration
- **AutoGPT:** Task decomposition and autonomous execution
- **LangGraph Multi-Agent Systems:** Hierarchical agent patterns
- **Tree of Thoughts (ToT):** Hierarchical reasoning framework

## Next Steps

**Immediate:**
1. ✅ Document this design (this file)
2. Review with user and refine based on feedback
3. Create Phase 1 implementation plan with detailed tasks

**Short-term:**
4. Implement Phase 1 (basic hierarchical mode)
5. Test with complex queries
6. Iterate based on results

**Long-term:**
7. Implement Phase 2 & 3 (full recursion)
8. Add advanced features (parallelization, adaptive depth, etc.)
9. Optimize performance and cost

---

**Document Version:** 1.0
**Author:** System design collaboration
**Review Status:** Pending user review
