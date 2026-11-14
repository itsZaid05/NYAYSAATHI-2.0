import hashlib
import secrets
import sqlite3
import time
from contextlib import contextmanager
from backend.config import ROOT, settings


@contextmanager
def connect():
    settings.runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = settings.runtime / "cases.sqlite3"
    db = sqlite3.connect(path, timeout=15)
    path.chmod(0o600)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def init():
    with connect() as db:
        db.executescript((ROOT / "backend/schema.sql").read_text())


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def session(role="guest"):
    token = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute(
            "INSERT INTO sessions VALUES (?,?,?)",
            (digest(token), role, time.time() + settings.session_hours * 3600),
        )
    return token


def cleanup():
    with connect() as db:
        db.execute("DELETE FROM cases WHERE expires_at < ?", (time.time(),))
        db.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
        db.execute("DELETE FROM download_tokens WHERE expires_at < ?", (time.time(),))


def audit(db, case_id, actor, action):
    db.execute(
        "INSERT INTO audit(case_id,actor,action,created_at) VALUES (?,?,?,?)",
        (case_id, actor, action, time.time()),
    )
