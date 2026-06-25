#!/usr/bin/env python3
# scripts/scaffold.py

"""
Domain Scaffolding — 一键生成新业务域的模块 Schema 和配置。

参考 langgraph-agent-starter 的 scripts/new_domain.py：
- 生成 config/schemas/<domain>_input.json
- 生成 config/schemas/<domain>_output.json
- 生成测试骨架

用法:
    python scripts/scaffold.py --domain ecommerce --modules auth,product,cart
    python scripts/scaffold.py --domain fintech --modules payment,risk,compliance
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ─── Schema 模板 ──────────────────────────────────────────────

INPUT_SCHEMA_TEMPLATE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "{domain}ModuleInput",
    "description": "{domain} 模块专家 Agent 的输入 Schema",
    "type": "object",
    "required": ["requirement", "constraints", "dependencies"],
    "properties": {
        "requirement": {
            "type": "string",
            "description": "该模块的需求描述",
        },
        "constraints": {
            "type": "array",
            "items": {"type": "string"},
            "description": "技术约束列表",
        },
        "dependencies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "依赖的外部模块列表",
        },
        "dependency_interfaces": {
            "type": "object",
            "description": "依赖模块的接口定义（不含实现）",
            "additionalProperties": {"type": "object"},
        },
        "tech_stack": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "framework": {"type": "string"},
                "database": {"type": "string"},
            },
        },
    },
}

OUTPUT_SCHEMA_TEMPLATE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "{domain}ModuleOutput",
    "description": "{domain} 模块专家 Agent 的输出 Schema",
    "type": "object",
    "required": ["module_spec", "confidence", "reasoning"],
    "properties": {
        "module_spec": {
            "type": "object",
            "required": ["components", "interfaces", "acceptance_criteria"],
            "properties": {
                "components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type", "description"],
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"enum": ["service", "model", "route", "util", "middleware"]},
                            "description": {"type": "string"},
                        },
                    },
                },
                "interfaces": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "method", "path"],
                        "properties": {
                            "name": {"type": "string"},
                            "method": {"type": "string"},
                            "path": {"type": "string"},
                        },
                    },
                },
                "acceptance_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string"},
    },
}


def _format_template(template: dict, domain: str) -> dict:
    """格式化模板中的 {domain} 占位符"""
    s = json.dumps(template, ensure_ascii=False)
    s = s.replace("{domain}", domain)
    return json.loads(s)


def scaffold_domain(domain: str, modules: list[str], output_dir: str) -> list[str]:
    """
    生成业务域的 Schema 文件。

    Args:
        domain: 业务域名 (如 "ecommerce")
        modules: 模块列表 (如 ["auth", "product"])
        output_dir: 输出目录

    Returns:
        创建的文件路径列表
    """
    schemas_dir = Path(output_dir) / "config" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    for module in modules:
        # Input schema
        input_schema = _format_template(INPUT_SCHEMA_TEMPLATE, module)
        input_path = schemas_dir / f"{module}_input.json"
        input_path.write_text(json.dumps(input_schema, ensure_ascii=False, indent=2), encoding="utf-8")
        created_files.append(str(input_path))

        # Output schema
        output_schema = _format_template(OUTPUT_SCHEMA_TEMPLATE, module)
        output_path = schemas_dir / f"{module}_output.json"
        output_path.write_text(json.dumps(output_schema, ensure_ascii=False, indent=2), encoding="utf-8")
        created_files.append(str(output_path))

    print(f"Created {len(created_files)} schema files in {schemas_dir}")
    for f in created_files:
        print(f"  {f}")

    return created_files


def main():
    parser = argparse.ArgumentParser(description="Scaffold domain module schemas")
    parser.add_argument("--domain", required=True, help="Domain name (e.g., ecommerce)")
    parser.add_argument("--modules", required=True, help="Comma-separated module names")
    parser.add_argument("--output", default=".", help="Output directory (default: current)")

    args = parser.parse_args()
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    if not modules:
        print("Error: No modules specified")
        sys.exit(1)

    print(f"\nScaffolding domain '{args.domain}' with {len(modules)} modules: {modules}\n")
    scaffold_domain(args.domain, modules, args.output)


if __name__ == "__main__":
    main()
