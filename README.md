# 🛡️ Fraud Guard

An end-to-end real-time financial fraud detection engine built with **XGBoost**, **ONNX Runtime**, **FastAPI**, and **React + TypeScript**.

**IBM Z Datathon 2026 | Track: AI Secured**

Every payment request is scored in milliseconds, and the system returns **ALLOW**, **VERIFY** (OTP/PIN) or **BLOCK** before the money moves. Each blocked or held payment comes with a SHAP explanation, and no sensitive data is exposed.

---

## 🧭 How it works

```text
Payment request -> Tokenize IDs + build features -> XGBoost (ONNX) -> Thresholds -> ALLOW / VERIFY / BLOCK
                                                                          |
                                        Dashboard + SHAP reasons + decision history (SQLite)
```

## ✨ Features

- **Real-time scoring** with ONNX Runtime and p50 / p99 latency tracking
- **Three outcomes:** ALLOW, VERIFY (user confirms with OTP), BLOCK
- **Explainability:** top-3 SHAP reasons for every non-ALLOW decision
- **Feedback loop:** payments confirmed as "this was me" are saved as genuine examples for retraining
- **React + TypeScript dashboard:** live counters, scrollable recent decisions, full history with filtering, and a "Test a payment" form
- **Honest evaluation:** time-based split, PR-AUC, precision and recall (never plain accuracy)

## 🔐 AI Secured

| Area | What we do |
|---|---|
| Privacy | Account IDs are replaced with keyed HMAC-SHA256 tokens; the model sees only derived numbers |
| Access control | `/score`, `/verify` and `/history` require an API key |
| Model integrity | SHA-256 hashes of the model files are verified at startup; tampering stops the server |
| Adversarial robustness | `adversarial.py` simulates evasive fraud and retrains to harden the model |
| Transparency | SHAP reasons give an audit trail without personal data |

---

## 🏗️ Project structure

```text
fraudguard/
├── app/                        # FastAPI backend
│   ├── __init__.py
│   └── main.py                 # API routes, tokenizer, SHAP explainer, SQLite history
│
├── train.py                    # Model training, thresholds, ONNX export, SHA-256 manifest
├── evaluate.py                 # Precision, recall and latency against the live API
├── adversarial.py              # Adversarial robustness testing
├── simulate.py                 # Transaction stream simulator for the dashboard
│
├── models/                     # Model artifacts (created by train.py, git-ignored)
│   ├── manifest.json           # Thresholds, metrics, feature list, SHA-256 hashes
│   ├── model.onnx              # ONNX model used for inference
│   └── model.json              # XGBoost model used for SHAP explanations
│
├── frontend/                   # React + TypeScript + Vite dashboard
│   ├── .env                    # VITE_API_KEY
│   ├── vite.config.ts          # Dev proxy to the backend
│   └── src/
│       ├── main.tsx  App.tsx  api.ts  types.ts  index.css
│       └── components/
│           ├── StatCards.tsx  RecentTable.tsx
│           ├── HistoryTable.tsx  TestPayment.tsx
│
├── data/                       # Datasets (git-ignored)
├── requirements.txt            # Python dependencies
├── .env                        # API_KEY, TOKEN_SECRET (git-ignored)
├── .env.example                # Example environment variables
└── .gitignore
```

---

## 🚀 Getting started

### 1. Prerequisites
- **Python 3.10 to 3.12** recommended (3.13 may have package compatibility issues)
- **Node.js 18+** and npm

### 2. Python environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment configuration

Create `.env` in the project root (or copy `.env.example`):

```text
API_KEY=demo123
TOKEN_SECRET=change-me
```

Create `frontend/.env`:

```text
VITE_API_KEY=demo123
```

The two API key values must match.

### 4. Dataset setup

Download the [PaySim Financial Fraud Dataset](https://www.kaggle.com/datasets/ealaxi/paysim1) from Kaggle and place the CSV in the `data/` directory:

```text
data/PS_20174392719_1491204439457_log.csv
```

*(Large datasets are excluded from Git to stay within repository size limits.)*

---

## 🧠 ML workflows

Train the model and export the ONNX artifacts (run once, and again after any model change):
```bash
python train.py
```

Check live accuracy against the running API:
```bash
python evaluate.py
```

Run adversarial robustness tests:
```bash
python adversarial.py
```

Stream transactions at the running backend so the dashboard moves:
```bash
python simulate.py
```

---

## 💻 Running the application locally

### Backend (FastAPI)
```bash
uvicorn app.main:app --port 8000
```
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔌 API

| Endpoint | Description |
|---|---|
| `POST /score` | Score a payment; returns decision, risk, latency and SHAP reasons |
| `POST /verify/{txn_id}?confirmed=true` | User answered the OTP; confirmed payments are saved as genuine examples |
| `GET /stats` | Counters, latency percentiles and recent decisions |
| `GET /history` | Paged decision history (`before_id`, `limit`, `decision`) |

All endpoints except `/stats` require the header `x-api-key`.

---

## 🐳 Running with Docker (optional)

Docker is not needed for the demo. To package the backend as a container:

```bash
docker build -t fraudguard .
docker run -p 8000:8000 --env-file .env fraudguard
```

This serves the API at [http://localhost:8000](http://localhost:8000). To also serve the React dashboard from the same container, use a multi-stage Dockerfile that builds `frontend/` and mount `frontend/dist` from FastAPI.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `FileNotFoundError: models/manifest.json` | Run `python train.py` first |
| 401 errors | Make sure `API_KEY` (root `.env`) equals `VITE_API_KEY` (`frontend/.env`) |
| Dashboard shows "Cannot reach the API" | Start the backend; restart `npm run dev` after changing config |
| No VERIFY decisions appear | PaySim scores are well separated; widen the VERIFY band in `train.py` and retrain |

## ⚠️ Limitations

- PaySim is synthetic, so metrics look stronger than they would on real UPI data. The balance-error features carry most of the signal.
- Thresholds are tuned on the same held-out period used for reporting; a separate validation slice would be more rigorous.
- Dashboard counters live in memory and reset on restart; decision history persists in `decisions.db`.
- The thresholds in `manifest.json` are not covered by the integrity check, only the model files.
- IBM Z / LinuxONE: the model is exported to ONNX and designed to be portable (for example with the IBM Z Deep Learning Compiler). It has not been tested on s390x.

## 🔭 Next steps

- Retrain on real bank/UPI data with a privacy review
- Add payee history, device and velocity features
- Federated learning across banks
- Integration with a bank payment switch
- Container packaging and s390x testing
- Automated tests (pytest) for feature engineering and the API