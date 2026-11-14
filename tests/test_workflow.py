import io
import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from backend.app import app
from backend.config import ROOT, settings
from backend.db import connect, digest

SCENARIOS = json.loads((ROOT / "synthetic_demo/evaluation_cases.json").read_text())


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_synthetic_consumer_scenarios(client, intake_data, scenario):
    data = {
        **intake_data,
        **{k: scenario[k] for k in ("narrative", "jurisdiction", "language")},
    }
    r = client.post("/api/cases/intake", json=data)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["category"] == scenario["expected_category"]
    assert a["sources"] == [] and a["options"] == []
    assert a["readiness"] == "Needs information"
    assert a["consent"]["sharing"] is False
    assert all(f["origin"] == "user_allegation" for f in a["facts"])
    assert (
        not a["timeline"]
        if scenario["id"] in ("unknown_dates", "invalid_date")
        else True
    )
    assert [e["date"] for e in a["timeline"]] == sorted(
        e["date"] for e in a["timeline"]
    )
    if scenario["id"] == "sensitive_email":
        assert "person@example.invalid" not in json.dumps(a)
    if scenario["id"] == "sensitive_phone":
        assert "9876543210" not in json.dumps(a)
    if scenario["id"] == "sensitive_id":
        assert "1234 5678 9012" not in json.dumps(a)
    if scenario["id"] == "emergency":
        assert (
            any("112" in x for x in a["safety_flags"])
            and not a["illustrative_scenarios"]
        )
    for story in a["illustrative_scenarios"]:
        assert story["label"] == "Fictional illustration — not a judgment"
    assert "not a probability of winning" in " ".join(a["readiness_flags"])


