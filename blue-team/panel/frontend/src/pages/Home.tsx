import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heatmap, HBar, ScoreGauge, Timeline } from '../components/Charts'
import { SevBadge } from '../components/SevBadge'
import { api } from '../lib/api'
import { SEV_COLOR, SEV_LABEL, fmtPct, fmtTime, scoreColor, sevOf } from '../lib/format'
import { useLive } from '../lib/live'
import type { Summary } from '../lib/types'

const SCORE_LABEL: Record<string, string> = {
  agents: 'Agentes activos',
  vulnerabilities: 'Vulnerabilidades',
  hardening: 'Hardening (SCA)',
  alerts: 'Carga de alertas',
  coverage: 'Cobertura de agentes',
}

function Kpi({ title, value, sub, tone }: { title: string; value: string | number; sub?: string; tone?: string }) {
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="text-3xl font-bold" style={tone ? { color: tone } : undefined}>
        {value}
      </div>
      {sub && <div className="mt-1 text-xs text-soc-muted">{sub}</div>}
    </div>
  )
}

export function Home() {
  const [range, setRange] = useState<'24h' | '7d'>('24h')
  const { events } = useLive()
  const { data, error, isLoading } = useQuery({
    queryKey: ['summary', range],
    queryFn: () => api<Summary>(`/api/dashboard/summary?range=${range}`),
    refetchInterval: 30000,
  })

  if (isLoading) return <p className="text-soc-muted">Cargando panel…</p>
  if (error || !data) return <p className="text-red-300">No se pudo cargar el resumen: {String(error)}</p>

  const { kpis, score, charts } = data
  const counts = range === '24h' ? kpis.alerts_24h : kpis.alerts_7d
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  const mttd = kpis.mttd.seconds
  const mttdOk = mttd != null && mttd <= kpis.mttd.target_seconds

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Resumen ejecutivo</h1>
        {data.demo_mode && <span className="rounded bg-amber-500/15 px-2 py-0.5 text-xs font-semibold text-amber-300">MODO DEMO</span>}
        <div className="ml-auto flex rounded-md border border-soc-border p-0.5 text-sm">
          {(['24h', '7d'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={clsx('rounded px-3 py-1', range === r ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-slate-200')}
            >
              {r === '24h' ? 'Últimas 24 h' : 'Últimos 7 días'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
        <div className="card">
          <div className="card-title">Security Score</div>
          <ScoreGauge value={score.total} />
          <ul className="space-y-1.5 text-xs">
            {Object.entries(score.breakdown).map(([k, v]) => (
              <li key={k} className="flex items-center gap-2">
                <span className="flex-1 text-soc-muted">{SCORE_LABEL[k] ?? k}</span>
                <span className="w-12 text-right font-mono" style={{ color: scoreColor(v.score) }}>
                  {v.score == null ? 's/d' : v.score.toFixed(0)}
                </span>
                <span className="w-10 text-right text-soc-muted">{v.weight}%</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div className="card col-span-2">
            <div className="card-title">Alertas por severidad · {range}</div>
            <div className="flex items-end gap-3">
              <div className="text-3xl font-bold">{total.toLocaleString('es-ES')}</div>
              <div className="flex flex-1 flex-wrap justify-end gap-2">
                {([4, 3, 2, 1] as const).map((s) => (
                  <div key={s} className="rounded border border-soc-border px-2 py-1 text-center">
                    <div className="text-lg font-semibold" style={{ color: SEV_COLOR[s] }}>
                      {counts[String(s) as keyof typeof counts].toLocaleString('es-ES')}
                    </div>
                    <div className="text-[10px] uppercase text-soc-muted">{SEV_LABEL[s]}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <Kpi
            title="Agentes activos"
            value={`${kpis.agents.active}/${kpis.agents.total}`}
            sub={fmtPct(kpis.agents.pct)}
            tone={scoreColor(kpis.agents.pct)}
          />
          <Kpi
            title="MTTD medio (7 d)"
            value={mttd == null ? '—' : `${mttd.toFixed(0)} s`}
            sub={`Objetivo < ${kpis.mttd.target_seconds} s · ${kpis.mttd.detected}/${kpis.mttd.runs} detectados`}
            tone={mttd == null ? undefined : mttdOk ? '#22c55e' : '#ef4444'}
          />
          <Kpi
            title="Hosts comprometidos"
            value={kpis.hosts_compromised.length}
            sub={kpis.hosts_compromised.join(', ') || 'Ninguno'}
            tone={kpis.hosts_compromised.length ? '#ef4444' : '#22c55e'}
          />
          <Kpi
            title="Hosts en riesgo"
            value={kpis.hosts_at_risk.length}
            sub={kpis.hosts_at_risk.join(', ') || 'Ninguno'}
            tone={kpis.hosts_at_risk.length ? '#f97316' : '#22c55e'}
          />
          <Kpi title="Incidentes" value={`${kpis.incidents.open} abiertos`} sub={`${kpis.incidents.closed} cerrados`} />
          <Kpi title="Cumplimiento SCA" value={fmtPct(kpis.sca_pct)} tone={scoreColor(kpis.sca_pct)} />
        </div>
      </div>

      <div className="card">
        <div className="card-title">Línea temporal de alertas</div>
        <Timeline data={charts.timeline} range={range} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <div className="card-title">Top reglas</div>
          <HBar items={charts.top_rules.map((r) => ({ label: `${r.rule_id} · ${r.title}`, value: r.count, sev: r.severity }))} />
        </div>
        <div className="card">
          <div className="card-title">Top IPs origen</div>
          <HBar items={charts.top_src_ips.map((r) => ({ label: r.ip, value: r.count, sev: r.max_severity }))} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="card">
          <div className="card-title">Mapa de calor por host (24 h, severidad ≥ media)</div>
          <Heatmap data={charts.heatmap} />
        </div>
        <div className="space-y-4">
          <div className="card">
            <div className="card-title">Pool DHCP</div>
            {data.dhcp.map((p) => (
              <div key={p.subnet} className="text-sm">
                <div className="flex justify-between">
                  <span className="font-mono text-xs">
                    {p.start} – {p.end}
                  </span>
                  <span>
                    {p.used}/{p.size}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded bg-soc-bg">
                  <div className="h-2 rounded bg-sky-500" style={{ width: `${p.pct ?? 0}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-title">Servicios (24 h)</div>
            <ul className="space-y-1 text-sm">
              {data.services.map((s) => (
                <li key={s.service} className="flex justify-between gap-2">
                  <span className="truncate">{s.service}</span>
                  <span className="font-mono text-xs" style={{ color: scoreColor(s.uptime_pct) }}>
                    {fmtPct(s.uptime_pct)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="mb-3 flex items-center">
          <div className="card-title mb-0">Alertas en directo</div>
          <Link to="/alertas" className="ml-auto text-xs text-sky-400 hover:underline">
            Ver todas →
          </Link>
        </div>
        {events.length === 0 ? (
          <p className="text-sm text-soc-muted">Esperando eventos…</p>
        ) : (
          <table className="w-full">
            <tbody>
              {events.slice(0, 10).map((e) => (
                <tr key={e.id} className={clsx('border-t border-soc-border', e.severity >= 4 && 'bg-red-500/5')}>
                  <td className="td w-24 font-mono text-xs text-soc-muted">{fmtTime(e.timestamp)}</td>
                  <td className="td w-24">
                    <SevBadge sev={sevOf(e.severity)} />
                  </td>
                  <td className="td w-20 text-xs uppercase text-soc-muted">{e.source}</td>
                  <td className="td">{e.title}</td>
                  <td className="td font-mono text-xs">{e.agent_name ?? e.src_ip ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
