import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { fmtDateTime } from '../lib/format'
import type { ConnectorInfo } from '../lib/types'
import { ConnectorList } from './Placeholder'

interface AuditItem { id: number; ts: string; username: string; action: string; target: string; ip: string }

export function Settings() {
  const { can } = useAuth()
  const connectors = useQuery({ queryKey: ['connectors'], queryFn: () => api<ConnectorInfo[]>('/api/connectors'), refetchInterval: 30000 })
  const audit = useQuery({
    queryKey: ['audit'],
    queryFn: () => api<{ total: number; items: AuditItem[] }>('/api/audit?limit=50'),
    enabled: can('admin'),
  })
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Configuración</h1>
      <div className="card max-w-3xl">
        <div className="card-title">Conectores</div>
        {connectors.data && <ConnectorList items={connectors.data} />}
        <p className="mt-3 text-xs text-soc-muted">
          Las credenciales y el modo (demo/real) se configuran con variables de entorno en <code>.env</code>; nunca se guardan en el repositorio.
        </p>
      </div>
      {can('admin') && (
        <div className="card overflow-x-auto">
          <div className="card-title">Registro de auditoría</div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">Fecha</th>
                <th className="th">Usuario</th>
                <th className="th">Acción</th>
                <th className="th">Objetivo</th>
                <th className="th">IP</th>
              </tr>
            </thead>
            <tbody>
              {audit.data?.items.map((a) => (
                <tr key={a.id} className="border-t border-soc-border">
                  <td className="td font-mono text-xs">{fmtDateTime(a.ts)}</td>
                  <td className="td">{a.username}</td>
                  <td className="td font-mono text-xs">{a.action}</td>
                  <td className="td text-xs">{a.target}</td>
                  <td className="td font-mono text-xs">{a.ip}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
