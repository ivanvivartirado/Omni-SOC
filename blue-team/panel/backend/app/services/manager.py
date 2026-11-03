"""Gestor de conectores: sondea cada fuente, guarda eventos y publica en vivo."""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select

from app.connectors.base import BaseConnector, ConnectorState, HealthStatus
from app.core.config import Settings
from app.core.db import session_factory
from app.demo.world import DemoRun, DemoWorld
from app.models import AttackRun, Event, Incident, IncidentStatus, LoginAttempt, ServiceCheck
from app.services.event_bus import EventBus
from app.services.serializers import event_out, event_to_row

log = logging.getLogger("panel.manager")

STATE_FIELDS = ("agents", "sca", "vulnerabilities", "leases", "reservations", "pools", "services", "assets")


class ConnectorManager:
    def __init__(
        self, settings: Settings, connectors: list[BaseConnector], bus: EventBus, world: DemoWorld | None = None
    ) -> None:
        self.settings = settings
        self.connectors = connectors
        self.bus = bus
        self.world = world
        self.state: dict[str, ConnectorState] = {}
        self.health: dict[str, HealthStatus] = {}
        self.last_event_at: dict[str, datetime] = {}
        self._tasks: list[asyncio.Task[None]] = []

    # ------------------------------------------------------------------ ciclo de vida
    async def start(self) -> None:
        if self.world is not None:
            await self._seed_demo_history()
        for c in self.connectors:
            self._tasks.append(asyncio.create_task(self._events_loop(c), name=f"events:{c.name}"))
            self._tasks.append(asyncio.create_task(self._state_loop(c), name=f"state:{c.name}"))
        self._tasks.append(asyncio.create_task(self._maintenance_loop(), name="maintenance"))

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await t
        for c in self.connectors:
            await c.close()

    # ------------------------------------------------------------------ bucles
    async def _events_loop(self, c: BaseConnector) -> None:
        while True:
            try:
                events = await c.collect_events(self.last_event_at.get(c.name))
                if events:
                    await self._store_events(events)
                    self.last_event_at[c.name] = max(e.timestamp for e in events)
                    for e in events:
                        self.bus.publish({"type": "event", "data": event_out(e)})
                if self.world is not None:
                    await self._store_runs(self.world.drain_runs())
            except Exception:  # noqa: BLE001 - un conector caído no debe tumbar el panel
                log.exception("Error recogiendo eventos de %s", c.name)
            await asyncio.sleep(self.settings.events_poll_seconds)

    async def _state_loop(self, c: BaseConnector) -> None:
        while True:
            try:
                self.health[c.name] = await c.health()
                st = await c.collect_state()
                self.state[c.name] = st
                if st.services:
                    async with session_factory()() as s:
                        s.add_all(
                            ServiceCheck(service=x.name, ok=x.ok, latency_ms=x.latency_ms, detail=x.detail[:255])
                            for x in st.services
                        )
                        await s.commit()
            except Exception as exc:  # noqa: BLE001
                log.exception("Error recogiendo estado de %s", c.name)
                self.health[c.name] = HealthStatus(ok=False, mode=c.mode, detail=str(exc)[:200], checked_at=datetime.now(UTC))
            await asyncio.sleep(self.settings.state_poll_seconds)

    async def _maintenance_loop(self) -> None:
        while True:
            await asyncio.sleep(3600)
            try:
                cutoff = datetime.now(UTC) - timedelta(days=self.settings.event_retention_days)
                async with session_factory()() as s:
                    await s.execute(delete(Event).where(Event.ts < cutoff))
                    await s.execute(delete(ServiceCheck).where(ServiceCheck.ts < cutoff))
                    await s.execute(delete(LoginAttempt).where(LoginAttempt.ts < datetime.now(UTC) - timedelta(days=7)))
                    await s.commit()
            except Exception:  # noqa: BLE001
                log.exception("Error en mantenimiento")

    # ------------------------------------------------------------------ persistencia
    async def _store_events(self, events: list) -> None:  # noqa: ANN001
        async with session_factory()() as s:
            ids = [e.id for e in events]
            existing = set((await s.scalars(select(Event.id).where(Event.id.in_(ids)))).all())
            s.add_all(event_to_row(e) for e in events if e.id not in existing)
            await s.commit()

    async def _store_runs(self, runs: list[DemoRun]) -> None:
        if not runs:
            return
        async with session_factory()() as s:
            s.add_all(
                AttackRun(
                    scenario=r.scenario,
                    started_at=r.started_at,
                    detected_at=r.detected_at,
                    detected_rule=r.detected_rule,
                    false_positives=r.false_positives,
                )
                for r in runs
            )
            await s.commit()

    async def _seed_demo_history(self) -> None:
        assert self.world is not None
        async with session_factory()() as s:
            if await s.scalar(select(func.count()).select_from(Event)):
                return
        log.info("Modo demo: generando %s días de histórico", self.settings.demo_history_days)
        now = datetime.now(UTC)
        events, runs = self.world.generate_history(self.settings.demo_history_days, now)
        async with session_factory()() as s:
            for i in range(0, len(events), 1000):
                s.add_all(event_to_row(e) for e in events[i : i + 1000])
                await s.flush()
            s.add_all(
                AttackRun(
                    scenario=r.scenario,
                    started_at=r.started_at,
                    detected_at=r.detected_at,
                    detected_rule=r.detected_rule,
                    false_positives=r.false_positives,
                )
                for r in runs
            )
            s.add_all(self._demo_incidents(now))
            for h in range(24 * 7, 0, -1):
                for x in self.world.services():
                    s.add(
                        ServiceCheck(
                            service=x.name, ts=now - timedelta(hours=h), ok=x.ok, latency_ms=x.latency_ms, detail=x.detail
                        )
                    )
            await s.commit()

    @staticmethod
    def _demo_incidents(now: datetime) -> list[Incident]:
        def inc(title: str, sev: int, status: IncidentStatus, who: str, hours: float, closed: float | None) -> Incident:
            return Incident(
                title=title,
                severity=sev,
                status=status,
                assignee=who,
                created_at=now - timedelta(hours=hours),
                closed_at=now - timedelta(hours=closed) if closed is not None else None,
            )

        return [
            inc("Fuerza bruta SSH desde 192.168.15.164 contra omni-server", 3, IncidentStatus.CLOSED, "Iker", 140, 138),
            inc("Escaneo de puertos Nmap contra omni-cliente", 2, IncidentStatus.CLOSED, "Ivan", 96, 95),
            inc("EICAR detectado en omni-cliente (/home/usuario/Descargas)", 4, IncidentStatus.RESOLVED, "Ivan", 50, 49),
            inc("Agente de pc-rrhh desconectado más de 48 h", 2, IncidentStatus.ANALYSIS, "Iker", 30, None),
            inc("Fuerza bruta SSH con éxito: revisar sesión de ubuntu", 4, IncidentStatus.NEW, "", 3, None),
        ]

    # ------------------------------------------------------------------ vistas agregadas
    def merged(self) -> ConnectorState:
        out = ConnectorState()
        for st in self.state.values():
            for f in STATE_FIELDS:
                val = getattr(st, f)
                if val is not None:
                    setattr(out, f, (getattr(out, f) or []) + val)
            out.extra.update(st.extra)
        return out
