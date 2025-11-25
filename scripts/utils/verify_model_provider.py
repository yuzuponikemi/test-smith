"""
Quick verification script to check which model provider is being used.

Usage:
    python verify_model_provider.py
"""

from dotenv import load_dotenv

load_dotenv()

import os

from src.models import (
    MODEL_PROVIDER,
    get_evaluation_model,
    get_planner_model,
    get_synthesizer_model,
)


def main():
    print("="*60)
    print("MODEL PROVIDER VERIFICATION")
    print("="*60)

    print("\n📍 Environment Variable:")
    print(f"   MODEL_PROVIDER = {os.getenv('MODEL_PROVIDER', 'not set')}")

    print("\n📍 src/models.py Variable:")
    print(f"   MODEL_PROVIDER = {MODEL_PROVIDER}")

    print("\n🤖 Active Models:")
    print(f"   Planner: {get_planner_model()}")
    print(f"   Evaluator: {get_evaluation_model()}")
    print(f"   Synthesizer: {get_synthesizer_model()}")

    # Check if Gemini or Ollama
    evaluator = str(get_evaluation_model())

    if "gemini" in evaluator.lower():
        print("\n✅ SUCCESS: Using Gemini API")
        print("   Model: gemini-1.5-flash")
        print("   Speed: Very fast (1-3s per call)")
    elif "ollama" in evaluator.lower():
        print("\n✅ SUCCESS: Using Ollama (local)")
        print("   Model: llama3/command-r")
        print("   Speed: Slower (10-30s per call)")
    else:
        print("\n⚠️  WARNING: Unknown model type")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
