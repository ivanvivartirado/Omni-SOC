from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import current_user, require_role
from app.models import AuditLog, Event, Role, User
from app.services import dashboard
from app.services.audit import audit
from app.services.serializers import event_out, iso

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/summary")
async def summary(
    request: Request,
    range: Literal["24h", "7d"] = "24h",
    _: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await dashboard.summary(session, request.app.state.manager, request.app.state.settings, range)


@router.get("/alerts")
async def alerts(
    source: Literal["wazuh", "suricata"] | None = None,
    min_severity: int = Query(0, ge=0, le=4),
    q: str | None = Query(None, max_length=100),
    src_ip: str | None = Query(None, max_length=64),
    agent: str | None = Query(None, max_length=128),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    conds = [Event.severity >= min_severity]
    if source:
        conds.append(Event.source == source)
    if src_ip:
        conds.append(Event.src_ip == src_ip)
    if agent:
        conds.append(Event.agent_name == agent)
    if q:
        like = f"%{q}%"
        conds.append(or_(Event.title.ilike(like), Event.rule_id == q, Event.src_ip == q, Event.agent_name.ilike(like)))
    total = await session.scalar(select(func.count()).select_from(Event).where(*conds))
    rows = await session.scalars(select(Event).where(*conds).order_by(Event.ts.desc()).limit(limit).offset(offset))
    return {"total": total, "items": [event_out(e) for e in rows]}


@router.get("/alerts/{event_id}")
async def alert_detail(
    event_id: str, _: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    ev = await session.get(Event, event_id)
    if not ev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alerta no encontrada")
    return event_out(ev, include_raw=True)


@router.get("/connectors")
async def connectors(request: Request, _: User = Depends(current_user)) -> list[dict[str, Any]]:
    m = request.app.state.manager
    out = []
    for c in m.connectors:
        h = m.health.get(c.name)
        out.append(
            {
                "name": c.name,
                "label": c.label,
                "mode": c.mode,
                "ok": h.ok if h else None,
                "detail": h.detail if h else "Iniciando",
                "checked_at": iso(h.checked_at) if h else None,
                "last_event_at": iso(m.last_event_at.get(c.name)),
            }
        )
    return out


@router.get("/state")
async def state(request: Request, _: User = Depends(current_user)) -> dict[str, Any]:
    return request.app.state.manager.merged().model_dump(mode="json")


@router.post("/demo/trigger/{scenario}")
async def demo_trigger(
    scenario: Literal["hydra_ssh", "nmap_scan", "eicar"],
    request: Request,
    user: User = Depends(require_role(Role.ANALYST)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    world = request.app.state.manager.world
    if world is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo disponible en modo demo")
    run = world.trigger(scenario)
    await audit(session, request, "demo_trigger", user=user, target=scenario)
    return {"scenario": run.scenario, "started_at": iso(run.started_at), "detected_at": iso(run.detected_at)}


@router.get("/audit")
async def audit_log(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    total = await session.scalar(select(func.count()).select_from(AuditLog))
    rows = await session.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit).offset(offset))
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "ts": iso(r.ts),
                "username": r.username,
                "action": r.action,
                "target": r.target,
                "ip": r.ip,
                "details": r.details,
            }
            for r in rows
        ],
    }
