# tools/rag/context_injector.py

"""
RAG 上下文注入器。

在 Agent prompt 中自动注入 RAG 检索结果，使专家 Agent 能引用知识库内容。

用法:
    injector = RAGContextInjector(rag_engine)
    enhanced_prompt = await injector.inject(original_prompt, agent_id="expert_auth")
"""

import logging
from typing import Optional

from tools.rag.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class RAGContextInjector:
    """RAG 上下文注入器"""

    def __init__(self, rag_engine: RAGEngine, top_k: int = 3):
        self.rag_engine = rag_engine
        self.top_k = top_k

    async def inject(self, prompt: str, agent_id: str = "",
                     query_hint: str = None) -> str:
        """
        在 prompt 中注入 RAG 检索结果。

        Args:
            prompt: 原始 prompt
            agent_id: Agent 标识（用于日志）
            query_hint: 查询提示（默认从 prompt 最后一行提取）

        Returns:
            增强后的 prompt（包含检索到的上下文）
        """
        try:
            # 提取查询
            query = query_hint or self._extract_query(prompt)
            if not query:
                return prompt

            # 检索
            result = await self.rag_engine.query(query, top_k=self.top_k)
            if not result.sources:
                return prompt

            # 格式化上下文
            context_block = self._format_context(result.sources)
            enhanced = f"{prompt}\n\n## 知识库参考资料\n{context_block}\n"
            logger.info("[RAGInjector] Injected %d sources for %s",
                        len(result.sources), agent_id)
            return enhanced

        except Exception as e:
            logger.warning("[RAGInjector] Failed to inject context: %s", e)
            return prompt

    def _extract_query(self, prompt: str) -> str:
        """从 prompt 中提取查询关键词"""
        lines = prompt.strip().split("\n")
        # 取最后一行非空内容作为查询
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                return line[:200]
        return prompt[:200]

    def _format_context(self, sources) -> str:
        """格式化检索结果为上下文文本"""
        parts = []
        for i, chunk in enumerate(sources, 1):
            source = chunk.metadata.get("source", chunk.source or "unknown")
            parts.append(f"[{i}] (来源: {source})\n{chunk.content}")
        return "\n\n".join(parts)
