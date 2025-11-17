"""
Root Cause Synthesizer Node - Generates comprehensive root cause analysis report.

Part of the Causal Inference Graph workflow for root cause analysis.
"""

from src.models import get_root_cause_synthesizer_model
from src.prompts.root_cause_synthesizer_prompt import ROOT_CAUSE_SYNTHESIZER_PROMPT


def root_cause_synthesizer_node(state: dict) -> dict:
    """
    Synthesizes all analysis into a comprehensive root cause analysis report.

    Args:
        state: Current graph state with all analysis results

    Returns:
        Updated state with final report
    """
    print("---ROOT CAUSE SYNTHESIZER---")

    query = state.get("query", "")
    issue_summary = state.get("issue_summary", "")
    symptoms = state.get("symptoms", [])
    context = state.get("context", "")
    scope = state.get("scope", "")
    ranked_hypotheses = state.get("ranked_hypotheses", [])
    causal_graph_data = state.get("causal_graph_data", {})

    print(f"  Synthesizing root cause analysis report...")
    print(f"  Report includes {len(ranked_hypotheses)} ranked hypotheses")

    # Get model
    model = get_root_cause_synthesizer_model()

    # Format issue analysis for prompt
    issue_analysis_str = f"""
Summary: {issue_summary}
Symptoms: {', '.join(symptoms)}
Context: {context}
Scope: {scope}
"""

    # Format ranked hypotheses for prompt
    ranked_hypotheses_str = "\n".join([
        f"{i+1}. {h['hypothesis_id']}: {h['description']}\n"
        f"   Likelihood: {h['likelihood']:.2f} | Confidence: {h['confidence']}\n"
        f"   Supporting factors: {', '.join(h['supporting_factors'][:3])}\n"
        f"   Recommendation: {h['recommendation']}"
        for i, h in enumerate(ranked_hypotheses)
    ])

    # Format causal graph data
    causal_graph_str = str(causal_graph_data) if causal_graph_data else "No graph data generated"

    # Format prompt and invoke
    prompt = ROOT_CAUSE_SYNTHESIZER_PROMPT.format(
        query=query,
        issue_analysis=issue_analysis_str,
        ranked_hypotheses=ranked_hypotheses_str,
        causal_graph_data=causal_graph_str
    )

    message = model.invoke(prompt)
    report = message.content

    print(f"  Generated comprehensive report ({len(report)} characters)")

    return {
        "report": report
    }
