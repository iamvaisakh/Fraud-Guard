import os
import time
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

URL = os.environ.get("API_URL", "http://localhost:8000/score")
API_KEY = os.environ.get("API_KEY", "demo123")
DATA_PATH = ROOT_DIR / "data" / "PS_20174392719_1491204439457_log.csv"

def simulate(delay_sec: float = 0.2, limit_transactions: int = 330):
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}.")

    print(f"Loading simulation transactions from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df = df[df.type.isin(["TRANSFER", "CASH_OUT"])].sort_values("step")
    df = df[df.step > df.step.quantile(0.8)]

    sample = pd.concat([
        df[df.isFraud == 1].head(30),
        df[df.isFraud == 0].sample(min(300, len(df[df.isFraud == 0])), random_state=1)
    ]).sample(frac=1, random_state=42)

    if limit_transactions:
        sample = sample.head(limit_transactions)

    print(f"Simulating stream of {len(sample)} transactions to {URL}...")
    for i, r in enumerate(sample.itertuples()):
        body = dict(
            txn_id=f"T{i}",
            type=r.type,
            amount=float(r.amount),
            oldbalanceOrg=float(r.oldbalanceOrg),
            newbalanceOrig=float(r.newbalanceOrig),
            oldbalanceDest=float(r.oldbalanceDest),
            newbalanceDest=float(r.newbalanceDest),
            hour=int(r.step % 24),
            sender_id=str(r.nameOrig),
            receiver_id=str(r.nameDest),
        )
        try:
            res = requests.post(
                URL,
                json=body,
                headers={"x-api-key": API_KEY},
                timeout=5
            ).json()
            is_fraud_label = "🚨 FRAUD" if r.isFraud == 1 else "✅ GENUINE"
            print(f"[{i+1}/{len(sample)}] Actual: {is_fraud_label} | Decision: {res.get('decision')} | Risk: {res.get('risk')} | Latency: {res.get('latency_ms')}ms")
        except Exception as e:
            print(f"Failed to post transaction {i}: {e}")
            break

        time.sleep(delay_sec)

if __name__ == "__main__":
    simulate()
