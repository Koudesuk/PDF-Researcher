import React, { useState, useRef, useMemo, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { FaUpload, FaTimes, FaSearchPlus, FaSearchMinus, FaCamera, FaSpinner } from 'react-icons/fa';
import axios from 'axios';
import { PDF_OPTIONS, calculateScale } from '../utils/pdf-utils';
import CustomPopup from '../utils/popup-utils';

// Import required styles for PDF rendering
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

interface PDFHandlerProps {
  onFileLoaded?: (file: File) => void;
  isCapturing?: boolean;
  onStartCapture?: () => void;
  onClose?: () => void;
}

const PDFHandler: React.FC<PDFHandlerProps> = ({
  onFileLoaded = () => {},
  isCapturing = false,
  onStartCapture = () => {},
  onClose = () => {},
}) => {
  // State management
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.5);
  const [pageInputValue, setPageInputValue] = useState<string>('1');
  const [visiblePages, setVisiblePages] = useState<number[]>([1]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [showFileExistsPopup, setShowFileExistsPopup] = useState<boolean>(false);
  const [showErrorPopup, setShowErrorPopup] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  
  // References
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const baseScale = useRef<number>(1.5);
  const intersectionObserver = useRef<IntersectionObserver | null>(null);
  const pendingFileRef = useRef<File | null>(null);
  
  // Options memo to prevent unnecessary re-renders
  const options = useMemo(() => PDF_OPTIONS, []);

  // Handle text selection
  const handleTextSelect = (pageNumber: number) => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;
  
    const range = selection.getRangeAt(0);
    const selectedText = range.toString().trim();
  
    if (selectedText) {
      // Create custom event with proper typing
      const event = new CustomEvent('textSelected', {
        detail: { 
          text: selectedText, 
          pageNumber: pageNumber 
        }
      }) as CustomEvent<{ text: string; pageNumber: number }>;
      
      window.dispatchEvent(event);
  
      // Send selected text to backend
      axios.post('http://localhost:9999/selected-text', {
        text: selectedText,
        pageNumber: pageNumber
      }).catch(error => {
        console.error('Error sending selected text:', error);
      });
    }
  };

  // Setup intersection observer for page tracking
  useEffect(() => {
    if (!containerRef.current) return;

    const options = {
      root: containerRef.current,
      threshold: 0.1
    };

    const callback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach(entry => {
        const pageNumber = parseInt(entry.target.getAttribute('data-page-number') || '1');
        
        if (entry.isIntersecting && !visiblePages.includes(pageNumber)) {
          setVisiblePages(prev => [...prev, pageNumber].sort((a, b) => a - b));
        } else if (!entry.isIntersecting) {
          setVisiblePages(prev => prev.filter(p => p !== pageNumber));
        }
      });
    };

    intersectionObserver.current = new IntersectionObserver(callback, options);
    return () => {
      intersectionObserver.current?.disconnect();
    };
  }, [visiblePages]);

  // Observer setup for each page
  const observePage = (element: HTMLDivElement | null) => {
    if (element && intersectionObserver.current) {
      intersectionObserver.current.observe(element);
    }
  };

  // Update current page based on scroll position
  const updateCurrentPage = () => {
    if (!containerRef.current) return;
    
    const pages = Array.from(containerRef.current.getElementsByClassName('pdf-page'));
    let closestPage = 1;
    let closestDistance = Infinity;

    pages.forEach(page => {
      const rect = page.getBoundingClientRect();
      const containerRect = containerRef.current!.getBoundingClientRect();
      const distance = Math.abs(rect.top - containerRect.top);
      
      if (distance < closestDistance) {
        closestDistance = distance;
        closestPage = parseInt(page.getAttribute('data-page-number') || '1');
      }
    });

    if (visiblePages.includes(closestPage)) {
      setCurrentPage(closestPage);
      setPageInputValue(closestPage.toString());
    }
  };

  // File selection handler
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || file.type !== 'application/pdf') return;
    
    setIsUploading(true);
    pendingFileRef.current = file;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post('http://localhost:9999/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data.status === 'exists') {
        setShowFileExistsPopup(true);
      } else {
        handleFileLoad(file);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setErrorMessage('檔案上傳失敗，請再試一次。');
      setShowErrorPopup(true);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileLoad = (file: File) => {
    setPdfFile(file);
    setCurrentPage(1);
    setPageInputValue('1');
    setVisiblePages([1]);
    onFileLoaded(file);
  };

  // Document load handlers
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  // Zoom handlers
  const handleZoom = (increment: boolean) => {
    setScale(prevScale => calculateScale(prevScale, baseScale.current, increment));
  };

  // Page navigation handlers
  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPageInputValue(e.target.value);
  };

  const handlePageInputBlur = () => {
    const pageNum = parseInt(pageInputValue);
    if (isNaN(pageNum) || pageNum < 1 || pageNum > numPages) {
      setPageInputValue(currentPage.toString());
      return;
    }
    
    const pageElement = containerRef.current?.querySelector(`[data-page-number="${pageNum}"]`);
    pageElement?.scrollIntoView({ behavior: 'smooth' });
  };

  const handlePageInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.currentTarget.blur();
    }
  };

  // Scroll handler
  const handleScroll = () => {
    updateCurrentPage();
  };

  // Reset handler
  const handleClose = () => {
    setPdfFile(null);
    setNumPages(0);
    setScale(baseScale.current);
    setCurrentPage(1);
    setPageInputValue('1');
    setVisiblePages([1]);
    onClose?.();
  };

  return (
    <div className="h-full w-full bg-gray-800 rounded-lg relative flex flex-col overflow-hidden">
      {pdfFile ? (
        <>
          {/* Controls */}
          <div className="absolute top-4 left-4 right-4 flex justify-between items-center z-10 bg-gray-700 p-2 rounded-lg">
            <div className="flex items-center gap-2">
              <button
                onClick={handleClose}
                className="bg-red-500 hover:bg-red-600 text-white p-2 rounded-full"
              >
                <FaTimes />
              </button>
              
              <button
                onClick={onStartCapture}
                className={`
                  bg-green-500 hover:bg-green-600 
                  text-white p-2 rounded-lg 
                  transition-all duration-200 
                  ${isCapturing ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}
                `}
                title="Take Screenshot"
                disabled={isCapturing}
              >
                <FaCamera className={isCapturing ? 'animate-pulse' : ''} />
              </button>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-gray-600 px-3 py-1 rounded">
                <input
                  type="text"
                  value={pageInputValue}
                  onChange={handlePageInputChange}
                  onBlur={handlePageInputBlur}
                  onKeyDown={handlePageInputKeyDown}
                  className="w-12 bg-gray-700 text-white text-center rounded px-1"
                />
                <span className="text-white">/ {numPages}</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleZoom(false)}
                  className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg"
                >
                  <FaSearchMinus />
                </button>
                <span className="text-white">{Math.round(scale * 100)}%</span>
                <button
                  onClick={() => handleZoom(true)}
                  className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg"
                >
                  <FaSearchPlus />
                </button>
              </div>
            </div>
          </div>

          {/* PDF Document */}
          <div 
            ref={containerRef}
            className="flex-1 overflow-y-auto px-4 w-full relative mt-16 flex-grow min-h-0"
            onScroll={handleScroll}
          >
            <Document
              file={pdfFile}
              onLoadSuccess={onDocumentLoadSuccess}
              options={options}
              className="flex flex-col items-center gap-4"
            >
              {Array.from(new Array(numPages), (_, index) => index + 1).map(pageNumber => (
                <div
                  key={pageNumber}
                  ref={observePage}
                  data-page-number={pageNumber}
                  className="pdf-page relative shadow-lg"
                  onMouseUp={() => handleTextSelect(pageNumber)}
                >
                  <Page
                    pageNumber={pageNumber}
                    scale={scale}
                    renderAnnotationLayer
                    renderTextLayer
                    className="shadow-lg"
                  />
                </div>
              ))}
            </Document>
          </div>
        </>
      ) : (
        // Upload prompt
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept="application/pdf"
            className="hidden"
            disabled={isUploading}
          />
          {isUploading ? (
            <div className="flex items-center gap-3">
              <FaSpinner className="animate-spin text-2xl text-blue-500" />
              <span className="text-white font-medium">Processing PDF...</span>
            </div>
          ) : (
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg flex items-center gap-2"
            >
              <FaUpload />
              Upload PDF
            </button>
          )}
        </div>
      )}

      {/* 檔案已存在提示彈窗 */}
      <CustomPopup
        open={showFileExistsPopup}
        onClose={() => setShowFileExistsPopup(false)}
        title="檔案已存在"
        showConfirm
        onConfirm={() => {
          if (pendingFileRef.current) {
            handleFileLoad(pendingFileRef.current);
          }
          setShowFileExistsPopup(false);
        }}
        confirmText="確認載入"
        cancelText="取消"
      >
        <p>檔案已存在且內容相同，將直接載入該檔案。</p>
      </CustomPopup>

      {/* 錯誤提示彈窗 */}
      <CustomPopup
        open={showErrorPopup}
        onClose={() => setShowErrorPopup(false)}
        title="錯誤"
      >
        <p>{errorMessage}</p>
      </CustomPopup>
    </div>
  );
};

export default PDFHandler;