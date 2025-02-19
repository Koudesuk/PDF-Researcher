# Stage 1: 構建前端
FROM node:20-slim AS frontend-builder
WORKDIR /frontend

# 複製前端依賴相關文件
COPY frontend/package*.json ./
RUN npm install

# 複製源代碼並構建
COPY frontend/ .
RUN npm run build

# Stage 2: 構建後端
FROM python:3.12.6-slim AS backend-builder
WORKDIR /app

# 安裝構建依賴
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: 最終映像
FROM python:3.12.6-slim
LABEL maintainer="Koudesuk" \
    description="Research Assistant with PDF processing and AI capabilities" \
    version="1.0"

WORKDIR /app

# 安裝 nginx 和運行時依賴
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    libgl1-mesa-glx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 配置 nginx
COPY nginx.conf /etc/nginx/nginx.conf

# 建立必要的目錄
RUN mkdir -p /app/frontend/dist /app/backend/uploads /app/backend/screenshots /app/backend/logs /app/config

# 從構建階段複製文件
COPY --from=frontend-builder /frontend/dist /app/frontend/dist
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# 複製後端代碼和啟動腳本
COPY backend/ /app/backend/
COPY start.sh .
RUN chmod +x start.sh

# 配置環境變量
ENV FLASK_APP=backend/app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GOOGLETRANS_TIMEOUT=5 \
    GOOGLETRANS_RETRY=3

# 修改目錄權限
RUN chown -R www-data:www-data /app && \
    chown -R www-data:www-data /var/log/nginx && \
    chown -R www-data:www-data /var/lib/nginx

# 切換到非root用戶
USER www-data

# 暴露端口
EXPOSE 9999 5173

# 設置啟動命令
CMD ["./start.sh"]