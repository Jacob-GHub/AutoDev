// components/responses/ToolCallTrace.jsx
import React, { useState } from 'react'

const toolLabels = {
  find_function_location: 'Located',
  get_callers: 'Found callers of',
  get_called_functions: 'Found calls from',
  get_function_code: 'Read code of',
  semantic_search: 'Searched for',
  get_repo_structure: 'Read repo structure',
}

const ToolCallTrace = ({ toolCalls }) => {
  const [expanded, setExpanded] = useState(false)

  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className="mb-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-white/40 hover:text-white/60 bg-white/5 border border-white/10 rounded px-3 py-1 transition-colors"
      >
        <span>{expanded ? '▼' : '▶'}</span>
        <span>
          Explored {toolCalls.length} step{toolCalls.length > 1 ? 's' : ''}
        </span>
      </button>

      {expanded && (
        <div className="mt-2 pl-3 border-l border-white/10 space-y-2">
          {toolCalls.map((tc, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="text-white/30 text-xs">{idx + 1}.</span>
              <span className="text-white/60 text-xs">{toolLabels[tc.tool] || tc.tool}</span>
              <span className="text-white/80 text-xs font-mono bg-white/5 px-1.5 py-0.5 rounded">
                {Object.values(tc.args).join(', ')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ToolCallTrace
