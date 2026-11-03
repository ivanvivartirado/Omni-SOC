export type Role = 'admin' | 'analyst' | 'viewer'
export type Sev = 0 | 1 | 2 | 3 | 4

export interface User { id: number; username: string; full_name: string; role: Role }

export interface SecEvent {
  id: string
  timestamp: string
  source: 'wazuh' | 'suricata'
  severity: Sev
  severity_label?: string
  rule_id: string | null
  rule_level: number | null
  title: string
  category: string | null
  src_ip: string | null
  dst_ip: string | null
  dst_port: number | null
  protocol: string | null
  agent_id: string | null
  agent_name: string | null
  mitre_ids: string[]
  mitre_tactics: string[]
  tags: string[]
  raw?: unknown
}

export type SevCounts = Record<'0' | '1' | '2' | '3' | '4', number>

export interface Summary {
  generated_at: string
  range: '24h' | '7d'
  demo_mode: boolean
  kpis: {
    alerts_24h: SevCounts
    alerts_7d: SevCounts
    agents: { active: number; total: number; pct: number | null }
    hosts_compromised: string[]
    hosts_at_risk: string[]
    mttd: { seconds: number | null; target_seconds: number; runs: number; detected: number; detection_rate: number | null }
    incidents: { open: number; closed: number }
    sca_pct: number | null
  }
  score: {
    total: number | null
    breakdown: Record<string, { score: number | null; weight: number }>
    alert_load: number
  }
  charts: {
    timeline: { bucket: string; s0: number; s1: number; s2: number; s3: number; s4: number }[]
    top_rules: { source: string; rule_id: string; title: string; severity: Sev; count: number }[]
    top_src_ips: { ip: string; count: number; max_severity: Sev }[]
    heatmap: { hosts: string[]; hours: string[]; cells: [hour: number, host: number, count: number][] }
  }
  dhcp: { subnet: string; start: string; end: string; size: number; used: number; pct: number | null }[]
  services: { service: string; checks: number; uptime_pct: number | null; avg_latency_ms: number | null }[]
}

export interface ConnectorInfo {
  name: string
  label: string
  mode: 'demo' | 'real' | 'pendiente'
  ok: boolean | null
  detail: string
  checked_at: string | null
  last_event_at: string | null
}
