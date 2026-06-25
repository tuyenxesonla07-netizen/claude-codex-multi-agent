# tools/hitl/audit.py

"""
审计日志 — 记录所有工具调用和高风险操作。

参考 customer-service-agent 的 ToolRuntime.audit_log：
- 每次工具调用记录：时间、工具名、参数（脱敏）、风险等级、审批结果、执行结果
- 支持按会话/工具查询
- 支持导出 JSON

用于合规审查、安全审计、问题追溯。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditLog:
    """
    审计日志。

    记录所有工具调用，支持查询和导出。
    持久化到 JSONL 文件（每行一条记录）。

    用法:
        audit = AuditLog("data/audit_log.jsonl")
        audit.record({
            "tool": "generate_code",
            "args": {"module": "auth"},
            "risk": "medium",
            "ok": True,
        })
        records = audit.query(session_id="s1")
    """

    def __init__(self, persist_path: str = "data/audit_log.jsonl"):
        self.persist_path = Path(persist_path) if persist_path else None
        self._records: list[dict] = []
        if self.persist_path and self.persist_path.exists():
            self._load()

    def record(self, event: dict) -> None:
        """
        记录一条审计事件。

        Args:
            event: 事件字典，可包含:
                - tool: 工具名
                - args: 参数（会自动脱敏）
                - risk: 风险等级
                - ok: 是否成功
                - blocked: 是否被拦截
                - session_id: 会话 ID
                - trace_id: 追踪 ID
                - approval: 审批结果
                - latency_ms: 延迟
        """
        event.setdefault("time", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        self._records.append(event)
        self._append_to_file(event)

    def query(self, session_id: str = None, tool_name: str = None,
              risk_level: str = None, limit: int = 100) -> list[dict]:
        """
        查询审计记录。

        Args:
            session_id: 按会话 ID 过滤
            tool_name: 按工具名过滤
            risk_level: 按风险等级过滤
            limit: 返回最大条数
        """
        results = self._records
        if session_id:
            results = [r for r in results if r.get("session_id") == session_id]
        if tool_name:
            results = [r for r in results if r.get("tool") == tool_name]
        if risk_level:
            results = [r for r in results if r.get("risk") == risk_level]
        return results[-limit:]

    def export(self, format: str = "json") -> str:
        """
        导出审计日志。

        Args:
            format: "json" | "jsonl"
        """
        if format == "jsonl":
            return "\n".join(json.dumps(r, ensure_ascii=False) for r in self._records)
        return json.dumps(self._records, ensure_ascii=False, indent=2)

    def summary(self) -> dict:
        """返回审计统计摘要"""
        total = len(self._records)
        blocked = sum(1 for r in self._records if r.get("blocked"))
        failed = sum(1 for r in self._records if r.get("ok") is False and not r.get("blocked"))
        by_tool: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        for r in self._records:
            by_tool[r.get("tool", "unknown")] = by_tool.get(r.get("tool", "unknown"), 0) + 1
            by_risk[r.get("risk", "unknown")] = by_risk.get(r.get("risk", "unknown"), 0) + 1

        return {
            "total_records": total,
            "blocked": blocked,
            "failed": failed,
            "by_tool": by_tool,
            "by_risk": by_risk,
        }

    def _append_to_file(self, event: dict) -> None:
        """追加写入文件"""
        if not self.persist_path:
            return
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persist_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("[AuditLog] Write failed: %s", e)

    def _load(self) -> None:
        """从文件加载"""
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._records.append(json.loads(line))
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def __len__(self) -> int:
        return len(self._records)
