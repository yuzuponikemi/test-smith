from src.config.research_depth import get_depth_config
from src.models import get_master_planner_model
from src.prompts.master_planner_prompt import MASTER_PLANNER_PROMPT
from src.schemas import MasterPlan
from src.utils.logging_utils import print_node_header


def _get_depth_guidance(research_depth: str) -> str:
    """Generate depth-specific guidance for subtask generation."""
    guidance_map = {
        "quick": """**Quick Research Mode**
- Target: 1-2 subtasks (minimum 1)
- Focus: Fast, focused research on the core question
- Create a single subtask that captures the main research goal""",
        "standard": """**Standard Research Mode**
- Target: 2-5 subtasks
- Focus: Balanced coverage with good depth
- Decompose into meaningful, independent subtasks
- Each subtask should address a distinct aspect""",
        "deep": """**Deep Research Mode**
- Target: 5-10 subtasks
- Focus: Thorough investigation with multiple perspectives
- Decompose into finer-grained subtasks for detailed analysis
- Include related aspects that provide context
- Consider historical, current, and future dimensions""",
        "comprehensive": """**Comprehensive Research Mode**
- Target: 10-20 subtasks
- Focus: Exhaustive, multi-dimensional coverage
- Decompose into many specific subtasks covering ALL relevant aspects
- Include: technical, historical, social, economic, practical, theoretical dimensions
- Cover: background, current state, trends, challenges, opportunities, future outlook
- Every significant aspect deserves its own subtask
- This is the MOST THOROUGH mode - err on the side of more subtasks""",
    }
    return guidance_map.get(research_depth, guidance_map["standard"])


def _create_default_subtask(query: str) -> dict:
    """Create a default subtask when LLM fails or returns no subtasks."""
    from src.schemas import SubTask

    return SubTask(
        subtask_id="task_1",
        parent_id=None,
        depth=0,
        description=f"Research and analyze: {query}",
        focus_area="General comprehensive research",
        priority=1,
        dependencies=[],
        estimated_importance=1.0,
    ).model_dump()


def master_planner(state):
    """
    Master Planner - Creates Master Plan with subtask decomposition

    Always generates at least 1 subtask for unified workflow.
    All queries go through the hierarchical flow (Writer Graph).

    v3.0: Unified architecture - no more simple/hierarchical split
    """
    print_node_header("MASTER PLANNER")

    query = state["query"]
    research_depth = state.get("research_depth", "standard")
    print(f"  Analyzing query: {query[:100]}...")
    print(f"  Research depth: {research_depth}")

    # Get KB metadata for context (reuse existing function from Strategic Planner)
    from src.nodes.planner_node import check_kb_contents

    kb_info = check_kb_contents()

    # Get depth-specific guidance
    depth_guidance = _get_depth_guidance(research_depth)

    # Invoke LLM with structured output (using command-r for better structured output)
    model = get_master_planner_model()
    structured_llm = model.with_structured_output(MasterPlan)

    prompt = MASTER_PLANNER_PROMPT.format(
        query=query,
        kb_summary=kb_info["summary"],
        kb_available=kb_info["available"],
        research_depth=research_depth,
        depth_guidance=depth_guidance,
    )

    try:
        master_plan = structured_llm.invoke(prompt)

        # Ensure at least 1 subtask exists (unified architecture)
        subtasks_list = [s.model_dump() for s in master_plan.subtasks]
        if len(subtasks_list) == 0:
            print("\n  ⚠ No subtasks generated, creating default subtask")
            subtasks_list = [_create_default_subtask(query)]

        # Always use hierarchical mode (unified architecture)
        print("\n  ✓ Analysis complete")
        print(f"  Reasoning: {master_plan.complexity_reasoning[:200]}...")
        print("  Execution Mode: hierarchical (unified)")
        print(f"\n  Subtasks Generated: {len(subtasks_list)}")

        for subtask in subtasks_list:
            deps = (
                f" (depends: {subtask.get('dependencies', [])})"
                if subtask.get("dependencies")
                else ""
            )
            desc = subtask.get("description", "")[:80]
            print(
                f"    {subtask.get('priority', 1)}. [{subtask.get('subtask_id', 'unknown')}] {desc}...{deps}"
            )

        print(f"\n  Overall Strategy: {master_plan.overall_strategy[:200]}...\n")

        # Get depth config for budget-aware settings
        depth_config = get_depth_config(state.get("research_depth", "standard"))

        # Build master plan dict
        master_plan_dict = {
            "is_complex": True,  # Always true in unified architecture
            "complexity_reasoning": master_plan.complexity_reasoning,
            "execution_mode": "hierarchical",
            "subtasks": subtasks_list,
            "overall_strategy": master_plan.overall_strategy,
        }

        # Convert to dict for state (LangGraph requires JSON-serializable types)
        return {
            "execution_mode": "hierarchical",  # Always hierarchical
            "master_plan": master_plan_dict,
            "current_subtask_index": 0,
            "current_subtask_id": "",
            "subtask_results": {},
            # Phase 2 fields
            "max_depth": 2,  # Maximum recursion depth for Phase 2-beta
            "subtask_evaluations": {},
            # Phase 4 fields (Dynamic Replanning)
            "revision_count": 0,
            "plan_revisions": [],
            "max_revisions": 3,  # Maximum allowed plan revisions
            "max_total_subtasks": depth_config.max_subtasks,  # Based on research depth
            "revision_triggers": [],
            # Phase 4.1 fields (Budget-Aware Control)
            "node_execution_count": 0,  # Track recursion usage
            "recursion_limit": depth_config.recursion_limit,  # Based on research depth
            "budget_warnings": [],
        }

    except Exception as e:
        print("  ⚠ Warning: Master planning failed, using default subtask")
        print(f"  Error: {e}")

        # Get depth config for budget-aware settings
        depth_config = get_depth_config(state.get("research_depth", "standard"))

        # Fallback: create default subtask (still hierarchical)
        master_plan_dict = {
            "is_complex": True,
            "complexity_reasoning": f"Fallback due to error: {e}",
            "execution_mode": "hierarchical",
            "subtasks": [_create_default_subtask(query)],
            "overall_strategy": "Single-pass comprehensive research",
        }

        return {
            "execution_mode": "hierarchical",  # Always hierarchical
            "master_plan": master_plan_dict,
            "current_subtask_index": 0,
            "current_subtask_id": "",
            "subtask_results": {},
            # Phase 2 fields
            "max_depth": 2,
            "subtask_evaluations": {},
            # Phase 4 fields
            "revision_count": 0,
            "plan_revisions": [],
            "max_revisions": 3,
            "max_total_subtasks": depth_config.max_subtasks,
            "revision_triggers": [],
            # Phase 4.1 fields
            "node_execution_count": 0,
            "recursion_limit": depth_config.recursion_limit,
            "budget_warnings": [],
        }
