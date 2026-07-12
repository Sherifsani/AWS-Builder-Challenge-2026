import { useCallback, useEffect, useMemo, useState } from 'react'
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
      setBullets(await api.listBullets())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBullets()
  }, [loadBullets])

  // Re-imports can add education/sections to the profile — refresh both.
  const afterImport = useCallback(async () => {
    await loadBullets()
    try {
      onProfileChange(await api.me())
    } catch {
      /* non-fatal */
    }
  }, [loadBullets, onProfileChange])

  const stats = useMemo(() => {
    const skills = new Set()
    const projects = new Set()
    for (const b of bullets) {
      ;(b.skills || []).forEach((s) => skills.add(s.toLowerCase()))
      if (b.project) projects.add(b.project)
    }
    return { bullets: bullets.length, skills: skills.size, projects: projects.size }
  }, [bullets])

  return (
    <div className="workbench">
      <aside className="rail">
        <ProfileCard profile={profile} onProfileChange={onProfileChange} />

        <div className="card">
          <div className="stats">
            <div className="stat">
              <div className="stat-num">{stats.bullets}</div>
              <div className="stat-label">Bullets</div>
            </div>
            <div className="stat">
              <div className="stat-num">{stats.skills}</div>
              <div className="stat-label">Skills</div>
            </div>
            <div className="stat">
              <div className="stat-num">{stats.projects}</div>
              <div className="stat-label">Projects</div>
            </div>
            <div className="stat">
              <div className="stat-num">{profile?.education?.length || 0}</div>
              <div className="stat-label">Education</div>
            </div>
          </div>
        </div>

        <CapturedSections profile={profile} />
      </aside>

      <div className="flow">
        <section className="stage">
          <div className="stage-label"><span className="stage-num">01</span> Your material</div>
          <div className="card">
            <div className="card-head"><h2>Import a resume</h2></div>
            <p className="muted">
              Upload a PDF or DOCX. We extract your bullets, education, and other
              sections automatically — nothing gets dropped.
            </p>
            <ResumeUpload onImported={afterImport} />
          </div>

          {error && <div className="error" style={{ marginTop: 14 }}>{error}</div>}
          {loading ? (
            <div className="card" style={{ marginTop: 18 }}><p className="muted">Loading bullets…</p></div>
          ) : (
            <BulletList bullets={bullets} onChange={loadBullets} />
          )}
        </section>

        <section className="stage">
          <div className="stage-label"><span className="stage-num">02</span> Tailor to a job</div>
          <MatchForm bullets={bullets} />
        </section>

        <section className="stage">
          <div className="stage-label"><span className="stage-num">03</span> Generate CV</div>
          <CVView bullets={bullets} />
        </section>
      </div>
    </div>
  )
}

function CapturedSections({ profile }) {
  const education = profile?.education || []
  const sections = profile?.sections || []
  if (education.length === 0 && sections.length === 0) return null

  return (
    <div className="card">
      <div className="card-head"><h2>Captured</h2></div>
      <p className="muted">Kept verbatim for your CV.</p>
      <ul className="mini-list">
        {education.map((e, i) => (
          <li key={`e${i}`}>
            <div className="t">{e.credential || e.institution}</div>
            <div className="s">{[e.institution, e.date].filter(Boolean).join(' · ')}</div>
          </li>
        ))}
        {sections.map((s, i) => (
          <li key={`s${i}`}>
            <div className="t">{s.title}</div>
            <div className="s">{(s.items || []).length} item{(s.items || []).length === 1 ? '' : 's'}</div>
          </li>
        ))}
      </ul>
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
      onProfileChange(await api.updateMe(form))
      setEditing(false)
    } finally {
      setBusy(false)
    }
  }

  const initials = (profile?.name || profile?.email || '?')
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')

  return (
    <section className="card profile-card">
      {editing ? (
        <form onSubmit={save}>
          <label>Name<input value={form.name} onChange={set('name')} placeholder="Ada Lovelace" /></label>
          <label>Headline<input value={form.headline} onChange={set('headline')} placeholder="Backend Engineer" /></label>
          <label>Contact<input value={form.contact} onChange={set('contact')} placeholder="email · github · linkedin" /></label>
          <div className="row-actions">
            <button className="btn-primary" type="submit" disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </button>
            <button className="btn-ghost" type="button" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </form>
      ) : (
        <>
          <div className="profile-head">
            <div className="avatar">{initials}</div>
            <div>
              <h2>{profile?.name || 'Your name'}</h2>
              <div className="headline">{profile?.headline || 'Add a headline'}</div>
            </div>
          </div>
          <p className="profile-contact">{profile?.contact || profile?.email}</p>
          <div className="row-actions" style={{ marginTop: 12 }}>
            <button className="btn-secondary" onClick={() => setEditing(true)}>Edit profile</button>
          </div>
        </>
      )}
    </section>
  )
}
