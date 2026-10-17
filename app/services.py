import json
import hashlib
import hmac
import numpy as np
import onnxruntime as ort
import xgboost as xgb
from app.config import MODELS_DIR, TOKEN_SECRET, FEEDBACK_FILE
from app.schemas import Txn

class ModelManager:
    def __init__(self):
        self.manifest_path = MODELS_DIR / "manifest.json"
        self.onnx_path = MODELS_DIR / "model.onnx"
        self.xgb_path = MODELS_DIR / "model.json"

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Missing manifest at {self.manifest_path}")

        with open(self.manifest_path, "r") as f:
            self.manifest = json.load(f)

        # Integrity verification
        for f, expected in self.manifest["hashes"].items():
            model_file = MODELS_DIR / f
            if not model_file.exists():
                raise FileNotFoundError(f"Required model file missing: {model_file}")
            actual = hashlib.sha256(open(model_file, "rb").read()).hexdigest()
            if actual != expected:
                raise RuntimeError(f"Model tampering detected for {f}: hash mismatch!")

        self.features = self.manifest["features"]
        self.block_t = self.manifest["metrics"]["block_threshold"]
        self.verify_t = self.manifest["metrics"]["verify_threshold"]

        # Inference session & XGBoost explainer
        self.sess = ort.InferenceSession(str(self.onnx_path))
        self.booster = xgb.Booster()
        self.booster.load_model(str(self.xgb_path))

    def build_features(self, t: Txn) -> np.ndarray:
        return np.array([[
            t.amount,
            t.oldbalanceOrg,
            t.newbalanceOrig,
            t.oldbalanceDest,
            t.newbalanceDest,
            t.newbalanceOrig + t.amount - t.oldbalanceOrg,
            t.oldbalanceDest + t.amount - t.newbalanceDest,
            t.hour,
            1.0 if t.type == "TRANSFER" else 0.0
        ]], dtype=np.float32)

    def explain(self, x: np.ndarray, top: int = 3):
        contribs = self.booster.predict(xgb.DMatrix(x, feature_names=None), pred_contribs=True)[0][:-1]
        top_indices = np.argsort(-np.abs(contribs))[:top]
        return [
            {
                "feature": self.features[i],
                "value": float(x[0][i]),
                "impact": float(contribs[i])
            }
            for i in top_indices
        ]

    def predict_risk(self, x: np.ndarray) -> float:
        out = self.sess.run(None, {"input": x})
        probs = out[1]
        if isinstance(probs[0], dict):
            return float(probs[0][1])
        return float(probs[0][1])

def tokenize_id(raw_id: str) -> str:
    """Keyed HMAC hash – irreversible without secret."""
    return hmac.new(TOKEN_SECRET, raw_id.encode(), hashlib.sha256).hexdigest()[:16]

def save_feedback(entry: dict):
    feedback_data = []
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, "r") as f:
                feedback_data = json.load(f)
        except Exception:
            feedback_data = []
    feedback_data.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_data, f, indent=2)
