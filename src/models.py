import os
from langchain_ollama.chat_models import ChatOllama

# Configuration
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")  # "gemini" or "ollama"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Default Gemini models
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"  # Stable and widely supported
ADVANCED_GEMINI_MODEL = "gemini-1.5-pro"   # For complex tasks (optional)


def _get_model(gemini_model: str = DEFAULT_GEMINI_MODEL, ollama_model: str = "llama3", temperature: float = 0.7):
    """
    Factory function to get the appropriate model based on MODEL_PROVIDER.

    Args:
        gemini_model: Gemini model to use (default: gemini-1.5-flash)
        ollama_model: Ollama model to use as fallback
        temperature: Model temperature (0.0-1.0)

    Returns:
        Configured chat model
    """
    if MODEL_PROVIDER == "gemini":
        # Import only when needed to avoid dependency errors
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain_google_genai is required when MODEL_PROVIDER=gemini. "
                "Install it with: pip install langchain-google-genai"
            )

        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required when MODEL_PROVIDER=gemini. "
                "Please set it in your .env file or environment."
            )
        return ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=GOOGLE_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True  # Gemini compatibility
        )
    elif MODEL_PROVIDER == "ollama":
        return ChatOllama(model=ollama_model, temperature=temperature)
    else:
        raise ValueError(f"Unknown MODEL_PROVIDER: {MODEL_PROVIDER}. Use 'gemini' or 'ollama'")


def get_planner_model():
    """Strategic planner for query allocation (RAG vs Web)"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.7
    )


def get_master_planner_model():
    """
    Model for Master Planner (hierarchical decomposition)
    Uses more advanced model for better structured output generation
    """
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,  # Flash is fast enough for planning
        ollama_model="command-r",
        temperature=0.7
    )


def get_reflection_model():
    """Reflection and self-evaluation"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.7
    )


def get_evaluation_model():
    """Quality and sufficiency evaluation"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="command-r",
        temperature=0.5  # Lower temperature for more consistent evaluation
    )


def get_analyzer_model():
    """Data analysis and summarization"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.7
    )


def get_synthesizer_model():
    """Final report synthesis"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.8  # Slightly higher for more creative synthesis
    )


# === Causal Inference Models ===

def get_issue_analyzer_model():
    """Issue analysis and symptom extraction for causal inference"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.5  # Lower temperature for systematic analysis
    )


def get_brainstormer_model():
    """Root cause hypothesis generation (brainstorming)"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.9  # Higher temperature for creative divergent thinking
    )


def get_evidence_planner_model():
    """Strategic evidence gathering planning for causal validation"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.7
    )


def get_causal_checker_model():
    """Causal relationship validation and evidence assessment"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="command-r",
        temperature=0.5  # Lower temperature for rigorous causal reasoning
    )


def get_hypothesis_validator_model():
    """Hypothesis ranking and probability assessment"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="command-r",
        temperature=0.5  # Lower temperature for consistent ranking
    )


def get_root_cause_synthesizer_model():
    """Root cause analysis report synthesis"""
    return _get_model(
        gemini_model=DEFAULT_GEMINI_MODEL,
        ollama_model="llama3",
        temperature=0.8  # Slightly higher for comprehensive reporting
    )
