export type GloopMood = 'idle' | 'reading' | 'thinking' | 'done' | 'error'

/**
 * Where the pupils look in moods that don't follow the cursor,
 * in SVG units, relative to the center of each eye.
 */
export const FIXED_GAZE: Partial<Record<GloopMood, { x: number; y: number }>> = {
  reading: { x: 0, y: 4.5 },
  thinking: { x: 3.5, y: -3.5 },
  error: { x: -2.5, y: 3.5 },
}

/** How long a mood lingers before Gloop relaxes back to idle. */
export const SETTLE_MS: Partial<Record<GloopMood, number>> = {
  done: 2800,
  error: 4500,
}
