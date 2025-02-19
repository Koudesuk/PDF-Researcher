import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <div className="markdown-content overflow-hidden">
      <ReactMarkdown
        className="prose prose-invert max-w-none prose-compact"
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h1: ({ node, ...props }) => <h1 className="text-xl font-bold mb-2" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-lg font-bold mb-2" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-base font-bold mb-2" {...props} />,
          h4: ({ node, ...props }) => <h4 className="text-sm font-bold mb-2" {...props} />,
          h5: ({ node, ...props }) => <h5 className="text-xs font-bold mb-2" {...props} />,
          h6: ({ node, ...props }) => <h6 className="text-[10px] font-bold mb-2" {...props} />,
          p: ({ children }) => <p className="mb-2">{children}</p>
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
