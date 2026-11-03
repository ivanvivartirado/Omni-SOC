# Métricas y Security Score

Todos los porcentajes se calculan a partir de datos reales (o demo) en `backend/app/services/metrics.py`, con tests en `backend/tests/test_metrics.py`. Si un dato no está disponible se muestra `—` en lugar de inventar un valor.

## Porcentajes

| Métrica | Fórmula |
|---|---|
| Agentes activos | agentes `active` / agentes totales, sin contar el `000` (el propio manager) |
| Uso del pool DHCP | leases válidos dentro del rango del pool / tamaño del pool. Válido = `state 0` y no caducado. Pool actual: `192.168.15.200-230` = 31 IPs |
| Cumplimiento SCA | `pass / (pass + fail)` sumando todos los agentes; los *not applicable* no cuentan (igual que Wazuh) |
| Uptime de servicio | comprobaciones correctas / comprobaciones totales (24 h) |
| Cobertura de agentes | activos que deberían tener agente y lo tienen activo / activos que deberían tenerlo (Kali y la impresora no cuentan) |
| Tasa de detección | ataques simulados detectados / ataques simulados (7 d) |

## MTTD

Media de `primera alerta que detecta el ataque − inicio del ataque` de las simulaciones detectadas en los últimos 7 días. Objetivo: **< 60 s**. Las no detectadas no entran en la media, pero bajan la tasa de detección.

## Hosts comprometidos / en riesgo

- **Comprometido**: al menos una alerta crítica (nivel Wazuh ≥ 12) asociada al agente en las últimas 24 h.
- **En riesgo**: al menos una alerta alta (nivel Wazuh 10-11) y ninguna crítica.

## Severidad

| Severidad | Wazuh (nivel) | Suricata |
|---|---|---|
| crítica | ≥ 12 | — |
| alta | 10-11 | 1 |
| media | 7-9 | 2 |
| baja | 3-6 | 3 |
| info | 0-2 | 4 |

Los umbrales de Wazuh son configurables con `SEVERITY_THRESHOLDS`.

## Security Score (0-100)

Media ponderada de 5 categorías (pesos por defecto 20 % cada una, configurables con `SCORE_WEIGHTS`):

| Categoría | Cálculo (0-100) |
|---|---|
| Agentes | % de agentes activos |
| Vulnerabilidades | `100 − Σ penalización / nº agentes`, con penalización Critical 15, High 7, Medium 2, Low 0,5 |
| Hardening | % de cumplimiento SCA |
| Alertas | `100 − carga`, donde carga = Σ peso(severidad) × (1 − antigüedad_h / 24) de las alertas de las últimas 24 h; peso crítica 10, alta 3, media 0,5 |
| Cobertura | % de cobertura de agentes |

Si una categoría no tiene datos (por ejemplo, el conector no está configurado) su peso se reparte entre las demás, y el desglose la muestra como `s/d`. Así una alerta crítica reciente resta 10 puntos a la categoría de alertas y su efecto desaparece de forma gradual en 24 h.
