import base64
import hashlib
import hmac
import io
import json
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from pypdf import PdfReader
from backend.config import ROOT, settings
from backend.db import audit, cleanup, connect, digest, init, session
from backend.engine import assess, make_draft, redact
from backend.packet import packet
from backend.providers import ReviewedLegalSources
from backend.schemas import (
    CaseAssessment,
    Consent,
    DraftRequest,
    Intake,
    LawyerLogin,
    Message,
    ShareRequest,
)


@asynccontextmanager
async def lifespan(app):
    init()
    cleanup()
    yield


app = FastAPI(title="NyaySaathi — Indian consumer case preparation", lifespan=lifespan)
from backend.security import BodyLimit

app.add_middleware(BodyLimit)


@app.middleware("http")
async def guards(request, call_next):
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        from urllib.parse import urlparse

        origin = request.headers.get("origin")
        if (
            origin and urlparse(origin).netloc != request.headers.get("host")
        ) or request.headers.get("sec-fetch-site") == "cross-site":
            return Response("Cross-origin mutation rejected", status_code=403)
        if request.url.path != "/api/session":
            csrf = request.cookies.get("nyay_csrf", "")
            if not csrf or not secrets.compare_digest(
                csrf, request.headers.get("x-csrf-token", "")
            ):
                return Response("CSRF token required", status_code=403)
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 6 * 1024 * 1024):
            return Response("Request too large", status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def actor(request: Request):
    cleanup()
    token = request.cookies.get("nyay_session", "")
    with connect() as db:
        row = db.execute(
            "SELECT * FROM sessions WHERE token_hash=? AND expires_at>?",
            (digest(token), time.time()),
        ).fetchone()
    if not row:
        raise HTTPException(401, "Session expired; start a new confidential workspace")
    return dict(row)


def owner(case_id, who):
    with connect() as db:
        row = db.execute(
            "SELECT * FROM cases WHERE id=? AND owner=?", (case_id, who["token_hash"])
        ).fetchone()
    if not row:
        raise HTTPException(404, "Case not found")
    return dict(row), CaseAssessment.model_validate_json(row["state"])


def evidence_rows(case_id):
    with connect() as db:
        return [
            dict(r)
            for r in db.execute(
                "SELECT id,filename,kind,mime,excerpt FROM evidence WHERE case_id=? ORDER BY created_at",
                (case_id,),
            )
        ]


def save(a, who, action):
    with connect() as db:
        db.execute(
            "UPDATE cases SET state=?,updated_at=? WHERE id=?",
            (a.model_dump_json(), time.time(), a.case_id),
        )
        audit(db, a.case_id, who["token_hash"], action)


def narrative_for(a):
    with connect() as db:
        row = db.execute(
            "SELECT text FROM narratives WHERE case_id=?", (a.case_id,)
        ).fetchone()
    return (
        row["text"]
        if row
        else "\n".join(f.text for f in a.facts if f.origin == "user_allegation")
    )


def refresh(a):
    return assess(
        a.case_id,
        narrative_for(a),
        a.jurisdiction,
        a.language,
        a.consent,
        evidence_rows(a.case_id),
        a,
        use_ai=False,
    )


@app.get("/api/health")
def health():
    with connect() as db:
        db.execute("SELECT 1")
    sources = ReviewedLegalSources()
    return {
        "status": "ok",
        "database": "sqlite-fts5",
        "reviewed_sources": len(sources.records),
        "gemini_configured": bool(
            settings.gemini_key and settings.gemini_model and settings.terms_reviewed
        ),
        "live_gemini_verified": False,
        "lawyer_enabled": bool(settings.lawyer_password),
        "legal_readiness": "reviewed passages required"
        if not sources.records
        else "reviewed source pack loaded",
        "demo_only": True,
    }


@app.post("/api/session")
def new_session(response: Response):
    token = session()
    response.set_cookie(
        "nyay_session",
        token,
        httponly=True,
        samesite="strict",
        secure=settings.secure_cookie,
        max_age=settings.session_hours * 3600,
    )
    response.set_cookie(
        "nyay_csrf",
        secrets.token_urlsafe(24),
        httponly=False,
        samesite="strict",
        secure=settings.secure_cookie,
        max_age=settings.session_hours * 3600,
    )
    return {
        "role": "guest",
        "retention_days": settings.retention_days,
        "session_hours": settings.session_hours,
    }


@app.get("/api/session")
def get_session(who=Depends(actor)):
    return {"role": who["role"]}


@app.get("/api/cases")
def list_cases(who=Depends(actor)):
    with connect() as db:
        rows = db.execute(
            "SELECT id,state,created_at FROM cases WHERE owner=? ORDER BY created_at DESC",
            (who["token_hash"],),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "category": json.loads(r["state"])["category"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@app.post("/api/cases/intake", response_model=CaseAssessment)
def intake(data: Intake, who=Depends(actor)):
    if who["role"] != "guest":
        raise HTTPException(403, "Use a guest workspace for intake")
    if not data.consent.processing:
        raise HTTPException(422, "Explicit processing consent is required")
    if not data.consent.fictional_demo:
        raise HTTPException(
            422,
            "This demonstrator accepts fictional identities and synthetic documents only",
        )
    if data.consent.sharing:
        raise HTTPException(
            422, "Sharing requires a separate deliberate action after review"
        )
    with connect() as db:
        if (
            db.execute(
                "SELECT count(*) FROM cases WHERE owner=?", (who["token_hash"],)
            ).fetchone()[0]
            >= 20
        ):
            raise HTTPException(429, "Workspace case limit reached; delete old cases")
    case_id = uuid.uuid4().hex
    a = assess(
        case_id, data.narrative, data.jurisdiction.upper(), data.language, data.consent
    )
    now = time.time()
    with connect() as db:
        db.execute(
            "INSERT INTO cases VALUES (?,?,?,?,?,?)",
            (
                case_id,
                who["token_hash"],
                now,
                now,
                now + settings.retention_days * 86400,
                a.model_dump_json(),
            ),
        )
        db.execute(
            "INSERT INTO narratives VALUES (?,?)", (case_id, redact(data.narrative))
        )
        audit(
            db,
            case_id,
            who["token_hash"],
            "processing_consent; synthetic_only; ai=" + str(data.consent.ai_processing),
        )
    return a


@app.get("/api/cases/{case_id}/assessment", response_model=CaseAssessment)
def assessment(case_id: str, who=Depends(actor)):
    _, a = owner(case_id, who)
    # Re-check source validity on read: expired passages are never kept alive by case persistence.
    a = refresh(a)
    save(a, who, "assessment_refreshed")
    return a


@app.post("/api/cases/{case_id}/message", response_model=CaseAssessment)
def message(case_id: str, data: Message, who=Depends(actor)):
    _, a = owner(case_id, who)
    text = narrative_for(a) + "\n" + data.text
    if len(text) > 30000:
        raise HTTPException(413, "Case narrative limit reached")
    result = assess(
        case_id, text, a.jurisdiction, a.language, a.consent, evidence_rows(case_id), a
    )
    with connect() as db:
        db.execute(
            "UPDATE narratives SET text=? WHERE case_id=?", (redact(text), case_id)
        )
    save(result, who, "message_added")
    return result


@app.post("/api/cases/{case_id}/evidence")
async def upload(
    case_id: str,
    file: UploadFile = File(...),
    kind: str = Form(...),
    who=Depends(actor),
):
    _, a = owner(case_id, who)
    if kind not in ("invoice", "fault", "communication", "warranty", "other"):
        raise HTTPException(422, "Unknown evidence type")
    data = await file.read(5 * 1024 * 1024 + 1)
    if not data or len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "File must contain 1 byte to 5 MB")
    name = Path(file.filename or "").name[:120]
    mime = file.content_type or ""
    if (
        name.lower().endswith(".pdf")
        and mime == "application/pdf"
        and data.startswith(b"%PDF-")
    ):
        try:
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted or len(reader.pages) > 40:
                raise ValueError()
            for page in reader.pages:
                if page.get("/AA") or page.get("/Annots"):
                    raise ValueError()
            root = reader.trailer["/Root"]
            if any(k in root for k in ("/OpenAction", "/AA", "/Names", "/AcroForm")):
                raise ValueError()
            text = "\n".join(
                (page.extract_text() or "")[:12000] for page in reader.pages
            )[:30000]
        except Exception:
            raise HTTPException(
                422,
                "Unreadable, encrypted, active-content or oversized PDF; upload a flattened synthetic PDF",
            ) from None
    elif name.lower().endswith(".txt") and mime == "text/plain":
        try:
            text = data.decode("utf-8")
            if "\x00" in text:
                raise ValueError()
        except (UnicodeError, ValueError):
            raise HTTPException(
                422, "Text must be UTF-8 without binary content"
            ) from None
        if len(text) > 30000:
            raise HTTPException(413, "Extractable text limit is 30,000 characters")
    else:
        raise HTTPException(
            415,
            "Only UTF-8 .txt and flattened text-based .pdf files are supported; no OCR",
        )
    if redact(text) != text:
        raise HTTPException(
            422,
            "Identifiers detected: upload a wholly synthetic document. Automated detection cannot guarantee privacy.",
        )
    with connect() as db:
        if (
            db.execute(
                "SELECT count(*) FROM evidence WHERE case_id=?", (case_id,)
            ).fetchone()[0]
            >= 12
        ):
            raise HTTPException(429, "Maximum 12 evidence files per case")
        docid = uuid.uuid4().hex
        db.execute(
            "INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)",
            (docid, case_id, name, kind, mime, data, text, time.time()),
        )
        audit(db, case_id, who["token_hash"], "synthetic_document_uploaded:" + docid)
    result = refresh(a)
    save(result, who, "evidence_extracted_locally")
    return {
        "id": docid,
        "filename": name,
        "characters_extracted": len(text),
        "extraction": "text only; no OCR or authenticity verification",
        "warnings": document_flags(a, text),
        "assessment": result.model_dump(mode="json"),
    }


def document_flags(a, text):
    import re

    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    known = {e.date for e in a.timeline}
    return (
        [
            "Document contains dates absent from the narrative; review and reconcile them: "
            + ", ".join(dates)
        ]
        if any(d not in known for d in dates)
        else []
    ) + ([] if text.strip() else ["No extractable text; OCR is unavailable."])


@app.get("/api/cases/{case_id}/evidence")
def documents(case_id: str, who=Depends(actor)):
    _, a = owner(case_id, who)
    return [
        {**r, "warnings": document_flags(a, r["excerpt"])}
        for r in evidence_rows(case_id)
    ]


@app.get("/api/cases/{case_id}/evidence/{doc_id}")
def document(case_id: str, doc_id: str, who=Depends(actor)):
    owner(case_id, who)
    with connect() as db:
        row = db.execute(
            "SELECT * FROM evidence WHERE id=? AND case_id=?", (doc_id, case_id)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Document not found")
    return Response(
        row["content"],
        media_type=row["mime"],
        headers={
            "Content-Disposition": 'attachment; filename="synthetic-evidence'
            + (".pdf" if row["mime"] == "application/pdf" else ".txt")
            + '"'
        },
    )


@app.post("/api/cases/{case_id}/draft", response_model=CaseAssessment)
def draft(case_id: str, data: DraftRequest, who=Depends(actor)):
    _, a = owner(case_id, who)
    if a.category in (
        "unsupported_domain",
        "unsupported_jurisdiction",
        "needs_clarification",
    ):
        raise HTTPException(422, "Drafting is limited to Indian consumer disputes")
    d = make_draft(a)
    if data.content is not None:
        d.content = redact(data.content)
    a.drafts = [d]
    save(a, who, "seller_draft_saved")
    return a


def packet_for(a):
    return packet(refresh(a), evidence_rows(a.case_id))


@app.post("/api/cases/{case_id}/packet-link")
def packet_link(case_id: str, who=Depends(actor)):
    owner(case_id, who)
    nonce = secrets.token_urlsafe(24)
    expiry = int(time.time()) + 300
    payload = f"{case_id}:{expiry}:{nonce}"
    signature = hmac.new(
        who["token_hash"].encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    grant = base64.urlsafe_b64encode((payload + ":" + signature).encode()).decode()
    with connect() as db:
        db.execute(
            "INSERT INTO download_tokens VALUES (?,?,?,?)",
            (digest(grant), case_id, who["token_hash"], expiry),
        )
    return {
        "url": f"/api/cases/{case_id}/packet.pdf?grant={grant}",
        "expires_in_seconds": 300,
        "requires_owner_session": True,
    }


@app.get("/api/cases/{case_id}/packet.pdf")
def pdf(case_id: str, grant: str | None = None, who=Depends(actor)):
    _, a = owner(case_id, who)
    if grant:
        try:
            cid, expiry, nonce, signature = (
                base64.urlsafe_b64decode(grant).decode().split(":")
            )
            expected = hmac.new(
                who["token_hash"].encode(),
                f"{cid}:{expiry}:{nonce}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if (
                cid != case_id
                or int(expiry) < time.time()
                or not hmac.compare_digest(expected, signature)
            ):
                raise ValueError()
        except Exception:
            raise HTTPException(403, "Download link invalid or expired") from None
        with connect() as db:
            if not db.execute(
                "SELECT 1 FROM download_tokens WHERE token_hash=? AND owner=?",
                (digest(grant), who["token_hash"]),
            ).fetchone():
                raise HTTPException(403, "Download grant not found")
    return Response(
        packet_for(a),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="nyaysaathi-case-packet.pdf"'
        },
    )


@app.post("/api/cases/{case_id}/share")
def share(case_id: str, data: ShareRequest, who=Depends(actor)):
    _, a = owner(case_id, who)
    if not data.consent:
        raise HTTPException(422, "Explicit separate sharing consent required")
    if not settings.lawyer_password:
        raise HTTPException(
            503, "Demo lawyer inbox disabled until a private password is configured"
        )
    a.consent.sharing = True
    a.handoff_status = "shared_with_demo_lawyer"
    content = packet_for(a)
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO handoffs VALUES (?,?,?,0)",
            (case_id, content, time.time()),
        )
        db.execute(
            "UPDATE cases SET state=? WHERE id=?", (a.model_dump_json(), case_id)
        )
        audit(
            db,
            case_id,
            who["token_hash"],
            "explicit_share_consent; packet_snapshot_shared_with_demo_lawyer",
        )
    return {
        "status": a.handoff_status,
        "notice": "Shared only with the demonstration inbox; no verified advocate, email or government filing.",
    }


@app.post("/api/cases/{case_id}/revoke")
def revoke(case_id: str, who=Depends(actor)):
    _, a = owner(case_id, who)
    with connect() as db:
        db.execute("DELETE FROM handoffs WHERE case_id=?", (case_id,))
        audit(db, case_id, who["token_hash"], "sharing_revoked")
    a.consent.sharing = False
    a.handoff_status = "not_shared"
    save(a, who, "sharing_status_updated")
    return {
        "status": "not_shared",
        "notice": "Inbox access removed; copies already downloaded cannot be recalled.",
    }


@app.get("/api/sources/{source_id}")
def source(source_id: str):
    found = next((s for s in ReviewedLegalSources().records if s.id == source_id), None)
    if not found:
        raise HTTPException(404, "No currently reviewed source with that ID")
    return found


@app.post("/api/lawyer/login")
def lawyer_login(data: LawyerLogin, response: Response, who=Depends(actor)):
    if not settings.lawyer_password:
        raise HTTPException(503, "Demo lawyer access is disabled")
    # Bound failed attempts to the session; password never logged.
    with connect() as db:
        # Also enforce a global demo login cap so creating fresh sessions cannot bypass it.
        db.execute("DELETE FROM login_attempts WHERE at<?", (time.time() - 900,))
        count = db.execute(
            "SELECT count(*) FROM login_attempts WHERE actor=?", (who["token_hash"],)
        ).fetchone()[0]
        total = db.execute("SELECT count(*) FROM login_attempts").fetchone()[0]
        if count >= 5 or total >= 30:
            raise HTTPException(429, "Too many attempts; try again after 15 minutes")
        db.execute(
            "INSERT INTO login_attempts VALUES (?,?)", (who["token_hash"], time.time())
        )
    if not secrets.compare_digest(data.password, settings.lawyer_password):
        raise HTTPException(403, "Invalid demo lawyer credentials")
    # Separate role cookie replaces guest access; UI keeps guest in original browser/session if desired.
    token = session("lawyer")
    response.set_cookie(
        "nyay_session",
        token,
        httponly=True,
        samesite="strict",
        secure=settings.secure_cookie,
        max_age=settings.session_hours * 3600,
    )
    return {
        "role": "lawyer",
        "notice": "Demonstration account; not a verified advocate",
    }


def require_lawyer(who):
    if who["role"] != "lawyer":
        raise HTTPException(403, "Demo lawyer authentication required")


@app.get("/api/lawyer/inbox")
def inbox(who=Depends(actor)):
    require_lawyer(who)
    with connect() as db:
        rows = db.execute(
            "SELECT case_id,created_at,reviewed FROM handoffs ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/lawyer/inbox/{case_id}/packet.pdf")
def lawyer_packet(case_id: str, who=Depends(actor)):
    require_lawyer(who)
    with connect() as db:
        row = db.execute(
            "SELECT packet FROM handoffs WHERE case_id=?", (case_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "No shared packet")
        audit(db, case_id, who["token_hash"], "demo_lawyer_downloaded_shared_snapshot")
    return Response(
        row["packet"],
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="demo-handoff.pdf"'},
    )


@app.post("/api/lawyer/inbox/{case_id}/review")
def lawyer_review(case_id: str, who=Depends(actor)):
    require_lawyer(who)
    with connect() as db:
        row = db.execute(
            "SELECT state FROM cases WHERE id=? AND EXISTS (SELECT 1 FROM handoffs WHERE case_id=cases.id)",
            (case_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "No shared case")
        a = CaseAssessment.model_validate_json(row["state"])
        a.handoff_status = "reviewed_by_demo_lawyer"
        db.execute(
            "UPDATE cases SET state=? WHERE id=?", (a.model_dump_json(), case_id)
        )
        db.execute("UPDATE handoffs SET reviewed=1 WHERE case_id=?", (case_id,))
        audit(
            db, case_id, who["token_hash"], "demo_lawyer_acknowledged; not_legal_review"
        )
    return {
        "status": "reviewed_by_demo_lawyer",
        "notice": "Demo acknowledgment only; not professional advice",
    }


@app.get("/api/cases/{case_id}/audit")
def audits(case_id: str, who=Depends(actor)):
    owner(case_id, who)
    with connect() as db:
        rows = db.execute(
            "SELECT action,created_at FROM audit WHERE case_id=? ORDER BY id",
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.delete("/api/cases/{case_id}")
def delete(case_id: str, who=Depends(actor)):
    owner(case_id, who)
    with connect() as db:
        db.execute("DELETE FROM cases WHERE id=?", (case_id,))
    return {
        "deleted": True,
        "notice": "Case, evidence, drafts, download grants and handoff removed. Previously downloaded copies cannot be recalled.",
    }


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html")


@app.get("/{asset}")
def asset(asset: str):
    if asset not in {"app.js", "style.css"}:
        raise HTTPException(404, "Not found")
    return FileResponse(ROOT / asset)
