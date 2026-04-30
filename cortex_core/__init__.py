"""
CortexOS Core Framework
========================
Backend primitives for SimpliXio, a decision system that turns
scattered thoughts, project noise, and open loops into 3 priorities
and one next action.

Modules:
    engine      – Central orchestrator
    knowledge   – Knowledge note CRUD & search
    pipeline    – Step-based pipeline runner
    digest      – Weekly digest processing
    posts       – Social post generation
    scoring     – Article & digest quality evaluation
    memory      – User profile & context memory
    focus       – Daily focus brief generator
    llm         – LLM provider abstraction
    config      – Runtime configuration
"""

__version__ = "0.1.0"
__author__ = "Pierre-Henry Soria"

from cortex_core.config import CortexConfig
from cortex_core.engine import CortexEngine

__all__ = ["CortexConfig", "CortexEngine", "__version__"]
