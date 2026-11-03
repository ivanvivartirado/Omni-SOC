from datetime import UTC, datetime

from app.connectors.base import BaseConnector, ConnectorState, HealthStatus, SecurityEvent
from app.demo.world import DemoWorld


class DemoConnector(BaseConnector):
    mode = "demo"

    def __init__(self, world: DemoWorld) -> None:
        self.world = world

    async def health(self) -> HealthStatus:
        return HealthStatus(ok=True, mode="demo", detail="Datos simulados", checked_at=datetime.now(UTC))


class _EventSource(DemoConnector):
    async def collect_events(self, since: datetime | None) -> list[SecurityEvent]:
        self.world.advance()
        return self.world.take(self.name)


class WazuhDemo(_EventSource):
    name = "wazuh"
    label = "Wazuh SIEM"

    async def collect_state(self) -> ConnectorState:
        w = self.world
        return ConnectorState(
            agents=w.agents(datetime.now(UTC)), sca=w.sca(), vulnerabilities=w.vulnerabilities(), assets=w.assets()
        )


class SuricataDemo(_EventSource):
    name = "suricata"
    label = "Suricata IDS"


class KeaDemo(DemoConnector):
    name = "kea"
    label = "Kea DHCP"

    async def collect_state(self) -> ConnectorState:
        w = self.world
        return ConnectorState(leases=w.leases(datetime.now(UTC)), reservations=w.reservations(), pools=w.pools())


class DnsDemo(DemoConnector):
    name = "dns"
    label = "BIND9 DNS"

    async def collect_state(self) -> ConnectorState:
        return ConnectorState(extra={"dns": self.world.dns()})


class PfSenseDemo(DemoConnector):
    name = "pfsense"
    label = "pfSense"

    async def collect_state(self) -> ConnectorState:
        return ConnectorState(extra={"pfsense": self.world.pfsense()})


class ServicesDemo(DemoConnector):
    name = "services"
    label = "Salud de servicios"

    async def collect_state(self) -> ConnectorState:
        return ConnectorState(services=self.world.services())


class GithubDemo(DemoConnector):
    name = "github"
    label = "GitHub Projects"

    async def collect_state(self) -> ConnectorState:
        return ConnectorState(extra={"project": self.world.github()})
