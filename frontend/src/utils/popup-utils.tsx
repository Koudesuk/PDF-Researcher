import React from 'react';
import Popup from 'reactjs-popup';
import 'reactjs-popup/dist/index.css';

// 自定義彈出視窗樣式
const popupStyles = `
  .popup-overlay {
    background: rgba(0, 0, 0, 0.5);
  }
  
  .popup-content {
    background: none !important;
    border: none !important;
    padding: 0 !important;
    width: auto !important;
  }
`;

interface ButtonColors {
  confirm?: string;
  confirmHover?: string;
  cancel?: string;
  cancelHover?: string;
}

interface PopupProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  showConfirm?: boolean;
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
  buttonColors?: ButtonColors;
}

// 自訂彈出視窗組件
const CustomPopup: React.FC<PopupProps> = ({
  open,
  onClose,
  title,
  children,
  showConfirm = false,
  onConfirm,
  confirmText = '確認',
  cancelText = '取消',
  buttonColors = {
    confirm: 'bg-blue-500',
    confirmHover: 'hover:bg-blue-600',
    cancel: 'bg-gray-600',
    cancelHover: 'hover:bg-gray-700'
  }
}) => {
  return (
    <>
      <style>{popupStyles}</style>
      <Popup 
        open={open} 
        onClose={onClose} 
        modal 
        nested
        closeOnDocumentClick={false}
        className="dark-popup"
      >
        <div className="bg-gray-800 rounded-lg p-4 w-full max-w-md mx-auto shadow-xl">
          {title && (
            <div className="mb-4 pb-2 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white">{title}</h2>
            </div>
          )}
          
          <div className="text-white mb-4">
            {children}
          </div>

          <div className="flex justify-end gap-2">
            {showConfirm ? (
              <>
                <button
                  onClick={() => {
                    onConfirm?.();
                    onClose();
                  }}
                  className={`${buttonColors.confirm} ${buttonColors.confirmHover} text-white px-4 py-2 rounded transition-colors`}
                >
                  {confirmText}
                </button>
                <button
                  onClick={onClose}
                  className={`${buttonColors.cancel} ${buttonColors.cancelHover} text-white px-4 py-2 rounded transition-colors`}
                >
                  {cancelText}
                </button>
              </>
            ) : (
              <button
                onClick={onClose}
                className={`${buttonColors.confirm} ${buttonColors.confirmHover} text-white px-4 py-2 rounded transition-colors`}
              >
                確定
              </button>
            )}
          </div>
        </div>
      </Popup>
    </>
  );
};

export default CustomPopup;