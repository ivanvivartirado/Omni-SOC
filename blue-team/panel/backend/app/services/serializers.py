from datetime import UTC, datetime
from typing import Any

from app.connectors.base import SEVERITY_LABELS, SecurityEvent
from app.models import Event


def as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def iso(dt: datetime | None) -> str | None:
    d = as_utc(dt)
    return d.isoformat().replace("+00:00", "Z") if d else None


def event_to_row(ev: SecurityEvent) -> Event:
    return Event(
        id=ev.id,
        ts=ev.timestamp,
        source=ev.source,
        severity=int(ev.severity),
        rule_id=ev.rule_id,
        rule_level=ev.rule_level,
        title=ev.title[:512],
        category=ev.category[:128],
        src_ip=ev.src_ip,
        dst_ip=ev.dst_ip,
        dst_port=ev.dst_port,
        protocol=ev.protocol,
        agent_id=ev.agent_id,
        agent_name=ev.agent_name,
        mitre_ids=ev.mitre_ids,
        mitre_tactics=ev.mitre_tactics,
        tags=ev.tags,
        raw=ev.raw,
    )


def _common(d: dict[str, Any]) -> dict[str, Any]:
    d["severity_label"] = SEVERITY_LABELS[d["severity"]]
    return d


def event_out(ev: Event | SecurityEvent, include_raw: bool = False) -> dict[str, Any]:
    if isinstance(ev, SecurityEvent):
        d = ev.model_dump(exclude={"raw"} if not include_raw else set())
        d["severity"] = int(ev.severity)
        d["timestamp"] = iso(ev.timestamp)
        return _common(d)
    d = {
        "id": ev.id,
        "timestamp": iso(ev.ts),
        "source": ev.source,
        "severity": ev.severity,
        "rule_id": ev.rule_id,
        "rule_level": ev.rule_level,
        "title": ev.title,
        "category": ev.category,
        "src_ip": ev.src_ip,
        "dst_ip": ev.dst_ip,
        "dst_port": ev.dst_port,
        "protocol": ev.protocol,
        "agent_id": ev.agent_id,
        "agent_name": ev.agent_name,
        "mitre_ids": ev.mitre_ids,
        "mitre_tactics": ev.mitre_tactics,
        "tags": ev.tags,
    }
    if include_raw:
        d["raw"] = ev.raw
    return _common(d)
