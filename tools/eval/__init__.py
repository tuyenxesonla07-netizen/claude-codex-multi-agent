# tools/eval/__init__.py

"""
Eval — 自动化评估系统。

参考 wsk-agent 的课程评估设计：
- Eval Cases: 25 个测试用例（模块生成、安全、预算、收敛）
- Behavioral Assertions: 行为检查函数
- Eval Runner: 运行所有用例，收集结果
- Eval Report: 生成评估报告

用法:
    from tools.eval import EvalRunner, EVAL_CASES

    runner = EvalRunner()
    report = runner.run_all()
    print(report.render_table())
"""

from tools.eval.cases import EVAL_CASES
from tools.eval.assertions import BehavioralCheckResult
from tools.eval.runner import EvalRunner
from tools.eval.report import EvalReport

__all__ = ["EVAL_CASES", "BehavioralCheckResult", "EvalRunner", "EvalReport"]
