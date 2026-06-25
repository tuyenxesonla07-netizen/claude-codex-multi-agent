# claude-codex-multi-agent

Schema-First Multi-Agent Development Pipeline

A Python-based orchestration framework that compiles module schemas into structured agent workflows. Each functional module (auth, product catalog, shopping cart, order system, payment, notification, reporting) is analyzed by a dedicated expert agent, with automated context derivation, quality gates, and fix-loop convergence.

## What it does

- **Schema-first compilation**: JSON input/output schemas drive prompt generation, context injection, fix templates, and quality gates automatically.
- **7 expert agents + 1 supervisor**: Hierarchical delegation with dependency-aware topological ordering.
- **Automated quality gates**: Generated from output schemas; algorithmic convergence detection for fix loops.
- **Pluggable LLM layer**: Mock provider (deterministic, no API key) + Anthropic Claude integration.
- **Event-driven messaging**: Pub/sub message bus with topic-based routing between agents.
- **In-memory stores**: Requirement, interface, and spec stores for runtime state management.

## Quick Start

```bash
# Run all tests
python -B -m pytest tests/ -v

# Run end-to-end trace example
python -B -c "import examples.ecommerce_trace; examples.ecommerce_trace.run_trace()"
```

## Architecture

```
User → Supervisor → PipelineCompiler → Expert Agents → Supervisor
                      ↓
                ContextDeriver → auto-inject context
                FixDeriver → auto-generate fix instructions
                QualityGateGenerator → auto-gate from schemas
```

## Modules

| Module | Expert | Dependencies |
|--------|--------|-------------|
| authentication | AuthExpert | — |
| product_catalog | ProductExpert | authentication |
| shopping_cart | CartExpert | authentication |
| order_system | OrderExpert | authentication, shopping_cart |
| payment_integration | PaymentExpert | authentication, order_system |
| notification_service | NotificationExpert | authentication |
| data_reporting | ReportExpert | authentication, order_system |

## Testing

```bash
python -B -m pytest tests/ -v
python -B -m pytest tests/ --cov=tools --cov=agents -v
```
