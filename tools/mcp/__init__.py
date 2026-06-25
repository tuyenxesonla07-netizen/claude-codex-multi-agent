# tools/mcp/__init__.py

"""
MCP (Model Context Protocol) 工具调用模块。

tools/mcp/
├── tool_registry.py   — 工具注册与发现
├── mcp_server.py      — MCP 服务端（JSON-RPC over SSE）
└── builtin_tools.py   — 内置工具定义
"""

from tools.mcp.tool_registry import ToolRegistry, ToolDefinition
from tools.mcp.mcp_server import MCPServer

__all__ = ["ToolRegistry", "ToolDefinition", "MCPServer"]
