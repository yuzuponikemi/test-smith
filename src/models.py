import os
from enum import Enum

from langchain_ollama.chat_models import ChatOllama

# =============================================================================
# Provider Configuration
# =============================================================================
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")  # "gemini" or "ollama"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Default Gemini models
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
ADVANCED_GEMINI_MODEL = "gemini-1.5-pro"

# Ollama context window sizes (model training max)
OLLAMA_CONTEXT_LENGTHS: dict[str, int] = {
    "qwen3-next": 262144,
    "command-r": 131072,
    "llama3": 8192,
}

# Default Ollama model (used by _get_model() fallback)
DEFAULT_OLLAMA_MODEL = "qwen3-next"


# =============================================================================
# Quality Profile System
# =============================================================================
class QualityProfile(str, Enum):
    """Model allocation profiles for different use cases.

    DRAFT:      Pipeline connectivity testing. All llama3, minimal context.
    STANDARD:   Logic verification. All command-r, moderate context.
    PRODUCTION: Best quality. Hybrid qwen3-next (quality) + command-r (speed).
    """

    DRAFT = "draft"
    STANDARD = "standard"
    PRODUCTION = "production"


# Node roles: determines which model tier is used per quality profile
ROLE_FAST = "fast"  # Speed-critical: planner, evaluator, graph_selector
ROLE_BALANCED = "balanced"  # Moderate: code assistant, evidence planner
ROLE_QUALITY = "quality"  # Quality-critical: analyzer, synthesizer, reflection

# Profile → Role → {model, num_ctx}
# Context sizes are optimized per role based on typical input/output lengths.
# TPS is unaffected by num_ctx (up to 131K), but VRAM scales linearly.
QUALITY_PROFILES: dict[QualityProfile, dict[str, dict[str, str | int]]] = {
    QualityProfile.DRAFT: {
        #   llama3: 56 tps, ~5GB VRAM. No thinking overhead.
        ROLE_FAST: {"model": "llama3", "num_ctx": 2048},
        ROLE_BALANCED: {"model": "llama3", "num_ctx": 4096},
        ROLE_QUALITY: {"model": "llama3", "num_ctx": 4096},
    },
    QualityProfile.STANDARD: {
        #   command-r: 14.8 tps, 19-27GB VRAM. No thinking overhead.
        ROLE_FAST: {"model": "command-r", "num_ctx": 8192},
        ROLE_BALANCED: {"model": "command-r", "num_ctx": 16384},
        ROLE_QUALITY: {"model": "command-r", "num_ctx": 32768},
    },
    QualityProfile.PRODUCTION: {
        #   command-r for speed nodes (no thinking overhead)
        #   qwen3-next for quality nodes (thinking improves analysis)
        #   qwen3-next: 22 tps gen, but ~95% of tokens are hidden thinking.
        #   Use ctx≤131072 to avoid 24% TPS penalty at 262K.
        ROLE_FAST: {"model": "command-r", "num_ctx": 8192},
        ROLE_BALANCED: {"model": "command-r", "num_ctx": 32768},
        ROLE_QUALITY: {"model": "qwen3-next", "num_ctx": 65536},
    },
}

# Expected performance characteristics per profile:
#   DRAFT:      ~2-5 min (quick_research), low quality, minimal VRAM (~5GB)
#   STANDARD:   ~5-8 min (quick_research), moderate quality, ~27GB VRAM
#   PRODUCTION: ~15-25 min (quick_research), high quality, ~75GB VRAM
#               (command-r 20GB + qwen3-next 55GB coexist in 96GB)


def get_quality_profile() -> QualityProfile:
    """Get current quality profile from MODEL_QUALITY env var."""
    raw = os.getenv("MODEL_QUALITY", "standard").lower()
    try:
        return QualityProfile(raw)
    except ValueError:
        return QualityProfile.STANDARD


def set_quality_profile(profile: str | QualityProfile) -> None:
    """Set quality profile programmatically (e.g., from CLI --quality flag)."""
    if isinstance(profile, QualityProfile):
        os.environ["MODEL_QUALITY"] = profile.value
    else:
        os.environ["MODEL_QUALITY"] = str(profile).lower()


def get_profile_info() -> dict[str, str]:
    """Get human-readable info about all available profiles."""
    return {
        "draft": "動作確認用: llama3 (8B), ~56 tps, ~5GB VRAM",
        "standard": "ロジック確認用: command-r (32B), ~15 tps, ~27GB VRAM",
        "production": "本番用: qwen3-next + command-r, best quality, ~75GB VRAM",
    }


# =============================================================================
# Model Factory Functions
# =============================================================================


