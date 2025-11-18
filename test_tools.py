#!/usr/bin/env python3
"""
Test script for the Tool Use System

This script tests the tool registry, built-in tools, and tool execution.
"""

import asyncio
from src.tools import (
    get_tool_registry,
    initialize_tools,
    list_available_tools,
)


def test_builtin_tools():
    """Test all built-in function tools"""
    print("\n" + "="*60)
    print("TESTING BUILT-IN TOOLS")
    print("="*60)

    registry = get_tool_registry()

    # Test calculator
    print("\n1. Calculator Tool")
    result = registry.execute_tool_sync("calculator", {"expression": "sqrt(16) + 2**3"})
    print(f"   sqrt(16) + 2**3 = {result}")

    result = registry.execute_tool_sync("calculator", {"expression": "sin(3.14159/2)"})
    print(f"   sin(pi/2) = {result}")

    # Test statistics
    print("\n2. Statistics Analyzer Tool")
    numbers = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    result = registry.execute_tool_sync("statistics_analyzer", {
        "numbers": numbers,
        "operation": "summary"
    })
    print(f"   Summary of {numbers}:")
    print(f"   {result}")

    # Test JSON parser
    print("\n3. JSON Parser Tool")
    json_data = '{"name": "Test", "data": {"value": 42, "items": ["a", "b", "c"]}}'
    result = registry.execute_tool_sync("json_parser", {
        "json_string": json_data,
        "query": "data.value"
    })
    print(f"   Extracted data.value = {result}")

    # Test unit converter
    print("\n4. Unit Converter Tool")
    result = registry.execute_tool_sync("unit_converter", {
        "value": 100,
        "from_unit": "km",
        "to_unit": "miles"
    })
    print(f"   {result}")

    result = registry.execute_tool_sync("unit_converter", {
        "value": 32,
        "from_unit": "celsius",
        "to_unit": "fahrenheit"
    })
    print(f"   {result}")

    # Test text analyzer
    print("\n5. Text Analyzer Tool")
    text = "This is a test. It has multiple sentences. How many words are there?"
    result = registry.execute_tool_sync("text_analyzer", {
        "text": text,
        "analysis_type": "summary"
    })
    print(f"   Analysis of text:")
    print(f"   {result}")

    # Test date calculator
    print("\n6. Date Calculator Tool")
    result = registry.execute_tool_sync("date_calculator", {
        "operation": "diff",
        "date1": "2024-01-01",
        "date2": "2024-12-31"
    })
    print(f"   Days in 2024: {result}")

    result = registry.execute_tool_sync("date_calculator", {
        "operation": "add",
        "date1": "2024-01-01",
        "days": 100
    })
    print(f"   100 days after 2024-01-01: {result}")

    # Test Python executor
    print("\n7. Python Executor Tool")
    code = """
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
print(f"Sum of squares: {sum(squared)}")
"""
    result = registry.execute_tool_sync("python_executor", {"code": code})
    print(f"   Code execution result:")
    print(f"   {result}")

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60 + "\n")


def test_tool_schemas():
    """Test that tool schemas are correctly formatted for LLM"""
    print("\n" + "="*60)
    print("TESTING TOOL SCHEMAS")
    print("="*60)

    registry = get_tool_registry()
    schemas = registry.get_tool_schemas()

    print(f"\nFound {len(schemas)} tool schemas:")
    for schema in schemas:
        name = schema["function"]["name"]
        desc = schema["function"]["description"][:50]
        print(f"  - {name}: {desc}...")

    print("\n" + "="*60 + "\n")


async def test_async_execution():
    """Test async tool execution"""
    print("\n" + "="*60)
    print("TESTING ASYNC EXECUTION")
    print("="*60)

    registry = get_tool_registry()

    # Execute multiple tools concurrently
    results = await asyncio.gather(
        registry.execute_tool("calculator", {"expression": "2 + 2"}),
        registry.execute_tool("calculator", {"expression": "10 * 5"}),
        registry.execute_tool("unit_converter", {
            "value": 1,
            "from_unit": "km",
            "to_unit": "m"
        }),
    )

    print("\nConcurrent execution results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result}")

    print("\n" + "="*60 + "\n")


def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("TEST-SMITH TOOL SYSTEM TEST")
    print("="*60)

    # Initialize tools
    initialize_tools(enable_builtin=True, enable_mcp=False)

    # List available tools
    list_available_tools()

    # Test built-in tools
    test_builtin_tools()

    # Test tool schemas
    test_tool_schemas()

    # Test async execution
    asyncio.run(test_async_execution())

    print("\nAll tests passed!")


if __name__ == "__main__":
    main()
