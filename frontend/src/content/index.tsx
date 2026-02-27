import React, { useEffect, useRef, useState } from 'react'
import ReactDOM from 'react-dom'
import '../style/btn.less'
import '../style/index.css'
import SemanticLookup from '../components/responses/semantic_lookup/index'
import RepoSummary from '../components/responses/repo_summary'
import FunctionSummary from '../components/responses/function_summary'
import CallGraph from '../components/responses/call_graph'
import { createRoot } from 'react-dom/client'
import AnswerDisplay from '../components/responses/AnswerDisplay'
import ToolCallTrace from '../components/responses/ToolCallTrace'

const root = document.createElement('div')
root.id = 'crx-root'
document.body.appendChild(root)

const App = () => {
  const [showModal, setShowModal] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState(null)
  const [answerList, setAnswerList] = useState([])
  const [submitted, setSubmitted] = useState(false)
  const [questionType, setQuestionType] = useState('semantic_lookup')
  const [validAnswer, setValidAnswer] = useState(false)
  const [open, setOpen] = useState(false)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingStatus, setLoadingStatus] = useState('')
  const latestAnswerRef = useRef(null)
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  const componentsMap = {
    semantic_lookup: SemanticLookup,
    repo_summary: RepoSummary,
    function_summary: FunctionSummary,
    call_graph: CallGraph,
  }

  useEffect(() => {
    if (latestAnswerRef.current) {
      latestAnswerRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [answerList])

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    if (open) {
      setTimeout(() => document.querySelector('input')?.focus(), 100)
    }
  }, [open])

  const SelectedComponent = componentsMap[questionType]

  const extractRepoUrl = () => {
    const match = window.location.pathname.match(/^\/([^/]+)\/([^/]+)/)
    if (!match) return null
    return `https://github.com/${match[1]}/${match[2]}.git`
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoadingStatus('Cloning Repository...')
    setLoading(true)
    setSubmitted(false)

    try {
      const response = await fetch('http://127.0.0.1:3000/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: inputValue,
          repoUrl: extractRepoUrl(),
          history: history,
        }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const event = decoder.decode(value)
        console.log('Received: ', event)

        const lines = event.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.replace('data: ', ''))
            console.log(data.status)
            if (data.status == 'done') {
              setAnswer(data.answer)
              setAnswerList((prev) => [...prev, data.answer])
              setHistory((prev) => [
                ...prev,
                { role: 'user', content: inputValue },
                { role: 'assistant', content: data.answer.answer },
              ])
              setQuestionType(data.answer.type)
              setError(null)
            } else if (data.status === 'error') {
              setError(data.message)
              setAnswer(null)
            } else {
              setLoadingStatus(data.message)
            }
          }
        }
      }
    } catch (err) {
      setError('Something went wrong. Please try again.')
      console.error('Error:', err)
      setAnswer(null)
    }

    setLoading(false)
    setLoadingStatus('')
    setSubmitted(true)
  }

  const handleAnswer = async (e) => {
    e.preventDefault()
  }

  return (
    <>
      {/* Floating Button */}
      {!open && (
        <button
          onClick={() => setOpen(!open)}
          className="fixed bottom-10 right-10 z-[9999] bg-neutral-100 text-black hover:bg-neutral-200 px-4 py-3 rounded-full shadow-lg backdrop-blur hover:bg-white transition-colors"
        >
          Ask Repo Question
        </button>
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 right-0 h-full w-[400px] backdrop-blur-md bg-black bg-opacity-50 text-white shadow-2xl border-l border-white/10 z-[9998] transition-transform duration-300 ease-in-out flex flex-col ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-6 pb-4 border-b border-white/10">
          <h2 className="text-lg font-semibold">Ask a question</h2>
          <div className="flex gap-2 items-center">
            {answerList.length > 0 && (
              <button
                onClick={() => {
                  setAnswerList([])
                  setHistory([])
                }}
                className="text-white/50 text-xs hover:text-white"
              >
                Clear
              </button>
            )}
            <button
              onClick={() => setOpen(false)}
              className="text-white text-xl hover:text-red-400"
            >
              ✖
            </button>
          </div>
        </div>

        {/* Scrollable answers */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {answerList.map((ans, idx) => (
            <div key={idx} ref={idx === answerList.length - 1 ? latestAnswerRef : null}>
              <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginBottom: '4px' }}>
                {ans.question}
              </p>
              <ToolCallTrace toolCalls={ans.tool_calls} />
              <AnswerDisplay answer={ans.answer} />
            </div>
          ))}
          {loading && (
            <div className="mt-4 flex items-center gap-3">
              <div className="flex space-x-1">
                <div className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce [animation-delay:0ms]" />
                <div className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce [animation-delay:150ms]" />
                <div className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-sm text-white/60">{loadingStatus}</span>
            </div>
          )}
          {submitted && !answer && !loading && (
            <p className="text-red-300 text-sm">No relevant code found.</p>
          )}
        </div>

        {/* Sticky input at bottom */}
        <div className="p-4 border-t border-white/10">
          {error && <p className="text-red-400 mb-2 text-sm">{error}</p>}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="flex-1 bg-black bg-opacity-30 border border-white/20 rounded px-3 py-2 text-white placeholder-gray-300"
              placeholder="Ask a question..."
            />
            <button
              type="submit"
              disabled={loading}
              className={`px-4 py-2 rounded font-semibold ${
                loading
                  ? 'bg-gray-500 cursor-not-allowed'
                  : 'bg-neutral-100 text-black hover:bg-neutral-200'
              }`}
            >
              {loading ? '...' : 'Ask'}
            </button>
          </form>
        </div>
      </div>
    </>
  )
}
const container = document.getElementById('crx-root')

if (container) {
  const root = createRoot(container)
  root.render(<App />)
}
