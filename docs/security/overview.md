# Estado de seguridad y hardening – Omni-SOC

Este documento resume los controles de seguridad aplicados al servidor del laboratorio y separa las medidas verificadas de las tareas pendientes. Fecha de actualización: 2026-11-19.

## Resumen

| Área | Estado | Evidencia / observación |
|---|---|---|
| UFW | Aplicado | Reglas comprobadas con `ufw status numbered`; cambios de reglas versionados |
| Docker Compose de Wazuh | Aplicado | Override validado y desplegado; puertos API e indexer ligados a localhost |
| SSH con clave pública | Verificado | Conexión desde `snowden-105` a `ivan@omnisoc-server` con Ed25519 |
| Parámetros SSH | Verificado | `MaxAuthTries 3`, `PubkeyAuthentication yes`, `PermitRootLogin prohibit-password` |
| Fail2ban | Activo | Servicio habilitado y jail `sshd` activo |
| Prueba de bloqueo Fail2ban | Pendiente | No se ha generado un bloqueo de prueba |
| Desactivar contraseña SSH | Pendiente / no aplicado | `PasswordAuthentication yes` se mantiene deliberadamente |
| Actualizaciones Ubuntu | Pendiente | Se observaron 84 paquetes actualizables, incluidas 45 actualizaciones de seguridad estándar |

## 1. Firewall UFW

Las reglas locales fueron revisadas y se eliminaron reglas globales redundantes o innecesarias de SSH y del puerto 5636. La administración SSH y los servicios internos deben mantenerse limitados a la red autorizada.

Comprobaciones útiles en el servidor:

```bash
sudo ufw status numbered
sudo ufw status verbose
```

Los archivos de reglas versionados son una referencia de configuración; el estado efectivo debe comprobarse en el propio host después de cada cambio.

## 2. Docker Compose de Wazuh

El override versionado está en [infra/wazuh/compose.hardening.yml](../../infra/wazuh/compose.hardening.yml).

Publicaciones configuradas por el override:

- Manager: TCP/1514 y TCP/1515 para agentes; API TCP/55000 ligada a `127.0.0.1`.
- Indexer: TCP/9200 ligado a `127.0.0.1`.
- Dashboard: HTTPS publicado en el puerto 443 según el Compose base.
- Se elimina la publicación UDP/514 del manager. La recepción de syslog TCP/514 del host se gestiona mediante rsyslog por separado.

Validación de configuración (desde `docker-compose/wazuh-docker/single-node`, dentro del repositorio):

```bash
docker compose \
  -f docker-compose.yml \
  -f ../../../infra/wazuh/compose.hardening.yml \
  config --quiet
```

La ruta relativa presupone que el repositorio mantiene la estructura indicada. Para aplicar el override al despliegue, usar los mismos dos archivos con `up -d`, después de validar la configuración y comprobar que los secretos y certificados locales están disponibles.

Comprobación de publicaciones activas:

```bash
docker ps --format "table {{.Names}}\\t{{.Ports}}"
```

## 3. SSH

Archivo operativo: `/etc/ssh/sshd_config.d/00-omnisoc-hardening.conf`.

Configuración:

```text
MaxAuthTries 3
PubkeyAuthentication yes
PermitRootLogin prohibit-password
```

La configuración efectiva se verificó con:

```bash
sudo sshd -t
sudo sshd -T | grep -Ei '^(maxauthtries|passwordauthentication|permitrootlogin|pubkeyauthentication) '
```

Valores efectivos comprobados:

- `maxauthtries 3`
- `permitrootlogin prohibit-password`
- `pubkeyauthentication yes`
- `passwordauthentication yes`

Se probó una conexión por clave Ed25519 desde `snowden-105` (192.168.15.105) al usuario `ivan` en `omnisoc-server` (192.168.15.122).

**No se ha desactivado la autenticación por contraseña.** Antes de cambiarla, hay que inventariar todos los accesos administrativos y probar las claves desde cada equipo necesario. Mantener una sesión administrativa abierta durante cualquier cambio de SSH.

## 4. Fail2ban

Archivo operativo: `/etc/fail2ban/jail.d/omnisoc-sshd.local`.

Parámetros efectivos comprobados:

- Jail: `sshd`
- Backend: `systemd`
- Puerto: `22`
- `maxretry = 5`
- `findtime = 600` segundos
- `bantime = 3600` segundos
- IP administrativa excluida: `192.168.15.105`

Comprobaciones realizadas:

```bash
sudo fail2ban-client -t
sudo systemctl is-enabled fail2ban
sudo systemctl is-active fail2ban
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo fail2ban-client get sshd maxretry
sudo fail2ban-client get sshd findtime
sudo fail2ban-client get sshd bantime
sudo fail2ban-client get sshd ignoreip
```

El servicio quedó habilitado y activo, con el jail `sshd` cargado. En la última consulta había cero intentos fallidos y cero IP bloqueadas. Esto confirma el estado del jail, pero no demuestra un bloqueo real; esa prueba queda pendiente y debe realizarse desde una IP de prueba que no sea la administrativa.

## 5. Pendientes y mantenimiento

- [ ] Diseñar y ejecutar una prueba controlada de bloqueo Fail2ban desde un host/IP de prueba no excluido.
- [ ] Decidir si se desactiva `PasswordAuthentication` después de comprobar todas las vías de acceso y recuperación.
- [ ] Revisar las actualizaciones pendientes de Ubuntu y planificar una ventana de mantenimiento con copia de seguridad y comprobaciones de Wazuh, Docker, SSH y red.
- [ ] Revisar periódicamente las reglas UFW efectivas y los puertos publicados por Docker.
- [ ] Mantener sincronizada esta documentación con la configuración real del servidor.

## 6. Protección de secretos

No guardar en el repositorio contraseñas reales, claves privadas, tokens, certificados privados ni archivos `.env` de producción. Los archivos de configuración operativos bajo `/etc` se documentan aquí, pero no se copian al repositorio cuando contienen datos específicos del host o información sensible.
