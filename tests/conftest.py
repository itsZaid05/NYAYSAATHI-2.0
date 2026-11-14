import pytest
from fastapi.testclient import TestClient
from backend.config import settings
from backend.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    from backend.providers import GeminiProvider

    monkeypatch.setattr(GeminiProvider, "generation_cooldown_until", 0.0)
    monkeypatch.setattr(GeminiProvider, "generation_state", {})
    monkeypatch.setattr(settings, "runtime", tmp_path / "runtime")
    monkeypatch.setattr(settings, "gemini_key", "")
    monkeypatch.setattr(settings, "gemini_model", "")
    monkeypatch.setattr(settings, "terms_reviewed", False)
    monkeypatch.setattr(settings, "lawyer_password", "test-only-private-password")
    with TestClient(app) as c:
        c.post("/api/session")
        c.headers["X-CSRF-Token"] = c.cookies.get("nyay_csrf")
        yield c


@pytest.fixture
def intake_data():
    return {
        "narrative": "Fictional: I bought a defective laptop from Demo Seller on 2026-10-01. It failed on 2026-10-03 and the seller refused a replacement.",
        "jurisdiction": "IN",
        "language": "en",
        "consent": {"processing": True, "fictional_demo": True, "ai_processing": False},
    }
