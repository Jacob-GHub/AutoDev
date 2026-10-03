export type ToolCall = {
  tool: string
  args: Record<string, unknown>
  result: unknown
}

export type AgentAnswer = {
  type: string
  question: string
  answer: string
  tool_calls: ToolCall[]
}

/** One server-sent event from POST /api/ask. */
export type StreamEvent =
  | { status: 'indexing' | 'thinking'; message: string }
  | { status: 'done'; answer: AgentAnswer; conversationId: string }
  | { status: 'error'; message: string }

export type AskRequest = {
  question: string
  repoUrl: string
  conversationId: string | null
}
