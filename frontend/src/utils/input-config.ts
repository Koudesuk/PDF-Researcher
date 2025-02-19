// 定義通用的輸入框設定
export const INPUT_CONFIG = {
  maxRows: 5, // 最大行數限制為 5 行
  minHeight: 40, // 最小高度為 40px
  lineHeight: 20, // 預設行高
} as const;

// 計算最大高度
export const getMaxHeight = () => {
  return INPUT_CONFIG.lineHeight * INPUT_CONFIG.maxRows;
};