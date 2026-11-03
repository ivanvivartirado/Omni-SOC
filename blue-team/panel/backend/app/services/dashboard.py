"""Agregados para la Home (KPIs, Security Score y gráficas)."""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import Severity
from app.core.config import Settings
from app.core.db import dialect
from app.models import OPEN_INCIDENT_STATUSES, AttackRun, Event, Incident, ServiceCheck
from app.services import metrics
from app.services.manager import ConnectorManager
from app.services.serializers import as_utc, iso

Range = Literal["24h", "7d"]
RANGES: dict[str, timedelta] = {"24h": timedelta(hours=24), "7d": timedelta(days=7)}
MTTD_TARGET_SECONDS = 60


def _bucket(col: Any, unit: Literal["hour", "day"]) -> Any:
    if dialect() == "sqlite":
        return func.strftime("%Y-%m-%dT%H:00:00Z" if unit == "hour" else "%Y-%m-%dT00:00:00Z", col)
    return func.to_char(func.date_trunc(unit, col), 'YYYY-MM-DD"T"HH24:00:00"Z"')


async def severity_counts(s: AsyncSession, since: datetime) -> dict[int, int]:
    rows = await s.execute(select(Event.severity, func.count()).where(Event.ts >= since).group_by(Event.severity))
    counts = {int(sev): 0 for sev in Severity}
    counts.update({int(sev): n for sev, n in rows.all()})
    return counts


async def timeline(s: AsyncSession, since: datetime, unit: Literal["hour", "day"]) -> list[dict[str, Any]]:
    b = _bucket(Event.ts, unit)
    rows = (
        await s.execute(select(b, Event.severity, func.count()).where(Event.ts >= since).group_by(b, Event.severity).order_by(b))
    ).all()
    buckets: dict[str, dict[str, Any]] = {}
    for bucket, sev, n in rows:
        buckets.setdefault(bucket, {"bucket": bucket, **{f"s{i}": 0 for i in range(5)}})[f"s{sev}"] = n
    return list(buckets.values())


