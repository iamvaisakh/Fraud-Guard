import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
DATA_DIR = ROOT_DIR / "data"
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"

# Load environment configuration
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.environ.get("API_KEY", "demo123")
TOKEN_SECRET = os.environ.get("TOKEN_SECRET", "change-me-to-a-secure-random-secret").encode()
FEEDBACK_FILE = ROOT_DIR / "feedback.json"
