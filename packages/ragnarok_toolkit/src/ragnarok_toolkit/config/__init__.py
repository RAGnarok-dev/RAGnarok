# ragnarok_toolkit/config.py

import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─── Logging configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# ─── Environment flags ─────────────────────────────────────────────────────────
ENV = os.environ.get("ENV", "dev")  # e.g. "dev" / "prod"

# ─── Server settings ──────────────────────────────────────────────────────────
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))

# ─── Permission manager ───────────────────────────────────────────────────────
PERMISSION_CACHE_SIZE = int(os.environ.get("PERMISSION_CACHE_SIZE", "1000"))

# ─── JWT / Authentication settings ────────────────────────────────────────────
# Secret key for signing tokens. Must be kept safe!
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "your-default-dev-secret-key-please-change"  # never use this in prod
)

# JWT signing algorithm
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

# Token expiry (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
