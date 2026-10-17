import type { RecentRow } from '../types'

interface Props { rows: RecentRow[] }

export default function RecentTable({ rows }: Props) {
  if (!rows.length) {
    return <p className="muted">No transactions yet. Run simulate.py or use the form.</p>
  }
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr><th>Txn</th><th>Sender</th><th>Decision</th><th>Risk</th><th>ms</th></tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={`${r.txn}-${i}`}>
              <td className="mono">{r.txn}</td>
              <td className="mono">{r.from}</td>
              <td><span className={`pill ${r.decision}`}>{r.decision}</span></td>
              <td>{r.risk}</td>
              <td>{r.ms}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}