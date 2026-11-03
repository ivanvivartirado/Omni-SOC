import clsx from 'clsx'
import {
  Activity, Bell, BellOff, Boxes, Crosshair, FileWarning, Gauge, LogOut, Network, Radar, Router, Settings, Shield, ShieldAlert,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { useLive } from '../lib/live'

const NAV = [
  { to: '/', label: 'Inicio', icon: Gauge, end: true },
  { to: '/alertas', label: 'Alertas', icon: ShieldAlert },
  { to: '/wazuh', label: 'Wazuh', icon: Shield },
  { to: '/suricata', label: 'Suricata', icon: Radar },
  { to: '/infraestructura', label: 'Infraestructura', icon: Router },
  { to: '/topologia', label: 'Topología', icon: Network },
  { to: '/activos', label: 'Activos', icon: Boxes },
  { to: '/incidentes', label: 'Incidentes', icon: FileWarning },
  { to: '/simulaciones', label: 'Simulaciones', icon: Crosshair },
  { to: '/configuracion', label: 'Configuración', icon: Settings },
]

const ROLE_LABEL = { admin: 'Administrador', analyst: 'Analista', viewer: 'Lector' }

export function Layout() {
  const { user, logout } = useAuth()
  const { connected, lastCritical, sound, setSound } = useLive()
  const [flash, setFlash] = useState<string | null>(null)

  useEffect(() => {
    if (!lastCritical) return
    setFlash(lastCritical.id)
    const t = setTimeout(() => setFlash(null), 8000)
    return () => clearTimeout(t)
  }, [lastCritical])

  return (
    <div className="flex h-full">
      <aside className="flex w-56 shrink-0 flex-col border-r border-soc-border bg-soc-panel">
        <div className="flex items-center gap-2 px-4 py-4">
          <Shield className="h-6 w-6 text-soc-accent" />
          <div>
            <div className="text-sm font-bold tracking-wide">OMNI SOC</div>
            <div className="text-[10px] uppercase tracking-widest text-soc-muted">Blue Team Command Center</div>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 px-2">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm',
                  isActive ? 'bg-sky-500/10 text-sky-300' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-soc-border p-3 text-xs">
          <div className="font-medium text-slate-300">{user?.full_name || user?.username}</div>
          <div className="text-soc-muted">{user && ROLE_LABEL[user.role]}</div>
          <button className="btn-ghost mt-2 w-full justify-center" onClick={logout}>
            <LogOut className="h-4 w-4" /> Cerrar sesión
          </button>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end gap-4 border-b border-soc-border px-6 py-2 text-xs">
          {flash && lastCritical && (
            <div className="flash-critical mr-auto truncate rounded bg-red-500/15 px-3 py-1 text-red-300" role="alert">
              CRÍTICA · {lastCritical.title} {lastCritical.agent_name ? `· ${lastCritical.agent_name}` : ''}
            </div>
          )}
          <button
            className="btn-ghost py-1"
            onClick={() => setSound(!sound)}
            title={sound ? 'Silenciar alertas críticas' : 'Activar sonido en alertas críticas'}
          >
            {sound ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
          </button>
          <span className="flex items-center gap-2">
            <Activity className={clsx('h-4 w-4', connected ? 'text-green-400' : 'text-red-400')} />
            {connected ? 'Tiempo real' : 'Reconectando…'}
          </span>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
