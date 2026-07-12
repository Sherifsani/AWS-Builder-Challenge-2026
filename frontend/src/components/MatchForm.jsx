import { useState } from 'react'
import { api } from '../api'
import MatchResults from './MatchResults'

export default function MatchForm({ bullets }) {
  const [jd, setJd] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const run = async (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    setBusy(true)
    try {
      const res = await api.match(jd)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>Match &amp; gap analysis</h2>
      </div>
      <p className="muted">
        Paste a job description — we rank your bullets by fit and flag the keywords
        you're missing.
      </p>
      <form onSubmit={run}>
        <textarea
          rows={8}
          required
          placeholder="Paste the job description here…"
          value={jd}
          onChange={(e) => setJd(e.target.value)}
        />
        <div className="row-actions">
          <button className="btn-primary" type="submit" disabled={busy || !jd.trim()}>
            {busy ? 'Matching…' : 'Match my resume'}
          </button>
          {bullets.length === 0 && (
            <span className="muted">Add bullets first to enable matching.</span>
          )}
        </div>
      </form>

      {error && <div className="error">{error}</div>}
      <MatchResults result={result} bullets={bullets} />
    </section>
  )
}
