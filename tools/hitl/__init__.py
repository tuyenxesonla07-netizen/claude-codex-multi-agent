# tools/hitl/__init__.py

"""
HITL (Human-in-the-Loop) — 高风险操作的人工审批机制。

参考 customer-service-agent 的 ToolRuntime 审批流程：
- 低风险工具（查询、读取）自动放行
- 中风险工具（代码生成）可配置自动/手动
- 高风险工具（执行代码、文件写入）必须人工审批

用法:
    from tools.hitl import AutoApprovalHandler, ManualApprovalHandler, AuditLog

    approval = AutoApprovalHandler(auto_under_risk="medium")
    result = approval.request_approval("write_file", {"path": "/etc/config"}, "high")
    # result = {"approved": False, "approver": None, "requires_human": True}
"""

from tools.hitl.approval import ApprovalHandler, AutoApprovalHandler, ManualApprovalHandler
from tools.hitl.audit import AuditLog

__all__ = [
    "ApprovalHandler",
    "AutoApprovalHandler",
    "ManualApprovalHandler",
    "AuditLog",
]
