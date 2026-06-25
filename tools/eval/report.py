# tools/eval/report.py

"""
Eval Report — 评估报告生成和渲染。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalReport:
    """评估报告"""
    cases_total: int = 0
    cases_passed: int = 0
    per_case_results: list = field(default_factory=list)

    @classmethod
    def from_results(cls, results: list[dict]) -> EvalReport:
        """从用例结果创建报告"""
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        return cls(
            cases_total=total,
            cases_passed=passed,
            per_case_results=results,
        )

    @property
    def pass_rate(self) -> str:
        """通过率"""
        if self.cases_total == 0:
            return "0/0"
        return f"{self.cases_passed}/{self.cases_total}"

    @property
    def pass_percentage(self) -> float:
        """通过百分比"""
        if self.cases_total == 0:
            return 0.0
        return round(self.cases_passed / self.cases_total * 100, 1)

    def render_table(self) -> str:
        """渲染文本表格"""
        lines = [
            "",
            "=" * 70,
            "  EVALUATION REPORT",
            "=" * 70,
            f"  Total: {self.cases_total} | Passed: {self.cases_passed} | "
            f"Rate: {self.pass_rate} ({self.pass_percentage}%)",
            "-" * 70,
        ]

        # 按类别分组
        categories = {
            "module_gen": "Module Generation",
            "code": "Code Quality",
            "security": "Security",
            "budget": "Budget Protection",
            "convergence": "Convergence",
        }

        current_cat = None
        for result in self.per_case_results:
            case_id = result["id"]
            # 推断类别
            cat = case_id.split("_")[0] if "_" in case_id else "other"
            if cat in categories and cat != current_cat:
                current_cat = cat
                lines.append(f"\n  [{categories[cat]}]")

            status = "PASS" if result["passed"] else "FAIL"
            lines.append(f"    {status}  {case_id:<35} {result['input'][:30]}")

            # 显示失败的检查
            if not result["passed"]:
                for check in result.get("checks", []):
                    if not check["passed"]:
                        lines.append(f"           ^ {check['name']}: {check['detail'][:60]}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    def to_json(self) -> str:
        """导出 JSON"""
        return json.dumps({
            "summary": {
                "total": self.cases_total,
                "passed": self.cases_passed,
                "pass_rate": self.pass_rate,
                "pass_percentage": self.pass_percentage,
            },
            "cases": self.per_case_results,
        }, ensure_ascii=False, indent=2)
