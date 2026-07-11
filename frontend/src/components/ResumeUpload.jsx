import { useRef, useState } from 'react'
import { api } from '../api'

// Read a File as base64 (strip the "data:...;base64," prefix the API doesn't want).
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function ResumeUpload({ onImported }) {
  const inputRef = useRef(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)

  const handleFile = async (file) => {
    if (!file) return
    setError(null)
    setStatus(null)
    setBusy(true)
    try {
      const content_base64 = await fileToBase64(file)
      const res = await api.importResume({ filename: file.name, content_base64 })
      setStatus(`Imported ${res.imported} bullet${res.imported === 1 ? '' : 's'}.`)
      onImported?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="upload">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        style={{ display: 'none' }}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <button
        className="btn-secondary"
        disabled={busy}
        onClick={() => inputRef.current?.click()}
      >
        {busy ? 'Parsing resume…' : 'Import from resume (PDF/DOCX)'}
      </button>
      {status && <span className="ok">{status}</span>}
      {error && <span className="error inline">{error}</span>}
    </div>
  )
}
