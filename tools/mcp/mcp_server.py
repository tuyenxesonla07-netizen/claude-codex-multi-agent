# tools/mcp/mcp_server.py

"""
MCP 服务端实现。

支持两种传输方式：
1. SSE (Server-Sent Events) — 用于 Web 客户端
2. stdio — 用于本地 CLI 客户端

协议：JSON-RPC 2.0
工具发现：tools/list
工具调用：tools/call

用法:
    server = MCPServer(registry, host="localhost", port=9000)
    await server.start_sse()  # 启动 SSE 服务
"""

import json
import logging
import asyncio
from typing import Any, Dict, Optional

from tools.mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP 协议服务端"""

    def __init__(self, registry: ToolRegistry, host: str = "localhost",
                 port: int = 9000):
        self.registry = registry
        self.host = host
        self.port = port
        self._server = None

    async def start_sse(self) -> None:
        """启动 SSE 模式的服务（供 Web 客户端连接）"""
        try:
            from fastapi import FastAPI
            from sse_starlette.sse import EventSourceResponse
        except ImportError:
            logger.warning("pip install sse-starlette for MCP SSE support")
            return

        app = FastAPI()

        @app.get("/sse")
        async def sse_endpoint():
            async def event_generator():
                # 发送初始 tools/list
                tools = self.registry.to_mcp_format()
                yield {
                    "event": "tools",
                    "data": json.dumps({"tools": tools}),
                }
            return EventSourceResponse(event_generator())

        @app.post("/mcp")
        async def mcp_endpoint(request: Dict):
            return await self._handle_request(request)

        import uvicorn
        config = uvicorn.Config(app, host=self.host, port=self.port)
        self._server = uvicorn.Server(config)
        logger.info("[MCPServer] Starting SSE server at %s:%s", self.host, self.port)
        await self._server.serve()

    async def handle_message(self, message: Dict) -> Dict:
        """处理单条 JSON-RPC 消息"""
        msg_id = message.get("id", "unknown")
        method = message.get("method", "")
        params = message.get("params", {})

        try:
            if method == "tools/list":
                tools = self.registry.to_mcp_format()
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}

            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = await self.registry.call(name, arguments)
                return {
                    "jsonrpc": "2.0", "id": msg_id,
                    "result": {"content": str(result), "isError": False},
                }

            elif method == "initialize":
                return {
                    "jsonrpc": "2.0", "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "claude-codex-multi-agent", "version": "2.0.0"},
                    },
                }

            else:
                return {
                    "jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

        except Exception as e:
            logger.error("[MCPServer] Error handling %s: %s", method, e)
            return {
                "jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32603, "message": str(e)},
            }

    async def _handle_request(self, request: Dict) -> Dict:
        """处理 HTTP POST 请求（FastAPI 路由用）"""
        return await self.handle_message(request)

    async def stop(self) -> None:
        """停止服务"""
        if self._server:
            self._server.should_exit = True
