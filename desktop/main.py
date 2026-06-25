# desktop/main.py

"""
Claude-Codex Multi-Agent 桌面端。

使用 pywebview 创建轻量级桌面应用，内嵌 FastAPI 后端。
无需 Electron/Node.js，纯 Python 实现。

依赖: pip install pywebview

用法:
    python desktop/main.py
"""

import threading
import logging
import sys
import os

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s - %(message)s")
logger = logging.getLogger("desktop")


def start_backend():
    """在后台线程启动 FastAPI 后端"""
    import uvicorn
    from server.app import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def main():
    """桌面端入口"""
    try:
        import webview
    except ImportError:
        print("=" * 60)
        print("  桌面端依赖未安装")
        print("  请运行: pip install pywebview")
        print("=" * 60)
        sys.exit(1)

    # 启动后端
    logger.info("Starting backend server...")
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # 等待后端启动
    import time
    time.sleep(2)

    # 创建桌面窗口
    logger.info("Creating desktop window...")
    webview.create_window(
        title="Claude-Codex Multi-Agent Pipeline",
        url="http://127.0.0.1:8000",
        width=1440,
        height=900,
        min_size=(1024, 768),
        text_select=True,
    )

    # 启动 pywebview
    webview.start(debug=False)
    logger.info("Desktop application closed.")


if __name__ == "__main__":
    main()
