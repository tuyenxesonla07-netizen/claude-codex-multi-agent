# tools/agent/__init__.py

"""
Agent 执行层 — 负责调用真实 LLM 生成代码

tools/agent/claude_code.py  → ClaudeCodeExecutor（真实 LLM 代码生成）
"""

from tools.agent.claude_code import ClaudeCodeExecutor

__all__ = ["ClaudeCodeExecutor"]
