#!/bin/bash

# 設置 Ollama 主機環境變量
export OLLAMA_HOST=${OLLAMA_HOST:-"host.docker.internal"}
echo "Setting OLLAMA_HOST to: $OLLAMA_HOST"

# 設置 Flask 生產環境
export FLASK_ENV=production
export FLASK_DEBUG=0

# 啟動 nginx 在背景運行
nginx -g 'daemon off;' &

# 等待 nginx 啟動
sleep 2

# 啟動 Flask 後端服務
exec python backend/app.py