from datetime import UTC, datetime, timedelta

from app.connectors.base import Agent, Asset, Lease, Pool, ScaResult, Severity, Vulnerability, wazuh_level_to_severity
from app.services import metrics

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)


def agent(i: str, status: str = "active") -> Agent:
    return Agent(id=i, name=f"a{i}", status=status)  # type: ignore[arg-type]


def test_pct_handles_zero_total():
    assert metrics.pct(1, 0) is None
    assert metrics.pct(1, 3) == 33.3


def test_agents_active_excludes_manager():
    agents = [agent("000"), agent("001"), agent("002", "disconnected"), agent("003"), agent("004", "never_connected")]
    assert metrics.agents_active(agents) == (2, 4, 50.0)


def test_pool_usage_counts_only_valid_leases_in_range():
    pool = Pool(subnet_id=1, subnet="192.168.15.0/24", start="192.168.15.200", end="192.168.15.230")
    leases = [
        Lease(ip="192.168.15.201", mac="a", expires_at=NOW + timedelta(hours=1)),
        Lease(ip="192.168.15.230", mac="b", expires_at=NOW + timedelta(hours=1)),
        Lease(ip="192.168.15.202", mac="c", expires_at=NOW - timedelta(minutes=1)),  # caducado
        Lease(ip="192.168.15.203", mac="d", expires_at=NOW + timedelta(hours=1), state=2),  # liberado
        Lease(ip="192.168.15.165", mac="e", expires_at=NOW + timedelta(hours=1)),  # fuera del pool
    ]
    [usage] = metrics.pool_usage([pool], leases, NOW)
    assert usage["size"] == 31
    assert usage["used"] == 2
    assert usage["pct"] == 6.5


def test_sca_ignores_not_applicable():
    res = [
        ScaResult(agent_id="1", policy="p", passed=60, failed=40, not_applicable=100),
        ScaResult(agent_id="2", policy="p", passed=20, failed=80),
    ]
    assert metrics.sca_compliance(res) == 40.0
    assert metrics.sca_compliance([]) is None


def test_uptime_and_progress():
    assert metrics.uptime(287, 288) == 99.7
    assert metrics.project_progress(26, 44) == 59.1


def test_mttd_ignores_undetected_and_future():
    t = NOW - timedelta(minutes=10)
    runs = [(t, t + timedelta(seconds=10)), (t, t + timedelta(seconds=30)), (t, None), (t, NOW + timedelta(seconds=5))]
    assert metrics.mttd_seconds(runs, NOW) == 20.0
    assert metrics.mttd_seconds([(t, None)], NOW) is None


def test_agent_coverage_only_expected_assets():
    assets = [
        Asset(name="s", agent_id="001"),
        Asset(name="c", agent_id="002"),
        Asset(name="pc", agent_id=None),
        Asset(name="kali", agent_expected=False),
    ]
    agents = [agent("001"), agent("002", "disconnected")]
    assert metrics.agent_coverage(assets, agents) == 33.3


def test_vulnerability_score():
    vulns = [Vulnerability(agent_id="1", cve="c1", severity="Critical"), Vulnerability(agent_id="1", cve="c2", severity="High")]
    assert metrics.vulnerability_score(vulns, 2) == 89.0
    assert metrics.vulnerability_score(vulns, 0) is None


def test_alert_load_decays_with_age():
    fresh = metrics.alert_load([(Severity.CRITICAL, 0)])
    old = metrics.alert_load([(Severity.CRITICAL, 18)])
    assert fresh == 10 and old == 2.5
    assert metrics.alert_load([(Severity.LOW, 0), (Severity.HIGH, 30)]) == 0
    assert metrics.alerts_score(150) == 0


def test_security_score_reweights_missing_components():
    r = metrics.security_score({"agents": 100, "vulnerabilities": 50, "hardening": None, "alerts": 100, "coverage": 50})
    assert r.total == 75.0
    assert r.breakdown["hardening"]["score"] is None
    assert metrics.security_score({k: None for k in metrics.DEFAULT_WEIGHTS}).total is None


def test_parse_weights():
    w = metrics.parse_weights("agents:40,unknown:5,alerts:10")
    assert w["agents"] == 40 and w["alerts"] == 10 and w["coverage"] == 20 and "unknown" not in w


def test_wazuh_level_mapping():
    assert [wazuh_level_to_severity(x) for x in (0, 3, 7, 10, 12, 15)] == [0, 1, 2, 3, 4, 4]
