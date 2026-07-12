import { lazy, Suspense, useRef, useState } from 'react'
import { api } from '../api'

// react-pdf is ~1.4 MB; load it only once a CV exists (see CVPdfTools).
const CVPdfTools = lazy(() => import('./CVPdfTools'))

// Download a string as a file (client-side, no server round-trip).
function downloadText(filename, text) {
  const blob = new Blob([text], { type: 'application/x-tex' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function CVView({ bullets }) {
  const [jd, setJd] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)
  const overleafForm = useRef(null)

  const run = async (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    setCopied(false)
    setBusy(true)
    try {
      setResult(await api.generateCV(jd))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(result.tex)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setError('Copy failed — select the text manually.')
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>Generate tailored CV (LaTeX)</h2>
      </div>
      <p className="muted">
        Builds a one-page CV from your profile and the bullets most relevant to this
        job. Preview and download a PDF right here (no LaTeX needed), or grab the{' '}
        <code>.tex</code> to compile in Overleaf.
      </p>

      <form onSubmit={run}>
        <textarea
          rows={6}
          required
          placeholder="Paste the job description…"
          value={jd}
          onChange={(e) => setJd(e.target.value)}
        />
        <div className="row-actions">
          <button className="btn-primary" type="submit" disabled={busy || !jd.trim()}>
            {busy ? 'Generating…' : 'Generate CV'}
          </button>
          {bullets.length === 0 && (
            <span className="muted">Add bullets first to enable CV generation.</span>
          )}
        </div>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="cv-output">
          <Suspense fallback={<p className="muted">Loading PDF tools…</p>}>
            <CVPdfTools content={result.content} filename={result.filename} />
          </Suspense>
          <div className="row-actions cv-toolbar">
            <button className="btn-secondary" onClick={copy}>
              {copied ? 'Copied ✓' : 'Copy .tex'}
            </button>
            <button
              className="btn-secondary"
              onClick={() => downloadText(result.filename, result.tex)}
            >
              Download .tex
            </button>
            {/* Overleaf accepts a form POST of URI-encoded source. */}
            <form
              ref={overleafForm}
              action="https://www.overleaf.com/docs"
              method="post"
              target="_blank"
              rel="noopener"
            >
              <input type="hidden" name="encoded_snip" value={encodeURIComponent(result.tex)} />
              <button className="btn-secondary" type="submit">Open in Overleaf ↗</button>
            </form>
          </div>
          <details className="tex-details">
            <summary>View LaTeX source</summary>
            <pre className="tex-source">{result.tex}</pre>
          </details>
        </div>
      )}
    </section>
  )
}
