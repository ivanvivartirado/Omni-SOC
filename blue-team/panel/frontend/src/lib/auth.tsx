import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, post } from './api'
import type { Role, User } from './types'

interface AuthCtx {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  can: (role: Role) => boolean
}

const RANK: Record<Role, number> = { viewer: 0, analyst: 1, admin: 2 }
const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<User>('/api/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
    const onLogout = () => setUser(null)
    window.addEventListener('soc:logout', onLogout)
    return () => window.removeEventListener('soc:logout', onLogout)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    setUser(await post<User>('/api/auth/login', { username, password }))
  }, [])

  const logout = useCallback(async () => {
    try {
      await post('/api/auth/logout')
    } finally {
      setUser(null)
    }
  }, [])

  const can = useCallback((role: Role) => !!user && RANK[user.role] >= RANK[role], [user])

  return <Ctx.Provider value={{ user, loading, login, logout, can }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth fuera de AuthProvider')
  return ctx
}
