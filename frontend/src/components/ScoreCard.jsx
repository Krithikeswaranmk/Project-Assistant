import { CircularProgressbar, buildStyles } from 'react-circular-progressbar'
import 'react-circular-progressbar/dist/styles.css'

function scoreColor(score) {
  if (score > 70) return '#4ade80'
  if (score > 40) return '#f59e0b'
  return '#ef4444'
}

export default function ScoreCard({ score }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 className="text-white font-semibold mb-4">Overall Relevance</h3>
      <div className="w-28 h-28 mx-auto">
        <CircularProgressbar
          value={score}
          text={`${score}%`}
          styles={buildStyles({
            pathColor: scoreColor(score),
            textColor: '#fff',
            trailColor: '#1f2937',
          })}
        />
      </div>
    </div>
  )
}
