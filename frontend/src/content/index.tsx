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
root.style.cssText = `bottom: 150px; right: 80px; position: fixed; z-index: 9999`
document.body.appendChild(root)

const btnHeight = 50
const btnWidth = 250

function App() {
  const [clicked, setClicked] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState([])
  const [submitted, setSubmitted] = useState(false)
  const [questionType, setQuestionType] = useState('')

  const componentsMap: Record<string, React.ComponentType<{ answer: typeof answer }>> = {
    semantic_lookup: SemanticLookup,
    repo_summary: RepoSummary,
    function_summary: FunctionSummary,
    call_graph: CallGraph,
  }

  const SelectedComponent = componentsMap[questionType]

  const handleClick = () => {
    setClicked(!clicked)
  }

  const extractRepoUrl = () => {
    const match = window.location.pathname.match(/^\/([^/]+)\/([^/]+)/)
    if (!match) return null

    const owner = match[1]
    const repo = match[2]

    return `https://github.com/${owner}/${repo}.git`
  }

  useEffect(() => {
    console.log('Updated answer:', answer)
  }, [answer])

  const repoUrl = extractRepoUrl()

  const handleSubmit = async (e) => {
    e.preventDefault()
    console.log(inputValue)
    setLoading(true)
    setSubmitted(false)

    try {
      const response = await fetch('http://127.0.0.1:3000/api/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputValue,
          repoUrl: extractRepoUrl(),
        }),
      })

      const data = await response.json()
      console.log(data)
      setAnswer(data.answer.results)
      setQuestionType(data.answer.type)
    } catch (err) {
      console.error('error fetching answer:', err)
      setAnswer([])
    }
    setLoading(false)
    setSubmitted(true)
  }
  return (
    <div className="fixed bottom-36 right-20 bg-white border border-gray-300 shadow-xl rounded-xl p-4 w-[400px] max-h-[80vh] overflow-y-auto text-sm font-sans z-[9999]">
      <button
        className="w-full bg-blue-600 text-white font-semibold py-2 px-4 rounded hover:bg-blue-700 transition"
        onClick={handleClick}
      >
        Ask a question about the repo?
      </button>

      {clicked && (
        <form onSubmit={handleSubmit} className="mt-4 space-y-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Type your question"
          />
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2 rounded text-white font-semibold ${
              loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-700 hover:bg-blue-800'
            } transition`}
          >
            {loading ? 'Asking...' : 'Ask'}
          </button>
        </form>
      )}
      {/* {console.log('Rendering answer:', answer)}
      {console.log('SelectedComponent:', SelectedComponent)} */}
      {answer.length > 0 && SelectedComponent && <SelectedComponent answer={answer} />}
      {submitted && answer.length === 0 && clicked && !loading && (
        <div className="mt-4 text-red-500 text-sm">❌ No relevant code found.</div>
      )}
    </div>
  )
}

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('crx-root'),
)
