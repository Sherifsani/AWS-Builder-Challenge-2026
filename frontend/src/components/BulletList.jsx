import { useState } from 'react'
import { api } from '../api'

const EMPTY = { bullet: '', project: '', skills: '', category: '', impact_metric: '' }

// The form uses a comma-separated string for skills; convert to/from the API's list.
function toPayload(form) {
  return {
    bullet: form.bullet.trim(),
    project: form.project.trim() || null,
    skills: form.skills
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
    category: form.category.trim() || null,
    impact_metric: form.impact_metric.trim() || null,
  }
}

function BulletForm({ initial, onSubmit, onCancel, submitLabel }) {
  const [form, setForm] = useState(initial)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (!form.bullet.trim()) return
    setBusy(true)
    try {
      await onSubmit(toPayload(form))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="bullet-form" onSubmit={submit}>
      <textarea
        rows={2}
        required
        placeholder="Resume bullet, e.g. Built a FastAPI service handling 1k rps"
        value={form.bullet}
        onChange={set('bullet')}
      />
      <div className="grid-2">
        <input placeholder="Project" value={form.project} onChange={set('project')} />
        <input placeholder="Category (backend / cloud / AI / frontend)" value={form.category} onChange={set('category')} />
      </div>
      <div className="grid-2">
        <input placeholder="Skills (comma separated)" value={form.skills} onChange={set('skills')} />
        <input placeholder="Impact metric (optional)" value={form.impact_metric} onChange={set('impact_metric')} />
      </div>
      <div className="row-actions">
        <button className="btn-primary" type="submit" disabled={busy}>
          {busy ? 'Saving…' : submitLabel}
        </button>
        {onCancel && (
          <button className="btn-ghost" type="button" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}

export default function BulletList({ bullets, onChange }) {
  const [adding, setAdding] = useState(false)
  const [editingId, setEditingId] = useState(null)

  const add = async (payload) => {
    await api.addBullet(payload)
    setAdding(false)
    onChange()
  }
  const update = async (id, payload) => {
    await api.updateBullet(id, payload)
    setEditingId(null)
    onChange()
  }
  const remove = async (id) => {
    await api.deleteBullet(id)
    onChange()
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>Your bullets <span className="count">{bullets.length}</span></h2>
        {!adding && (
          <button className="btn-secondary" onClick={() => setAdding(true)}>
            + Add bullet
          </button>
        )}
      </div>

      {adding && (
        <BulletForm
          initial={{ ...EMPTY }}
          onSubmit={add}
          onCancel={() => setAdding(false)}
          submitLabel="Add bullet"
        />
      )}

      {bullets.length === 0 && !adding && (
        <p className="muted">No bullets yet. Add one, or import a resume above.</p>
      )}

      <ul className="bullets">
        {bullets.map((b) =>
          editingId === b.bullet_id ? (
            <li key={b.bullet_id}>
              <BulletForm
                initial={{
                  bullet: b.bullet || '',
                  project: b.project || '',
                  skills: (b.skills || []).join(', '),
                  category: b.category || '',
                  impact_metric: b.impact_metric || '',
                }}
                onSubmit={(p) => update(b.bullet_id, p)}
                onCancel={() => setEditingId(null)}
                submitLabel="Save changes"
              />
            </li>
          ) : (
            <li key={b.bullet_id} className="bullet-item">
              <div className="bullet-main">
                <p className="bullet-text">{b.bullet}</p>
                <div className="tags">
                  {b.project && <span className="tag">{b.project}</span>}
                  {b.category && <span className="tag tag-cat">{b.category}</span>}
                  {(b.skills || []).map((s) => (
                    <span className="tag tag-skill" key={s}>{s}</span>
                  ))}
                  {b.impact_metric && <span className="tag tag-impact">{b.impact_metric}</span>}
                </div>
              </div>
              <div className="bullet-actions">
                <button className="btn-link" onClick={() => setEditingId(b.bullet_id)}>Edit</button>
                <button className="btn-link danger" onClick={() => remove(b.bullet_id)}>Delete</button>
              </div>
            </li>
          )
        )}
      </ul>
    </section>
  )
}
