import os
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain.schema import messages_from_dict, messages_to_dict, HumanMessage, AIMessage, BaseMessage
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from rich.console import Console
from rich import print as rprint
from rich.panel import Panel
from rich.traceback import install

# 安裝 rich 的異常追蹤
install(show_locals=True)

# 創建 rich console 實例
console = Console()


class CustomFileChatMessageHistory:
    """自定義的檔案對話歷史管理器"""

    def __init__(self, filepath: str, encoding: str = 'utf-8'):
        self.filepath = filepath
        self.encoding = encoding
        self.messages = []
        self._load_messages()

    def _load_messages(self):
        """從檔案載入訊息"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding=self.encoding) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.messages = data
                    else:
                        self.messages = []
            except json.JSONDecodeError:
                self.messages = []
        else:
            self.messages = []

    def _save_messages(self):
        """保存訊息到檔案"""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding=self.encoding) as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def add_message(self, message: Dict[str, Any]):
        """添加新訊息"""
        self.messages.append(message)
        self._save_messages()

    def get_messages(self) -> List[Dict[str, Any]]:
        """獲取所有訊息"""
        return self.messages

    def clear_messages(self):
        """清空所有訊息"""
        self.messages = []
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
            # 如果目錄為空，則刪除目錄
            directory = os.path.dirname(self.filepath)
            if os.path.exists(directory) and not os.listdir(directory):
                os.rmdir(directory)


class ChatLogger:
    """聊天記錄管理器，整合對話管理與記憶體管理功能"""

    def __init__(self, base_dir: str = 'logs'):
        """
        初始化聊天記錄管理器

        Args:
            base_dir (str): 對話記錄的基礎目錄
        """
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        self.histories = {}  # 用於存儲每個PDF文件的對話歷史

    def _get_dialog_path(self, pdf_filename: str) -> str:
        """
        獲取對話記錄檔案的路徑

        Args:
            pdf_filename (str): PDF 文件名稱

        Returns:
            str: 對話記錄檔案的完整路徑
        """
        pdf_dialog_dir = os.path.join(
            self.base_dir, os.path.splitext(pdf_filename)[0])
        if not os.path.exists(pdf_dialog_dir):
            os.makedirs(pdf_dialog_dir)
        return os.path.join(pdf_dialog_dir, 'chatlog.json')

    def _get_chat_history(self, pdf_filename: str) -> CustomFileChatMessageHistory:
        """
        獲取或創建特定PDF文件的聊天歷史記錄

        Args:
            pdf_filename (str): PDF 文件名稱

        Returns:
            CustomFileChatMessageHistory: 聊天歷史記錄對象
        """
        try:
            if pdf_filename not in self.histories:
                chat_file = self._get_dialog_path(pdf_filename)
                self.histories[pdf_filename] = CustomFileChatMessageHistory(
                    chat_file,
                    encoding='utf-8'
                )
            return self.histories[pdf_filename]
        except Exception as e:
            console.print(Panel(
                f"[red]Error getting chat history for[/red] [yellow]{pdf_filename}[/yellow]\n"
                f"[red]Error:[/red] {str(e)}",
                title="Chat History Error",
                border_style="red"
            ))
            raise Exception(f"無法獲取對話歷史: {str(e)}")

    def load_chat_history(self, pdf_filename: str) -> List[Dict[str, Any]]:
        """
        載入對話歷史記錄

        Args:
            pdf_filename (str): PDF 文件名稱

        Returns:
            List[Dict[str, Any]]: 對話歷史記錄列表
        """
        try:
            history = self._get_chat_history(pdf_filename)
            return history.get_messages()
        except Exception as e:
            console.print(Panel(
                f"[red]Error loading chat history for[/red] [yellow]{pdf_filename}[/yellow]\n"
                f"[red]Error details:[/red] {str(e)}",
                title="Loading History Error",
                border_style="red"
            ))
            rprint("[yellow]Returning empty message list due to error[/yellow]")
            return []

    def clear_chat_history(self, pdf_filename: Optional[str] = None):
        """
        清空對話歷史記錄

        Args:
            pdf_filename (Optional[str]): PDF 文件名稱。如果為 None，則清空所有對話記錄
        """
        try:
            if pdf_filename:
                # 清空特定PDF的對話記錄
                if pdf_filename in self.histories:
                    self.histories[pdf_filename].clear_messages()
                    del self.histories[pdf_filename]
            else:
                # 清空所有對話記錄
                for history in self.histories.values():
                    history.clear_messages()
                self.histories.clear()

                # 刪除整個日誌目錄
                if os.path.exists(self.base_dir):
                    for root, dirs, files in os.walk(self.base_dir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            try:
                                os.rmdir(os.path.join(root, name))
                            except OSError:
                                pass
                    try:
                        os.rmdir(self.base_dir)
                        os.makedirs(self.base_dir)  # 重新創建空目錄
                    except OSError:
                        pass

        except Exception as e:
            console.print(Panel(
                f"[red]Error clearing chat history for[/red] [yellow]{pdf_filename if pdf_filename else 'all files'}[/yellow]\n"
                f"[red]Error details:[/red] {str(e)}",
                title="Clear History Error",
                border_style="red"
            ))
            raise Exception(f"無法清空對話歷史: {str(e)}")

    def process_chat(self, message: str, pdf_filename: Optional[str],
                     response_generator: callable) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        處理完整的對話流程

        Args:
            message (str): 使用者輸入的訊息
            pdf_filename (Optional[str]): PDF 文件名稱
            response_generator (callable): 生成回應的函數

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (使用者訊息, AI回應訊息)
        """
        # 創建使用者訊息
        user_message = {
            'id': str(datetime.datetime.now().timestamp()),
            'content': message,
            'role': 'user',
            'timestamp': datetime.datetime.now().isoformat()
        }

        if pdf_filename:
            try:
                history = self._get_chat_history(pdf_filename)
                history.add_message(user_message)
            except Exception as e:
                console.print(Panel(
                    f"[red]Error adding human message to history for[/red] [yellow]{pdf_filename}[/yellow]\n"
                    f"[red]Error details:[/red] {str(e)}",
                    title="Message Save Error",
                    border_style="red"
                ))
                raise Exception(f"無法保存對話歷史: {str(e)}")

        try:
            # 生成回應
            response = response_generator(message)
        except Exception as e:
            response = f"抱歉，我無法理解您的問題。錯誤：{str(e)}"

        # 創建 AI 回應訊息
        assistant_message = {
            'id': str(datetime.datetime.now().timestamp()),
            'content': response,
            'role': 'assistant',
            'timestamp': datetime.datetime.now().isoformat()
        }

        if pdf_filename:
            try:
                history = self._get_chat_history(pdf_filename)
                history.add_message(assistant_message)
            except Exception as e:
                console.print(Panel(
                    f"[red]Error adding AI message to history for[/red] [yellow]{pdf_filename}[/yellow]\n"
                    f"[red]Error details:[/red] {str(e)}",
                    title="AI Response Save Error",
                    border_style="red"
                ))
                raise Exception(f"無法保存AI回應到對話歷史: {str(e)}")

        return user_message, assistant_message
