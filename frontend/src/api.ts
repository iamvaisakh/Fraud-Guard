import type { Stats, ScoreRequest, ScoreResponse, VerifyResponse } from './types'

const KEY = import.meta.env.VITE_API_KEY as string

export const getStats = async (): Promise<Stats> => {
  const r = await fetch('/stats')
  if (!r.ok) throw new Error(`API error ${r.status}`)
  return r.json()
}

export async function scorePayment(body: ScoreRequest): Promise<ScoreResponse> {
  const r = await fetch('/score', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-api-key': KEY },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`API error ${r.status}`)
  return r.json()
}

export async function verifyPayment(txnId: string, confirmed: boolean): Promise<VerifyResponse> {
  const r = await fetch(`/verify/${txnId}?confirmed=${confirmed}`, {
    method: 'POST',
    headers: { 'x-api-key': KEY },
  })
  if (!r.ok) throw new Error(`API error ${r.status}`)
  return r.json()
}