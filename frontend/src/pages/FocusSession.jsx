import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import TaskList from '../components/TaskList'
import Timer from '../components/Timer'
import { completeSession, updateTask } from '../lib/api'

function deadlineClass(status) {
  if (status === 'on_track') return 'bg-green-900/30 text-green-300'
  if (status === 'at_risk') return 'bg-amber-900/30 text-amber-300'
  return 'bg-red-900/30 text-red-300'
}

export default function FocusSession() {
  const navigate = useNavigate()
  const location = useLocation()
  const session = location.state?.session

  if (!session) {
    navigate('/dashboard')
    return null
  }

  const [tasks, setTasks] = useState(session.tasks || [])

  const completedCount = useMemo(() => tasks.filter((task) => task.completed).length, [tasks])
  const completionPercent = tasks.length ? Math.round((completedCount / tasks.length) * 100) : 0

  async function onToggleTask(index, completed) {
    setTasks((prev) => prev.map((task, i) => (i === index ? { ...task, completed } : task)))
    try {
      await updateTask(session.session_id, index, { completed })
    } catch (_err) {
      // Keep optimistic UI in phase 1.
    }
  }

  async function endSession() {
    try {
      await completeSession(session.session_id)
    } finally {
      navigate('/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-purple-900/30 border border-purple-800 rounded-xl p-4">
            <p className="text-sm text-purple-200">Session Goal</p>
            <h1 className="text-xl font-semibold mt-1">{session.goal}</h1>
          </div>

          <TaskList tasks={tasks} onToggle={onToggleTask} />

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 italic text-gray-300">
            {session.session_strategy || 'Follow the tasks in order and keep each block tightly scoped.'}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <Timer totalMinutes={session.focus_minutes || 60} onComplete={() => {}} />

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
            <p className="text-sm text-gray-300">{completedCount} of {tasks.length} tasks completed</p>
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-2 bg-purple-500" style={{ width: `${completionPercent}%` }} />
            </div>
            <div>
              <span className={`px-2 py-1 text-xs rounded-full ${deadlineClass(session.deadline_status || 'on_track')}`}>
                Deadline Status: {session.deadline_status || 'on_track'}
              </span>
            </div>
            <button className="w-full rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500" onClick={endSession}>
              End Session
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
