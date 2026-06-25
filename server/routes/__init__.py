# server/routes/__init__.py

"""
API 路由注册。

从 server/app.py 导入并注册所有子路由。
"""

from server.routes.rag import router as rag_router

__all__ = ["rag_router"]
