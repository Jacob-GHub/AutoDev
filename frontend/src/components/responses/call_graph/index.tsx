import React from 'react'

const CallGraph = ({ answer }) => {
  if (!Array.isArray(answer) || answer.length === 0) {
    return <div>No summary data available.</div>
  }
  return (
    <div className="mt-4 space-y-4 max-h-[300px] overflow-y-auto">
      {answer?.map((result, idx) => (
        <div key={idx} className="bg-gray-100 p-3 rounded border border-gray-300 text-sm">
          <div className="text-gray-700 font-medium mb-2">
            🔍 Callers of <span className="font-mono">{result.target}</span>:
          </div>
          {result?.callers?.map((caller, i) => (
            <div
              key={i}
              className="ml-2 pl-2 border-l-2 border-blue-400 text-xs text-gray-600 mb-1"
            >
              📄 <span className="font-mono text-gray-700">{caller}</span> →{' '}
              {/* <span className="font-mono text-gray-700">{caller.function}</span> at line{' '}
              <span className="font-mono text-gray-700">{caller.line}</span> */}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export default CallGraph
