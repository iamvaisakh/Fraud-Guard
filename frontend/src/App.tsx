import { useEffect, useState } from 'react'
import { getStats } from './api'
import type { Stats } from './types'
import StatCards from './components/StatCards'
import RecentTable from './components/RecentTable'
import TestPayment from './components/TestPayment'

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const s = await getStats()
        if (alive) { setStats(s); setError(null) }
      } catch {
        if (alive) setError('Cannot reach the API on port 8000. Is the server running?')
      }
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => { alive = false; clearInterval(id) }
  }, [])

  return (
    <div className="page">
      <header>
        <h1>Real-Time Fraud Guard</h1>
        <span className="sub">Build to protect your financial transactions</span>
      </header>

      {error && <div className="banner">{error}</div>}

      {stats && (
        <>
          <StatCards s={stats} />
          <div className="two-col">
            <section className="panel">
              <h3>Recent decisions</h3>
              <RecentTable rows={stats.recent} />
            </section>
            <section className="panel">
              <h3>Test a payment</h3>
              <TestPayment />
            </section>
          </div>
        </>
      )}
    </div>
  )
}