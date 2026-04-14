import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOnboardStatus, onboardUser } from '../lib/api'
import { supabase } from '../lib/supabase'

const roleOptions = [
  'ML Engineer',
  'Full Stack Developer',
  'Backend Engineer',
  'Frontend Engineer',
  'Data Scientist',
  'DevOps Engineer',
  'Mobile Developer',
  'Other',
]

const experienceOptions = ['student', 'junior', 'mid', 'senior']

const focusOptions = [
  'Machine Learning',
  'Web Development',
  'Data Engineering',
  'Cloud/DevOps',
  'Mobile',
  'Systems Programming',
  'Research',
]

function StepDots({ step }) {
  return (
    <div className="flex items-center gap-2">
      {[1, 2, 3, 4].map((dot) => (
        <div key={dot} className={`w-2.5 h-2.5 rounded-full ${dot <= step ? 'bg-purple-500' : 'bg-gray-700'}`} />
      ))}
    </div>
  )
}

export default function Onboarding() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [authLoading, setAuthLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [complete, setComplete] = useState(false)
  const [status, setStatus] = useState({ repos_done: 0, repos_total: 0, status: 'indexing' })
  const [githubMethod, setGithubMethod] = useState('oauth')
  const [form, setForm] = useState({
    user_id: '',
    name: '',
    email: '',
    password: '',
    github_username: '',
    github_token: '',
    target_role: 'Full Stack Developer',
    experience_level: 'student',
    focus_areas: [],
  })

  const backendUrl = import.meta.env.VITE_BACKEND_URL
  const progressPercent = useMemo(() => {
    if (!status.repos_total) return 15
    return Math.max(10, Math.min(100, Math.round((status.repos_done / status.repos_total) * 100)))
  }, [status])

  useEffect(() => {
    if (step !== 4 || !form.user_id || complete) {
      return undefined
    }

    let intervalId
    let mounted = true

    async function runOnboarding() {
      setLoading(true)
      setError('')
      try {
        await onboardUser({
          user_id: form.user_id,
          name: form.name,
          github_username: form.github_username,
          github_token: githubMethod === 'pat' ? form.github_token : '',
          target_role: form.target_role,
          experience_level: form.experience_level,
          focus_areas: form.focus_areas,
        })
      } catch (err) {
        if (mounted) {
          setError(err?.response?.data?.detail || 'Failed to start onboarding. Please retry.')
          setLoading(false)
        }
        return
      }

      intervalId = window.setInterval(async () => {
        try {
          const resp = await getOnboardStatus(form.user_id)
          if (!mounted) return
          setStatus(resp.data)
          if (resp.data.status === 'complete') {
            setComplete(true)
            setLoading(false)
            window.clearInterval(intervalId)
          }
          if (resp.data.status === 'error') {
            setError('Repository indexing failed. Please retry onboarding.')
            setLoading(false)
            window.clearInterval(intervalId)
          }
        } catch (_err) {
          if (!mounted) return
          setError('Status polling failed. Please retry.')
          setLoading(false)
          window.clearInterval(intervalId)
        }
      }, 3000)
    }

    runOnboarding()

    return () => {
      mounted = false
      if (intervalId) window.clearInterval(intervalId)
    }
  }, [step, form, githubMethod, complete])

  async function handleSignUp() {
    setAuthLoading(true)
    setError('')
    const { data, error: signUpError } = await supabase.auth.signUp({
      email: form.email,
      password: form.password,
    })
    setAuthLoading(false)

    if (signUpError) {
      setError(signUpError.message)
      return
    }

    if (!data.user) {
      setError('No user returned from Supabase sign up.')
      return
    }

    setForm((prev) => ({ ...prev, user_id: data.user.id }))
    setStep(2)
  }

  function toggleFocus(area) {
    setForm((prev) => {
      const set = new Set(prev.focus_areas)
      if (set.has(area)) set.delete(area)
      else set.add(area)
      return { ...prev, focus_areas: [...set] }
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 to-gray-900 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-2xl bg-gray-900 border border-gray-800 rounded-xl p-8 space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-400">Step {step} of 4</p>
          <StepDots step={step} />
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h1 className="text-3xl font-bold">Welcome to Project-Pilot</h1>
            <p className="text-gray-300">Your AI-powered project assistant</p>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
              placeholder="What should we call you?"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            />
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
            />
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
              placeholder="Password"
              type="password"
              value={form.password}
              onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
            />
            <button
              className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50"
              disabled={!form.name || !form.email || !form.password || authLoading}
              onClick={handleSignUp}
            >
              {authLoading ? 'Creating Account...' : 'Get Started ->'}
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Connect your GitHub</h2>
            <p className="text-gray-300">We'll analyze your repos to understand your skills</p>

            <div className="grid md:grid-cols-2 gap-4">
              <div className={`border rounded-xl p-4 ${githubMethod === 'oauth' ? 'border-purple-500 bg-gray-800' : 'border-gray-800 bg-gray-900'}`}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold">Connect with GitHub OAuth</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-green-900/30 text-green-300">Recommended</span>
                </div>
                <a className="inline-block rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500 text-white" href={`${backendUrl}/api/auth/github`}>
                  Connect GitHub OAuth
                </a>
                <button
                  className="mt-3 rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-gray-800 hover:bg-gray-700 text-white"
                  onClick={() => {
                    setGithubMethod('oauth')
                    setStep(3)
                  }}
                >
                  Continue with OAuth
                </button>
              </div>

              <div className={`border rounded-xl p-4 ${githubMethod === 'pat' ? 'border-purple-500 bg-gray-800' : 'border-gray-800 bg-gray-900'}`}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold">Use a Personal Access Token</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-amber-900/30 text-amber-300">Advanced</span>
                </div>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 mb-2"
                  placeholder="ghp_..."
                  value={form.github_token}
                  onChange={(e) => {
                    setGithubMethod('pat')
                    setForm((prev) => ({ ...prev, github_token: e.target.value }))
                  }}
                />
                <a className="text-sm text-purple-400 hover:text-purple-300" href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens" target="_blank" rel="noreferrer">
                  How to create a PAT
                </a>
                <button
                  className="mt-3 rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500 text-white"
                  onClick={() => setStep(3)}
                >
                  Continue with PAT
                </button>
              </div>
            </div>

            <div className="text-sm text-gray-400 bg-gray-800/60 border border-gray-700 rounded-lg p-3">
              Your token is stored encrypted and only used to read your repositories.
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Tell us about yourself</h2>

            <select
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
              value={form.target_role}
              onChange={(e) => setForm((prev) => ({ ...prev, target_role: e.target.value }))}
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>

            <select
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
              value={form.experience_level}
              onChange={(e) => setForm((prev) => ({ ...prev, experience_level: e.target.value }))}
            >
              {experienceOptions.map((exp) => (
                <option key={exp} value={exp}>
                  {exp}
                </option>
              ))}
            </select>

            {githubMethod === 'pat' && (
              <input
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
                placeholder="GitHub username"
                value={form.github_username}
                onChange={(e) => setForm((prev) => ({ ...prev, github_username: e.target.value }))}
              />
            )}

            <div>
              <p className="text-gray-300 mb-2">What are your focus areas?</p>
              <div className="flex flex-wrap gap-2">
                {focusOptions.map((area) => {
                  const active = form.focus_areas.includes(area)
                  return (
                    <button
                      key={area}
                      type="button"
                      className={`px-3 py-1.5 rounded-full text-sm border ${active ? 'bg-purple-600 border-purple-500 text-white' : 'bg-gray-800 border-gray-700 text-gray-300'}`}
                      onClick={() => toggleFocus(area)}
                    >
                      {area}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="flex gap-2">
              <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-gray-800 hover:bg-gray-700 text-white" onClick={() => setStep(2)}>
                Back
              </button>
              <button
                className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500 text-white"
                onClick={() => setStep(4)}
              >
                Start Indexing
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-5">
            <h2 className="text-2xl font-semibold">Indexing</h2>
            {!complete ? (
              <>
                <div className="animate-pulse text-gray-300">Analyzing your repositories... ({status.repos_done}/{status.repos_total || '?' } repos indexed)</div>
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-3 bg-purple-600 transition-all duration-500" style={{ width: `${progressPercent}%` }} />
                </div>
                {loading ? <p className="text-sm text-gray-500">This can take 60-120 seconds for larger repositories.</p> : null}
              </>
            ) : (
              <>
                <p className="text-green-400 text-xl">Your profile is ready!</p>
                <button className="rounded-lg px-4 py-2 font-medium transition-all duration-200 bg-purple-600 hover:bg-purple-500 text-white" onClick={() => navigate('/dashboard')}>
                  Go to Dashboard
                </button>
              </>
            )}
            {error ? (
              <div className="bg-red-900/30 border border-red-800 rounded-lg p-3 text-red-300">
                {error}
                <button
                  className="ml-3 rounded-lg px-3 py-1 bg-gray-800 hover:bg-gray-700 text-white"
                  onClick={() => {
                    setComplete(false)
                    setStatus({ repos_done: 0, repos_total: 0, status: 'indexing' })
                    setError('')
                    setStep(4)
                  }}
                >
                  Retry
                </button>
              </div>
            ) : null}
          </div>
        )}

        {error && step !== 4 ? <div className="text-red-400 text-sm">{error}</div> : null}
      </div>
    </div>
  )
}
