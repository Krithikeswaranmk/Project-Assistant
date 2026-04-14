export default function TaskList({ tasks, onToggle }) {
  const typeBadge = {
    code: 'bg-blue-900/30 text-blue-300',
    research: 'bg-purple-900/30 text-purple-300',
    test: 'bg-green-900/30 text-green-300',
    review: 'bg-amber-900/30 text-amber-300',
    design: 'bg-pink-900/30 text-pink-300',
  }

  return (
    <div className="space-y-3">
      {tasks.map((task, index) => (
        <div key={task.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={Boolean(task.completed)}
              onChange={(e) => onToggle(index, e.target.checked)}
              className="mt-1"
            />
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className={`font-semibold ${task.completed ? 'text-gray-500 line-through' : 'text-white'}`}>{task.title}</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${typeBadge[task.type] || 'bg-gray-800 text-gray-300'}`}>{task.type}</span>
                <span className="text-xs text-gray-500">~{task.estimated_minutes} min</span>
              </div>
              <p className="text-sm text-gray-400 mt-1">{task.description}</p>
              {task.relevant_file ? <p className="text-xs text-purple-300 mt-2 font-mono">{task.relevant_file}</p> : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
