# server/routes/workflow.py

"""
工作流 API 路由。

端点:
    GET    /workflows                  — 工作流列表
    POST   /workflows                  — 创建工作流
    GET    /workflows/{id}             — 获取工作流详情
    DELETE /workflows/{id}             — 删除工作流
    POST   /workflows/{id}/run         — 异步执行
    GET    /workflows/runs/{run_id}     — 执行结果
    GET    /workflows/{id}/runs        — 执行历史
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflow"])


class CreateWorkflowRequest(BaseModel):
    id: Optional[str] = None
    name: str
    nodes: list = []
    edges: list = []
    metadata: Optional[dict] = {}


def get_workflow_engine(request):
    return request.app.state.workflow_engine


@router.get("")
async def list_workflows(request):
    """列出所有工作流"""
    engine = get_workflow_engine(request)
    return {"workflows": engine.list_workflows()}


@router.post("")
async def create_workflow(req: CreateWorkflowRequest, request):
    """创建工作流"""
    engine = get_workflow_engine(request)
    definition = req.dict()
    if not definition.get("id"):
        import uuid
        definition["id"] = str(uuid.uuid4())

    try:
        workflow = engine.load_workflow(definition)
        return {"id": workflow.id, "name": workflow.name, "node_count": len(workflow.nodes)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, request):
    """获取工作流详情"""
    engine = get_workflow_engine(request)
    wf = engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return {
        "id": wf.id,
        "name": wf.name,
        "nodes": [{"id": n.id, "type": n.type.value, "name": n.name, "inputs": n.inputs} for n in wf.nodes.values()],
        "edges": [{"from": src, "to": dst} for src, dsts in wf.edges.items() for dst in dsts],
    }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, request):
    """删除工作流"""
    engine = get_workflow_engine(request)
    if workflow_id in engine._workflows:
        del engine._workflows[workflow_id]
        return {"deleted": True}
    raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, request, input_data: dict = None):
    """异步执行工作流"""
    engine = get_workflow_engine(request)
    input_data = input_data or {}
    context = {
        "llm_provider": getattr(request.app.state, "llm_provider", None),
        "rag_engine": getattr(request.app.state, "rag_engine", None),
        "tool_registry": getattr(request.app.state, "tool_registry", None),
    }
    try:
        run_id = await engine.execute_async(workflow_id, input_data, context)
        return {"run_id": run_id, "workflow_id": workflow_id, "status": "running"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_run_result(run_id: str, request):
    """获取执行结果"""
    engine = get_workflow_engine(request)
    result = engine.get_run_result(run_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return {
        "run_id": run_id,
        "workflow_id": result.workflow_id,
        "status": result.status,
        "execution_time_ms": result.execution_time_ms,
        "outputs": result.outputs,
        "logs": [{"node_id": l.node_id, "status": l.status, "duration_ms": l.duration_ms} for l in result.logs],
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }


@router.get("/{workflow_id}/runs")
async def list_runs(workflow_id: str, request):
    """列出工作流的执行历史"""
    engine = get_workflow_engine(request)
    runs = engine.list_runs(workflow_id)
    return {"runs": runs}
