# Dockerfile

# Stage 1: Frontend build (optional, can be skipped for dev)
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production || echo "No frontend directory, skipping"
COPY frontend/ .
RUN npm run build 2>/dev/null || echo "No frontend build, skipping"

# Stage 2: Backend
FROM python:3.12-slim AS backend

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 如果前端构建成功，复制静态文件
COPY --from=frontend-build /app/frontend/dist /app/static 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
