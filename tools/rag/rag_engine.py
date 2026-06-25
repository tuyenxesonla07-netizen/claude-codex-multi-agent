# tools/rag/rag_engine.py

"""
RAG 引擎：编排完整的 RAG 流程。

入库：文档 → 加载 → 分块 → 向量化 → 存储
查询：问题 → 向量化 → 检索 → 上下文注入 → LLM 生成

用法:
    engine = RAGEngine(loader, splitter, embedder, vector_store)
    doc_id = await engine.ingest_file("test.pdf")
    result = await engine.query("问题是什么？", top_k=5)
    print(result.answer, result.sources)
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from tools.rag.document_loader import DocumentLoader
from tools.rag.text_splitter import TextSplitter, DocumentChunk
from tools.rag.embedder import Embedder
from tools.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """RAG 查询结果"""
    answer: str                              # LLM 生成的回答
    sources: List[DocumentChunk]             # 引用的文档块
    context: str                             # 注入上下文的完整 prompt
    query_embedding: List[float] = field(default_factory=list)


class RAGEngine:
    """RAG 引擎：入库 + 检索增强生成"""

    def __init__(self, loader: DocumentLoader, splitter: TextSplitter,
                 embedder: Embedder, vector_store: VectorStore):
        self.loader = loader
        self.splitter = splitter
        self.embedder = embedder
        self.vector_store = vector_store

    async def ingest_file(self, path: str, metadata: dict = None) -> str:
        """文档入库，返回 document_id"""
        doc = await self.loader.load_file(path)
        doc_id = str(uuid.uuid4())
        chunks = self.splitter.split_text(
            doc.content,
            metadata={**doc.metadata, **(metadata or {})},
            document_id=doc_id,
            source=doc.source,
        )
        if not chunks:
            logger.warning("[RAGEngine] No chunks produced for %s", path)
            return doc_id

        texts = [c.content for c in chunks]
        embeddings = await self.embedder.embed_texts(texts)
        await self.vector_store.upsert(chunks, embeddings)
        logger.info("[RAGEngine] Ingested %d chunks from %s", len(chunks), path)
        return doc_id

    async def ingest_url(self, url: str, metadata: dict = None) -> str:
        """网页入库，返回 document_id"""
        doc = await self.loader.load_url(url)
        doc_id = str(uuid.uuid4())
        chunks = self.splitter.split_text(
            doc.content,
            metadata={**doc.metadata, **(metadata or {})},
            document_id=doc_id,
            source=url,
        )
        if not chunks:
            return doc_id

        texts = [c.content for c in chunks]
        embeddings = await self.embedder.embed_texts(texts)
        await self.vector_store.upsert(chunks, embeddings)
        logger.info("[RAGEngine] Ingested %d chunks from %s", len(chunks), url)
        return doc_id

    async def ingest_text(self, text: str, source: str = "inline",
                          metadata: dict = None) -> str:
        """纯文本入库，返回 document_id"""
        doc_id = str(uuid.uuid4())
        chunks = self.splitter.split_text(
            text,
            metadata=metadata or {},
            document_id=doc_id,
            source=source,
        )
        if not chunks:
            return doc_id

        texts = [c.content for c in chunks]
        embeddings = await self.embedder.embed_texts(texts)
        await self.vector_store.upsert(chunks, embeddings)
        return doc_id

    async def query(self, question: str, top_k: int = 5,
                    provider=None) -> RAGResult:
        """检索增强生成"""
        # 1. 向量化查询
        query_embedding = await self.embedder.embed_query(question)

        # 2. 相似度检索
        sources = await self.vector_store.search(query_embedding, top_k=top_k)

        # 3. 组装上下文
        context_parts = []
        for i, chunk in enumerate(sources, 1):
            context_parts.append(f"[{i}] {chunk.content}")
        context = "\n\n".join(context_parts)

        # 4. 构建 prompt
        prompt = f"""基于以下参考资料回答问题。如果参考资料不包含相关信息，请明确说明。

参考资料:
{context}

问题: {question}

回答:"""

        # 5. LLM 生成回答
        answer = ""
        if provider:
            response = provider.complete(prompt=prompt, temperature=0.3)
            answer = response.content if response.success else "生成回答失败"
        else:
            answer = "（未配置 LLM Provider，仅返回检索结果）\n\n" + context

        return RAGResult(
            answer=answer,
            sources=sources,
            context=prompt,
            query_embedding=query_embedding,
        )

    async def stats(self) -> dict:
        """返回知识库统计"""
        total_chunks = await self.vector_store.count()
        documents = await self.vector_store.list_documents(limit=1)
        return {
            "total_chunks": total_chunks,
            "total_documents": len(documents),
        }
