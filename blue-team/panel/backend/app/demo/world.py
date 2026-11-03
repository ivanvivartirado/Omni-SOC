"""Laboratorio simulado de Omni SOC para el MODO DEMO.

Reproduce la red 192.168.15.0/24 y genera eventos con la forma de los reales (reglas y firmas de
Wazuh/Suricata) para los casos de uso CU2 (Hydra contra SSH), CU3 (Nmap) y CU4 (EICAR), además de
ruido de fondo. Los datos son ficticios.
"""

import heapq
import itertools
import random
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.connectors.base import (
    Agent,
    Asset,
    Lease,
    Pool,
    Reservation,
    ScaResult,
    SecurityEvent,
    ServiceStatus,
    Vulnerability,
    suricata_severity,
    wazuh_level_to_severity,
)


@dataclass(frozen=True)
class Host:
    name: str
    ip: str
    mac: str
    os: str
    role: str
    criticality: str
    vlan: str
    agent_id: str | None = None
    agent_status: str = "active"
    agent_version: str = "v4.9.2"
    agent_expected: bool = True


SERVER = Host(
    "omni-server",
    "192.168.15.122",
    "08:00:27:4e:12:7a",
    "Ubuntu Server 24.04 LTS",
    "Servidor (Wazuh, Apache, DNS, DHCP, Suricata)",
    "alta",
    "servidores",
    "000",
)
CLIENT = Host(
    "omni-cliente",
    "192.168.15.165",
    "08:00:27:ac:68:ac",
    "Ubuntu Desktop 24.04 LTS",
    "Equipo de usuario",
    "media",
    "clientes",
    "001",
)
KALI = Host(
    "omni-kali",
    "192.168.15.164",
    "08:00:27:5a:87:bc",
    "Kali Linux 2024.4",
    "Atacante (red team)",
    "baja",
    "laboratorio",
    agent_expected=False,
)
HOSTS: list[Host] = [
    SERVER,
    CLIENT,
    Host(
        "pc-contabilidad",
        "192.168.15.201",
        "08:00:27:c1:9e:02",
        "Windows 11 Pro 23H2",
        "Equipo de usuario (contabilidad)",
        "alta",
        "clientes",
        "002",
    ),
    Host(
        "pc-rrhh",
        "192.168.15.202",
        "08:00:27:7b:31:d4",
        "Windows 10 Pro 22H2",
        "Equipo de usuario (RRHH)",
        "media",
        "clientes",
        "003",
        agent_status="disconnected",
        agent_version="v4.8.1",
    ),
    Host("srv-backup", "192.168.15.203", "08:00:27:e5:40:9b", "Debian 12", "Servidor de copias", "alta", "servidores", "004"),
    Host(
        "impresora-hp",
        "192.168.15.205",
        "3c:52:82:1a:6f:90",
        "HP LaserJet firmware",
        "Impresora de red",
        "baja",
        "clientes",
        agent_expected=False,
    ),
    KALI,
    Host(
        "pfsense",
        "192.168.15.10",
        "08:00:27:00:00:10",
        "pfSense CE 2.7.2",
        "Firewall / router",
        "alta",
        "core",
        agent_expected=False,
    ),
]
HOST_BY_ID = {h.agent_id: h for h in HOSTS if h.agent_id}
UNKNOWN_DEVICE = ("192.168.15.217", "a6:3f:91:5c:0e:27", "android-5f2c")

