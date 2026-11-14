# Feature matrix

Status reflects implemented capability, not a claim that external services are ready.

| Feature | Implementation | Validation / limitation |
|---|---|---|
| Existing identity/navigation | Original stylesheet, purple/cream identity, dashboard/intake/story/summary/documents/lawyers/privacy/settings/help | Browser desktop/tablet/mobile; no React migration |
| Confidential intake | Explicit processing + fictional-data consent; optional separate Gemini opt-in; English/Hindi | Real data intentionally refused unless user confirms fictional (confirmation cannot prove synthetic origin) |
| Persistent sessions/cases | SQLite migrations; hashed opaque session cookies, expiry, owner authorization, redacted full narrative | API persistence/reopen and cross-user tests |
| Issues/facts/timeline | Conservative bilingual rules; verbatim Gemini extraction when enabled; explicit ISO dates only | 31 synthetic scenarios; no inference of unknown dates |
| Verified law | Reviewed-source provider; immutable official artifacts, exact-text/hash/date/jurisdiction/rights checks; 36-entry review queue | **BLOCKED:** zero reviewed passages, official network requests denied; no section applicability claims displayed |
| Hybrid retrieval | SQLite FTS5 BM25 + optional real Gemini embedding adapter and reciprocal-rank fusion | Lexical and hybrid paths tested with clearly synthetic fixtures; live embeddings unverified; local fallback labelled lexical |
| Gemini orchestration | Real REST model listing, structured extraction and grounded passage selection, Pydantic/provenance checks | Provider transport/error paths tested using mocks; **live use blocked by missing key/model and terms review** |
| Case comparison/story | Clearly labelled fictional scenario cards; no judgments or outcome predictions | Browser/API tests; authentic case comparison disabled |
| Evidence/documents | Private TXT/flattened PDF uploads, local text extraction, date-discrepancy prompts, category checklist | Type/magic/size/encryption/active-content limits; no OCR, DOCX, image analysis or authenticity verification |
| Readiness | Strong/Partial/Needs information from uploaded categories and missing facts | No success probability; completeness cannot establish evidential sufficiency |
| Complaint drafting | Editable seller representation with allegations/placeholders and no invented legal deadlines | Not a commission pleading; no sending/filing automation |
| Case packet | Unicode HTML-to-PDF, facts, timeline, inventory, sources or abstention, drafts and limitations | English/Hindi PDF tests; signed expiring session-bound download grants |
| Lawyer handoff | Separate private demo role, explicit snapshot sharing, inbox, download, acknowledgment, revocation and audit | Functional local demonstration; not a verified advocate or live professional service |
| Official filing guidance | NCH, e-Jagriti, India Code, NALSA starting points and clear pathway boundaries | External portals not validated/reachable here; no filing integration or deadline calculation |
| Deletion/retention | Cascading case/file/handoff deletion, session/retention cleanup on startup and requests | Downloaded copies/backups cannot be recalled; no production retention certification |
| UK / external ingestion | Disabled UK provider, explicit per-source manual importer; no crawler or autonomous ingestion | Licensing, jurisdiction and source review required before enabling |
| Deployment | Single FastAPI process serving only allowlisted frontend files | Local fictional demo; public sensitive-data launch not approved/validated |

The full grounded-AI definition of done is **not met** while live Gemini and reviewed legal sources remain unavailable. Local case-preparation and demonstration handoff are independently functional.
