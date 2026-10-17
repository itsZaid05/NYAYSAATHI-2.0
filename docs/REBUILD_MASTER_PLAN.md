# NyaySaathi UK — Phase-by-Phase Rebuild Master Plan
**Licence status (2026-10-18): Find Case Law Computational Analysis Licence APPLIED by owner, NOT YET GRANTED.** Case-law live retrieval stays gated (`CASELAW_LIVE_ENABLED` + `CASELAW_COMPUTATIONAL_LICENCE_CONFIRMED`) until the grant letter/terms are received and checked. Applied ≠ permitted. Legislation (OGL v3.0) is the only live legal source until then.

## Accuracy doctrine (applies to every query)
1. User's words are allegations, never facts. 2. No proposition reaches the user unless tied to a retrieved, allow-listed official source passing distinctive-term passage relevance (`server/pipeline.py`). 3. Retrieval relevance ≠ outcome probability — no win %, costs, or durations without validated methodology (currently: none). 4. Missing/irrelevant sources ⇒ abstain explicitly. 5. Every answer shows sources, passages, retrieval trace and uncertainty. 6. LLM (optional, server-side, off by default) may only rephrase verified propositions; it may never introduce a citation (URL allow-list enforced before ranking).

## Query pipeline (implemented in server/pipeline.py, wired to /api/explain)
Intake narrative → safety screen (pre-retrieval, deterministic) → structured case state (user-correctable) → per-issue query plan (primary + legislation-discovery) → provider search (legislation now; case law after grant) → URL allow-list drop → dedupe → transparent lexical ranking (title 2×, passage 1×) → distinctive-term verification gate → grounded explanation OR abstention → evidence gaps + next questions → content-free audit event.

---

## Phase 0 — Baseline & audit ✅ DONE
Entry: repo as-is. Tasks: full audit, dataset quarantine, secret scrub. Exit gate: docs/REPOSITORY_AUDIT.md, DATASET_AUDIT.md. Evidence: commit 9866c02.

## Phase 1 — Legal-source rights & compliance 🟡 IN PROGRESS (owner)
Tasks: TNA licence application ✅ applied; record grant terms/licence category/duration/conditions in UK_LEGAL_DATA_RESEARCH.md when received; confirm whether R&D vs Transactional covers consumer-facing use; OGL attribution implemented. Gate: **written grant checked → only then flip env flags.** Risk: refusal/high-risk classification ("fully automated legal advice") → mitigation: human-review positioning, no outcome prediction (already enforced).

## Phase 2 — Core contracts & schemas ✅ DONE (v1)
CaseState, Source, audit events (`server/core.py`). Remaining: versioned JSON-schema export + case-state edit/confirm endpoint (PATCH semantics) with provenance per edited field. Acceptance: user edits mark facts `user-confirmed`, AI inference never overwrites user text. Tests: round-trip, provenance, correction.

## Phase 3 — Legislation connector ✅ DONE v2 (provision-level CLML parse server/legislation.py, ranked provisions, in-force never asserted without metadata, TTL cache; live smoke = deploy gate)
Atom search, OGL attribution, graceful 502. Next quality tasks: (a) fetch provision-level CLML (`/data.xml`) and extract relevant sections, not just feed summaries; (b) version metadata: enacted vs revised, in-force status only if metadata supports it; (c) short-TTL cache keyed by identifier+retrieved_at. Gate: live smoke test from deploy host (sandbox egress blocked). Tests: recorded Atom/CLML fixtures, version labelling, outage.

## Phase 4 — Case-law connector ⛔ BLOCKED ON GRANT
Adapter built + licence gate tested. On grant: enable search, add neutral-citation/court/date parsing from LegalDocML, court-level authority labelling (binding vs persuasive guidance, never automated merits). Tests: fixtures, pagination, licence-flag-off regression. Gate: grant terms on file + flags set in deploy env only.

## Phase 5 — Retrieval, ranking & verification ✅ DONE (v1 lexical)
Pipeline + URL allow-list + distinctive-term gate + abstention (`server/pipeline.py`), evaluation harness (`server/evaluate.py`). Next after licence: semantic/hybrid retrieval **only over licence-permitted index**, reranking evaluation vs lexical baseline (adopt only if Recall@5/nDCG improves on labelled set). Quality targets (labelled set, to be built): citation precision 100% (fabricated = release blocker), correct-abstention ≥90%, issue recall ≥90%.

## Phase 6 — Intake, timeline & evidence ✅ DONE v2 (POST /api/case-state/confirm — user-confirmed provenance, evidence statuses; UI binding renderCaseSummaryUK in app.js)
Deterministic extraction, safety signposting, checklists. Next: editable case-state UI binding (timeline/checklist status persisted in localStorage), contradiction/gap prompts, follow-up question loop (max 3 targeted questions before explanation). Tests: eval scenarios, approximate dates, user correction.

## Phase 7 — Grounded explanation ✅ v2 (server/llm.py best-model polish layer: per-task model env, citation revalidation + banned-claim rejection, deterministic fallback; off unless LLM_API_KEY+model configured server-side). Story/packet from verified propositions: NEXT
Next: story mode regenerated from verified propositions only (clearly fictional), packet export (print/PDF via browser), deadline flags **only** when sourced from retrieved provision text (extracted limitation wording + "verify this deadline" warning). Gate: solicitor review of templates (Phase 10).

## Phase 8 — Lawyer discovery & consent handoff 🟡 HONEST STUB
Empty verified directory + consent state machine (pending only). Next: only populate from a verifiable source (SRA/Law Society data under its terms); match explanation = area/location/language only, no quality scores. Gate: no transfer without explicit consent (tested), statuses never claim acceptance.

## Phase 9 — UI integration ✅ DONE (v1)
Analytics removed, UK content, real wiring, empty/error states. Next: full case-summary rendering of pipeline output (sources/passages/trace), accessibility pass (labels, focus, contrast), responsive QA. Gate: every advertised feature works or is labelled unavailable.

## Phase 10 — Evaluation, security & pilot readiness 🟡 STARTED
Done: offline eval (issue_recall 1.0, safety 1.0, abstention 1.0 on 6 scenarios — small set, not an accuracy claim), 6 unit tests. Remaining: expand to ≥50 solicitor-labelled scenarios per area, live retrieval metrics, prompt-injection tests on narratives/documents, access-control tests, **qualified solicitor review sign-off**. Gate: no pilot without it.

## Phase 11 — Deployment & monitoring ⬜
Env secrets on host, live smoke tests (G3), uptime/error monitoring (content-free), source-outage runbook, rollback = previous commit. Gate: health + legislation search verified live.

## Per-feature quality bar (best-possible-advice standard)
Intake: empathy script reviewed, never repeats intrusive questions. Issues: multi-label candidates + uncertainty, never single forced class. Legislation: provision-level text + version. Cases: real judgments + court/date + "how it differs" notes. Explanation: every proposition cited or removed. Evidence: items tied to an issue, "may help" vs "required" only if sourced. Risk: sourced deadlines only. Packet: user-confirmed facts distinguished from unverified. Lawyers: verified data or empty. Privacy: narratives never logged; keys server-side only.

## Immediate next actions (while licence pending)
1. Phase 3 provision-level fetch + fixtures. 2. Phase 6/9 editable case-state UI. 3. Phase 10 scenario set expansion. 4. On grant: Phase 4 enablement in one flagged commit + live tests.
