import React, { useState, useEffect, useRef } from 'react';
import { FaPaperPlane, FaTrash, FaImage, FaGlobe } from 'react-icons/fa';
import chatUtils, { ChatMessage } from '../utils/chat-utils';
import LoadingIndicator from './loading-indicator';
import MarkdownRenderer from './markdown-renderer';
import useChatFeatureStore from '../utils/chat-feature-utils';
import { handleInputResize, handleShiftEnterKey, scrollbarStyles } from '../utils/input-handler-utils';
import { INPUT_CONFIG } from '../utils/input-config';
import { handlePaste } from '../utils/paste-handler-utils';
import clearChatUtils from '../utils/clear-chat-utils';
import CustomPopup from '../utils/popup-utils';
import toast from 'react-hot-toast';

interface ChatProps {
  currentPdf?: string | null;
}

const Chat: React.FC<ChatProps> = ({ currentPdf = null }) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { 
    enableChatWithPicture,
    enableWebResearch,
    toggleChatWithPicture,
    toggleWebResearch 
  } = useChatFeatureStore();

  // 滾動到最新訊息
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      const chatContainer = messagesEndRef.current.parentElement;
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 當輸入框內容變化時調整高度
  useEffect(() => {
    if (textareaRef.current) {
      handleInputResize(textareaRef.current, {
        maxRows: INPUT_CONFIG.maxRows,
        minHeight: INPUT_CONFIG.minHeight
      });
    }
  }, [message]);

  // 當 PDF 改變時載入對應的對話紀錄
  useEffect(() => {
    const loadHistory = async () => {
      if (currentPdf) {
        try {
          setIsLoading(true);
          const history = await chatUtils.loadChatHistory(currentPdf);
          setMessages(history.messages);
        } catch (error) {
          console.error('Error loading chat history:', error);
          toast.error('無法載入對話紀錄');
        } finally {
          setIsLoading(false);
        }
      } else {
        setMessages([]);
      }
    };

    loadHistory();
  }, [currentPdf]);

  // 清空對話紀錄
  const handleClearChat = async () => {
    try {
      setIsLoading(true);
      await clearChatUtils.clearChatHistory(currentPdf);
      setMessages([]);
      toast.success('對話紀錄已清空');
    } catch (error) {
      console.error('Error clearing chat history:', error);
      toast.error('清空對話紀錄失敗');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (message.trim()) {
      try {
        // 先加入使用者訊息
        const userMessage: ChatMessage = {
          id: Date.now().toString(),
          content: message.trim(),
          role: 'user',
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, userMessage]);
        setMessage('');
        setIsLoading(true);

        // 發送訊息到後端並等待回應，包含功能開關狀態
        const response = await chatUtils.sendMessage(
          message.trim(),
          currentPdf,
          enableChatWithPicture,
          enableWebResearch
        );
        setMessages(prev => [...prev, response]);

        // 重置輸入框高度
        if (textareaRef.current) {
          textareaRef.current.style.height = '40px';
        }

      } catch (error) {
        console.error('Error sending message:', error);
        toast.error('發送訊息失敗');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
      handleSend();
      return;
    } else if (handleShiftEnterKey(e)) {
      return;
    }
  };

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div className="bg-gray-800 rounded-lg p-4 h-full w-full flex flex-col">
        <div className="flex flex-col flex-grow min-h-0">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-white text-lg">Chat</h2>
            <button
              onClick={() => setShowClearConfirm(true)}
              disabled={isLoading || messages.length === 0}
              className={`text-gray-400 hover:text-red-500 transition-colors p-2 rounded
                ${(isLoading || messages.length === 0) ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-700'}`}
              title="清空對話紀錄"
            >
              <FaTrash />
            </button>
          </div>
          <div className="bg-gray-700 rounded p-3 flex-grow mb-4 overflow-y-auto">
            {isLoading && messages.length === 0 ? (
              <div className="text-gray-400 text-center py-2">載入對話紀錄中...</div>
            ) : (
              <>
                {messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <div
                      key={msg.id}
                      className={`mb-3 ${isUser ? 'text-right' : 'text-left'}`}
                    >
                      <div
                        className={`inline-block max-w-[70%] rounded-lg px-4 py-2 ${
                          isUser
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-600 text-gray-100'
                        }`}
                      >
                        <div className={`text-sm break-words overflow-hidden ${isUser ? 'text-right' : 'text-left'}`}>
                          <MarkdownRenderer content={msg.content} />
                        </div>
                        <div className="text-xs mt-1 opacity-70">
                          {chatUtils.formatTimestamp(msg.timestamp)}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {isLoading && (
                  <div className="mb-3 text-left">
                    <div className="inline-block max-w-[70%] rounded-lg px-4 py-2 bg-gray-600">
                      <LoadingIndicator />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                onPaste={(e) => {
                  if (textareaRef.current) {
                    handlePaste(e, textareaRef.current, setMessage);
                  }
                }}
                disabled={isLoading}
                rows={1}
                className={`flex-grow bg-gray-700 text-white rounded px-3 py-2
                  focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none min-h-[40px] max-h-[200px]
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                placeholder={isLoading ? '請稍候...' : '輸入訊息...'}
                style={{
                  overflowY: 'auto',
                  transition: 'height 0.1s ease'
                }}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !message.trim()}
                className={`bg-blue-500 text-white px-4 py-2 rounded self-end h-[40px]
                  ${
                    isLoading || !message.trim()
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-blue-600'
                  }`}
              >
                <FaPaperPlane />
              </button>
            </div>
            <div className="flex gap-2 h-[20px] items-center">
              <button
                title="附加圖片"
                onClick={toggleChatWithPicture}
                className={`p-1 rounded-full transition-colors ${
                  enableChatWithPicture
                    ? 'bg-blue-500/20 text-blue-400'
                    : 'text-gray-400 hover:text-blue-400'
                }`}
              >
                <FaImage size={12} />
              </button>
              <button
                title="啟用搜尋"
                onClick={toggleWebResearch}
                className={`p-1 rounded-full transition-colors ${
                  enableWebResearch
                    ? 'bg-blue-500/20 text-blue-400'
                    : 'text-gray-400 hover:text-blue-400'
                }`}
              >
                <FaGlobe size={12} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 清空對話確認彈窗 */}
      <CustomPopup
        open={showClearConfirm}
        onClose={() => setShowClearConfirm(false)}
        title="清空對話確認"
        showConfirm
        onConfirm={handleClearChat}
        confirmText="確定清空"
        cancelText="取消"
        buttonColors={{
          confirm: 'bg-red-500',
          confirmHover: 'hover:bg-red-600',
          cancel: 'bg-gray-600',
          cancelHover: 'hover:bg-gray-700'
        }}
      >
        <p>確定要清空所有對話紀錄嗎？此操作無法復原。</p>
      </CustomPopup>
    </>
  );
};

export default Chat;