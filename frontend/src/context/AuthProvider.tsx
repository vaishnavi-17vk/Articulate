
 // Holds the signed-in user and the login, register and logout actions, and restores the session
// when the page loads.
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import {
  fetchCurrentUser,
  isUnauthorised,
  loginUser,
  registerUser,
  tokenStore,
} from '../services/api'
import type { User } from '../services/api'
import { AuthContext } from './auth-context'
import type { AuthContextValue, AuthStatus } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  // Restore the session on first load if a token is already stored.
  useEffect(() => {
    let cancelled = false

    async function restore() {
      if (!tokenStore.get()) {
        setStatus('anonymous')
        return
      }
      try {
        const me = await fetchCurrentUser()
        if (!cancelled) {
          setUser(me)
          setStatus('authenticated')
        }
      } catch (error) {
        // Only discard the token when the server says it is invalid.
        if (isUnauthorised(error)) tokenStore.clear()
        if (!cancelled) {
          setUser(null)
          setStatus('anonymous')
        }
      }
    }

    void restore()
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const token = await loginUser(email, password)
    tokenStore.set(token)
    try {
      const me = await fetchCurrentUser()
      setUser(me)
      setStatus('authenticated')
    } catch (error) {
      tokenStore.clear()
      throw error
    }
  }, [])

  const register = useCallback(
    async (email: string, password: string) => {
      await registerUser(email, password)
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
