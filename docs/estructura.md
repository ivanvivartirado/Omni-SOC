# Estructura y arquitectura del laboratorio

## 1. Topología actual

El laboratorio está formado por **tres máquinas**. Wazuh y Suricata están instalados en la misma máquina servidor; no se contempla una cuarta máquina de monitorización.

| Máquina | Función | Responsabilidades |
|---|---|---|
| Servidor Linux | Infraestructura y monitorización | Servicios de red/web, firewall, Suricata y Wazuh |
| Cliente | Equipo de usuario | Acceder a los servicios y generar actividad legítima o de prueba |
| Kali Linux | Equipo de pruebas | Ejecutar escaneos y otros escenarios controlados contra el laboratorio |

Esta tabla describe la topología comunicada para el laboratorio. Las direcciones IP, interfaces, redes y reglas de segmentación se deben mantener en el diagrama y en la documentación de despliegue cuando estén confirmadas.

## 2. Organización de carpetas

### `blue-team/` — configuración defensiva del servidor

- `apache2/`: configuración del servidor web y contenido publicado.
- `bind9/`: configuración DNS y ficheros de zona.
- `kea/`: configuración del servicio DHCP.
- `ufw/`: reglas del firewall local.

### `monitorizacion/` — detección y gestión de eventos

- `suricata/`: configuración del IDS, reglas locales y unidad del servicio.
- `wazuh/`: despliegue de Wazuh mediante Docker Compose y reglas locales.
- `rsyslog/`: configuración relacionada con la recepción y gestión de logs del sistema.

Wazuh y Suricata pertenecen a esta misma máquina servidor. La integración entre ambos debe documentar el origen de los eventos, la ruta de `eve.json`, el mecanismo de lectura por Wazuh y una prueba de extremo a extremo.

**Pendiente de validar:** el Compose de Wazuh referencia ficheros de configuración y certificados bajo `monitorizacion/wazuh/config/`. Antes de considerar el despliegue reproducible, hay que comprobar que esos ficheros se generan o se proporcionan mediante el procedimiento de instalación y que no se versionan claves privadas.

### `red-team/` — pruebas desde Kali

Aquí se documentarán los escenarios de prueba, comandos, objetivos, evidencias y resultados. Cada escenario debe indicar cómo ejecutarlo desde Kali y qué alerta o registro se espera observar en el servidor.

### `infra/` — automatización

Carpeta reservada para la infraestructura como código y los procedimientos de despliegue reproducible. La presencia de esta carpeta no implica que la automatización esté implementada todavía.

### `scripts/` — utilidades

- `auditar.sh`: comprobaciones de auditoría.
- `backup.sh`: copia de seguridad.
- `subir.sh`: sincronización de configuraciones del servidor con el repositorio.

### `docs/` — documentación general

Contiene la propuesta, este documento y los diagramas del laboratorio. Los procedimientos específicos de cada herramienta pueden permanecer junto a su configuración.

## 3. Convenciones de organización

1. **Una responsabilidad por carpeta:** servicios de infraestructura en `blue-team/`, monitorización en `monitorizacion/`, pruebas en `red-team/`.
2. **No duplicar configuraciones:** mantener una única copia versionada de cada configuración y enlazarla desde la documentación.
3. **Separar configuración y evidencias:** no guardar logs voluminosos, capturas con datos sensibles ni resultados temporales en las carpetas de configuración.
4. **Proteger secretos:** no subir ficheros `.env` reales, contraseñas, tokens, claves privadas ni certificados privados. Los ejemplos deben usar valores claramente ficticios.
5. **Documentar las pruebas:** cada detección debe relacionar el escenario ejecutado en Kali, el evento generado por Suricata y la alerta observada en Wazuh.
6. **Validar antes de reorganizar rutas:** los scripts pueden depender de las rutas actuales. Cualquier cambio de nombre o ubicación debe actualizar también sus referencias.

## 4. Tareas de organización pendientes

- [ ] Completar la documentación de las tres máquinas con IP, interfaz, sistema operativo y servicios.
- [ ] Añadir instrucciones de instalación y comprobación de Suricata y Wazuh.
- [ ] Revisar las rutas de configuración y certificados que utiliza el Compose de Wazuh.
- [ ] Documentar y probar la integración Suricata → Wazuh en el servidor.
- [ ] Añadir los escenarios de Kali y sus evidencias en `red-team/`.
- [ ] Incorporar IaC en `infra/` cuando el despliegue esté definido.
