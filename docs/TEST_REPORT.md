Latest continuation from `1bbf9cb`: [actual results and remaining legal-source blockers](LEGAL_INTELLIGENCE_CONTINUATION.md). Current suite: **107 passed**. Fresh cohort: **26/30 strict, 17/30 exact**; final same-cohort replay: **28/30 strict, 22/30 exact**. The earlier iteration below is preserved, not replaced or combined into a higher score.

# Current test report — 2026-11-14

Branch: `feature/generalized-consumer-analysis`, based on remote main `1274bee` after PR #2. Implementation milestone: `25de2d0`. All identities/documents/narratives used for provider calls were synthetic.

## Commands and observed results

| Check | Actual outcome |
|---|---|
| `/workspace/nyay-consumer-venv/bin/python -m pytest -q` | **99 passed**, one upstream Starlette/AnyIO deprecation warning, no skips in this environment |
| Live 30-case unseen evaluation | Full rounds 9/30 then 20/30 strict passes; targeted 3/10 recheck. Latest recorded outputs: **23/30 strict passes**, **30/30 dynamic understanding/provenance/evidence-suggestion checks** |
| `node tests/generalized-browser.cjs` against port 8011 | PASS LIVE for a separate new subscription narrative through issue understanding, upload, documents/PDF, demo recipient acknowledgment, persistence, revocation and deletion; law segment blocked |
| `node tests/browser.cjs` | **PASS LOCAL**: full original workflow, separate demo recipient, three viewport widths and Hindi persistence rerun on the upgraded service |
| Ordinary startup `python -m scripts.run_demo --port 8011` | Actual configured-model probe detected generation HTTP 404, selected and verified `gemini-3.1-flash-lite`; configured `gemini-embedding-2` appeared on a later catalogue page and actually returned 3072-dimensional vectors. Decisions are visible, not silent environment rewrites |
| Strict provider JSON-schema probe | Raw complex Pydantic schema returned HTTP 400; compact inlined decoder schema succeeded. Full Pydantic/provenance limits still run after generation |
| Dependency/hash, JS syntax, Python formatting and Git whitespace checks | Hash-pinned dependency installation preserved; `uv pip check` reports 34 compatible packages; `node --check`, `ruff format --check` and `git diff --check` passed |

## What the automated suite establishes

Existing security and case lifecycle regressions are preserved: private sessions, owner/role access, CSRF/cross-origin checks, consent, TTL/deletion, safe PDF/TXT/PNG uploads and OCR, protected/signed downloads, six editable templates, Unicode PDF, audit, handoff snapshots and revocation.

New tests cover the actual generalisation failure modes: novel narratives reach dynamic understanding before keyword rejection; incidental police references do not discard consumer aspects; multi-issue research is decomposed; issue/entity IDs map to original narrative text; paraphrased summaries and inferred remedies are not promoted into user facts; evidence uploads preserve novel issue context through draft/PDF/read operations; provider schemas are compact but backend validation stays strict; known permission-required portals cannot be approved merely by writing “public”; startup model fallback is actually probed/reported; quota cooldown avoids repeated calls; factual gaps remain visible when the model emits no direct question; and subscription stories recognise the new issue family.

## Live versus mocked versus blocked

**Actual external:** model catalogue, generation, English/Hindi dynamic intake, thirty new-case attempts with targeted rechecks, real embeddings, a new live browser narrative, and provider 400/404/429/503 observations. No success is inferred from model listing alone.

**Actual local:** SQLite persistence, canonical corrected context, narrative IDs, OCR, exports, source artifact/date/rights validation mechanics, owner/CSRF controls and demonstration recipient workflow.

**Mock/fixture-only:** ranking over approved-looking synthetic passages, claim-support acceptance/rejection, artificial timeouts and deterministic catalogue/fallback branches. These are not authentic law or evidence of legal correctness.

**Still blocked:** a genuinely approved statutory/rules/guidance corpus, live real-source hybrid retrieval, source-grounded legal explanations and independent assessment of their substantive applicability. The corpus remains empty. NCH and NALSA policies require prior reproduction permission. Migrated India Code is excluded by the current running policy despite its saved draft grant. No independent qualified legal reviewer has approved interpretations.

Detailed, unaltered expectation/results mapping: [UNSEEN_EVALUATION.md](UNSEEN_EVALUATION.md) and [evaluation/unseen-live-results.json](evaluation/unseen-live-results.json). The seven strict coverage failures remain open. AI agreement is not scored as legal truth.

## Release/deployment conclusion

The scoped fictional-data preparation workflow is usable, and the novel-input routing/configuration bugs were fixed. The full requested Definition of Done is **NOT MET**: authentic legal material and independent legal validation remain external prerequisites, and seven expected secondary issue labels were missed in the benchmark. No public deployment or environment publication occurred. The service is loopback-only on port 8011; real-user processing remains gated. No claim of arbitrary unseen-problem accuracy, verified advocates or official government filing is made.

## Final resilience check

A final restart received an actual transient HTTP 503 during the generation probe. The app retained local operation and did not claim live availability. A new authenticated/CSRF-protected, rate-limited `POST /api/provider/recheck` and visible “Retry AI connection” action allow explicit recovery without restarting. It preserves an unsaved intake and respects provider cooldown; tests cover authentication/CSRF and a three-probe/five-minute budget. The failed live browser attempt is retained as provider unavailability, not counted as passing. A subsequent fresh live browser journey passed, including story, document and handoff steps. The authenticated provider-recheck endpoint was also exercised against the actual API: HTTP 200, generation and embedding probes both verified. Historical success cannot mask a current failed generation or model-catalogue probe; explicit regression tests cover both. A final ordinary restart again verified generation and embedding access on the latest code.

A subsequent live intake attempt also failed safely with the provider’s combined network/response-envelope diagnostic; the original failure was not sufficiently specific to determine its cause. Transport-class versus malformed-response reporting was then separated without exposing raw errors or response bodies. After that diagnostic change, the final complete unseen browser run passed on the latest service. This does not erase the intervening failed attempt or establish provider uptime. The final unit suite remained 99 passed; formatting/syntax/whitespace checks passed, all three raw evaluation-report hashes matched their committed manifest, and scanning the 79 tracked/new delivery files found no injected-secret values or credential-pattern matches.
