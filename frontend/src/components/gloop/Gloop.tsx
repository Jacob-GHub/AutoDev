import React, { useEffect, useId, useRef } from 'react'
import type { GloopMood } from './moods'
import { useBlink } from './useBlink'
import { useEyeTracking } from './useEyeTracking'

type GloopProps = {
  mood: GloopMood
  size?: number
}

export default function Gloop({ mood, size = 140 }: GloopProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const rootRef = useRef<SVGGElement>(null)

  useEyeTracking(svgRef, mood)
  useBlink(svgRef, mood)

  // Restart the hop animation every time Gloop enters "done".
  useEffect(() => {
    const root = rootRef.current
    if (mood !== 'done' || !root) return
    root.classList.remove('hop')
    void root.getBoundingClientRect() // force a reflow so the animation restarts
    root.classList.add('hop')
  }, [mood])

  const uid = useId().replace(/:/g, '')
  const id = (name: string) => `gloop-${uid}-${name}`
  const ref = (name: string) => `url(#${id(name)})`

  return (
    <div className="gloop" data-mood={mood} style={{ width: size, height: size * 1.05 }}>
      <div className="gloop-halo" />

      <svg ref={svgRef} className="gloop-svg" viewBox="0 0 200 210" fill="none" aria-hidden="true">
        <defs>
          <radialGradient
            id={id('body')}
            cx="0"
            cy="0"
            r="1"
            gradientUnits="userSpaceOnUse"
            gradientTransform="translate(83 98) scale(112 107)"
          >
            <stop offset="0" stopColor="#D6FF7E" />
            <stop offset="0.45" stopColor="#84F43E" />
            <stop offset="1" stopColor="#34C72F" />
          </radialGradient>
          <radialGradient
            id={id('foot-l')}
            cx="0"
            cy="0"
            r="1"
            gradientUnits="userSpaceOnUse"
            gradientTransform="translate(76 188) scale(21 11)"
          >
            <stop offset="0" stopColor="#6FE93A" />
            <stop offset="1" stopColor="#2FAE27" />
          </radialGradient>
          <radialGradient
            id={id('foot-r')}
            cx="0"
            cy="0"
            r="1"
            gradientUnits="userSpaceOnUse"
            gradientTransform="translate(124 188) scale(21 11)"
          >
            <stop offset="0" stopColor="#6FE93A" />
            <stop offset="1" stopColor="#2FAE27" />
          </radialGradient>
          <filter id={id('blur')} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" />
          </filter>
          <clipPath id={id('eye-l')}>
            <circle cx="70" cy="30" r="14" />
          </clipPath>
          <clipPath id={id('eye-r')}>
            <circle cx="130" cy="30" r="14" />
          </clipPath>
        </defs>

        <ellipse
          cx="100"
          cy="200"
          rx="52"
          ry="6"
          fill="#84F63E"
          fillOpacity="0.2"
          filter={ref('blur')}
        />

        <g ref={rootRef} className="gloop-root">
          <ellipse cx="76" cy="191" rx="15" ry="8" fill={ref('foot-l')} />
          <ellipse cx="124" cy="191" rx="15" ry="8" fill={ref('foot-r')} />
          <g className="gloop-squish">
            <EyeStalk side="l" cx={70} stem="M88 68C86 54 76 46 71 40" clip={ref('eye-l')} />
            <EyeStalk side="r" cx={130} stem="M112 68C114 54 124 46 129 40" clip={ref('eye-r')} />

            <path
              d="M100 58C142 58 168 92 170 136C172 172 145 192 100 192C55 192 28 172 30 136C32 92 58 58 100 58Z"
              fill={ref('body')}
            />
            <ellipse
              cx="72"
              cy="86"
              rx="17"
              ry="9"
              transform="rotate(-28 72 86)"
              fill="#FFFFFF"
              fillOpacity="0.32"
              filter={ref('blur')}
            />

            <ellipse cx="70" cy="113" rx="9" ry="5" fill="#FF6FA3" fillOpacity="0.5" />
            <ellipse cx="130" cy="113" rx="9" ry="5" fill="#FF6FA3" fillOpacity="0.5" />
            <path
              className="gloop-mouth"
              d="M92 104Q100 111 108 104"
              stroke="#0F3A0C"
              strokeWidth="3.2"
              strokeLinecap="round"
            />

            <g opacity="0.55">
              <path d="M100 138L100 172" stroke="#27A325" strokeWidth="3" strokeLinecap="round" />
              <path
                d="M100 164C100 154 113 156 113 147"
                stroke="#27A325"
                strokeWidth="3"
                strokeLinecap="round"
              />
              <circle cx="100" cy="138" r="4.5" fill="#27A325" />
              <circle cx="100" cy="172" r="4.5" fill="#27A325" />
              <circle cx="113" cy="145" r="4.5" fill="#27A325" />
            </g>
          </g>
        </g>
      </svg>
    </div>
  )
}

type EyeStalkProps = {
  side: 'l' | 'r'
  cx: number
  stem: string
  clip: string
}

function EyeStalk({ side, cx, stem, clip }: EyeStalkProps) {
  return (
    <g className={`gloop-stalk-${side}`}>
      <g className={`gloop-sway-${side}`}>
        <path d={stem} stroke="#7FF03F" strokeWidth="7" strokeLinecap="round" />
        <g className={`gloop-eye gloop-eye-${side}`}>
          <circle
            className="gloop-eyeball"
            cx={cx}
            cy="30"
            r="14"
            fill="#F6FFF0"
            stroke="#46C82E"
            strokeWidth="1.5"
          />
          <g className="gloop-pupil">
            <circle cx={cx} cy="30" r="6.2" fill="#101510" />
            <circle cx={cx + 2.2} cy="27.6" r="1.9" fill="#FFFFFF" />
          </g>
          {/* Eyelids wait just outside the eyeball and slide in to narrow the eyes. */}
          <g clipPath={clip}>
            <rect
              className="gloop-lid-top"
              x={cx - 16}
              y="-14"
              width="32"
              height="30"
              fill="#7CEE3D"
            />
            <rect
              className="gloop-lid-bottom"
              x={cx - 16}
              y="44"
              width="32"
              height="30"
              fill="#7CEE3D"
            />
          </g>
        </g>
      </g>
    </g>
  )
}