def _get_model(
    gemini_model: str = DEFAULT_GEMINI_MODEL,
    ollama_model: str = DEFAULT_OLLAMA_MODEL,
    temperature: float = 0.7,
    num_ctx: int | None = None,
):
    """Low-level factory: get model by explicit provider/model name.

    Prefer _get_model_for_role() for profile-aware model selection.
    """
    if MODEL_PROVIDER == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain_google_genai is required when MODEL_PROVIDER=gemini. "
                "Install it with: pip install langchain-google-genai"
            ) from None

        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required when MODEL_PROVIDER=gemini. "
                "Please set it in your .env file or environment."
            )
        return ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=GOOGLE_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True,
        )
    elif MODEL_PROVIDER == "ollama":
        if num_ctx is None:
            num_ctx = OLLAMA_CONTEXT_LENGTHS.get(ollama_model, 8192)
        return ChatOllama(model=ollama_model, temperature=temperature, num_ctx=num_ctx)
    else:
        raise ValueError(f"Unknown MODEL_PROVIDER: {MODEL_PROVIDER}. Use 'gemini' or 'ollama'")


def _get_model_for_role(
    role: str,
    temperature: float = 0.7,
    gemini_model: str = DEFAULT_GEMINI_MODEL,
):
    """Profile-aware factory: get model based on node role and current quality profile.

    Args:
        role: ROLE_FAST, ROLE_BALANCED, or ROLE_QUALITY
        temperature: Model temperature (0.0-1.0)
        gemini_model: Gemini model override (used when MODEL_PROVIDER=gemini)
    """
    if MODEL_PROVIDER == "gemini":
        return _get_model(gemini_model=gemini_model, temperature=temperature)

    profile = get_quality_profile()
    config = QUALITY_PROFILES[profile][role]
    model_name = str(config["model"])
    num_ctx = int(config["num_ctx"])
    return ChatOllama(model=model_name, temperature=temperature, num_ctx=num_ctx)


# =============================================================================
# Node-specific Model Getters
# =============================================================================

# --- Research Pipeline ---


def get_planner_model():
    """Strategic planner for query allocation (RAG vs Web)"""
    return _get_model_for_role(ROLE_FAST, temperature=0.7)


def get_master_planner_model():
    """Master Planner for hierarchical decomposition"""
    return _get_model_for_role(ROLE_FAST, temperature=0.7)


def get_reflection_model():
    """Reflection and self-evaluation"""
    return _get_model_for_role(ROLE_QUALITY, temperature=0.7)


def get_evaluation_model():
    """Quality and sufficiency evaluation"""
    return _get_model_for_role(ROLE_FAST, temperature=0.5)


def get_analyzer_model():
    """Data analysis and summarization"""
    return _get_model_for_role(ROLE_QUALITY, temperature=0.7)


def get_synthesizer_model():
    """Final report synthesis"""
    return _get_model_for_role(ROLE_QUALITY, temperature=0.8)


# --- Causal Inference ---


def get_issue_analyzer_model():
    """Issue analysis and symptom extraction for causal inference"""
    return _get_model_for_role(ROLE_BALANCED, temperature=0.5)


def get_brainstormer_model():
    """Root cause hypothesis generation (brainstorming)"""
    return _get_model_for_role(ROLE_QUALITY, temperature=0.9)


def get_causal_checker_model():
    """Causal relationship validation and evidence assessment"""
    return _get_model_for_role(ROLE_QUALITY, temperature=0.5)


def get_evidence_planner_model():
    """Strategic evidence gathering planning for causal validation"""
    return _get_model_for_role(ROLE_FAST, temperature=0.7)


def get_hypothesis_validator_model():
    """Hypothesis ranking and probability assessment"""
    return _get_model_for_role(ROLE_BALANCED, temperature=0.5)


def get_root_cause_synthesizer_model():
    """Root cause analysis report synthesis"""
    return _get_model_for_role(ROLE_QUALITY, temperature=0.8)


# --- Code Execution ---


def get_code_executor_model():
    """Code generation and execution planning"""
    return _get_model_for_role(ROLE_BALANCED, temperature=0.3)


# --- Code Assistant ---


def get_code_assistant_model():
    """Code analysis and explanation for codebase queries"""
    return _get_model_for_role(ROLE_BALANCED, temperature=0.5)


# --- Graph Selection ---


def get_graph_selector_model():
    """Graph workflow selection based on query classification."""
    return _get_model_for_role(
        ROLE_FAST,
        temperature=0.1,
        gemini_model="gemini-1.5-flash",
    )
