import React, { forwardRef } from 'react'
import type { Turn } from '../../hooks/useAsk'
import Gloop from '../gloop/Gloop'
import type { GloopMood } from '../gloop/moods'
import Composer from './Composer'
import MessageList from './MessageList'

type PanelProps = {
  open: boolean
  mood: GloopMood
  caption: string
  turns: Turn[]
  busy: boolean
  repoUrl: string | null
  onAsk: (question: string) => void
  onClear: () => void
  onClose: () => void
}

/** The glass side panel. data-mood drives the border light and outer glow. */
const Panel = forwardRef<HTMLInputElement, PanelProps>(
  ({ open, mood, caption, turns, busy, repoUrl, onAsk, onClear, onClose }, inputRef) => (
    <section
      className={`ad-panel ${open ? 'is-open' : ''}`}
      data-mood={mood}
      aria-label="AutoDev"
      aria-hidden={!open}
    >
      <header className="ad-header">
        <div className="ad-header-actions">
          {turns.length > 0 && (
            <button className="ad-text-btn" onClick={onClear}>Clear</button>
          )}
          <button className="ad-icon-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Only mount Gloop while open, so his animation loop isn't running off-screen. */}
        {open && <Gloop mood={mood} size={124} />}
        <div className="ad-name">Gloop</div>
        <div className="ad-caption" aria-live="polite">{caption}</div>
      </header>

      <MessageList turns={turns} />

      <Composer
        ref={inputRef}
        disabled={busy}
        disabledReason={repoUrl ? undefined : 'Open a repository to ask about it'}
        onSubmit={onAsk}
      />
    </section>
  ),
)

export default Panel
