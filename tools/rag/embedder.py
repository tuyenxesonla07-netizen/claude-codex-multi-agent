# tools/rag/embedder.py

"""
文本向量化。

支持多种 embedding 后端：
1. OpenAI embeddings API（text-embedding-3-small 等）
2. sentence-transformers 本地模型
3. 任意 LLM Provider 的 complete() 方法（fallback）

用法:
    embedder = Embedder()  # 默认 OpenAI
    vectors = await embedder.embed_texts(["文本1", "文本2"])
"""

import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class Embedder:
    """文本向量化器"""

    def __init__(self, provider=None, model: str = "text-embedding-3-small",
                 base_url: str = None, api_key: str = None):
        """
        Args:
            provider: LLMProvider 实例（用于 fallback 或 OpenAI embeddings）
            model: embedding 模型名
            base_url: OpenAI-compatible embedding endpoint
            api_key: API Key
        """
        self.provider = provider
        self.model = model
        self._base_url = base_url
        self._api_key = api_key
        self._local_model = None

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本"""
        if not texts:
            return []

        # 尝试本地 sentence-transformers
        if self._try_local():
            return self._embed_local(texts)

        # 尝试 OpenAI embeddings API
        if self._base_url:
            return await self._embed_via_api(texts)

        # Fallback: 使用 LLM Provider 的 complete 方法
        if self.provider:
            return await self._embed_via_llm(texts)

        raise RuntimeError(
            "No embedding method available. "
            "Install sentence-transformers or set OPENAI_API_KEY."
        )

    async def embed_query(self, query: str) -> List[float]:
        """向量化单条查询"""
        results = await self.embed_texts([query])
        return results[0] if results else []

    def _try_local(self) -> bool:
        """尝试加载本地 sentence-transformers 模型"""
        if self._local_model is not None:
            return True
        try:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[Embedder] Using local sentence-transformers model")
            return True
        except ImportError:
            return False

    def _embed_local(self, texts: List[str]]) -> List[List[float]]:
        """使用本地模型向量化"""
        embeddings = self._local_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    async def _embed_via_api(self, texts: List[str]) -> List[List[float]]:
        """通过 OpenAI embeddings API 向量化"""
        try:
            import httpx
        except ImportError:
            raise ImportError("pip install httpx")

        base = self._base_url or "https://api.openai.com/v1"
        key = self._api_key or ""

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base}/embeddings",
                json={"model": self.model, "input": texts},
                headers={"Authorization": f"Bearer {key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]

    async def _embed_via_llm(self, texts: List[str]]) -> List[List[float]]:
        """通过 LLM Provider 的 complete 方法获取 embedding（fallback）"""
        results = []
        for text in texts:
            response = self.provider.complete(
                prompt=f"Generate a 384-dimensional embedding vector for: {text[:200]}",
                output_format="json",
            )
            if response.success and response.parsed:
                results.append(response.parsed)
            else:
                # 返回零向量作为 fallback
                results.append([0.0] * 384)
        return results
