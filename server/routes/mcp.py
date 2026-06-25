# server/routes/mcp.py

"""
MCP (Model Context Protocol) API 路由。

端点:
    GET  /mcp/tools              — 列出所有可用工具
    POST /mcp/tools/{name}/call   — 调用指定工具
    GET  /mcp/health            — MCP 服务健康检查
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict = {}


def get_tool_registry(request):
    """从 app state 获取工具注册中心"""
    return request.app.state.tool_registry


@router.get("/tools")
async def list_tools(request):
    """列出所有可用工具（MCP 协议格式）"""
    registry = get_tool_registry(request)
    return {"tools": registry.to_mcp_format()}


@router.post("/tools/{name}/call")
async def call_tool(name: str, req: ToolCallRequest, request):
    """调用指定工具"""
    registry = get_tool_registry(request)
    try:
        result = await registry.call(name, req.arguments)
        return {"content": str(result), "isError": False}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Tool not found: {name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def mcp_health(request):
    """MCP 服务健康检查"""
    registry = get_tool_registry(request)
    tools = registry.list_tools()
    return {"status": "ok", "tools_count": len(tools)}
