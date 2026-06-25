# tools/workflow/__init__.py

"""
可视化工作流引擎。

支持 DAG 执行、并行分支、条件路由、人工审批节点。

tools/workflow/
├── engine.py    — 工作流执行引擎
└── nodes.py     — 节点类型定义
"""

from tools.workflow.engine import WorkflowEngine, Workflow, WorkflowNode, WorkflowResult
from tools.workflow.nodes import LLMNode, RAGNode, ToolNode, CodeNode, BranchNode

__all__ = [
    "WorkflowEngine", "Workflow", "WorkflowNode", "WorkflowResult",
    "LLMNode", "RAGNode", "ToolNode", "CodeNode", "BranchNode",
]
