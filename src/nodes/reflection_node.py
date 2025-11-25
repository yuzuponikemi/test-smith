from src.models import get_reflection_model
from src.prompts.reflection_prompt import REFLECTION_PROMPT
from src.schemas import ReflectionCritique
from src.utils.logging_utils import print_node_header


def reflection_node(state):
    """
    Meta-reasoning reflection agent that critically examines research findings.

    Identifies:
    - Logical fallacies and reasoning gaps
    - Contradictions and inconsistencies
    - Bias indicators
    - Missing perspectives and evidence gaps
    - Source credibility issues

    Returns structured critique that informs whether to continue research or proceed to synthesis.
    """
    print_node_header("REFLECTION")
    model = get_reflection_model()

    # Get context for reflection
    original_query = state.get("query", "")
    analyzed_data = state.get("analyzed_data", [])
    execution_mode = state.get("execution_mode", "simple")

    # Build context info based on execution mode
    if execution_mode == "hierarchical":
        current_subtask_id = state.get("current_subtask_id", "unknown")
        context_info = f"Subtask {current_subtask_id}"
    else:
        loop_count = state.get("loop_count", 0)
        context_info = f"Iteration {loop_count}"

    print(f"  Context: {execution_mode} mode, {context_info}")
    print(f"  Analyzing {len(analyzed_data)} data points")

    # Use structured output for reliable critique
    structured_llm = model.with_structured_output(ReflectionCritique)

    prompt = REFLECTION_PROMPT.format(
        original_query=original_query,
        analyzed_data=analyzed_data,
        execution_mode=execution_mode,
        context_info=context_info
    )

    try:
        critique = structured_llm.invoke(prompt)

        # Print summary of critique
        print(f"  Overall Quality: {critique.overall_quality}")
        print(f"  Evidence Strength: {critique.evidence_strength}")
        print(f"  Confidence Score: {critique.confidence_score:.2f}")
        print(f"  Critique Points: {len(critique.critique_points)}")

        # Print critical issues
        critical_issues = [cp for cp in critique.critique_points if cp.severity == "critical"]
        if critical_issues:
            print(f"  ⚠️  CRITICAL ISSUES: {len(critical_issues)}")
            for issue in critical_issues:
                print(f"      - {issue.category}: {issue.description[:80]}...")

        # Print contradictions
        if critique.contradictions:
            print(f"  ⚠️  CONTRADICTIONS: {len(critique.contradictions)}")

        # Print decision
        decision = "CONTINUE RESEARCH" if critique.should_continue_research else "PROCEED TO SYNTHESIS"
        print(f"  Decision: {decision}")
        if critique.continuation_reasoning:
            print(f"  Reasoning: {critique.continuation_reasoning[:100]}...")

        # Convert to dict for state storage (JSON-serializable)
        critique_dict = critique.model_dump()

        return {
            "reflection_critique": critique_dict,
            "reflection_quality": critique.overall_quality,
            "should_continue_research": critique.should_continue_research,
            "reflection_confidence": critique.confidence_score
        }

    except Exception as e:
        print(f"  Warning: Structured reflection failed, using fallback: {e}")
        message = model.invoke(prompt)

        # Return fallback with conservative defaults
        return {
            "reflection_critique": {
                "overall_quality": "adequate",
                "quality_reasoning": message.content,
                "critique_points": [],
                "missing_perspectives": [],
                "contradictions": [],
                "bias_indicators": [],
                "evidence_strength": "moderate",
                "should_continue_research": False,
                "continuation_reasoning": "Fallback reflection used - proceeding with synthesis",
                "synthesis_recommendations": [],
                "confidence_score": 0.7
            },
            "reflection_quality": "adequate",
            "should_continue_research": False,
            "reflection_confidence": 0.7
        }
