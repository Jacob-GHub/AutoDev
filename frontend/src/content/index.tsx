import React, { useState } from 'react'
import ReactDOM from 'react-dom'
import '../style/btn.less'

const root = document.createElement('div')
root.id = 'crx-root'
root.style.cssText = `bottom: 150px; right: 80px; position: fixed; z-index: 9999`
document.body.appendChild(root)

const btnHeight = 50
const btnWidth = 250

function App() {
  const [clicked, setClicked] = useState(false)
  const [inputValue, setInputValue] = useState('')

  const handleClick = () => {
    setClicked(!clicked)
  }
  const handleSubmit = (e) => {
    e.preventDefault()
    console.log(inputValue)
  }
  return (
    <div>
      <button className="crx-btn" onClick={handleClick}>
        Ask a question about the repo?
      </button>
      {clicked && (
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          ></input>
        </form>
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
