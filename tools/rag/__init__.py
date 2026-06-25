# tools/rag/__init__.py

"""
RAG (Retrieval-Augmented Generation) 知识库模块。

tools/rag/
├── document_loader.py   — 文档加载（PDF/DOCX/TXT/MD/网页）
├── text_splitter.py     — 文本分块
├── embedder.py          — 向量化
├── vector_store.py      — pgvector 存储与检索
├── rag_engine.py        — RAG 全流程编排
└── context_injector.py  — Agent prompt 上下文注入
"""

from tools.rag.text_splitter import TextSplitter, DocumentChunk
from tools.rag.rag_engine import RAGEngine, RAGResult

__all__ = ["TextSplitter", "DocumentChunk", "RAGEngine", "RAGResult"]
