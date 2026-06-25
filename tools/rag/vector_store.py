# tools/rag/vector_store.py

"""
pgvector 向量存储。

封装 PostgreSQL + pgvector 的文档块 CRUD 和相似度检索。
依赖 AsyncPostgresStore 或直接使用 asyncpg 连接。

用法:
    store = VectorStore(dsn="postgresql://...")
    await store.init()
    await store.upsert(chunks, embeddings)
    results = await store.search(query_embedding, top_k=5)
"""

import json
import logging
from typing import Any, Dict, List, Optional

from tools.rag.text_splitter import DocumentChunk

logger = logging.getLogger(__name__)

try:
    import asyncpg
    _ASYNC_PG_AVAILABLE = True
except ImportError:
    _ASYNC_PG_AVAILABLE = False


class VectorStore:
    """pgvector 向量存储"""

    def __init__(self, dsn: str = None):
        self._dsn = dsn
        self._conn: Optional[Any] = None

    async def init(self) -> None:
        """初始化连接和表"""
        if not _ASYNC_PG_AVAILABLE:
            raise ImportError("pip install asyncpg")
        if not self._dsn:
            raise ValueError("DATABASE_URL not set")
        self._conn = await asyncpg.connect(self._dsn)
        await self._conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                embedding vector(1536),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id
            ON document_chunks (document_id)
        """)
        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON document_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)

    async def upsert(self, chunks: List[DocumentChunk],
                     embeddings: List[List[float]]) -> int:
        """批量插入文档块和向量，返回插入数量"""
        count = 0
        for chunk, embedding in zip(chunks, embeddings):
            await self._conn.execute("""
                INSERT INTO document_chunks (document_id, content, embedding, metadata)
                VALUES ($1, $2, $3, $4)
            """, chunk.document_id, chunk.content, embedding,
                json.dumps(chunk.metadata))
            count += 1
        return count

    async def search(self, query_embedding: List[float],
                     top_k: int = 10,
                     filters: Dict = None,
                     document_id: str = None) -> List[DocumentChunk]:
        """余弦相似度检索"""
        params = [query_embedding, top_k]
        where_clauses = []

        if document_id:
            params.append(document_id)
            where_clauses.append(f"document_id = ${len(params)}")

        if filters:
            for key, val in filters.items():
                params.append(val)
                where_clauses.append(f"metadata->>'{key}' = ${len(params)}")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        rows = await self._conn.fetch(f"""
            SELECT id, document_id, content, metadata, embedding,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM document_chunks
            {where_sql}
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """, *params)

        return [
            DocumentChunk(
                content=row["content"],
                metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
                document_id=str(row["document_id"]),
                chunk_index=0,
                source="",
                position=0,
            )
            for row in rows
        ]

    async def delete(self, document_id: str) -> bool:
        """删除指定文档的所有块"""
        result = await self._conn.execute(
            "DELETE FROM document_chunks WHERE document_id = $1", document_id
        )
        return "DELETE" in result

    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """列出去重文档列表"""
        rows = await self._conn.fetch("""
            SELECT DISTINCT document_id,
                   MIN(created_at) AS created_at,
                   COUNT(*) AS chunk_count
            FROM document_chunks
            GROUP BY document_id
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        return [dict(row) for row in rows]

    async def count(self) -> int:
        """返回文档块总数"""
        row = await self._conn.fetchrow("SELECT COUNT(*) AS cnt FROM document_chunks")
        return row["cnt"]

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
