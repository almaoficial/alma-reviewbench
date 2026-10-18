"""ALMA ReviewBench adapter.

The package is dependency-free and deterministic in its DEFAULT mode
(``backend=mock``, US$0, no network).  A real model backend exists in
``agent/llm_reviewer.py`` but is fail-closed: it refuses to call anything
unless explicitly armed (ALLOW_REAL_LLM=1, API key, spend cap), and its
candidates pass through the same frozen ALMA evidence gate as the mock
reviewer's.
"""

__all__ = ["__version__"]

__version__ = "0.2.0"
