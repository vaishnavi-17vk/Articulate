
 // The only file that talks to the backend. Components call these functions and never use axios
// directly.
import axios from 'axios'

export interface User {
  id: string
  email: string
  created_at: string
}

interface TokenResponse {
  access_token: string
  token_type: string
}

const TOKEN_KEY = 'articulate.token'
let memoryToken: string | null = null

/** Token persistence. Falls back to memory when browser storage is unavailable. */
export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY) ?? memoryToken
    } catch {
      return memoryToken
    }
  },
  set(token: string): void {
    memoryToken = token
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* storage unavailable, memory copy is used for this tab */
    }
  },
  clear(): void {
    memoryToken = null
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* nothing to clear */
    }
  },
}

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function registerUser(email: string, password: string): Promise<User> {
  const { data } = await http.post<User>('/auth/register', { email, password })
  return data
}

export async function loginUser(email: string, password: string): Promise<string> {
  const { data } = await http.post<TokenResponse>('/auth/login', { email, password })
  return data.access_token
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await http.get<User>('/auth/me')
  return data
}

export function isUnauthorised(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 401
}

export function isConflict(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 409
}

/** Turn any thrown value into a sentence that is safe to show a user. */
export function errorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback
  if (!error.response) return 'Cannot reach the server. Check your connection and try again.'

  const detail: unknown = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (first?.msg) return first.msg.replace(/^Value error, /, '')
  }
  return fallback
}
