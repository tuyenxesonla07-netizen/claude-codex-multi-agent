# tools/__init__.py

"""
Tools layer — compiler, llm, messaging, quality, stores, agent.

This file makes `tools` a regular Python package so that
`from tools.xxx import ...` works reliably across all tooling
(pytest, mypy, packaging, etc.).
"""

from tools.llm import create_llm_provider
from tools.compiler import PipelineCompiler
from tools.messaging import MessageBus, Message, Topic
from tools.quality import QualityEvaluator, ReviewResult, ConvergenceDetector

__all__ = [
    "create_llm_provider",
    "PipelineCompiler",
    "MessageBus",
    "Message",
    "Topic",
    "QualityEvaluator",
    "ReviewResult",
    "ConvergenceDetector",
]
