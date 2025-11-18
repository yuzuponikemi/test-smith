"""
Model Provider Switcher

Easily switch between Ollama and Gemini for Test-Smith evaluations.

Usage:
    # Switch to Gemini
    python switch_model_provider.py gemini

    # Switch to Ollama
    python switch_model_provider.py ollama

    # Check current provider
    python switch_model_provider.py status
"""

import sys
import os
from pathlib import Path


def read_env_file(env_path: str = ".env") -> dict:
    """Read .env file into a dictionary."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"')
    return env_vars


def write_env_file(env_vars: dict, env_path: str = ".env"):
    """Write dictionary to .env file."""
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f'{key}="{value}"\n')


def switch_provider(provider: str):
    """Switch MODEL_PROVIDER in .env file."""
    if provider not in ['ollama', 'gemini']:
        print(f"❌ Error: Invalid provider '{provider}'")
        print("   Valid options: 'ollama' or 'gemini'")
        sys.exit(1)

    env_vars = read_env_file()
    current_provider = env_vars.get('MODEL_PROVIDER', 'ollama')

    if current_provider == provider:
        print(f"ℹ️  Already using {provider}")
        print_provider_info(provider)
        return

    # Update provider
    env_vars['MODEL_PROVIDER'] = provider
    write_env_file(env_vars)

    print(f"✅ Switched to {provider}")
    print_provider_info(provider)

    # Verify required configuration
    verify_configuration(provider, env_vars)


def print_provider_info(provider: str):
    """Print information about the selected provider."""
    if provider == 'gemini':
        print("\n📊 Gemini Configuration:")
        print("   - Model: gemini-1.5-flash (default)")
        print("   - Speed: Very fast")
        print("   - Cost: Pay-per-use (check Google AI pricing)")
        print("   - Requires: GOOGLE_API_KEY in .env")
    else:
        print("\n🦙 Ollama Configuration:")
        print("   - Models: llama3, command-r")
        print("   - Speed: Depends on hardware")
        print("   - Cost: Free (local)")
        print("   - Requires: Ollama running locally")


def verify_configuration(provider: str, env_vars: dict):
    """Verify required configuration for provider."""
    print("\n🔍 Verifying configuration...")

    if provider == 'gemini':
        if not env_vars.get('GOOGLE_API_KEY'):
            print("   ⚠️  Warning: GOOGLE_API_KEY not found in .env")
            print("   Add it with: GOOGLE_API_KEY=\"your-api-key-here\"")
        else:
            print("   ✓ GOOGLE_API_KEY configured")

    else:  # ollama
        # Check if Ollama is running
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("   ✓ Ollama is running")
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                required = ['llama3', 'command-r', 'nomic-embed-text']
                for model in required:
                    if any(model in name for name in model_names):
                        print(f"   ✓ {model} available")
                    else:
                        print(f"   ⚠️  {model} not found (install: ollama pull {model})")
            else:
                print("   ⚠️  Ollama not responding")
        except:
            print("   ⚠️  Cannot connect to Ollama (is it running?)")


def show_status():
    """Show current model provider status."""
    env_vars = read_env_file()
    current_provider = env_vars.get('MODEL_PROVIDER', 'ollama')

    print("="*60)
    print("MODEL PROVIDER STATUS")
    print("="*60)
    print(f"\n📍 Current Provider: {current_provider}")
    print_provider_info(current_provider)
    verify_configuration(current_provider, env_vars)
    print("\n" + "="*60)


def show_help():
    """Show usage help."""
    print("""
Model Provider Switcher for Test-Smith

USAGE:
    python switch_model_provider.py <command>

COMMANDS:
    gemini      Switch to Gemini API (Google)
    ollama      Switch to Ollama (local)
    status      Show current provider and configuration

EXAMPLES:
    # Switch to Gemini for faster evaluation
    python switch_model_provider.py gemini

    # Switch back to Ollama
    python switch_model_provider.py ollama

    # Check current setup
    python switch_model_provider.py status

PROVIDER COMPARISON:

Gemini (gemini-1.5-flash):
    ✓ Very fast responses
    ✓ High quality outputs
    ✓ No local GPU needed
    ✗ Costs money (pay-per-use)
    ✗ Requires API key

Ollama (llama3/command-r):
    ✓ Completely free
    ✓ Private/local
    ✓ No API limits
    ✗ Slower (depends on hardware)
    ✗ Requires good CPU/GPU

AFTER SWITCHING:
    Run evaluation with new provider:
    python evaluate_agent.py --dry-run --limit 3
    """)


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command in ['help', '--help', '-h']:
        show_help()
    elif command == 'status':
        show_status()
    elif command in ['gemini', 'ollama']:
        switch_provider(command)
    else:
        print(f"❌ Unknown command: {command}")
        print("\nValid commands: gemini, ollama, status, help")
        sys.exit(1)


if __name__ == "__main__":
    main()
