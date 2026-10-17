from typing import List, Optional, Literal
from pydantic import BaseModel, Field

DecisionType = Literal["ALLOW", "VERIFY", "BLOCK"]

class Txn(BaseModel):
    txn_id: str
    type: Literal["TRANSFER", "CASH_OUT"]
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    hour: int = Field(ge=0, le=23)
    sender_id: str
    receiver_id: str

class Reason(BaseModel):
    feature: str
    value: float
    impact: float

class ScoreResponse(BaseModel):
    txn_id: str
    decision: DecisionType
    risk: float
    latency_ms: float
    reasons: Optional[List[Reason]] = None

class VerifyResponse(BaseModel):
    status: Literal["released", "held"]

class RecentRow(BaseModel):
    txn: str
    from_: str = Field(alias="from")
    decision: DecisionType
    risk: float
    ms: float

    class Config:
        populate_by_name = True

class StatsResponse(BaseModel):
    scanned: int
    allow: int
    verify: int
    block: int
    p50_ms: float
    p99_ms: float
    recent: List[dict]
