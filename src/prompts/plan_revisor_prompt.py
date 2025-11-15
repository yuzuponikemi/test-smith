"""
Plan Revisor Prompt for Phase 4: Dynamic Replanning

Analyzes subtask execution results and determines if the Master Plan should be
revised to add new subtasks, adjust priorities, or change scope based on discoveries.
"""

PLAN_REVISOR_PROMPT = """You are a research plan revisor that analyzes discoveries and adapts the research strategy.

## Context

### Original User Query
{original_query}

### Current Master Plan
{master_plan}

**Total Subtasks in Plan:** {total_subtasks}
**Completed Subtasks:** {completed_subtasks}
**Remaining Subtasks:** {remaining_subtasks}

### Just Completed Subtask
**ID:** {current_subtask_id}
**Description:** {current_subtask_description}
**Focus Area:** {current_subtask_focus}
**Importance:** {current_subtask_importance}

### Research Findings from This Subtask
{subtask_findings}

### Depth Evaluation
{depth_evaluation}

### Revision Status
**Revisions Made So Far:** {revision_count}/{max_revisions}
**Total Subtasks So Far:** {total_subtasks}/{max_total_subtasks}

## Your Task

Analyze the research findings and determine if the Master Plan needs revision.

### Revision Triggers

Consider revising the plan if you detect:

1. **NEW_TOPIC**: Important related topic discovered that's NOT covered by existing subtasks
   - Example: Research on "Japanese AI history" reveals "Fifth Generation Computer Project had major international impact" but no subtask covers international reactions
   - Criteria: Topic is highly relevant AND important AND not already planned

2. **SCOPE_ADJUSTMENT**: Current scope is too narrow or too broad
   - Too narrow: Missing critical aspects of the query
   - Too broad: Subtasks are unfocused, duplicating work
   - Criteria: Coverage gaps OR inefficient task distribution

3. **CONTRADICTION**: Conflicting information discovered that needs resolution
   - Example: Different sources give contradictory dates or facts
   - Criteria: Contradictions are important AND need dedicated research to resolve

4. **IMPORTANCE_SHIFT**: Unexpected importance of certain aspects
   - Example: A subtask marked low importance reveals critical insights
   - Criteria: Actual importance significantly differs from estimated importance

5. **NONE**: No revision needed
   - Findings are within expected scope
   - Existing subtasks already cover related areas
   - Low importance discovery
   - Already at revision limits

### Revision Guidelines

**DO Revise If:**
- ✓ Discovery is **important** (would significantly improve final report)
- ✓ Discovery is **NOT covered** by existing pending subtasks
- ✓ Within revision budget (revision_count < max_revisions)
- ✓ Within subtask budget (total_subtasks + new_subtasks ≤ max_total_subtasks)
- ✓ Clear **actionable** subtasks can be defined

**DON'T Revise If:**
- ✗ Already at max revisions (safety limit)
- ✗ Already at max total subtasks (cost control)
- ✗ Discovery is tangentially related (not core to user query)
- ✗ Existing pending subtasks already cover this area
- ✗ Discovery is interesting but low importance
- ✗ Too vague to define concrete subtasks

### Output Format

Provide a PlanRevision with:

1. **should_revise** (bool): True if revision is recommended
2. **revision_reasoning** (str): Detailed explanation
3. **trigger_type** (str): One of: "new_topic", "scope_adjustment", "contradiction", "importance_shift", "none"
4. **new_subtasks** (list): Subtasks to add (empty if no revision)
5. **removed_subtasks** (list): Subtask IDs to skip (empty if no revision)
6. **priority_changes** (dict): subtask_id → new_priority (empty if no revision)
7. **estimated_impact** (str): How this improves the final report

## Examples

### Example 1: Revision Needed (New Topic Discovered)

**Findings:** "Research on Japanese AI history (1950s-1990s) revealed that the Fifth Generation Computer Project (1982-1992) had significant international impact, influencing European AI initiatives like ESPRIT and causing concern in the US about Japanese technological dominance."

**Existing Subtasks:**
- task_1: Historical background (COMPLETED)
- task_2: Current state (PENDING)
- task_3: Future prospects (PENDING)

**Analysis:** The international impact is highly relevant but not covered by existing subtasks.

**Output:**
```json
{{
  "should_revise": true,
  "revision_reasoning": "The Fifth Generation Computer Project's international impact is a significant discovery that deserves dedicated research. This aspect is important for understanding Japan's AI history comprehensively, but is not covered by existing subtasks (task_2 focuses on current state, task_3 on future). The discovery is concrete enough to define actionable subtasks. We are within budget (0/3 revisions, 6/20 subtasks).",
  "trigger_type": "new_topic",
  "new_subtasks": [
    {{
      "subtask_id": "task_4",
      "parent_id": null,
      "depth": 0,
      "description": "International reactions and impact of Japan's Fifth Generation Computer Project",
      "focus_area": "International AI competition and collaboration",
      "priority": 4,
      "dependencies": ["task_1"],
      "estimated_importance": 0.85
    }},
    {{
      "subtask_id": "task_5",
      "parent_id": null,
      "depth": 0,
      "description": "Comparison with European and US AI initiatives in the 1980s",
      "focus_area": "Comparative international AI development",
      "priority": 5,
      "dependencies": ["task_4"],
      "estimated_importance": 0.75
    }}
  ],
  "removed_subtasks": [],
  "priority_changes": {{}},
  "estimated_impact": "Adding these subtasks will provide crucial context about Japan's AI history in a global perspective, making the final report more comprehensive and addressing the international dimension that emerged as significant from the research."
}}
```

### Example 2: No Revision Needed (Already Covered)

**Findings:** "Research on LangGraph architecture revealed it uses state machines and supports multi-agent systems."

**Existing Subtasks:**
- task_1: LangGraph architecture (COMPLETED)
- task_2: LangGraph use cases (PENDING)
- task_3: AutoGPT architecture (PENDING)
- task_4: Comparison (PENDING)

**Analysis:** Multi-agent systems are interesting but task_2 (use cases) will naturally cover this.

**Output:**
```json
{{
  "should_revise": false,
  "revision_reasoning": "The discovery about multi-agent systems support is valuable, but it will naturally be covered by task_2 (use cases) which is still pending. No need to create a separate subtask. The finding enhances our understanding but doesn't require plan adjustment.",
  "trigger_type": "none",
  "new_subtasks": [],
  "removed_subtasks": [],
  "priority_changes": {{}},
  "estimated_impact": "No revision needed - existing subtasks provide adequate coverage."
}}
```

### Example 3: No Revision (At Revision Limit)

**Findings:** "Discovered that quantum computing may impact AI development."

**Revision Status:** 3/3 revisions used

**Output:**
```json
{{
  "should_revise": false,
  "revision_reasoning": "While quantum computing's impact on AI is an interesting discovery, we have reached the maximum revision limit (3/3). To maintain cost control and prevent scope creep, we should not add more subtasks. This topic could be mentioned briefly in the 'Future Prospects' subtask if relevant, but doesn't warrant a separate revision.",
  "trigger_type": "none",
  "new_subtasks": [],
  "removed_subtasks": [],
  "priority_changes": {{}},
  "estimated_impact": "No revision - at safety limit. Existing subtasks should provide comprehensive coverage."
}}
```

### Example 4: Revision Needed (Importance Shift)

**Findings:** "Research on technical architecture revealed that security considerations are critical and much more complex than expected, with 12 major vulnerabilities discovered in similar systems."

**Existing Subtasks:**
- task_1: Technical architecture (COMPLETED)
- task_2: Performance benchmarks (PENDING - priority 2, importance 0.6)
- task_3: Integration guide (PENDING - priority 3, importance 0.5)

**Analysis:** Security is more important than initially estimated.

**Output:**
```json
{{
  "should_revise": true,
  "revision_reasoning": "Security vulnerabilities are more critical than initially estimated. The discovery of 12 major vulnerabilities in similar systems suggests this deserves higher priority and possibly a dedicated subtask. We should add a security-focused subtask and increase priority of security-related work.",
  "trigger_type": "importance_shift",
  "new_subtasks": [
    {{
      "subtask_id": "task_4",
      "parent_id": null,
      "depth": 0,
      "description": "Security architecture and vulnerability analysis",
      "focus_area": "Security and threat modeling",
      "priority": 2,
      "dependencies": ["task_1"],
      "estimated_importance": 0.95
    }}
  ],
  "removed_subtasks": [],
  "priority_changes": {{
    "task_2": 3,
    "task_3": 4
  }},
  "estimated_impact": "Elevating security analysis will provide critical insights for users evaluating this system for production use, significantly improving the practical value of the final report."
}}
```

## Now Analyze the Current Subtask Results

Based on the findings above, determine if the Master Plan needs revision.

Think through:
1. What significant discoveries were made?
2. Are these discoveries covered by existing pending subtasks?
3. Is the discovery important enough to warrant revision?
4. Are we within budget constraints?
5. Can we define concrete, actionable new subtasks?

Provide your PlanRevision analysis:
"""
