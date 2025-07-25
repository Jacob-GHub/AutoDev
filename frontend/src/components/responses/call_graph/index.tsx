import React from 'react'

const CallGraph = ({ answer }) => {
  if (!Array.isArray(answer) || answer.length === 0) {
    return <div className="text-sm text-gray-400 italic mt-4">No call graph data available.</div>
  }

  return (
    <div className="mt-4 space-y-6 pr-1">
      {answer.map((result, idx) => (
        <div
          key={idx}
          className="bg-white/5 border border-white/10 rounded-xl p-4 shadow-md transition hover:shadow-lg"
        >
          <div className="text-white/90 font-medium mb-3 text-sm">
            🔍 Callers of{' '}
            <span className="font-mono bg-white/10 px-2 py-0.5 rounded text-white">
              {result.target}
            </span>
          </div>

          <div className="space-y-2">
            {result?.callers?.length > 0 ? (
              result.callers.map((caller, i) => (
                <div key={i} className="pl-4 border-l-2 border-blue-500 text-xs text-white/70">
                  📄 <span className="font-mono text-white">{caller}</span>
                </div>
              ))
            ) : (
              <div className="text-xs text-gray-400 italic">No callers found.</div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default CallGraph
