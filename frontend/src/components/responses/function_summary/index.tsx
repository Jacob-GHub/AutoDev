import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

const FunctionSummary = ({ answer }) => {
  if (!answer || !Array.isArray(answer)) return null

  return (
    <div className="mt-4 space-y-4 max-h-[300px] overflow-y-auto">
      {answer.map((result, idx) => (
        <div key={idx} className="bg-gray-100 p-3 rounded border border-gray-300 text-sm">
          <div key={idx} className="bg-gray-100 p-3 rounded border border-gray-300 text-sm">
            <div className="font-medium text-gray-700 mb-1">
              📄 File: <span className="font-mono">{result.file}</span>
            </div>
            <div className="mb-2 text-sm text-gray-700">
              🔧 Function: <span className="font-mono">{result.function}</span>
            </div>
            <div className="text-gray-600 italic mb-2">💡 {result.summary}</div>
            <SyntaxHighlighter
              language="python"
              style={oneDark}
              wrapLongLines
              customStyle={{
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
                padding: '1rem',
                background: '#282c34',
              }}
            >
              {result.code}
            </SyntaxHighlighter>
          </div>
        </div>
      ))}
    </div>
  )
}

export default FunctionSummary
