Latest continuation from `1bbf9cb`: [actual results and remaining legal-source blockers](LEGAL_INTELLIGENCE_CONTINUATION.md). Current suite: **107 passed**. Fresh cohort: **26/30 strict, 17/30 exact**; final same-cohort replay: **28/30 strict, 22/30 exact**. The earlier iteration below is preserved, not replaced or combined into a higher score.

# Unseen consumer-dispute evaluation — 2026-11-14

This is an actual external-provider evaluation, not 30 mocked responses or a legal-accuracy claim. The frozen narratives and expectations are in `tests/evaluation/unseen_consumer_cases.json`. They are disjoint from the earlier 31 demonstration narratives, cover the six requested dispute families, include English/Hindi and several mixed issues, and contain no real confidential identities.

## Method

The application receives each narrative, jurisdiction, language and explicit fictional-data/AI consent. **Expected issue labels are not sent to Gemini.** The backend resolves selected factual segment IDs to original text, validates entities, generates per-issue research/evidence needs and applies source gates. The evaluation compares outputs against predeclared issue-family expectations and deterministic provenance checks.

The full v1 round exposed genuine defects: paraphrased fact summaries rejected an otherwise useful response; some issues omitted evidence suggestions; a remedy could be inferred without a source excerpt. Fixes introduced exact segment selection, a compact provider-constrained decoder schema plus full backend validation, mandatory per-issue evidence suggestions and omission of unsupported remedies. A real HTTP 429 free-tier limit and a 503 were recorded; a bounded cooldown now prevents immediate repeated calls. A provider catalogue is paginated rather than assuming the first page is complete.

## Actual outcomes (no expectations relabelled)

| Run | Attempted | Passed every strict check |
|---|---:|---:|
| First full run, v1 | 30 | 9 |
| Revised full run, v2 | 30 | 20 |
| Targeted post-fix v3 recheck of v2's ten failures | 10 | 3 |
| Latest recorded attempt per case (v2 + v3) | **30** | **23** |

The combined latest set is **not a single uniformly rerun final batch**. Its exact round provenance and field-level checks are committed in `docs/evaluation/unseen-live-results.json`. Original raw reports remain under ignored `runtime/`; their SHA-256 hashes are retained in the committed report.

Latest recorded results:

- 30/30 accepted dynamic consumer understanding.
- 30/30 issue quotations resolve to the actual supplied narrative.
- 30/30 contain case-specific evidence suggestions.
- 30 distinct evidence-suggestion sets; 16 distinct direct follow-up sets. Empty direct model questions were a remaining UX gap; the final implementation now exposes the model's identified factual gaps as explicitly phrased clarification prompts, with a regression test. The benchmark is not silently credited with that subsequent change.
- **23/30 pass full expected issue-family coverage.** Seven secondary-tag misses remain: D05, M05, R03, R05, V05, W02, W03. For example, a repeated-fault/repair dispute was classified as warranty without a separate defective-product tag. These are recorded as failures, even where the issue title mentions the associated facts.
- **0 approved legal passages. Legal correctness and statutory applicability were NOT assessed.** No source-grounded legal acceptance gate is passed by this score.

This demonstrates useful adaptation to new facts, not guaranteed performance for every unseen problem. Expected issue families are factual triage targets, not an independently qualified legal gold standard. Further generalisation evaluation and expert adjudication of issue coverage remain necessary.

## Reproduce

```bash
.venv/bin/python -m scripts.evaluate_unseen --live --workers 1 --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001 --output runtime/unseen-recheck.json
# Targeted debugging without overwriting previous evidence:
.venv/bin/python -m scripts.evaluate_unseen --live --workers 1 --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001 --only R03,D05 --output runtime/unseen-targeted.json
```

`--live` explicitly authorises synthetic provider calls. Sequential runs pause between cases and stop that run when quota cooldown is reached. Do not replay repeatedly against an exhausted quota or claim unattempted cases passed. A nonzero exit reports failures; it is not hidden by a pipe.

## Browser verification

`tests/generalized-browser.cjs` enters a separate, newly written monthly-gardening-plan dispute **without selecting a sample button**. It checks live dynamic subscription understanding, preserved state after upload, contextual dashboard, fictional story, editable request/PDF, separate demo lawyer acknowledgment, refresh, revocation and deletion. The authentic-law segment is explicitly reported blocked. This is a working case-preparation demonstration, not a completed Indian legal-reasoning release.
