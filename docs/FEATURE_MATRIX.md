# Final feature matrix — grounded-intelligence iteration

`WORKING — LIVE VERIFIED` means an actual external service succeeded. `WORKING — LOCAL VERIFIED` means real local behavior passed; mocked provider tests do not upgrade that label.

| Capability | Final status | Evidence / boundary |
|---|---|---|
| Gemini model list, minimal JSON generation, structured intake and multi-turn follow-up | WORKING — LIVE VERIFIED | Actual HTTP success using explicitly selected listed stable gemini-3.1-flash-lite; browser → API → Gemini exercised |
| Gemini embeddings | WORKING — LIVE VERIFIED | Actual configured gemini-embedding-2 response with 3072 dimensions; gemini-embedding-001 was also exercised |
| Default saved model settings | WORKING — LIVE VERIFIED | Startup detects configured generation rejection and probes/reports the audited fallback. Configured embeddings are verified after catalogue pagination; saved bindings remain unchanged |
| Persistent private guest cases, consent, owner/role/CSRF controls | WORKING — LOCAL VERIFIED | Original controls preserved; backend persistence, cross-user denial, expiry/deletion tests |
| Canonical entities, facts, timeline, conversation and correction | WORKING — LOCAL VERIFIED | Provenance-checked entities, full corrected narrative, persistent turns, date basis/timezone, context PATCH and language persistence |
| Natural AI conversation | WORKING — LIVE VERIFIED | Real supportive contextual responses and updated questions; no fixed response substituted as live AI |
| Contextual case workspace | WORKING — LOCAL VERIFIED | Case ribbon, parties/amount/remedy panel, issues, gaps, sources, readiness and document actions update together |
| Verified Indian legal corpus | BLOCKED — EXTERNAL DEPENDENCY | Zero approved passages; official migration/domain access, authenticity/rights/version review still needed |
| Online/offline ingestion and section-aware candidate preparation | WORKING — LOCAL VERIFIED | Official-host restrictions; provenance/checksum/rights attestation; exact-text checks; no automatic approval of local files |
| Hybrid retrieval over genuine statutes | BLOCKED — EXTERNAL DEPENDENCY | FTS5/semantic fusion path exists and fixture tests pass; actual embeddings succeed, but authentic source corpus is absent |
| Conditional legal reasoning + separate support evaluator | PARTIAL | Structured claims, exact artifact/source mapping, fact provenance, outcome-guarantee rejection, independent AI verdicts; authentic-source live run and qualified human review not done |
| Personalised fictional stories | WORKING — LOCAL VERIFIED | 16 original bilingual scenarios selected by facts/category; case-specific similarity/difference framework and relevant-source IDs when genuinely available |
| Gemini story comparison grounded in law | PARTIAL | Integrated into reasoning/support path; no authentic-law live comparison can yet be accepted |
| Authentic precedent comparison | NOT IMPLEMENTED | UI/provider/data contracts present and disabled; no authorised independently validated judgments or fabricated cases |
| Evidence PDFs/TXT/images and OCR | WORKING — LOCAL VERIFIED | Real local Tesseract PNG test, bounded decoding/timeouts, date/amount/reference extraction and document IDs; OCR can misread, no authenticity guarantee |
| Evidence relevance/contradiction assistance | PARTIAL | Provenance, literal date discrepancies, suspicious instruction warnings and token-overlap relevance; not a comprehensive evidence evaluator |
| Explainable readiness | WORKING — LOCAL VERIFIED | Separate factual/evidence/reconciliation/source/review findings; four file categories alone cannot create Strong; no winning probabilities |
| Six editable preparation templates, text and Unicode PDF export | WORKING — LOCAL VERIFIED | Seller letter, refund/replacement request, grievance summary, chronology, inventory, lawyer brief; missing fields explicit, not commission pleadings |
| Case packet and signed owner-bound downloads | WORKING — LOCAL VERIFIED | Facts, evidence, analysis when accepted, conditions, references/abstention, drafts and limits; external PDF resource fetch disabled |
| Demo lawyer sharing, receipt, revocation and audit | WORKING — LOCAL VERIFIED | Browser test with independent authenticated recipient; packet snapshots only, no verified advocate/representation claim |
| Official assistance links | PARTIAL | NCH portal inspected live; links distinguish preparation/filing. Current e-Jagriti procedure, eligibility/deadline advice not verified |
| English/Hindi and responsive UI | WORKING — LOCAL VERIFIED | Persistent case language, labelled controls, 1440/768/390px checks and Hindi PDF; no full WCAG certification |
| Service failure and demo AI budget | WORKING — LOCAL VERIFIED | Controlled timeout/429/Retry-After/embedding-fallback tests; 20 AI-context mutations/hour/session; consent withdrawal/deletion remain available |
| Protected local deployment | WORKING — LOCAL VERIFIED | Loopback-only demo on port 8011 with startup model probes and visible selection; no public deployment |
| Real-user beta | NOT IMPLEMENTED | Explicitly gated pending privacy, provider contracts, strong auth, legal/security review, storage/backup controls and abuse protection |
| UK legal provider | NOT IMPLEMENTED | Disabled pending licensing and jurisdiction review |

The requested complete grounded-law acceptance journey remains **PARTIAL**. No authentic legal passage or professional legal interpretation has been invented to turn this table green. See LEGAL_SOURCE_MANIFEST.md, GEMINI_LIVE_VALIDATION.md and TEST_REPORT.md for evidence.

## Current generalisation changes (supersedes earlier gaps where noted)

| Capability | Current status | Evidence / remaining limit |
|---|---|---|
| Dynamic scope and multiple factual issues | WORKING — LIVE VERIFIED | Keyword fallback no longer vetoes unseen narratives before Gemini. Thirty new cases have accepted dynamic/provenance/evidence outputs; seven strict secondary-category misses remain |
| Exact factual provenance | WORKING — LOCAL VERIFIED | Provider selects constrained narrative IDs; server resolves original text. Summaries/inferred remedies cannot become user facts |
| Per-issue retrieval and evidence requirements | PARTIAL | Research is decomposed and contextual evidence suggestions replace universal warranty checklists; genuine-law retrieval is still blocked |
| Evidence refresh preserves novel context | WORKING — LIVE VERIFIED | Independent unseen subscription browser case retained issue state through upload, draft/PDF, refresh, handoff and deletion |
| Ordinary-startup model configuration | WORKING — LIVE VERIFIED | Actual synthetic probes select/report working generation fallback and verify configured embeddings; no saved-variable rewrite |
| Provider failure / cooldown | WORKING — LOCAL VERIFIED | Actual 429/503 observations and controlled retry/cooldown regression tests; quotas are an external limit |
| Reviewed Indian law corpus / independent legal applicability | BLOCKED — EXTERNAL DEPENDENCY | No cleared authentic passages; migrated-source grant unapplied; reachable NCH/NALSA portal reuse requires prior permission |

The overall requested legal-assistant Definition of Done remains **NOT MET**. Neither 30 accepted triage responses nor a 23/30 strict issue-coverage score establishes legal correctness or guarantees arbitrary unseen-problem handling.
