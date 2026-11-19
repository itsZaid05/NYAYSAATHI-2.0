# NyaySaathi 2.0

An India-first **fictional-data consumer case-preparation demonstrator**, preserving NyaySaathi's existing purple/cream identity and navigation. One FastAPI service serves the existing vanilla frontend and persists cases in SQLite with FTS5.

**Current boundary:** local intake → facts/timeline → evidence → editable seller letter → PDF → consent-based demo lawyer inbox works. Verified legal reasoning is withheld until official passages pass manual source/rights review. Real Gemini intake and embeddings have now been exercised with explicitly selected supported models; ordinary startup now probes and visibly resolves incompatible generation settings. Authentic-source legal analysis remains unverified and gated. This is not legal advice or an official filing service.

## Install and run

**Testing in Safari on a Mac:** extract the source ZIP and run `Run_NyaySaathi_Mac.command`. It prepares local dependencies and opens Safari after the local server is ready. [Mac instructions and credential limits](docs/MAC_SAFARI.md).

Python 3.11+ (tested on 3.12), Linux with Pango/Harfbuzz and DejaVu/Noto Devanagari fonts for PDF rendering. On Debian/Ubuntu these are supplied by `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz0b`, `fonts-dejavu-core`, `fonts-noto-core`. Use your environment's approved package installer if missing. No Node build or ML weight download is required.

```bash
cd /workspace/NYAYSAATHI-2.0
python -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
mkdir -p runtime/cache
export XDG_CACHE_HOME="$PWD/runtime/cache"
.venv/bin/python -m scripts.seed_demo
.venv/bin/python -m scripts.run_demo --port 8011
```

The command above binds local port **8011** and reads the private, randomly generated lawyer password from `runtime/demo-lawyer-password`. It does not print the password. Use a local development browser to access the server. The server serves only `/`, `/style.css`, `/app.js` and API routes, never `.env`, the database or the synthetic dataset. Do not use a directory-wide static HTTP server.

