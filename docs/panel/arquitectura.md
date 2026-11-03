# Arquitectura del panel

```
navegador ──HTTPS 8443──▶ web (Nginx: TLS, estáticos, proxy /api y WebSocket)
                              │
                              ▼
                         api (FastAPI, 1 proceso)
                         ├── ConnectorManager: tareas asyncio que consultan cada conector
                         │     ├── eventos cada EVENTS_POLL_SECONDS (2 s)  → SQLite + WebSocket
                         │     └── estado cada STATE_POLL_SECONDS (30 s)   → memoria
                         ├── API REST /api/*  (auth, dashboard, alertas, usuarios, auditoría)
                         └── SQLite en volumen (eventos, usuarios, auditoría, incidentes, ataques)
```

## Conectores

Cada fuente implementa `BaseConnector` (`backend/app/connectors/base.py`):

| Método | Uso |
|---|---|
| `health()` | estado de la conexión, se muestra en Configuración |
| `collect_events(since)` | eventos nuevos normalizados a `SecurityEvent` |
| `collect_state()` | foto del estado: agentes, SCA, vulnerabilidades, leases, servicios, activos… |

El registro (`connectors/registry.py`) elige la implementación según `DEMO_MODE`. En la fase 1 solo existen las implementaciones demo (`app/demo/`); con `DEMO_MODE=false` los conectores aparecen como *pendiente* hasta su fase.

| Conector | Fuente real prevista | Fase |
|---|---|---|
| Wazuh | API 55000 (agentes, SCA, vulnerabilidades) + Indexer 9200 (alertas). Detecta 4.7 / 4.8+ | 2 |
| Suricata | `/var/log/suricata/eve.json` (lectura incremental, montado en solo lectura) | 2 |
| Kea | `/var/lib/kea/kea-leases4.csv` + `kea-dhcp4.conf` | 3 |
| DNS | BIND9 (`rndc status`, log de consultas) | 3 |
| pfSense | API / syslog | 3 |
| Servicios | comprobaciones HTTP/TCP/TLS desde el propio panel | 3 |
| GitHub | GitHub Projects (token de solo lectura) | 5 |

## Modo demo

`app/demo/world.py` simula la red real del laboratorio (omni-server, omni-cliente, omni-kali, pfSense y varios equipos de oficina) con tráfico de fondo y ataques periódicos. Los IDs de regla son los de Wazuh y Suricata (p. ej. 5710/5712/5763 para fuerza bruta SSH, 2001219 ET SCAN, 554/87105 para EICAR), así que lo que se ve en demo es lo mismo que se verá con datos reales.

## Fases

| Fase | Contenido |
|---|---|
| 1 | Esqueleto, modo demo, auth/RBAC/auditoría, Home ejecutiva, alertas en directo, Docker, CI |
| 2 | Conectores reales Wazuh (4.7 y 4.8+) y Suricata, correlación, vistas Wazuh y Suricata |
| 3 | Kea, DNS, pfSense, salud de servicios, inventario de activos y topología |
| 4 | Incidentes y playbooks, simulaciones CU2-CU4 con medición real de MTTD, exportación CSV/PDF |
| 5 | Notificaciones (Telegram, email, Discord/Slack), GitHub Projects, despliegue con Ansible y pulido |
