import React, { useState } from 'react'
import type { ToolCall } from '../../api/types'

const TOOL_LABELS: Record<string, string> = {
  find_function_location: 'Located',
  get_callers: 'Found callers of',
  get_called_functions: 'Found calls from',
  get_function_code: 'Read',
  semantic_search: 'Searched for',
  get_repo_structure: 'Read the repo structure',
}

const describeArgs = (args: Record<string, unknown>) =>
  Object.values(args ?? {})
    .map(String)
    .join(', ')

/** A collapsible list of the steps the agent took to reach its answer. */
export default function ToolCallTrace({ toolCalls }: { toolCalls: ToolCall[] }) {
  const [expanded, setExpanded] = useState(false)
  if (!toolCalls?.length) return null

  return (
    <div className="ad-trace">
      <button
        className={`ad-trace-toggle ${expanded ? 'is-expanded' : ''}`}
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span className="ad-trace-dot" />
        Explored {toolCalls.length} step{toolCalls.length === 1 ? '' : 's'}
        <span className="ad-trace-chevron" aria-hidden="true">
          &gt;
        </span>
      </button>

      {expanded && (
        <ol className="ad-trace-steps">
          {toolCalls.map((call, i) => {
            const args = describeArgs(call.args)
            return (
              <li key={i}>
                <span>{TOOL_LABELS[call.tool] ?? call.tool}</span>
                {args && <code>{args}</code>}
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
