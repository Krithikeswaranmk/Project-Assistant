import { useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar'
import 'react-circular-progressbar/dist/styles.css'
import ProjectCard from '../components/ProjectCard'
import SkeletonLoader from '../components/SkeletonLoader'
import { getProfile, planSession } from '../lib/api'
import { supabase } from '../lib/supabase'
import { AuthContext } from '../App'

function scoreColor(score) {
  if (score > 70) return '#4ade80'
  if (score > 40) return '#f59e0b'
  return '#ef4444'
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { user } = useContext(AuthContext)
  const [profileData, setProfileData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [planLoading, setPlanLoading] = useState(false)
  const [planForm, setPlanForm] = useState({
    project_name: '',
    repo_name: '',
    goal: '',
    deadline: '',
    complexity: 'medium',
    focus_minutes: 60,
  })

  useEffect(() => {
    if (!user) return
    async function load() {
      setLoading(true)
      try {
        const resp = await getProfile(user.id)
        setProfileData(resp.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user])

  const topSkills = useMemo(() => {
    if (!profileData?.skill_coverage) return []
    return Object.entries(profileData.skill_coverage)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
  }, [profileData])

  async function handleLogout() {
    await supabase.auth.signOut()
    navigate('/')
  }

  async function generatePlan() {
    if (!user) return
    setPlanLoading(true)
    try {
      const resp = await planSession({
        user_id: user.id,
        project_name: planForm.project_name || planForm.repo_name,
        repo_name: planForm.repo_name,
        goal: planForm.goal,
        deadline: planForm.deadline,
        focus_minutes: Number(planForm.focus_minutes),
        complexity: planForm.complexity,
      })
      setModalOpen(false)
      navigate('/focus', {
        state: {
          session: resp.data,
        },
      })
    } finally {
      setPlanLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 p-6">
        <SkeletonLoader />
      </div>
    )
  }

  const profile = profileData?.profile || {}
  const repos = profileData?.repos || []

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-3 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-700 flex items-center justify-center font-bold">PP</div>
            <div className="flex items-center gap-3">
              {profile.avatar_url ? <img src={profile.avatar_url} alt="avatar" className="w-8 h-8 rounded-full" /> : null}
              <div>
                <p className="font-semibold">Project-Pilot</p>
                <p className="text-sm text-gray-400">{profile.name || user?.email || 'User'}</p>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400" onClick={() => setModalOpen(true)}>
              Start Working
            </button>
            <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 border border-gray-700 hover:bg-gray-800" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="font-semibold mb-4">Overall Relevance</h3>
            <div className="w-28 h-28">
              <CircularProgressbar
                value={profileData?.overall_relevance_percent || 0}
                text={`${profileData?.overall_relevance_percent || 0}%`}
                styles={buildStyles({
                  pathColor: scoreColor(profileData?.overall_relevance_percent || 0),
                  trailColor: '#1f2937',
                  textColor: '#fff',
                })}
              />
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="font-semibold mb-2">Top Project</h3>
            <p className="text-purple-300 font-medium">{profileData?.top_project?.name || 'N/A'}</p>
            <p className="text-sm text-gray-400 mt-2">{profileData?.top_project?.reason || 'Connect repos to see insights.'}</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="font-semibold mb-3">Skill Coverage</h3>
            <div className="space-y-2">
              {topSkills.length === 0 ? <p className="text-gray-500 text-sm">No skills computed yet.</p> : null}
              {topSkills.map(([skill, score]) => (
                <div key={skill}>
                  <div className="flex items-center justify-between text-xs mb-1 text-gray-300">
                    <span>{skill}</span>
                    <span>{score}%</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-2 bg-purple-500" style={{ width: `${score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4">Your Projects</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {repos.map((repo) => (
              <ProjectCard key={repo.id || repo.name} repo={repo} userId={user.id} />
            ))}
          </div>
        </section>
      </div>

      {modalOpen ? (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="text-2xl font-semibold">Start a Focus Session</h3>

            <div>
              <label className="text-sm text-gray-400">Which project?</label>
              <select
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
                value={planForm.repo_name}
                onChange={(e) => setPlanForm((prev) => ({ ...prev, repo_name: e.target.value, project_name: e.target.value }))}
              >
                <option value="">Select a project</option>
                {repos.map((repo) => (
                  <option key={repo.name} value={repo.name}>
                    {repo.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm text-gray-400">What do you want to accomplish?</label>
              <textarea
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
                rows={4}
                placeholder="e.g. Implement the training loop for my CNN model"
                value={planForm.goal}
                onChange={(e) => setPlanForm((prev) => ({ ...prev, goal: e.target.value }))}
              />
            </div>

            <div>
              <label className="text-sm text-gray-400">When is the deadline?</label>
              <input
                type="date"
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
                value={planForm.deadline}
                onChange={(e) => setPlanForm((prev) => ({ ...prev, deadline: e.target.value }))}
              />
            </div>

            <div>
              <label className="text-sm text-gray-400">How complex is this task?</label>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {['low', 'medium', 'high'].map((level) => (
                  <button
                    key={level}
                    className={`rounded-lg px-4 py-2 font-medium transition-all duration-200 border ${planForm.complexity === level ? 'bg-purple-600 border-purple-500' : 'border-gray-700 bg-gray-800 hover:bg-gray-700'}`}
                    onClick={() => setPlanForm((prev) => ({ ...prev, complexity: level }))}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm text-gray-400">How long can you focus?</label>
              <div className="flex flex-wrap gap-2 mt-2">
                {[25, 45, 60, 90].map((minutes) => (
                  <button
                    key={minutes}
                    className={`rounded-lg px-4 py-2 font-medium transition-all duration-200 ${planForm.focus_minutes === minutes ? 'bg-purple-600 text-white' : 'bg-gray-800 hover:bg-gray-700 text-gray-300'}`}
                    onClick={() => setPlanForm((prev) => ({ ...prev, focus_minutes: minutes }))}
                  >
                    {minutes} min
                  </button>
                ))}
              </div>
            </div>

            {planLoading ? <div className="text-gray-400">Analyzing your codebase and building your session plan...</div> : null}

            <div className="flex justify-end gap-2">
              <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-gray-800 hover:bg-gray-700" onClick={() => setModalOpen(false)}>
                Cancel
              </button>
              <button
                className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500"
                disabled={!planForm.repo_name || !planForm.goal || !planForm.deadline || planLoading}
                onClick={generatePlan}
              >
                Generate My Plan
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
