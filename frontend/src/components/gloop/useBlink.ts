import { useEffect, useRef, type RefObject } from 'react'
import type { GloopMood } from './moods'

/** Blinks at random intervals, with an occasional double blink. */
export function useBlink(svgRef: RefObject<SVGSVGElement>, mood: GloopMood) {
  const moodRef = useRef(mood)
  moodRef.current = mood

  useEffect(() => {
    const timers: number[] = []

    const blink = () => {
      svgRef.current?.classList.add('blinking')
      timers.push(window.setTimeout(() => svgRef.current?.classList.remove('blinking'), 120))
    }

    const schedule = () => {
      timers.push(
        window.setTimeout(() => {
          if (moodRef.current !== 'done') { // happy squint eyes look odd mid-blink
            blink()
            if (Math.random() < 0.2) timers.push(window.setTimeout(blink, 260))
          }
          schedule()
        }, 2200 + Math.random() * 4000),
      )
    }

    schedule()
    return () => timers.forEach(clearTimeout)
  }, [svgRef])
}
