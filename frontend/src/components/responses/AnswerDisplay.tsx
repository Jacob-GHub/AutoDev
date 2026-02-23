// components/responses/AnswerDisplay.jsx
import React from 'react'
import ReactMarkdown from 'react-markdown'

const AnswerDisplay = ({ answer }) => {
  return (
    <div className="mb-4 p-3 bg-white/10 rounded-lg text-sm text-white leading-relaxed prose prose-invert prose-sm max-w-none">
      <ReactMarkdown
        components={{
          h3: ({ children }) => <h3 className="text-white font-semibold mt-3 mb-1">{children}</h3>,
          h2: ({ children }) => <h2 className="text-white font-semibold mt-4 mb-2">{children}</h2>,
          strong: ({ children }) => (
            <strong className="text-white font-semibold">{children}</strong>
          ),
          li: ({ children }) => <li className="ml-4 list-disc text-white/80">{children}</li>,
          p: ({ children }) => <p className="mb-2 text-white/90">{children}</p>,
          code: ({ children }) => (
            <code className="bg-white/10 px-1 rounded font-mono text-blue-300 text-xs">
              {children}
            </code>
          ),
        }}
      >
        {answer}
      </ReactMarkdown>
    </div>
  )
}

export default AnswerDisplay
