# tools/llm/openai_compat.py

"""
OpenAI-compatible LLM Provider.

Requires: pip install httpx
Optional dependency — only needed when using backend="openai-compatible".
"""

from typing import Optional

from tools.llm.base import LLMProvider, LLMResponse

# Optional dependency: httpx
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False


class OpenAICompatibleProvider(LLMProvider):
    """
    OpenAI-compatible API Provider.

    Usage:
        provider = OpenAICompatibleProvider(api_key="sk-...", base_url="https://...")
        response = provider.complete("Analyze this requirement..")

    Note: requires `httpx` package. Install with: pip install httpx
    """

    def __init__(self, api_key, base_url=None, model='claude-opus-4-7', max_tokens=8192):
        if not _HTTPX_AVAILABLE:
            raise ImportError(
                "httpx package is required for openai-compatible backend. "
                "Install with: pip install httpx"
            )
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._default_max_tokens = max_tokens
        self._client = httpx.Client(
            base_url=base_url or 'https://api.openai.com/v1',
            headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'},
            timeout=120.0,
        )

    def complete(self, prompt, system_prompt='', output_format='text', max_tokens=None, temperature=0.7):
        max_tokens = max_tokens or self._default_max_tokens
        messages = [{'role': 'user', 'content': prompt}]
        if system_prompt:
            messages = [{'role': 'system', 'content': system_prompt}] + messages
        body = {'model': self._model, 'max_tokens': max_tokens, 'temperature': temperature, 'messages': messages}
        try:
            resp = self._client.post('/chat/completions', json=body)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get('choices', [])
            if not choices:
                return LLMResponse(content='', success=False, error='No choices', model=self._model)
            content = choices[0].get('message', {}).get('content', '')
            usage = data.get('usage', {})
            return LLMResponse(content=content, parsed=None, tokens_used=usage.get('total_tokens', 0), model=self._model, success=True)
        except Exception as e:
            return LLMResponse(content='', success=False, error=str(e), model=self._model)

    def get_name(self):
        return 'openai-compatible/' + self._model

    def close(self):
        self._client.close()

    def __del__(self):
        try:
            self._client.close()
        except Exception as e:
            pass  # client may already be closed
