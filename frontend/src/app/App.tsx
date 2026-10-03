import React, { useCallback, useEffect, useRef, useState } from 'react'
import Launcher from '../components/panel/Launcher'
import Panel from '../components/panel/Panel'
import { useAsk } from '../hooks/useAsk'
import { useKeyboardIsolation } from '../hooks/useKeyboardIsolation'
import { getRepoUrl } from '../utils/github'

export default function App() {
  const [open, setOpen] = useState(false)
  const [repoUrl, setRepoUrl] = useState(getRepoUrl)
  const { turns, mood, caption, busy, ask, reset } = useAsk()
  const inputRef = useRef<HTMLInputElement>(null)
  const appRef = useRef<HTMLDivElement | null>(null)

  // Keys typed in our UI must not trigger GitHub's shortcuts (Escape still closes the panel).
  useKeyboardIsolation(appRef, () => setOpen(false))

  // GitHub navigates without full page loads, so re-read the repo on each navigation.
  useEffect(() => {
    const update = () => setRepoUrl(getRepoUrl())
    document.addEventListener('turbo:load', update)
    window.addEventListener('popstate', update)
    return () => {
      document.removeEventListener('turbo:load', update)
      window.removeEventListener('popstate', update)
    }
  }, [])

  // Escape pressed on GitHub's page (outside our UI) also closes the panel.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // Focus the input once the panel has slid in.
  useEffect(() => {
    if (!open) return
    const t = window.setTimeout(() => inputRef.current?.focus(), 350)
    return () => window.clearTimeout(t)
  }, [open])

  const handleAsk = useCallback(
    (question: string) => {
      const repo = getRepoUrl()
      if (repo) ask(question, repo)
    },
    [ask],
  )

  return (
    <div className="ad-app" ref={appRef}>
      <Launcher visible={!open} mood={mood} onOpen={() => setOpen(true)} />
      <Panel
        ref={inputRef}
        open={open}
        mood={mood}
        caption={caption}
        turns={turns}
        busy={busy}
        repoUrl={repoUrl}
        onAsk={handleAsk}
        onClear={reset}
        onClose={() => setOpen(false)}
      />
    </div>
  )
}
