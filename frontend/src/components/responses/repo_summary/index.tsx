import React from 'react'

const RepoSummary = ({ answer }) => {
  if (!answer || answer.length === 0) return null

  const { summary, entry_points, key_modules } = answer[0]

  return (
    <div className="mt-4 space-y-4 text-sm">
      <div className="bg-gray-100 p-4 rounded border border-gray-300">
        <div className="font-semibold mb-2">📦 Repository Summary</div>
        <p className="mb-2">{summary}</p>
        <div className="mb-1 font-medium">🚀 Entry Points:</div>
        <ul className="list-disc list-inside text-xs text-gray-700 mb-2">
          {entry_points.map((file, idx) => (
            <li key={idx}>{file}</li>
          ))}
        </ul>
        <div className="mb-1 font-medium">📚 Key Modules:</div>
        <ul className="list-disc list-inside text-xs text-gray-700">
          {key_modules.map((file, idx) => (
            <li key={idx}>{file}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default RepoSummary
