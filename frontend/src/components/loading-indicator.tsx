import React from 'react';

const LoadingIndicator: React.FC = () => {
  return (
    <div className="flex items-center space-x-2 text-gray-400">
      <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
      <span className="text-sm">processing...</span>
    </div>
  );
};

export default LoadingIndicator;