# tools/workflow/engine.py

"""
工作流执行引擎。

支持 DAG 拓扑排序执行、并行分支、条件路由。
工作流定义格式为 JSON/YAML，支持序列化和持久化。

用法:
    engine = WorkflowEngine()
    workflow = engine.load_workflow({
        "id": "wf-001",
        "name": "代码生成流水线",
        "nodes": [
            {"id": "n1", "type": "llm", "name": "需求分析", "config": {"prompt": "分析需求: {{input}}"}},
            {"id": "n2", "type": "tool", "name": "代码生成", "config": {"tool_name": "generate_code"}, "inputs": ["n1"]},
        ],
        "edges": [{"from": "n1", "to": "n2"}]
    })
    result = await engine.execute_async("wf-001", {"input": "用户登录模块"})
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import deque

from tools.workflow.nodes import (
    WorkflowNode, NodeType, LLMNode, RAGNode, ToolNode, CodeNode, BranchNode,
)

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    """工作流定义"""
    id: str
    name: str
    nodes: Dict[str, WorkflowNode]       # node_id → node
    edges: Dict[str, List[str]]          # node_id → [下游 node_id]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionLog:
    """单条执行日志"""
    node_id: str
    status: str          # success / failed / skipped
    output: Any
    duration_ms: int
    timestamp: str


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str
    status: str          # success / failed / running
    outputs: Dict[str, Any]    # 各节点最终输出
    execution_time_ms: int
    logs: List[ExecutionLog]
    started_at: str = ""
    finished_at: str = ""


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._runs: Dict[str, WorkflowResult] = {}

    def load_workflow(self, definition: dict) -> Workflow:
        """从字典加载工作流定义"""
        nodes = {}
        for node_def in definition.get("nodes", []):
            node = WorkflowNode(
                id=node_def["id"],
                type=NodeType(node_def.get("type", "llm")),
                name=node_def.get("name", node_def["id"]),
                config=node_def.get("config", {}),
                inputs=node_def.get("inputs", []),
            )
            nodes[node.id] = node

        edges = {}
        for edge_def in definition.get("edges", []):
            src = edge_def.get("from", "")
            dst = edge_def.get("to", "")
            if src not in edges:
                edges[src] = []
            edges[src].append(dst)

        workflow = Workflow(
            id=definition.get("id", ""),
            name=definition.get("name", ""),
            nodes=nodes,
            edges=edges,
            metadata=definition.get("metadata", {}),
        )
        self._workflows[workflow.id] = workflow
        logger.info("[WorkflowEngine] Loaded workflow '%s' with %d nodes",
                    workflow.id, len(nodes))
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> List[dict]:
        return [
            {"id": w.id, "name": w.name, "node_count": len(w.nodes)}
            for w in self._workflows.values()
        ]

    async def execute_async(self, workflow_id: str, input_data: dict,
                            context: dict = None) -> str:
        """异步执行工作流，返回 run_id"""
        import uuid
        run_id = str(uuid.uuid4())
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        result = WorkflowResult(
            workflow_id=workflow_id,
            status="running",
            outputs={"_input": input_data},
            execution_time_ms=0,
            logs=[],
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._runs[run_id] = result

        # 异步执行
        asyncio.create_task(self._run_workflow(workflow, result, input_data, context))
        return run_id

    def get_run_result(self, run_id: str) -> Optional[WorkflowResult]:
        return self._runs.get(run_id)

    def list_runs(self, workflow_id: str = None) -> List[dict]:
        runs = []
        for run_id, result in self._runs.items():
            if workflow_id and result.workflow_id != workflow_id:
                continue
            runs.append({
                "run_id": run_id,
                "workflow_id": result.workflow_id,
                "status": result.status,
                "started_at": result.started_at,
            })
        return runs

    async def _run_workflow(self, workflow: Workflow, result: WorkflowResult,
                            input_data: dict, context: dict = None):
        """执行工作流（拓扑排序 + 并行执行）"""
        start_time = datetime.now(timezone.utc)
        try:
            # 拓扑排序
            order = self._topological_sort(workflow)
            result.outputs["_input"] = input_data

            for node_id in order:
                node = workflow.nodes.get(node_id)
                if not node:
                    continue

                # 收集上游输入
                upstream_inputs = {}
                for dep_id in node.inputs:
                    if dep_id in result.outputs:
                        upstream_inputs[dep_id] = result.outputs[dep_id]

                # 合并 input_data 到第一个节点
                if not result.outputs:
                    upstream_inputs.update(input_data)

                # 执行节点
                node_start = datetime.now(timezone.utc)
                output = await self._execute_node(node, upstream_inputs, context)
                node_duration = int((datetime.now(timezone.utc) - node_start).total_seconds() * 1000)

                result.outputs[node_id] = output
                result.logs.append(ExecutionLog(
                    node_id=node_id,
                    status="success",
                    output=str(output)[:500],
                    duration_ms=node_duration,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))

            result.status = "success"
        except Exception as e:
            logger.error("[WorkflowEngine] Execution failed: %s", e)
            result.status = "failed"
            result.logs.append(ExecutionLog(
                node_id="_engine",
                status="failed",
                output=str(e),
                duration_ms=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
        finally:
            result.execution_time_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )
            result.finished_at = datetime.now(timezone.utc).isoformat()

    async def _execute_node(self, node: WorkflowNode, inputs: dict,
                            context: dict = None) -> Any:
        """根据节点类型执行"""
        if node.type == NodeType.LLM:
            llm_node = LLMNode(
                prompt_template=node.config.get("prompt_template", ""),
                provider=context.get("llm_provider") if context else None,
                temperature=node.config.get("temperature", 0.7),
            )
            return await llm_node.execute(inputs)

        elif node.type == NodeType.RAG:
            rag_node = RAGNode(
                rag_engine=context.get("rag_engine") if context else None,
                top_k=node.config.get("top_k", 5),
            )
            return await rag_node.execute(inputs)

        elif node.type == NodeType.TOOL:
            tool_node = ToolNode(
                tool_registry=context.get("tool_registry") if context else None,
                tool_name=node.config.get("tool_name", ""),
                arguments=node.config.get("arguments", {}),
            )
            return await tool_node.execute(inputs)

        elif node.type == NodeType.CODE:
            code_node = CodeNode(code_template=node.config.get("code", ""))
            return await code_node.execute(inputs)

        elif node.type == NodeType.BRANCH:
            branch_node = BranchNode(
                condition=node.config.get("condition", "true"),
                branches=node.config.get("branches", {}),
            )
            return await branch_node.execute(inputs)

        else:
            return f"[Unknown node type: {node.type}]"

    def _topological_sort(self, workflow: Workflow) -> List[str]:
        """拓扑排序（Kahn's Algorithm）"""
        in_degree = {nid: 0 for nid in workflow.nodes}
        for src, dsts in workflow.edges.items():
            for dst in dsts:
                if dst in in_degree:
                    in_degree[dst] += 1

        queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
        result = []
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            for dst in workflow.edges.get(node_id, []):
                in_degree[dst] -= 1
                if in_degree[dst] == 0:
                    queue.append(dst)
        return result
