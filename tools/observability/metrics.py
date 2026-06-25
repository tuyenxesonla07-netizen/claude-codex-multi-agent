# tools/observability/metrics.py

"""
流水线指标统计。

跟踪 Token 消耗、步骤数、延迟、每 Agent/每工具调用次数。
用于成本核算和性能优化。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineMetrics:
    """单次流水线运行的指标"""
    session_id: str = ""
    total_steps: int = 0
    total_tool_calls: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    per_agent_metrics: dict = field(default_factory=dict)
    per_tool_metrics: dict = field(default_factory=dict)

    def record_agent_call(self, agent_id: str, tokens: int = 0, latency_ms: float = 0):
        """记录 Agent 调用"""
        self.total_steps += 1
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms
        if agent_id not in self.per_agent_metrics:
            self.per_agent_metrics[agent_id] = {"calls": 0, "tokens": 0}
        self.per_agent_metrics[agent_id]["calls"] += 1
        self.per_agent_metrics[agent_id]["tokens"] += tokens

    def record_tool_call(self, tool_name: str, tokens: int = 0, latency_ms: float = 0):
        """记录工具调用"""
        self.total_tool_calls += 1
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms
        if tool_name not in self.per_tool_metrics:
            self.per_tool_metrics[tool_name] = {"calls": 0, "tokens": 0}
        self.per_tool_metrics[tool_name]["calls"] += 1
        self.per_tool_metrics[tool_name]["tokens"] += tokens

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "total_steps": self.total_steps,
            "total_tool_calls": self.total_tool_calls,
            "total_tokens": self.total_tokens,
            "total_latency_ms": round(self.total_latency_ms, 1),
            "per_agent": self.per_agent_metrics,
            "per_tool": self.per_tool_metrics,
        }
