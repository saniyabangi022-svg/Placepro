"""Loads settings from the .env file (never hard-code credentials)."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class Settings:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "rpms_db")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    FRONTEND_DIR = (ROOT / os.getenv("FRONTEND_DIR", "../placepro-frontend")).resolve()
    LOG_FILE = ROOT / "logs" / "activity_log.txt"


settings = Settings()
