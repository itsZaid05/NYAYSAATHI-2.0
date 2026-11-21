# Deployment and operational limits

This release supports **local fictional-data demonstrations**. Full source-grounded Gemini acceptance gates are not yet satisfied. Do not advertise production legal advice, confidential-data readiness, verified advocates or filing integrations.

## Single-process deployment
1. Install Python 3.11+, Pango/Harfbuzz and Unicode fonts; create a virtualenv and install `requirements.lock` with hash verification as in README.
2. Use a dedicated ordinary OS account. Mount `NYAYSAATHI_RUNTIME` on a private persistent disk, restrict directory access, and configure disk encryption/backup retention separately. Uploaded evidence is inside the SQLite DB, never a public file directory.
3. Provision backend-only secrets through your deployment secret manager. No demo lawyer access exists without a configured password or an explicitly seeded local password file.
4. Start `python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010 --no-access-log` behind a same-origin HTTPS reverse proxy. Use one worker for this demonstration. The app has no cross-origin API. Set `COOKIE_SECURE=true` behind HTTPS, preserve original Host, enforce a 6 MB proxy body limit, and do not expose the runtime/source directory. Disable or redact query strings in proxy logs: PDF download grants are session-bound and expire, but should not be logged unnecessarily.
5. Probe `/api/health`: DB must work; `reviewed_sources` and `gemini_configured` are separate capabilities. `live_ai_available` requires a current successful generation probe/request and no active quota cooldown. Historical observations and configuration alone do not establish current availability.
6. Run synthetic acceptance/API/browser tests against the intended deployment, review accessibility and network failures, then follow the source-review/live-Gemini gates below.

## Release gates still open
- Fetch and manually review 30–60 relevant official passages, rights, versions/commencement, current rules, notifications and official procedures. Current corpus is empty. Confirm actual current links and forum requirements.
- Generation/embedding access and fictional factual intake were exercised in this environment. Verify pricing, account quota and provider terms for the intended deployment, then test grounded reasoning/citation validation against authentic approved sources; that legal segment remains blocked.
- Independent legal review of retrieval relevance and legal applicability. Exact-quote validation alone does not establish correct legal analysis.
- Full source-grounded end-to-end rehearsal. Local preparation tests alone cannot meet this gate.
- Before real-user/public deployment: robust account authentication/recovery, per-IP/global API quotas, security/privacy review, malware scanning/sandboxed document parsing, disaster recovery and privacy/provider contract assessment. The single password demo lawyer is not a professional marketplace.

## Retention and recovery
Startup and authenticated requests delete expired sessions/cases with cascading evidence, handoff and grant removal. For idle installations, run an approved scheduled `python -c 'from backend.db import init,cleanup; init(); cleanup()'`. Deletion is logical DB deletion, not certified secure erasure; use encryption/retention controls for disks and backups. Downloaded copies are outside server control. Guest sessions cannot be recovered once their cookie is lost or expired.

## Explicitly unsupported
Actual government submissions, lawyer verification, payments, notifications, live chat/calls, authentic precedent comparison, limitation/forum calculations, DOCX uploads, legal training/fine-tuning, UK advice and real sensitive data on unpaid Gemini. The UI either removes these old mock affordances or explicitly qualifies availability. Limited local PNG/JPEG OCR is supported when Tesseract is installed, as described below.

## Current explicit local runtime

The verified local generation model override is `--model gemini-3.1-flash-lite`; the verified embedding override is `--embedding-model gemini-embedding-001`. Start `python -m scripts.run_demo` with those explicit arguments and `--port 8011`. Saved settings are not changed. A listed model may still reject the account; verify actual generation as well.

Schema version 2 is additive and applied at startup. Tesseract OCR runs locally with a 20-second subprocess timeout and image size/pixel limits. English OCR was exercised; Hindi OCR additionally requires the `hin` language pack. PDFs remain untrusted files; production parsing isolation and malware controls are not established. Session-level AI budgets are not sufficient production-wide abuse protection.

No public endpoint, public deployment or publication was created. Existing owner/CSRF/document controls remain active, but this is still a fictional-data-only demonstration. Migrated official/Gemini-documentation domains must be applied in environment settings before source/rights/current-pricing review can proceed. See LEGAL_SOURCE_MANIFEST.md for the exact new grants.

## Startup verification and current release boundary

Normal startup now performs actual synthetic model probes (`GEMINI_VERIFY_ON_START=true`). It detects the incompatible saved generation value, probes the previously audited fallback, and reports selection/errors in `/api/health` and private `runtime/provider-status.json`. It never rewrites the saved secret/model bindings. Listing alone is insufficient, and failures/cooldown must not be represented as readiness.

For this account the paginated catalogue and actual probe now validate configured `gemini-embedding-2`; `gemini-embedding-001` remains an explicit previously tested fallback. Old first-page-only absence is not used to declare a model unavailable. Missing credentials/terms or exhausted quotas retain the local factual workflow, with AI availability qualified.

The deployment remains local, synthetic-data-only and **not a completed legal assistant**. No public URL or environment publication was created. The full release requires the existing migrated-domain draft to be applied, authentic law/rules/guidance with cleared reuse/versions, independent substantive legal review, and further evaluation of the seven secondary issue-label misses.

Transient startup failure does not permanently strand the UI: “Retry AI connection” calls authenticated `POST /api/provider/recheck` (CSRF protected, at most three probes/five minutes/session). It uses only synthetic connectivity data, preserves a pending intake, exposes failure, and respects cooldown. This is bounded user-requested recovery, not guaranteed provider uptime or an unbounded retry loop.
