# Claude-Codex Multi-Agent Pipeline

## Project Overview
Schema-first multi-agent development pipeline. Compiles JSON schemas into orchestration logic, then dispatches to expert agents for code generation, quality review, and fix loops.

## Architecture
```
User Requirement
  → CodexSupervisor (parse → identify modules → dispatch)
    → PipelineCompiler (context strategies → dependency graph → quality gates)
      → ExpertAgent × N (auto-discovered from config/schemas/)
        → ClaudeCodeExecutor (LLM code generation + AST validation)
          → QualityEvaluator → ConvergenceDetector → Fix loop
```

## Key Directories
- `agents/supervisor/` — Orchestrator (run_phase1, run_phase2)
- `agents/experts/` — Dynamic expert agents (auto-discovered, no per-module classes)
- `tools/compiler/` — Pipeline compiler (context deriver, quality gates, fix instructions)
- `tools/rag/` — Knowledge base with pgvector
- `tools/mcp/` — MCP tool server (JSON-RPC over SSE)
- `tools/skills/` — Skill packages (SKILL.md, auto-loaded)
- `tools/memory/` — Short-term + long-term memory
- `tools/guardrails/` — Input/output security
- `tools/hitl/` — Human-in-the-loop approval + audit
- `tools/observability/` — Tracing + metrics
- `tools/eval/` — Automated evaluation suite
- `config/schemas/` — Module input/output schemas (JSON)
- `config/agents.yaml` — Agent registry and capabilities

## Adding a New Module
1. Add `config/schemas/xxx_input.json` + `xxx_output.json`
2. Add `expert_xxx` section to `config/agents.yaml` with capabilities
3. No Python code changes needed — auto-discovered at runtime

## Commands
```bash
# Run end-to-end trace
python -m examples.ecommerce_trace

# Run tests
python -m pytest tests/ -v

# Run eval suite
python -m tools.eval.runner

# Start server
uvicorn server.app:app --reload

# Frontend
cd frontend && npm run dev
```

## Environment Variables
- `LLM_API_KEY` — API key for LLM provider
- `LLM_API_BASE_URL` — Base URL (default: https://www.dayueai.fun)
- `LLM_API_MODEL` — Model name (default: claude-opus-4-7)
- `DATABASE_URL` — PostgreSQL connection (optional, falls back to SQLite)
