# Validación de alertas ICMP

## Objetivo
Comprobar el flujo de detección desde Suricata hasta Wazuh en el laboratorio Omni-SOC.

## Procedimiento
1. Identificar la dirección IP del servidor y comprobar la conectividad desde el cliente.
2. Desde el cliente, ejecutar `ping -c 4 <IP_SERVIDOR>` sustituyendo el marcador por la IP del laboratorio.
3. En el servidor, comprobar los eventos con `sudo tail -f /var/log/suricata/eve.json`.
4. Buscar la firma personalizada ICMP (SID 1000001, si sigue configurada).
5. En Wazuh Dashboard, seleccionar el intervalo temporal de la prueba y buscar la firma correspondiente.

## Criterios de aceptación
- Suricata registra una alerta asociada al tráfico generado.
- Wazuh recibe y permite localizar el evento.
- Las IP de origen y destino corresponden a los equipos del laboratorio.

Si no aparece la alerta, revisar la interfaz monitorizada, las reglas cargadas y la lectura de eve.json por Wazuh. Registrar las evidencias y la fecha de ejecución; esta guía no certifica una nueva ejecución de la prueba.
