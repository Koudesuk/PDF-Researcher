import { ClipboardEvent } from 'react';
import { handleInputResize } from './input-handler-utils';
import { INPUT_CONFIG } from './input-config';

/**
 * 處理貼上事件，確保正確處理多行文本
 * @param event - ClipboardEvent 事件物件
 * @param element - 文本輸入元素
 * @param setValue - 用於更新輸入值的函數
 */
export const handlePaste = (
  event: ClipboardEvent<HTMLTextAreaElement>,
  element: HTMLTextAreaElement,
  setValue: (value: string) => void
) => {
  // 阻止默認貼上行為
  event.preventDefault();

  // 從剪貼簿獲取純文本內容
  const clipboardData = event.clipboardData;
  const pastedText = clipboardData.getData('text/plain');

  // 處理文本
  const processedText = processMultilineText(pastedText);

  // 獲取當前選擇範圍
  const start = element.selectionStart;
  const end = element.selectionEnd;
  const currentValue = element.value;

  // 組合新的文本內容
  const newValue = currentValue.substring(0, start) + 
                  processedText + 
                  currentValue.substring(end);

  // 更新輸入框的值
  setValue(newValue);

  // 在下一個事件循環中設置新的游標位置和調整高度
  setTimeout(() => {
    // 設置新的游標位置
    const newPosition = start + processedText.length;
    element.selectionStart = newPosition;
    element.selectionEnd = newPosition;
// 調整輸入框高度，使用設定的最大行數
handleInputResize(element, {
  maxRows: INPUT_CONFIG.maxRows,
  minHeight: INPUT_CONFIG.minHeight
});
    handleInputResize(element);
  }, 0);
};

/**
 * 處理多行文本，確保換行符的一致性
 * @param text - 要處理的文本
 * @returns 處理後的文本
 */
const processMultilineText = (text: string): string => {
  // 統一換行符格式（將 \r\n 或 \r 轉換為 \n）
  const normalizedText = text.replace(/\r\n|\r/g, '\n');

  // 移除開頭和結尾的空白行
  return normalizedText.replace(/^\n+|\n+$/g, '');
};

/**
 * 檢測文本是否包含換行符
 * @param text - 要檢查的文本
 * @returns 是否包含換行符
 */
export const hasLineBreaks = (text: string): boolean => {
  return /\r\n|\r|\n/.test(text);
};