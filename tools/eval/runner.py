# tools/eval/runner.py

"""
Eval Runner — 运行所有测试用例并生成报告。

用法:
    from tools.eval import EvalRunner, EVAL_CASES

    runner = EvalRunner()
    report = runner.run_all()
    print(report.render_table())
"""

from __future__ import annotations

import ast
import logging
import random
from typing import Callable, Optional

from tools.eval.cases import EVAL_CASES
from tools.eval.assertions import ASSERTION_FUNCTIONS, BehavioralCheckResult
from tools.eval.report import EvalReport

logger = logging.getLogger(__name__)


class EvalRunner:
    """
    评估运行器。

    运行所有 EVAL_CASES，收集结果，生成 EvalReport。
    """

    def __init__(self, run_pipeline_fn: Callable = None, verbose: bool = True):
        """
        Args:
            run_pipeline_fn: 运行流水线的函数，接收 input 字符串，返回 result 字典。
                             为 None 时使用 mock 结果（用于测试）。
            verbose: 是否打印进度
        """
        self.run_pipeline_fn = run_pipeline_fn
        self.verbose = verbose

    def run_case(self, case: dict) -> dict:
        """运行单个测试用例"""
        case_id = case["id"]
        user_input = case["input"]

        if self.verbose:
            print(f"  Running: {case_id}...", end=" ")

        try:
            if self.run_pipeline_fn:
                result = self.run_pipeline_fn(user_input)
            else:
                result = self._mock_result(case)

            # 执行所有检查
            checks = []
            for check_name in case.get("checks", []):
                check_fn = ASSERTION_FUNCTIONS.get(check_name)
                if check_fn:
                    check_result = check_fn(result, case)
                    checks.append({
                        "name": check_name,
                        "passed": check_result.passed,
                        "detail": check_result.detail,
                    })

            passed = all(c["passed"] for c in checks)
            if self.verbose:
                print("PASS" if passed else "FAIL")

            return {
                "id": case_id,
                "input": user_input[:80],
                "passed": passed,
                "checks": checks,
                "result_summary": result.get("summary", ""),
            }

        except Exception as e:
            if self.verbose:
                print(f"ERROR: {e}")
            return {
                "id": case_id,
                "input": user_input[:80],
                "passed": False,
                "checks": [{"name": "error", "passed": False, "detail": str(e)}],
                "result_summary": "",
            }

    def run_all(self, cases: list = None, verbose: bool = None) -> EvalReport:
        """
        运行所有测试用例并生成报告。

        Args:
            cases: 自定义用例列表（默认使用 EVAL_CASES）
            verbose: 是否打印进度
        """
        if cases is None:
            cases = EVAL_CASES
        if verbose is not None:
            self.verbose = verbose

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"  Running {len(cases)} eval cases...")
            print(f"{'='*60}")

        results = []
        for case in cases:
            result = self.run_case(case)
            results.append(result)

        return EvalReport.from_results(results)

    def _mock_result(self, case: dict) -> dict:
        """
        生成 Mock 结果（用于测试框架本身）。

        根据 case 的 checks 生成合理的 mock 数据。
        """
        result = {
            "generated_modules": [],
            "code_artifact": {},
            "blocked": False,
            "pii_found": [],
            "steps": 0,
            "iterations": 0,
            "max_steps": 10,
            "max_iterations": 3,
            "summary": "mock result",
        }

        # 根据 case 填充 mock 数据
        if "expected_modules" in case:
            result["generated_modules"] = case["expected_modules"]
            result["code_artifact"] = {
                mod: f"# Module: {mod}\nclass {mod.title()}Service:\n    '''{mod} service'''\n    pass\n"
                for mod in case["expected_modules"]
            }

        if case.get("expected_blocked"):
            result["blocked"] = True

        if "expected_pii_found" in case:
            result["pii_found"] = case["expected_pii_found"]

        result["steps"] = random.randint(3, 8)
        result["iterations"] = random.randint(1, 3)

        return result
