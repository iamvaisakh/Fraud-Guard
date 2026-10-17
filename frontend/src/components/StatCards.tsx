import type { Stats } from '../types'

interface Props { s: Stats }

export default function StatCards({ s }: Props) {
  const total = s.scanned || 1
  const pct = (n: number) => `${(n / total) * 100}%`

  const cards = [
    { label: 'Scanned', value: s.scanned, cls: '' },
    { label: 'Allowed', value: s.allow, cls: 'ALLOW' },
    { label: 'Verify', value: s.verify, cls: 'VERIFY' },
    { label: 'Fraud blocked', value: s.block, cls: 'BLOCK' },
    { label: 'Latency p50 / p99', value: `${s.p50_ms} / ${s.p99_ms} ms`, cls: '' },
  ]

  return (
    <>
      <div className="cards">
        {cards.map((c) => (
          <div className="card" key={c.label}>
            <div className="label">{c.label}</div>
            <div className={`num ${c.cls}`}>{c.value}</div>
          </div>
        ))}
      </div>
      <div className="split" title="Share of ALLOW / VERIFY / BLOCK">
        <div className="seg ALLOW-bg" style={{ width: pct(s.allow) }} />
        <div className="seg VERIFY-bg" style={{ width: pct(s.verify) }} />
        <div className="seg BLOCK-bg" style={{ width: pct(s.block) }} />
      </div>
    </>
  )
}