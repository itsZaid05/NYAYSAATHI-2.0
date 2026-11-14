# Deployment and operational limits

This release supports **local fictional-data demonstrations**. Full source-grounded Gemini acceptance gates are not yet satisfied. Do not advertise production legal advice, confidential-data readiness, verified advocates or filing integrations.

## Single-process deployment
1. Install Python 3.11+, Pango/Harfbuzz and Unicode fonts; create a virtualenv and install `requirements.lock` with hash verification as in README.
2. Use a dedicated ordinary OS account. Mount `NYAYSAATHI_RUNTIME` on a private persistent disk, restrict directory access, and configure disk encryption/backup retention separately. Uploaded evidence is inside the SQLite DB, never a public file directory.
3. Provision backend-only secrets through your deployment secret manager. No demo lawyer access exists without a configured password or an explicitly seeded local password file.
4. Start `python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010 --no-access-log` behind a same-origin HTTPS reverse proxy. Use one worker for this demonstration. The app has no cross-origin API. Set `COOKIE_SECURE=true` behind HTTPS, preserve original Host, enforce a 6 MB proxy body limit, and do not expose the runtime/source directory. Disable or redact query strings in proxy logs: PDF download grants are session-bound and expire, but should not be logged unnecessarily.
5. Probe `/api/health`: DB must work; `reviewed_sources` and `gemini_configured` are separate capabilities. Configuration is not proof that a live generation succeeds. The health endpoint deliberately makes no live-Gemini readiness claim.
6. Run synthetic acceptance/API/browser tests against the intended deployment, review accessibility and network failures, then follow the source-review/live-Gemini gates below.

## Release gates still open
- Fetch and manually review 30–60 relevant official passages, rights, versions/commencement, current rules, notifications and official procedures. Current corpus is empty. Confirm actual current links and forum requirements.
- Verify stable Gemini generation and embedding model availability, pricing, account quota and provider terms using secure credentials. Test live structured extraction, follow-up selection, grounded reasoning, citation validation and service failure handling with fictional data.
- Independent legal review of retrieval relevance and legal applicability. Exact-quote validation alone does not establish correct legal analysis.
- Full source-grounded end-to-end rehearsal. Local preparation tests alone cannot meet this gate.
- Before real-user/public deployment: robust account authentication/recovery, per-IP/global API quotas, security/privacy review, malware scanning/sandboxed document parsing, disaster recovery and privacy/provider contract assessment. The single password demo lawyer is not a professional marketplace.

## Retention and recovery
Startup and authenticated requests delete expired sessions/cases with cascading evidence, handoff and grant removal. For idle installations, run an approved scheduled `python -c 'from backend.db import init,cleanup; init(); cleanup()'`. Deletion is logical DB deletion, not certified secure erasure; use encryption/retention controls for disks and backups. Downloaded copies are outside server control. Guest sessions cannot be recovered once their cookie is lost or expired.

## Explicitly unsupported
Actual government submissions, lawyer verification, payments, notifications, live chat/calls, authentic precedent comparison, limitation/forum calculations, OCR, DOCX/image uploads, legal training/fine-tuning, UK advice and real sensitive data on unpaid Gemini. The UI either removes these old mock affordances or explicitly qualifies availability.
