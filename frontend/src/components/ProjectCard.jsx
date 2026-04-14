import { format } from 'date-fns'
import { ThumbsDown, ThumbsUp } from 'lucide-react'
import { submitScoreFeedback } from '../lib/api'

const languageColors = {
  JavaScript: 'bg-yellow-900/30 text-yellow-400',
  TypeScript: 'bg-blue-900/30 text-blue-400',
  Python: 'bg-green-900/30 text-green-400',
  Go: 'bg-cyan-900/30 text-cyan-400',
  Rust: 'bg-orange-900/30 text-orange-400',
}

function scoreBarColor(score) {
  if (score > 70) return 'bg-green-500'
  if (score > 40) return 'bg-amber-500'
  return 'bg-red-500'
}

export default function ProjectCard({ repo, userId }) {
  const languageClass = languageColors[repo.language] || 'bg-gray-800 text-gray-300'

  async function onFeedback(scoreType, helpful) {
    try {
      await submitScoreFeedback(userId, {
        repo_name: repo.name,
        score_type: scoreType,
        helpful,
      })
    } catch (_err) {
      // Fail silently for lightweight UX.
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-white text-lg font-semibold">{repo.name}</h3>
        <span className={`px-2 py-1 rounded-md text-xs font-medium ${languageClass}`}>{repo.language || 'Unknown'}</span>
      </div>

      <p className="text-gray-400 text-sm">{repo.one_line_summary || repo.description || 'No summary available.'}</p>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-sm text-gray-300 mb-1">
            <span className="flex items-center gap-2">Relevance to Role: {repo.relevance_score}% <span className="px-1.5 py-0.5 text-xs bg-purple-900/40 text-purple-300 rounded">AI</span></span>
            <span className="flex items-center gap-2">
              <button className="text-gray-400 hover:text-green-400" onClick={() => onFeedback('relevance', true)}><ThumbsUp size={14} /></button>
              <button className="text-gray-400 hover:text-red-400" onClick={() => onFeedback('relevance', false)}><ThumbsDown size={14} /></button>
            </span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div className={`h-2 ${scoreBarColor(repo.relevance_score || 0)}`} style={{ width: `${repo.relevance_score || 0}%` }} />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-sm text-gray-300 mb-1">
            <span className="flex items-center gap-2">Market Demand: {repo.market_demand_score}% <span className="px-1.5 py-0.5 text-xs bg-purple-900/40 text-purple-300 rounded">AI</span></span>
            <span className="flex items-center gap-2">
              <button className="text-gray-400 hover:text-green-400" onClick={() => onFeedback('market_demand', true)}><ThumbsUp size={14} /></button>
              <button className="text-gray-400 hover:text-red-400" onClick={() => onFeedback('market_demand', false)}><ThumbsDown size={14} /></button>
            </span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div className={`h-2 ${scoreBarColor(repo.market_demand_score || 0)}`} style={{ width: `${repo.market_demand_score || 0}%` }} />
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {(repo.missing_skills || []).map((skill) => (
          <span key={`${repo.name}-miss-${skill}`} className="px-2 py-1 rounded-full text-xs bg-red-900/30 text-red-300">
            Add: {skill}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {(repo.key_skills || []).map((skill) => (
          <span key={`${repo.name}-key-${skill}`} className="px-2 py-1 rounded-full text-xs bg-green-900/30 text-green-300">
            {skill}
          </span>
        ))}
      </div>

      <div className="text-xs text-gray-500 flex items-center justify-between">
        <span>Stars: {repo.stars || 0}</span>
        <span>{repo.last_updated ? format(new Date(repo.last_updated), 'MMM d, yyyy') : 'Unknown update date'}</span>
      </div>
    </div>
  )
}
