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
          <span className="logo">R</span> Résumé&nbsp;Bench
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
          <div className="auth-wrap">
            <Auth onAuthed={handleAuthed} />
          </div>
        ) : loading ? (
          <div className="hero"><p className="muted">Loading your bench…</p></div>
        ) : (
          <>
            <section className="hero">
              <p className="hero-eyebrow">Tailor · Match · Ship</p>
              <h1>
                Cut a resume that fits <em>this</em> job.
              </h1>
              <p>
                Keep one bank of bullets. Paste a job description and get a ranked,
                keyword-checked resume — plus a polished CV you can download in a click.
              </p>
            </section>
            <Dashboard profile={profile} onProfileChange={setProfile} />
          </>
        )}
      </main>

      <footer className="footer">
        Built for the AWS Builder Center — Weekend Productivity Challenge
      </footer>
    </div>
  )
}
