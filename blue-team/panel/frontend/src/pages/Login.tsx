import { Shield } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'

export function Login() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [wait, setWait] = useState(0)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (wait <= 0) return
    const t = setTimeout(() => setWait((w) => w - 1), 1000)
    return () => clearTimeout(t)
  }, [wait])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(username, password)
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setWait(err.retryAfter ?? 60)
        setError('Demasiados intentos fallidos. Espera antes de volver a intentarlo.')
      } else {
        setError(err instanceof ApiError ? err.message : 'No se pudo conectar con el servidor')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex h-full items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4">
        <div className="flex items-center gap-3">
          <Shield className="h-8 w-8 text-soc-accent" />
          <div>
            <h1 className="text-lg font-bold">Omni SOC</h1>
            <p className="text-xs text-soc-muted">Blue Team Command Center</p>
          </div>
        </div>
        <label className="block text-sm">
          Usuario
          <input className="input mt-1" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>
        <label className="block text-sm">
          Contraseña
          <input
            className="input mt-1"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && (
          <p className="rounded bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">
            {error} {wait > 0 && `(${wait} s)`}
          </p>
        )}
        <button className="btn-primary w-full justify-center" disabled={busy || wait > 0}>
          {busy ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}
