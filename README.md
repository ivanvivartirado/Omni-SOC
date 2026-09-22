# Omni SOC

Infraestructura de red que simula el entorno de una pequeña o mediana empresa, sobre la que se despliegan capacidades de monitorización, detección y respuesta ante incidentes de seguridad. El objetivo es crear un entorno práctico de laboratorio donde se pueda aprender a operar un pequeño SOC, integrando administración de sistemas, redes y ciberseguridad defensiva/ofensiva.

Proyecto de ciclo formativo (ASIR/ASIX), pensado como práctica integral de administración de sistemas en red combinada con ciberseguridad ofensiva y defensiva (red team / blue team).

## 1. Idea del proyecto

### Título
Omni SOC

### Descripción
El proyecto consiste en el diseño, despliegue y mantenimiento de una infraestructura de red completa que simula el entorno de una pequeña o mediana empresa, sobre la que se implementan servicios básicos, segmentación de red y mecanismos de monitorización y detección de incidentes. El resultado es un entorno de laboratorio que se comporta como una organización real desde el punto de vista tecnológico y de seguridad.

La idea principal es crear un pequeño “SOC” funcional en el que se pueda observar el tráfico, centralizar logs, detectar anomalías y reaccionar ante posibles amenazas. Todo ello se despliega de forma automatizada para que el entorno pueda reproducirse en otra máquina o laboratorio sin necesidad de volver a configurarlo desde cero.

## 2. Problema y usuario

Muchas pequeñas y medianas empresas no disponen de personal ni presupuesto para contar con un departamento de ciberseguridad propio. Esto hace que sus redes queden expuestas: no se monitoriza el tráfico, no se detectan intentos de intrusión a tiempo y, cuando ocurre un incidente, muchas veces se descubre tarde o nunca.

El problema que aborda el proyecto es la falta de visibilidad y capacidad de respuesta ante incidentes de seguridad en infraestructuras de tamaño reducido. En muchos casos, estas organizaciones tienen servicios esenciales, equipos conectados a internet y varios usuarios trabajando en red, pero no cuentan con herramientas ni procedimientos adecuados para detectar amenazas o reaccionar ante ellas.

### Perfil objetivo
- Pequeñas y medianas empresas sin SOC propio.
- Administradores de sistemas o técnicos de red que necesitan monitorizar y proteger su infraestructura.
- Estudiantes o profesionales en formación que quieran aprender a montar y operar un entorno de seguridad básico.
- Entorno académico para practicar conceptos de redes, sistemas y ciberseguridad.

## 3. Solución propuesta

La solución consiste en simular una red empresarial y vigilarla como lo haría un equipo de seguridad real. El sistema permitirá:

- Red simulada de empresa: varios equipos y servidores conectados entre sí, reproduciendo la estructura de una pyme real.
- Monitorización continua: vigilancia del tráfico y de la actividad de la red para conocer en todo momento qué está ocurriendo.
- Detección de incidentes: identificación de comportamientos sospechosos o ataques, como accesos no autorizados, movimientos extraños o malware.
- Alertas: notificación al responsable cuando se detecta algo anómalo para poder actuar rápidamente.
- Respuesta ante incidentes: procedimientos y acciones para contener y mitigar una amenaza una vez detectada.
- Simulación de ataques: realización de pruebas controladas para verificar que el sistema de detección funciona correctamente.
- Infraestructura reproducible: despliegue automatizado del entorno para poder recrearlo en otra máquina o laboratorio sin reconstruir todo manualmente.

En definitiva, el proyecto permitirá aprender a montar una infraestructura realista, monitorizarla y responder ante amenazas de forma ordenada y documentada.

## 4. Alcance del proyecto

1. Desplegar una infraestructura de red virtualizada que simule una pyme con diferentes segmentos y servicios.
2. Configurar un entorno con firewall, segmentación por VLANs y servicios básicos de red.
3. Implementar un SIEM (por ejemplo, Wazuh) y un IDS/IPS de red (por ejemplo, Suricata) para centralizar logs y detectar tráfico sospechoso.
4. Generar alertas para escenarios comunes como fuerza bruta, escaneo de red, accesos anómalos y comportamiento sospechoso.
5. Simular ataques controlados para validar la detección y la respuesta del entorno.
6. Documentar los procedimientos de respuesta ante incidentes y automatizar el despliegue del entorno.

## 5. Arquitectura (borrador)

Se pretende diseñar una infraestructura compuesta por varias capas:

- Segmentación de red mediante VLANs para diferenciar áreas funcionales.
- Firewall o encaminador de seguridad para controlar el tráfico entre segmentos.
- Servidor Windows con Active Directory, servicio de usuarios y políticas de seguridad.
- Servidor Linux con servicios básicos de infraestructura (DNS, DHCP, web, gestión, etc.).
- Equipos cliente para representar estaciones de trabajo de usuarios.
- Servidor de monitorización y análisis, donde se centralicen logs y alertas.
- Entorno atacante o laboratorio de pruebas para simular amenazas controladas.

