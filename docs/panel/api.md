# API del panel

Documentación interactiva (OpenAPI) en `https://<host>:8443/api/docs`, solo con `DEMO_MODE=true`; en modo real se desactiva.

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/api/auth/login` | — | `{username, password}` → cookies de sesión |
| POST | `/api/auth/refresh` | — | renueva el token de acceso |
| POST | `/api/auth/logout` | lector | cierra sesión e invalida tokens |
| GET | `/api/auth/me` | lector | usuario actual |
| POST | `/api/auth/password` | lector | cambia la contraseña propia |
| GET | `/api/dashboard/summary?range=24h\|7d` | lector | KPIs, Security Score y datos de gráficas |
| GET | `/api/alerts` | lector | filtros: `source`, `min_severity`, `q`, `src_ip`, `agent`, `limit`, `offset` |
| GET | `/api/alerts/{id}` | lector | detalle con el JSON original |
| GET | `/api/connectors` | lector | estado de cada conector |
| GET | `/api/state` | lector | estado combinado (agentes, leases, servicios, activos…) |
| POST | `/api/demo/trigger/{hydra_ssh\|nmap_scan\|eicar}` | analista | lanza una simulación (solo en modo demo) |
| GET | `/api/audit` | admin | registro de auditoría |
| GET/POST/PATCH | `/api/users` | admin | gestión de usuarios |
| WS | `/api/ws/events` | lector | `{"type": "event", "data": {...}}` por cada alerta nueva |
| GET | `/api/health` | — | estado del servicio |
