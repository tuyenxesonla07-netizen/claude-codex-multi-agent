# tools/llm/gemini.py

"""
Google Gemini LLM Provider.

Requires: pip install httpx
Environment: GOOGLE_API_KEY
"""

import os
from typing import Optional

from tools.llm.base import LLMProvider, LLMResponse

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False


class GeminiProvider(LLMProvider):
    """Google Gemini API Provider (OpenAI-compatible via Google AI Studio)."""

    def __init__(self, api_key: str = None, base_url: str = None,
                 model: str = "gemini-1.5-flash", max_tokens: int = 8192):
        if not _HTTPX_AVAILABLE:
            raise ImportError("pip install httpx")
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not self._api_key:
            raise ValueError("Set GOOGLE_API_KEY or pass api_key")
        self._base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self._model = model
        self._default_max_tokens = max_tokens
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
        self._api_key_query = self._api_key  # Gemini uses query param auth

    def complete(self, prompt: str, system_prompt: str = "",
                 output_format: str = "text", max_tokens: int = None,
                 temperature: float = 0.7) -> LLMResponse:
        max_tokens = max_tokens or self._default_max_tokens
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        body = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if output_format == "json":
            body["response_format"] = {"type": "json_object"}
        try:
            url = f"/openai/models/{self._model}:generateContent?key={self._api_key_query}"
            resp = self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return LLMResponse(content="", success=False, error="No choices", model=self._model)
            content = choices[0].get("message", {}).get("content", "")
            usage = data.get("usageMetadata", {})
            total = usage.get("totalTokenCount", 0)
            return LLMResponse(content=content, parsed=None,
                               tokens_used=total, model=self._model, success=True)
        except Exception as e:
            return LLMResponse(content="", success=False, error=str(e), model=self._model)

    def get_name(self) -> str:
        return f"gemini/{self._model}"

    def close(self):
        self._client.close()
