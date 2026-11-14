# NyaySaathi 2.0

An India-first **fictional-data consumer case-preparation demonstrator**, preserving NyaySaathi's existing purple/cream identity and navigation. One FastAPI service serves the existing vanilla frontend and persists cases in SQLite with FTS5.

**Current boundary:** local intake → facts/timeline → evidence → editable seller letter → PDF → consent-based demo lawyer inbox works. Verified legal reasoning is withheld until official passages pass manual source/rights review. Live Gemini is unverified and disabled without credentials, a supported configured model and terms review. This is not legal advice or an official filing service.

## Install and run

Python 3.11+ (tested on 3.12), Linux with Pango/Harfbuzz and DejaVu/Noto Devanagari fonts for PDF rendering. On Debian/Ubuntu these are supplied by `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz0b`, `fonts-dejavu-core`, `fonts-noto-core`. Use your environment's approved package installer if missing. No Node build or ML weight download is required.

```bash
cd /workspace/NYAYSAATHI-2.0
python -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
mkdir -p runtime/cache
export XDG_CACHE_HOME="$PWD/runtime/cache"
.venv/bin/python -m scripts.seed_demo
.venv/bin/python -m scripts.run_demo
```

The local demo runner binds port **8010** and reads the private, randomly generated lawyer password from `runtime/demo-lawyer-password`. It does not print the password. Use a local development browser to access the server. The server serves only `/`, `/style.css`, `/app.js` and API routes, never `.env`, the database or the synthetic dataset. Do not use a directory-wide static HTTP server.

For development with an explicitly configured environment:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010 --reload --no-access-log
```

`python main.py` also runs the integrated app on port 8000. No live process survives an environment snapshot. Use the existing checkout; tasks are already isolated and do not need a Git worktree unless explicitly requested.

## Configuration

See `.env.example` for names and non-secret defaults. Export variables with a service manager or shell; the backend does not automatically load `.env`. Never place secret values in JavaScript, source files, docs or chat.

- `GEMINI_API_KEY`: secure backend binding for `generativelanguage.googleapis.com`.
- `GEMINI_MODEL`: select a supported stable model after `python -m scripts.check_gemini`. No model name is guessed or hard-coded.
- `GEMINI_EMBEDDING_MODEL`: optional, verify model availability and permission first.
- `GEMINI_TERMS_REVIEWED=true`: operator has reviewed terms/pricing/account quotas; does not itself prove availability. Each session still requires separate AI opt-in. Sensitive-looking input is blocked from model transmission.
- `DEMO_LAWYER_PASSWORD`: private demonstration-account password, no default. The local demo runner can use the seeded private file instead.
- `NYAYSAATHI_RUNTIME`: private persistent directory (default `runtime/`). DB/file permissions restrict access; disk encryption and backups are deployment responsibilities.
- `COOKIE_SECURE=true` behind HTTPS. Leave false only for local HTTP.
- `SESSION_TTL_HOURS` (default 24, maximum 168), `RETENTION_DAYS` (default 7, maximum 30). Case data is also removed when its owning session expires. Cleanup occurs on startup and authenticated requests; schedule maintenance for idle installations if necessary.

Official-source and Gemini domains must be allowed by the environment policy. See [source review and rights](docs/SOURCES_AND_RIGHTS.md). A network/settings draft was saved; this does not apply or publish it. Current proxy requests to India Code fail with 403. No secret is requested in chat.

## Tests

```bash
.venv/bin/python -m pytest -q
# Optional browser test, using the environment's installed Playwright + Chromium:
NYAY_TEST_URL=http://127.0.0.1:8010 node tests/browser.cjs
```

For another machine, install Playwright using your normal approved tooling (`npm install --no-save --package-lock=false playwright`), set `CHROMIUM_PATH` if required, and supply `NYAY_LAWYER_PASSWORD_FILE` to the local private file for the browser handoff test. The script tests deletion only on a newly created fictional case. No external messages are sent.

[Actual test results](docs/TEST_REPORT.md) distinguish local, synthetic-fixture and blocked live checks. [Demo script](docs/DEMO_SCRIPT.md), [audit](docs/REPO_AUDIT.md), [feature matrix](docs/FEATURE_MATRIX.md), [deployment](docs/DEPLOYMENT.md).

## Data and API

`backend/schema.sql` is the idempotent version-1 migration, applied at startup. It stores sessions, cases, full redacted narratives, evidence BLOBs/text, audit records, handoff snapshots, expiring signed grants, FTS index and optional embedding cache. Runtime files are ignored by Git. `scripts.seed_demo` creates one fictional case/draft and private local session material; repeating it creates a separate case.

Case routes implement intake, follow-up, assessment, uploads, draft editing, PDF, share/revoke, consent audit and deletion. `/docs` contains OpenAPI contracts. Mutations require session cookies plus the `X-CSRF-Token` matching the readable `nyay_csrf` cookie, except session creation. Each case route checks owner access; lawyer routes check a separate role and expose only explicitly shared packet snapshots.

The 306-record old dataset is quarantined under `synthetic_demo/` and never used for legal retrieval. No real judgments are claimed. UK retrieval and unapproved external ingestion are disabled.
