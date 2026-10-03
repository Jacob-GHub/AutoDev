import { useCallback, useEffect, useRef, useState } from 'react'
import { askStream } from '../api/askStream'
import type { AgentAnswer } from '../api/types'
import { SETTLE_MS, type GloopMood } from '../components/gloop/moods'

export type Turn = {
  id: number
  question: string
  answer?: AgentAnswer
  error?: string
}

const IDLE_CAPTION = 'Ask me anything about this repo'

/**
 * Owns the conversation: the list of turns, the server conversation id,
 * and Gloop's mood + caption, which are driven by the stream's events.
 */
export function useAsk() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [mood, setMood] = useState<GloopMood>('idle')
  const [caption, setCaption] = useState(IDLE_CAPTION)
  const [busy, setBusy] = useState(false)

  const conversationId = useRef<string | null>(null)
  const repoOfConversation = useRef<string | null>(null)
  const abort = useRef<AbortController | null>(null)
  const settleTimer = useRef<number| undefined>(undefined)
  const nextId = useRef(0)

  const showMood = useCallback((next: GloopMood, text: string) => {
    window.clearTimeout(settleTimer.current)
    setMood(next)
    setCaption(text)
    const settleAfter = SETTLE_MS[next]
    if (settleAfter) {
      settleTimer.current = window.setTimeout(() => {
        setMood('idle')
        setCaption(IDLE_CAPTION)
      }, settleAfter)
    }
  }, [])

  const updateTurn = (id: number, patch: Partial<Turn>) =>
    setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)))

  const reset = useCallback(() => {
    abort.current?.abort()
    conversationId.current = null
    repoOfConversation.current = null
    setTurns([])
    setBusy(false)
    showMood('idle', IDLE_CAPTION)
  }, [showMood])

  const ask = useCallback(
    async (question: string, repoUrl: string) => {
      // A conversation belongs to one repo; start fresh after navigating to another.
      if (repoOfConversation.current && repoOfConversation.current !== repoUrl) {
        conversationId.current = null
        setTurns([])
      }
      repoOfConversation.current = repoUrl

      const id = nextId.current++
      setTurns((prev) => [...prev, { id, question }])
      setBusy(true)
      showMood('reading', 'Syncing the repository…')

      const controller = new AbortController()
      abort.current = controller

      try {
        for await (const event of askStream(
          { question, repoUrl, conversationId: conversationId.current },
          controller.signal,
        )) {
          switch (event.status) {
            case 'indexing':
              showMood('reading', event.message)
              break
            case 'thinking':
              showMood('thinking', 'Thinking through the code…')
              break
            case 'done':
              conversationId.current = event.conversationId
              updateTurn(id, { answer: event.answer })
              showMood('done', 'Found it.')
              break
            case 'error':
              updateTurn(id, { error: event.message })
              showMood('error', 'Hmm, something went wrong.')
              break
          }
        }
      } catch (err) {
        if (controller.signal.aborted) return // cleared by the user
        const message = err instanceof Error ? err.message : 'Something went wrong.'
        updateTurn(id, { error: message })
        showMood('error', "I couldn't reach the server.")
      } finally {
        if (abort.current === controller) {
          abort.current = null
          setBusy(false)
        }
      }
    },
    [showMood],
  )

  // Cancel any in-flight request when the app unmounts.
  useEffect(() => () => {
    abort.current?.abort()
    window.clearTimeout(settleTimer.current)
  }, [])

  return { turns, mood, caption, busy, ask, reset }
}
