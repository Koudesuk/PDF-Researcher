import { KeyboardEvent } from 'react';
import { INPUT_CONFIG } from './input-config';

interface InputHandlerOptions {
  maxRows?: number;
  minHeight?: number;
}

export const handleInputResize = (
  element: HTMLTextAreaElement,
  options: InputHandlerOptions = {}
) => {
  const { maxRows = INPUT_CONFIG.maxRows, minHeight = INPUT_CONFIG.minHeight } = options;
  
  // 重置高度以獲取正確的 scrollHeight
  element.style.height = 'auto';
  
  // 計算內容的實際高度
  const contentHeight = element.scrollHeight;
  const lineHeight = parseInt(getComputedStyle(element).lineHeight);
  const maxHeight = lineHeight * maxRows;
  
  // 設置新的高度，但不超過最大行數限制
  const newHeight = Math.min(Math.max(minHeight, contentHeight), maxHeight);
  element.style.height = `${newHeight}px`;
  
  // 根據內容高度決定是否啟用滾動
  element.style.overflowY = contentHeight > maxHeight ? 'auto' : 'hidden';
  
  // 隱藏滾動條但保持功能
  element.style.scrollbarWidth = 'none';
  // 使用類型斷言來處理非標準屬性
  (element.style as any).msOverflowStyle = 'none';
};

export const handleShiftEnterKey = (event: KeyboardEvent<HTMLTextAreaElement>) => {
  if (event.key === 'Enter' && event.shiftKey) {
    event.preventDefault();
    const element = event.currentTarget;
    const start = element.selectionStart;
    const end = element.selectionEnd;
    const value = element.value;
    
    // 在游標位置插入換行符
    element.value = value.substring(0, start) + '\n' + value.substring(end);
    
    // 設置游標位置
    element.selectionStart = element.selectionEnd = start + 1;
    
    // 觸發 resize
    handleInputResize(element);
    return true;
  }
  return false;
};

// 移除 Firefox 的默認滾動條樣式
export const scrollbarStyles = `
  textarea::-webkit-scrollbar {
    display: none;
  }
  textarea {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
`;