import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    processing_mode: str = "demonstration"
    runtime: Path = Path(
        os.getenv("NYAYSAATHI_RUNTIME", str(ROOT / "runtime"))
    ).resolve()
    gemini_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"
    embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL") or "gemini-embedding-001"
    verify_models_on_start: bool = (
        os.getenv("GEMINI_VERIFY_ON_START", "true").lower() == "true"
    )
    model_configuration: dict | None = None
    terms_reviewed: bool = os.getenv("GEMINI_TERMS_REVIEWED", "false").lower() == "true"
    lawyer_password: str = os.getenv("DEMO_LAWYER_PASSWORD", "")
    secure_cookie: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    session_hours: int = max(1, min(168, int(os.getenv("SESSION_TTL_HOURS", "24"))))
    retention_days: int = max(1, min(30, int(os.getenv("RETENTION_DAYS", "7"))))


settings = Settings()
