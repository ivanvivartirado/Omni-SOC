import { SEV_COLOR, SEV_LABEL } from '../lib/format'
import type { Sev } from '../lib/types'

export function SevBadge({ sev }: { sev: Sev }) {
  return (
    <span
      className="inline-block min-w-[4.5rem] rounded px-2 py-0.5 text-center text-xs font-semibold uppercase"
      style={{ backgroundColor: `${SEV_COLOR[sev]}26`, color: SEV_COLOR[sev] }}
    >
      {SEV_LABEL[sev]}
    </span>
  )
}
