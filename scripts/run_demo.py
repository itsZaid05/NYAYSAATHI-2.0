"""Local-only demo runner. Reads an explicitly seeded private lawyer password."""

import os
from pathlib import Path
from backend.config import settings

if __name__ == "__main__":
    cache = settings.runtime / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("XDG_CACHE_HOME", str(cache))
    password = settings.runtime / "demo-lawyer-password"
    if password.exists() and not os.getenv("DEMO_LAWYER_PASSWORD"):
        settings.lawyer_password = password.read_text().strip()
    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", "8010")),
        access_log=False,
    )
