import os
from pathlib import Path
import pandas as pd
import requests
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

URL = os.environ.get("API_URL", "http://localhost:8000/score")
API_KEY = os.environ.get("API_KEY", "demo123")
HEAD = {"x-api-key": API_KEY}
DATA_PATH = ROOT_DIR / "data" / "PS_20174392719_1491204439457_log.csv"

def evaluate():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}.")

    print(f"Reading validation sample from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df = df[df.type.isin(["TRANSFER", "CASH_OUT"])].sort_values("step")
    df = df[df.step > df.step.quantile(0.8)]  # Unseen future part

    # Sample up to 200 fraud + 2000 genuine
    sample = pd.concat([
        df[df.isFraud == 1].head(200),
        df[df.isFraud == 0].sample(min(2000, len(df[df.isFraud == 0])), random_state=7),
    ]).sample(frac=1, random_state=1)

    print(f"Sending {len(sample)} test transactions to {URL}...")
    y_true, y_pred, lat = [], [], []
    for i, r in enumerate(sample.itertuples()):
        body = dict(
            txn_id=f"E{i}",
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
            res = requests.post(URL, json=body, headers=HEAD, timeout=10).json()
            y_true.append(int(r.isFraud))
            y_pred.append(1 if res.get("decision") == "BLOCK" else 0)
            lat.append(res.get("latency_ms", 0))
        except Exception as e:
            print(f"Error querying {URL}: {e}")
            return

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    print("\n=== Evaluation Results ===")
    print(f"Caught fraud (TP): {tp}   Missed fraud (FN): {fn}")
    print(f"Wrongly blocked genuine (FP): {fp}   Correctly allowed (TN): {tn}")
    print(f"Precision: {precision_score(y_true, y_pred):.3f}")
    print(f"Recall:    {recall_score(y_true, y_pred):.3f}")
    if lat:
        print(f"Avg latency: {sum(lat)/len(lat):.2f} ms")

if __name__ == "__main__":
    evaluate()
