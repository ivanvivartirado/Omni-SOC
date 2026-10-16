# Propuesta de proyecto de desarrollo

## 1. Idea del proyecto

**Título:** Omni SOC

**Descripción:** El proyecto consiste en el diseño, despliegue y mantenimiento de una infraestructura de red completa que simula el entorno de una pequeña/mediana empresa, sobre la cual se implementan capacidades de monitorización, detección y respuesta ante incidentes de seguridad (un pequeño "SOC").

## 2. Problema y usuario

Muchas pequeñas y medianas empresas no disponen de personal ni presupuesto para tener un departamento de ciberseguridad propio. Esto hace que sus redes queden expuestas: no hay quien monitorice el tráfico, no se detectan intentos de intrusión a tiempo, y cuando ocurre un incidente se detecta tarde o no se detecta nunca.

El problema que aborda el proyecto es la falta de visibilidad y capacidad de respuesta ante incidentes de seguridad en infraestructuras de tamaño reducido.

El perfil objetivo son pequeñas y medianas empresas (pymes) que no cuentan con un SOC propio, así como el administrador de sistemas o técnico de red de esa empresa, que sería quien usaría las herramientas de monitorización y respuesta implementadas en el proyecto. También puede plantearse como un entorno de prácticas/formación para técnicos que quieran aprender a montar y operar un SOC básico.

## 3. Solución propuesta

El sistema permitirá simular la red de una empresa pequeña/mediana y vigilar como lo haría un equipo de seguridad real: detectar cuándo algo raro está pasando en la red, avisar de ello y poder reaccionar antes de que el problema vaya a más. Además, al estar todo desplegado de forma automatizada, permitirá volver a montar esa misma infraestructura en otro equipo sin tener que rehacerlo todo a mano.

- **Red simulada de empresa:** varios equipos y servidores conectados entre sí, imitando cómo se organiza la red de una pyme real.
- **Monitorización continua:** vigilancia del tráfico y la actividad de la red para saber en todo momento qué está pasando.
- **Detección de incidentes:** capacidad de identificar comportamientos sospechosos o ataques (intentos de acceso no autorizados, malware, movimientos extraños en la red).
- **Alertas:** aviso al responsable de la red cuando se detecta algo anómalo, para que pueda actuar rápido.
- **Respuesta ante incidentes:** procedimientos o acciones para contener y solucionar un problema una vez detectado.
- **Simulación de ataques:** posibilidad de provocar incidentes de forma controlada para comprobar que el sistema de detección funciona correctamente.
- **Infraestructura reproducible:** todo el entorno se puede volver a desplegar de forma automática en otra máquina, sin configurarlo manualmente desde cero.

## 4. Alcance del proyecto

1. Desplegar una infraestructura de red virtualizada que simula una pyme: servidor Windows con Active Directory, servidor Linux, equipos cliente y firewall con segmentación en VLANs.
2. Implementar un SIEM (ej. Wazuh) y un IDS de red (ej. Suricata) que centralizan logs y detectan actividad sospechosa, con alertas configuradas para los escenarios más comunes.
3. Simular ataques controlados (fuerza bruta, malware de prueba, escaneo de red) para comprobar que el sistema de detección funciona.
4. Documentar procedimientos de respuesta ante incidentes y automatizar el despliegue del entorno para que sea reproducible.

## 5. Relación con el ciclo formativo

Los módulos que trataremos en nuestro proyecto serán los siguientes:

- **Servicios de red e internet:** configuración de los servicios de red (DNS, DHCP, servidor web, etc.), todo lo necesario para que la estructura simulada funcione como la de una empresa real.
- **Seguridad y alta disponibilidad:** aplicación de medidas de seguridad en las máquinas (firewall, hardening, control de accesos). Conceptos de detección y respuesta ante incidencias que son parte del proyecto.
- **Administración de sistemas operativos:** instalación, configuración y mantenimiento de los sistemas operativos (servidores y clientes).

## 6. Valor del proyecto

Lo que hace útil este proyecto es que nos va a servir a nivel personal: somos dos estudiantes de ASIX a los que nos interesa trabajar en un futuro en el ámbito de la ciberseguridad. Por esta razón nos hemos planteado hacer este modelo de proyecto para mejorar y ampliar nuestros conocimientos. Será interesante y nos motivará saber defender y atacar sistemas y comprender los fundamentos técnicos de cómo y por qué se hace.
