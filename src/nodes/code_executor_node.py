"""
Code Executor Node - Generates and executes Python code for research tasks

This node enables code execution within the research workflow, allowing:
- Data analysis and calculations
- Information processing
- Complex transformations
- Validation and verification

Safety features (Docker sandbox - MCP-aligned architecture):
- Isolated Docker container execution (preferred)
- No network access (--network=none)
- Memory limit (512MB)
- CPU limit (1 core)
- Timeout protection (60 seconds)
- Fallback to restricted environment if Docker unavailable

Design philosophy:
- Implements MCP paradigm: "Code execution as independent service"
- Loaded only when code_execution graph is selected (0 tokens overhead otherwise)
- Reusable across different LLM applications via MCP protocol
"""

import io
import subprocess
import tempfile
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from src.models import get_code_executor_model
from src.prompts.code_executor_prompt import CODE_EXECUTOR_PROMPT
from src.utils.logging_utils import print_node_header


def check_docker_available() -> bool:
    """Check if Docker is available on the system"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def execute_code_in_docker(code: str, timeout: int = 60) -> tuple[bool, str, str, float]:
    """
    Execute Python code in a sandboxed Docker container (PR #10 approach).

    Security features:
    - No network access
    - Memory limit: 512MB
    - CPU limit: 1 core
    - Timeout: 60 seconds
    - Read-only filesystem

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (success, output, error, execution_time)
    """
    start_time = time.time()

    # Create temporary directory for code
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = Path(tmpdir) / "script.py"
        code_file.write_text(code)

        # Docker run command with security restrictions
        docker_cmd = [
            "docker",
            "run",
            "--rm",  # Remove container after execution
            "--network=none",  # No network access
            "--memory=512m",  # Memory limit
            "--cpus=1",  # CPU limit
            "--read-only",  # Read-only filesystem
            "--tmpfs",
            "/tmp:rw,size=100m",  # Temporary writable space
            "-v",
            f"{tmpdir}:/workspace:ro",  # Mount code as read-only
            "-w",
            "/workspace",
            "python:3.11-slim",  # Lightweight Python image
            "python",
            "script.py",
        ]

        try:
            result = subprocess.run(docker_cmd, capture_output=True, timeout=timeout, text=True)

            execution_time = time.time() - start_time

            if result.returncode == 0:
                output = (
                    result.stdout if result.stdout else "Code executed successfully (no output)"
                )
                return True, output, "", execution_time
            else:
                error = result.stderr if result.stderr else f"Exit code: {result.returncode}"
                return False, "", error, execution_time

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, "", f"Execution timeout ({timeout}s exceeded)", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, "", f"Docker execution error: {str(e)}", execution_time


def execute_code_safely(code: str, _timeout: int = 10) -> tuple[bool, str, str, float]:
    """
    Execute Python code in a restricted environment.

    Args:
        code: Python code to execute
        _timeout: Maximum execution time in seconds (unused in current implementation)

    Returns:
        Tuple of (success, output, error, execution_time)
    """
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Create restricted globals (no dangerous builtins)
    restricted_globals = {
        "__builtins__": {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "print": print,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
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
        return (
            True,
            output if output else "Code executed successfully (no output)",
            "",
            execution_time,
        )

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

    MCP-aligned implementation:
    - This node is loaded ONLY when code_execution graph is selected
    - Provides isolated code execution service
    - Can be externalized as MCP server in future

    Takes a code execution request from state and:
    1. Generates Python code using LLM
    2. Executes code in Docker sandbox (preferred) or fallback environment
    3. Returns results with execution metadata
    """
    print_node_header("CODE EXECUTOR")

    task_description = state.get("code_task", "")

    # If no explicit code_task, use the original query
    # (This happens when code_execution graph is auto-selected)
    if not task_description:
        task_description = state.get("query", "")
        if task_description:
            print(f"  Using query as code task: {task_description[:100]}...")
        else:
            print("  No code execution task or query - skipping")
            return {"code_execution_results": []}

    # Get context from analyzed data if available
    context = state.get("context_for_code", "")
    if not context:
        # Use analyzed data as context
        analyzed_data = state.get("analyzed_data", [])
        if analyzed_data:
            context = "\n\n".join(analyzed_data[:2])  # Use first 2 analyzed chunks
            print(f"  Using analyzed data as context ({len(context)} chars)")

    input_data = state.get("code_input_data", "")
    requirements = state.get("code_requirements", [])
    expected_output = state.get("expected_code_output", "")

    print(f"  Generating code for task: {task_description}")

    # Check Docker availability
    docker_available = check_docker_available()
    if docker_available:
        print("  ✓ Docker available - using sandboxed execution")
    else:
        print("  ⚠️  Docker unavailable - using fallback restricted environment")
        print("     (Development mode: Code executes WITHOUT full sandbox protections)")

    # Step 1: Generate code using LLM
    model = get_code_executor_model()

    prompt = CODE_EXECUTOR_PROMPT.format(
        task_description=task_description,
        context=context,
        input_data=input_data if input_data else "None",
        requirements="\n".join(f"- {req}" for req in requirements) if requirements else "None",
        expected_output=expected_output if expected_output else "Any format",
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

        # Step 2: Execute code safely (Docker preferred, fallback if unavailable)
        print("  Executing code...")
        if docker_available:
            success, output, error, exec_time = execute_code_in_docker(generated_code, timeout=60)
            execution_mode = "docker_sandbox"
        else:
            success, output, error, exec_time = execute_code_safely(generated_code, timeout=10)
            execution_mode = "restricted_fallback"

        if success:
            print(f"  ✓ Execution successful ({exec_time:.2f}s) [{execution_mode}]")
            print(f"  Output: {output[:200]}...")
        else:
            print(f"  ✗ Execution failed ({exec_time:.2f}s) [{execution_mode}]")
            print(f"  Error: {error[:200]}...")

        # Step 3: Return results
        result = {
            "success": success,
            "output": output,
            "error": error if error else None,
            "execution_time": exec_time,
            "execution_mode": execution_mode,
            "code": generated_code,
        }

        return {"code_execution_results": [result]}

    except Exception as e:
        print(f"  Error during code generation: {e}")
        error_result = {
            "success": False,
            "output": "",
            "error": f"Code generation failed: {str(e)}",
            "execution_time": 0.0,
            "execution_mode": "failed",
            "code": "",
        }
        return {"code_execution_results": [error_result]}
