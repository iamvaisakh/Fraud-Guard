from fastapi.testclient import TestClient
from app.main import app
from app.config import API_KEY

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "scanned" in data
    assert "p50_ms" in data
    assert isinstance(data["recent"], list)

def test_score_unauthorized():
    payload = {
        "txn_id": "test_1",
        "type": "TRANSFER",
        "amount": 100.0,
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 400.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 100.0,
        "hour": 12,
        "sender_id": "C12345",
        "receiver_id": "C67890"
    }
    # No API key provided
    response = client.post("/score", json=payload)
    assert response.status_code == 401

def test_score_authorized():
    payload = {
        "txn_id": "test_2",
        "type": "TRANSFER",
        "amount": 100.0,
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 400.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 100.0,
        "hour": 12,
        "sender_id": "C12345",
        "receiver_id": "C67890"
    }
    response = client.post("/score", json=payload, headers={"x-api-key": API_KEY})
    assert response.status_code == 200
    res = response.json()
    assert res["txn_id"] == "test_2"
    assert res["decision"] in ["ALLOW", "VERIFY", "BLOCK"]
    assert "risk" in res
    assert "latency_ms" in res
