import time
from collections import deque
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import API_KEY, FRONTEND_DIST_DIR
from app.schemas import Txn, ScoreResponse, VerifyResponse, StatsResponse
from app.services import ModelManager, tokenize_id, save_feedback

# Initialize core services
app = FastAPI(
    title="Fraud Guard API",
    description="Real-time Financial Fraud Detection Engine with ONNX & XGBoost SHAP",
    version="1.0.0"
)

# Enable CORS for local dev servers (e.g. Vite on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_manager = ModelManager()

# In-memory operational metrics
stats = {"scanned": 0, "allow": 0, "verify": 0, "block": 0}
latencies = deque(maxlen=1000)
recent = deque(maxlen=20)
pending = {}  # txn_id -> features (awaiting user verification)

def verify_auth(key: str):
    if not key or key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

@app.get("/health")
def health():
    return {"status": "ok", "service": "fraudguard-api"}

@app.post("/score", response_model=ScoreResponse)
def score(t: Txn, x_api_key: str = Header(None)):
    verify_auth(x_api_key)
    t0 = time.perf_counter()

    x = model_manager.build_features(t)
    risk = model_manager.predict_risk(x)

    if risk >= model_manager.block_t:
        decision = "BLOCK"
    elif risk >= model_manager.verify_t:
        decision = "VERIFY"
    else:
        decision = "ALLOW"

    ms = (time.perf_counter() - t0) * 1000
    latencies.append(ms)
    stats["scanned"] += 1
    stats[decision.lower()] += 1

    resp = {
        "txn_id": t.txn_id,
        "decision": decision,
        "risk": round(risk, 4),
        "latency_ms": round(ms, 2)
    }

    if decision != "ALLOW":
        resp["reasons"] = model_manager.explain(x)

    if decision == "VERIFY":
        pending[t.txn_id] = x

    recent.appendleft({
        "txn": tokenize_id(t.txn_id),
        "from": tokenize_id(t.sender_id),
        "decision": decision,
        "risk": round(risk, 3),
        "ms": round(ms, 2)
    })

    return resp

@app.post("/verify/{txn_id}", response_model=VerifyResponse)
def verify(txn_id: str, confirmed: bool = Query(...), x_api_key: str = Header(None)):
    verify_auth(x_api_key)
    if confirmed and txn_id in pending:
        feat = pending.pop(txn_id)
        save_feedback({"features": feat[0].tolist(), "label": 0})
        return {"status": "released"}
    elif not confirmed and txn_id in pending:
        pending.pop(txn_id)
        return {"status": "held"}
    return {"status": "held"}

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    l = sorted(latencies) or [0.0]
    p50 = round(l[len(l) // 2], 2)
    p99 = round(l[max(0, int(len(l) * 0.99) - 1)], 2)
    return {
        **stats,
        "p50_ms": p50,
        "p99_ms": p99,
        "recent": list(recent)
    }

# Mount static build files when frontend has been built into frontend/dist
if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        target = FRONTEND_DIST_DIR / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
