import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

const FunctionSummary = ({ answer }) => {
  if (!Array.isArray(answer) || answer.length === 0 || !answer[0].summary) {
    return <div className="text-sm text-gray-400 italic">No summary data available.</div>
  }

  return (
    <div className="mt-4 space-y-6 overflow-y-auto pr-1 max-h-[300px]">
      {answer.map((result, idx) => (
        <div
          key={idx}
          className="bg-white/5 border border-white/10 rounded-xl p-4 shadow-md space-y-3 text-sm transition hover:shadow-lg"
        >
          <div className="text-white/90 font-medium">
            📄 File: <span className="font-mono text-blue-400">{result.file}</span>
          </div>

          <div className="text-white/90">
            🔧 Function: <span className="font-mono text-purple-400">{result.function}</span>
          </div>

          <div className="italic text-white/70">💡 {result.summary}</div>

          {result.code ? (
            <SyntaxHighlighter
              language="python"
              style={oneDark}
              wrapLongLines
              customStyle={{
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
                padding: '1rem',
                margin: 0,
                background: '#282c34',
              }}
            >
              {result.code}
            </SyntaxHighlighter>
          ) : (
            <div className="text-gray-400 italic">No code available.</div>
          )}
        </div>
      ))}
    </div>
  )
}

export default FunctionSummary
