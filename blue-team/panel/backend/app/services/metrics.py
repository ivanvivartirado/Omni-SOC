"""Cálculo de porcentajes, MTTD y Security Score. Funciones puras (sin BD) para poder testearlas.

Las fórmulas están documentadas en docs/panel/metricas.md.
"""

import ipaddress
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from app.connectors.base import Agent, Asset, Lease, Pool, ScaResult, Severity, Vulnerability


def pct(part: float, total: float) -> float | None:
    if total <= 0:
        return None
    return round(100 * part / total, 1)


def agents_active(agents: Sequence[Agent]) -> tuple[int, int, float | None]:
    """Agentes activos / total, sin contar el 000 (el propio manager)."""
    real = [a for a in agents if a.id != "000"]
    active = sum(1 for a in real if a.status == "active")
    return active, len(real), pct(active, len(real))


def pool_size(pool: Pool) -> int:
    return int(ipaddress.IPv4Address(pool.end)) - int(ipaddress.IPv4Address(pool.start)) + 1


def lease_in_pool(lease: Lease, pool: Pool) -> bool:
    ip = int(ipaddress.IPv4Address(lease.ip))
    return int(ipaddress.IPv4Address(pool.start)) <= ip <= int(ipaddress.IPv4Address(pool.end))


def active_leases(leases: Iterable[Lease], now: datetime) -> list[Lease]:
    """Lease válido: state 0 (default en Kea) y no caducado."""
    return [lease for lease in leases if lease.state == 0 and lease.expires_at > now]


def pool_usage(pools: Sequence[Pool], leases: Sequence[Lease], now: datetime) -> list[dict[str, object]]:
    valid = active_leases(leases, now)
    out = []
    for pool in pools:
        size = pool_size(pool)
        used = sum(1 for lease in valid if lease.subnet_id == pool.subnet_id and lease_in_pool(lease, pool))
        out.append(
            {"subnet": pool.subnet, "start": pool.start, "end": pool.end, "size": size, "used": used, "pct": pct(used, size)}
        )
    return out


def sca_compliance(results: Sequence[ScaResult]) -> float | None:
    """pass / (pass + fail); los 'not applicable' no cuentan (mismo criterio que Wazuh)."""
    passed = sum(r.passed for r in results)
    failed = sum(r.failed for r in results)
    return pct(passed, passed + failed)


def uptime(ok_checks: int, total_checks: int) -> float | None:
    return pct(ok_checks, total_checks)


def project_progress(done: int, total: int) -> float | None:
    return pct(done, total)


def mttd_seconds(runs: Iterable[tuple[datetime, datetime | None]], now: datetime) -> float | None:
    """Media de (primera alerta que detecta el ataque - inicio del ataque) de las ejecuciones detectadas."""
    deltas = [(d - s).total_seconds() for s, d in runs if d is not None and d <= now]
    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 1)


def agent_coverage(assets: Sequence[Asset], agents: Sequence[Agent]) -> float | None:
    """Activos que deberían tener agente y lo tienen activo / activos que deberían tenerlo."""
    active_ids = {a.id for a in agents if a.status == "active"}
    expected = [a for a in assets if a.agent_expected]
    covered = sum(1 for a in expected if a.agent_id in active_ids)
    return pct(covered, len(expected))


VULN_PENALTY = {"Critical": 15.0, "High": 7.0, "Medium": 2.0, "Low": 0.5}
ALERT_WEIGHT = {Severity.CRITICAL: 10.0, Severity.HIGH: 3.0, Severity.MEDIUM: 0.5}


def vulnerability_score(vulns: Sequence[Vulnerability], n_agents: int) -> float | None:
    if n_agents <= 0:
        return None
    penalty = sum(VULN_PENALTY[v.severity] for v in vulns) / n_agents
    return round(max(0.0, 100 - penalty), 1)


def alert_load(alerts: Iterable[tuple[int, float]]) -> float:
    """Suma de peso(severidad) × (1 - antigüedad_h/24) de las alertas de las últimas 24 h.

    `alerts` son pares (severidad, antigüedad en horas). Una alerta pesa menos a medida que envejece.
    """
    return sum(ALERT_WEIGHT.get(Severity(s), 0.0) * max(0.0, 1 - age / 24) for s, age in alerts)


def alerts_score(load: float) -> float:
    return round(max(0.0, 100 - load), 1)


DEFAULT_WEIGHTS = {"agents": 20.0, "vulnerabilities": 20.0, "hardening": 20.0, "alerts": 20.0, "coverage": 20.0}


def parse_weights(raw: str) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    for part in raw.split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            if k.strip() in weights:
                weights[k.strip()] = float(v)
    return weights


@dataclass
class ScoreResult:
    total: float | None
    breakdown: dict[str, dict[str, float | None]] = field(default_factory=dict)


def security_score(components: dict[str, float | None], weights: dict[str, float] | None = None) -> ScoreResult:
    """Media ponderada de las categorías disponibles (0-100). Si falta un dato, se reparte su peso."""
    weights = weights or DEFAULT_WEIGHTS
    available = {k: v for k, v in components.items() if v is not None and weights.get(k, 0) > 0}
    total_w = sum(weights[k] for k in available)
    total = round(sum(v * weights[k] for k, v in available.items()) / total_w, 1) if total_w else None
    breakdown = {k: {"score": components.get(k), "weight": weights.get(k, 0.0)} for k in weights}
    return ScoreResult(total=total, breakdown=breakdown)
