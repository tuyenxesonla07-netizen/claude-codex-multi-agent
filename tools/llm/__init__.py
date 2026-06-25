# tools/llm/__init__.py

"""
LLM Provider 抽象层，支持多种 LLM 后端。

用法:
    from tools.llm import create_llm_provider

    # 默认: Mock (无需 API key)
    provider = create_llm_provider()

    # Anthropic (需要 ANTHROPIC_API_KEY)
    provider = create_llm_provider("anthropic", api_key="sk-...")

    # OpenAI-compatible (自定义 base_url)
    provider = create_llm_provider("openai-compatible", api_key="sk-...", base_url="https://fumin.ai")

    # DeepSeek
    provider = create_llm_provider("deepseek", api_key="sk-...")

    # Qwen (通义千问)
    provider = create_llm_provider("qwen", api_key="sk-...")

    # Gemini
    provider = create_llm_provider("gemini", api_key="...")

    # MiniMax
    provider = create_llm_provider("minimax", api_key="...")

    # GLM (智谱)
    provider = create_llm_provider("glm", api_key="...")

    # 调用
    result = provider.complete("分析这个需求..", output_format="json")
"""

from tools.llm.base import LLMProvider, LLMResponse
from tools.llm.mock import MockLLMProvider

# Optional providers
try:
    from tools.llm.anthropic import AnthropicClaudeProvider
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

try:
    from tools.llm.deepseek import DeepSeekProvider
    _DEEPSEEK_AVAILABLE = True
except ImportError:
    _DEEPSEEK_AVAILABLE = False

try:
    from tools.llm.qwen import QwenProvider
    _QWEN_AVAILABLE = True
except ImportError:
    _QWEN_AVAILABLE = False

try:
    from tools.llm.gemini import GeminiProvider
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

try:
    from tools.llm.minimax import MiniMaxProvider
    _MINIMAX_AVAILABLE = True
except ImportError:
    _MINIMAX_AVAILABLE = False

try:
    from tools.llm.glm import GLMProvider
    _GLM_AVAILABLE = True
except ImportError:
    _GLM_AVAILABLE = False


def create_llm_provider(
    backend: str = "mock",
    api_key: str = None,
    model: str = None,
    **kwargs,
) -> LLMProvider:
    if backend == "mock":
        return MockLLMProvider(**kwargs)

    if backend == "anthropic":
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Run: pip install anthropic --break-system-packages"
            )
        return AnthropicClaudeProvider(api_key=api_key, model=model, **kwargs)

    if backend == "deepseek":
        if not _DEEPSEEK_AVAILABLE:
            raise ImportError("pip install httpx")
        return DeepSeekProvider(api_key=api_key, model=model or "deepseek-chat", **kwargs)

    if backend == "qwen":
        if not _QWEN_AVAILABLE:
            raise ImportError("pip install httpx")
        return QwenProvider(api_key=api_key, model=model or "qwen-turbo", **kwargs)

    if backend == "gemini":
        if not _GEMINI_AVAILABLE:
            raise ImportError("pip install httpx")
        return GeminiProvider(api_key=api_key, model=model or "gemini-1.5-flash", **kwargs)

    if backend == "minimax":
        if not _MINIMAX_AVAILABLE:
            raise ImportError("pip install httpx")
        return MiniMaxProvider(api_key=api_key, model=model or "abab6.5s-chat", **kwargs)

    if backend == "glm":
        if not _GLM_AVAILABLE:
            raise ImportError("pip install httpx")
        return GLMProvider(api_key=api_key, model=model or "glm-4-flash", **kwargs)

    if backend == "openai-compatible":
        from tools.llm.openai_compat import OpenAICompatibleProvider
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=kwargs.get("base_url"),
            model=model or "claude-opus-4-7",
        )

    raise ValueError(f"Unknown LLM backend: {backend}")


__all__ = [
    "LLMProvider",
    "LLMResponse",
    "MockLLMProvider",
    "create_llm_provider",
]

if _ANTHROPIC_AVAILABLE:
    __all__.append("AnthropicClaudeProvider")
if _DEEPSEEK_AVAILABLE:
    __all__.append("DeepSeekProvider")
if _QWEN_AVAILABLE:
    __all__.append("QwenProvider")
if _GEMINI_AVAILABLE:
    __all__.append("GeminiProvider")
if _MINIMAX_AVAILABLE:
    __all__.append("MiniMaxProvider")
if _GLM_AVAILABLE:
    __all__.append("GLMProvider")
