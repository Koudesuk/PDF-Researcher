import * as React from 'react';
import { useState } from 'react';
import PDFHandler from './components/pdf-handler';
import Translate from './components/translate';
import Chat from './components/chat';
import { ScreenShotController, ScreenShot } from 'react-component-screenshot';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';

const App: React.FC = () => {
  const controller = new ScreenShotController();
  const [isCapturing, setIsCapturing] = useState(false);
  const [currentPdfName, setCurrentPdfName] = useState<string | null>(null);

  const handleScreenshot = async (loadingToastId: string) => {
    try {
      // Get the screenshot as base64
      const base64Image = await controller.capture();
      
      if (base64Image) {
        // Remove the data URL prefix to get just the base64 string
        const base64Data = base64Image.split(',')[1];

        // Send to backend
        const response = await axios.post('http://localhost:9999/upload-screenshot', {
          screenshot: base64Data
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        console.log('Screenshot uploaded:', response.data);
        
        // Dismiss the loading toast
        toast.dismiss(loadingToastId);
        
        // Show success toast
        toast.success('截圖已儲存！', {
          duration: 3000,
          position: 'bottom-right',
          style: {
            background: '#333',
            color: '#fff',
          },
        });
      }
      
    } catch (error) {
      console.error('Error taking/uploading screenshot:', error);
      
      // Dismiss the loading toast
      toast.dismiss(loadingToastId);
      
      // Show error toast
      toast.error('截圖失敗', {
        duration: 3000,
        position: 'bottom-right',
        style: {
          background: '#333',
          color: '#fff',
        },
      });
    } finally {
      setIsCapturing(false);
    }
  };

  const startScreenshotMode = () => {
    setIsCapturing(true);
    
    // Show loading toast and get its ID
    const loadingToastId = toast.loading('擷取圖片中...', {
      position: 'bottom-right',
      style: {
        background: '#333',
        color: '#fff',
      },
    });
    
    // Add a small delay before capture
    setTimeout(() => {
      controller.capture()
        .then((base64Image) => {
          if (base64Image) {
            handleScreenshot(loadingToastId);
          } else {
            // Handle the case where capture returns null
            toast.dismiss(loadingToastId);
            toast.error('截圖失敗', {
              duration: 3000,
              position: 'bottom-right',
              style: {
                background: '#333',
                color: '#fff',
              },
            });
            setIsCapturing(false);
          }
        })
        .catch((error) => {
          console.error('Capture error:', error);
          toast.dismiss(loadingToastId);
          toast.error('截圖失敗', {
            duration: 3000,
            position: 'bottom-right',
            style: {
              background: '#333',
              color: '#fff',
            },
          });
          setIsCapturing(false);
        });
    }, 100);
  };

  const handleFileLoaded = (file: File) => {
    setCurrentPdfName(file.name);
  };

  const handlePdfClose = () => {
    // 只需要重置 currentPdfName，這樣 Chat 組件會自動清空顯示的內容
    setCurrentPdfName(null);
  };

  return (
    <ScreenShot controller={controller}>
      <div className="h-screen bg-gray-900 overflow-hidden">
        <Toaster
          toastOptions={{
            className: 'dark:bg-gray-800 dark:text-white',
            style: {
              background: '#333',
              color: '#fff',
            },
          }}
        />
        
        <div className="container mx-auto h-full p-6 flex gap-6">
          {/* Left Panel - 60% */}
          <div className="w-[60%] h-full">
            <PDFHandler
              isCapturing={isCapturing}
              onStartCapture={startScreenshotMode}
              onFileLoaded={handleFileLoaded}
              onClose={handlePdfClose}
            />
          </div>

          {/* Right Panel - 40% */}
          <div className="w-[40%] h-full flex flex-col gap-6">
            {/* Translation Panel - 20% */}
            <div className="h-[20%]">
              <Translate />
            </div>
            {/* Chat Panel - 80% */}
            <div className="h-[80%]">
              <Chat currentPdf={currentPdfName} />
            </div>
          </div>
        </div>
      </div>
    </ScreenShot>
  );
};

export default App;