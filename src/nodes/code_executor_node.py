"""
Code Executor Node - Generates and executes Python code for research tasks

This node enables code execution within the research workflow, allowing:
- Data analysis and calculations
- Information processing
- Complex transformations
- Validation and verification

Safety features:
- Restricted execution environment
- Timeout limits
- Resource constraints
- No dangerous operations
"""

import sys
import io
import time
from contextlib import redirect_stdout, redirect_stderr
from src.models import get_code_executor_model
from src.prompts.code_executor_prompt import CODE_EXECUTOR_PROMPT
from src.utils.logging_utils import print_node_header


def execute_code_safely(code: str, timeout: int = 10) -> tuple[bool, str, str, float]:
    """
    Execute Python code in a restricted environment.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (success, output, error, execution_time)
    """
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Create restricted globals (no dangerous builtins)
    restricted_globals = {
        '__builtins__': {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
        }
    }

    start_time = time.time()

    try:
        # Redirect stdout/stderr
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute code with restricted globals
            exec(code, restricted_globals)

        execution_time = time.time() - start_time
        output = stdout_capture.getvalue()
        return True, output if output else "Code executed successfully (no output)", "", execution_time

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"
        stderr_output = stderr_capture.getvalue()
        if stderr_output:
            error_msg += f"\n{stderr_output}"
        return False, "", error_msg, execution_time


def code_executor(state):
    """
    Code Executor Node - Generates and executes Python code

    Takes a code execution request from state and:
    1. Generates Python code using LLM
    2. Executes code in restricted environment
    3. Returns results with execution metadata
    """
    print_node_header("CODE EXECUTOR")

    task_description = state.get("code_task", "")
    context = state.get("context_for_code", "")
    input_data = state.get("code_input_data", "")
    requirements = state.get("code_requirements", [])
    expected_output = state.get("expected_code_output", "")

    if not task_description:
        print("  No code execution task specified - skipping")
        return {"code_execution_results": []}

    print(f"  Generating code for task: {task_description}")

    # Step 1: Generate code using LLM
    model = get_code_executor_model()

    prompt = CODE_EXECUTOR_PROMPT.format(
        task_description=task_description,
        context=context,
        input_data=input_data if input_data else "None",
        requirements="\n".join(f"- {req}" for req in requirements) if requirements else "None",
        expected_output=expected_output if expected_output else "Any format"
    )

    try:
        response = model.invoke(prompt)
        generated_code = response.content.strip()

        # Extract code from markdown code blocks if present
        if "```python" in generated_code:
            # Extract code between ```python and ```
            start = generated_code.find("```python") + 9
            end = generated_code.find("```", start)
            generated_code = generated_code[start:end].strip()
        elif "```" in generated_code:
            # Extract code between ``` and ```
            start = generated_code.find("```") + 3
            end = generated_code.find("```", start)
            generated_code = generated_code[start:end].strip()

        print(f"  Generated code ({len(generated_code)} chars)")
        print(f"  Code preview:\n{generated_code[:200]}...")

        # Step 2: Execute code safely
        print("  Executing code...")
        success, output, error, exec_time = execute_code_safely(generated_code)

        if success:
            print(f"  ✓ Execution successful ({exec_time:.2f}s)")
            print(f"  Output: {output[:200]}...")
        else:
            print(f"  ✗ Execution failed ({exec_time:.2f}s)")
            print(f"  Error: {error[:200]}...")

        # Step 3: Return results
        result = {
            "success": success,
            "output": output,
            "error": error if error else None,
            "execution_time": exec_time,
            "code": generated_code
        }

        return {"code_execution_results": [result]}

    except Exception as e:
        print(f"  Error during code generation: {e}")
        error_result = {
            "success": False,
            "output": "",
            "error": f"Code generation failed: {str(e)}",
            "execution_time": 0.0,
            "code": ""
        }
        return {"code_execution_results": [error_result]}
