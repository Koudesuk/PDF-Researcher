# 📚 PDF Paper Researcher

一個強大的 PDF 論文研究助手，利用本地 LLM 技術處理和分析學術論文內容。本項目使用 Ollama 作為本地大型語言模型，提供高效且私密的論文處理體驗。

## ✨ 功能特點

- 📑 PDF 文件解析與內容提取
- 🔍 智能文本分析與摘要生成
- 🌐 支持多語言翻譯功能
- 💡 論文要點提取與重點分析
- 🤖 基於 Ollama 的本地 LLM 處理
- 🔒 保護隱私，所有處理皆在本地進行

## 🏗 系統架構

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + Flask
- **LLM Engine**: Ollama
- **容器化**: Docker
- **向量搜索**: FAISS
- **網路搜索**: Tavily API

## 🚀 安裝指南

### 前置需求

在開始安裝之前，請確保您的系統滿足以下要求：

- 🖥 **硬體需求**:
  - VRAM: 至少 12GB
  - 硬碟空間: 20GB+ (建議使用 SSD)
- 📦 **必要軟體**:
  - [Ollama](https://ollama.ai)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 安裝步驟

#### 1️⃣ 下載必要的 LLM 模型

```bash
ollama pull llama2-uncensored
ollama pull phi4
ollama pull mxbai-embed-large
```

#### 2️⃣ 配置環境

1. 在項目根目錄下創建 `config` 文件夾
2. 在 `config` 文件夾中創建 `Tavily_API_KEY.txt` 文件
3. 將您的 Tavily API 金鑰添加到 `Tavily_API_KEY.txt` 文件中

#### 3️⃣ 啟動服務

在項目根目錄下執行以下命令：

```bash
docker network create research-network
docker-compose up -d
```

#### 4️⃣ 訪問應用

當所有容器都成功啟動後，打開瀏覽器訪問：

```
http://localhost:5173
```

## 🎯 使用指南

1. 將 PDF 論文上傳到網頁界面
2. 系統會自動處理並分析 PDF 內容
3. 可以通過對話界面與系統進行交互
4. 支持多語言翻譯功能
5. 可以進行論文重點提取和總結

## 🔧 故障排除

- 如果服務無法啟動，請檢查 Docker 服務是否正常運行
- 確保所有必要的端口（5173、8000）未被占用
- 檢查 Ollama 服務是否正常運行
- 確保 API 金鑰配置正確

## 📝 注意事項

- 首次運行時，模型下載可能需要一些時間
- 建議使用穩定的網絡連接
- 處理大型 PDF 文件時可能需要更多時間
- 確保系統有足夠的資源來運行 LLM 模型

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來幫助改進這個專案！

## 📄 授權

本項目採用 MIT 授權協議。
