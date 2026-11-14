# Legal-intelligence continuation from 1bbf9cb — 2026-11-14

The full legal-assistant Definition of Done is **NOT MET**. Approved authentic legal passages remain **0**, so authentic-source hybrid retrieval, substantive grounded legal reasoning and independent legal-applicability validation are blocked. No fictional or remembered legal text was substituted.

## Implemented

Gemini now makes a structured present/unclear/not-stated review of all eight factual issue families. Every positive finding must select actual narrative segments and include case-specific evidence needs and research terms. The server materialises all supported facets, instead of letting one broad issue title absorb other categories. Incomplete facets are withheld without erasing independently grounded concerns. Missing families, unknown segment IDs and conflicting scope fail closed. The review persists with the case; old saved cases remain readable with default fields.

A general rubric distinguishes a physical fault, an express-cover dispute, failure of a purchased service, treatment of requested money back, pre-transaction representations, recurring billing and explicit digital transaction context. Online-shopping is a channel facet, not wrongdoing or proof of standing. The prompt contains no benchmark narratives, case IDs or expected-label answers. Per-issue retrieval now covers up to eight facets while keeping the source pack bounded at eight.

## Review of the original seven failures

The original fixture and historical scores were preserved. The factual-label audit is [seven-expectation-review.json](evaluation/seven-expectation-review.json), and its separate reviewed fixture is `tests/evaluation/revalidated_seven_cases.json`.

D05, R03, R05, W02 and W03 support multiple distinct factual research questions. M05 supports pricing-disclosure research and an explicit digital transaction facet, while standing/merits remain uncertain. **V05 does not state a refund request or refusal**: its extra expected refund label was unjustified. Removing it from a separately named fixture is an expectation correction, not evidence that the model learned to detect a missing issue. This audit is coding-assistant factual review, not an independent qualified legal opinion.

The first new seven-case run scored 5/7 against unchanged expectations: D05 was unavailable (actual 503), while V05 omitted the unjustified refund label. A subsequent targeted run on the final implementation returned both D05's fault/cover concerns and V05's service concern (2/2 against explicitly reviewed expectations). Other extra labels remain visible; these mixed attempts are not presented as one clean final seven-case batch.

## Fresh evaluation and final replay

Thirty new fictional narratives were frozen in `tests/evaluation/fresh_multi_issue_cases.json` before calls; they are disjoint from the previous cohort, contain four Hindi cases, at least twenty multi-issue cases, and predeclared forbidden labels to detect unsupported inference. Expected labels are never passed to Gemini. No real confidential data was transmitted.

| Run | Attempted | Strict preparation/triage checks | Exact expected label set |
|---|---:|---:|---:|
| v5 first exposure — fresh | 30 | 26/30 | 17/30 |
| v6 same-cohort final replay — regression | 30 | 28/30 | 22/30 |

The first exposure had an actual ReadTimeout, an HTTP 503, and two incomplete-facet responses that originally discarded the entire extraction. Partial-response handling fixes that failure mode. The rubric was clarified to avoid inferring digital ordering from delivery/digital content and advertising from mere contractual non-performance. The final replay is **not another fresh unseen score**. Results are not combined or cherry-picked into one higher score.

Final strict failures: F13 (a refund-refusal label was inferred without a stated refund request/refusal) and F27 (actual ReadTimeout). Final cases with additional tags: F06, F10, F13, F22, F24, F26, F30. A strict pass establishes expected coverage plus the predeclared negative controls, **not precision of every added label**. Exact-set results expose that difference. For example, the first run inferred online shopping from some facts that did not state an ordering channel. The final replay still needs per-case factual/expert adjudication of extra tags; no claim of arbitrary unseen-problem accuracy is made.

Full input-level outputs, questions, provenance and category-review reasons are committed in [evaluation](evaluation/round2-summary.json), with hashes. The reports' `legal_validation` is explicitly NOT ASSESSED; passing triage never counts as a legal-accuracy pass.

## Actual validation

- `/workspace/nyay-consumer-venv/bin/python -m pytest -q`: **107 passed**, one upstream Starlette/AnyIO deprecation warning, no skips.
- `NYAY_TEST_URL=http://127.0.0.1:8011 node tests/browser.cjs`: PASS, preserving original local lifecycle, evidence/PDF, separate demo recipient, revocation, responsive widths and Hindi persistence.
- `NYAY_TEST_URL=http://127.0.0.1:8011 node tests/generalized-browser.cjs`: initial actual HTTP 503 failure retained; subsequent PASS on the latest implementation. A separately entered new membership dispute contains advertising, recurring-debit and explicit payment-reversal concerns. It traversed real Gemini → evidence upload → contextual story → editable document → PDF → consent-based demo-lawyer receipt → refresh → revocation → deletion.
- `NYAY_TEST_URL=http://127.0.0.1:8011 node tests/generalized-browser.cjs --require-grounded`: **BLOCKED, exit 2** before claiming a legal analysis. The strict mode requires genuine loaded sources, accepted legal claims, artifact hashes, source/quote/fact mappings and actual frontend source links, then the same preparation/handoff workflow. Its law-enabled branch has **not** been exercised against authentic law.
- Actual startup probes again verified audited generation fallback and configured embeddings. Provider outages remain an external reliability limit; no test failure was silently counted as success.
- Final Python/JavaScript formatting, JS syntax and Git whitespace checks passed; dependency check found 34 compatible installed packages. Committed raw-report and frozen-fixture hashes matched. Scanning 89 delivery files found no injected credential values or credential-pattern matches.

## Legal source and independent-review blockers

The managed environment still reports applied network policy revision 1, excluding migrated India Code/Department domains. India Code's reachable old homepage only announces migration; the Act candidate returns HTML, not PDF. Both legacy official record/search requests timed out. The old Department Act page returned 503; e-Jagriti returned 403. NCH guidance is reachable, but the inspected portal disclaimer requires prior reproduction permission. Existing NALSA permission conditions were not presumed waived.

The recovered local `cpa2019.pdf` is invalid HTML, and no authentic official artifact plus provenance/rights documentation was supplied in the workspace. The existing offline importer was therefore **not falsely attested or used to approve it**. Source-attempt evidence and checksums are in `knowledge/source_access_attempts_round2.json`. No statute version, amendment completeness or reuse basis was established merely from a plausible URL or title.

To unblock: apply the already-saved migrated official-domain grants through the environment controls, or supply an independently acquired authentic official PDF/HTML with provenance, version/commencement/amendment review and documented reuse basis. Use the existing review-controlled importer only after those checks. Source access alone does not establish rights or legal applicability. Current rules/notifications and qualified independent legal assessment remain required.

No complete authentic-source-grounded analysis was demonstrated. Independent legal accuracy/citation-applicability review was **NOT PERFORMED**, and no qualified reviewer is implied. The app continues to withhold unsupported law, citations and deadlines.

## Reproduce and deployment

```bash
/workspace/nyay-consumer-venv/bin/python -m scripts.run_demo --port 8011
# Fresh fixture replay; subsequent executions are regressions, not first exposure:
/workspace/nyay-consumer-venv/bin/python -m scripts.evaluate_unseen --live --workers 1 --model gemini-3.1-flash-lite --cases tests/evaluation/fresh_multi_issue_cases.json --output runtime/fresh-replay.json
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/generalized-browser.cjs
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/generalized-browser.cjs --require-grounded
```

The service remains loopback-only on port 8011, fictional-data-only, with existing consent, owner/role access, CSRF, upload, document, retention/deletion and handoff safeguards preserved. No environment publication, public deployment, real advocate verification or official government filing occurred.
