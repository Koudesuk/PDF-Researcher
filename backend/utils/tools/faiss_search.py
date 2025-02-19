import os
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from rich.console import Console

console = Console()


class FAISSSearchTool:
    """FAISS vector database search tool."""

    def __init__(self, model_name: str = "mxbai-embed-large"):
        """
        初始化 FAISS 搜索工具

        Args:
            model_name (str): Ollama embedding 模型名稱
        """
        self.embeddings = OllamaEmbeddings(model=model_name)

    def search_similar_content(self, query: str, pdf_filename: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        在 FAISS vector database 中搜索與查詢相似的內容

        Args:
            query (str): 搜索查詢文本
            pdf_filename (str): PDF 文件名稱
            top_k (int): 返回的最相似結果數量

        Returns:
            List[Dict[str, Any]]: 搜索結果列表，每個結果包含內容和相似度分數
        """
        try:
            # 獲取 FAISS index 路徑
            base_name = os.path.splitext(pdf_filename)[0]
            index_path = os.path.join("FAISS_index", base_name)

            # 檢查 FAISS index 是否存在
            if not os.path.exists(index_path):
                console.print(
                    f"[red]Error: FAISS index not found for {pdf_filename}[/red]")
                return []

            # 加載 FAISS index，允許反序列化
            db = FAISS.load_local(
                folder_path=index_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )

            # 執行相似度搜索
            results = db.similarity_search_with_score(query, k=top_k)

            # 格式化結果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "score": float(score),  # 將numpy.float64轉換為Python float
                    "metadata": doc.metadata
                })

            return formatted_results

        except Exception as e:
            console.print(f"[red]Error searching FAISS index: {str(e)}[/red]")
            return []
