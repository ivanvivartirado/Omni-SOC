# Omni-SOC

Laboratorio académico que reproduce una pequeña infraestructura empresarial para practicar administración de sistemas, monitorización, detección y respuesta ante incidentes.

> **Topología actual:** tres máquinas virtuales: servidor Linux, cliente y Kali Linux. Wazuh y Suricata se ejecutan en el servidor.

## Estado del laboratorio

- **Servidor Linux:** servicios de red y web, firewall y herramientas de monitorización.
- **Cliente:** equipo de usuario para comprobar los servicios y generar actividad.
- **Kali Linux:** máquina de pruebas para ejecutar escenarios controlados.
- **Wazuh + Suricata:** desplegados en el servidor; la integración y las pruebas deben validarse y documentarse.

La arquitectura y el contenido de cada carpeta se explican en [docs/estructura.md](docs/estructura.md). La idea y el alcance inicial del proyecto están en [docs/propuesta.md](docs/propuesta.md).

## Estructura del repositorio

```text
Omni-SOC/
├── blue-team/              # Configuración defensiva del servidor
│   ├── apache2/            # Servidor web
│   ├── bind9/              # DNS
│   ├── kea/                # DHCP
│   └── ufw/                # Firewall
├── monitorizacion/         # Detección y centralización de eventos
│   ├── rsyslog/            # Recepción/configuración de logs del sistema
│   ├── suricata/           # IDS de red, reglas y configuración
│   └── wazuh/              # SIEM, Compose y reglas locales
├── red-team/               # Escenarios y procedimientos desde Kali
├── infra/                  # Automatización e infraestructura como código
├── scripts/                # Utilidades de auditoría, backup y sincronización
└── docs/                   # Propuesta, arquitectura y documentación
    └── img/                # Diagramas e imágenes
```

## Documentación

| Documento | Contenido |
|---|---|
| [Estructura y arquitectura](docs/estructura.md) | Rol de las tres máquinas, carpetas y estado de organización |
| [Propuesta del proyecto](docs/propuesta.md) | Idea, problema, solución y alcance inicial |
| [Diagrama de red](docs/img/diagrama-red.png) | Diagrama disponible del laboratorio |

## Scripts

Los scripts se encuentran en `scripts/`:

- `auditar.sh`: auditoría del servidor.
- `backup.sh`: copia de seguridad.
- `subir.sh`: sincronización de configuraciones del servidor con el repositorio.

Antes de sincronizar cambios, se puede ejecutar `./scripts/subir.sh --ver` para revisar qué copiaría el script. Revisad siempre el resultado antes de hacer commit o push.

## Criterios para mantener el repositorio

1. Guardar aquí configuraciones y documentación, no logs reales, volcados, contraseñas ni claves privadas.
2. Mantener las configuraciones agrupadas por función: servicios del servidor en `blue-team/`, monitorización en `monitorizacion/` y pruebas ofensivas en `red-team/`.
3. Documentar los pasos de instalación y validación junto a la herramienta correspondiente o en `docs/`.
4. No marcar una función como terminada hasta haberla probado en las máquinas del laboratorio.
5. Los cambios de infraestructura deben indicar qué máquina afectan y cómo comprobar que funcionan.

## Tecnologías principales

Linux, Windows (según el alcance del laboratorio), Apache, Bind9, Kea, UFW, Suricata y Wazuh. La automatización con IaC y los escenarios de pruebas se irán incorporando conforme se implementen y validen.
