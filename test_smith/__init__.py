"""Public Python API for test-smith.

This package is a thin façade over the internal ``src.*`` modules so that
external consumers can ``from test_smith.agents.react import ReActAgent``
without depending on the internal layout. The actual implementation still
lives under ``src/``; do not put logic in this package.
"""

__all__ = ["__version__"]

__version__ = "2.3.0"
