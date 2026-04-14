import { useEffect, useMemo, useState } from 'react'

function formatTime(seconds) {
  const h = String(Math.floor(seconds / 3600)).padStart(2, '0')
  const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0')
  const s = String(seconds % 60).padStart(2, '0')
  return `${h}:${m}:${s}`
}

export default function Timer({ totalMinutes, onComplete }) {
  const totalSeconds = totalMinutes * 60
  const [secondsLeft, setSecondsLeft] = useState(totalSeconds)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    setSecondsLeft(totalSeconds)
    setIsRunning(false)
  }, [totalSeconds])

  useEffect(() => {
    if (!isRunning || secondsLeft <= 0) {
      if (secondsLeft === 0) {
        onComplete?.()
      }
      return undefined
    }

    const id = window.setInterval(() => {
      setSecondsLeft((prev) => Math.max(0, prev - 1))
    }, 1000)

    return () => window.clearInterval(id)
  }, [isRunning, secondsLeft, onComplete])

  const progress = useMemo(() => {
    if (totalSeconds <= 0) return 0
    return ((totalSeconds - secondsLeft) / totalSeconds) * 100
  }, [secondsLeft, totalSeconds])

  const radius = 68
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference - (progress / 100) * circumference

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center space-y-4">
      <div className="relative w-40 h-40 mx-auto">
        <svg className="w-40 h-40 -rotate-90" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={radius} stroke="#1f2937" strokeWidth="10" fill="transparent" />
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="#a855f7"
            strokeWidth="10"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-white">{formatTime(secondsLeft)}</div>
      </div>

      <div className="flex justify-center gap-2">
        <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500 text-white" onClick={() => setIsRunning(true)}>
          Start
        </button>
        <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-gray-800 hover:bg-gray-700 text-white" onClick={() => setIsRunning(false)}>
          Pause
        </button>
        <button
          className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-gray-800 hover:bg-gray-700 text-white"
          onClick={() => {
            setIsRunning(false)
            setSecondsLeft(totalSeconds)
          }}
        >
          Reset
        </button>
      </div>
    </div>
  )
}
