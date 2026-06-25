# Claude-Codex Multi-Agent - Option D Implementation
# Schema-First Compilation Architecture

import json
import logging
import os

logger = logging.getLogger(__name__)

from tools.llm import create_llm_provider
from tools.compiler import (
    PipelineCompiler,
    ContextDeriver,
    PromptTemplateGenerator,
    FixInstructionDeriver,
    DependencyGraphBuilder,
    QualityGateGenerator,
)
from tools.stores import (
    RequirementStore,
    ModuleRequirement,
    InterfaceStore,
    InterfaceDef,
    SpecStore,
    ModuleSpec,
)
from tools.messaging import MessageBus, Message, Topic
from tools.quality import QualityEvaluator, ReviewResult, ConvergenceDetector
from agents.supervisor import CodexSupervisor, Requirement, ModuleTask
from agents.experts import (
    ExpertAgent,
    create_expert_agents,
    ExpertInput,
    ExpertOutput,
    ReviewInput,
    ReviewOutput,
)


class ClaudeCodexMultiAgent:
    def __init__(self, config_dir="config", llm_backend="mock", llm_api_key=None, llm_base_url=None):
        self.requirement_store = RequirementStore()
        self.interface_store = InterfaceStore()
        self.spec_store = SpecStore()
        self.message_bus = MessageBus()

        # LLM Provider (mock 默认, anthropic/openai-compatible 可选)
        if llm_backend == "openai-compatible":
            self.llm_provider = create_llm_provider(
                backend=llm_backend, api_key=llm_api_key, base_url=llm_base_url
            )
        else:
            self.llm_provider = create_llm_provider(
                backend=llm_backend, api_key=llm_api_key
            )

        self.compiler = PipelineCompiler(
            requirement_store=self.requirement_store,
            interface_store=self.interface_store,
            spec_store=self.spec_store,
            message_bus=self.message_bus,
        )

        self.quality_evaluator = QualityEvaluator(message_bus=self.message_bus)

        self.agents_config = self._load_agents_config(config_dir)
        self.supervisor = CodexSupervisor(self.agents_config)
        self.expert_agents = create_expert_agents(
            os.path.join(config_dir, "schemas"),
            agents_config=self.agents_config,
            llm_provider=self.llm_provider,
        )

    def compile_pipeline(self, module_schemas, input_schemas=None):
        return self.compiler.compile(module_schemas, input_schemas=input_schemas)

    def run_phase1(self, user_requirement):
        requirement = self.supervisor.parse_requirement(user_requirement)
        input_schemas, output_schemas = self._load_schemas()
        compiled = self.compile_pipeline(output_schemas, input_schemas=input_schemas)

        module_specs = {}
        for module_name in compiled.implementation_order:
            strategy = compiled.context_strategies.get(module_name)
            input_schema = input_schemas.get(module_name, {})
            expert_input = self._build_expert_input(
                module_name, input_schema, strategy, compiled
            )
            expert = self.expert_agents.get(module_name)
            if expert:
                output = expert.process(expert_input)
                module_specs[module_name] = output
                self.spec_store.put(
                    module_name,
                    ModuleSpec(
                        module_name=module_name,
                        components=[
                            {"name": c.get("name", "Unknown"), "type": c.get("type", "service"),
                             "description": c.get("description", "")}
                            for c in output.components
                        ],
                        interfaces=[
                            {"name": i.get("name", "unknown"), "method": i.get("method", "POST"),
                             "path": i.get("path", "/")}
                            for i in output.interfaces
                        ],
                        acceptance_criteria=output.acceptance_criteria,
                        state_machine=output.state_machine,
                        confidence=output.confidence,
                    ),
                )

        # Generate real code using the supervisor
        code_artifact = {}
        for module_name, spec in module_specs.items():
            code = self.supervisor.generate_code(
                module_spec=spec.__dict__ if hasattr(spec, "__dict__") else spec,
                llm_provider=self.llm_provider,
                module_name=module_name,
            )
            if code:
                code_artifact[module_name] = code

        # Print code generation stats
        total_lines = sum(c.count(chr(10)) + 1 for c in code_artifact.values())
        print(f"[MultiAgent] Generated {len(code_artifact)} modules, {total_lines} total lines")
        for mod, code in code_artifact.items():
            print(f"  {mod}: {code.count(chr(10)) + 1} lines")

        return {
            "compiled": compiled,
            "module_specs": module_specs,
            "prompt": compiled.prompt_template.template_str,
            "code_artifact": code_artifact,
        }

    def run_phase2(self, code_artifact, compiled_pipeline=None):
        if compiled_pipeline is None:
            input_schemas, output_schemas = self._load_schemas()
            compiled_pipeline = self.compile_pipeline(
                output_schemas, input_schemas=input_schemas
            )

        detector = ConvergenceDetector(max_iterations=3)
        iteration = 0

        while True:
            review_results = self._simulate_reviews(
                compiled_pipeline.implementation_order
            )
            report = self.quality_evaluator.evaluate(
                review_results, iteration=iteration
            )
            should_continue, reason = detector.should_continue(
                iteration=iteration,
                quality_score=report.quality_score,
                has_critical=report.has_critical,
            )
            if not should_continue:
                break
            iteration += 1

        return {
            "passed": report.passed,
            "quality_score": report.quality_score,
            "iterations": iteration,
            "convergence_status": reason,
        }

    def _load_agents_config(self, config_dir):
        try:
            import yaml
        except ImportError:
            logger.warning("pyyaml not installed, agents config will be empty. Install with: pip install pyyaml")
            return {}
        agents_path = os.path.join(config_dir, "agents.yaml")
        if os.path.exists(agents_path):
            with open(agents_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                yaml_lines = []
                in_yaml = False
                for line in lines:
                    if line.strip().startswith("```yaml"):
                        in_yaml = True
                        continue
                    if line.strip() == "```" and in_yaml:
                        break
                    if in_yaml:
                        yaml_lines.append(line)
                return yaml.safe_load("\n".join(yaml_lines)) if yaml_lines else {}
        return {}

    def _load_schemas(self):
        schemas_dir = os.path.join(os.path.dirname(__file__), "config", "schemas")
        input_schemas = {}
        output_schemas = {}
        if os.path.exists(schemas_dir):
            for filename in os.listdir(schemas_dir):
                path = os.path.join(schemas_dir, filename)
                with open(path, encoding="utf-8") as f:
                    schema = json.load(f)
                if filename.endswith("_input.json"):
                    module = filename.replace("_input.json", "")
                    input_schemas[module] = schema
                elif filename.endswith("_output.json"):
                    module = filename.replace("_output.json", "")
                    output_schemas[module] = schema
        return input_schemas, output_schemas

    def _build_expert_input(self, module_name, input_schema, strategy, compiled):
        requirement_text = input_schema.get("description", module_name)
        constraints = []
        dependency_interfaces = {}
        if input_schema.get("properties"):
            props = input_schema["properties"]
            if "constraints" in props:
                constraints = props["constraints"].get("default", [])
            if "security_requirements" in props:
                constraints.extend(props["security_requirements"].get("default", []))
            if "compliance_requirements" in props:
                constraints.extend(props["compliance_requirements"].get("default", []))
        if strategy and strategy.needs_dependency_interfaces:
            deps = strategy.depends_on
            for dep in deps:
                dep_interfaces = self.interface_store.get_for_injection(dep)
                if dep_interfaces:
                    dependency_interfaces[dep] = dep_interfaces
        return ExpertInput(
            module_name=module_name,
            requirement=requirement_text,
            constraints=constraints,
            dependency_interfaces=dependency_interfaces,
            global_constraints={
                "language": "Python 3.12",
                "framework": "FastAPI",
                "coding_style": "Google Python Style Guide",
            },
        )

    def _simulate_reviews(self, module_order):
        _rng = __import__("random").Random(42)
        results = []
        for module_name in module_order:
            expert = self.expert_agents.get(module_name)
            if expert:
                review = expert.review(ReviewInput(
                    module_name=module_name,
                    code_snippet="# simulated code",
                ))
                results.append(
                    ReviewResult(
                        module=module_name,
                        verdict=review.verdict,
                        issues=review.issues,
                        confidence=_rng.uniform(0.7, 0.95),
                    )
                )
            else:
                results.append(ReviewResult(module=module_name, verdict="pass"))
        return results

    def _generate_fix_instructions(self, review_results, compiled_pipeline):
        all_instructions = []
        for result in review_results:
            if result.verdict != "pass":
                module_name = result.module
                fix_template = compiled_pipeline.fix_templates.get(module_name)
                if fix_template and result.issues:
                    instructions = fix_template.generate_fix_instructions(
                        result.issues
                    )
                    all_instructions.extend(instructions)
        return all_instructions


__all__ = [
    "ClaudeCodexMultiAgent",
    "PipelineCompiler",
    "ContextDeriver",
    "PromptTemplateGenerator",
    "FixInstructionDeriver",
    "DependencyGraphBuilder",
    "QualityGateGenerator",
    "RequirementStore",
    "InterfaceStore",
    "SpecStore",
    "MessageBus",
    "Message",
    "Topic",
    "QualityEvaluator",
    "ReviewResult",
    "ConvergenceDetector",
    "ExpertAgent",
    "create_expert_agents",
    "ExpertInput",
    "ExpertOutput",
    "ReviewInput",
    "ReviewOutput",
]


