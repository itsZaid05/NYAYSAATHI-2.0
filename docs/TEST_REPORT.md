# Test report — 2026-11-14

Target: NYAYSAATHI-2.0, branch `feature/india-consumer-workflow`. Python 3.12.14, FastAPI 0.115.12, Pydantic 2.11.4, SQLite FTS5, WeasyPrint 65.1; headless system Chromium through the environment's Playwright. All user identities/documents and source fixtures in tests are synthetic.

## Executed and passed

| Command / check | Actual result |
|---|---|
| `UV_CACHE_DIR=/workspace/.uv-cache uv pip install --python /workspace/nyay-consumer-venv/bin/python --require-hashes -r requirements.lock` | 34 packages checked; hash-locked install successful |
| `uv pip check --python /workspace/nyay-consumer-venv/bin/python` | All installed packages compatible |
| `/workspace/nyay-consumer-venv/bin/python -m pytest -q` | **61 passed**, one upstream Starlette/AnyIO deprecation warning, zero skips/xfails |
| `NYAY_TEST_URL=http://127.0.0.1:8010 node tests/browser.cjs` | Full local browser preparation workflow and separate authenticated demo-lawyer handoff passed, zero page errors |
| `node --check app.js` | Passed |
| `git diff --check` | Passed after correcting trailing whitespace |
| `python -m scripts.seed_demo` | Actual fictional case/draft persisted; private session/password files created with mode 0600; no secrets printed |
| Local `/api/health` | Database ready, `reviewed_sources=0`, `gemini_configured=false`, demo lawyer enabled with private local seed password |

The test suite includes **31** valid/ambiguous/incomplete/unsupported/sensitive English/Hindi consumer narratives. Other tests cover full case lifecycle, database persistence across app connections, separate role authentication, consent, cross-user denial, CSRF/cross-origin denial, expiry/deletion, streamed body/file limits, signed grant integrity/expiry/ownership, upload type/content checks, local extraction, date-discrepancy prompts, English/Hindi PDF output, snapshot sharing/revocation, source artifact/version/rights checks, stale/fake citation rejection, and model hallucination rejection.

Provider transport tests exercise the actual Gemini request/JSON-validation code through **mock HTTP transport**. Hybrid retrieval is tested with **mock embeddings and explicitly synthetic test passages**. These tests establish adapter/control behavior; they do not validate a live model, authentic statutory content, legal relevance or legal correctness.

Browser test: consented intake, follow-up, four real backend evidence uploads, readiness transition, seller letter creation/edit/save, actual PDF download, reload persistence, labelled story, source abstention, explicit sharing, a second authenticated lawyer cookie context, shared snapshot download, demo acknowledgment, revocation, deletion, Hindi switch and no horizontal overflow at 1440/768/390 px. Mobile Hindi screenshot was visually inspected (`runtime/mobile-hi.png`, ignored local artifact). Native labelled controls, focus outlines, live status and keyboard-accessible navigation are present; this is not a full WCAG audit.

## External checks blocked / not run

- **Official law access:** candidate India Code PDF request returned proxy CONNECT **403**. No official text was obtained, no source was manually reviewed, and zero genuine source links were validated end to end. A network-domain draft was saved; it has not been confirmed applied or published.
- **Gemini:** `python -m scripts.check_gemini` exited 1 with “Gemini key is not configured”. No live extraction/reasoning/embedding, model availability, actual pricing or account quota verified. No secret value was requested in chat.
- **Full source-grounded laptop journey:** NOT PASSED / not run with real legal sources and Gemini. Local preparation and handoff passed separately. Actual-law applicability must be independently reviewed after access/source preparation.
- Public deployment, professional lawyer services, government filing, OCR, actual judgments, UK licensing/provider and real confidential-data processing are unsupported/unrun, not successful integrations.

## Release gate assessment

- No system-generated fabricated legal citations observed. Current production source corpus is empty and legal outputs abstain. Tests also reject invented references using synthetic fixtures. This does not validate legal analysis over an authentic corpus.
- No generated litigation success percentages, fictional judgments represented as real, verified-advocate claims or government-filing claims in the active UI.
- Only synthetic material processed in tests; no real sensitive data sent to Gemini. Real-data safety cannot be guaranteed by regex screening or consent alone.
- **Full requested release gate remains OPEN:** official reviewed legal knowledge and live Gemini end-to-end validation are required before claiming the full legal-intelligence platform is ready.

## Remaining engineering limits
Conservative rules support issue classification and ISO-date reconstruction; ambiguous dates need clarification. Readiness checks document-category presence and missing fields, not document quality. No authentic precedent comparison, OCR or autonomous official ingestion. SQLite/private guest sessions are suitable for the scoped local demonstration; production identity recovery, global service abuse protection, isolated document parsing, privacy/security review, backup deletion and legal/provider contracts need separate work.

## Environment recheck after configuration update request

Checked 2026-11-14T05:28:39+05:30 (India time).

- Re-ran the suite: **61 passed**, one upstream deprecation warning; browser journey including separate authenticated lawyer context, download, acknowledgment, revocation and deletion passed again.
- All 34 installed packages are compatible. JavaScript syntax and Git whitespace checks passed. SQLite `PRAGMA quick_check` returned `ok`, schema version 1, private database/password/session files have mode 0600.
- The existing local demo service remains running on port 8010. Health reports database OK, demo-lawyer enabled, zero reviewed sources and Gemini not configured.
- Runtime status still reports applied/observed spec revision **1**, enforced package-manager-only network policy, and no secret or runtime-variable bindings. The saved draft is revision **4**: required domains are listed, but GEMINI_API_KEY has `has_saved_binding=false`; model/terms variables remain pending requirements. These are observations about this attached machine, not a claim about values entered elsewhere.
- Fresh TLS-verified requests to India Code, Gemini models, National Consumer Helpline and e-Jagriti each failed at proxy CONNECT with HTTP 403. A fresh Gemini availability command exited 1 because no key is configured. Process-variable checks and local configuration checks inspected only names/presence; no secret values were printed.
- No duplicate secret requirement or replacement draft was created. Applying the relevant saved settings and securely binding the credential are still prerequisites to live model/source validation.
