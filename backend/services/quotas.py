"""Small demo abuse budget, independent of provider account quotas."""

import time
from fastapi import HTTPException
from backend.db import connect


def consume(actor, bucket, limit=20, window=3600):
    now = time.time()
    with connect() as db:
        db.execute("DELETE FROM request_budget WHERE at<?", (now - window,))
        count = db.execute(
            "SELECT count(*) FROM request_budget WHERE actor=? AND bucket=?",
            (actor, bucket),
        ).fetchone()[0]
        if count >= limit:
            raise HTTPException(
                429,
                "Demo request budget reached; wait before trying again",
                headers={"Retry-After": str(window)},
            )
        db.execute("INSERT INTO request_budget VALUES (?,?,?)", (actor, bucket, now))
