"""Local-only demo runner. Reads an explicitly seeded private lawyer password."""

import os
from pathlib import Path
from backend.config import settings

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Local fictional-data demo; no public binding"
    )
    parser.add_argument(
        "--model",
        help="Explicit runtime-only generation-model override, selected after live verification",
    )
    parser.add_argument(
        "--embedding-model", help="Explicit runtime-only embedding-model override"
    )
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8010")))
    args = parser.parse_args()
    if args.model:
        settings.gemini_model = args.model
    if args.embedding_model:
        settings.embedding_model = args.embedding_model
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
        port=args.port,
        access_log=False,
    )
