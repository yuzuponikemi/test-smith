"""Models layer — public API façade.

Re-exports the role-based model factories so consumers can do
``from test_smith.models import get_planner_model`` without depending on
the internal ``src.models`` namespace.
"""

from src.models import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OLLAMA_MODEL,
    QualityProfile,
    _get_model,
    _get_model_for_role,
    get_analyzer_model,
    get_brainstormer_model,
    get_causal_checker_model,
    get_code_assistant_model,
    get_code_executor_model,
    get_evaluation_model,
    get_evidence_planner_model,
    get_graph_selector_model,
    get_hypothesis_validator_model,
    get_issue_analyzer_model,
    get_master_planner_model,
    get_planner_model,
    get_profile_info,
    get_quality_profile,
    get_reflection_model,
    get_root_cause_synthesizer_model,
    get_synthesizer_model,
    set_quality_profile,
)

__all__ = [
    "QualityProfile",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_OLLAMA_MODEL",
    "get_quality_profile",
    "set_quality_profile",
    "get_profile_info",
    "_get_model",
    "_get_model_for_role",
    "get_planner_model",
    "get_master_planner_model",
    "get_reflection_model",
    "get_evaluation_model",
    "get_analyzer_model",
    "get_synthesizer_model",
    "get_issue_analyzer_model",
    "get_brainstormer_model",
    "get_causal_checker_model",
    "get_evidence_planner_model",
    "get_hypothesis_validator_model",
    "get_root_cause_synthesizer_model",
    "get_code_executor_model",
    "get_code_assistant_model",
    "get_graph_selector_model",
]
