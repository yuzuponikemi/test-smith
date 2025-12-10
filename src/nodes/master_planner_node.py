from src.config.research_depth import get_depth_config
from src.models import get_master_planner_model
from src.prompts.master_planner_prompt import MASTER_PLANNER_PROMPT
from src.schemas import MasterPlan
from src.utils.logging_utils import print_node_header


def _get_depth_guidance(research_depth: str) -> str:
    """Generate depth-specific guidance for subtask generation."""
    guidance_map = {
        "quick": """**Quick Research Mode**
- Target: SIMPLE mode preferred (no decomposition)
- If decomposition is absolutely necessary: 1-2 subtasks maximum
- Focus: Fast, surface-level research
- Only decompose if query has clearly distinct parts""",
        "standard": """**Standard Research Mode**
- Target: 3-5 subtasks for complex queries
- Focus: Balanced coverage with good depth
- Decompose when query has multiple aspects or requires comparison
- Each subtask should be meaningful and independent""",
        "deep": """**Deep Research Mode**
- Target: 5-10 subtasks for complex queries
- Focus: Thorough investigation with multiple perspectives
- Decompose into finer-grained subtasks for detailed analysis
- Include related aspects that provide context
- Consider historical, current, and future dimensions""",
        "comprehensive": """**Comprehensive Research Mode**
- Target: 10-20 subtasks for complex queries
- Focus: Exhaustive, multi-dimensional coverage
- Decompose into many specific subtasks covering ALL relevant aspects
- Include: technical, historical, social, economic, practical, theoretical dimensions
- Cover: background, current state, trends, challenges, opportunities, future outlook
- Every significant aspect deserves its own subtask
- This is the MOST THOROUGH mode - err on the side of more subtasks""",
    }
    return guidance_map.get(research_depth, guidance_map["standard"])


def master_planner(state):
    """
    Master Planner - Detects query complexity and creates Master Plan

    Simple queries: Delegates to Strategic Planner (existing flow)
    Complex queries: Decomposes into subtasks for hierarchical execution

    Phase 1 (v2.0-alpha): Basic hierarchical decomposition
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

        # Validate: If hierarchical mode but no subtasks, force simple mode
        if master_plan.is_complex and len(master_plan.subtasks) == 0:
            print(
                "\n  ⚠ Warning: LLM selected hierarchical but generated no subtasks. "
                "Forcing simple mode."
            )
            master_plan.is_complex = False
            master_plan.execution_mode = "simple"

        # Log results
        complexity = "COMPLEX" if master_plan.is_complex else "SIMPLE"
        print(f"\n  ✓ Complexity Assessment: {complexity}")
        print(f"  Reasoning: {master_plan.complexity_reasoning[:200]}...")
        print(f"  Execution Mode: {master_plan.execution_mode}")

        if master_plan.is_complex:
            print(f"\n  Subtasks Generated: {len(master_plan.subtasks)}")
            for subtask in master_plan.subtasks:
                deps = f" (depends: {subtask.dependencies})" if subtask.dependencies else ""
                print(
                    f"    {subtask.priority}. [{subtask.subtask_id}] {subtask.description[:80]}...{deps}"
                )
            print(f"\n  Overall Strategy: {master_plan.overall_strategy[:200]}...\n")
        else:
            print(f"  Strategy: {master_plan.overall_strategy[:150]}...\n")

        # Get depth config for budget-aware settings
        depth_config = get_depth_config(state.get("research_depth", "standard"))

        # Convert to dict for state (LangGraph requires JSON-serializable types)
        return {
            "execution_mode": master_plan.execution_mode,
            "master_plan": master_plan.dict() if master_plan.is_complex else None,
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
        print("  ⚠ Warning: Master planning failed, falling back to simple mode")
        print(f"  Error: {e}")

        # Fallback: treat as simple query
        return {
            "execution_mode": "simple",
            "master_plan": None,
            "current_subtask_index": 0,
            "current_subtask_id": "",
            "subtask_results": {},
        }