def test_complete_local_journey_and_persistence(client, intake_data):
    a = client.post("/api/cases/intake", json=intake_data).json()
    cid = a["case_id"]
    assert a["timeline"][0]["date"] == "2026-10-01"
    assert any("seller" in q.lower() for q in a["unknowns"])
    r = client.post(
        f"/api/cases/{cid}/message",
        json={
            "text": "The platform was Demo Store. I contacted the seller on 2026-10-04."
        },
    )
    assert r.status_code == 200
    for kind in ["invoice", "fault", "communication", "warranty"]:
        r = client.post(
            f"/api/cases/{cid}/evidence",
            data={"kind": kind},
            files={
                "file": (
                    kind + ".txt",
                    "Fictional " + kind + " dated 2026-10-01",
                    "text/plain",
                )
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["characters_extracted"] > 10
    a = client.get(f"/api/cases/{cid}/assessment").json()
    # Four self-classified uploads do not establish legal or procedural readiness.
    assert a["readiness"] == "Partial"
    assert any(
        f["dimension"] == "legal sources" and f["status"] == "missing"
        for f in a["readiness_findings"]
    )
    assert any("How much" in q for q in a["unknowns"])
    assert len(a["facts"]) >= 5
    a = client.post(f"/api/cases/{cid}/draft", json={}).json()
    assert "NOT FILED" in a["drafts"][0]["content"]
    a = client.post(
        f"/api/cases/{cid}/draft",
        json={
            "content": "Fictional edited seller request. No legal deadline asserted."
        },
    ).json()
    assert a["drafts"][0]["content"].startswith("Fictional edited")
    link = client.post(f"/api/cases/{cid}/packet-link").json()["url"]
    r = client.get(link)
    assert r.status_code == 200 and r.content.startswith(b"%PDF-")
    text = " ".join(
        p.extract_text() or "" for p in PdfReader(io.BytesIO(r.content)).pages
    )
    assert "NyaySaathi" in text and "Fictional edited" in text
    assert "No verified law passages" in text
    assert (
        client.post(f"/api/cases/{cid}/share", json={"consent": False}).status_code
        == 422
    )
    assert (
        client.post(f"/api/cases/{cid}/share", json={"consent": True}).status_code
        == 200
    )
    # A separate app connection and cookie session recover actual persisted database state.
    with TestClient(app) as reopened:
        reopened.cookies.update(client.cookies)
        assert (
            reopened.get(f"/api/cases/{cid}/assessment").json()["drafts"] == a["drafts"]
        )
    with TestClient(app) as lawyer:
        lawyer.post("/api/session")
        lawyer.headers["X-CSRF-Token"] = lawyer.cookies.get("nyay_csrf")
        assert (
            lawyer.post("/api/lawyer/login", json={"password": "wrong"}).status_code
            == 403
        )
        assert (
            lawyer.post(
                "/api/lawyer/login", json={"password": "test-only-private-password"}
            ).status_code
            == 200
        )
        assert lawyer.get("/api/lawyer/inbox").json()[0]["case_id"] == cid
        assert lawyer.get(f"/api/cases/{cid}/assessment").status_code == 404
        assert lawyer.get(f"/api/lawyer/inbox/{cid}/packet.pdf").content.startswith(
            b"%PDF-"
        )
        assert lawyer.post(f"/api/lawyer/inbox/{cid}/review").status_code == 200
        assert (
            client.get(f"/api/cases/{cid}/assessment").json()["handoff_status"]
            == "reviewed_by_demo_lawyer"
        )
        assert client.post(f"/api/cases/{cid}/revoke").status_code == 200
        assert lawyer.get(f"/api/lawyer/inbox/{cid}/packet.pdf").status_code == 404
        assert (
            client.post(f"/api/cases/{cid}/share", json={"consent": True}).status_code
            == 200
        )
        audit = client.get(f"/api/cases/{cid}/audit").json()
        assert any("explicit_share_consent" in row["action"] for row in audit)
        assert client.delete(f"/api/cases/{cid}").status_code == 200
        assert lawyer.get("/api/lawyer/inbox").json() == []
    assert client.get(link).status_code == 404
    with connect() as db:
        for table in ["evidence", "narratives", "audit", "handoffs", "download_tokens"]:
            assert db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_access_consent_csrf_and_files(client, intake_data):
    for field in ["processing", "fictional_demo"]:
        data = {**intake_data, "consent": {**intake_data["consent"], field: False}}
        assert client.post("/api/cases/intake", json=data).status_code == 422
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    assert (
        client.post(
            "/api/cases/intake", json=intake_data, headers={"X-CSRF-Token": "wrong"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/cases/intake",
            json=intake_data,
            headers={"Origin": "https://evil.invalid"},
        ).status_code
        == 403
    )
    assert client.get("/api/lawyer/inbox").status_code == 403
    assert client.get("/.env").status_code == 404
    assert client.get("/synthetic_demo/legacy_unverified_cases.json").status_code == 404
    assert client.get("/api/sources/fake-section-999").status_code == 404
    assert client.get(f"/api/cases/{cid}/packet.pdf?grant=bad").status_code == 403
    with TestClient(app) as stranger:
        assert stranger.get(f"/api/cases/{cid}/assessment").status_code == 401
        stranger.post("/api/session")
        stranger.headers["X-CSRF-Token"] = stranger.cookies.get("nyay_csrf")
        assert stranger.get(f"/api/cases/{cid}/assessment").status_code == 404
        assert stranger.get(f"/api/cases/{cid}/packet.pdf").status_code == 404
        link = client.post(f"/api/cases/{cid}/packet-link").json()["url"]
        assert stranger.get(link).status_code == 404
        assert stranger.delete(f"/api/cases/{cid}").status_code == 404
    for filename, content, mime, expected in [
        ("x.exe", b"MZ123", "application/octet-stream", 415),
        ("x.pdf", b"not pdf", "application/pdf", 415),
        ("x.pdf", b"%PDF-malformed", "application/pdf", 422),
        ("x.txt", b"\x00binary", "text/plain", 422),
        ("x.txt", b"Synthetic name person@example.invalid", "text/plain", 422),
        ("x.txt", b"", "text/plain", 413),
        ("x.txt", b"x" * (5 * 1024 * 1024 + 1), "text/plain", 413),
    ]:
        r = client.post(
            f"/api/cases/{cid}/evidence",
            data={"kind": "invoice"},
            files={"file": (filename, content, mime)},
        )
        assert r.status_code == expected, r.text


def test_no_configured_provider_is_safe(client, intake_data, monkeypatch):
    data = {**intake_data, "consent": {**intake_data["consent"], "ai_processing": True}}
    a = client.post("/api/cases/intake", json=data).json()
    assert "unavailable" in a["ai_status"] and not a["options"]
    monkeypatch.setattr(settings, "lawyer_password", "")
    assert (
        client.post(
            f"/api/cases/{a['case_id']}/share", json={"consent": True}
        ).status_code
        == 503
    )
    assert client.get("/api/health").json()["gemini_configured"] is False


def test_retention_and_session_expiry(client, intake_data):
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    with connect() as db:
        db.execute("UPDATE cases SET expires_at=?", (time.time() - 1,))
    assert client.get(f"/api/cases/{cid}/assessment").status_code == 404
    with connect() as db:
        db.execute("UPDATE sessions SET expires_at=?", (time.time() - 1,))
    assert client.get("/api/cases").status_code == 401


def test_document_date_discrepancy(client, intake_data):
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    r = client.post(
        f"/api/cases/{cid}/evidence",
        data={"kind": "invoice"},
        files={
            "file": ("bill.txt", "Fictional invoice dated 2026-09-15", "text/plain")
        },
    )
    assert "reconcile" in r.json()["warnings"][0]
    doc = r.json()["id"]
    assert (
        client.get(f"/api/cases/{cid}/evidence/{doc}").content
        == b"Fictional invoice dated 2026-09-15"
    )


def test_hindi_pdf_and_unsupported_draft(client, intake_data):
    d = {
        **intake_data,
        "language": "hi",
        "narrative": "काल्पनिक: मैंने ऑनलाइन लैपटॉप खरीदा और वह खराब है।",
    }
    a = client.post("/api/cases/intake", json=d).json()
    cid = a["case_id"]
    assert (
        "विक्रेता"
        in client.post(f"/api/cases/{cid}/draft", json={}).json()["drafts"][0][
            "content"
        ]
    )
    assert client.get(f"/api/cases/{cid}/packet.pdf").content.startswith(b"%PDF-")
    d["jurisdiction"] = "UK"
    a = client.post("/api/cases/intake", json=d).json()
    assert client.post(f"/api/cases/{a['case_id']}/draft", json={}).status_code == 422


def test_actual_chunked_body_limit(client):
    def chunks():
        for _ in range(7):
            yield b"x" * (1024 * 1024)

    assert client.post("/api/session", content=chunks()).status_code == 413


def test_share_snapshot_is_not_updated_without_consent(client, intake_data):
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    assert (
        client.post(f"/api/cases/{cid}/share", json={"consent": True}).status_code
        == 200
    )
    with connect() as db:
        before = db.execute(
            "SELECT packet FROM handoffs WHERE case_id=?", (cid,)
        ).fetchone()["packet"]
    client.post(
        f"/api/cases/{cid}/message",
        json={"text": "The fictional seller has now replied on 2026-10-10."},
    )
    with connect() as db:
        after = db.execute(
            "SELECT packet FROM handoffs WHERE case_id=?", (cid,)
        ).fetchone()["packet"]
    assert before == after


def test_expired_signed_download_and_cookie_flags(client, intake_data):
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    url = client.post(f"/api/cases/{cid}/packet-link").json()["url"]
    with connect() as db:
        db.execute("UPDATE download_tokens SET expires_at=?", (time.time() - 1,))
    assert client.get(url).status_code == 403
    with TestClient(app) as fresh:
        response = fresh.post("/api/session")
        cookies = response.headers.get_list("set-cookie")
        assert any(
            "nyay_session=" in c and "HttpOnly" in c and "SameSite=strict" in c
            for c in cookies
        )
