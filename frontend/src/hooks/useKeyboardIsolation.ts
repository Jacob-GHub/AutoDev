import { useEffect, useRef, type RefObject } from 'react'

const KEY_EVENTS = ['keydown', 'keypress', 'keyup'] as const

/**
 * Keeps keystrokes typed inside our UI from reaching GitHub's keyboard shortcuts.
 *
 * Why this is needed: when an event leaves a Shadow DOM, the browser "retargets" it,
 * so to GitHub the event seems to come from our host <div>, not from our <input>.
 * GitHub's shortcut handler only ignores keys typed into text fields, so it treats
 * "h" or "k" as a page shortcut and cancels the keystroke before the letter is typed.
 *
 * The fix: listen on window in the capture phase, which runs before every other
 * listener on the page, and stop any key event that came from inside our UI.
 * Typing itself still works, because inserting a character is the browser's
 * default action, not a listener.
 *
 * Trade-off: this also stops React's own onKeyDown handlers inside the UI, so
 * keyboard behavior for our UI lives here instead (e.g. Escape to close).
 */
export function useKeyboardIsolation(appRef: RefObject<HTMLElement>, onEscape: () => void) {
  const onEscapeRef = useRef(onEscape)
  onEscapeRef.current = onEscape

  useEffect(() => {
    const root = appRef.current?.getRootNode()
    if (!(root instanceof ShadowRoot)) return
    const host = root.host

    const isolate = (e: Event) => {
      if (!e.composedPath().includes(host)) return // a key pressed on GitHub itself
      if (e.type === 'keydown' && (e as KeyboardEvent).key === 'Escape') onEscapeRef.current()
      e.stopImmediatePropagation()
    }

    KEY_EVENTS.forEach((type) => window.addEventListener(type, isolate, true))
    return () => KEY_EVENTS.forEach((type) => window.removeEventListener(type, isolate, true))
  }, [appRef])
}