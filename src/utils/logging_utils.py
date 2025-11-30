"""
Logging and Output Management Utilities

This module provides centralized logging and output management for Test-Smith.
It handles:
- Execution logs (detailed node-by-node execution traces)
- Final research reports (markdown output)
- Debug information
- Performance metrics

Usage:
    from src.utils.logging_utils import setup_execution_logger, save_report

    logger = setup_execution_logger("my_query")
    logger.log_node_start("master_planner")
    # ... do work ...
    logger.log_node_end("master_planner", {"execution_mode": "hierarchical"})

    save_report(report_content, "my_query")
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def get_current_model_info() -> str:
    """
    Get information about currently configured LLM provider and model.

    Returns:
        String describing the current model (e.g., "gemini/gemini-2.5-flash" or "ollama/llama3+command-r")
    """
    from dotenv import load_dotenv

    load_dotenv()

    provider = os.getenv("MODEL_PROVIDER", "ollama")

    if provider == "gemini":
        from src.models import DEFAULT_GEMINI_MODEL

        return f"gemini/{DEFAULT_GEMINI_MODEL}"
    else:
        # Ollama uses different models for different tasks
        return "ollama/llama3+command-r"


def print_node_header(node_name: str):
    """
    Print a standardized node header with model information.

    Shows which LLM model is being used for this node execution.

    Example:
        print_node_header("MASTER PLANNER")
        # Outputs: ---MASTER PLANNER (ollama/llama3+command-r)---

    Args:
        node_name: Name of the node (e.g., "MASTER PLANNER", "SYNTHESIZER")
    """
    model_info = get_current_model_info()
    print(f"---{node_name} ({model_info})---")


class ExecutionLogger:
    """
    Logger for tracking execution flow through the LangGraph workflow.

    Logs are saved to: logs/execution_YYYYMMDD_HHMMSS_<sanitized_query>.log
    """

    def __init__(self, query: str, thread_id: str):
        self.query = query
        self.thread_id = thread_id
        self.start_time = datetime.now()

        # Create logs directory if it doesn't exist
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)

        # Generate log filename
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        sanitized_query = self._sanitize_filename(query[:50])
        self.log_file = self.logs_dir / f"execution_{timestamp}_{sanitized_query}.log"

        # Initialize log file
        self._write_header()

    def _sanitize_filename(self, text: str) -> str:
        """Convert text to safe filename."""
        # Replace unsafe characters
        safe = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in text)
        # Replace spaces with underscores
        safe = safe.replace(" ", "_")
        # Remove consecutive underscores
        while "__" in safe:
            safe = safe.replace("__", "_")
        return safe.strip("_")

    def _write_header(self):
        """Write log file header."""
        header = f"""{"=" * 80}
Test-Smith Execution Log
{"=" * 80}
Query: {self.query}
Thread ID: {self.thread_id}
Start Time: {self.start_time.isoformat()}
{"=" * 80}

