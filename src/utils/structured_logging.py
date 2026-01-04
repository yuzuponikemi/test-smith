"""
Structured Logging for Test-Smith

Provides structured, machine-readable logging using structlog.
Replaces print-based logging with contextual, queryable log events.

Features:
- JSON-formatted logs for production
- Human-readable console output for development
- Automatic context binding (node, query, thread_id)
- Performance metrics (execution time, token usage)
- Integration with existing ExecutionLogger

Usage:
    from src.utils.structured_logging import get_logger, log_node_execution

    # Get logger with context
    logger = get_logger(node="planner", query="What is TDD?")

    # Log events
    logger.info("query_allocated",
                rag_queries=["query1"],
                web_queries=["query2"],
                strategy="Use RAG for basics")

    # Context manager for node execution
    with log_node_execution("planner", state):
        result = planner_logic(state)
"""

import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

import structlog

# ==============================================
# Structlog Configuration
# ==============================================


def configure_structlog(json_logs: bool = None, log_level: str = None):
    """
    Configure structlog for the application.

    Args:
        json_logs: If True, output JSON logs. If None, uses env var STRUCTURED_LOGS_JSON (default: False for dev)
        log_level: Log level (DEBUG, INFO, WARNING, ERROR). If None, uses env var LOG_LEVEL (default: INFO)
    """
    # Determine output format
    if json_logs is None:
        json_logs = os.getenv("STRUCTURED_LOGS_JSON", "false").lower() == "true"

    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure processors
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add context from thread-local storage
        structlog.contextvars.merge_contextvars,
        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Uncomment for colorized output in terminals
        # structlog.dev.ConsoleRenderer() if not json_logs else structlog.processors.JSONRenderer(),
    ]

    # Final renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable console output for development
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=structlog.dev.plain_traceback
            )
        )

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.make_filtering_bound_logger(_level_to_int(log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def _level_to_int(level: str) -> int:
    """Convert log level string to integer."""
    levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    return levels.get(level.upper(), 20)


# Initialize structlog on module import
configure_structlog()


# ==============================================
# Logger Factory
# ==============================================


def get_logger(name: str = None, **initial_context) -> structlog.BoundLogger:
    """
    Get a structured logger with optional initial context.

    Args:
        name: Logger name (typically module or node name)
        **initial_context: Initial context to bind to all log calls

    Returns:
        Bound logger with context

    Example:
        logger = get_logger("planner", query="What is TDD?", thread_id="abc-123")
        logger.info("query_allocated", rag_queries=2, web_queries=1)

        # Output (development):
        # 2025-01-24T10:30:45.123Z [info] query_allocated query=What is TDD? thread_id=abc-123 rag_queries=2 web_queries=1

        # Output (production JSON):
        # {"event": "query_allocated", "level": "info", "timestamp": "2025-01-24T10:30:45.123Z",
        #  "query": "What is TDD?", "thread_id": "abc-123", "rag_queries": 2, "web_queries": 1}
    """
    logger = structlog.get_logger(name)

    # Bind initial context
    if initial_context:
        logger = logger.bind(**initial_context)

    return logger


def get_node_logger(node_name: str, state: dict[str, Any]) -> structlog.BoundLogger:
    """
    Get a logger with node execution context automatically bound.

    Args:
        node_name: Name of the node (e.g., "planner", "analyzer")
        state: Current state dictionary containing query, thread_id, etc.

    Returns:
        Logger with node context bound

    Example:
        logger = get_node_logger("planner", state)
        logger.info("kb_check_complete", available=True, total_chunks=150)
    """
    # Extract common context from state
    context = {
        "node": node_name,
        "query": state.get("query", ""),
        "loop_count": state.get("loop_count", 0),
    }

    # Add thread_id if available
    if "thread_id" in state:
        context["thread_id"] = state["thread_id"]

    # Get model info
    from src.utils.logging_utils import get_current_model_info

    context["model"] = get_current_model_info()

    return get_logger(node_name, **context)


# ==============================================
# Context Managers
# ==============================================


@contextmanager
def log_node_execution(node_name: str, state: dict[str, Any]):
    """
    Context manager for logging node execution with automatic timing.

    Automatically logs:
    - Node start
    - Execution time
    - Success/failure
    - Node end

    Args:
        node_name: Name of the node
        state: Current state dictionary

    Yields:
        Logger instance bound with node context

    Example:
        with log_node_execution("planner", state) as logger:
            logger.info("kb_check_start")
            kb_info = check_kb_contents()
            logger.info("kb_check_complete", chunks=kb_info['total_chunks'])
            return result

        # Automatically logs:
        # - node_start (with timestamp)
        # - Your custom log events
        # - node_end (with execution_time_ms)
    """
    logger = get_node_logger(node_name, state)

    start_time = time.time()
    logger.info("node_start", node=node_name)

    try:
        yield logger
        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(
            "node_end",
            node=node_name,
            execution_time_ms=round(execution_time_ms, 2),
            status="success",
        )

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(
            "node_end",
            node=node_name,
            execution_time_ms=round(execution_time_ms, 2),
            status="error",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise


@contextmanager
def log_performance(logger: structlog.BoundLogger, operation: str, **extra_context):
    """
    Context manager for performance measurement.

    Args:
        logger: Structured logger instance
        operation: Name of the operation being measured
        **extra_context: Additional context to log

    Yields:
        None

    Example:
        with log_performance(logger, "kb_retrieval", collection="research_agent"):
            results = vectorstore.similarity_search(query, k=5)

        # Logs: {"event": "operation_complete", "operation": "kb_retrieval",
        #        "duration_ms": 123.45, "collection": "research_agent"}
    """
    start_time = time.time()

    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "operation_complete",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **extra_context,
        )


# ==============================================
# Decorators
# ==============================================


def log_function_call(func):
    """
    Decorator to log function calls with arguments and execution time.

    Example:
        @log_function_call
        def my_function(arg1, arg2):
            return arg1 + arg2

        # Logs: function_call, function_return (with execution time)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        # Log function call
        logger.debug(
            "function_call",
            function=func.__name__,
            args=args[:3] if len(args) <= 3 else f"{len(args)} args",  # Avoid logging huge args
            kwargs=list(kwargs.keys()),
        )

        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            logger.debug(
                "function_return",
                function=func.__name__,
                duration_ms=round(duration_ms, 2),
                status="success",
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                "function_return",
                function=func.__name__,
                duration_ms=round(duration_ms, 2),
                status="error",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    return wrapper


# ==============================================
# Helper Functions
# ==============================================


def log_query_allocation(
    logger: structlog.BoundLogger, rag_queries: list, web_queries: list, strategy: str
):
    """
    Log query allocation in a standardized format.

    Args:
        logger: Structured logger instance
        rag_queries: List of RAG queries
        web_queries: List of web queries
        strategy: Allocation strategy reasoning
    """
    logger.info(
        "query_allocation",
        rag_query_count=len(rag_queries),
        web_query_count=len(web_queries),
        total_queries=len(rag_queries) + len(web_queries),
        strategy=strategy[:200],  # Truncate long strategies
        rag_queries=rag_queries,
        web_queries=web_queries,
    )


def log_evaluation_result(
    logger: structlog.BoundLogger, is_sufficient: bool, reason: str, loop_count: int
):
    """
    Log evaluation result in a standardized format.

    Args:
        logger: Structured logger instance
        is_sufficient: Whether information is sufficient
        reason: Evaluation reasoning
        loop_count: Current iteration count
    """
    logger.info(
        "evaluation_complete",
        is_sufficient=is_sufficient,
        reason=reason[:200],  # Truncate long reasons
        loop_count=loop_count,
        decision="synthesize" if is_sufficient else "refine",
    )


def log_analysis_summary(
    logger: structlog.BoundLogger,
    web_result_count: int,
    rag_result_count: int,
    code_result_count: int = 0,
):
    """
    Log analysis summary in a standardized format.

    Args:
        logger: Structured logger instance
        web_result_count: Number of web search results
        rag_result_count: Number of RAG retrieval results
        code_result_count: Number of code execution results
    """
    logger.info(
        "analysis_start",
        web_results=web_result_count,
        rag_results=rag_result_count,
        code_results=code_result_count,
        total_results=web_result_count + rag_result_count + code_result_count,
    )


def log_kb_status(logger: structlog.BoundLogger, kb_info: dict[str, Any]):
    """
    Log knowledge base status in a standardized format.

    Args:
        logger: Structured logger instance
        kb_info: Knowledge base information dictionary
    """
    logger.info(
        "kb_status",
        available=kb_info.get("available", False),
        total_chunks=kb_info.get("total_chunks", 0),
        document_count=len(kb_info.get("document_types", [])),
        summary=kb_info.get("summary", ""),
    )


# ==============================================
# File Logging (for structured logs)
# ==============================================


def setup_file_logging(log_dir: str = "logs/structured", _json_format: bool = True):
    """
    Set up file-based structured logging.

    Args:
        log_dir: Directory to store log files
        json_format: If True, use JSON format. If False, use pretty-printed format.

    Returns:
        Path to the log file
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"structured_{timestamp}.log"

    # Note: For production file logging, consider using python-json-logger
    # or configuring structlog with FileHandler
    # This is a simplified implementation

    return log_file


# ==============================================
# Backward Compatibility
# ==============================================


def print_node_header_structured(node_name: str, state: dict[str, Any] | None = None):
    """
    Structured logging version of print_node_header.

    Logs node start with model information.
    Maintains backward compatibility with old print_node_header.

    Args:
        node_name: Name of the node
        state: Optional state dictionary for additional context
    """
    from src.utils.logging_utils import get_current_model_info

    logger = get_node_logger(node_name, state) if state else get_logger(node_name)

    model_info = get_current_model_info()

    # Log structured event
    logger.info("node_header", node=node_name, model=model_info)

    # Also print for visual feedback (can be disabled in production)
    print(f"---{node_name} ({model_info})---")
