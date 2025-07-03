import React, { useState } from 'react'
import ReactDOM from 'react-dom'
import '../style/btn.less'
import '../style/index.css'

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
  const [answer, setAnswer] = useState('')

  const handleClick = () => {
    setClicked(!clicked)
  }
  const handleSubmit = async (e) => {
    e.preventDefault()
    console.log(inputValue)
    setLoading(true)
    const repoUrl = window.location.href

    try {
      const response = await fetch('http://127.0.0.1:3000/api/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputValue,
          repoUrl: repoUrl,
        }),
      })

      const data = await response.json()
      setAnswer(data.answer)
    } catch (err) {
      console.error('error fetching answer:', err)
      setAnswer('something went wrong.')
    }
    setLoading(false)
  }
  return (
    <div className="fixed bottom-36 right-20 bg-white border border-gray-300 shadow-xl rounded-xl p-4 w-[300px] text-sm font-sans z-[9999]">
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

      {answer && (
        <div className="mt-4 bg-gray-100 rounded p-3 text-gray-800">
          <strong className="block mb-1 text-gray-700">Answer:</strong>
          <div>{answer}</div>
        </div>
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
