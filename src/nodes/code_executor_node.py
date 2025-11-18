"""
Code executor node for running Python code in a sandboxed environment.

This node generates and executes Python code for quantitative analysis,
data processing, and visualization tasks during research.
"""

import os
import tempfile
import time
import subprocess
from pathlib import Path

from src.models import get_code_generator_model, get_code_result_analyzer_model
from src.utils.logging_utils import print_node_header
from src.prompts.code_executor_prompt import (
    CODE_GENERATOR_PROMPT,
    CODE_RESULT_ANALYZER_PROMPT
)
from src.schemas import GeneratedCode, CodeAnalysisResult


def execute_code_in_sandbox(code: str, timeout: int = 60) -> dict:
    """
    Execute Python code in a Docker sandbox for safety.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with execution results
    """
    # Create a temporary directory for code execution
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write code to file
        code_file = Path(temp_dir) / "script.py"
        code_file.write_text(code)

        # Create output directory for artifacts
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()

        # Docker command for sandboxed execution
        # Uses python:3.11-slim with common data science packages
        docker_cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "--network=none",  # No network access for security
            "--memory=512m",  # Memory limit
            "--cpus=1",  # CPU limit
            "-v", f"{temp_dir}:/app:ro",  # Mount code directory read-only
            "-v", f"{output_dir}:/output",  # Mount output directory
            "-w", "/app",
            "python:3.11-slim",
            "bash", "-c",
            # Install common packages and run the script
            f"""
            pip install -q pandas numpy matplotlib seaborn scipy requests 2>/dev/null && \
            cd /output && \
            python /app/script.py
            """
        ]

        start_time = time.time()

        try:
            # Execute with timeout
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            # Collect artifacts
            artifacts = []
            for artifact_file in output_dir.iterdir():
                if artifact_file.is_file():
                    artifacts.append(artifact_file.name)

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "execution_time_seconds": execution_time,
                "artifacts": artifacts
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "execution_time_seconds": timeout,
                "artifacts": []
            }
        except FileNotFoundError:
            # Docker not available, fall back to direct execution with warnings
            return execute_code_directly(code, timeout, temp_dir, output_dir)
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "execution_time_seconds": time.time() - start_time,
                "artifacts": []
            }


def execute_code_directly(code: str, timeout: int, temp_dir: str, output_dir: Path) -> dict:
    """
    Fallback: Execute code directly when Docker is not available.

    WARNING: This is less secure than Docker execution.
    Only use in development/trusted environments.
    """
    print("  Warning: Docker not available, using direct execution (less secure)")

    # Prepend output directory change to the code
    modified_code = f"""
import os
os.chdir('{output_dir}')

{code}
"""

    code_file = Path(temp_dir) / "script.py"
    code_file.write_text(modified_code)

    start_time = time.time()

    try:
        result = subprocess.run(
            ["python", str(code_file)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(output_dir)
        )

        execution_time = time.time() - start_time

        # Collect artifacts
        artifacts = []
        for artifact_file in output_dir.iterdir():
            if artifact_file.is_file():
                artifacts.append(artifact_file.name)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else "",
            "execution_time_seconds": execution_time,
            "artifacts": artifacts
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Execution timed out after {timeout} seconds",
            "execution_time_seconds": timeout,
            "artifacts": []
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"Execution error: {str(e)}",
            "execution_time_seconds": time.time() - start_time,
            "artifacts": []
        }


def code_executor_node(state: dict) -> dict:
    """
    Generate and execute Python code for quantitative analysis.

    This node:
    1. Generates Python code based on the task description
    2. Executes it in a sandboxed Docker environment
    3. Analyzes the results
    4. Returns findings to be integrated with research

    Args:
        state: Current graph state containing:
            - query: Original user query
            - code_task_description: What computation to perform
            - code_data_context: Data to process
            - analyzed_data: Research data collected so far

    Returns:
        State update with code execution results
    """
    print_node_header("CODE EXECUTOR")

    # Extract state
    query = state.get("query", "")
    task_description = state.get("code_task_description", "")
    data_context = state.get("code_data_context", "")

    if not task_description:
        print("  No task description provided, skipping code execution")
        return {
            "code_execution_results": "",
            "code_artifacts": []
        }

    print(f"  Task: {task_description[:80]}...")

    # Step 1: Generate code
    print("  Generating Python code...")
    code_gen_model = get_code_generator_model()

    try:
        # Try structured output first
        structured_model = code_gen_model.with_structured_output(GeneratedCode)
        prompt = CODE_GENERATOR_PROMPT.format(
            task_description=task_description,
            data_context=data_context
        )
        generated = structured_model.invoke(prompt)
        code = generated.code
        code_description = generated.description
    except Exception as e:
        # Fallback to raw generation
        print(f"  Warning: Structured generation failed, using fallback: {e}")
        prompt = CODE_GENERATOR_PROMPT.format(
            task_description=task_description,
            data_context=data_context
        )
        response = code_gen_model.invoke(prompt)
        code = response.content
        code_description = task_description

    print(f"  Generated {len(code.splitlines())} lines of code")

    # Step 2: Execute code in sandbox
    print("  Executing code in sandbox...")
    execution_result = execute_code_in_sandbox(code, timeout=60)

    status = "SUCCESS" if execution_result["success"] else "FAILED"
    print(f"  Execution: {status} ({execution_result['execution_time_seconds']:.2f}s)")

    if execution_result["artifacts"]:
        print(f"  Artifacts: {', '.join(execution_result['artifacts'])}")

    # Step 3: Analyze results
    print("  Analyzing execution results...")
    analyzer_model = get_code_result_analyzer_model()

    error_msg = f"Error: {execution_result['error']}" if execution_result["error"] else ""

    analysis_prompt = CODE_RESULT_ANALYZER_PROMPT.format(
        query=query,
        task_description=task_description,
        code=code,
        execution_output=execution_result["output"][:5000],  # Limit output size
        execution_status=status,
        error_message=error_msg
    )

    try:
        structured_analyzer = analyzer_model.with_structured_output(CodeAnalysisResult)
        analysis = structured_analyzer.invoke(analysis_prompt)

        # Format analysis for state
        analysis_text = f"""## Code Execution Analysis

**Task:** {code_description}

**Key Findings:**
{chr(10).join(f'- {finding}' for finding in analysis.key_findings)}

**Quantitative Results:**
{analysis.quantitative_results}

**Interpretation:**
{analysis.interpretation}

**Limitations:**
{chr(10).join(f'- {lim}' for lim in analysis.limitations) if analysis.limitations else 'None noted'}
"""
        if analysis.visualization_description:
            analysis_text += f"\n**Visualization:** {analysis.visualization_description}"

    except Exception as e:
        print(f"  Warning: Structured analysis failed, using raw output: {e}")
        response = analyzer_model.invoke(analysis_prompt)
        analysis_text = response.content

    print("  Code execution complete")

    return {
        "code_execution_results": analysis_text,
        "code_artifacts": execution_result["artifacts"],
        "code_output": execution_result["output"],
        "code_success": execution_result["success"]
    }
