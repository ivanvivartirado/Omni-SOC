# Seguridad del panel

| Control | Implementación |
|---|---|
| Contraseñas | Argon2id (`argon2-cffi`). Mínimo 12 caracteres con 3 tipos distintos |
| Sesión | JWT de acceso (15 min) y de refresco (8 h) en cookies `HttpOnly`, `Secure`, `SameSite=Strict`. El refresco solo se envía a `/api/auth` |
| Revocación | cada usuario tiene `token_version`; cerrar sesión, cambiar la contraseña o desactivar el usuario invalida todos sus tokens |
| CSRF | cookie `csrf_token` + cabecera `X-CSRF-Token` obligatoria en POST/PATCH/PUT/DELETE |
| Fuerza bruta | bloqueo progresivo por usuario (5 fallos → 1, 2, 4… min, máx. 60) y por IP (20 fallos / 15 min), más `limit_req` de Nginx en `/api/auth/login`. No revela si el usuario existe (verificación con hash ficticio) |
| Roles | `viewer` (lectura), `analyst` (+ simulaciones y, en fase 4, incidentes), `admin` (+ usuarios, auditoría y configuración) |
| Auditoría | tabla `audit_log`: logins, fallos, bloqueos, cambios de usuarios y contraseñas, simulaciones |
| WebSocket | requiere cookie de sesión válida y `Origin` incluido en `ALLOWED_ORIGINS` |
| Transporte | TLS 1.2/1.3 en Nginx (8443), HSTS. Certificado autofirmado si no se monta uno |
| Cabeceras | CSP estricta sin recursos externos, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer` |
| Contenedores | API sin root, sistema de ficheros de solo lectura, `cap_drop: ALL`, `no-new-privileges`, límites de memoria. La API no publica puertos: solo se accede a través de Nginx |
| Secretos | solo en `.env` (ignorado por git). `SECRET_KEY` autogenerada y guardada en el volumen de datos si no se define |

## Aviso sobre el repositorio

`blue-team/bind9/named.conf.local` contiene en claro el secreto TSIG `kea-bind-key` y está en el historial público. Hay que **rotarlo** en el servidor (`tsig-keygen kea-bind-key`) y sustituirlo en el repo por un marcador, porque `scripts/subir.sh` no lo oculta.
