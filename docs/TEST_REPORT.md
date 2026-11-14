# Test report — grounded-intelligence iteration, 2026-11-14

Baseline: `0f3f93f`. Dedicated branch: `feature/grounded-consumer-intelligence`. First tested milestone: `35be10f`. This report supersedes the previous local-only report; prior 61-test functionality has been retained and extended. Python 3.12.14, FastAPI 0.115.12, Pydantic 2.11.4, SQLite FTS5, WeasyPrint, system Chromium/Playwright and local Tesseract 5.

## Actual executions

| Command / check | Actual result |
|---|---|
| `/workspace/nyay-consumer-venv/bin/python -m pytest -q` | **81 passed**, one upstream Starlette/AnyIO deprecation warning; no skipped tests in this environment |
| `NYAY_TEST_URL=http://127.0.0.1:8011 node tests/browser.cjs` | **PASS LOCAL**: full journey, separate authenticated demo-lawyer handoff, revocation/deletion, 1440/768/390px layouts and persistent Hindi switch, rechecked on the upgraded server |
| `NYAY_TEST_URL=http://127.0.0.1:8011 node tests/live-browser.cjs` | **PASS LIVE** real Gemini intake + follow-up via frontend/authenticated API; canonical entity/history/timeline, lawyer-brief generation and deletion. Official-law segment explicitly **BLOCKED** |
| `python -m scripts.validate_live --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001` | Real model list, minimal generation, structured intake, multi-turn factual follow-up and real embeddings **PASS**; actual-law hybrid retrieval/reasoning **BLOCKED**, not replaced by fixtures |
| Local OCR image-upload test | **PASS**; actual synthetic invoice PNG decoded by Tesseract; amount, order reference, date and document provenance verified |
| Individual six-template TXT/PDF API tests | **PASS**, including edits/persistence and Unicode PDFs |
| `node --check app.js`, `git diff --check` | Passed during implementation; final checks run before commit |

The suite retains **31 synthetic evaluation narratives**, including Hindi/English, incomplete/ambiguous facts, unsupported jurisdiction/domain, identifiers, prompt injection and fabricated authority. Added checks cover canonical corrections/history/language, trusted-reference relative dates, missing facts, non-category-count readiness, six independently persisted templates, authentic-provenance offline-import requirements, section-aware **unapproved** candidates, story relevance/labels, unsupported proposition rejection, explicit beta gate, AI context budget, consent withdrawal under exhaustion, model timeout/429 Retry-After and embedding outage lexical fallback.

One original readiness expectation intentionally changed: four self-classified file uploads with missing factual/source coverage now remain Partial. The lifecycle test still checks all persistence, draft editing, PDF, sharing, lawyer isolation/receipt, revocation, audit and cascading deletion assertions. A browser assertion was updated to wait for the newly persistent asynchronous language update rather than expecting an immediate label-only change.

## Mocked versus actual evidence

- **Actual external:** authenticated model list, successful stable-model generation, structured English/Hindi intake, multi-turn updates, real embedding requests and frontend → backend → Gemini calls. Detailed account/model results are in GEMINI_LIVE_VALIDATION.md.
- **Actual local:** database/session/security, PDF/TXT/image extraction, Tesseract OCR, document templates/export, signed downloads, lawyer snapshot workflow, context/corrections, original scenario retrieval and UI/browser interactions.
- **Synthetic fixtures/mocks:** lexical/hybrid ranking contract, statutory-source validation, support evaluator acceptance/rejection, malformed/counterfeit source records, timeout/429 and embedding failures. Test-only source passages are not real law and are never persisted into the production corpus.
- **Not run / blocked:** legal retrieval and claim entailment over genuine approved legislation; current legal applicability review; authentic judgment comparison; live procedural filing; public or real-user deployment. No qualified reviewer has assessed new statutory interpretations.

## Release assessment

No approved statute, authentic judgment, statutory deadline, guaranteed remedy, advocate verification, winning percentage or government submission has been fabricated. There are **zero approved legal passages**. Source cards/analysis visibly abstain until real artifact/provenance/rights/version requirements can be met. Real embedding generation alone is not reported as a live hybrid legal RAG system.

Current India Code legacy content is invalid HTML or timeouts; the website announces migration to a domain missing from the running allowlist. NCH pages are reachable but their copyrighted content is not bulk indexed. New domain additions were saved to the environment draft without publication. Genuine official documents can alternatively be supplied through the reviewer-attested offline importer.

## Security / operational limits

Demonstration-only processing is explicitly gated. Native OCR is bounded but can misread; only English (`eng`) and orientation (`osd`) Tesseract packs are installed, so Hindi image OCR is not claimed. Text PDFs and bilingual intake/PDF rendering remain supported. No file authenticity verification or production malware sandbox is claimed. The separate AI support evaluator is not an independent legal professional. Guest-cookie recovery, strong beta identity, production-global abuse controls, encryption/backup erasure and provider/privacy/legal contracts still need review. No public service was deployed.

## Final artifact inspection

Generated a real three-page Hindi/English packet with seller representation and lawyer brief. Opened it with pypdf, rasterised its first page with pdftoppm and visually inspected the rendering; Devanagari text and explicit no-law/no-filing disclosures render correctly. The actual live browser dashboard screenshot was also visually inspected. Artifacts remain private ignored runtime files. Some technical audit/readiness messages remain English; full translation and a full WCAG audit are not claimed.
