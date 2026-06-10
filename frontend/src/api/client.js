import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: `${BASE}/api`, timeout: 60000 })

api.interceptors.response.use(
  res => res,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(msg))
  }
)

export const sendMessage = (sessionId, message, customerId = null) =>
  api.post('/chat', {
    session_id: sessionId,
    message,
    ...(customerId && { customer_id: customerId })
  }).then(r => r.data)

export const fetchTrace = (sessionId) =>
  api.get(`/trace/${sessionId}`).then(r => r.data)

export const fetchSessions = () =>
  api.get('/sessions').then(r => r.data)

export const deleteSession = (sessionId) =>
  api.delete(`/sessions/${sessionId}`).then(r => r.data)

export const fetchPolicy = () =>
  api.get('/policy').then(r => r.data)

export const fetchTickets = () =>
  api.get('/tickets').then(r => r.data)

export const fetchMetrics = () =>
  api.get('/metrics').then(r => r.data)

export const createTraceStream = (sessionId, onStep, onError) => {
  const source = new EventSource(`${BASE}/api/trace-stream/${sessionId}`)
  source.onmessage = (e) => {
    try { onStep(JSON.parse(e.data)) } catch (_) {}
  }
  source.onerror = onError
  return source
}