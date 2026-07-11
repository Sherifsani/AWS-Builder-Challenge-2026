import { useEffect, useState } from 'react'
import { api, getToken, setToken, clearToken } from './api'
import Auth from './components/Auth'
import Dashboard from './components/Dashboard'

export default function App() {
  const [authed, setAuthed] = useState(Boolean(getToken()))
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(Boolean(getToken()))

  // On load (or after login) fetch the profile; a 401 means a stale token.
  useEffect(() => {
    if (!authed) return
    let cancelled = false
    setLoading(true)
    api
      .me()
      .then((p) => !cancelled && setProfile(p))
      .catch(() => {
        clearToken()
        if (!cancelled) setAuthed(false)
      })
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [authed])

  const handleAuthed = (token) => {
    setToken(token)
    setAuthed(true)
  }

  const handleLogout = () => {
    clearToken()
    setProfile(null)
    setAuthed(false)
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">✦</span> Resume Tailor
        </div>
        {authed && (
          <div className="topbar-right">
            {profile?.email && <span className="who">{profile.email}</span>}
            <button className="btn-ghost" onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </header>

      <main className="content">
        {!authed ? (
          <Auth onAuthed={handleAuthed} />
        ) : loading ? (
          <p className="muted">Loading…</p>
        ) : (
          <Dashboard profile={profile} onProfileChange={setProfile} />
        )}
      </main>

      <footer className="footer muted">
        AWS Builder Center — Weekend Productivity Challenge
      </footer>
    </div>
  )
}
