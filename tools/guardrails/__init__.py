# tools/guardrails/__init__.py

"""
Security Layer — 输入护栏 + 输出护栏。

参考 customer-service-agent 的 Guardrails 设计：
- InputGuard: 注入检测 + PII 脱敏 + 长度限制
- OutputGuard: 泄漏防护 + 代码安全检查 + PII 回流清理

用法:
    from tools.guardrails import InputGuard, OutputGuard

    ig = InputGuard()
    result = ig.check("My phone is 13812345678")
    # result.passed, result.text (脱敏后), result.pii_found

    og = OutputGuard()
    result = og.check("sk-abc123...")
    # result.passed, result.text (清理后), result.issues
"""

from tools.guardrails.input_guard import InputGuard, InputCheckResult
from tools.guardrails.output_guard import OutputGuard, OutputCheckResult

__all__ = ["InputGuard", "InputCheckResult", "OutputGuard", "OutputCheckResult"]
