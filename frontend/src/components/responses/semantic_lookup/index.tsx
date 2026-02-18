import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { toast } from 'react-hot-toast'

const SemanticLookup = ({ answer }) => {
  if (!answer || !Array.isArray(answer) || answer.length === 0) {
    return <div className="text-sm text-gray-400 italic">No summary data available.</div>
  }

  const handleCopy = (code) => {
    navigator.clipboard.writeText(code)
    toast.success('Copied to clipboard!')
  }

  return (
    <div className="mt-4 space-y-6 overflow-y-auto pr-1">
      {answer.map((result, idx) => (
        <div
          key={idx}
          className="relative z-0 bg-white/5 border border-white/10 rounded-xl p-4 shadow-md transition hover:shadow-lg"
        >
          <div className="flex justify-between items-center mb-2 text-sm text-white/80">
            <span>
              📄 <span className="font-mono text-white">{result.file}</span>
            </span>
            <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full text-xs font-medium">
              🔎 Score: {result?.score?.toFixed(2)}
            </span>
          </div>

          <div className="relative bg-[#282c34] border border-white/10 rounded-xl p-4 shadow-md transition hover:shadow-lg">
            <SyntaxHighlighter
              language="python"
              style={oneDark}
              wrapLongLines
              customStyle={{
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
                padding: '1rem',
                background: '#282c34',
                margin: 0,
              }}
            >
              {result.code}
            </SyntaxHighlighter>

            <button
              onClick={() => handleCopy(result.code)}
              className="absolute top-2 right-2 bg-white/10 hover:bg-white/20 text-xs text-white px-2 py-1 rounded hidden group-hover:block"
            >
              Copy
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default SemanticLookup
