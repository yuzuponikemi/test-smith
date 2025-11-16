#!/usr/bin/env python3
"""
Test script to verify dual model provider setup (Ollama + Claude).
Tests model factory functions and displays active configuration.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import (
    get_planner_model,
    get_master_planner_model,
    get_evaluation_model,
    get_analyzer_model,
    get_synthesizer_model,
    get_active_models,
    USE_CLAUDE
)

def test_model_initialization():
    """Test that all model factory functions work correctly."""
    print("=" * 60)
    print("Test-Smith Model Configuration Test")
    print("=" * 60)

    # Display active configuration
    print(f"\n🔧 Configuration:")
    print(f"   USE_CLAUDE: {USE_CLAUDE}")

    active_models = get_active_models()
    print(f"\n📋 Active Models:")
    print(f"   Provider: {active_models['provider']}")
    print(f"   Planner: {active_models['planner']}")
    print(f"   Master Planner: {active_models['master_planner']}")
    print(f"   Evaluation: {active_models['evaluation']}")
    print(f"   Analyzer: {active_models['analyzer']}")
    print(f"   Synthesizer: {active_models['synthesizer']}")

    # Test model instantiation
    print(f"\n🧪 Testing Model Instantiation:")

    try:
        planner = get_planner_model()
        print(f"   ✓ Planner model: {type(planner).__name__}")

        master_planner = get_master_planner_model()
        print(f"   ✓ Master Planner model: {type(master_planner).__name__}")

        evaluator = get_evaluation_model()
        print(f"   ✓ Evaluator model: {type(evaluator).__name__}")

        analyzer = get_analyzer_model()
        print(f"   ✓ Analyzer model: {type(analyzer).__name__}")

        synthesizer = get_synthesizer_model()
        print(f"   ✓ Synthesizer model: {type(synthesizer).__name__}")

        print(f"\n✅ All models initialized successfully!")

        # Display model details for Claude
        if USE_CLAUDE:
            print(f"\n📊 Claude Model Details:")
            print(f"   Model ID: {planner.model}")
            if hasattr(planner, 'model_kwargs'):
                print(f"   Model kwargs: {planner.model_kwargs}")
            print(f"\n   Detectability features:")
            print(f"   - Source tag: 'test-smith-research-agent'")
            print(f"   - Version tag: '2025-01-15'")
            print(f"   - LangSmith tracing: Enabled")
            print(f"   - Anthropic dashboard: Enabled")

        return True

    except Exception as e:
        print(f"\n❌ Error during model initialization:")
        print(f"   {type(e).__name__}: {str(e)}")

        if USE_CLAUDE and "API key" in str(e):
            print(f"\n💡 Tip: Make sure ANTHROPIC_API_KEY is set in .env file")
        elif not USE_CLAUDE and "ollama" in str(e).lower():
            print(f"\n💡 Tip: Make sure Ollama is running: ollama list")

        return False

def main():
    success = test_model_initialization()

    print("\n" + "=" * 60)
    if success:
        print("✅ Model configuration test PASSED")

        if not USE_CLAUDE:
            print("\n💡 To test Claude models:")
            print("   1. Edit .env file:")
            print("      USE_CLAUDE=\"true\"")
            print("      ANTHROPIC_API_KEY=\"your-key-here\"")
            print("   2. Run this script again")
    else:
        print("❌ Model configuration test FAILED")
        sys.exit(1)

    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
