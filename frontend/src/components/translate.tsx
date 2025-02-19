import React, { useState, useEffect } from 'react';
import { FaLanguage } from 'react-icons/fa';

interface TextSelectedEvent extends CustomEvent {
  detail: {
    text: string;
    pageNumber: number;
  };
}

const LANGUAGES = [
  { code: 'zh-TW', name: '繁體中文' },
  { code: 'zh-CN', name: '简体中文' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
];

const scrollbarStyles = `
  .custom-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: #4B5563 #1F2937;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 8px;
  }

  .custom-scrollbar::-webkit-scrollbar-track {
    background: #1F2937;
    border-radius: 4px;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #4B5563;
    border-radius: 4px;
    border: 2px solid #1F2937;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: #6B7280;
  }
`;

const Translate: React.FC = () => {
  const [originalText, setOriginalText] = useState<string>('');
  const [translatedText, setTranslatedText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [targetLanguage, setTargetLanguage] = useState<string>('zh-TW');

  useEffect(() => {
    const styleSheet = document.createElement('style');
    styleSheet.textContent = scrollbarStyles;
    document.head.appendChild(styleSheet);

    return () => {
      document.head.removeChild(styleSheet);
    };
  }, []);

  useEffect(() => {
    const handleSelectedText = (event: TextSelectedEvent) => {
      setOriginalText(event.detail.text || '');
      setTranslatedText('');
    };

    window.addEventListener('textSelected', handleSelectedText as EventListener);
    return () => window.removeEventListener('textSelected', handleSelectedText as EventListener);
  }, []);

  useEffect(() => {
    const translateText = async () => {
      if (!originalText) return;
      
      setLoading(true);
      try {
        const response = await fetch('http://localhost:9999/selected-text', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: originalText,
            targetLanguage: targetLanguage
          }),
        });

        const data = await response.json();
        if (data.status === 'success') {
          setTranslatedText(data.translatedText);
        }
      } catch (error) {
        console.error('Translation error:', error);
      } finally {
        setLoading(false);
      }
    };

    translateText();
  }, [originalText, targetLanguage]);

  return (
    <div className="bg-gray-800 rounded-lg p-3 h-full w-full flex flex-col">
      {/* Header section - reduced height and padding */}
      <div className="flex items-center justify-between mb-2 h-8">
        <div className="flex items-center gap-1.5">
          <FaLanguage className="text-blue-500 text-lg" />
          <h2 className="text-white text-base">Translation</h2>
        </div>
        
        {/* Language selector - reduced size */}
        <select
          value={targetLanguage}
          onChange={(e) => setTargetLanguage(e.target.value)}
          className="bg-gray-700 text-white rounded px-2 py-0.5 text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
      </div>
      
      {/* Translation content - increased height */}
      <div className="flex-1 min-h-0">
        <div className="h-full bg-gray-700 rounded-lg p-3 overflow-auto custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <p className="text-white whitespace-pre-wrap">
              {translatedText || 'Translation text will appear here...'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Translate;