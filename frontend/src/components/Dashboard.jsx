import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import BulletList from './BulletList'
import ResumeUpload from './ResumeUpload'
import MatchForm from './MatchForm'
import CVView from './CVView'

export default function Dashboard({ profile, onProfileChange }) {
  const [bullets, setBullets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadBullets = useCallback(async () => {
    setError(null)
    try {
      const items = await api.listBullets()
      setBullets(items)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBullets()
  }, [loadBullets])

  return (
    <div className="dashboard">
      <ProfileCard profile={profile} onProfileChange={onProfileChange} />

      <section className="card">
        <div className="card-head">
          <h2>Import</h2>
        </div>
        <p className="muted">
          Upload an existing resume and we'll extract structured bullets automatically.
        </p>
        <ResumeUpload onImported={loadBullets} />
      </section>

      {error && <div className="error">{error}</div>}
      {loading ? (
        <p className="muted">Loading bullets…</p>
      ) : (
        <BulletList bullets={bullets} onChange={loadBullets} />
      )}

      <MatchForm bullets={bullets} />

      <CVView bullets={bullets} />
    </div>
  )
}

function ProfileCard({ profile, onProfileChange }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: profile?.name || '',
    contact: profile?.contact || '',
    headline: profile?.headline || '',
  })
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const updated = await api.updateMe(form)
      onProfileChange(updated)
      setEditing(false)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>Profile</h2>
        {!editing && (
          <button className="btn-ghost" onClick={() => setEditing(true)}>Edit</button>
        )}
      </div>
      {editing ? (
        <form onSubmit={save}>
          <div className="grid-2">
            <label>Name<input value={form.name} onChange={set('name')} /></label>
            <label>Contact<input value={form.contact} onChange={set('contact')} /></label>
          </div>
          <label>Headline<input value={form.headline} onChange={set('headline')} placeholder="Backend Engineer" /></label>
          <div className="row-actions">
            <button className="btn-primary" type="submit" disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </button>
            <button className="btn-ghost" type="button" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </form>
      ) : (
        <div className="profile-view">
          <p><strong>{profile?.name || '—'}</strong> {profile?.headline && <span className="muted">· {profile.headline}</span>}</p>
          <p className="muted">{profile?.contact || profile?.email}</p>
        </div>
      )}
    </section>
  )
}
