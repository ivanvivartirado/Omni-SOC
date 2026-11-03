"""Interfaz común de los conectores.

Cada fuente (Wazuh, Suricata, Kea...) implementa BaseConnector. El gestor llama periódicamente a
collect_events() (eventos de seguridad, alta frecuencia) y collect_state() (estado: agentes,
leases, servicios..., baja frecuencia). Un conector solo rellena los campos que conoce.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field


class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


SEVERITY_LABELS = {0: "info", 1: "baja", 2: "media", 3: "alta", 4: "crítica"}


def wazuh_level_to_severity(level: int, thresholds: tuple[int, int, int, int] = (3, 7, 10, 12)) -> Severity:
    low, medium, high, critical = thresholds
    if level >= critical:
        return Severity.CRITICAL
    if level >= high:
        return Severity.HIGH
    if level >= medium:
        return Severity.MEDIUM
    if level >= low:
        return Severity.LOW
    return Severity.INFO


def suricata_severity(sev: int) -> Severity:
    """Suricata: 1 = alta, 2 = media, 3 = baja (y >3 informativa)."""
    return {1: Severity.HIGH, 2: Severity.MEDIUM, 3: Severity.LOW}.get(sev, Severity.INFO)


class SecurityEvent(BaseModel):
    id: str
    timestamp: datetime
    source: str
    severity: Severity
    rule_id: str = ""
    rule_level: int | None = None
    title: str = ""
    category: str = ""
    src_ip: str | None = None
    dst_ip: str | None = None
    dst_port: int | None = None
    protocol: str | None = None
    agent_id: str | None = None
    agent_name: str | None = None
    mitre_ids: list[str] = Field(default_factory=list)
    mitre_tactics: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


AgentStatus = Literal["active", "disconnected", "never_connected", "pending"]


class Agent(BaseModel):
    id: str
    name: str
    ip: str | None = None
    os: str = ""
    version: str = ""
    status: AgentStatus
    last_keepalive: datetime | None = None


class ScaResult(BaseModel):
    agent_id: str
    policy: str
    passed: int
    failed: int
    not_applicable: int = 0


class Vulnerability(BaseModel):
    agent_id: str
    cve: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    package: str = ""
    title: str = ""


class Lease(BaseModel):
    ip: str
    mac: str
    hostname: str = ""
    expires_at: datetime
    state: int = 0
    subnet_id: int = 1


class Reservation(BaseModel):
    ip: str
    mac: str
    hostname: str = ""


class Pool(BaseModel):
    subnet_id: int
    subnet: str
    start: str
    end: str


class ServiceStatus(BaseModel):
    name: str
    target: str
    ok: bool
    latency_ms: float | None = None
    detail: str = ""
    cert_days_left: int | None = None


class Asset(BaseModel):
    name: str
    ip: str | None = None
    mac: str | None = None
    os: str = ""
    role: str = ""
    criticality: Literal["baja", "media", "alta"] = "media"
    vlan: str = ""
    agent_id: str | None = None
    agent_expected: bool = True


class ConnectorState(BaseModel):
    agents: list[Agent] | None = None
    sca: list[ScaResult] | None = None
    vulnerabilities: list[Vulnerability] | None = None
    leases: list[Lease] | None = None
    reservations: list[Reservation] | None = None
    pools: list[Pool] | None = None
    services: list[ServiceStatus] | None = None
    assets: list[Asset] | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class HealthStatus(BaseModel):
    ok: bool
    mode: Literal["demo", "real", "pendiente"]
    detail: str = ""
    checked_at: datetime | None = None


class BaseConnector(ABC):
    name: ClassVar[str]
    label: ClassVar[str]
    mode: ClassVar[Literal["demo", "real", "pendiente"]] = "real"

    @abstractmethod
    async def health(self) -> HealthStatus: ...

    async def collect_events(self, since: datetime | None) -> list[SecurityEvent]:
        return []

    async def collect_state(self) -> ConnectorState:
        return ConnectorState()

    async def close(self) -> None:  # noqa: B027
        """Liberar recursos (clientes HTTP, ficheros abiertos...)."""


class PendingConnector(BaseConnector):
    """Marcador para conectores reales que llegan en fases posteriores."""

    mode = "pendiente"

    def __init__(self, name: str, label: str, phase: int) -> None:
        self.name = name  # type: ignore[misc]
        self.label = label  # type: ignore[misc]
        self._phase = phase

    async def health(self) -> HealthStatus:
        return HealthStatus(ok=False, mode="pendiente", detail=f"Conector real previsto en la fase {self._phase}")
