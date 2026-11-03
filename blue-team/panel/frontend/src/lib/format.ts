import type { Sev } from './types'

export const SEV_LABEL = ['info', 'baja', 'media', 'alta', 'crítica'] as const
export const SEV_COLOR = ['#64748b', '#22c55e', '#eab308', '#f97316', '#ef4444'] as const

export const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export const fmtDateTime = (iso: string) =>
  new Date(iso).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })

export const fmtPct = (v: number | null | undefined) => (v == null ? '—' : `${v.toFixed(1)} %`)

export const sevOf = (n: number) => Math.max(0, Math.min(4, n)) as Sev

export const scoreColor = (v: number | null) =>
  v == null ? '#64748b' : v >= 80 ? '#22c55e' : v >= 60 ? '#eab308' : v >= 40 ? '#f97316' : '#ef4444'
