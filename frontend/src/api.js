// Thin fetch wrapper around the backend API. Attaches the JWT (if present) and
// normalises error handling so components can just await and catch.

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

const TOKEN_KEY = 'resume_tailor_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    const detail = data && data.detail ? data.detail : res.statusText
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    const err = new Error(message)
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  signup: (payload) => request('/auth/signup', { method: 'POST', body: payload, auth: false }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload, auth: false }),
  me: () => request('/me'),
  updateMe: (payload) => request('/me', { method: 'PUT', body: payload }),
  listBullets: () => request('/bullets'),
  addBullet: (payload) => request('/bullets', { method: 'POST', body: payload }),
  updateBullet: (id, payload) => request(`/bullets/${id}`, { method: 'PUT', body: payload }),
  deleteBullet: (id) => request(`/bullets/${id}`, { method: 'DELETE' }),
  importResume: (payload) => request('/resume/import', { method: 'POST', body: payload }),
  match: (jobDescription) => request('/match', { method: 'POST', body: { job_description: jobDescription } }),
  generateCV: (jobDescription) => request('/generate-cv', { method: 'POST', body: { job_description: jobDescription } }),
}