# rule_id: (nivel, descripción, grupos, mitre ids, mitre tácticas)
WAZUH_RULES: dict[str, tuple[int, str, list[str], list[str], list[str]]] = {
    "5710": (
        5,
        "sshd: Attempt to login using a non-existent user",
        ["syslog", "sshd", "authentication_failed"],
        ["T1110.001", "T1021.004"],
        ["Credential Access", "Lateral Movement"],
    ),
    "5760": (
        5,
        "sshd: authentication failed.",
        ["syslog", "sshd", "authentication_failed"],
        ["T1110.001", "T1021.004"],
        ["Credential Access", "Lateral Movement"],
    ),
    "5712": (
        10,
        "sshd: brute force trying to get access to the system. Non existent user.",
        ["syslog", "sshd", "authentication_failures"],
        ["T1110"],
        ["Credential Access"],
    ),
    "5763": (
        10,
        "sshd: brute force trying to get access to the system. Authentication failed.",
        ["syslog", "sshd", "authentication_failures"],
        ["T1110"],
        ["Credential Access"],
    ),
    "5715": (
        3,
        "sshd: authentication success.",
        ["syslog", "sshd", "authentication_success"],
        ["T1078", "T1021"],
        ["Defense Evasion", "Initial Access", "Lateral Movement"],
    ),
    "40112": (
        12,
        "Multiple authentication failures followed by a success.",
        ["syslog", "attack", "authentication_success"],
        ["T1110"],
        ["Credential Access"],
    ),
    "5501": (
        3,
        "PAM: Login session opened.",
        ["pam", "syslog", "authentication_success"],
        ["T1078"],
        ["Defense Evasion", "Initial Access"],
    ),
    "5402": (
        3,
        "Successful sudo to ROOT executed.",
        ["syslog", "sudo"],
        ["T1548.003"],
        ["Privilege Escalation", "Defense Evasion"],
    ),
    "554": (5, "File added to the system.", ["ossec", "syscheck", "syscheck_entry_added"], [], []),
    "550": (7, "Integrity checksum changed.", ["ossec", "syscheck", "syscheck_entry_modified"], ["T1565.001"], ["Impact"]),
    "52502": (8, "ClamAV: Virus detected", ["clamd", "freshclam", "virus"], [], []),
    "87105": (
        12,
        "VirusTotal: Alert - /home/usuario/Descargas/eicar.com - 62 engines detected this file",
        ["virustotal"],
        ["T1203"],
        ["Execution"],
    ),
    "31101": (5, "Web server 400 error code.", ["web", "accesslog", "attack"], [], []),
    "533": (7, "Listened ports status (netstat) changed (new port opened or closed).", ["ossec"], ["T1049"], ["Discovery"]),
    "60106": (
        3,
        "Windows logon success.",
        ["windows", "authentication_success"],
        ["T1078"],
        ["Defense Evasion", "Initial Access"],
    ),
    "60122": (
        5,
        "Logon failure - Unknown user or bad password.",
        ["windows", "authentication_failed"],
        ["T1078", "T1531"],
        ["Defense Evasion", "Impact"],
    ),
}

# sid: (severidad suricata, firma, categoría)
SURICATA_SIGS: dict[int, tuple[int, str, str]] = {
    2001219: (2, "ET SCAN Potential SSH Scan", "Attempted Information Leak"),
    2009358: (2, "ET SCAN Nmap Scripting Engine User-Agent Detected (Nmap Scripting Engine)", "Web Application Attack"),
    2024364: (2, "ET SCAN Possible Nmap User-Agent Observed", "Web Application Attack"),
    2010937: (2, "ET SCAN Suspicious inbound to mySQL port 3306", "Potentially Bad Traffic"),
    2010936: (2, "ET SCAN Suspicious inbound to Oracle SQL port 1521", "Potentially Bad Traffic"),
    2002910: (2, "ET SCAN Potential VNC Scan 5800-5820", "Attempted Information Leak"),
    2100366: (3, "GPL ICMP_INFO PING *NIX", "Misc activity"),
    2013028: (3, "ET POLICY curl User-Agent Outbound", "Attempted Information Leak"),
    2210045: (3, "SURICATA STREAM Packet with invalid ack", "Generic Protocol Command Decode"),
}

SCENARIO_DETECTION_RULES = {
    "hydra_ssh": {"5712", "5763", "2001219"},
    "nmap_scan": {"2009358", "2024364", "2010937", "2010936", "2002910"},
    "eicar": {"52502", "87105"},
}


@dataclass
class DemoRun:
    scenario: str
    started_at: datetime
    detected_at: datetime | None
    detected_rule: str
    false_positives: int


