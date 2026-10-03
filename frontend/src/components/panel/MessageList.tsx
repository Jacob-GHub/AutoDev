import React, { useEffect, useRef } from 'react'
import type { Turn } from '../../hooks/useAsk'
import AnswerDisplay from '../responses/AnswerDisplay'
import ToolCallTrace from '../responses/ToolCallTrace'

export default function MessageList({ turns }: { turns: Turn[] }) {
  const endRef = useRef<HTMLDivElement>(null)

  // Keep the newest message in view.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turns])

  if (turns.length === 0) {
    return (
      <div className="ad-messages ad-empty">
        <p>Try “How does this project start up?” or “Where is authentication handled?”</p>
      </div>
    )
  }

  return (
    <div className="ad-messages">
      {turns.map((turn) => (
        <div key={turn.id} className="ad-turn">
          <div className="ad-question">{turn.question}</div>
          {turn.answer && (
            <div className="ad-reply">
              <ToolCallTrace toolCalls={turn.answer.tool_calls} />
              <AnswerDisplay answer={turn.answer.answer} />
            </div>
          )}
          {turn.error && <p className="ad-error">{turn.error}</p>}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}
