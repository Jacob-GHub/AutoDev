import React, { forwardRef, useState } from 'react'

type ComposerProps = {
  disabled: boolean
  /** Shown instead of the input's placeholder when asking isn't possible. */
  disabledReason?: string
  onSubmit: (question: string) => void
}

const Composer = forwardRef<HTMLInputElement, ComposerProps>(
  ({ disabled, disabledReason, onSubmit }, ref) => {
    const [value, setValue] = useState('')

    const submit = (e: React.FormEvent) => {
      e.preventDefault()
      const question = value.trim()
      if (!question || disabled) return
      onSubmit(question)
      setValue('')
    }

    return (
      <form className="ad-composer" onSubmit={submit}>
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={disabledReason ?? 'Ask Gloop about this repo…'}
          aria-label="Question"
          disabled={Boolean(disabledReason)}
        />
        <button type="submit" disabled={disabled || !value.trim()} aria-label="Send">
          ↑
        </button>
      </form>
    )
  },
)

export default Composer