class DemoWorld:
    def __init__(self, seed: int | None = None, thresholds: tuple[int, int, int, int] = (3, 7, 10, 12)) -> None:
        self.rng = random.Random(seed)
        self.thresholds = thresholds
        self._lock = threading.Lock()
        self._pending: list[tuple[datetime, int, SecurityEvent]] = []
        self._counter = itertools.count()
        self._queues: dict[str, list[SecurityEvent]] = {"wazuh": [], "suricata": []}
        self._runs: list[DemoRun] = []
        now = datetime.now(UTC)
        self._next_noise = now
        self._next_scenario = now + timedelta(seconds=self.rng.uniform(20, 60))

    # ---------------------------------------------------------------- construcción de eventos
    def _id(self) -> str:
        return uuid.UUID(int=self.rng.getrandbits(128)).hex

    def wazuh_event(
        self,
        ts: datetime,
        rule_id: str,
        host: Host,
        src_ip: str | None = None,
        data: dict[str, Any] | None = None,
        full_log: str = "",
    ) -> SecurityEvent:
        level, desc, groups, mitre_ids, tactics = WAZUH_RULES[rule_id]
        raw = {
            "timestamp": ts.isoformat(),
            "rule": {
                "id": rule_id,
                "level": level,
                "description": desc,
                "groups": groups,
                "mitre": {"id": mitre_ids, "tactic": tactics},
            },
            "agent": {"id": host.agent_id, "name": host.name, "ip": host.ip},
            "manager": {"name": SERVER.name},
            "data": {"srcip": src_ip, **(data or {})} if src_ip else (data or {}),
            "full_log": full_log,
            "location": "/var/log/auth.log" if "sshd" in groups else "",
        }
        return SecurityEvent(
            id=self._id(),
            timestamp=ts,
            source="wazuh",
            severity=wazuh_level_to_severity(level, self.thresholds),
            rule_id=rule_id,
            rule_level=level,
            title=desc,
            category=groups[-1],
            src_ip=src_ip,
            dst_ip=host.ip,
            agent_id=host.agent_id,
            agent_name=host.name,
            mitre_ids=mitre_ids,
            mitre_tactics=tactics,
            raw=raw,
        )

    def suricata_event(
        self, ts: datetime, sid: int, src: str, dst: str, dst_port: int | None, proto: str = "TCP"
    ) -> SecurityEvent:
        sev, sig, cat = SURICATA_SIGS[sid]
        src_port = self.rng.randint(32768, 60999)
        raw = {
            "timestamp": ts.isoformat(),
            "flow_id": self.rng.getrandbits(50),
            "in_iface": "enp0s3",
            "event_type": "alert",
            "src_ip": src,
            "src_port": src_port,
            "dest_ip": dst,
            "dest_port": dst_port,
            "proto": proto,
            "alert": {
                "action": "allowed",
                "gid": 1,
                "signature_id": sid,
                "rev": 1,
                "signature": sig,
                "category": cat,
                "severity": sev,
            },
        }
        return SecurityEvent(
            id=self._id(),
            timestamp=ts,
            source="suricata",
            severity=suricata_severity(sev),
            rule_id=str(sid),
            title=sig,
            category=cat,
            src_ip=src,
            dst_ip=dst,
            dst_port=dst_port,
            protocol=proto,
            agent_name=self.host_by_ip(dst),
            raw=raw,
        )

    @staticmethod
    def host_by_ip(ip: str | None) -> str | None:
        return next((h.name for h in HOSTS if h.ip == ip), None)

    # ---------------------------------------------------------------- escenarios
    def scenario_hydra(self, t0: datetime) -> tuple[list[SecurityEvent], DemoRun]:
        rng, events = self.rng, []
        duration = rng.uniform(25, 60)
        attempts = rng.randint(30, 90)
        users = ["root", "admin", "ivan", "iker", "test", "oracle", "ubuntu", "pi"]
        for i in range(attempts):
            ts = t0 + timedelta(seconds=duration * i / attempts + rng.uniform(0, 0.4))
            user = rng.choice(users)
            rule = "5760" if user in ("root", "ivan", "iker", "ubuntu") else "5710"
            events.append(
                self.wazuh_event(
                    ts,
                    rule,
                    SERVER,
                    KALI.ip,
                    {"srcuser": user, "srcport": str(rng.randint(40000, 60000))},
                    f"sshd[{rng.randint(1000, 9999)}]: Failed password for {user} from {KALI.ip} port 22 ssh2",
                )
            )
        events.append(self.suricata_event(t0 + timedelta(seconds=rng.uniform(1.5, 6)), 2001219, KALI.ip, SERVER.ip, 22))
        for _ in range(rng.randint(1, 3)):
            rule = rng.choice(["5712", "5763"])
            events.append(
                self.wazuh_event(t0 + timedelta(seconds=rng.uniform(4, duration)), rule, SERVER, KALI.ip, {"srcuser": "root"})
            )
        if rng.random() < 0.12:
            end = t0 + timedelta(seconds=duration + 1)
            events.append(self.wazuh_event(end, "5715", SERVER, KALI.ip, {"dstuser": "ubuntu"}))
            events.append(self.wazuh_event(end + timedelta(seconds=0.5), "40112", SERVER, KALI.ip, {"dstuser": "ubuntu"}))
        return events, self._run("hydra_ssh", t0, events)

    def scenario_nmap(self, t0: datetime) -> tuple[list[SecurityEvent], DemoRun]:
        rng, events = self.rng, []
        target = rng.choice([SERVER, CLIENT])
        stealthy = rng.random() < 0.06
        if not stealthy:
            sigs = [(2010937, 3306), (2010936, 1521), (2002910, 5800)]
            if rng.random() < 0.6:
                sigs += [(2009358, 80), (2024364, 80)]
            for sid, port in sigs:
                events.append(self.suricata_event(t0 + timedelta(seconds=rng.uniform(1, 12)), sid, KALI.ip, target.ip, port))
        events.append(self.suricata_event(t0 + timedelta(seconds=0.2), 2100366, KALI.ip, target.ip, None, "ICMP"))
        for _ in range(rng.randint(2, 8)):
            events.append(
                self.suricata_event(
                    t0 + timedelta(seconds=rng.uniform(1, 15)), 2210045, KALI.ip, target.ip, rng.choice([22, 53, 80, 443, 8080])
                )
            )
        return events, self._run("nmap_scan", t0, events)

    def scenario_eicar(self, t0: datetime) -> tuple[list[SecurityEvent], DemoRun]:
        rng = self.rng
        slow = rng.random() < 0.1
        base = rng.uniform(70, 180) if slow else 0
        path = "/home/usuario/Descargas/eicar.com"
        events = [
            self.wazuh_event(
                t0 + timedelta(seconds=base + rng.uniform(2, 6)),
                "554",
                CLIENT,
                data={"path": path},
                full_log=f"File '{path}' added",
            ),
            self.wazuh_event(
                t0 + timedelta(seconds=base + rng.uniform(8, 30)),
                "52502",
                CLIENT,
                full_log=f"clamd[812]: {path}: Win.Test.EICAR_HDB-1 FOUND",
            ),
            self.wazuh_event(
                t0 + timedelta(seconds=base + rng.uniform(15, 55)),
                "87105",
                CLIENT,
                data={"virustotal": {"positives": "62", "total": "68", "source": {"file": path}}},
            ),
        ]
        return events, self._run("eicar", t0, events)

    def _run(self, scenario: str, t0: datetime, events: list[SecurityEvent]) -> DemoRun:
        rules = SCENARIO_DETECTION_RULES[scenario]
        hits = sorted((e for e in events if e.rule_id in rules), key=lambda e: e.timestamp)
        first = hits[0] if hits else None
        return DemoRun(
            scenario, t0, first.timestamp if first else None, first.rule_id if first else "", 1 if self.rng.random() < 0.08 else 0
        )

    def random_scenario(self, t0: datetime) -> tuple[list[SecurityEvent], DemoRun]:
        fn = self.rng.choices([self.scenario_hydra, self.scenario_nmap, self.scenario_eicar], weights=[0.4, 0.35, 0.25])[0]
        return fn(t0)

    # ---------------------------------------------------------------- ruido de fondo
    def noise_event(self, ts: datetime) -> SecurityEvent:
        rng = self.rng
        win = HOST_BY_ID["002"]
        choice = rng.choices(
            ["ssh_ok", "pam", "sudo", "win_ok", "win_fail", "web400", "netstat", "fim", "ping", "curl", "stream"],
            weights=[14, 12, 8, 14, 3, 6, 1, 1, 10, 6, 8],
        )[0]
        user = rng.choice(["ivan", "iker"])
        match choice:
            case "ssh_ok":
                return self.wazuh_event(
                    ts, "5715", SERVER, CLIENT.ip, {"dstuser": user}, f"sshd: Accepted publickey for {user} from {CLIENT.ip}"
                )
            case "pam":
                return self.wazuh_event(ts, "5501", rng.choice([SERVER, CLIENT]), data={"dstuser": user})
            case "sudo":
                return self.wazuh_event(
                    ts, "5402", rng.choice([SERVER, CLIENT, HOST_BY_ID["004"]]), data={"srcuser": user, "dstuser": "root"}
                )
            case "win_ok":
                return self.wazuh_event(ts, "60106", win, data={"win": {"eventdata": {"targetUserName": "conta"}}})
            case "win_fail":
                return self.wazuh_event(ts, "60122", win, data={"win": {"eventdata": {"targetUserName": "conta"}}})
            case "web400":
                return self.wazuh_event(
                    ts,
                    "31101",
                    SERVER,
                    rng.choice([CLIENT.ip, win.ip]),
                    {"url": rng.choice(["/favicon.ico", "/wp-login.php", "/.env"]), "id": "404"},
                )
            case "netstat":
                return self.wazuh_event(ts, "533", rng.choice([SERVER, HOST_BY_ID["004"]]))
            case "fim":
                return self.wazuh_event(ts, "550", SERVER, data={"path": rng.choice(["/etc/hosts", "/etc/passwd"])})
            case "ping":
                return self.suricata_event(ts, 2100366, rng.choice([CLIENT.ip, win.ip]), SERVER.ip, None, "ICMP")
            case "curl":
                return self.suricata_event(ts, 2013028, rng.choice([CLIENT.ip, SERVER.ip]), "151.101.2.132", 80)
            case _:
                return self.suricata_event(ts, 2210045, rng.choice([CLIENT.ip, win.ip]), SERVER.ip, 443)

    # ---------------------------------------------------------------- reloj
    def generate_history(self, days: int, now: datetime | None = None) -> tuple[list[SecurityEvent], list[DemoRun]]:
        now = now or datetime.now(UTC)
        t = now - timedelta(days=days)
        events: list[SecurityEvent] = []
        runs: list[DemoRun] = []
        next_scenario = t + timedelta(hours=self.rng.uniform(1, 4))
        while t < now:
            events.append(self.noise_event(t))
            t += timedelta(seconds=self.rng.expovariate(1 / 150))
            if t >= next_scenario:
                evs, run = self.random_scenario(next_scenario)
                events += [e for e in evs if e.timestamp < now]
                runs.append(run)
                next_scenario += timedelta(hours=self.rng.uniform(2, 7))
        return events, runs

    def advance(self, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        with self._lock:
            while self._next_noise <= now:
                self._push(self.noise_event(self._next_noise))
                self._next_noise += timedelta(seconds=self.rng.expovariate(1 / 5))
            while self._next_scenario <= now:
                evs, run = self.random_scenario(self._next_scenario)
                for e in evs:
                    self._push(e)
                self._runs.append(run)
                self._next_scenario += timedelta(seconds=self.rng.uniform(90, 240))
            while self._pending and self._pending[0][0] <= now:
                _, _, ev = heapq.heappop(self._pending)
                self._queues[ev.source].append(ev)

    def trigger(self, scenario: str, now: datetime | None = None) -> DemoRun:
        fn = {"hydra_ssh": self.scenario_hydra, "nmap_scan": self.scenario_nmap, "eicar": self.scenario_eicar}[scenario]
        evs, run = fn(now or datetime.now(UTC))
        with self._lock:
            for e in evs:
                self._push(e)
            self._runs.append(run)
        return run

    def _push(self, ev: SecurityEvent) -> None:
        heapq.heappush(self._pending, (ev.timestamp, next(self._counter), ev))

    def take(self, source: str) -> list[SecurityEvent]:
        with self._lock:
            items, self._queues[source] = self._queues[source], []
        return items

    def drain_runs(self) -> list[DemoRun]:
        with self._lock:
            runs, self._runs = self._runs, []
        return runs

    # ---------------------------------------------------------------- estado
    def agents(self, now: datetime) -> list[Agent]:
        out = []
        for h in HOSTS:
            if not h.agent_id:
                continue
            ka = now - (timedelta(seconds=self.rng.randint(5, 60)) if h.agent_status == "active" else timedelta(days=2, hours=3))
            out.append(
                Agent(
                    id=h.agent_id,
                    name=h.name,
                    ip=h.ip,
                    os=h.os,
                    version=h.agent_version,
                    status=h.agent_status,
                    last_keepalive=ka,
                )
            )  # type: ignore[arg-type]
        return out

    @staticmethod
    def sca() -> list[ScaResult]:
        return [
            ScaResult(
                agent_id="000", policy="CIS Ubuntu Linux 24.04 LTS Benchmark v1.0.0", passed=148, failed=52, not_applicable=31
            ),
            ScaResult(
                agent_id="001", policy="CIS Ubuntu Linux 24.04 LTS Benchmark v1.0.0", passed=121, failed=79, not_applicable=31
            ),
            ScaResult(
                agent_id="002",
                policy="CIS Microsoft Windows 11 Enterprise Benchmark v3.0.0",
                passed=231,
                failed=148,
                not_applicable=12,
            ),
            ScaResult(
                agent_id="003",
                policy="CIS Microsoft Windows 10 Enterprise Benchmark v3.0.0",
                passed=187,
                failed=196,
                not_applicable=9,
            ),
            ScaResult(agent_id="004", policy="CIS Debian Linux 12 Benchmark v1.1.0", passed=162, failed=41, not_applicable=24),
        ]

    @staticmethod
    def vulnerabilities() -> list[Vulnerability]:
        return [
            Vulnerability(
                agent_id="000",
                cve="CVE-2024-38475",
                severity="High",
                package="apache2",
                title="mod_rewrite: mapeo de URL a rutas del sistema",
            ),
            Vulnerability(agent_id="000", cve="CVE-2024-2511", severity="Low", package="openssl"),
            Vulnerability(
                agent_id="001",
                cve="CVE-2024-9680",
                severity="Critical",
                package="firefox",
                title="Use-after-free en animation timelines",
            ),
            Vulnerability(agent_id="001", cve="CVE-2024-6345", severity="High", package="python3-setuptools"),
            Vulnerability(
                agent_id="002", cve="CVE-2025-0411", severity="High", package="7-Zip", title="Bypass de Mark-of-the-Web"
            ),
            Vulnerability(agent_id="002", cve="CVE-2024-43451", severity="Medium", package="Windows NTLM"),
            Vulnerability(
                agent_id="003", cve="CVE-2024-38063", severity="Critical", package="Windows TCP/IP", title="RCE por IPv6"
            ),
            Vulnerability(agent_id="003", cve="CVE-2024-30088", severity="High", package="Windows Kernel"),
            Vulnerability(agent_id="004", cve="CVE-2024-6387", severity="High", package="openssh-server", title="regreSSHion"),
            Vulnerability(agent_id="004", cve="CVE-2023-48795", severity="Medium", package="openssh-server", title="Terrapin"),
            Vulnerability(agent_id="004", cve="CVE-2024-28085", severity="Medium", package="util-linux"),
            Vulnerability(agent_id="001", cve="CVE-2023-4016", severity="Low", package="procps"),
        ]

    def leases(self, now: datetime) -> list[Lease]:
        out = [
            Lease(ip=h.ip, mac=h.mac, hostname=h.name, expires_at=now + timedelta(hours=self.rng.uniform(2, 23)))
            for h in HOSTS
            if h.ip.startswith("192.168.15.2")
        ]
        ip, mac, name = UNKNOWN_DEVICE
        out.append(Lease(ip=ip, mac=mac, hostname=name, expires_at=now + timedelta(minutes=self.rng.uniform(10, 50))))
        return out

    @staticmethod
    def reservations() -> list[Reservation]:
        return [
            Reservation(ip=CLIENT.ip, mac=CLIENT.mac, hostname=CLIENT.name),
            Reservation(ip=KALI.ip, mac=KALI.mac, hostname=KALI.name),
        ]

    @staticmethod
    def pools() -> list[Pool]:
        return [Pool(subnet_id=1, subnet="192.168.15.0/24", start="192.168.15.200", end="192.168.15.230")]

    @staticmethod
    def assets() -> list[Asset]:
        return [
            Asset(
                name=h.name,
                ip=h.ip,
                mac=h.mac,
                os=h.os,
                role=h.role,
                criticality=h.criticality,  # type: ignore[arg-type]
                vlan=h.vlan,
                agent_id=h.agent_id,
                agent_expected=h.agent_expected,
            )
            for h in HOSTS
        ]

    def services(self) -> list[ServiceStatus]:
        rng = self.rng
        spec = [
            ("Apache HTTP", "http://192.168.15.122", 4, None),
            ("Apache HTTPS", "https://192.168.15.122", 6, 287),
            ("Wazuh API", "https://192.168.15.122:55000", 18, 3600),
            ("Wazuh Indexer", "https://192.168.15.122:9200", 25, 3600),
            ("BIND9 DNS", "dns://192.168.15.122:53", 2, None),
            ("Kea DHCP", "udp://192.168.15.122:67", 1, None),
            ("EveBox", "http://192.168.15.122:5636", 9, None),
            ("pfSense", "https://192.168.15.10", 12, 41),
        ]
        out = []
        for name, target, base, cert in spec:
            ok = rng.random() > 0.01
            out.append(
                ServiceStatus(
                    name=name,
                    target=target,
                    ok=ok,
                    latency_ms=round(base * rng.uniform(0.7, 1.8), 1) if ok else None,
                    detail="OK" if ok else "Timeout",
                    cert_days_left=cert,
                )
            )
        return out

    def dns(self) -> dict[str, Any]:
        rng = self.rng
        return {
            "queries_per_min": rng.randint(40, 140),
            "top_domains": [
                {"domain": d, "count": rng.randint(20, 400)}
                for d in [
                    "omnisoc.local",
                    "ubuntu.com",
                    "packages.wazuh.com",
                    "github.com",
                    "microsoft.com",
                    "rules.emergingthreats.net",
                ]
            ],
            "suspicious": [
                {"domain": "xj3k9qz7w1vb.top", "client": CLIENT.ip, "reason": "Entropía alta (posible DGA)"},
                {"domain": "eicar.org", "client": CLIENT.ip, "reason": "Dominio de prueba de malware"},
            ],
        }

    def pfsense(self) -> dict[str, Any]:
        rng = self.rng
        return {
            "status": "mock",
            "blocks_last_hour": rng.randint(5, 80),
            "vlans": [
                {"name": "servidores", "id": 10, "mbps": round(rng.uniform(1, 30), 1)},
                {"name": "soc", "id": 20, "mbps": round(rng.uniform(0.5, 8), 1)},
                {"name": "clientes", "id": 30, "mbps": round(rng.uniform(1, 45), 1)},
            ],
        }

    @staticmethod
    def github() -> dict[str, Any]:
        return {
            "phases": [
                {"name": "Fase 1 · Infraestructura base", "done": 14, "total": 14},
                {"name": "Fase 2 · SIEM e IDS", "done": 9, "total": 12},
                {"name": "Fase 3 · Segmentación y pfSense", "done": 2, "total": 10},
                {"name": "Fase 4 · Respuesta a incidentes", "done": 1, "total": 8},
            ],
            "by_assignee": {"Iker": {"done": 13, "total": 22}, "Ivan": {"done": 13, "total": 22}},
        }
