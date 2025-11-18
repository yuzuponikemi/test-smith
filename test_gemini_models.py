"""Test which Gemini models are available"""

import os
from dotenv import load_dotenv
load_dotenv()

# Try to list available models
try:
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    print("Available Gemini models:")
    print("="*60)
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✓ {m.name}")
    print("="*60)

except Exception as e:
    print(f"Error listing models: {e}")
    print("\nTrying alternative model names...")

# Test different model name formats
test_models = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-flash-latest",
]

from langchain_google_genai import ChatGoogleGenerativeAI

print("\nTesting model names:")
print("="*60)

for model_name in test_models:
    try:
        print(f"\nTrying: {model_name}")
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        # Try a simple call
        response = llm.invoke("Say 'test' if you can read this")
        print(f"  ✅ SUCCESS: {model_name}")
        print(f"  Response: {response.content[:50]}...")
        break  # Stop on first success
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"  ❌ FAILED: {error_msg}")

print("\n" + "="*60)
