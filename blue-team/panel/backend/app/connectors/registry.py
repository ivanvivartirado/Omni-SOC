"""Registro de conectores. Para añadir una fuente nueva: crea su clase y añádela a CONNECTORS."""

from dataclasses import dataclass

from app.connectors.base import BaseConnector, PendingConnector
from app.core.config import Settings
from app.demo import connectors as demo
from app.demo.world import DemoWorld


@dataclass(frozen=True)
class ConnectorSpec:
    name: str
    label: str
    demo_cls: type[demo.DemoConnector]
    real_cls: type[BaseConnector] | None
    phase: int


CONNECTORS: list[ConnectorSpec] = [
    ConnectorSpec("wazuh", "Wazuh SIEM", demo.WazuhDemo, None, 2),
    ConnectorSpec("suricata", "Suricata IDS", demo.SuricataDemo, None, 2),
    ConnectorSpec("kea", "Kea DHCP", demo.KeaDemo, None, 3),
    ConnectorSpec("dns", "BIND9 DNS", demo.DnsDemo, None, 3),
    ConnectorSpec("pfsense", "pfSense", demo.PfSenseDemo, None, 3),
    ConnectorSpec("services", "Salud de servicios", demo.ServicesDemo, None, 3),
    ConnectorSpec("github", "GitHub Projects", demo.GithubDemo, None, 5),
]


def build_connectors(settings: Settings, world: DemoWorld | None) -> list[BaseConnector]:
    enabled = set(settings.connectors)
    result: list[BaseConnector] = []
    for spec in CONNECTORS:
        if spec.name not in enabled:
            continue
        if settings.demo_mode:
            assert world is not None
            result.append(spec.demo_cls(world))
        elif spec.real_cls is not None:
            result.append(spec.real_cls(settings))  # type: ignore[call-arg]
        else:
            result.append(PendingConnector(spec.name, spec.label, spec.phase))
    return result
