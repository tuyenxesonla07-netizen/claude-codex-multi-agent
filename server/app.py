"""
server/app.py

FastAPI server for the Multi-Agent Development Pipeline.
Provides REST endpoints for pipeline execution and status monitoring.

Usage:
    uvicorn server.app:app --reload
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `from tools.xxx import ...` works
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# ===========================================================================
# Logging
# ===========================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger("server.app")

# ===========================================================================
# Pydantic models
# ===========================================================================
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

if BaseModel is not None:
    class CompileRequest(BaseModel):
        project_name: str = "Untitled"
        project_description: str = ""
        modules: Optional[List[str]] = None
        global_constraints: Optional[Dict[str, str]] = None

    class RunRequest(BaseModel):
        requirement: str
        project_name: str = "Untitled"
        modules: Optional[List[str]] = None
        stream: bool = True

    class AgentDirectRequest(BaseModel):
        requirement: str = ""
        constraints: List[str] = []
        dependency_interfaces: Dict[str, Any] = {}
        global_constraints: Dict[str, str] = {}
        mode: str = "analysis"
        code_snippet: Optional[str] = None

    class ErrorResponse(BaseModel):
        error: str
        detail: Optional[str] = None
        timestamp: str

# ===========================================================================
# Module name alias mapping
# ===========================================================================
MODULE_NAME_ALIASES = {
    "auth": "authentication",
    "product": "product_catalog",
    "cart": "shopping_cart",
    "order": "order_system",
    "payment": "payment_integration",
    "notification": "notification_service",
    "report": "data_reporting",
}
MODULE_NAMES = list(MODULE_NAME_ALIASES.values())

# ===========================================================================
# In-memory task store
# ===========================================================================
_task_store: Dict[str, Dict[str, Any]] = {}

# ===========================================================================
# FastAPI app + CORS
# ===========================================================================
app = FastAPI(
    title="Claude-Codex Multi-Agent Pipeline",
    description="Schema-First Multi-Agent Development Pipeline API",
    version="3.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================================================
# Global exception handlers
# ===========================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

# ===========================================================================
# Helpers
# ===========================================================================

def _resolve_module_name(name: str) -> str:
    return MODULE_NAME_ALIASES.get(name, name)

def _load_schemas(config_dir: str = None) -> tuple:
    if config_dir is None:
        config_dir = os.path.join(_PROJECT_ROOT, "config")
    schemas_dir = os.path.join(config_dir, "schemas")
    input_schemas: Dict[str, Any] = {}
    output_schemas: Dict[str, Any] = {}
    if not os.path.exists(schemas_dir):
        return input_schemas, output_schemas
    for filename in os.listdir(schemas_dir):
        path_ = os.path.join(schemas_dir, filename)
        with open(path_, encoding="utf-8") as f:
            schema = json.load(f)
        if filename.endswith("_input.json"):
            input_schemas[filename.replace("_input.json", "")] = schema
        elif filename.endswith("_output.json"):
            output_schemas[filename.replace("_output.json", "")] = schema
    return input_schemas, output_schemas

def _load_agents_config(config_dir: str = None) -> dict:
    try:
        import yaml as _yaml
    except ImportError:
        logger.warning("pyyaml not installed, /agents endpoint will return empty list. Install with: pip install pyyaml")
        return {}
    if config_dir is None:
        config_dir = os.path.join(_PROJECT_ROOT, "config")
    agents_path = os.path.join(config_dir, "agents.yaml")
    if os.path.exists(agents_path):
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        yaml_lines: List[str] = []
        in_yaml = False
        for line in lines:
            if line.strip().startswith("```yaml"):
                in_yaml = True
                continue
            if line.strip() == "```" and in_yaml:
                break
            if in_yaml:
                yaml_lines.append(line)
        return _yaml.safe_load("\n".join(yaml_lines)) if yaml_lines else {}
    return {}

def _build_agent_list(agents_config: dict) -> List[Dict[str, Any]]:
    agents = agents_config.get("agents", {})
    result = []
    for agent_id, cfg in agents.items():
        result.append({
            "agent_id": agent_id,
            "role": cfg.get("role", "unknown"),
            "module": cfg.get("module", ""),
            "version": cfg.get("version", "1.0.0"),
            "capabilities": cfg.get("capabilities", []),
            "dependencies": cfg.get("dependencies", []),
            "review_capabilities": cfg.get("review_capabilities", []),
        })
    return result

def _get_module_schemas(output_schemas: Dict[str, Any], modules: Optional[List[str]] = None) -> Dict[str, Any]:
    if not modules:
        return output_schemas
    resolved = {_resolve_module_name(m) for m in modules}
    return {k: v for k, v in output_schemas.items() if k in resolved}

async def _update_task(task_id: str, **kwargs):
    task = _task_store.get(task_id)
    if task:
        task.update(kwargs)
        task["updated_at"] = datetime.now(timezone.utc).isoformat()

# ===========================================================================
# Existing endpoints
# ===========================================================================

@app.get("/")
async def root():
    return {"status": "ok", "service": "claude-codex-multi-agent"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/modules")
async def list_modules():
    return {"modules": MODULE_NAMES}

@app.get("/schema/{module_name}")
async def get_schema(module_name: str):
    schemas_dir = os.path.join(_PROJECT_ROOT, "config", "schemas")
    resolved = _resolve_module_name(module_name)
    output_path = os.path.join(schemas_dir, f"{resolved}_output.json")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail=f"Schema not found for module: {module_name}")
    with open(output_path, encoding="utf-8") as f:
        schema = json.load(f)
    return {"module": module_name, "schema": schema}

# ===========================================================================
# 1. POST /pipeline/compile
# ===========================================================================

@app.post("/pipeline/compile")
async def pipeline_compile(body: Dict[str, Any]):
    from tools.compiler import PipelineCompiler

    project_name = body.get("project_name", "Untitled") if isinstance(body, dict) else "Untitled"
    project_description = body.get("project_description", "") if isinstance(body, dict) else ""
    modules = body.get("modules", None) if isinstance(body, dict) else None
    global_constraints = body.get("global_constraints", None) if isinstance(body, dict) else None

    input_schemas, output_schemas = _load_schemas()
    filtered_schemas = _get_module_schemas(output_schemas, modules)

    if not filtered_schemas:
        raise HTTPException(status_code=400, detail="No module schemas found for the given modules")

    compiler = PipelineCompiler(global_constraints=global_constraints)
    compiled = compiler.compile(
        filtered_schemas,
        input_schemas=input_schemas,
        project_name=project_name,
        project_description=project_description,
    )

    config = compiled.to_superpowers_config()
    return JSONResponse(content={
        "success": True,
        "project_name": compiled.metadata.get("project_name", project_name),
        "module_count": len(compiled.module_schemas),
        "implementation_order": compiled.implementation_order,
        "context_strategies": config["pipeline"]["phases"]["requirement_decomposition"]["context_strategies"],
        "fix_templates": config["pipeline"]["phases"]["code_review"]["fix_templates"],
        "quality_gates": config["pipeline"]["phases"]["code_review"]["quality_gates"],
        "prompt_template": compiled.prompt_template.template_str,
        "metadata": compiled.metadata,
    })

# ===========================================================================
# 2. POST /pipeline/run
# ===========================================================================

@app.post("/pipeline/run")
async def pipeline_run(body: Dict[str, Any]):
    requirement_text = body.get("requirement", "") if isinstance(body, dict) else ""
    project_name = body.get("project_name", "Untitled") if isinstance(body, dict) else "Untitled"
    modules = body.get("modules", None) if isinstance(body, dict) else None
    stream = body.get("stream", True) if isinstance(body, dict) else True

    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    _task_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "current_step": None,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }

    if stream:
        return StreamingResponse(
            _stream_pipeline(task_id, requirement_text, project_name, modules),
            media_type="text/event-stream",
        )
    else:
        result = await _execute_pipeline(task_id, requirement_text, project_name, modules)
        return JSONResponse(content={"success": True, "task_id": task_id, **result})

# ===========================================================================
# Pipeline execution (shared)
# ===========================================================================

async def _run_phase1(task_id, requirement_text, project_name, compiled, llm_provider):
    from tools.agent import ClaudeCodeExecutor
    from agents.supervisor import CodexSupervisor, Requirement
    from agents.experts import create_expert_agents

    executor = ClaudeCodeExecutor(llm_provider=llm_provider)
    agents_config = _load_agents_config()
    supervisor = CodexSupervisor(agents_config)
    experts = create_expert_agents(
        os.path.join(_PROJECT_ROOT, "config", "schemas"),
        llm_provider=llm_provider,
    )
    requirement = Requirement(
        functional_modules=compiled.implementation_order,
        raw_text=requirement_text,
    )
    return supervisor.run_phase1(
        requirement=requirement,
        experts=experts,
        compiled_pipeline=compiled,
        llm_provider=llm_provider,
    )

async def _run_phase2(task_id, code_artifact, module_specs, compiled, llm_provider):
    from agents.experts import create_expert_agents, ReviewInput
    from tools.quality import QualityEvaluator, ConvergenceDetector

    experts = create_expert_agents(
        os.path.join(_PROJECT_ROOT, "config", "schemas"),
        llm_provider=llm_provider,
    )
    quality_evaluator = QualityEvaluator(quality_gates=compiled.quality_gates)
    detector = ConvergenceDetector(max_iterations=3)

    review_results = []
    for module_name in compiled.implementation_order:
        expert = experts.get(module_name)
        code = code_artifact.get(module_name, "")
        spec = module_specs.get(module_name, {})
        if expert and code:
            review_input = ReviewInput(
                module_name=module_name,
                code_snippet=code,
                expected_interfaces=spec.get("interfaces", []),
                expected_acceptance_criteria=spec.get("acceptance_criteria", []),
            )
            review_output = expert.review(review_input)
            review_results.append({
                "module": module_name,
                "verdict": review_output.verdict,
                "issues": review_output.issues,
                "metrics": review_output.metrics,
            })

    iteration = 0
    report = quality_evaluator.evaluate(review_results, iteration=iteration)
    while True:
        should_continue, reason = detector.should_continue(
            iteration=iteration,
            quality_score=report.quality_score,
            has_critical=report.has_critical,
        )
        if not should_continue:
            break
        iteration += 1
        report = quality_evaluator.evaluate(review_results, iteration=iteration)

    return {
        "passed": report.passed,
        "quality_score": report.quality_score,
        "iterations": iteration,
        "convergence_status": reason,
        "reviews": review_results,
    }

async def _execute_pipeline(task_id, requirement_text, project_name, modules):
    try:
        await _update_task(task_id, status="phase1", progress=0.0, current_step="initializing")
        input_schemas, output_schemas = _load_schemas()
        filtered_schemas = _get_module_schemas(output_schemas, modules)

        if not filtered_schemas:
            await _update_task(task_id, status="failed", error="No module schemas found")
            return {"phase1": None, "phase2": None, "code_artifact": None, "message": "No module schemas found"}

        from tools.compiler import PipelineCompiler
        try:
            from tools.agent.claude_code import DayueAIProvider
            llm_provider = DayueAIProvider()
        except (ValueError, ImportError) as e:
            await _update_task(task_id, status="failed", error=f"LLM provider init failed: {e}")
            return {"phase1": None, "phase2": None, "code_artifact": None, "message": str(e)}

        compiler = PipelineCompiler()

        await _update_task(task_id, progress=0.1, current_step="expert_analysis")
        phase1_result = await _run_phase1(task_id, requirement_text, project_name, compiled, llm_provider)
        code_artifact = phase1_result.get("code_artifact", {})
        module_specs = phase1_result.get("module_specs", {})

        await _update_task(task_id, status="phase2", progress=0.6, current_step="code_review")
        phase2_result = await _run_phase2(task_id, code_artifact, module_specs, compiled, llm_provider)

        code_summary = {mod: {"lines": code.count(chr(10)) + 1 if code else 0} for mod, code in code_artifact.items()}
        await _update_task(task_id, status="completed", progress=1.0)

        return {
            "phase1": {"module_specs": module_specs, "code_summary": code_summary},
            "phase2": phase2_result,
            "code_artifact": code_artifact,
        }
    except Exception as exc:
        logger.exception("Pipeline execution failed")
        await _update_task(task_id, status="failed", error=str(exc))
        return {"phase1": None, "phase2": None, "code_artifact": None, "message": str(exc)}

# ===========================================================================
# Streaming pipeline (SSE)
# ===========================================================================

async def _stream_pipeline(task_id, requirement_text, project_name, modules):
    def _event(event_type, data):
        payload = json.dumps(data, ensure_ascii=False, default=str)
        return f"event: {event_type}\ndata: {payload}\n\n"

    try:
        await _update_task(task_id, status="phase1", progress=0.0, current_step="initializing")
        yield _event("phase", {"phase": "phase1", "status": "started"})

        await _update_task(task_id, progress=0.05, current_step="loading_schemas")
        yield _event("step", {"step": "loading_schemas", "message": "Loading schemas..."})

        input_schemas, output_schemas = _load_schemas()
        filtered_schemas = _get_module_schemas(output_schemas, modules)

        if not filtered_schemas:
            yield _event("error", {"error": "No module schemas found"})
            await _update_task(task_id, status="failed", error="No module schemas found")
            return

        await _update_task(task_id, progress=0.1, current_step="compiling_pipeline")
        yield _event("step", {"step": "compiling_pipeline", "message": "Compiling pipeline..."})

        from tools.compiler import PipelineCompiler
        try:
            from tools.agent.claude_code import DayueAIProvider
            llm_provider = DayueAIProvider()
        except (ValueError, ImportError) as e:
            yield _event("error", {"error": f"LLM provider init failed: {e}"})
            await _update_task(task_id, status="failed", error=str(e))
            return

        compiler = PipelineCompiler()
        compiled = compiler.compile(filtered_schemas, input_schemas=input_schemas, project_name=project_name)

        yield _event("compiled", {
            "implementation_order": compiled.implementation_order,
            "module_count": len(compiled.module_schemas),
            "quality_gates": len(compiled.quality_gates.gates),
        })

        await _update_task(task_id, progress=0.2, current_step="expert_analysis")
        yield _event("step", {"step": "expert_analysis", "message": "Running expert analysis..."})

        llm_provider = DayueAIProvider()
        phase1_result = await _run_phase1(task_id, requirement_text, project_name, compiled, llm_provider)
        code_artifact = phase1_result.get("code_artifact", {})
        module_specs = phase1_result.get("module_specs", {})

        code_summary = {}
        for mod, code in code_artifact.items():
            code_summary[mod] = {"lines": code.count(chr(10)) + 1 if code else 0, "valid": bool(code)}

        yield _event("phase1_complete", {
            "modules_generated": code_summary,
            "total_lines": sum(v["lines"] for v in code_summary.values()),
        })

        await _update_task(task_id, progress=0.6, current_step="code_review")
        yield _event("phase", {"phase": "phase2", "status": "started"})
        yield _event("step", {"step": "code_review", "message": "Running code review..."})

        phase2_result = await _run_phase2(task_id, code_artifact, module_specs, compiled, llm_provider)

        await _update_task(task_id, progress=1.0, current_step="completed")

        final_result = {
            "phase1": {"module_specs": module_specs, "code_summary": code_summary},
            "phase2": phase2_result,
            "code_artifact": code_artifact,
        }
        await _update_task(task_id, status="completed", progress=1.0, result=final_result)

        yield _event("complete", {
            "quality_score": phase2_result["quality_score"],
            "passed": phase2_result["passed"],
            "total_lines": sum(v["lines"] for v in code_summary.values()),
        })

    except Exception as exc:
        logger.exception("Pipeline stream failed")
        await _update_task(task_id, status="failed", error=str(exc))
        yield _event("error", {"error": str(exc)})

# ===========================================================================
# 3. GET /pipeline/status/{task_id}
# ===========================================================================

@app.get("/pipeline/status/{task_id}")
async def pipeline_status(task_id: str):
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return JSONResponse(content={
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "current_step": task.get("current_step"),
        "result": task.get("result"),
        "error": task.get("error"),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    })

# ===========================================================================
# 4. GET /agents
# ===========================================================================

@app.get("/agents")
async def list_agents():
    agents_config = _load_agents_config()
    agent_list = _build_agent_list(agents_config)
    return JSONResponse(content={"agents": agent_list, "total": len(agent_list)})

# ===========================================================================
# 5. POST /agent/{module_name}/direct
# ===========================================================================

@app.post("/agent/{module_name}/direct")
async def agent_direct(module_name: str, body: Dict[str, Any]):
    from agents.experts import create_expert_agents, ExpertInput, ReviewInput
    try:
        from tools.agent.claude_code import DayueAIProvider
        llm_provider = DayueAIProvider()
    except (ValueError, ImportError) as e:
        raise HTTPException(status_code=503, detail=f"LLM provider unavailable: {e}")

    resolved = _resolve_module_name(module_name)
    experts = create_expert_agents(
        os.path.join(_PROJECT_ROOT, "config", "schemas"),
        llm_provider=llm_provider,
    )

    mode = body.get("mode", "analysis") if isinstance(body, dict) else "analysis"
    expert = experts.get(resolved)

    if not expert:
        raise HTTPException(
            status_code=404,
            detail=f"No expert agent for module: {module_name} (resolved: {resolved})",
        )

    if mode == "review":
        code_snippet = body.get("code_snippet", "") if isinstance(body, dict) else ""
        review_input = ReviewInput(
            module_name=resolved,
            code_snippet=code_snippet,
        )
        review_output = expert.review(review_input)
        return JSONResponse(content={
            "success": True,
            "module_name": resolved,
            "mode": "review",
            "result": {
                "verdict": review_output.verdict,
                "issues": review_output.issues,
                "metrics": review_output.metrics,
            },
        })
    else:
        requirement = body.get("requirement", "") if isinstance(body, dict) else ""
        constraints = body.get("constraints", []) if isinstance(body, dict) else []
        expert_input = ExpertInput(
            module_name=resolved,
            requirement=requirement,
            constraints=constraints,
        )
        output = expert.process(expert_input)
        return JSONResponse(content={
            "success": True,
            "module_name": resolved,
            "mode": "analysis",
            "result": {
                "components": output.components,
                "interfaces": output.interfaces,
                "acceptance_criteria": output.acceptance_criteria,
                "state_machine": output.state_machine,
                "confidence": output.confidence,
                "reasoning": output.reasoning,
            },
        })


# ─── 注册子路由 ─────────────────────────────────────────────────────

def register_routers(app):
    """注册所有子路由"""
    try:
        from server.routes.rag import router as rag_router
        app.include_router(rag_router)
        logger.info("Registered RAG router")
    except Exception as e:
        logger.warning("RAG router not available: %s", e)

    try:
        from server.routes.mcp import router as mcp_router
        app.include_router(mcp_router)
        logger.info("Registered MCP router")
    except Exception as e:
        logger.warning("MCP router not available: %s", e)

    try:
        from server.routes.workflow import router as workflow_router
        app.include_router(workflow_router)
        logger.info("Registered Workflow router")
    except Exception as e:
        logger.warning("Workflow router not available: %s", e)


register_routers(app)
