# tools/agent/claude_code.py

"""
Claude Code Executor — 真实 LLM 代码生成器

通过 dayueai.fun API 调用 Claude Opus 4.7 生成可执行 Python 代码。
使用 urllib.request（无需安装额外包）。
"""

import ast
import json
import logging
import os
import urllib.request
import urllib.error
from typing import Optional

from tools.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# ============================================================
# API 配置 — 优先从环境变量读取，fallback 到默认值
# ============================================================
API_BASE_URL = os.environ.get("LLM_API_BASE_URL", "https://www.dayueai.fun")
API_KEY = os.environ.get("LLM_API_KEY", "")
API_MODEL = os.environ.get("LLM_API_MODEL", "claude-opus-4-7")


class DayueAIProvider(LLMProvider):
    """
    dayueai.fun 的 OpenAI-compatible LLM Provider

    认证方式: Header "x-api-key"
    """

    def __init__(
        self,
        api_key: str = API_KEY,
        base_url: str = API_BASE_URL,
        model: str = API_MODEL,
        max_tokens: int = 8192,
    ):
        self._api_key = api_key
        if not self._api_key:
            raise ValueError(
                "API key is required. Set LLM_API_KEY environment variable "
                "or pass api_key parameter directly."
            )
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._default_max_tokens = max_tokens

    def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        output_format: str = "text",
        max_tokens: int = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        调用 dayueai.fun Chat Completions API

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            output_format: 输出格式 ("text" | "json")
            max_tokens: 最大 token 数
            temperature: 温度

        Returns:
            LLMResponse
        """
        max_tokens = max_tokens or self._default_max_tokens

        # 构建 messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 构建请求体
        body = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        # JSON 输出模式
        if output_format == "json":
            body["response_format"] = {"type": "json_object"}

        url = f"{self._base_url}/v1/chat/completions"
        data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)

            choices = result.get("choices", [])
            if not choices:
                return LLMResponse(
                    content="",
                    success=False,
                    error="API 返回无 choices",
                    model=self._model,
                )

            content = choices[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)

            # 解析 JSON
            parsed = None
            if output_format == "json":
                try:
                    clean = content.strip()
                    # 清理可能的 markdown 代码块
                    if clean.startswith("```"):
                        lines = clean.split("\n")
                        # 去掉第一行 (```json 或 ```) 和最后一行 (```)
                        if lines[-1].strip() == "```":
                            lines = lines[1:-1]
                        else:
                            lines = lines[1:]
                        clean = "\n".join(lines).strip()
                    parsed = json.loads(clean)
                except json.JSONDecodeError as e:
                    return LLMResponse(
                        content=content,
                        success=False,
                        error=f"JSON 解析失败: {e}",
                        model=self._model,
                        tokens_used=tokens_used,
                    )

            return LLMResponse(
                content=content,
                parsed=parsed,
                tokens_used=tokens_used,
                model=self._model,
                success=True,
            )

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception as read_err:
                logger.debug("Could not read error body: %s", read_err)
            return LLMResponse(
                content="",
                success=False,
                error=f"HTTP {e.code}: {error_body or e.reason}",
                model=self._model,
            )
        except urllib.error.URLError as e:
            return LLMResponse(
                content="",
                success=False,
                error=f"URL 错误: {e.reason}",
                model=self._model,
            )
        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                error=f"调用异常: {e}",
                model=self._model,
            )

    def get_name(self) -> str:
        return f"dayueai/{self._model}"


class ClaudeCodeExecutor:
    """
    Claude Code 执行器 — 调用真实 LLM 生成可执行 Python 代码

    用法:
        executor = ClaudeCodeExecutor()
        code = executor.generate_code(spec, module_name)
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Args:
            llm_provider: LLM Provider 实例。默认为 DayueAIProvider。
        """
        self.llm = llm_provider or DayueAIProvider()

    def _build_code_prompt(self, spec: dict, module_name: str) -> tuple:
        """
        构建代码生成的 system_prompt 和 user_prompt

        Args:
            spec: 模块规格（含 components, interfaces, acceptance_criteria 等）
            module_name: 模块名称

        Returns:
            (system_prompt, user_prompt)
        """
        components = spec.get("components", [])
        interfaces = spec.get("interfaces", [])
        acceptance_criteria = spec.get("acceptance_criteria", [])
        state_machine = spec.get("state_machine")

        # 构建组件描述
        spec_lines = []
        for comp in components:
            if isinstance(comp, dict):
                spec_lines.append(
                    f'- {comp.get("name", "?")} ({comp.get("type", "?")}): {comp.get("description", "")}'
                )
            else:
                spec_lines.append(f"- {comp}")

        # 构建接口描述
        interface_lines = []
        for iface in interfaces:
            if isinstance(iface, dict):
                interface_lines.append(
                    f'- {iface.get("name", "?")} {iface.get("method", "?")} {iface.get("path", "?")}'
                )
            else:
                interface_lines.append(f"- {iface}")

        # 构建验收标准
        criteria_lines = [f"- {c}" for c in acceptance_criteria]

        # 构建状态机描述
        sm_lines = []
        if state_machine:
            states = state_machine.get("states", [])
            transitions = state_machine.get("transitions", [])
            sm_lines.append(f"States: {', '.join(states)}")
            for t in transitions:
                sm_lines.append(f"  {t.get('from')} --[{t.get('trigger')}]--> {t.get('to')}")

        user_prompt_parts = [
            f"根据以下规格生成 Python 代码：",
            "",
            f"## 模块名称: {module_name}",
            "",
            "## 组件:",
        ] + spec_lines + [
            "",
            "## 接口:",
        ] + interface_lines + [
            "",
            "## 验收标准:",
        ] + criteria_lines

        if sm_lines:
            user_prompt_parts += ["", "## 状态机:"]
            user_prompt_parts += sm_lines

        user_prompt_parts += [
            "",
            "## 要求:",
            "- 可解析的 Python 3.10+ 代码",
            "- 包含 type hints 和 docstrings",
            "- 使用 FastAPI / pydantic (如适用)",
            "- 实现上述所有组件和接口",
            "- 包含合理的错误处理",
            "- 只输出代码，不要 markdown 代码块",
        ]

        user_prompt = "\n".join(user_prompt_parts)

        system_prompt = (
            "You are an expert Python code generator. "
            "Generate complete, runnable, production-ready Python code. "
            "Output ONLY raw Python code — no markdown, no explanation, no code fences."
        )

        return system_prompt, user_prompt

    def generate_code(self, spec: dict, module_name: str) -> str:
        """
        生成可执行 Python 代码

        Args:
            spec: 模块规格字典
            module_name: 模块名称

        Returns:
            生成的 Python 代码字符串。失败时返回空字符串。
        """
        system_prompt, user_prompt = self._build_code_prompt(spec, module_name)

        logger.info("[ClaudeCode] 正在为模块 '%s' 生成代码...", module_name)

        response = self.llm.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            output_format="text",
            max_tokens=8192,
            temperature=0.2,
        )

        if not response.success or not response.content:
            logger.warning(
                "[ClaudeCode] 模块 '%s' LLM 调用失败: %s",
                module_name,
                response.error,
            )
            return ""

        code = response.content.strip()

        # 清理可能的 markdown 代码块
        if code.startswith("```"):
            parts = code.split("\n", 1)
            if len(parts) > 1:
                code = parts[1]
            else:
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()

        # 验证代码可解析
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.warning(
                "[ClaudeCode] 模块 '%s' AST 验证失败: %s (response length: %d)",
                module_name,
                e,
                len(response.content or ""),
            )
            return ""

        lines = code.count("\n") + 1
        logger.info(
            "[ClaudeCode] 模块 '%s' 生成成功: %d 行代码",
            module_name,
            lines,
        )
        return code

    def _execute_llm(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """
        直接调用 LLM（内部方法，供高级用法）

        Args:
            prompt: 用户提示
            system_prompt: 系统提示

        Returns:
            LLMResponse
        """
        return self.llm.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            output_format="text",
            max_tokens=8192,
            temperature=0.2,
        )
