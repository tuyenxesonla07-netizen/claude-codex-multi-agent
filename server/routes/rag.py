# server/routes/rag.py

"""
RAG 知识库 API 路由。

端点:
    POST /rag/documents/upload   — 上传文件入库
    POST /rag/documents/crawl    — 爬取网页入库
    POST /rag/documents/text     — 纯文本入库
    GET  /rag/documents          — 文档列表
    DELETE /rag/documents/{doc_id} — 删除文档
    POST /rag/query              — 知识库问答
    GET  /rag/stats              — 知识库统计
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


class CrawlRequest(BaseModel):
    url: str
    metadata: Optional[dict] = None


class TextIngestRequest(BaseModel):
    text: str
    source: str = "inline"
    metadata: Optional[dict] = None


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


def get_rag_engine(request):
    """从 app state 获取 RAG 引擎"""
    return request.app.state.rag_engine


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文件到知识库"""
    from tools.rag.document_loader import DocumentLoader
    from tools.rag.rag_engine import RAGEngine

    engine: RAGEngine = get_rag_engine(request=None)  # 由 app 注入
    loader = DocumentLoader()

    try:
        data = await file.read()
        doc = await loader.load_stream(data, file.filename)
        doc_id = await engine.ingest_text(
            doc.content, source=file.filename, metadata=doc.metadata
        )
        return {"document_id": doc_id, "filename": file.filename, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/crawl")
async def crawl_document(req: CrawlRequest, request):
    """爬取网页到知识库"""
    engine = get_rag_engine(request)
    try:
        doc_id = await engine.ingest_url(req.url, metadata=req.metadata)
        return {"document_id": doc_id, "url": req.url, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/text")
async def ingest_text(req: TextIngestRequest, request):
    """纯文本入库"""
    engine = get_rag_engine(request)
    try:
        doc_id = await engine.ingest_text(req.text, source=req.source, metadata=req.metadata)
        return {"document_id": doc_id, "source": req.source, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(request, limit: int = 100, offset: int = 0):
    """列出知识库文档"""
    engine = get_rag_engine(request)
    try:
        docs = await engine.vector_store.list_documents(limit=limit, offset=offset)
        return {"documents": docs, "total": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, request):
    """删除文档"""
    engine = get_rag_engine(request)
    try:
        deleted = await engine.vector_store.delete(doc_id)
        return {"deleted": deleted, "document_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def rag_query(req: QueryRequest, request):
    """知识库问答"""
    engine = get_rag_engine(request)
    try:
        provider = getattr(request.app.state, "llm_provider", None)
        result = await engine.query(req.question, top_k=req.top_k, provider=provider)
        return {
            "answer": result.answer,
            "sources": [
                {
                    "content": s.content[:200],
                    "source": s.metadata.get("source", s.source),
                    "document_id": s.document_id,
                }
                for s in result.sources
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def rag_stats(request):
    """知识库统计"""
    engine = get_rag_engine(request)
    try:
        stats = await engine.stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
