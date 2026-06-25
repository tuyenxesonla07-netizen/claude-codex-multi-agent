# Claude-Codex Multi-Agent Pipeline

This project uses a schema-driven multi-agent architecture for automated code generation.

## Core Principle
Agents are defined in `config/schemas/` and `config/agents.yaml`.
Do not modify `agents/experts/__init__.py` unless adding new base capabilities.
New modules = new schema files + YAML registration only.

## Key Files
- `agents/experts/__init__.py` — Single `ExpertAgent` class + `create_expert_agents()` auto-discovery
- `config/schemas/` — Module definitions (input/output JSON Schema)
- `config/agents.yaml` — Agent capabilities and routing config
- `tools/compiler/` — Schema → orchestration logic compiler
- `tools/rag/` — pgvector-backed knowledge base
- `tools/mcp/` — MCP tool server

## Adding a Module
1. Create `config/schemas/{module}_input.json` + `{module}_output.json`
2. Add `expert_{module}` to `config/agents.yaml` with capabilities list
3. Done — no Python changes needed
