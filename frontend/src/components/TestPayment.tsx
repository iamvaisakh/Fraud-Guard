import { useState } from 'react'
import type { FormEvent } from 'react'
import { scorePayment, verifyPayment } from '../api'
import type { ScoreResponse, TxnType } from '../types'

type NumField = 'amount' | 'oldbalanceOrg' | 'newbalanceOrig' | 'oldbalanceDest' | 'newbalanceDest' | 'hour'

interface FormState {
  type: TxnType
  amount: string
  oldbalanceOrg: string
  newbalanceOrig: string
  oldbalanceDest: string
  newbalanceDest: string
  hour: string
}

const FIELDS: NumField[] = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'hour']

const PRESETS: Record<string, FormState> = {
  'Normal payment': {
    type: 'CASH_OUT', amount: '5000', oldbalanceOrg: '20000', newbalanceOrig: '15000',
    oldbalanceDest: '10000', newbalanceDest: '15000', hour: '14',
  },
  'Suspicious payment': {
    type: 'TRANSFER', amount: '181', oldbalanceOrg: '181', newbalanceOrig: '0',
    oldbalanceDest: '0', newbalanceDest: '0', hour: '3',
  },
}

export default function TestPayment() {
  const [form, setForm] = useState<FormState>(PRESETS['Normal payment'])
  const [result, setResult] = useState<ScoreResponse | null>(null)
  const [verifyMsg, setVerifyMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((f) => ({ ...f, [k]: v }))

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setBusy(true); setErr(null); setVerifyMsg(null)
    try {
      const res = await scorePayment({
        txn_id: `UI-${Date.now()}`,
        type: form.type,
        sender_id: 'C_demo_sender',
        receiver_id: 'C_demo_receiver',
        amount: Number(form.amount),
        oldbalanceOrg: Number(form.oldbalanceOrg),
        newbalanceOrig: Number(form.newbalanceOrig),
        oldbalanceDest: Number(form.oldbalanceDest),
        newbalanceDest: Number(form.newbalanceDest),
        hour: Number(form.hour),
      })
      setResult(res)
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setErr(`${msg} (check the API key matches)`)
    } finally {
      setBusy(false)
    }
  }

  async function answer(confirmed: boolean) {
    if (!result) return
    try {
      const r = await verifyPayment(result.txn_id, confirmed)
      setVerifyMsg(r.status === 'released'
        ? 'Payment released. Saved as a genuine example.'
        : 'Payment held.')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Unknown error')
    }
  }

  return (
    <div>
      <div className="presets">
        {Object.keys(PRESETS).map((name) => (
          <button key={name} type="button" className="ghost"
                  onClick={() => { setForm(PRESETS[name]); setResult(null) }}>
            {name}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="form">
        <label>Type
          <select value={form.type} onChange={(e) => set('type', e.target.value as TxnType)}>
            <option>TRANSFER</option>
            <option>CASH_OUT</option>
          </select>
        </label>
        {FIELDS.map((k) => (
          <label key={k}>{k}
            <input type="number" value={form[k]} onChange={(e) => set(k, e.target.value)} />
          </label>
        ))}
        <button disabled={busy}>{busy ? 'Scoring…' : 'Score payment'}</button>
      </form>

      {err && <div className="banner">{err}</div>}

      {result && (
        <div className="result">
          <div>
            <span className={`pill big ${result.decision}`}>{result.decision}</span>
            <span className="muted"> risk {result.risk} · {result.latency_ms} ms</span>
          </div>

          {result.reasons && (
            <>
              <h4>Why (SHAP)</h4>
              <ul>
                {result.reasons.map((r) => (
                  <li key={r.feature}>
                    <b>{r.feature}</b> = {Math.round(r.value * 100) / 100}
                    <span className={r.impact > 0 ? 'BLOCK' : 'ALLOW'}>
                      {' '}{r.impact > 0 ? '▲ raises' : '▼ lowers'} risk ({r.impact.toFixed(2)})
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {result.decision === 'VERIFY' && !verifyMsg && (
            <div className="presets">
              <span className="muted">Confirm with OTP: was this you?</span>
              <button type="button" onClick={() => answer(true)}>Yes, this was me</button>
              <button type="button" className="ghost" onClick={() => answer(false)}>No</button>
            </div>
          )}
          {verifyMsg && <p className="muted">{verifyMsg}</p>}
        </div>
      )}
    </div>
  )
}