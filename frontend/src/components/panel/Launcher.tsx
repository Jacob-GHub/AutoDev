import React from 'react'
import Gloop from '../gloop/Gloop'
import type { GloopMood } from '../gloop/moods'

type LauncherProps = {
  visible: boolean
  mood: GloopMood
  onOpen: () => void
}

/** Gloop peeking up from the bottom-right corner. Hover lifts him; click opens the panel. */
export default function Launcher({ visible, mood, onOpen }: LauncherProps) {
  return (
    <button
      className={`ad-launcher ${visible ? '' : 'is-hidden'}`}
      onClick={onOpen}
      aria-label="Ask Gloop about this repo"
      tabIndex={visible ? 0 : -1}
    >
      <Gloop mood={mood} size={96} />
    </button>
  )
}