async def top_rules(s: AsyncSession, since: datetime, limit: int = 10) -> list[dict[str, Any]]:
    rows = await s.execute(
        select(Event.source, Event.rule_id, Event.title, func.max(Event.severity), func.count().label("n"))
        .where(Event.ts >= since)
        .group_by(Event.source, Event.rule_id, Event.title)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [{"source": src, "rule_id": rid, "title": t, "severity": sev, "count": n} for src, rid, t, sev, n in rows]


async def top_src_ips(s: AsyncSession, since: datetime, limit: int = 10) -> list[dict[str, Any]]:
    rows = await s.execute(
        select(Event.src_ip, func.count(), func.max(Event.severity))
        .where(Event.ts >= since, Event.src_ip.is_not(None), Event.severity >= Severity.LOW)
        .group_by(Event.src_ip)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [{"ip": ip, "count": n, "max_severity": sev} for ip, n, sev in rows]


async def heatmap(s: AsyncSession, since: datetime) -> dict[str, Any]:
    b = _bucket(Event.ts, "hour")
    rows = (
        await s.execute(
            select(Event.agent_name, b, func.count())
            .where(Event.ts >= since, Event.agent_name.is_not(None), Event.severity >= Severity.MEDIUM)
            .group_by(Event.agent_name, b)
        )
    ).all()
    hosts = sorted({r[0] for r in rows})
    start = since.replace(minute=0, second=0, microsecond=0)
    hours = [(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00:00Z") for i in range(25)]
    idx = {h: i for i, h in enumerate(hours)}
    cells = [[idx[bucket], hosts.index(host), n] for host, bucket, n in rows if bucket in idx]
    return {"hosts": hosts, "hours": hours, "cells": cells}


async def host_risk(s: AsyncSession, since: datetime) -> tuple[list[str], list[str]]:
    """Comprometido = ≥1 alerta crítica en 24 h; en riesgo = ≥1 alerta alta (y ninguna crítica)."""
    rows = (
        await s.execute(
            select(Event.agent_name, func.max(Event.severity))
            .where(Event.ts >= since, Event.agent_name.is_not(None), Event.severity >= Severity.HIGH)
            .group_by(Event.agent_name)
        )
    ).all()
    compromised = sorted(h for h, sev in rows if sev >= Severity.CRITICAL)
    at_risk = sorted(h for h, sev in rows if sev == Severity.HIGH)
    return compromised, at_risk


async def alert_load(s: AsyncSession, now: datetime) -> float:
    since = now - timedelta(hours=24)
    b = _bucket(Event.ts, "hour")
    rows = (
        await s.execute(
            select(b, Event.severity, func.count())
            .where(Event.ts >= since, Event.severity >= Severity.MEDIUM)
            .group_by(b, Event.severity)
        )
    ).all()
    pairs: list[tuple[int, float]] = []
    for bucket, sev, n in rows:
        age = (now - datetime.fromisoformat(bucket.replace("Z", "+00:00"))).total_seconds() / 3600
        pairs += [(sev, max(0.0, age - 0.5))] * n
    return metrics.alert_load(pairs)


async def mttd(s: AsyncSession, now: datetime, since: datetime) -> dict[str, Any]:
    runs = (await s.execute(select(AttackRun.started_at, AttackRun.detected_at).where(AttackRun.started_at >= since))).all()
    pairs = [(as_utc(a), as_utc(b)) for a, b in runs]
    value = metrics.mttd_seconds(pairs, now)  # type: ignore[arg-type]
    detected = sum(1 for _, d in pairs if d is not None and d <= now)
    return {
        "seconds": value,
        "target_seconds": MTTD_TARGET_SECONDS,
        "runs": len(pairs),
        "detected": detected,
        "detection_rate": metrics.pct(detected, len(pairs)),
    }


async def incidents(s: AsyncSession) -> dict[str, int]:
    open_n, closed_n = (
        await s.execute(
            select(
                func.coalesce(func.sum(case((Incident.status.in_(OPEN_INCIDENT_STATUSES), 1), else_=0)), 0),
                func.coalesce(func.sum(case((Incident.status.not_in(OPEN_INCIDENT_STATUSES), 1), else_=0)), 0),
            )
        )
    ).one()
    return {"open": int(open_n), "closed": int(closed_n)}


async def services_uptime(s: AsyncSession, since: datetime) -> list[dict[str, Any]]:
    rows = await s.execute(
        select(
            ServiceCheck.service, func.count(), func.sum(case((ServiceCheck.ok, 1), else_=0)), func.avg(ServiceCheck.latency_ms)
        )
        .where(ServiceCheck.ts >= since)
        .group_by(ServiceCheck.service)
        .order_by(ServiceCheck.service)
    )
    return [
        {
            "service": name,
            "checks": total,
            "uptime_pct": metrics.uptime(int(ok or 0), total),
            "avg_latency_ms": round(lat, 1) if lat is not None else None,
        }
        for name, total, ok, lat in rows
    ]


async def summary(s: AsyncSession, manager: ConnectorManager, settings: Settings, rng: Range) -> dict[str, Any]:
    now = datetime.now(UTC)
    since = now - RANGES[rng]
    since_24h = now - timedelta(hours=24)
    state = manager.merged()
    agents = state.agents or []
    active, total, agents_pct = metrics.agents_active(agents)
    compromised, at_risk = await host_risk(s, since_24h)
    load = await alert_load(s, now)

    components = {
        "agents": agents_pct,
        "vulnerabilities": metrics.vulnerability_score(state.vulnerabilities or [], len(agents)) if agents else None,
        "hardening": metrics.sca_compliance(state.sca or []),
        "alerts": metrics.alerts_score(load),
        "coverage": metrics.agent_coverage(state.assets or [], agents) if state.assets else None,
    }
    score = metrics.security_score(components, metrics.parse_weights(settings.score_weights))

    return {
        "generated_at": iso(now),
        "range": rng,
        "demo_mode": settings.demo_mode,
        "kpis": {
            "alerts_24h": await severity_counts(s, since_24h),
            "alerts_7d": await severity_counts(s, now - RANGES["7d"]),
            "agents": {"active": active, "total": total, "pct": agents_pct},
            "hosts_compromised": compromised,
            "hosts_at_risk": at_risk,
            "mttd": await mttd(s, now, now - RANGES["7d"]),
            "incidents": await incidents(s),
            "sca_pct": components["hardening"],
        },
        "score": {"total": score.total, "breakdown": score.breakdown, "alert_load": round(load, 1)},
        "charts": {
            "timeline": await timeline(s, since, "hour" if rng == "24h" else "day"),
            "top_rules": await top_rules(s, since),
            "top_src_ips": await top_src_ips(s, since),
            "heatmap": await heatmap(s, since_24h),
        },
        "dhcp": metrics.pool_usage(state.pools or [], state.leases or [], now),
        "services": await services_uptime(s, since_24h),
    }