For development with an explicitly configured environment:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010 --reload --no-access-log
```

`python main.py` also runs the integrated app on port 8011 (or the `PORT` override). No live process survives an environment snapshot. Use the existing checkout; tasks are already isolated and do not need a Git worktree unless explicitly requested.

## Configuration

See `.env.example` for names and non-secret defaults. Export variables with a service manager or shell; the backend does not automatically load `.env`. Never place secret values in JavaScript, source files, docs or chat.

- `GEMINI_API_KEY`: secure backend binding for `generativelanguage.googleapis.com`.
- `GEMINI_MODEL`: select a supported model after `python -m scripts.check_gemini`. Empty/unavailable settings use a visibly reported, previously audited fallback only after an actual startup probe succeeds.
- `GEMINI_EMBEDDING_MODEL`: optional, verify model availability and permission first.
- `GEMINI_TERMS_REVIEWED=true`: operator has reviewed terms/pricing/account quotas; does not itself prove availability. Each session still requires separate AI opt-in. Sensitive-looking input is blocked from model transmission.
- `DEMO_LAWYER_PASSWORD`: private demonstration-account password, no default. The local demo runner can use the seeded private file instead.
- `NYAYSAATHI_RUNTIME`: private persistent directory (default `runtime/`). DB/file permissions restrict access; disk encryption and backups are deployment responsibilities.
- `COOKIE_SECURE=true` behind HTTPS. Leave false only for local HTTP.
- `SESSION_TTL_HOURS` (default 24, maximum 168), `RETENTION_DAYS` (default 7, maximum 30). Case data is also removed when its owning session expires. Cleanup occurs on startup and authenticated requests; schedule maintenance for idle installations if necessary.

Official-source and Gemini domains must be allowed by the environment policy. See [source review and rights](docs/SOURCES_AND_RIGHTS.md). A network/settings draft was saved; this does not apply or publish it. The migrated India Code domain is currently denied; the old PDF URL returns invalid HTML. See the current source manifest. No secret is requested in chat.

## Tests

```bash
.venv/bin/python -m pytest -q
# Optional browser test, using the environment's installed Playwright + Chromium:
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/browser.cjs
```

For another machine, install Playwright using your normal approved tooling (`npm install --no-save --package-lock=false playwright`), set `CHROMIUM_PATH` if required, and supply `NYAY_LAWYER_PASSWORD_FILE` to the local private file for the browser handoff test. The script tests deletion only on a newly created fictional case. No external messages are sent.

[Actual test results](docs/TEST_REPORT.md) distinguish local, synthetic-fixture and blocked live checks. [Demo script](docs/DEMO_SCRIPT.md), [audit](docs/REPO_AUDIT.md), [feature matrix](docs/FEATURE_MATRIX.md), [deployment](docs/DEPLOYMENT.md).

## Data and API

`backend/schema.sql` contains idempotent additive version-1/version-2 migrations, applied at startup. It stores sessions, cases, full redacted narratives, evidence BLOBs/text, audit records, handoff snapshots, expiring signed grants, FTS index and optional embedding cache. Runtime files are ignored by Git. `scripts.seed_demo` creates one fictional case/draft and private local session material; repeating it creates a separate case.

Case routes implement intake, follow-up, assessment, uploads, draft editing, PDF, share/revoke, consent audit and deletion. `/docs` contains OpenAPI contracts. Mutations require session cookies plus the `X-CSRF-Token` matching the readable `nyay_csrf` cookie, except session creation. Each case route checks owner access; lawyer routes check a separate role and expose only explicitly shared packet snapshots.

The 306-record old dataset is quarantined under `synthetic_demo/` and never used for legal retrieval. No real judgments are claimed. UK retrieval and unapproved external ingestion are disabled.

## Grounded-intelligence iteration (current)

The implementation now includes canonical parties/amounts/remedy provenance, natural Gemini follow-ups, saved conversation/corrections, contextual dashboard, 16 original bilingual fictional scenarios, six document templates, structured document findings and local Tesseract OCR for synthetic PNG/JPEG images. Python Pillow is explicitly pinned; native Tesseract (`tesseract-ocr`, optional `tesseract-ocr-hin`) is required for OCR. If absent, image extraction fails visibly; PDF/TXT still work.

The additive schema-v2 migration adds per-session demo AI budgets. Existing case JSON is read with safe defaults; full corrected narratives and original labelled dialogue remain stored. AI consent can be changed independently of deleting the case. The local model budget is 20 AI-context mutations/hour/session and does not describe account/provider quota. Consent withdrawal and deletion are never charged.

Actual account validation found the saved generation model unavailable to this account. The paginated catalogue and an actual embedding call now validate the saved embedding identifier. Ordinary startup selects and reports a successfully probed generation fallback; explicit overrides below were also exercised. Saved environment variables remain unchanged:

```bash
.venv/bin/python -m scripts.run_demo --port 8011
.venv/bin/python -m scripts.validate_live --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/live-browser.cjs
```

Use the actual current model-list and generation checks on your account before selecting models. Model listing alone did not establish generation availability here. Read [live validation](docs/GEMINI_LIVE_VALIDATION.md) for HTTP outcomes, current pricing/terms-access limits and quota caveats.

**Legal source gate remains open:** India Code migrated to `indiacode.gov.in`; the former PDF URL is invalid HTML. New domain grants were saved to the draft but not applied or published. No authentic statute has been approved. The new [offline importer](docs/LEGAL_SOURCE_MANIFEST.md) accepts only a reviewer-attested official artifact with independently established provenance, recorded checksum, rights/version metadata and exact passages. It never treats a local PDF as self-authenticating. Source-grounded legal conclusions remain withheld until these requirements are met.
## Current unseen-problem validation

Dynamic Gemini scope and multi-issue extraction now precede keyword fallback. Each issue/entity references exact narrative segment IDs; the backend creates provenance from original text, not model summaries. Each issue contributes research terms and case-specific evidence suggestions. Evidence uploads preserve novel issue understanding across refresh, documents and handoff.

Ordinary startup (`python -m scripts.run_demo --port 8011`) verifies actual account/model access with synthetic probes, reports fallback decisions and quota cooldown in `/api/health`, and does not rewrite saved variables. Catalogue pagination now recognises later-page embedding models. Model flags remain optional explicit overrides.

The latest continuation adds a complete per-family issue review and a separate fresh thirty-case cohort: **26/30 strict passes and 17/30 exact label sets on first exposure**. After general rubric/resilience fixes, replaying that same cohort produced **28/30 strict passes and 22/30 exact label sets**; that replay is not another unseen score. An unsupported refund inference and a provider timeout remain strict failures, with additional tags still needing review. The full suite now passes **140 tests**, including the offline-review workflow. Read the [continuation report](docs/LEGAL_INTELLIGENCE_CONTINUATION.md) and full per-case outputs. The [earlier evaluation](docs/UNSEEN_EVALUATION.md) is preserved as historical evidence.

**The legal Definition of Done is not met:** no authentic legal passage has cleared source/rights/version review. New source domains are already in the draft but not applied; reachable NCH/NALSA portal policies require prior reproduction permission. No source-grounded legal opinion or independent applicability validation is claimed. See [source manifest](docs/LEGAL_SOURCE_MANIFEST.md) and the unsent [permission-request draft](docs/SOURCE_REUSE_REQUEST.md).

## Adding verified law later

The [offline review workflow](docs/OFFLINE_INGESTION.md) now supports private PDF staging, nonmutating validation and explicit atomic batch admission into the existing source provider. All candidates begin pending. Provenance, current version, appropriate reuse rights and the pipeline’s actual storage/search/AI/export uses require recorded review before admission. No RAG rebuild is needed. The corpus remains empty; project PDFs and invalid HTML are not authority. [Actual offline tests](docs/OFFLINE_INGESTION_TEST_REPORT.md): 140 passed, original browser passed, pending CLI check/import correctly blocked with the real registry unchanged.
