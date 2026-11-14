# Implementation log

- Audited the complete selected checkout before code changes. Corrected requested target to NYAYSAATHI-2.0, per user.
- Created feature/india-consumer-workflow. Retained recognizable brand, CSS and navigation. Removed mock analytics and unsupported performance/advocate claims from the active UI.
- Quarantined legacy dataset and disabled old RAG entry point. Building persistent API, privacy boundaries, review-gated knowledge providers and real Gemini adapter.
- External prerequisites: official-source domains and Gemini API access are blocked or unconfigured. No manual source review or live Gemini validation is claimed.
- Implemented single-process FastAPI integration and SQLite version-1 schema with private evidence BLOBs, redacted complete narratives, opaque expiring sessions, ownership checks, CSRF protection and audit trail.
- Replaced active mock frontend with API-connected screens while reusing the original stylesheet and brand. Retained navigation; removed obsolete analytics and misleading simulated services.
- Implemented explicit synthetic-data consent, optional Gemini consent, unsupported-domain/jurisdiction gating, conservative English/Hindi questions, literal fact/date provenance checks and qualitative evidence readiness.
- Implemented local TXT/PDF extraction with limits and date reconciliation prompts, editable seller letters, Unicode PDFs with source-unavailability disclosure, session-bound signed download grants and deletion/retention controls.
- Implemented voluntary snapshot sharing, separate authenticated demo lawyer inbox, PDF download, acknowledgment and revocation. Browser rehearsal used two independent cookie contexts.
- Removed embedded credential material and tracked compiled copies; untracked the local .env without deleting the user's local file. Owner rotation/history remediation remains separate.
- Added 31 synthetic evaluation narratives and meaningful API/source/provider/security/browser tests. Dependencies are pinned in a hash-verified lock file. Exact outcomes are recorded in TEST_REPORT.md.
- Source corpus remains empty by design. 36 review targets are a queue, not a completed verified knowledge base. Official-source access, rights review and live Gemini pricing/quota/model validation remain external release blockers.

## Grounded intelligence implementation
- Started from committed baseline 0f3f93f on dedicated branch feature/grounded-consumer-intelligence. Audited current routes/screens/contracts and distinguished live tests from mocks.
- New published environment has ready Gemini binding. Actual model-list request succeeded; configured embedding identifier is absent, while gemini-embedding-001 is available. Original legal artifact URL is invalid HTML and India Code announces a domain migration. Investigating approved official alternatives before ingesting any passage.
- Live account checks: original gemini-2.5-flash generation returned HTTP 404 (not available to new users), listed gemini-3.8-flash returned HTTP 503 (capacity), listed stable gemini-3.1-flash-lite returned HTTP 200. Real gemini-embedding-001 returned a 768-dimensional vector. Tests use explicit runtime overrides; saved user model variables are not silently overwritten.
- Added canonical entity provenance, persistent dialogue/corrections/AI-consent routes, natural factual questions, separate legal-claim support evaluation, 16 original bilingual fictional scenarios, multi-template preparation documents, document reconciliation and bounded local Tesseract OCR.
- Revised readiness semantics: category count alone no longer yields Strong; missing factual/source coverage and discrepancies remain visible. Updated the original lifecycle expectation accordingly, retaining its full persistence/PDF/handoff/deletion assertions.
