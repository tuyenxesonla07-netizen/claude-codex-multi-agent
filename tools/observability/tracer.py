# tools/observability/tracer.py

"""
全链路追踪器。

参考 customer-service-agent 的 Tracer：
- trace_id: 请求唯一标识
- span: 每个关键动作（支持嵌套）
- attributes: 记录决策依据
- render_tree(): 按父子关系渲染 span 树

用于排查：是检索没召回？工具被拦截？还是模型选错了工具？
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from datetime import datetime


class Tracer:
    """
    请求级追踪器。

    每次请求创建一条 trace，每个关键操作创建一个 span。
    span 支持嵌套（通过 _stack 维护父链）。

    用法:
        tracer = Tracer()
        with tracer.span("step1"):
            tracer.event("tool_called", tool="generate_code")
            with tracer.span("sub_step"):
                ...
        print(tracer.render_tree())
    """

    def __init__(self, name: str = "request"):
        self.trace_id = uuid.uuid4().hex[:8]
        self.name = name
        self.spans: list[dict] = []
        self._started = time.time()
        self._stack: list[str] = []

    @contextmanager
    def span(self, name: str, **attributes):
        """
        创建嵌套 span 的上下文管理器。

        Args:
            name: span 名称
            **attributes: 自定义属性
        """
        span = {
            "trace_id": self.trace_id,
            "span_id": uuid.uuid4().hex[:6],
            "parent_id": self._stack[-1] if self._stack else None,
            "name": name,
            "start_ms": round((time.time() - self._started) * 1000, 1),
            "attributes": dict(attributes),
            "status": "ok",
        }
        self.spans.append(span)
        self._stack.append(span["span_id"])
        try:
            yield span
        except Exception as e:
            span["status"] = "error"
            span["attributes"]["error"] = f"{type(e).__name__}: {e}"
            raise
        finally:
            span["duration_ms"] = round((time.time() - self._started) * 1000 - span["start_ms"], 1)
            self._stack.pop()

    def event(self, name: str, **attributes) -> None:
        """记录零时长事件"""
        with self.span(name, **attributes):
            pass

    def summary(self) -> dict:
        """返回 trace 摘要"""
        return {
            "trace_id": self.trace_id,
            "total_spans": len(self.spans),
            "total_ms": round((time.time() - self._started) * 1000, 1),
            "errors": sum(1 for s in self.spans if s["status"] == "error"),
        }

    def render_tree(self) -> str:
        """渲染 span 树（终端/日志可视化）"""
        children: dict[str | None, list[dict]] = {}
        for span in self.spans:
            children.setdefault(span["parent_id"], []).append(span)

        lines = [f"trace {self.trace_id} ({datetime.now().strftime('%H:%M:%S')})"]

        def walk(parent_id: str | None, depth: int) -> None:
            for span in children.get(parent_id, []):
                mark = "x" if span["status"] == "error" else "*"
                attrs = ", ".join(f"{k}={v}" for k, v in span["attributes"].items())
                if len(attrs) > 80:
                    attrs = attrs[:77] + "..."
                prefix = "  " * (depth + 1)
                duration = span.get("duration_ms", 0)
                lines.append(f"{prefix}{mark} {span['name']} [{duration}ms]{' ' + attrs if attrs else ''}")
                walk(span["span_id"], depth + 1)

        walk(None, 0)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {"summary": self.summary(), "spans": self.spans}
