# Claude-Codex Multi-Agent 项目落地教程

> **版本**: v1.0 | **日期**: 2026-06-24  
> **适用场景**: 中大型 Python 项目的 AI 辅助开发、自动化代码生成与审查

---

## 目录

1. [项目概览](#1-项目概览)
2. [环境准备](#2-环境准备)
3. [快速开始（5 分钟跑通）](#3-快速开始5-分钟跑通)
4. [核心架构理解](#4-核心架构理解)
5. [完整使用指南](#5-完整使用指南)
6. [Schema 编写规范](#6-schema-编写规范)
7. [接入真实 LLM](#7-接入真实-llm)
8. [部署上线](#8-部署上线)
9. [最佳实践](#9-最佳实践)
10. [常见问题](#10-常见问题)

---

## 1. 项目概览

### 1.1 这是什么？

Claude-Codex Multi-Agent 是一个 **Schema-First 的多 Agent 协作开发流水线**，能够：

| 能力 | 说明 |
|------|------|
| 需求自动拆分 | 将自然语言需求解析为功能模块 |
| 并行专家分析 | 7 个专家 Agent 并行处理各模块 |
| Schema 驱动编译 | 从 JSON Schema 自动推导编排逻辑 |
| 质量审查 + 收敛 | 自动检测修复循环，保证交付质量 |
| Prompt 自动生成 | 根据模块规格整合生成完整 Prompt |

### 1.2 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| 框架 | FastAPI（生成目标） |
| 数据格式 | JSON Schema (Draft-07) |
| 配置 | YAML |
| 测试 | pytest |
| 部署 | Docker + CI/CD |

### 1.3 项目结构

```
项目/
├── __init__.py              # 主入口: ClaudeCodexMultiAgent
├── config/
│   ├── agents.yaml           # Agent 注册（7 专家 + 主管）
│   ├── pipeline.yaml         # 流水线配置（双阶段 + 质量门禁）
│   └── schemas/              # 每个模块的 input/output Schema
│       ├── auth_input.json
│       ├── auth_output.json
│       └── ...
├── tools/
│   ├── compiler/             # 核心编译引擎（5 个子推导器）
│   ├── stores/               # 运行时数据存储
│   ├── messaging/            # 消息总线
│   └── quality/              # 质量评估 + 收敛检测
├── agents/
│   ├── supervisor/           # Codex 主管 Agent
│   └── experts/              # 专家 Agent（按模块）
├── examples/
│   └── ecommerce_trace.py    # 端到端示例
└── tests/                    # 94+ 测试用例
```

---

## 2. 环境准备

### 2.1 系统要求

- Python 3.12+
- pip / poetry
- 8GB+ RAM（运行 LLM 推理）
- （可选）Docker 20+（部署用）

### 2.2 安装步骤

```bash
# 1. 克隆项目
cd "D:\闲置\Claude+Codex工作流\项目\claude-codex-multi-agent"

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -B -m pytest tests/ -v --tb=short
```

### 2.3 依赖清单

```txt
# requirements.txt
pyyaml>=6.0
jsonschema>=4.17
pytest>=7.4
pytest-cov>=4.1
anthropic>=0.30        # 真实 LLM 调用
fastapi>=0.100         # 生成的代码框架
uvicorn>=0.23          # ASGI 服务器
pydantic>=2.0          # 数据校验
```

---

## 3. 快速开始（5 分钟跑通）

### 3.1 运行端到端 Trace

```bash
cd "D:\闲置\Claude+Codex工作流\项目\claude-codex-multi-agent"

# 运行完整的商城场景示例
python -B -c "import examples.ecommerce_trace; examples.ecommerce_trace.run_trace()"
```

**预期输出：**

```
======================================================================
  Claude-Codex Multi-Agent — 端到端 Trace
  场景: 构建在线商城（7 个功能模块）
======================================================================

[Step 1] Codex 解析需求
--------------------------------------------------
  输入: 构建一个在线商城，支持用户注册登录、商品浏览...
  识别模块: ['authentication', 'product_catalog', ...]

[Step 2] 编译流水线
--------------------------------------------------
  加载 input_schema: 7 个
  加载 output_schema: 7 个
  编译完成:
    - 上下文策略: 7 个
    - 实现顺序: ['authentication', 'product_catalog', ...]
    - 修复模板: 7 个
    - 质量门禁: 5 个

[Step 3] 上下文注入推导
--------------------------------------------------
    authentication: 安全上下文, 全局约束
    product_catalog: 搜索需求, 全局约束
    ...

[Step 4] 专家 Agent 并行分析
--------------------------------------------------
    authentication: 4 组件, 4 接口
    product_catalog: 3 组件, 2 接口
    ...

[Step 5] Prompt 模板生成
--------------------------------------------------
  模板长度: 2847 字符
  包含模块: 7 个

[Step 6] 代码生成 + 审查
--------------------------------------------------
    ✓ authentication: 0 issues
    ✓ product_catalog: 0 issues
    ✗ shopping_cart: 1 issues
    ...

[Step 7] 质量评估
--------------------------------------------------
  质量评分: 0.85
  是否通过: 是
  收敛状态: passed

======================================================================
  Trace 完成
======================================================================
```

### 3.2 运行测试套件

```bash
# 全部测试
python -B -m pytest tests/ -v

# 带覆盖率
python -B -m pytest tests/ --cov=tools --cov=agents -v

# 仅运行编译器测试
python -B -m pytest tests/compiler/ -v
```

**预期结果：** `94+ passed`

### 3.3 编程式调用

```python
from __init__ import ClaudeCodexMultiAgent

# 初始化系统
system = ClaudeCodexMultiAgent(
    config_dir="config",
    llm_backend="mock",       # 开发阶段用 mock，生产用 "anthropic"
    llm_api_key=None
)

# 阶段一：需求拆分 → 模块规格
result = system.run_phase1(
    "构建一个在线商城，支持用户注册登录、商品浏览、购物车、下单、支付"
)

print(f"实现顺序: {result['compiled'].implementation_order}")
print(f"模块数: {len(result['module_specs'])}")
print(f"Prompt 长度: {len(result['prompt'])} 字符")

# 阶段二：代码审查
review = system.run_phase2(
    code_artifact="generated_code",
    compiled_pipeline=result['compiled']
)

print(f"质量评分: {review['quality_score']}")
print(f"审查结果: {'通过' if review['passed'] else '需修复'}")
print(f"迭代次数: {review['iterations']}")
```

---

## 4. 核心架构理解

### 4.1 双阶段流水线

```
┌─────────────────────────────────────────────────────────────┐
│            阶段一：需求拆分 (Requirement Decomposition)       │
│                                                             │
│  用户需求 → Codex 解析 → 识别模块 → 并行分发 → 收集规格      │
│           → Prompt 生成 → 代码生成                           │
├─────────────────────────────────────────────────────────────┤
│            阶段二：代码审查 (Code Review)                     │
│                                                             │
│  完整代码 → 分发审查 → 汇总评估 → 质量门禁 → 通过/修复        │
│                                    ↓                        │
│                              不通过 → 修复循环               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 编译器核心（5 个子推导器）

| 推导器 | 输入 | 输出 | 作用 |
|--------|------|------|------|
| `ContextDeriver` | input_schema | `ContextStrategy` | 推导每个模块需要注入的上下文 |
| `DependencyGraphBuilder` | 所有 schema | `DependencyGraph` | 拓扑排序确定实现顺序 |
| `PromptTemplateGenerator` | 模块规格 | `PromptTemplate` | 生成整合的 Prompt |
| `FixInstructionDeriver` | output_schema | `FixTemplate` | 生成修复指令模板 |
| `QualityGateGenerator` | output_schema | `QualityGateSuite` | 生成质量门禁规则 |

### 4.3 专家 Agent 依赖图

```
                    Codex (主管)
                        │
                  Superpowers
                        │
        ┌───────┬───────┼───────┬───────┐
        │       │       │       │       │
    Auth → Product → Cart → Order → Payment
        │                       │
    Notification              Report
```

- 无依赖模块优先实现（如 `authentication`）
- 有依赖模块按拓扑序串行（如 `order_system` 依赖 `cart`）
- 同层模块可并行处理

---

## 5. 完整使用指南

### 5.1 步骤一：定义模块 Schema

为每个功能模块创建 `config/schemas/<module>_input.json` 和 `<module>_output.json`。

**input Schema 示例：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OrderModuleInput",
  "description": "订单模块的输入 Schema",
  "type": "object",
  "required": ["requirement", "constraints"],
  "properties": {
    "requirement": {
      "type": "string",
      "description": "该模块的需求描述"
    },
    "constraints": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["订单状态机必须完整", "支持并发下单"]
    },
    "security_requirements": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["用户只能操作自己的订单"]
    }
  }
}
```

**output Schema 示例：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OrderModuleOutput",
  "type": "object",
  "required": ["module_spec", "confidence"],
  "properties": {
    "module_spec": {
      "type": "object",
      "required": ["components", "interfaces", "acceptance_criteria"],
      "properties": {
        "components": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
              "name": { "type": "string" },
              "type": { "enum": ["service", "model", "middleware", "route"] },
              "description": { "type": "string" }
            }
          }
        },
        "interfaces": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "method", "path"],
            "properties": {
              "name": { "type": "string" },
              "method": { "type": "string" },
              "path": { "type": "string" }
            }
          }
        },
        "acceptance_criteria": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
  }
}
```

### 5.2 步骤二：配置 Agent 注册

在 `config/agents.yaml` 中注册新模块：

```yaml
agents:
  expert_order:
    role: "expert"
    module: "order_system"
    version: "1.0.0"
    capabilities:
      - crud_operations
      - state_machine
      - inventory_management
    input_schema: "schemas/order_input.json"
    output_schema: "schemas/order_output.json"
    dependencies:
      - authentication
      - shopping_cart
```

### 5.3 步骤三：配置流水线

在 `config/pipeline.yaml` 中调整质量门禁：

```yaml
quality_gates:
  - name: "模块审查通过"
    metric: "all_modules_passed"
    operator: "equals"
    value: true
    blocking: true

  - name: "安全评分"
    metric: "security_score"
    operator: ">="
    value: 0.85        # 提高安全门槛
    blocking: true
```

### 5.4 步骤四：运行流水线

```python
from __init__ import ClaudeCodexMultiAgent

system = ClaudeCodexMultiAgent(
    config_dir="config",
    llm_backend="anthropic",
    llm_api_key="your-api-key"
)

# 完整双阶段运行
result = system.run_phase1("构建一个在线商城...")
review = system.run_phase2(
    code_artifact=result['module_specs'],
    compiled_pipeline=result['compiled']
)

if review['passed']:
    print("✅ 代码审查通过，可以部署！")
else:
    print(f"⚠️ 需要 {review['iterations']} 轮修复")
```

### 5.5 步骤五：集成生成的代码

```python
# 编译产物 → Superpowers 运行时配置
config = result['compiled'].to_superpowers_config()

# 保存为 JSON 供 CI/CD 使用
import json
with open("superpowers_config.json", "w") as f:
    json.dump(config, f, indent=2)
```

---

## 6. Schema 编写规范

### 6.1 Input Schema 规范

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `requirement` | string | ✅ | 模块需求描述 |
| `constraints` | string[] | ✅ | 技术约束列表 |
| `dependencies` | string[] | ❌ | 依赖的外部模块 |
| `tech_stack` | object | ❌ | 技术栈要求 |
| `security_requirements` | string[] | ❌ | 安全要求 |
| `compliance_requirements` | string[] | ❌ | 合规要求 |

### 6.2 Output Schema 规范

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `module_spec.components` | array | ✅ | 组件列表（service/model/route 等） |
| `module_spec.interfaces` | array | ✅ | 接口列表（name/method/path） |
| `module_spec.acceptance_criteria` | array | ✅ | 验收标准 |
| `confidence` | number | ✅ | 置信度 0-1 |
| `reasoning` | string | ❌ | 推理过程 |

### 6.3 设计原则

1. **最小权限** — input schema 只包含该模块必需的字段
2. **明确约束** — 用 `default` 值预填充常见约束
3. **可校验** — output schema 的 `required` 确保关键产出不缺失
4. **可扩展** — 用 `properties` 而非 `additionalProperties: false` 允许扩展

---

## 7. 接入真实 LLM

### 7.1 切换到 Anthropic 后端

```python
# 安装 SDK
pip install anthropic

# 初始化
system = ClaudeCodexMultiAgent(
    config_dir="config",
    llm_backend="anthropic",
    llm_api_key=os.environ["ANTHROPIC_API_KEY"]
)
```

### 7.2 LLM Provider 架构

```
tools/llm/
├── base.py              # LLMProvider 抽象基类
├── mock.py              # MockLLMProvider（测试用）
└── anthropic.py         # AnthropicLLMProvider（生产用）
```

### 7.3 自定义 Provider

```python
# tools/llm/custom.py
from tools.llm.base import LLMProvider

class CustomLLMProvider(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        # 接入你的 LLM API
        response = your_client.chat(
            model="your-model",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

---

## 8. 部署上线

### 8.1 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -B -m pytest tests/ -q  # 构建时跑测试

EXPOSE 8000
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建 + 运行
docker build -t claude-codex-multi-agent .
docker run -p 8000:8000 --env ANTHROPIC_API_KEY=xxx claude-codex-multi-agent
```

### 8.2 CI/CD 配置

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python -B -m pytest tests/ --cov=tools --cov=agents -v
      - run: python -B examples/ecommerce_trace.py
```

### 8.3 生产环境检查清单

- [ ] API Key 通过环境变量注入（不硬编码）
- [ ] LLM 调用配置速率限制
- [ ] 启用输出安全审查（guardrails）
- [ ] 配置日志追踪（tracing）
- [ ] 设置超时和重试策略
- [ ] 测试覆盖率 > 80%

---

## 9. 最佳实践

### 9.1 开发流程

```
1. 编写/修改 Schema → 2. 运行测试 → 3. 本地 Trace 验证 → 4. 提交代码
                                                      ↓
                                          CI 自动跑 94+ 测试
                                                      ↓
                                          合并到主分支 → 部署
```

### 9.2 Schema 演进策略

| 场景 | 做法 |
|------|------|
| 新增模块 | 创建新的 input/output JSON，在 agents.yaml 注册 |
| 修改接口 | 更新 output_schema 中的 interfaces 定义 |
| 调整质量 | 修改 pipeline.yaml 的 quality_gates |
| 扩展 Agent | 在 agents.yaml 添加 expert 条目 |

### 9.3 性能优化

- **并行处理**：同层无依赖模块并行分析（已实现）
- **缓存 Schema**：编译产物可序列化复用
- **增量运行**：只重新编译变更的模块
- **LLM 批处理**：合并多个小 Prompt 减少 API 调用

### 9.4 调试技巧

```python
# 开启详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 只运行编译器（不调用 LLM）
from tools.compiler import PipelineCompiler
compiler = PipelineCompiler()
compiled = compiler.compile(output_schemas, input_schemas=input_schemas)
print(compiled.implementation_order)  # 查看拓扑排序
print(compiled.context_strategies)    # 查看上下文策略
print(compiled.quality_gates.gates)    # 查看质量门禁
```

---

## 10. 常见问题

### Q1: Schema 校验失败怎么办？

```bash
# 验证 JSON Schema 语法
python -c "import json; json.load(open('config/schemas/auth_input.json'))"
```

确保：
- `$schema` 字段指向 `http://json-schema.org/draft-07/schema#`
- `required` 列出的字段在 `properties` 中有定义
- `enum` 值用方括号 `[]` 而非花括号

### Q2: 如何添加新的功能模块？

1. 在 `config/schemas/` 创建 `<module>_input.json` 和 `<module>_output.json`
2. 在 `config/agents.yaml` 的 `agents` 下添加 `expert_<module>` 条目
3. 在 `tools/compiler/pipeline_compiler.py` 的 `MODULE_NAME_MAP` 添加映射（如需要）
4. 运行 `python -B -m pytest tests/ -v` 确保不破坏现有测试

### Q3: 如何调整质量门禁阈值？

修改 `config/pipeline.yaml`：

```yaml
quality_gates:
  - name: "安全评分"
    metric: "security_score"
    operator: ">="
    value: 0.9        # 从 0.8 提高到 0.9
    blocking: true
```

### Q4: 编译产物如何集成到 CI/CD？

```python
# 在 CI 中运行编译并导出配置
config = compiled.to_superpowers_config()
with open("deploy_config.json", "w") as f:
    json.dump(config, f)
```

然后在部署时读取 `deploy_config.json` 初始化运行时。

### Q5: 支持哪些 LLM 后端？

当前支持：
- `mock` — 测试用，返回预设响应
- `anthropic` — Claude API（推荐生产使用）

可扩展：继承 `tools/llm/base.py` 的 `LLMProvider` 基类实现自定义后端。

---

## 附录

### A. 模块清单

| 模块 | 文件 | 依赖 | 功能 |
|------|------|------|------|
| authentication | `auth_*.json` | 无 | JWT 认证、会话管理 |
| product_catalog | `product_*.json` | auth | 商品搜索、分类管理 |
| shopping_cart | `cart_*.json` | auth, product | 购物车、价格计算 |
| order_system | `order_*.json` | auth, cart | 订单 CRUD、状态机 |
| payment_integration | `payment_*.json` | auth, order | 支付网关、幂等处理 |
| notification_service | `notification_*.json` | auth | 邮件/短信/推送 |
| data_reporting | `report_*.json` | auth, order | 数据聚合、报表导出 |

### B. 测试覆盖

| 测试目录 | 覆盖内容 | 用例数 |
|----------|----------|--------|
| `tests/compiler/` | 5 个子推导器 | 30+ |
| `tests/stores/` | 3 个数据存储 | 15+ |
| `tests/integration/` | 端到端流水线 | 20+ |
| **总计** | | **94+** |

### C. 参考链接

- [JSON Schema 规范](https://json-schema.org/specification)
- [Anthropic API 文档](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

*教程结束 — 项目已可落地应用于真实开发场景*
