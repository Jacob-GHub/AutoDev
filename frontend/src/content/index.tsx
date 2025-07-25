import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom'
import '../style/btn.less'
import '../style/index.css'
import SemanticLookup from '../components/responses/semantic_lookup/index'
import RepoSummary from '../components/responses/repo_summary'
import FunctionSummary from '../components/responses/function_summary'
import CallGraph from '../components/responses/call_graph'

const root = document.createElement('div')
root.id = 'crx-root'
document.body.appendChild(root)

const App = () => {
  const [showModal, setShowModal] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState([])
  const [submitted, setSubmitted] = useState(false)
  const [questionType, setQuestionType] = useState('semantic_lookup')
  const [open, setOpen] = useState(false)
  const [error, setError] = useState(null)
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  const componentsMap = {
    semantic_lookup: SemanticLookup,
    repo_summary: RepoSummary,
    function_summary: FunctionSummary,
    call_graph: CallGraph,
  }

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
    setLoading(true)
    setSubmitted(false)

    try {
      const response = await fetch('http://127.0.0.1:3000/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: inputValue,
          repoUrl: extractRepoUrl(),
        }),
      })

      const data = await response.json()
      console.log(data)
      setAnswer(data.answer.results)
      console.log(answer)
      setQuestionType(data.answer.type)
      console.log(questionType)
      setError(null)
    } catch (err) {
      setError('Something went wrong. Please try again.')
      console.error('Error:', err)
      setAnswer([])
    }

    setLoading(false)
    setSubmitted(true)
  }

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-10 right-10 z-[9999] bg-neutral-100 text-black hover:bg-neutral-200
 px-4 py-3 rounded-full shadow-lg backdrop-blur hover:bg-white transition-colors"
      >
        {open ? 'Close' : '💬 Ask Repo Question'}
      </button>

      <div
        className={`fixed top-0 right-0 h-full w-[400px] backdrop-blur-md bg-black bg-opacity-50 text-white shadow-2xl border-l border-white/10 z-[9998] transition-transform duration-300 ease-in-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="p-6 h-full flex flex-col overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Ask a question</h2>
            <button
              onClick={() => setOpen(false)}
              className="text-white text-xl hover:text-red-400"
            >
              ✖
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="w-full bg-black bg-opacity-30 border border-white/20 rounded px-3 py-2 text-white placeholder-gray-300"
              placeholder="Ask a question..."
            />

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2 rounded font-semibold ${
                loading
                  ? 'bg-gray-500 cursor-not-allowed'
                  : 'bg-neutral-100 text-black hover:bg-neutral-200'
              }`}
            >
              {loading ? (
                <div className="mt-4 animate-pulse space-y-3">
                  <div className="h-4 bg-gray-600 rounded w-3/4" />
                  <div className="h-4 bg-gray-600 rounded w-full" />
                  <div className="h-4 bg-gray-600 rounded w-1/2" />
                </div>
              ) : (
                'Ask'
              )}
            </button>
          </form>
          {error && <p className="text-red-400 mt-4 text-sm">{error}</p>}
          <div className="mt-4 flex-1 overflow-y-auto">
            {answer.length > 0 && SelectedComponent && <SelectedComponent answer={answer} />}
            {submitted && answer.length === 0 && !loading && (
              <p className="mt-4 text-red-300 text-sm">❌ No relevant code found.</p>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
ReactDOM.render(<App />, document.getElementById('crx-root'))
