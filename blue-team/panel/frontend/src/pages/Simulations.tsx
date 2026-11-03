import { useMutation } from '@tanstack/react-query'
import { Crosshair } from 'lucide-react'
import { useState } from 'react'
import { post } from '../lib/api'
import { useAuth } from '../lib/auth'
import { fmtTime } from '../lib/format'

const SCENARIOS = [
  { id: 'hydra_ssh', title: 'CU2 · Fuerza bruta SSH (Hydra)', desc: 'omni-kali lanza Hydra contra SSH de omni-server. Esperado: reglas 5710/5712/5763 y firma ET SCAN SSH.' },
  { id: 'nmap_scan', title: 'CU3 · Escaneo de puertos (Nmap)', desc: 'Escaneo SYN desde omni-kali a la red. Esperado: firmas ET SCAN de Suricata correladas con el host atacante.' },
  { id: 'eicar', title: 'CU4 · Malware de prueba (EICAR)', desc: 'Descarga de EICAR en omni-cliente. Esperado: FIM 554, rootcheck 52502 y VirusTotal 87105.' },
]

interface RunResult {
  scenario: string
  started_at: string
  detected_at: string | null
}

export function Simulations({ demo }: { demo: boolean }) {
  const { can } = useAuth()
  const [results, setResults] = useState<RunResult[]>([])
  const run = useMutation({
    mutationFn: (id: string) => post<RunResult>(`/api/demo/trigger/${id}`),
    onSuccess: (r) => setResults((prev) => [r, ...prev].slice(0, 10)),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Simulaciones de ataque</h1>
      <p className="max-w-3xl text-sm text-soc-muted">
        {demo
          ? 'En modo demo se inyectan los eventos que generaría cada ataque real para comprobar la detección y el MTTD.'
          : 'En modo real lanza el ataque desde omni-kali; el seguimiento automático de detección llega en la fase 4.'}
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        {SCENARIOS.map((s) => (
          <div key={s.id} className="card flex flex-col">
            <div className="mb-2 flex items-center gap-2 font-medium">
              <Crosshair className="h-4 w-4 text-red-400" /> {s.title}
            </div>
            <p className="flex-1 text-sm text-soc-muted">{s.desc}</p>
            {demo && (
              <button
                className="btn-primary mt-4 self-start"
                disabled={!can('analyst') || run.isPending}
                title={can('analyst') ? undefined : 'Requiere rol analista'}
                onClick={() => run.mutate(s.id)}
              >
                Simular
              </button>
            )}
          </div>
        ))}
      </div>
      {run.error && <p className="text-sm text-red-300">{String(run.error)}</p>}
      {results.length > 0 && (
        <div className="card">
          <div className="card-title">Ejecuciones de esta sesión</div>
          <ul className="space-y-1 text-sm">
            {results.map((r) => (
              <li key={r.started_at + r.scenario} className="font-mono text-xs">
                {fmtTime(r.started_at)} · {r.scenario} ·{' '}
                {r.detected_at
                  ? `detección prevista en ${((Date.parse(r.detected_at) - Date.parse(r.started_at)) / 1000).toFixed(1)} s`
                  : 'sin detección'}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
