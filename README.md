# Omni-SOC

Laboratorio académico que reproduce una pequeña infraestructura empresarial para practicar administración de sistemas, monitorización, detección y respuesta ante incidentes.

> **Topología:** tres máquinas virtuales: servidor Linux, cliente y Kali Linux. Wazuh y Suricata se ejecutan en el servidor.

## Estado del laboratorio

- **Servidor Linux (`omnisoc-server`):** servicios de red y web, firewall, recepción de logs y plataforma de monitorización.
- **Cliente:** equipo de usuario para comprobar servicios y generar actividad legítima o de prueba.
- **Kali Linux:** máquina de pruebas para ejecutar escenarios controlados.
- **Wazuh + Suricata:** desplegados en el servidor; la integración y las detecciones deben validarse mediante pruebas de extremo a extremo.

La arquitectura y el contenido de cada carpeta se explican en [docs/estructura.md](docs/estructura.md). La idea y el alcance inicial están en [docs/propuesta.md](docs/propuesta.md).

## Seguridad y hardening

Se han aplicado y comprobado las siguientes medidas en el servidor:

| Área | Medida | Estado |
|---|---|---|
| UFW | SSH y servicios administrativos limitados a la LAN `192.168.15.0/24`; eliminación de reglas globales innecesarias | Aplicado |
| Wazuh Docker | API `55000/tcp` e indexer `9200/tcp` publicados solo en `127.0.0.1` | Aplicado mediante override |
| Wazuh Docker | Publicación de `514/udp` retirada del contenedor manager | Aplicado |
| SSH | Autenticación Ed25519 probada desde el equipo administrativo | Verificado |
| SSH | `MaxAuthTries 3`, claves públicas habilitadas y acceso root por contraseña prohibido | Verificado |
| Fail2ban | Jail `sshd`, 5 intentos, ventana de 10 minutos y bloqueo de 1 hora | Activo y verificado |

**Pendiente / decisión operativa:** SSH mantiene `PasswordAuthentication yes` deliberadamente. No se ha probado un bloqueo real de Fail2ban. No se debe considerar desactivada la autenticación por contraseña ni completada una prueba de bloqueo.

Documentación:
- [Resumen de hardening](docs/security/overview.md)
- [Hardening SSH y Fail2ban](docs/security/hardening-ssh-fail2ban.md)
- [Override de puertos Docker para Wazuh](infra/wazuh/compose.hardening.yml)

### Aplicar el override de Docker Compose de Wazuh

El override se combina con el Compose original de Wazuh; no lo sustituye. Desde `docker-compose/wazuh-docker/single-node`:

```bash
docker compose \
  -f docker-compose.yml \
  -f ../../../infra/wazuh/compose.hardening.yml \
  config --quiet
```

Si la validación es correcta, para aplicar el despliegue:

```bash
docker compose \
  -f docker-compose.yml \
  -f ../../../infra/wazuh/compose.hardening.yml \
  up -d
```

El archivo base debe estar disponible en esa ruta y sus secretos/certificados deben estar preparados localmente. El override limita la API y el indexer a localhost, elimina la publicación UDP 514 del manager y conserva los puertos de agentes 1514/1515 y el Dashboard HTTPS 443 según el Compose base. La recepción de syslog TCP/514 del host se gestiona por separado mediante rsyslog.

## Estructura del repositorio

```text
Omni-SOC/
├── blue-team/              # Configuración defensiva del servidor
│   ├── apache2/            # Servidor web
│   ├── bind9/              # DNS
│   ├── kea/                # DHCP
│   └── ufw/                # Firewall
├── monitorizacion/         # Detección y centralización de eventos
│   ├── rsyslog/            # Recepción/gestión de logs
│   ├── suricata/           # IDS de red, reglas y configuración
│   └── wazuh/              # SIEM, despliegue y reglas locales
├── red-team/               # Escenarios y procedimientos desde Kali
├── infra/
│   └── wazuh/              # Overrides de despliegue y hardening
├── scripts/                # Auditoría, backup y sincronización
└── docs/
    ├── security/           # Hardening y controles de seguridad
    └── img/                # Diagramas e imágenes
```

## Documentación

| Documento | Contenido |
|---|---|
| [Estructura y arquitectura](docs/estructura.md) | Topología de las tres máquinas, carpetas y tareas pendientes |
| [Propuesta del proyecto](docs/propuesta.md) | Idea, problema, solución y alcance inicial |
| [Resumen de hardening](docs/security/overview.md) | Estado de UFW, Docker, SSH y Fail2ban |
| [Hardening SSH y Fail2ban](docs/security/hardening-ssh-fail2ban.md) | Configuración efectiva y comprobaciones de SSH/Fail2ban |
| [Override Docker Wazuh](infra/wazuh/compose.hardening.yml) | Restricciones de publicación de puertos |
| [Diagrama de red](docs/img/diagrama-red.png) | Diagrama disponible del laboratorio |

## Scripts

Los scripts se encuentran en `scripts/`:

- `auditar.sh`: auditoría del servidor.
- `backup.sh`: copia de seguridad.
- `subir.sh`: sincronización de configuraciones del servidor con el repositorio.

Antes de sincronizar cambios, se puede ejecutar `./scripts/subir.sh --ver` para revisar qué copiaría el script. Revisad siempre el resultado antes de hacer commit o push.

## Criterios para mantener el repositorio

1. Guardar configuraciones y documentación, no logs reales, volcados, contraseñas ni claves privadas.
2. Mantener las configuraciones agrupadas por función: servicios del servidor en `blue-team/`, monitorización en `monitorizacion/` y pruebas ofensivas en `red-team/`.
3. Documentar los pasos de instalación y validación junto a la herramienta correspondiente o en `docs/`.
4. No marcar una función como terminada hasta haberla probado en las máquinas del laboratorio.
5. Los cambios de infraestructura deben indicar qué máquina afectan y cómo comprobar que funcionan.
6. No versionar archivos `.env` reales, claves privadas, certificados privados ni copias de seguridad con secretos.

## Tecnologías principales

Linux, Docker Compose, Wazuh, Suricata, rsyslog, UFW, Fail2ban, Apache, Bind9 y Kea. La automatización con IaC y los escenarios de pruebas se irán incorporando conforme se implementen y validen.
