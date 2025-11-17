"""
Langfuse integration for LangGraph observability and tracing.

This module provides utilities to configure Langfuse callbacks for tracking
LLM calls, graph executions, and agent workflows.
"""

import os
from typing import Optional
from langfuse import Langfuse
from langfuse.callback import CallbackHandler


def is_langfuse_enabled() -> bool:
    """
    Check if Langfuse tracing is enabled via environment variables.

    Returns:
        bool: True if Langfuse is configured and enabled
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() in ["true", "1", "yes"]

    return enabled and bool(public_key) and bool(secret_key)


def get_langfuse_callback_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> Optional[CallbackHandler]:
    """
    Initialize and return a Langfuse callback handler if configured.

    Args:
        session_id: Optional session/thread ID for grouping traces
        user_id: Optional user identifier
        metadata: Optional metadata to attach to traces

    Returns:
        CallbackHandler if Langfuse is enabled, None otherwise
    """
    if not is_langfuse_enabled():
        return None

    try:
        # Get configuration from environment
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        # Initialize Langfuse client
        langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )

        # Create callback handler
        callback = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        return callback

    except Exception as e:
        print(f"Warning: Failed to initialize Langfuse callback handler: {e}")
        print("Continuing without Langfuse tracing...")
        return None


def flush_langfuse():
    """
    Flush any pending Langfuse traces.
    Call this at the end of execution to ensure all traces are sent.
    """
    if is_langfuse_enabled():
        try:
            from langfuse import Langfuse
            langfuse_client = Langfuse()
            langfuse_client.flush()
        except Exception as e:
            print(f"Warning: Failed to flush Langfuse traces: {e}")
