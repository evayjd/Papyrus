import { useAuthStore } from '@/stores/auth'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const authStore = useAuthStore()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }

  if (response.status === 204) return null as T
  return response.json()
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, display_name?: string) =>
    request<{ access_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name }),
    }),

  // Sessions
  createSession: (title?: string) =>
    request<{ id: string; title: string; status: string }>('/sessions/', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  listSessions: () =>
    request<Array<{ id: string; title: string; status: string; created_at: string }>>('/sessions/'),

  // Reports
  listReports: () =>
    request<Array<{ id: string; title: string; created_at: string }>>('/reports/'),

  getReport: (id: string) =>
    request<{ id: string; title: string; content: { markdown: string; papers: any[] }; created_at: string }>(`/reports/${id}`),

  deleteReport: (id: string) =>
    request<null>(`/reports/${id}`, { method: 'DELETE' }),
}

export function createWebSocket(sessionId: string): WebSocket {
  const wsBase = BASE_URL.replace('http', 'ws')
  return new WebSocket(`${wsBase}/research/ws/${sessionId}`)
}