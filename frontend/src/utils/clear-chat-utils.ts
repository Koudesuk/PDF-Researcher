import axios from 'axios';

const API_BASE_URL = 'http://localhost:9999';

export const clearChatUtils = {
  // 清空特定PDF的對話紀錄
  async clearChatHistory(pdfFilename: string | null): Promise<void> {
    try {
      await axios.delete(
        pdfFilename 
          ? `${API_BASE_URL}/chat-history/${pdfFilename}`
          : `${API_BASE_URL}/chat-history`
      );
    } catch (error) {
      console.error('Error clearing chat history:', error);
      throw error;
    }
  }
};

export default clearChatUtils;