# 🛡️ KodeForge

> **让企业敢用 AI 写代码，并能过 SOC 2 / HIPAA / 等保 审计**
>
> Schema-first 多智能体代码生成管线 × Quality Gate 收敛机制 × HITL 不可绕过审批链

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-1095%20passed-brightgreen.svg)](tests/)
[![Docker](https://img.shields.io/badge/docker-kodeforge%2Fcompliance-blue)](https://github.com/your-org/kodeforge/pkgs/container/kodeforge)

---

## 为什么需要这个？

企业用 AI 写代码最大的顾虑不是「写得不够快」，而是：

- **敢上线吗？** AI 代码质量参差不齐，没有系统收敛机制，出事背锅的是技术负责人
- **审计能过吗？** SOC 2 审计员问"AI 写的代码谁审的"，没有完整合规记录就没法回答
- **团队规模用 AI 后怎么管？** 每人都在用，标准不统一，质量无底线

**KodeForge 解决这三层问题：**

1. **Quality Gate 收敛** — 代码生成后自动评分，不通过就进入有界修复循环（ConvergenceDetector 保证终止，不会无限重试）
2. **HITL 审批链** — Critical/High issue 必须人工审批才能继续（不可绕过，不是"建议"）
3. **不可篡改审计日志** — 每次 AI 生成、质量评估、人工审批的完整链路，6 年留痕，SOC 2 / HIPAA / 等保 直接适用

**不做"AI 编码助手"（红海），做"AI 编码的合规基础设施"——代码生成之后的质量守门员。**

---

## 60 秒体验（无需 LLM API Key）

```bash
# 拉取 Docker 镜像
docker pull ghcr.io/your-org/kodeforge:latest

# 查看运行状态和可用合规预设
docker run --rm ghcr.io/your-org/kodeforge:latest status

# 跑质量门禁 demo（用内置 mock 数据，零依赖）
docker run --rm ghcr.io/your-org/kodeforge:latest validate --config-dir config

# 启动 API 服务（填入你自己的 LLM Key）
docker run --rm -p 8080:8080 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  ghcr.io/your-org/kodeforge:latest serve
```

启动后：
- API 文档 → http://localhost:8080/docs
- 健康检查 → http://localhost:8080/api/v1/health
- 提交代码到管线 → `POST /api/v1/pipeline/run`

---

## Workflow

```
AI 生成代码（Claude / GPT / Gemini）
      │
      ▼
🔒 OutputGuard（injection + PII 检测）
      │
      ▼
📊 QualityEvaluator（自动评分: critical / high / medium / low）
      │
      ├── PASS ──────────── AuditLog 记录 → ✅ 上线
      │
      └── FAIL
            │
            ▼
      ConvergenceDetector（有界修复循环，最多 N 次）
            │
            ├── 收敛 → AuditLog 记录 → 上线
            │
            └── 未收敛
                  │
                  ▼
            ✋ HITLApproval（Critical 必须人工审批，不可绕过）
                  │
                  ├── 通过 → AuditLog 记录 → 上线
                  └── 拒绝 → 拒绝记录留痕，流程终止

      ↑
整个链路：AuditLog 代码化保存（WORM，6 年不可篡改，SOC 2 / HIPAA 就绪）
```

---

## Quality Gate 预设（开箱即用）

| 预设 | 适用场景 | 关键约束 |
|------|---------|---------|
| `financial-general` | 城商行 / 金融科技 | Critical issue = 0；Quality Score ≥ 0.80 |
| `financial-tier3` | 等保三级银行核心系统 | Critical + High = 0；AI 生成代码占比 ≤ 60% |
| `financial-sox` | SOX 财务报告系统 | 所有模块强制 HITL；双人双签审批链 |
| `hipaa-phi` | 医疗健康（HIPAA） | ePHI 零容忍；人工 attestation 必须；季度审计 |

配置文件位于 `kodeforge_quality/presets/[name].yaml`，人类可读可定制。

---

## 核心差异（vs 现有工具）

| 维度 | KodeForge | Cursor / Copilot | CodeRabbit | Dify / LangGraph |
|------|-----------|------------------|------------|------------------|
| 代码生成 | ✅ Schema 驱动 | ✅ 通用 | ❌（只做 Review） | ✅ Agent 框架 |
| **质量门禁 + 收敛检测** | **✅ 内置** | ❌ | ❌ | ❌ 需自建 |
| **HITL 不可绕过审批** | **✅ 架构一等公民** | ❌ | ❌ | ❌ |
| **SOC 2 / HIPAA 审计追踪** | **✅ 不可篡改日志** | ❌ | ❌ | ⚠️ 部分 |
| RAG 双引擎辅助生成 | ✅ | ❌ | ❌ | ⚠️ 单引擎 |
| Schema-first（新增模块零代码） | ✅ | ❌ | — | ❌ |

---

## 架构

```
User Requirement
  → 🔒 InputGuard (injection detection + PII masking)
  → 🧠 Memory.load() (restore context)
  → ✋ HITL.request_approval() (risk-based gate)
  → 📊 CodexSupervisor.parse_requirement() → identify modules
  → 🔧 PipelineCompiler.compile() → context/order/prompts/fixes/gates
  → 📦 ExpertAgent.process() × N (with Skills injection, parallel)
  → ✍️ Supervisor.generate_code() × N (LLM code gen + AST validation)
  → ✅ OutputGuard.check() (code safety + PII cleanup)
  → 📊 QualityEvaluator + ConvergenceDetector (fix loop until convergence)
  → ✋ HITLApproval (Critical issues → human sign-off, unskippable)
  → 📋 AuditLog.record() (immutable, 6-year retention)
  → 🔍 Tracer + PipelineMetrics (full observability)
```

---

## Quick Start

### 选项 A：Docker（推荐种子客户试用）

```bash
# 拉镜像
docker pull ghcr.io/your-org/kodeforge:latest

# 跑 demo
docker run --rm ghcr.io/your-org/kodeforge:latest validate

# 启动服务
cp .env.example .env     # 填入你的 LLM Key
docker compose up
# 或生产模式
docker compose -f docker-compose.prod.yml up -d
```

### 选项 B：本地安装

```bash
pip install kodeforge
cc status                # 查看可用 LLM 和组件状态
cc run "Build a JWT auth module with FastAPI"   # 真实 LLM 完整管线
```

### Python API

```python
from kodeforge_quality import (
    QualityEvaluator, ConvergenceDetector, AuditLogger, GateConfig
)

evaluator = QualityEvaluator.from_preset("financial-general")
report = evaluator.evaluate(review_results)

if not report.passed:
    detector = ConvergenceDetector(max_iterations=3)
    should_fix, reason = detector.should_continue(iteration, report)
    if not should_fix:
        raise HITLRequiredException(report.audit_bundle)
```

---

## Use Cases

- **金融核心系统 AI Coding 合规** — 等保三级 + SOC 2 + 银保监发〔2022〕2 号
- **医疗 SaaS HIPAA 合规** — 2025 OCR 指引 AI 代码部署前必须有人工 attestation
- **政务数字化 AI 审计追踪** — 政府采购 AI 工具合规留痕
- **500+ 人研发团队 AI Coding 治理** — 质量底线 + 收敛保证 + 团队质量趋势
- **金融科技 SOC 2 Type II 审核** — Audit Log 直接输出，审计员一次性通过

---

## Testing

```bash
python -m pytest tests/ -v
# 1095 passed, 13 skipped, 0 failed
```

| Test File | Coverage Area | Tests |
|-----------|--------------|-------|
| `tests/test_quality.py` | QualityGate + ConvergenceDetector | 31 |
| `tests/test_hitl.py` | HITL Approval + AuditLog | 21 |
| `tests/test_guardrails.py` | Input/output security | 22 |
| `tests/compiler/` | Pipeline compiler | ~67 |
| `tests/integration/` | End-to-end pipeline | ~100 |
| `tests/stores/` | State management | ~20 |

---

## Documentation

| Document | 内容 |
|----------|------|
| [Quick Start](docs/QUICK_START.md) | 5 分钟上手 |
| [Quality Gate 配置](docs/PIPELINE_CONFIG.md) | 质量门禁、超时、重试策略 |
| [Schema Guide](docs/SCHEMA_GUIDE.md) | 模块 Schema 编写指南 |
| [RAG 双引擎调参](docs/RAG_CONFIG.md) | Search + Cognitive 引擎参数 |
| [Deployment](docs/DEPLOYMENT.md) | Docker / 生产部署（含 SOC 2 指引） |

---

## Environment Variables

| Variable | 用途 | 默认值 |
|----------|------|--------|
| `ANTHROPIC_API_KEY` | Claude（推荐用于代码审查质量） | — |
| `OPENAI_API_KEY` | OpenAI 兼容（DeepSeek/Tongyi/Zhipu/Kimi） | — |
| `KODEFORGE_PRESET` | Quality Gate 预设等级 | `financial-general` |
| `HITL_THRESHOLD` | HITL 触发阈值 | `clinical` |
| `AUDIT_LOG_DIR` | 审计日志目录 | `/tmp/audit` |
| `CC_SERVER_PORT` | API 端口 | `8080` |

完整变量列表见 [`.env.example`](.env.example)

---

## Project Structure

```
├── agents/                  # Supervisor + Expert agents
├── tools/
│   ├── quality/             # ⭐ QualityEvaluator + ConvergenceDetector
│   ├── hitl/                # ⭐ HITL risk-based approval + AuditLog
│   ├── guardrails/          # Input/output security
│   ├── compiler/            # Schema → compiled pipeline
│   ├── rag/                 # Dual-engine RAG (BM25+Vector+Graph + Cognitive)
│   ├── workflow/            # DAG engine
│   ├── llm/                 # 20+ LLM provider abstraction
│   └── cc_cli.py            # Unified CLI entry point
├── config/
│   ├── schemas/             # Module JSON schemas
│   ├── agents.yaml          # Agent registry
│   └── pipeline.yaml        # Quality gate, retry policies
├── packages/
│   └── kodeforge-quality/   # ⭐ Standalone Quality Gate pip package
├── Dockerfile.compliance    # ⭐ Seed-customer Docker image
├── Dockerfile.production    # Production Docker image
├── docker-compose.yml       # One-command dev deployment
├── docker-compose.prod.yml  # Production deployment (nginx + app)
├── .env.example             # Environment variable template
├── tests/                   # 1095+ tests
└── pyproject.toml           # Package config
```

---

## Roadmap

**Phase 1（现在） — 合规投资版**
- [x] Quality Gate + HITL 审批链（核心能力）
- [ ] `kodeforge-quality` 独立库（可 pip install）
- [ ] 金融/等保/HIPAA 预设配置文件
- [ ] 种子客户部署 + 白皮书

**Phase 2（Q4 2026） — 渠道与基础设施**
- [ ] GitHub Action 集成（开发者获客入口）
- [ ] SOC 2 / HIPAA 认证套件文档
- [ ] Team 商业版（$49/人/月）

**Phase 3（2027 H1） — 规模化**
- [ ] v1.0 商业版 GA
- [ ] 医疗/政务垂直扩展
- [ ] 渠道合作伙伴生态

详见 [docs/PATH_A_ROADMAP.md](docs/PATH_A_ROADMAP.md)

---

## License

MIT
