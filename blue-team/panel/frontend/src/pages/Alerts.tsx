import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Fragment, useState } from 'react'
import { SevBadge } from '../components/SevBadge'
import { api } from '../lib/api'
import { SEV_LABEL, fmtDateTime, sevOf } from '../lib/format'
import type { SecEvent } from '../lib/types'

const PAGE = 50

function Detail({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['alert', id], queryFn: () => api<SecEvent>(`/api/alerts/${id}`) })
  if (!data) return <p className="text-xs text-soc-muted">Cargando…</p>
  return (
    <div className="grid gap-4 md:grid-cols-[16rem_1fr]">
      <dl className="space-y-1 text-xs">
        {[
          ['Regla', data.rule_id],
          ['Nivel', data.rule_level],
          ['Categoría', data.category],
          ['Origen', data.src_ip],
          ['Destino', data.dst_ip && `${data.dst_ip}${data.dst_port ? `:${data.dst_port}` : ''}`],
          ['Protocolo', data.protocol],
          ['Agente', data.agent_name && `${data.agent_name} (${data.agent_id})`],
          ['MITRE', data.mitre_ids.join(', ')],
          ['Tácticas', data.mitre_tactics.join(', ')],
        ]
          .filter(([, v]) => v)
          .map(([k, v]) => (
            <div key={k as string} className="flex gap-2">
              <dt className="w-20 shrink-0 text-soc-muted">{k}</dt>
              <dd className="font-mono">{v}</dd>
            </div>
          ))}
      </dl>
      <pre className="max-h-72 overflow-auto rounded bg-soc-bg p-3 text-[11px] text-slate-300">{JSON.stringify(data.raw, null, 2)}</pre>
    </div>
  )
}

export function Alerts() {
  const [source, setSource] = useState('')
  const [minSev, setMinSev] = useState(0)
  const [q, setQ] = useState('')
  const [page, setPage] = useState(0)
  const [open, setOpen] = useState<string | null>(null)

  const params = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE), min_severity: String(minSev) })
  if (source) params.set('source', source)
  if (q.trim()) params.set('q', q.trim())

  const { data, isFetching } = useQuery({
    queryKey: ['alerts', params.toString()],
    queryFn: () => api<{ total: number; items: SecEvent[] }>(`/api/alerts?${params}`),
    placeholderData: keepPreviousData,
    refetchInterval: 15000,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE)) : 1

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Alertas</h1>
      <div className="card flex flex-wrap gap-3">
        <select className="input w-40" value={source} onChange={(e) => (setSource(e.target.value), setPage(0))} aria-label="Fuente">
          <option value="">Todas las fuentes</option>
          <option value="wazuh">Wazuh</option>
          <option value="suricata">Suricata</option>
        </select>
        <select className="input w-44" value={minSev} onChange={(e) => (setMinSev(Number(e.target.value)), setPage(0))} aria-label="Severidad mínima">
          {SEV_LABEL.map((l, i) => (
            <option key={l} value={i}>
              Severidad ≥ {l}
            </option>
          ))}
        </select>
        <input
          className="input flex-1"
          placeholder="Buscar por título, regla, IP o agente…"
          value={q}
          onChange={(e) => (setQ(e.target.value), setPage(0))}
          maxLength={100}
        />
      </div>
      <div className="card overflow-x-auto p-0">
        <table className="w-full">
          <thead className="border-b border-soc-border">
            <tr>
              <th className="th w-8" />
              <th className="th">Fecha</th>
              <th className="th">Severidad</th>
              <th className="th">Fuente</th>
              <th className="th">Regla</th>
              <th className="th">Descripción</th>
              <th className="th">Origen</th>
              <th className="th">Agente</th>
              <th className="th">MITRE</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((e) => (
              <Fragment key={e.id}>
                <tr className="cursor-pointer border-t border-soc-border hover:bg-white/5" onClick={() => setOpen(open === e.id ? null : e.id)}>
                  <td className="td text-soc-muted">{open === e.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}</td>
                  <td className="td whitespace-nowrap font-mono text-xs">{fmtDateTime(e.timestamp)}</td>
                  <td className="td">
                    <SevBadge sev={sevOf(e.severity)} />
                  </td>
                  <td className="td text-xs uppercase text-soc-muted">{e.source}</td>
                  <td className="td font-mono text-xs">{e.rule_id}</td>
                  <td className="td">{e.title}</td>
                  <td className="td font-mono text-xs">{e.src_ip}</td>
                  <td className="td text-xs">{e.agent_name}</td>
                  <td className="td font-mono text-xs">{e.mitre_ids.join(', ')}</td>
                </tr>
                {open === e.id && (
                  <tr className="bg-soc-bg/40">
                    <td colSpan={9} className="p-4">
                      <Detail id={e.id} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
        {data && data.items.length === 0 && <p className="p-4 text-sm text-soc-muted">Sin resultados.</p>}
      </div>
      <div className="flex items-center gap-3 text-sm text-soc-muted">
        <span>{data ? `${data.total.toLocaleString('es-ES')} alertas` : ''}</span>
        {isFetching && <span>Actualizando…</span>}
        <div className="ml-auto flex items-center gap-2">
          <button className="btn-ghost" disabled={page === 0} onClick={() => setPage(page - 1)}>
            Anterior
          </button>
          <span>
            {page + 1} / {pages}
          </span>
          <button className="btn-ghost" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>
            Siguiente
          </button>
        </div>
      </div>
    </div>
  )
}
