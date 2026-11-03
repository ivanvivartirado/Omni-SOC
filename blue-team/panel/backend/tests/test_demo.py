from datetime import UTC, datetime, timedelta

import pytest

from app.connectors.base import Severity
from app.connectors.registry import CONNECTORS, build_connectors
from app.core.config import Settings
from app.demo.world import DemoWorld

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)


def test_hydra_scenario_is_detected_with_brute_force_rules():
    events, run = DemoWorld(seed=1).scenario_hydra(NOW)
    rules = {e.rule_id for e in events}
    assert rules & {"5712", "5763"} and "2001219" in rules
    assert all(e.src_ip == "192.168.15.164" for e in events)
    assert run.detected_at is not None and (run.detected_at - NOW).total_seconds() < 60


def test_eicar_scenario_raises_critical_virustotal():
    events, run = DemoWorld(seed=2).scenario_eicar(NOW)
    vt = next(e for e in events if e.rule_id == "87105")
    assert vt.severity == Severity.CRITICAL and vt.agent_name == "omni-cliente"
    assert run.detected_rule in {"52502", "87105"}


def test_advance_releases_only_due_events():
    w = DemoWorld(seed=3)
    w.trigger("nmap_scan", NOW)
    w.advance(NOW + timedelta(seconds=0.5))
    early = w.take("suricata")
    w.advance(NOW + timedelta(seconds=30))
    late = w.take("suricata")
    assert all(e.timestamp <= NOW + timedelta(seconds=0.5) for e in early)
    assert late and all(e.source == "suricata" for e in late)


def test_history_spans_requested_days():
    events, runs = DemoWorld(seed=4).generate_history(2, NOW)
    assert min(e.timestamp for e in events) >= NOW - timedelta(days=2)
    assert max(e.timestamp for e in events) < NOW
    assert runs


@pytest.mark.parametrize("demo", [True, False])
def test_registry_builds_all_enabled(tmp_path, demo):
    s = Settings(data_dir=tmp_path, demo_mode=demo, enabled_connectors="wazuh,kea")
    conns = build_connectors(s, DemoWorld(seed=5) if demo else None)
    assert [c.name for c in conns] == ["wazuh", "kea"]
    assert all(c.mode == ("demo" if demo else "pendiente") for c in conns)
    assert len(CONNECTORS) == 7
