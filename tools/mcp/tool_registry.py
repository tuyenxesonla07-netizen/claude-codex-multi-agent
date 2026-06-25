# tools/mcp/tool_registry.py

"""
工具注册中心。

管理所有可用工具的注册、发现和调用。
工具定义遵循 MCP 协议规范（name, description, inputSchema）。

用法:
    registry = ToolRegistry()
    registry.register(ToolDefinition(name="echo", description="回显输入", input_schema={...}, handler=my_func))
    tools = registry.list_tools()
    result = await registry.call("echo", {"text": "hello"})
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """工具定义（MCP 协议格式）"""
    name: str                       # 工具名称
    description: str                # 工具描述（供 LLM 理解）
    input_schema: dict              # JSON Schema 格式的输入参数定义
    handler: Callable               # 实际执行函数（sync 或 async）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


class ToolRegistry:
    """工具注册与发现"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """注册工具"""
        if tool.name in self._tools:
            logger.warning("[ToolRegistry] Overwriting tool: %s", tool.name)
        self._tools[tool.name] = tool
        logger.info("[ToolRegistry] Registered tool: %s", tool.name)

    def register_func(self, name: str, description: str,
                      input_schema: dict, handler: Callable) -> None:
        """便捷注册：直接传入参数创建 ToolDefinition 并注册"""
        self.register(ToolDefinition(
            name=name, description=description,
            input_schema=input_schema, handler=handler,
        ))

    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def list_tools(self) -> List[ToolDefinition]:
        """列出所有已注册工具"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取指定工具"""
        return self._tools.get(name)

    async def call(self, name: str, arguments: dict) -> Any:
        """
        调用工具。

        Args:
            name: 工具名称
            arguments: 参数字典

        Returns:
            工具执行结果

        Raises:
            KeyError: 工具不存在
            RuntimeError: 执行失败
        """
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")

        try:
            handler = tool.handler
            # 支持 async handler
            if hasattr(handler, "__call__"):
                import asyncio
                if asyncio.iscoroutinefunction(handler):
                    return await handler(**arguments)
                return handler(**arguments)
        except Exception as e:
            logger.error("[ToolRegistry] Tool '%s' execution failed: %s", name, e)
            raise RuntimeError(f"Tool execution failed: {e}") from e

    def to_mcp_format(self) -> List[Dict]:
        """转换为 MCP 协议格式（用于 /mcp/tools 端点）"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
            }
            for t in self._tools.values()
        ]