"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(header)

    def log(self, message: str, level: str = "INFO"):
        """Write a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {level}: {message}\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)

        # Also print to console
        print(message)

    def log_node_start(self, node_name: str):
        """Log the start of a node execution with model info."""
        model_info = get_current_model_info()
        self.log(f"\n--- {node_name.upper()} ({model_info}) ---", "NODE")

    def log_node_end(self, node_name: str, output: dict[str, Any]):
        """Log the end of a node execution with its output."""
        # Format output for logging (truncate large values)
        formatted_output = self._format_output(output)
        self.log(f"Output from '{node_name}':\n{formatted_output}", "NODE")

    def log_subtask(self, subtask_id: str, subtask_info: dict[str, Any]):
        """Log subtask information."""
        self.log(f"\n━━━ Subtask: {subtask_id} ━━━", "SUBTASK")
        for key, value in subtask_info.items():
            self.log(f"  {key}: {value}")

    def log_master_plan(self, master_plan: dict[str, Any]):
        """Log the master plan details."""
        self.log("\n" + "=" * 80, "MASTER_PLAN")
        self.log(f"Complexity: {'COMPLEX' if master_plan.get('is_complex') else 'SIMPLE'}")
        self.log(f"Execution Mode: {master_plan.get('execution_mode')}")

        if master_plan.get("is_complex"):
            subtasks = master_plan.get("subtasks", [])
            self.log(f"Subtasks: {len(subtasks)}")
            for i, subtask in enumerate(subtasks, 1):
                self.log(f"\n  Subtask {i}: {subtask['subtask_id']}")
                self.log(f"    Description: {subtask['description']}")
                self.log(f"    Focus: {subtask['focus_area']}")
                self.log(
                    f"    Priority: {subtask['priority']}, Importance: {subtask['estimated_importance']}"
                )
                if subtask.get("dependencies"):
                    self.log(f"    Dependencies: {subtask['dependencies']}")

        self.log("=" * 80 + "\n")

    def log_queries(self, rag_queries: list, web_queries: list, strategy: str):
        """Log query allocation."""
        self.log(f"\nAllocation Strategy: {strategy}")
        self.log(f"RAG Queries ({len(rag_queries)}): {rag_queries}")
        self.log(f"Web Queries ({len(web_queries)}): {web_queries}")

    def log_error(self, error: Exception, context: str = ""):
        """Log an error."""
        self.log(f"ERROR in {context}: {type(error).__name__}: {str(error)}", "ERROR")

    def finalize(self, _final_report: str):
        """Write final summary and close log."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        footer = f"""
{"=" * 80}
Execution Complete
{"=" * 80}
End Time: {end_time.isoformat()}
Duration: {duration:.2f} seconds
Log File: {self.log_file}
{"=" * 80}
"""

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(footer)

        self.log(f"Execution completed in {duration:.2f}s", "INFO")
        self.log(f"Full log saved to: {self.log_file}")

    def _format_output(self, output: dict[str, Any], max_length: int = 200) -> str:
        """Format output dictionary for logging, truncating long values."""
        formatted = []
        for key, value in output.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                str_val = str(value)
                if len(str_val) > max_length:
                    str_val = str_val[:max_length] + "..."
                formatted.append(f"  {key}: {str_val}")
            elif isinstance(value, (list, dict)):
                # For complex types, show summary
                if isinstance(value, list):
                    formatted.append(f"  {key}: [{len(value)} items]")
                else:
                    formatted.append(f"  {key}: {{{len(value)} keys}}")
            else:
                formatted.append(f"  {key}: <{type(value).__name__}>")

        return "\n".join(formatted)


def setup_execution_logger(query: str, thread_id: str) -> ExecutionLogger:
    """
    Create and return an ExecutionLogger instance.

    Args:
        query: The user's query
        thread_id: The thread ID for this execution

    Returns:
        ExecutionLogger instance
    """
    return ExecutionLogger(query, thread_id)


def save_report(
    report_content: str,
    query: str,
    execution_mode: str = "simple",
    metadata: Optional[dict[str, Any]] = None,
) -> Path:
    """
    Save the final research report to a markdown file.

    Args:
        report_content: The markdown report content
        query: The original query
        execution_mode: "simple" or "hierarchical"
        metadata: Optional metadata to include in report header

    Returns:
        Path to the saved report file
    """
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Generate report filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_query = ExecutionLogger(query, "temp")._sanitize_filename(query[:50])
    report_file = reports_dir / f"report_{timestamp}_{execution_mode}_{sanitized_query}.md"

    # Build report with metadata header
    full_report = _build_report_with_metadata(report_content, query, execution_mode, metadata)

    # Save report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"\n{'=' * 80}")
    print(f"Report saved to: {report_file}")
    print(f"{'=' * 80}\n")

    return report_file


def _build_report_with_metadata(
    content: str, query: str, execution_mode: str, metadata: Optional[dict[str, Any]]
) -> str:
    """Build complete report with metadata header."""

    header = f"""---
generated_by: Test-Smith v2.0-alpha
execution_mode: {execution_mode}
timestamp: {datetime.now().isoformat()}
query: "{query}"
"""

    if metadata:
        for key, value in metadata.items():
            if isinstance(value, str):
                header += f'{key}: "{value}"\n'
            else:
                header += f"{key}: {value}\n"

    header += "---\n\n"

    return header + content


def get_recent_reports(limit: int = 10, execution_mode: Optional[str] = None) -> list[Path]:
    """
    Get list of recent report files.

    Args:
        limit: Maximum number of reports to return
        execution_mode: Filter by execution mode ("simple" or "hierarchical")

    Returns:
        List of Path objects for report files, sorted by modification time (newest first)
    """
    reports_dir = Path("reports")
    if not reports_dir.exists():
        return []

    # Get all markdown files
    reports = list(reports_dir.glob("report_*.md"))

    # Filter by execution mode if specified
    if execution_mode:
        reports = [r for r in reports if f"_{execution_mode}_" in r.name]

    # Sort by modification time (newest first)
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return reports[:limit]


def get_recent_logs(limit: int = 10) -> list[Path]:
    """
    Get list of recent log files.

    Args:
        limit: Maximum number of logs to return

    Returns:
        List of Path objects for log files, sorted by modification time (newest first)
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return []

    # Get all log files
    logs = list(logs_dir.glob("execution_*.log"))

    # Sort by modification time (newest first)
    logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return logs[:limit]


def cleanup_old_files(days: int = 30, dry_run: bool = True) -> dict[str, int]:
    """
    Clean up old log and report files.

    Args:
        days: Delete files older than this many days
        dry_run: If True, only report what would be deleted without deleting

    Returns:
        Dictionary with counts of deleted files
    """
    from datetime import timedelta

    cutoff_time = datetime.now() - timedelta(days=days)
    cutoff_timestamp = cutoff_time.timestamp()

    deleted = {"logs": 0, "reports": 0}

    # Check logs
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("execution_*.log"):
            if log_file.stat().st_mtime < cutoff_timestamp:
                if dry_run:
                    print(f"Would delete: {log_file}")
                else:
                    log_file.unlink()
                deleted["logs"] += 1

    # Check reports
    reports_dir = Path("reports")
    if reports_dir.exists():
        for report_file in reports_dir.glob("report_*.md"):
            if report_file.stat().st_mtime < cutoff_timestamp:
                if dry_run:
                    print(f"Would delete: {report_file}")
                else:
                    report_file.unlink()
                deleted["reports"] += 1

    return deleted
