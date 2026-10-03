import React from 'react'
import { createRoot } from 'react-dom/client'
import App from '../app/App'
import { appStyles } from '../app/styles'

const HOST_ID = 'autodev-root'

/**
 * Mounts AutoDev inside a Shadow DOM: GitHub's CSS can't style our UI,
 * and our CSS can't leak onto GitHub's page.
 */
function mount() {
  if (document.getElementById(HOST_ID)) return // already mounted

  // The rotating border light animates a custom property, which only works once it's
  // registered as an angle. Registration is page-wide and throws if repeated.
  try {
    ;(
      CSS as typeof CSS & {
        registerProperty: (property: {
          name: string
          syntax: string
          inherits: boolean
          initialValue: string
        }) => void
      }
    ).registerProperty({
      name: '--ad-angle',
      syntax: '<angle>',
      inherits: false,
      initialValue: '0deg',
    })
  } catch {
    // already registered
  }

  const host = document.createElement('div')
  host.id = HOST_ID
  // Attach to <html> rather than <body>: GitHub swaps out <body> when navigating.
  document.documentElement.appendChild(host)

  const shadow = host.attachShadow({ mode: 'open' })
  const style = document.createElement('style')
  style.textContent = appStyles
  shadow.appendChild(style)

  const container = document.createElement('div')
  shadow.appendChild(container)
  createRoot(container).render(<App />)
}

mount()
