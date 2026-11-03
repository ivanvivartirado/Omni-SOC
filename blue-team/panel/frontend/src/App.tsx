import { useQuery } from '@tanstack/react-query'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { api } from './lib/api'
import { useAuth } from './lib/auth'
import { LiveProvider } from './lib/live'
import { Alerts } from './pages/Alerts'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Placeholder } from './pages/Placeholder'
import { Settings } from './pages/Settings'
import { Simulations } from './pages/Simulations'

const STUBS = [
  { path: 'wazuh', title: 'Wazuh', phase: 2, connectors: ['wazuh'], items: ['Agentes y estado', 'FIM, SCA y vulnerabilidades', 'Mapeo MITRE ATT&CK', 'Compatibilidad 4.7 y 4.8+'] },
  { path: 'suricata', title: 'Suricata', phase: 2, connectors: ['suricata'], items: ['Alertas de eve.json', 'Firmas, categorías y protocolos', 'Correlación con Wazuh'] },
  {
    path: 'infraestructura',
    title: 'Infraestructura',
    phase: 3,
    connectors: ['kea', 'dns', 'pfsense', 'services'],
    items: ['Kea: concesiones, reservas y dispositivos desconocidos', 'BIND9: estado y dominios sospechosos', 'pfSense', 'Salud de servicios y certificados'],
  },
  { path: 'topologia', title: 'Topología', phase: 3, items: ['Mapa interactivo de la red 192.168.15.0/24 con estado en vivo'] },
  { path: 'activos', title: 'Activos', phase: 3, items: ['Inventario con IP, MAC, SO, rol, criticidad, agente y vulnerabilidades'] },
  { path: 'incidentes', title: 'Incidentes', phase: 4, items: ['Alerta → incidente', 'Playbooks SSH, escaneo y malware', 'Exportación CSV/PDF'] },
]

function Shell() {
  const health = useQuery({ queryKey: ['health'], queryFn: () => api<{ demo_mode: boolean }>('/api/health'), staleTime: Infinity })
  return (
    <LiveProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="alertas" element={<Alerts />} />
          {STUBS.map((s) => (
            <Route key={s.path} path={s.path} element={<Placeholder {...s} />} />
          ))}
          <Route path="simulaciones" element={<Simulations demo={health.data?.demo_mode ?? false} />} />
          <Route path="configuracion" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </LiveProvider>
  )
}

export default function App() {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Shell /> : <Login />
}
