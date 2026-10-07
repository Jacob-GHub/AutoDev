import { useEffect, useRef, type RefObject } from 'react'
import { FIXED_GAZE, type GloopMood } from './moods'

const MAX_LOOK = 5 // how far a pupil can move from the center of its eye, in SVG units

/**
 * Moves Gloop's pupils toward the cursor every frame,
 * or to a fixed gaze in moods like reading and thinking.
 */
export function useEyeTracking(svgRef: RefObject<SVGSVGElement>, mood: GloopMood) {
  const moodRef = useRef(mood)
  moodRef.current = mood

  useEffect(() => {
    let mouse: { x: number; y: number } | null = null
    let frame = 0

    const onMove = (e: PointerEvent) => { mouse = { x: e.clientX, y: e.clientY } }
    const onLeave = () => { mouse = null }

    const tick = () => {
      const fixed = FIXED_GAZE[moodRef.current]

      svgRef.current?.querySelectorAll<SVGGElement>('.gloop-eye').forEach((eye) => {
        const eyeball = eye.querySelector('.gloop-eyeball')
        const pupil = eye.querySelector<SVGGElement>('.gloop-pupil')
        if (!eyeball || !pupil) return

        let x = 0
        let y = 0
        if (fixed) {
          ;({ x, y } = fixed)
        } else if (mouse) {
          // Direction from the center of this eye to the cursor, on screen.
          const rect = eyeball.getBoundingClientRect()
          const dx = mouse.x - (rect.left + rect.width / 2)
          const dy = mouse.y - (rect.top + rect.height / 2)
          const dist = Math.hypot(dx, dy)
          // Keep the direction, but cap the distance so the pupil stays inside the eye.
          const reach = Math.min(MAX_LOOK, dist / 40)
          if (dist > 0) {
            x = (dx / dist) * reach
            y = (dy / dist) * reach
          }
        }
        pupil.style.transform = `translate(${x}px, ${y}px)`
      })

      frame = requestAnimationFrame(tick)
    }

    window.addEventListener('pointermove', onMove)
    document.addEventListener('pointerleave', onLeave)
    frame = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('pointermove', onMove)
      document.removeEventListener('pointerleave', onLeave)
    }
  }, [svgRef])
}
