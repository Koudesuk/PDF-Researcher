import axios from 'axios';

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

export interface ChatHistory {
  messages: ChatMessage[];
  pdfFilename: string | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9999';

export const chatUtils = {
  // 發送訊息到後端
  async sendMessage(
    message: string,
    pdfFilename: string | null,
    enableChatWithPicture: boolean,
    enableWebResearch: boolean
  ): Promise<ChatMessage> {
    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message,
        pdfFilename,
        enableChatWithPicture,
        enableWebResearch
      });
      
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  // 載入特定 PDF 的對話紀錄
  async loadChatHistory(pdfFilename: string): Promise<ChatHistory> {
    try {
      const response = await axios.get(`${API_BASE_URL}/chat-history/${pdfFilename}`);
      return response.data;
    } catch (error) {
      console.error('Error loading chat history:', error);
      throw error;
    }
  },

  // 格式化時間
  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

export default chatUtils;