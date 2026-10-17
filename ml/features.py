import pandas as pd

FEATURES = [
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "errorOrig",
    "errorDest",
    "hour",
    "is_transfer",
]

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate engineering features for transaction fraud detection."""
    out = pd.DataFrame()
    out["amount"] = df["amount"]
    out["oldbalanceOrg"] = df["oldbalanceOrg"]
    out["newbalanceOrig"] = df["newbalanceOrig"]
    out["oldbalanceDest"] = df["oldbalanceDest"]
    out["newbalanceDest"] = df["newbalanceDest"]
    out["errorOrig"] = df["newbalanceOrig"] + df["amount"] - df["oldbalanceOrg"]
    out["errorDest"] = df["oldbalanceDest"] + df["amount"] - df["newbalanceDest"]
    out["hour"] = df["step"] % 24
    out["is_transfer"] = (df["type"] == "TRANSFER").astype(int)
    return out[FEATURES]
