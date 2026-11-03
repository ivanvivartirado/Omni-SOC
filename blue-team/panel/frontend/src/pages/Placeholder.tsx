import { useQuery } from '@tanstack/react-query'
import { Construction } from 'lucide-react'
import { api } from '../lib/api'
import type { ConnectorInfo } from '../lib/types'

export function Placeholder({ title, phase, items, connectors = [] }: { title: string; phase: number; items: string[]; connectors?: string[] }) {
  const { data } = useQuery({ queryKey: ['connectors'], queryFn: () => api<ConnectorInfo[]>('/api/connectors'), refetchInterval: 30000 })
  const relevant = data?.filter((c) => connectors.includes(c.name)) ?? []
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{title}</h1>
      <div className="card max-w-2xl">
        <div className="mb-3 flex items-center gap-2 text-amber-300">
          <Construction className="h-5 w-5" /> Módulo previsto para la fase {phase}
        </div>
        <ul className="list-inside list-disc space-y-1 text-sm text-soc-muted">
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
      </div>
      {relevant.length > 0 && (
        <div className="card max-w-2xl">
          <div className="card-title">Estado de las fuentes</div>
          <ConnectorList items={relevant} />
        </div>
      )}
    </div>
  )
}

export function ConnectorList({ items }: { items: ConnectorInfo[] }) {
  return (
    <ul className="divide-y divide-soc-border text-sm">
      {items.map((c) => (
        <li key={c.name} className="flex items-center gap-3 py-2">
          <span className={`h-2.5 w-2.5 rounded-full ${c.ok == null ? 'bg-slate-500' : c.ok ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="flex-1">{c.label}</span>
          <span className="rounded bg-white/5 px-2 py-0.5 text-xs uppercase text-soc-muted">{c.mode}</span>
          <span className="w-56 truncate text-right text-xs text-soc-muted" title={c.detail}>
            {c.detail}
          </span>
        </li>
      ))}
    </ul>
  )
}
