import React from 'react'

const RepoSummary = ({ answer }) => {
  if (!answer || !Array.isArray(answer) || answer.length === 0) {
    return <div className="text-sm text-gray-400 italic mt-4">No summary data available.</div>
  }

  const { summary, entry_points, key_modules } = answer[0]

  return (
    <div className="mt-4 space-y-6 overflow-y-auto pr-1">
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 shadow-md text-sm text-white/90 transition hover:shadow-lg">
        <div className="font-semibold mb-3">📦 Repository Summary</div>
        <p className="mb-4 text-white/70">{summary}</p>

        <div className="mb-1 font-medium text-white/90">🚀 Entry Points:</div>
        <ul className="list-disc list-inside text-xs text-white/70 mb-4">
          {entry_points?.map((file, idx) => (
            <li key={idx} className="font-mono">
              {file}
            </li>
          ))}
        </ul>

        <div className="mb-1 font-medium text-white/90">📚 Key Modules:</div>
        <ul className="list-disc list-inside text-xs text-white/70">
          {key_modules?.map((file, idx) => (
            <li key={idx} className="font-mono">
              {file}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default RepoSummary
