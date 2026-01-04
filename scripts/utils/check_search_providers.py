#!/usr/bin/env python3
"""
Search Provider Health Check Script

Checks the health and configuration of all search providers.
Useful for diagnosing search issues and verifying API keys.
"""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv

from src.utils.search_providers import SearchProviderManager


def main():
    """Run health check on all search providers"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Test search providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--provider",
        type=str,
        help="Specific provider to test (e.g., mcp, tavily, duckduckgo). "
        "If not specified, tests all configured providers.",
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    print("=" * 80)
    print("SEARCH PROVIDER HEALTH CHECK")
    print("=" * 80)
    print()

    # Override priority if specific provider requested
    priority = None
    if args.provider:
        priority = [args.provider]
        print(f"Testing specific provider: {args.provider}")
        print()

    # Initialize provider manager
    try:
        manager = SearchProviderManager(priority=priority)
    except Exception as e:
        print(f"❌ Failed to initialize provider manager: {e}")
        return 1

    # Print status report
    print(manager.get_status_report())
    print()

    # Run health checks
    print("=" * 80)
    print("RUNNING HEALTH CHECKS")
    print("=" * 80)
    print()

    health_status = manager.health_check_all()
    print()

    # Test search with each provider
    print("=" * 80)
    print("TEST SEARCH (query: 'Python programming')")
    print("=" * 80)
    print()

    test_query = "Python programming"
    available = manager.get_available_providers()

    if not available:
        print("❌ No providers available for testing")
        return 1

    for provider_name in available:
        print(f"\n--- Testing {provider_name} ---")
        try:
            # Create temporary manager with single provider
            temp_manager = SearchProviderManager(priority=[provider_name])
            results = temp_manager.search(test_query, max_results=2, attempt_all=False)
            print(f"✅ Success: Retrieved {len(results)} results")

            # Show first result
            if results:
                first = results[0]
                print(f"   Sample: {first.get('title', 'No title')[:60]}...")

        except Exception as e:
            print(f"❌ Failed: {str(e)}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    healthy_count = sum(1 for status in health_status.values() if status)
    total_count = len(health_status)

    print(f"Healthy providers: {healthy_count}/{total_count}")
    print(f"Priority order: {' → '.join(manager.priority)}")
    print()

    if healthy_count == 0:
        print("⚠️  WARNING: No healthy search providers available!")
        print("   Please check your API keys and network connection.")
        return 1
    elif healthy_count < total_count:
        print("⚠️  Some providers are unavailable, but fallback is configured.")
        return 0
    else:
        print("✅ All configured providers are healthy!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
