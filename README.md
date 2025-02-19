# 📚 PDF Paper Researcher

A powerful PDF paper research assistant that utilizes local LLM technology to process and analyze academic papers. This project uses Ollama as a local large language model, providing an efficient and private paper processing experience.

[Chinese README](Documents/README-TW.md)

## ✨ Features

- 📑 PDF document parsing and content extraction
- 🔍 Intelligent text analysis and summary generation
- 🌐 Multi-language translation support
- 💡 Paper key points extraction and analysis
- 🤖 Local LLM processing based on Ollama
- 🔒 Privacy protection with all processing done locally

## 🏗 System Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + Flask
- **LLM Engine**: Ollama
- **Containerization**: Docker
- **Vector Search**: FAISS
- **Web Search**: Tavily API

## 🚀 Installation Guide

### Prerequisites

Before installation, ensure your system meets the following requirements:

- 🖥 **Hardware Requirements**:
  - VRAM: Minimum 12GB
  - Disk Space: 20GB+ (SSD recommended)
- 📦 **Required Software**:
  - [Ollama](https://ollama.ai)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Installation Steps

#### 1️⃣ Pull Required LLM Models

```bash
ollama pull llama3.2-vision
ollama pull phi4
ollama pull mxbai-embed-large
```

#### 2️⃣ Configure Environment

1. Create a `config` folder in the project root
2. Create `Tavily_API_KEY.txt` in the `config` folder
3. Add your Tavily API key to `Tavily_API_KEY.txt`

#### 3️⃣ Start Services

Run the following commands in the project root:

```bash
docker network create research-network
docker-compose up -d
```

#### 4️⃣ Access Application

Once all containers are running, open your browser and visit:

```
http://localhost:5173
```

## 🎯 Usage Guide

1. Upload PDF papers to the web interface
2. System will automatically process and analyze the PDF content
3. Interact with the system through the chat interface
4. Use multi-language translation features
5. Extract and summarize key points from papers

## 🔧 Troubleshooting

- If services fail to start, check if Docker is running properly
- Ensure all required ports (5173, 8000) are not in use
- Verify that Ollama service is running
- Check if API keys are configured correctly

## 📝 Notes

- Initial model downloads may take some time
- Stable internet connection recommended
- Processing large PDF files may require more time
- Ensure sufficient system resources for running LLM models

## 🤝 Contributing

Issues and Pull Requests are welcome to help improve this project!

## 📄 License

This project is licensed under the MIT License.
