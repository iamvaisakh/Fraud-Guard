import pandas as pd
from ml.features import make_features, FEATURES

def test_feature_columns_and_calculations():
    sample_data = pd.DataFrame([{
        "step": 15,
        "type": "TRANSFER",
        "amount": 1000.0,
        "oldbalanceOrg": 5000.0,
        "newbalanceOrig": 4000.0,
        "oldbalanceDest": 100.0,
        "newbalanceDest": 1100.0,
    }])

    feat = make_features(sample_data)

    # Verify column structure
    assert list(feat.columns) == FEATURES
    assert len(feat) == 1

    row = feat.iloc[0]
    # Check balance error math
    # errorOrig = newbalanceOrig + amount - oldbalanceOrg = 4000 + 1000 - 5000 = 0.0
    assert row["errorOrig"] == 0.0
    # errorDest = oldbalanceDest + amount - newbalanceDest = 100 + 1000 - 1100 = 0.0
    assert row["errorDest"] == 0.0
    # hour = 15 % 24 = 15
    assert row["hour"] == 15
    # is_transfer = 1 for TRANSFER
    assert row["is_transfer"] == 1

def test_cash_out_transfer_flag():
    sample_data = pd.DataFrame([{
        "step": 2,
        "type": "CASH_OUT",
        "amount": 500.0,
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 500.0,
    }])

    feat = make_features(sample_data)
    assert feat.iloc[0]["is_transfer"] == 0
