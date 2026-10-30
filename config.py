import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _persistent_secret() -> str:
    secret_file = BASE_DIR / ".instance_secret"
    if secret_file.exists():
        return secret_file.read_text(encoding="utf-8").strip()
    secret = secrets.token_urlsafe(64)
    secret_file.write_text(secret, encoding="utf-8")
    return secret


class Config:
    SECRET_KEY = os.getenv("ALPHAX_SECRET_KEY") or _persistent_secret()
    DATABASE = os.getenv("ALPHAX_DATABASE") or str(BASE_DIR / "database" / "alphax.db")
    MARKETPLACE_DATABASE_URL = os.getenv("ALPHAX_POSTGRES_URL", "").strip()
    MARKETPLACE_UPLOAD_ROOT = os.getenv("ALPHAX_TOOL_UPLOAD_ROOT") or str(BASE_DIR / "uploads" / "security_tools")
    CONTENT_HUB_UPLOAD_ROOT = os.getenv("ALPHAX_CONTENT_UPLOAD_ROOT") or str(BASE_DIR / "uploads" / "content_hub")
    MAX_CONTENT_LENGTH = int(os.getenv("ALPHAX_MAX_UPLOAD_MB", "512")) * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("ALPHAX_HTTPS", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    JSON_SORT_KEYS = False
    SEND_FILE_MAX_AGE_DEFAULT = 3600
