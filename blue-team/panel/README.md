# Omni SOC · Blue Team Command Center

Panel web único para el equipo defensivo de Omni SOC: reúne en una sola consola lo que hoy está repartido entre Wazuh, Suricata/EveBox, Kea, BIND9, pfSense y Apache.

> Estado: **fase 1** (esqueleto, modo demo, autenticación, Home ejecutiva y alertas en directo). Las fases siguientes conectan las fuentes reales. Ver [hoja de ruta](../../docs/panel/arquitectura.md#fases).

## Arranque rápido (modo demo)

```bash
cd blue-team/panel
cp .env.example .env          # ajusta ALLOWED_ORIGINS con la IP/nombre con el que vas a entrar
docker compose up -d --build
docker compose logs api | grep -A2 "Contraseña inicial"   # si dejaste ADMIN_PASSWORD vacío
```

Abre `https://192.168.15.122:8443` (o `https://localhost:8443`). El certificado es autofirmado: acéptalo o monta uno propio en el volumen `panel-certs` (`panel.crt` / `panel.key`).

En modo demo el panel genera 7 días de histórico realista de la red `192.168.15.0/24` y sigue produciendo eventos en directo. Desde **Simulaciones** un analista puede lanzar los casos de uso CU2 (Hydra), CU3 (Nmap) y CU4 (EICAR) y ver cómo llegan las alertas.

## Qué incluye la fase 1

| Área | Contenido |
|---|---|
| Home | Security Score 0-100 con desglose, alertas por severidad (24 h / 7 d), agentes activos, MTTD frente al objetivo de 60 s, hosts comprometidos / en riesgo, incidentes, cumplimiento SCA, línea temporal, top reglas, top IPs, mapa de calor por host, pool DHCP y uptime de servicios |
| Alertas | Tabla Wazuh + Suricata con filtros (fuente, severidad, búsqueda), paginación y detalle con JSON original y MITRE |
| Tiempo real | WebSocket `/api/ws/events`; aviso visual y sonoro (opcional) de alertas críticas |
| Seguridad | Login con Argon2id, JWT en cookies HttpOnly + SameSite=Strict, CSRF, bloqueo progresivo por usuario e IP, roles admin / analista / lector, registro de auditoría, TLS, cabeceras de seguridad |
| Conectores | Interfaz común con implementación demo para Wazuh, Suricata, Kea, DNS, pfSense, servicios y GitHub |

## Consumo de recursos

omni-server va justo de RAM, así que el panel son solo 2 contenedores con límite de memoria:

| Contenedor | Límite | Uso medido en demo |
|---|---|---|
| `api` (FastAPI + SQLite) | 256 MB | ~80 MB |
| `web` (Nginx + frontend estático) | 64 MB | ~4 MB |

Sin Redis, Celery ni PostgreSQL. Si más adelante hace falta, `DATABASE_URL` admite PostgreSQL.

## Configuración

Todo se configura con variables de entorno en `.env` (ver [`.env.example`](.env.example)). `.env` está en `.gitignore`: **no subas nunca credenciales al repo**. Si `SECRET_KEY` o `ADMIN_PASSWORD` se dejan vacíos se generan automáticamente.

## Desarrollo

```bash
# Backend (Python 3.12)
cd backend
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
ADMIN_PASSWORD='Dev-Password-123' COOKIE_SECURE=false ALLOWED_ORIGINS=http://localhost:5173 \
  .venv/bin/uvicorn app.main:app --reload
.venv/bin/ruff check app tests && .venv/bin/pytest

# Frontend (Node 20)
cd frontend
npm install
npm run dev        # http://localhost:5173, proxy de /api a 127.0.0.1:8000
npm run lint && npm run build
```

## Documentación

- [Arquitectura y fases](../../docs/panel/arquitectura.md)
- [Fórmulas de métricas y Security Score](../../docs/panel/metricas.md)
- [Seguridad del panel](../../docs/panel/seguridad.md)
- [API](../../docs/panel/api.md)
