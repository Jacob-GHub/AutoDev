import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

const SemanticLookup = ({ answer }) => {
  return (
    <div className="mt-4 space-y-4 max-h-[300px] overflow-y-auto">
      {answer.map((result, idx) => (
        <div key={idx} className="bg-gray-100 p-3 rounded border border-gray-300 text-sm">
          <div className="font-medium text-gray-700 mb-1">
            📄 File: <span className="font-mono">{result.file}</span>
          </div>
          <div className="text-xs text-gray-500 mb-2">
            🔎 Similarity Score: <span className="font-mono">{result.score}</span>
          </div>
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
      ))}
    </div>
  )
}
export default SemanticLookup
