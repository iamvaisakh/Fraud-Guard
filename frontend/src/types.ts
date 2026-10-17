export type Decision = 'ALLOW' | 'VERIFY' | 'BLOCK'

export interface RecentRow {
  txn: string
  from: string
  decision: Decision
  risk: number
  ms: number
}

export interface Stats {
  scanned: number
  allow: number
  verify: number
  block: number
  p50_ms: number
  p99_ms: number
  recent: RecentRow[]
}

export interface Reason {
  feature: string
  value: number
  impact: number
}

export interface ScoreResponse {
  txn_id: string
  decision: Decision
  risk: number
  latency_ms: number
  reasons?: Reason[]
}

export type TxnType = 'TRANSFER' | 'CASH_OUT'

export interface ScoreRequest {
  txn_id: string
  type: TxnType
  amount: number
  oldbalanceOrg: number
  newbalanceOrig: number
  oldbalanceDest: number
  newbalanceDest: number
  hour: number
  sender_id: string
  receiver_id: string
}

export interface VerifyResponse {
  status: 'released' | 'held'
}