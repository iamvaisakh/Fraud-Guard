import os
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_recall_curve, average_precision_score
from onnxmltools import convert_xgboost
from onnxmltools.convert.common.data_types import FloatTensorType

try:
    from ml.features import FEATURES, make_features
except ImportError:
    from features import FEATURES, make_features

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "PS_20174392719_1491204439457_log.csv"
MODELS_DIR = ROOT_DIR / "models"

def train():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Please ensure the CSV is placed in data/.")

    print(f"Loading dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df = df[df["type"].isin(["TRANSFER", "CASH_OUT"])].sort_values("step")

    # Time-based split: train on the past, test on the future
    cut = df["step"].quantile(0.8)
    tr, te = df[df.step <= cut], df[df.step > cut]
    Xtr, ytr = make_features(tr).values, tr["isFraud"].values
    Xte, yte = make_features(te).values, te["isFraud"].values

    spw = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=spw,
        tree_method="hist",
        eval_metric="aucpr",
        n_jobs=-1,
    )
    print("Training XGBoost classifier...")
    model.fit(Xtr, ytr)

    p = model.predict_proba(Xte)[:, 1]
    prec, rec, thr = precision_recall_curve(yte, p)
    pr_auc = average_precision_score(yte, p)

    # BLOCK threshold: highest recall while precision >= 90%
    ok = np.where(prec[:-1] >= 0.90)[0]
    block_t = float(thr[ok[np.argmax(rec[:-1][ok])]]) if len(ok) else 0.9
    # VERIFY threshold: precision >= 50% (uncertain zone)
    ok2 = np.where(prec[:-1] >= 0.50)[0]
    verify_t = float(thr[ok2[np.argmax(rec[:-1][ok2])]]) if len(ok2) else 0.5
    verify_t = min(verify_t, block_t)

    i = int(np.argmin(np.abs(thr - block_t)))
    metrics = {
        "pr_auc": float(pr_auc),
        "precision": float(prec[i]),
        "recall": float(rec[i]),
        "block_threshold": block_t,
        "verify_threshold": verify_t,
    }
    print("Training metrics:", metrics)

    # Save models + thresholds
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = MODELS_DIR / "model.json"
    onnx_path = MODELS_DIR / "model.onnx"
    manifest_path = MODELS_DIR / "manifest.json"

    model.get_booster().save_model(str(json_path))  # used for SHAP
    onx = convert_xgboost(model, initial_types=[("input", FloatTensorType([None, len(FEATURES)]))])
    with open(onnx_path, "wb") as f:
        f.write(onx.SerializeToString())

    # Integrity hashes (SHA-256)
    hashes = {
        "model.onnx": hashlib.sha256(open(onnx_path, "rb").read()).hexdigest(),
        "model.json": hashlib.sha256(open(json_path, "rb").read()).hexdigest(),
    }
    with open(manifest_path, "w") as f:
        json.dump({"hashes": hashes, "metrics": metrics, "features": FEATURES}, f, indent=2)

    print(f"Artifacts successfully exported to {MODELS_DIR}")

if __name__ == "__main__":
    train()
