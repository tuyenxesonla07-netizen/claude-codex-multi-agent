# tools/mcp/builtin_tools.py

"""
内置工具定义。

注册项目自带的工具函数到 ToolRegistry。
每个工具遵循 MCP 协议规范。

用法:
    registry = ToolRegistry()
    register_builtin_tools(registry)
"""

import ast
import logging
import math

from tools.mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def register_builtin_tools(registry: ToolRegistry) -> None:
    """注册所有内置工具"""

    # 1. generate_code — 生成 Python 代码
    registry.register_func(
        name="generate_code",
        description="根据规格生成可执行的 Python 代码。输入 spec（模块规格字典），返回代码字符串。",
        input_schema={
            "type": "object",
            "properties": {
                "spec": {
                    "type": "object",
                    "description": "模块规格，包含 components, interfaces, acceptance_criteria 等",
                },
                "module_name": {
                    "type": "string",
                    "description": "模块名称",
                },
            },
            "required": ["spec", "module_name"],
        },
        handler=_tool_generate_code,
    )

    # 2. validate_python — 验证 Python 代码语法
    registry.register_func(
        name="validate_python",
        description="验证 Python 代码的语法正确性。返回是否可解析及错误信息。",
        input_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要验证的 Python 代码",
                },
            },
            "required": ["code"],
        },
        handler=_tool_validate_python,
    )

    # 3. search_knowledge — 知识库检索
    registry.register_func(
        name="search_knowledge",
        description="在知识库中搜索相关信息。返回匹配的文档块列表。",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题",
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量（默认 5）",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        handler=_tool_search_knowledge,
    )

    # 4. compile_pipeline — 编译流水线
    registry.register_func(
        name="compile_pipeline",
        description="编译模块 Schema，返回实现顺序、上下文策略、修复模板和质量门禁。",
        input_schema={
            "type": "object",
            "properties": {
                "module_schemas": {
                    "type": "object",
                    "description": "模块 Schema 字典 {module_name: schema}",
                },
            },
            "required": ["module_schemas"],
        },
        handler=_tool_compile_pipeline,
    )

    # 5. execute_math — 数学计算
    registry.register_func(
        name="execute_math",
        description="执行数学表达式计算。支持基本运算和 math 模块函数。",
        input_schema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2 ** 10', 'math.sqrt(144)'",
                },
            },
            "required": ["expression"],
        },
        handler=_tool_execute_math,
    )

    logger.info("[BuiltinTools] Registered %d tools: %s",
                len(registry.list_tools()), [t.name for t in registry.list_tools()])


# ─── 工具实现 ──────────────────────────────────────────────

def _tool_generate_code(spec: dict, module_name: str, **kwargs) -> str:
    """生成 Python 代码（简化版，实际应调用 ClaudeCodeExecutor）"""
    components = spec.get("components", [])
    interfaces = spec.get("interfaces", [])

    lines = [f'"""Module: {module_name}"""', "from typing import Optional, List", ""]

    for comp in components:
        name = comp.get("name", "Unknown")
        comp_type = comp.get("type", "service")
        desc = comp.get("description", "")
        if comp_type == "service":
            lines.append(f"class {name}:")
            lines.append(f'    """{desc}"""')
            lines.append("    pass")
            lines.append("")

    for iface in interfaces:
        name = iface.get("name", "unknown")
        method = iface.get("method", "GET")
        path = iface.get("path", "/")
        lines.append(f"# Interface: {name} ({method} {path})")

    return "\n".join(lines)


def _tool_validate_python(code: str, **kwargs) -> dict:
    """验证 Python 代码语法"""
    try:
        ast.parse(code)
        return {"valid": True, "errors": []}
    except SyntaxError as e:
        return {"valid": False, "errors": [f"Line {e.lineno}: {e.msg}"]}


def _tool_search_knowledge(query: str, top_k: int = 5, **kwargs) -> list:
    """知识库检索（需要 app 注入 rag_engine）"""
    # 实际实现需要访问 RAG 引擎，这里返回占位
    return [{"content": f"Search results for: {query}", "source": "knowledge_base"}]


def _tool_compile_pipeline(module_schemas: dict, **kwargs) -> dict:
    """编译流水线"""
    try:
        from tools.compiler import PipelineCompiler
        compiler = PipelineCompiler()
        compiled = compiler.compile(module_schemas)
        return {
            "implementation_order": compiled.implementation_order,
            "module_count": len(compiled.module_schemas),
            "quality_gates": len(compiled.quality_gates.gates),
        }
    except Exception as e:
        return {"error": str(e)}


def _tool_execute_math(expression: str, **kwargs) -> dict:
    """安全数学计算"""
    try:
        # 安全评估：只允许数学运算
        allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e), "expression": expression}
