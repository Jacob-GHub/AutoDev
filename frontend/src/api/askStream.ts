import { API_BASE } from './config'
import type { AskRequest, StreamEvent } from './types'

/**
 * Sends a question and yields each server-sent event as it arrives.
 *
 *   for await (const event of askStream(req, signal)) { ... }
 *
 * Pass an AbortSignal to cancel the request (e.g. when the user clears the chat).
 */
export async function* askStream(
  request: AskRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.error || `Server returned ${response.status}`)
  }
  if (!response.body) throw new Error('Server sent an empty response')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // A network chunk can end mid-event, so only parse complete events
    // (terminated by a blank line) and keep the remainder for the next chunk.
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const event of events) {
      for (const line of event.split('\n')) {
        if (line.startsWith('data: ')) {
          yield JSON.parse(line.slice(6)) as StreamEvent
        }
      }
    }
  }
}
