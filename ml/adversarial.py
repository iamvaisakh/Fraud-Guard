from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb

try:
    from ml.features import make_features, FEATURES
except ImportError:
    from features import make_features, FEATURES

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "PS_20174392719_1491204439457_log.csv"

def evade(frame, seed=0):
    """Reshape fraud rows so they look more normal."""
    rng = np.random.default_rng(seed)
    f = frame.copy()
    f["amount"] = f["amount"] * rng.uniform(0.3, 0.9, len(f))
    f["newbalanceOrig"] = f["oldbalanceOrg"] - f["amount"]       # no origin mismatch
    f["newbalanceDest"] = f["oldbalanceDest"] + f["amount"]      # no dest mismatch
    return f

def fit(X, y):
    spw = (y == 0).sum() / max((y == 1).sum(), 1)
    return xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=spw,
        tree_method="hist",
        n_jobs=-1,
    ).fit(X, y)

def recall(model, frame):
    fr = frame[frame.isFraud == 1]
    return float(model.predict(make_features(fr).values).mean())

def run_adversarial_test():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}.")

    print("Loading data for adversarial evaluation...")
    df = pd.read_csv(DATA_PATH)
    df = df[df.type.isin(["TRANSFER", "CASH_OUT"])].sort_values("step")
    cut = df.step.quantile(0.8)
    tr, te = df[df.step <= cut], df[df.step > cut]

    base = fit(make_features(tr).values, tr.isFraud.values)
    attack = evade(te[te.isFraud == 1])
    attack["isFraud"] = 1
    print("Recall on clean fraud   :", round(recall(base, te), 4))
    print("Recall on evasive fraud :", round(recall(base, attack), 4))

    # Adversarial retraining
    print("Performing adversarial hardening...")
    adv_train = evade(tr[tr.isFraud == 1], seed=1)
    adv_train["isFraud"] = 1
    aug = pd.concat([tr, adv_train])
    hard = fit(make_features(aug).values, aug.isFraud.values)
    print("After hardening         :", round(recall(hard, attack), 4))

if __name__ == "__main__":
    run_adversarial_test()
