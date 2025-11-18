"""
Built-in Function Tools for Test-Smith

These tools provide computational and analytical capabilities
that enhance the research workflow.
"""

import json
import math
import statistics
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# === Tool Input Schemas ===

class CalculatorInput(BaseModel):
    """Input for the calculator tool"""
    expression: str = Field(description="Mathematical expression to evaluate (e.g., '2 + 2 * 3')")


class StatisticsInput(BaseModel):
    """Input for the statistics tool"""
    numbers: list[float] = Field(description="List of numbers to analyze")
    operation: str = Field(
        description="Statistical operation: 'mean', 'median', 'mode', 'stdev', 'variance', 'summary'"
    )


class JSONParserInput(BaseModel):
    """Input for the JSON parser tool"""
    json_string: str = Field(description="JSON string to parse and analyze")
    query: Optional[str] = Field(
        default=None,
        description="Optional dot-notation query path (e.g., 'data.items[0].name')"
    )


class UnitConverterInput(BaseModel):
    """Input for the unit converter tool"""
    value: float = Field(description="The value to convert")
    from_unit: str = Field(description="Source unit (e.g., 'km', 'miles', 'celsius', 'fahrenheit')")
    to_unit: str = Field(description="Target unit")


class TextAnalyzerInput(BaseModel):
    """Input for the text analyzer tool"""
    text: str = Field(description="Text to analyze")
    analysis_type: str = Field(
        description="Type of analysis: 'word_count', 'char_count', 'sentence_count', 'readability', 'summary'"
    )


class DateCalculatorInput(BaseModel):
    """Input for the date calculator tool"""
    operation: str = Field(
        description="Operation: 'diff' (difference between dates), 'add' (add days to date)"
    )
    date1: str = Field(description="First date in YYYY-MM-DD format")
    date2: Optional[str] = Field(default=None, description="Second date for diff operation")
    days: Optional[int] = Field(default=None, description="Number of days for add operation")


class CodeRunnerInput(BaseModel):
    """Input for the code runner tool"""
    code: str = Field(description="Python code to execute")
    timeout: int = Field(default=30, description="Execution timeout in seconds")


# === Tool Implementations ===

@tool("calculator", args_schema=CalculatorInput)
def calculator(expression: str) -> str:
    """
    Evaluate mathematical expressions safely.

    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, exp, abs, round
    Example: "sqrt(16) + 2**3" returns "12.0"
    """
    # Safe evaluation with limited namespace
    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "pow": pow,
    }

    try:
        # Remove potentially dangerous characters
        safe_expr = expression.replace("__", "")
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


@tool("statistics_analyzer", args_schema=StatisticsInput)
def statistics_analyzer(numbers: list[float], operation: str) -> str:
    """
    Perform statistical analysis on a list of numbers.

    Operations: mean, median, mode, stdev, variance, summary
    """
    if not numbers:
        return "Error: Empty list provided"

    try:
        if operation == "mean":
            result = statistics.mean(numbers)
            return f"Mean: {result:.4f}"

        elif operation == "median":
            result = statistics.median(numbers)
            return f"Median: {result:.4f}"

        elif operation == "mode":
            try:
                result = statistics.mode(numbers)
                return f"Mode: {result}"
            except statistics.StatisticsError:
                return "No unique mode found"

        elif operation == "stdev":
            if len(numbers) < 2:
                return "Error: Need at least 2 numbers for standard deviation"
            result = statistics.stdev(numbers)
            return f"Standard Deviation: {result:.4f}"

        elif operation == "variance":
            if len(numbers) < 2:
                return "Error: Need at least 2 numbers for variance"
            result = statistics.variance(numbers)
            return f"Variance: {result:.4f}"

        elif operation == "summary":
            summary = {
                "count": len(numbers),
                "mean": statistics.mean(numbers),
                "median": statistics.median(numbers),
                "min": min(numbers),
                "max": max(numbers),
                "range": max(numbers) - min(numbers),
            }
            if len(numbers) >= 2:
                summary["stdev"] = statistics.stdev(numbers)
            return f"Statistical Summary:\n{json.dumps(summary, indent=2)}"

        else:
            return f"Error: Unknown operation '{operation}'"

    except Exception as e:
        return f"Error in statistical analysis: {str(e)}"


