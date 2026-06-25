# tools/stores/postgres.py

"""
PostgreSQL + pgvector 异步存储层。

提供文档块（Document Chunk）的持久化存储与向量检索能力。
当 DATABASE_URL 未设置时，调用方应回退到 SQLite（StoreDatabase）。

用法:
    store = AsyncPostgresStore("postgresql://user:pass@localhost:5432/db")
    await store.init()
    await store.upsert_chunk("doc-1", "文本内容", [0.1, 0.2, ...], {"source": "test.pdf"})
    results = await store.similarity_search([0.1, 0.2, ...], top_k=5)
    await store.close()
"""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Optional dependency: asyncpg
try:
    import asyncpg
    _ASYNC_PG_AVAILABLE = True
except ImportError:
    _ASYNC_PG_AVAILABLE = False


@dataclass
class DocumentChunk:
    """单个文档块"""
    id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


class AsyncPostgresStore:
    """
    PostgreSQL + pgvector 异步存储。

    依赖: pip install asyncpg
    环境变量: DATABASE_URL (如 postgresql://user:pass@localhost:5432/claude_codex)
    """

    def __init__(self, dsn: str = None):
        self._dsn = dsn
        self._conn: Optional[Any] = None

    async def init(self) -> None:
        """初始化连接、建表、创建 pgvector 扩展"""
        if not _ASYNC_PG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for PostgreSQL support. "
                "Install with: pip install asyncpg"
            )
        if not self._dsn:
            raise ValueError("DATABASE_URL not set")
        self._conn = await asyncpg.connect(self._dsn)
        await self._create_tables()
        logger.info("[PostgresStore] Initialized database at %s", self._dsn)

    async def _create_tables(self) -> None:
        """创建 pgvector 扩展和表结构"""
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
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id
            ON document_chunks (document_id)
        """)
        # IVFFlat 索引（首次有数据后创建，这里先占位）
        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON document_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)

    async def upsert_chunk(self, document_id: str, content: str,
                           embedding: List[float], metadata: Dict = None) -> str:
        """插入或更新文档块，返回 chunk id"""
        row = await self._conn.fetchrow("""
            INSERT INTO document_chunks (document_id, content, embedding, metadata)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata
            RETURNING id
        """, document_id, content, embedding, json.dumps(metadata or {}))
        return str(row["id"])

    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> int:
        """批量插入文档块，返回插入数量"""
        count = 0
        for chunk in chunks:
            await self.upsert_chunk(
                chunk.document_id, chunk.content,
                chunk.embedding, chunk.metadata
            )
            count += 1
        return count

    async def similarity_search(self, query_embedding: List[float],
                                top_k: int = 10,
                                filters: Dict = None) -> List[DocumentChunk]:
        """余弦相似度检索"""
        # 构建 WHERE 条件
        where_clauses = []
        params = [query_embedding, top_k]
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
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                embedding=row["embedding"],
            )
            for row in rows
        ]

    async def delete_document(self, document_id: str) -> bool:
        """删除指定文档的所有块"""
        result = await self._conn.execute(
            "DELETE FROM document_chunks WHERE document_id = $1", document_id
        )
        return "DELETE" in result

    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """列出去重后的文档列表"""
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
        """关闭连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None
