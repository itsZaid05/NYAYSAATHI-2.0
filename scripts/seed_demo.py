"""Create a fictional backend case and private demo-login material (never print secrets)."""

import json
import os
import secrets
import time
import uuid
from backend.config import ROOT, settings
from backend.db import audit, connect, digest, init, session
from backend.engine import assess, make_draft
from backend.schemas import Consent


def main():
    init()
    token = session()
    cid = uuid.uuid4().hex
    narrative = "Fictional: I bought a laptop from Demo Seller on 2026-10-01 for INR 45000. It failed on 2026-10-03. I requested a replacement on 2026-10-04 and the seller refused."
    a = assess(
        cid, narrative, "IN", "en", Consent(processing=True, fictional_demo=True)
    )
    a.drafts = [make_draft(a)]
    now = time.time()
    with connect() as db:
        db.execute(
            "INSERT INTO cases VALUES (?,?,?,?,?,?)",
            (
                cid,
                digest(token),
                now,
                now,
                now + settings.retention_days * 86400,
                a.model_dump_json(),
            ),
        )
        db.execute("INSERT INTO narratives VALUES (?,?)", (cid, narrative))
        audit(
            db, cid, digest(token), "operator_seeded_fictional_demo; processing_consent"
        )
    path = settings.runtime / "seed-session.json"
    path.write_text(
        json.dumps(
            {
                "case_id": cid,
                "nyay_session": token,
                "notice": "Private local demo session cookie; do not commit or share.",
            },
            indent=2,
        )
    )
    path.chmod(0o600)
    password = settings.runtime / "demo-lawyer-password"
    if not password.exists():
        fd = os.open(password, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(secrets.token_urlsafe(24))
    print("Fictional case seeded:", cid)
    print("Private session material:", path)
    print("Private demo lawyer password file:", password)
    print(
        "Start with scripts.run_demo to use this local password. No source or Gemini verification is implied."
    )


if __name__ == "__main__":
    main()