@tool("json_parser", args_schema=JSONParserInput)
def json_parser(json_string: str, query: Optional[str] = None) -> str:
    """
    Parse JSON and optionally extract values using dot notation.

    Example query: "data.items[0].name" extracts nested value
    """
    try:
        data = json.loads(json_string)

        if query:
            # Navigate the JSON using dot notation
            parts = query.replace("[", ".").replace("]", "").split(".")
            result = data

            for part in parts:
                if not part:
                    continue
                if isinstance(result, dict):
                    result = result.get(part)
                elif isinstance(result, list):
                    try:
                        result = result[int(part)]
                    except (ValueError, IndexError):
                        return f"Error: Invalid index '{part}'"
                else:
                    return f"Error: Cannot navigate into {type(result)}"

                if result is None:
                    return f"Error: Path '{query}' not found"

            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            return str(result)

        # Return pretty-printed JSON
        return json.dumps(data, indent=2)

    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool("unit_converter", args_schema=UnitConverterInput)
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert between common units.

    Supports: length (km, m, miles, feet), temperature (celsius, fahrenheit, kelvin),
    weight (kg, lbs, oz), data (bytes, kb, mb, gb)
    """
    conversions = {
        # Length (base: meters)
        ("km", "m"): lambda x: x * 1000,
        ("m", "km"): lambda x: x / 1000,
        ("miles", "km"): lambda x: x * 1.60934,
        ("km", "miles"): lambda x: x / 1.60934,
        ("feet", "m"): lambda x: x * 0.3048,
        ("m", "feet"): lambda x: x / 0.3048,

        # Temperature
        ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("celsius", "kelvin"): lambda x: x + 273.15,
        ("kelvin", "celsius"): lambda x: x - 273.15,

        # Weight (base: kg)
        ("kg", "lbs"): lambda x: x * 2.20462,
        ("lbs", "kg"): lambda x: x / 2.20462,
        ("kg", "oz"): lambda x: x * 35.274,
        ("oz", "kg"): lambda x: x / 35.274,

        # Data (base: bytes)
        ("bytes", "kb"): lambda x: x / 1024,
        ("kb", "bytes"): lambda x: x * 1024,
        ("kb", "mb"): lambda x: x / 1024,
        ("mb", "kb"): lambda x: x * 1024,
        ("mb", "gb"): lambda x: x / 1024,
        ("gb", "mb"): lambda x: x * 1024,
    }

    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    key = (from_unit, to_unit)
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.4f} {to_unit}"

    return f"Error: Conversion from '{from_unit}' to '{to_unit}' not supported"


@tool("text_analyzer", args_schema=TextAnalyzerInput)
def text_analyzer(text: str, analysis_type: str) -> str:
    """
    Analyze text for various metrics.

    Analysis types: word_count, char_count, sentence_count, readability, summary
    """
    if not text:
        return "Error: Empty text provided"

    try:
        if analysis_type == "word_count":
            words = text.split()
            return f"Word count: {len(words)}"

        elif analysis_type == "char_count":
            return f"Character count: {len(text)} (without spaces: {len(text.replace(' ', ''))})"

        elif analysis_type == "sentence_count":
            # Simple sentence detection
            sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
            return f"Sentence count: {len(sentences)}"

        elif analysis_type == "readability":
            # Simple Flesch-Kincaid approximation
            words = text.split()
            sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]

            if not sentences:
                return "Error: No sentences found"

            avg_sentence_length = len(words) / len(sentences)

            # Estimate syllables (rough approximation)
            syllables = sum(max(1, len([c for c in word.lower() if c in 'aeiou'])) for word in words)
            avg_syllables = syllables / len(words) if words else 0

            # Flesch Reading Ease
            score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables

            if score >= 90:
                level = "Very Easy (5th grade)"
            elif score >= 80:
                level = "Easy (6th grade)"
            elif score >= 70:
                level = "Fairly Easy (7th grade)"
            elif score >= 60:
                level = "Standard (8th-9th grade)"
            elif score >= 50:
                level = "Fairly Difficult (10th-12th grade)"
            elif score >= 30:
                level = "Difficult (College)"
            else:
                level = "Very Difficult (Graduate)"

            return f"Readability Score: {score:.1f}\nLevel: {level}\nAvg sentence length: {avg_sentence_length:.1f} words"

        elif analysis_type == "summary":
            words = text.split()
            sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]

            summary = {
                "characters": len(text),
                "words": len(words),
                "sentences": len(sentences),
                "paragraphs": text.count("\n\n") + 1,
                "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            }
            return f"Text Analysis Summary:\n{json.dumps(summary, indent=2)}"

        else:
            return f"Error: Unknown analysis type '{analysis_type}'"

    except Exception as e:
        return f"Error in text analysis: {str(e)}"


@tool("date_calculator", args_schema=DateCalculatorInput)
def date_calculator(
    operation: str,
    date1: str,
    date2: Optional[str] = None,
    days: Optional[int] = None
) -> str:
    """
    Calculate date differences or add days to dates.

    Operations:
    - 'diff': Calculate days between date1 and date2
    - 'add': Add days to date1
    """
    from datetime import datetime, timedelta

    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")

        if operation == "diff":
            if not date2:
                return "Error: date2 required for diff operation"
            d2 = datetime.strptime(date2, "%Y-%m-%d")
            diff = abs((d2 - d1).days)
            return f"Difference: {diff} days"

        elif operation == "add":
            if days is None:
                return "Error: days required for add operation"
            result = d1 + timedelta(days=days)
            return f"Result: {result.strftime('%Y-%m-%d')}"

        else:
            return f"Error: Unknown operation '{operation}'"

    except ValueError as e:
        return f"Error: Invalid date format. Use YYYY-MM-DD. {str(e)}"


@tool("python_executor", args_schema=CodeRunnerInput)
def python_executor(code: str, timeout: int = 30) -> str:
    """
    Execute Python code in a sandboxed environment.

    WARNING: Limited execution - only safe operations allowed.
    For security, imports are restricted and some operations are blocked.
    """
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr

    # Restricted builtins
    safe_builtins = {
        'abs': abs, 'all': all, 'any': any, 'bool': bool,
        'dict': dict, 'enumerate': enumerate, 'filter': filter,
        'float': float, 'int': int, 'len': len, 'list': list,
        'map': map, 'max': max, 'min': min, 'print': print,
        'range': range, 'round': round, 'set': set, 'sorted': sorted,
        'str': str, 'sum': sum, 'tuple': tuple, 'zip': zip,
        'True': True, 'False': False, 'None': None,
    }

    # Safe modules
    safe_modules = {
        'math': math,
        'statistics': statistics,
        'json': json,
    }

    # Check for dangerous patterns
    dangerous = ['import', 'exec', 'eval', 'compile', '__', 'open', 'file', 'os', 'sys', 'subprocess']
    for pattern in dangerous:
        if pattern in code.lower():
            return f"Error: '{pattern}' is not allowed for security reasons"

    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, {"__builtins__": safe_builtins, **safe_modules})

        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()

        result = ""
        if output:
            result += f"Output:\n{output}"
        if errors:
            result += f"\nErrors:\n{errors}"

        return result if result else "Code executed successfully (no output)"

    except Exception as e:
        return f"Execution error: {str(e)}"


# === Registration Function ===

def register_builtin_tools(registry) -> None:
    """
    Register all built-in tools with the registry.

    Args:
        registry: ToolRegistry instance
    """
    print("Registering built-in function tools...")

    tools = [
        calculator,
        statistics_analyzer,
        json_parser,
        unit_converter,
        text_analyzer,
        date_calculator,
        python_executor,
    ]

    for tool_func in tools:
        registry.register_function_tool(tool_func)

    print(f"  Registered {len(tools)} built-in tools")