> Pendiente: diagrama detallado de red, topología final, servicios a desplegar, máquinas implicadas y roles de cada nodo.

## 6. Tecnologías

Se trabajará con herramientas y tecnologías orientadas a la virtualización, la automatización y la seguridad:

- Infraestructura como Código (IaC) para desplegar el entorno de forma reproducible y portátil.
- Virtualización con soluciones como Proxmox, VMware o VirtualBox.
- Sistemas operativos Windows y Linux para simular entornos empresariales reales.
- Herramientas de monitorización y detección, como Wazuh, Suricata o soluciones equivalentes.
- Administración y segmentación de red: VLANs, firewall, DNS, DHCP y servicios básicos.
- Automatización de despliegue mediante scripts y configuraciones versionadas.

> Pendiente: definir con detalle qué herramientas concretas se usarán en la implementación final y qué escenarios de seguridad se probarán.

## 7. Instalación / despliegue

El proyecto está pensado para poder desplegarse de forma automatizada y repetible en otra máquina o laboratorio.

Se contempla:

- Requisitos mínimos del sistema para levantar la infraestructura.
- Despliegue de máquinas virtuales y servicios bajo configuración automatizada.
- Configuración inicial de red, usuarios y políticas.
- Inicio de herramientas de monitorización y detección.
- Validación del funcionamiento del entorno.

> Pendiente: definir los comandos, scripts y procedimientos concretos de despliegue final.

## 8. Relación con el ciclo formativo

Los módulos del ciclo que se ponen en práctica en este proyecto son principalmente:

### Servicios de red e internet
Configuración de servicios de red como DNS, DHCP, firewall, segmentación, encaminamiento y servicios básicos para que la infraestructura funcione de forma realista.

### Seguridad y alta disponibilidad
Aplicación de medidas de seguridad, control de accesos, hardening de sistemas, detección y respuesta ante incidencias, así como conceptos fundamentales de ciberseguridad ofensiva y defensiva.

### Administración de sistemas operativos
Instalación, configuración y mantenimiento de servidores y clientes, tanto Windows como Linux, junto con la gestión de servicios y usuarios.

### Red team / blue team
El proyecto combina la parte de ataque controlado (detección y prueba de vulnerabilidades o comportamientos maliciosos) con la parte defensiva (monitorización, análisis, alertas y mitigación).

## 9. Valor del proyecto

Este proyecto tiene un valor muy importante desde el punto de vista formativo y profesional. Para nosotras/os, es una oportunidad para adquirir experiencia práctica en un ámbito muy demandado dentro de la informática y la ciberseguridad: la monitorización, detección y respuesta ante incidentes.

Además, nos permite desarrollar habilidades en varios campos a la vez:

- Administración de redes y servicios.
- Configuración de sistemas operativos y seguridad.
- Monitorización de entornos reales.
- Detección de amenazas y análisis de eventos.
- Trabajo en equipo, documentación y automatización.

Lo que hace especialmente útil este proyecto es que nos sirve como base para aprender a defender infraestructuras reales, entender cómo se comportan los ataques y cómo se responde ante ellos. Es un proyecto práctico, motivador y muy cercano a los escenarios profesionales del mundo de la ciberseguridad.

## 10. Equipo

Proyecto desarrollado por dos alumnos del ciclo con interés especial en la ciberseguridad ofensiva y defensiva, así como en la administración de sistemas y redes.

## 11. Objetivos

- Desplegar una infraestructura de red completa que simule un entorno empresarial real.
- Implementar monitorización, detección y respuesta ante incidentes de seguridad.
- Practicar de forma integrada contenidos de administración de sistemas en red del ciclo.
- Incorporar competencias de ciberseguridad ofensiva y defensiva.
- Documentar la infraestructura como código para que sea reproducible y portable.

## 12. Conclusión

Omni SOC es un proyecto de tipo académico y práctico pensado para aprender a montar, proteger y mantener una infraestructura de red realista en un entorno de laboratorio. Su enfoque combina redes, sistemas, automatización y seguridad, ofreciendo una visión completa del funcionamiento de un pequeño SOC y de la gestión de incidentes en un entorno empresarial.

Este proyecto no solo permite practicar conceptos del ciclo formativo, sino que además sienta las bases para desarrollar habilidades reales en el ámbito de la ciberseguridad, tanto a nivel técnico como analítico.

---

Proyecto desarrollado para aprender, experimentar y mejorar competencias en administración de sistemas, redes y seguridad informática.
