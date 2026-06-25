# tools/observability/__init__.py

"""
Observability — 全链路追踪 + 指标统计。

参考 customer-service-agent 的 Tracer：
- 每次请求一条 trace，每个关键动作一个 span（支持嵌套）
- span 的 attributes 记录决策依据
- 支持 render_tree() 可视化决策链

用法:
    from tools.observability import Tracer

    tracer = Tracer("pipeline_run")
    with tracer.span("compile", modules=7):
        with tracer.span("expert_analysis", agent="auth"):
            ...
        with tracer.span("code_gen", module="auth"):
            ...
    print(tracer.render_tree())
"""

from tools.observability.tracer import Tracer
from tools.observability.metrics import PipelineMetrics

__all__ = ["Tracer", "PipelineMetrics"]
