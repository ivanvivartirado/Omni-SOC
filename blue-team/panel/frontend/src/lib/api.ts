export class ApiError extends Error {
  constructor(public status: number, message: string, public retryAfter?: number) {
    super(message)
  }
}

function csrfToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return m ? decodeURIComponent(m[1]) : ''
}

let refreshing: Promise<boolean> | null = null

async function refresh(): Promise<boolean> {
  refreshing ??= fetch('/api/auth/refresh', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRF-Token': csrfToken() },
  })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => setTimeout(() => (refreshing = null), 0))
  return refreshing
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD'].includes(method)) headers.set('X-CSRF-Token', csrfToken())
  const res = await fetch(path, { ...init, method, headers, credentials: 'same-origin' })
  if (res.status === 401 && retry && !path.startsWith('/api/auth/')) {
    if (await refresh()) return api<T>(path, init, false)
    window.dispatchEvent(new Event('soc:logout'))
  }
  if (!res.ok) {
    let msg = res.statusText
    try {
      const body = await res.json()
      msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(res.status, msg, Number(res.headers.get('Retry-After')) || undefined)
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
