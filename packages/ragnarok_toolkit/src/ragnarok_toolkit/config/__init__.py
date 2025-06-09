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

# ─── RDB settings ──────────────────────────────────────────────────────────
RDB_HOST = os.environ.get("RDB_HOST", "localhost")
RDB_PORT = os.environ.get("RDB_PORT", "5432")
RDB_DATABASE_NAME = "ragnarok"
RDB_USERNAME = os.environ.get("RDB_USERNAME", "postgres")
RDB_PASSWORD = os.environ.get("RDB_PASSWORD", "lin061593")

# ─── Permission manager ───────────────────────────────────────────────────────
PERMISSION_CACHE_SIZE = int(os.environ.get("PERMISSION_CACHE_SIZE", "1000"))

# ─── JWT / Authentication settings ────────────────────────────────────────────
# Secret key for signing tokens. Must be kept safe!
SECRET_KEY = os.environ.get("SECRET_KEY", "your-default-dev-secret-key-please-change")  # never use this in prod

# JWT signing algorithm
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

# Token expiry (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ─── ODB settings ───────────────────────────────────────────────────────────
# ODB_ENDPOINT = os.environ.get("ODB_ENDPOINT", "http://localhost:9000")
# ODB_ACCESS_KEY = os.environ.get("ODB_ACCESS_KEY", "fTdBpg4eFpmMWdojeCHO")
# ODB_SECRET_KEY = os.environ.get("ODB_SECRET_KEY", "LgkALYBJiQqiPTuQCfs017k7e8QEjrSPCdZLUki1")

ODB_ENDPOINT = os.environ.get("ODB_ENDPOINT", "http://81.70.198.42:9000")
ODB_ACCESS_KEY = os.environ.get("ODB_ACCESS_KEY", "minioadmin")
ODB_SECRET_KEY = os.environ.get("ODB_SECRET_KEY", "minioadmin")

# ——— HF API KEY ─────────────────────────────────────────────────────────────
HF_API_KEY = os.environ.get("HF_API_KEY", "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")

# ———— SILICONFLOW API KEY ───────────────────────────────────────────────────
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "sf_1234567890")
