import React from 'react'
import ReactMarkdown from 'react-markdown'

/** The agent's answer, rendered from markdown. Styled by .ad-answer in panel.styles.ts. */
export default function AnswerDisplay({ answer }: { answer: string }) {
  return (
    <div className="ad-answer">
      <ReactMarkdown>{answer}</ReactMarkdown>
    </div>
  )
}
