# KodeForge

> **Let enterprises trust AI-generated code — and pass SOC 2 / HIPAA / 等保 audits.**
>
> Schema-first multi-agent code pipeline × Quality Gate convergence × Unskippable HITL approval chain

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-1095%20passed-brightgreen.svg)](tests/)
[![Lines](https://img.shields.io/badge/lines-15k+-purple)](README.md)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](https://github.com/tuyenxesonla07-netizen/Kode-Forge/blob/main/Dockerfile)

---

## The Problem

The #1 concern enterprises have about AI coding tools isn't *speed* — it's **trust**:

- **"Can we ship this?"** AI code quality varies wildly. Without systematic convergence, the tech lead takes the blame when something breaks.
- **"Will auditors accept this?"** SOC 2 auditors ask *"who reviewed this AI-generated code, and when?"* — without an immutable audit trail, there's no answer.
- **"How do we govern AI coding at scale?"** Every developer uses a different standard. No quality floor.

**KodeForge solves all three.**

> We don't compete with AI coding assistants (red ocean, 50+ competitors). We're the **quality gatekeeper after code generation** — compliance infrastructure for AI coding.

---

## How It Works

```
AI generates code (Claude / GPT / Gemini / DeepSeek / 20+ providers)
      │
      ▼
🔒 OutputGuard — injection detection + PII masking + AST safety check
      │
      ▼
📊 QualityEvaluator — auto-scored: critical / high / medium / low
      │
      ├── PASS → AuditLog records → ✅ Ship it
      │
      └── FAIL
            │
            ▼
      ConvergenceDetector — bounded fix loop (max N iterations, guaranteed termination)
            │
            ├── Converged → AuditLog records → ✅ Ship it
            │
            └── Not converged
                  │
                  ▼
            ✋ HITL Approval — Critical issues require human sign-off (UNSKIPPABLE)
                  │
                  ├── Approved → AuditLog records → ✅ Ship it
                  └── Rejected → rejection logged, pipeline halts

      ↑ Entire chain: AuditLog persists (WORM, 6-year retention, SOC 2 / HIPAA ready)
```

**Three guarantees:**

1. **Quality Gate** — automatic scoring with bounded fix loops. `ConvergenceDetector` guarantees termination; no infinite retries.
2. **HITL Approval** — Critical/High issues *require* human approval to proceed. Not a suggestion. Not skippable.
3. **Immutable Audit Log** — every AI generation, quality review, and human approval is permanently recorded for compliance.

---

## Why This Exists

Existing tools leave a critical gap:

| Capability | **KodeForge** | Cursor/Copilot | CodeRabbit | Dify/LangGraph | GitHub Compliance |
|------|------|------|------|------|------|
| Quality Gate + convergence | **✅ Built-in** | ❌ | ❌ | ❌ (build yourself) | ❌ |
| Unskippable HITL approval | **✅ First-class** | ❌ | ❌ | ❌ | ⚠️ Partial |
| SOC 2 / HIPAA audit trail | **✅ Immutable logs** | ❌ | ❌ | ⚠️ Partial | ⚠️ Beta |
| Schema-first pipeline | **✅ Zero-code modules** | ❌ | — | ❌ | ❌ |
| RAG dual-engine | **✅ Search + Cognitive** | ❌ | ❌ | ⚠️ Single-engine | ❌ |
| 20+ LLM providers | **✅ Swap with one CLI command** | ❌ | ❌ | ✅ | ❌ |

Most multi-agent frameworks make you wire agents by hand: `agent_a → agent_b → agent_c`. Change one agent, the DAG breaks.

**KodeForge is schema-first**: define *what* (module contracts as JSON Schema), the compiler figures out *how* (execution order, context injection, retry strategy, quality gates). Add a module by dropping two JSON files — zero Python code.

---

## Quick Start

### Option A: Zero-Config Demo (no API key required)

```bash
git clone https://github.com/tuyenxesonla07-netizen/Kode-Forge.git
cd Kode-Forge
pip install -e ".[dev]"
```

```bash
# Full pipeline demo with mock LLM — zero dependencies
python -m tools.cc_switch status
```

### Option B: With Real LLM

```bash
# Pick one provider:
export ANTHROPIC_API_KEY="sk-ant-..."        # Claude (recommended for code review quality)
export OPENAI_API_KEY="sk-..."               # OpenAI / DeepSeek / Tongyi / Kimi / Zhipu
export GEMINI_API_KEY="AIza..."              # Gemini

# Set quality preset for your industry:
export KODEFORGE_PRESET=financial-general    # Options: financial-general, financial-tier3, financial-sox, hipaa-phi

# Start API server
python -m tools.cc_switch serve --port 8080
```

Available endpoints:
- `POST /api/v1/pipeline/run` — submit code to the full pipeline
- `GET /api/v1/health` — health check
- API docs at `http://localhost:8080/docs`

### Option C: Docker

```bash
docker compose up             # Development mode
docker compose -f docker-compose.prod.yml up -d   # Production (nginx + app)
```

---

## Quality Gate Presets (out of the box)

| Preset | Use Case | Key Constraints |
|------|---------|---------|
| `financial-general` | City commercial banks / fintech | Critical issues = 0; Quality Score ≥ 0.80 |
| `financial-tier3` | Tier-3 accredited banking core systems | Critical + High = 0; AI-generated ratio ≤ 60% |
| `financial-sox` | SOX financial reporting systems | HITL enforced for all modules; four-eyes approval |
| `hipaa-phi` | Healthcare (HIPAA) | ePHI zero tolerance; human attestation required |

Edit `config/pipeline.yaml` to create custom presets. Human-readable YAML.

---

## Compliance Mapping

**SOC 2 (CC6 + CC7 + CC8):**
1. Which code is AI-generated → `AuditLog` tags source automatically
2. Who reviewed AI output and when → `HITLApproval` node logs the event
3. Model version + prompt traceability → `Tracer` full-chain recording
4. Immutable audit logs, 6-year retention → `AuditLog` designed for this

**HIPAA 2025 OCR Final Guidance:**
- AI-generated code requires `HumanAttestation` before deployment
- KodeForge's `HITLApprovalHandler` maps directly to this requirement

Full audit report: [SECURITY_RED_TEAM_REPORT.md](docs/SECURITY_RED_TEAM_REPORT.md)

---

## Architecture

```
User Requirement
  → 🔒 InputGuard (injection detection + PII masking)
  → 🧠 Memory.load() (restore context)
  → ✋ HITL.request_approval() (risk-based gate)
  → 📊 CodexSupervisor.parse_requirement() → identify modules
  → 🔧 PipelineCompiler.compile() → context/order/prompts/fixes/gates
  → 📦 ExpertAgent.process() × N (Skills injection, parallel)
  → ✍️ Supervisor.generate_code() × N (LLM code gen + AST validation)
  → ✅ OutputGuard.check() (code safety + PII cleanup)
  → 📊 QualityEvaluator + ConvergenceDetector (fix loop until convergence)
  → ✋ HITLApproval (Critical issues → human sign-off, unskippable)
  → 📋 AuditLog.record() (immutable, 6-year retention)
  → 🔍 Tracer + PipelineMetrics (full observability)
```

See [CLAUDE.md](CLAUDE.md) for detailed internal architecture.

---

## Adding a New Module

**Zero code changes** — just two config files:

1. Add `config/schemas/xxx_input.json` + `xxx_output.json`
2. Add `expert_xxx` section to `config/agents.yaml` with capabilities
3. Auto-discovered at runtime

---

## Use Cases

- **Financial core systems AI Coding compliance** — 等保三级 + SOC 2 + 银保监发〔2022〕2号
- **Healthcare SaaS HIPAA compliance** — 2025 OCR guidance requires human attestation for AI-generated code
- **Government digitalization AI audit trails** — traceability required for government procurement
- **500+ engineer team AI Coding governance** — quality floor + convergence guarantees + trend tracking
- **Fintech SOC 2 Type II audit** — Audit Log exports directly; auditors pass in one round

---

## Testing

```bash
python -m pytest tests/ -v
# 1095 passed, 13 skipped, 0 failed
```

Coverage spans: pipeline compiler, RAG dual-engine, quality gate, HITL approval, audit chain, guardrails, workflow DAG, LLM provider abstraction, memory, messaging, observability, and 8 security test categories (RAG defense, audit persistence, output guardrails, API auth, critical risk, rate limiting, semantic injection).

---

## Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](docs/QUICK_START.md) | 5-minute getting started |
| [Quality Gate Config](docs/PIPELINE_CONFIG.md) | Quality gate, timeout, retry policy |
| [Schema Guide](docs/SCHEMA_GUIDE.md) | How to write module JSON Schemas |
| [RAG Config](docs/RAG_CONFIG.md) | Search + Cognitive engine parameters |
| [Skill Authoring](docs/SKILL_AUTHORING.md) | How to write custom Skills |
| [Deployment](docs/DEPLOYMENT.md) | Docker / production deployment (SOC 2 guidance) |
| [Security Audit Report](docs/SECURITY_RED_TEAM_REPORT.md) | Full red team audit findings |
| [ADR](docs/adr/README.md) | Architecture Decision Records (6 ADRs) |

---

## Environment Variables

| Variable | Used For | Default |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Claude (recommended for code review quality) | — |
| `ANTHROPIC_BASE_URL` | Custom gateway / proxy URL | — |
| `ANTHROPIC_MODEL` | Model override (e.g. `claude-opus-4-7`) | — |
| `OPENAI_API_KEY` | OpenAI-compatible (DeepSeek/Tongyi/Zhipu/Kimi) | — |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint URL | — |
| `OPENAI_MODEL` | Model override (e.g. `gpt-4o`) | — |
| `GEMINI_API_KEY` | Google Gemini | — |
| `KODEFORGE_PRESET` | Quality Gate preset | `financial-general` |
| `HITL_THRESHOLD` | HITL trigger threshold | `medium` |

Full list: [`.env.example`](.env.example)

---

## Roadmap

| Phase | Timeline | Milestone |
|-------|---------|-----------|
| **v0.4 (now)** | Current | Quality Gate + HITL + AuditLog complete; 1095 tests passing |
| **v0.5** | Next | `kodeforge-gate` standalone CLI (`pip install`) |
| **v0.6** | Next | GitHub Action integration (developer acquisition channel) |
| **v1.0** | Target | GA with seed customers in financial vertical |

See [docs/PATH_A_ROADMAP](docs/PATH_A_ROADMAP.md) for the full strategic plan.

---

## License

MIT
