import { createContext, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { supabase } from './lib/supabase'
import Dashboard from './pages/Dashboard'
import FocusSession from './pages/FocusSession'
import Onboarding from './pages/Onboarding'

export const AuthContext = createContext({ user: null })

function ProtectedRoute({ user, children }) {
  if (!user) {
    return <Navigate to="/" replace />
  }
  return children
}

function RootRoute({ user }) {
  if (user) {
    return <Navigate to="/dashboard" replace />
  }
  return <Onboarding />
}

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function loadUser() {
      const { data } = await supabase.auth.getUser()
      if (isMounted) {
        setUser(data.user ?? null)
        setLoading(false)
      }
    }

    loadUser()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => {
      isMounted = false
      subscription.unsubscribe()
    }
  }, [])

  const contextValue = useMemo(() => ({ user }), [user])

  if (loading) {
    return <div className="min-h-screen bg-gray-950 text-gray-300 flex items-center justify-center">Loading...</div>
  }

  return (
    <AuthContext.Provider value={contextValue}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootRoute user={user} />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute user={user}>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/focus"
            element={
              <ProtectedRoute user={user}>
                <FocusSession />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}
