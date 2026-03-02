import os
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

# Database
_raw_db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://twin:twin@localhost:55432/twin")
# Railway uses postgres:// but SQLAlchemy needs postgresql+psycopg2://
DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1) if _raw_db_url.startswith("postgres://") else _raw_db_url

# Redis
REDIS_URL = os.getenv("REDIS_URL", "")
if not REDIS_URL:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    # Parse host/port from REDIS_URL for modules that need them separately
    from urllib.parse import urlparse as _urlparse
    _parsed = _urlparse(REDIS_URL)
    REDIS_HOST = _parsed.hostname or "localhost"
    REDIS_PORT = _parsed.port or 6379
    REDIS_DB = 0

# JWT Auth
import secrets as _sec
_default_secret = _sec.token_urlsafe(64)
SECRET_KEY = os.getenv("SECRET_KEY", _default_secret)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security
SECURITY_RATE_LIMIT_ENABLED = os.getenv("SECURITY_RATE_LIMIT_ENABLED", "true").lower() == "true"
SECURITY_BRUTE_FORCE_ENABLED = os.getenv("SECURITY_BRUTE_FORCE_ENABLED", "true").lower() == "true"
SECURITY_MAX_LOGIN_ATTEMPTS = int(os.getenv("SECURITY_MAX_LOGIN_ATTEMPTS", "5"))
SECURITY_LOCKOUT_MINUTES = int(os.getenv("SECURITY_LOCKOUT_MINUTES", "10"))

# Proxy configuration (0 = direct connection, 1+ = behind N proxies)
TRUSTED_PROXY_COUNT = int(os.getenv("TRUSTED_PROXY_COUNT", "0"))

# Field-level encryption key (32 bytes, base64-encoded)
# Generate: python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY", "")

# Twin Engine
TICK_MS = int(os.getenv("TICK_MS", "1500"))  # Optimized: 1.5s instead of 0.5s for better performance

# BSV Blockchain (audit notarization)
BSV_PRIVATE_KEY = os.getenv("BSV_PRIVATE_KEY", "")
BSV_NETWORK = os.getenv("BSV_NETWORK", "main")  # "main" or "testnet"
ARC_URL = os.getenv("ARC_URL", "https://arc.gorillapool.io")
WOC_BASE = (
    f"https://{'test-' if os.getenv('BSV_NETWORK', 'main') == 'testnet' else ''}api.whatsonchain.com/v1/bsv/{os.getenv('BSV_NETWORK', 'main')}"
)
LEDGER_PATH = Path(__file__).resolve().parent.parent / "data" / "blockchain_ledger.jsonl"

# Roles
ROLES = {
    "ADMIN": ["read", "write", "delete", "manage_users", "view_analytics"],
    "OPERATOR": ["read", "write", "view_analytics"],
    "VIEWER": ["read"]
}
